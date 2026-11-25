from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from .models import Candidate, CandidateStatus, DonorOffer, EventType, OfferEvent, Organ, Refusal, canonical
from .rules import (blood_compatible, blood_priority, eligible_waiting_days, geographic_tier,
                    hla_mismatches, ischemia_eligible, penalty_active, size_age_eligible,
                    stale, status_as_of, urgency_and_score)


@dataclass
class Decision:
    candidate_id: str
    eligible: bool
    exclusions: list[str] = field(default_factory=list)
    tier: int | None = None
    waiting_days: float = 0.0
    mismatches: int = 0
    urgency: int = 0
    score: dict = field(default_factory=dict)
    penalized: bool = False
    urgency_override: bool = False
    rank: int | None = None

    def output(self) -> dict:
        return canonical(self.__dict__)


class AuditRepository:
    def __init__(self, directory: str | Path = "outputs/match_runs") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, audit: dict) -> Path:
        path = self.directory / f"{audit['run_id']}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(path)
        return path

    def load(self, run_id: str) -> dict:
        return json.loads((self.directory / f"{run_id}.json").read_text(encoding="utf-8"))


class MatchEngine:
    """Deterministic BR-12 pipeline. It has no wall-clock or random dependency."""
    policy_version = "provisional-1"

    def __init__(self, transport_minutes: dict[tuple[str, str], int], audit_repository: AuditRepository | None = None, whole_unit_kidney_points: bool = False) -> None:
        self.transport_minutes = transport_minutes
        self.audit_repository = audit_repository
        self.whole_unit_kidney_points = whole_unit_kidney_points
        self.allocated: set[tuple[str, Organ]] = set()

    def _route(self, donor: DonorOffer, candidate: Candidate) -> int | None:
        if donor.hospital == candidate.hospital: return 0
        return self.transport_minutes.get((donor.hospital, candidate.hospital))

    def _decision(self, candidate: Candidate, donor: DonorOffer, at: datetime) -> Decision:
        decision = Decision(candidate.candidate_id, False)
        if donor.organ not in candidate.organs:
            decision.exclusions.append("not registered for organ"); return decision
        status = status_as_of(candidate, at, donor.organ)
        if status != CandidateStatus.ACTIVE:
            decision.exclusions.append(f"BR-10 status {status.value}"); return decision
        if stale(candidate, at):
            decision.exclusions.append("BR-10 stale clinical update"); return decision
        if not blood_compatible(donor.blood_group, candidate.blood_group):
            decision.exclusions.append("BR-01 incompatible blood group"); return decision
        passed, reason = size_age_eligible(donor, candidate)
        if not passed: decision.exclusions.append(reason); return decision
        passed, reason = ischemia_eligible(donor, candidate, self._route(donor, candidate), at)
        if not passed: decision.exclusions.append(reason); return decision
        decision.eligible = True
        decision.tier = geographic_tier(donor, candidate)
        decision.waiting_days = eligible_waiting_days(candidate, at, donor.organ)
        if self.whole_unit_kidney_points:
            decision.waiting_days = float(int(decision.waiting_days))
        decision.mismatches = hla_mismatches(donor.hla, candidate.hla)
        decision.urgency, decision.score = urgency_and_score(candidate, donor, decision.waiting_days, self.whole_unit_kidney_points)
        decision.penalized = penalty_active(candidate.refusals, at)
        decision.urgency_override = donor.organ == Organ.LIVER and decision.urgency == 2 and decision.tier <= 3 or donor.organ == Organ.HEART and decision.urgency == 3 and decision.tier <= 3
        return decision

    def _sort_key(self, candidate: Candidate, donor: DonorOffer, decision: Decision) -> tuple:
        # Explicit precedence: penalty, urgent tier override, tier, blood, score, BR-06, fallback ID.
        override = 0 if decision.urgency_override else 1
        tier = decision.tier if donor.organ == Organ.KIDNEY or not decision.urgency_override else 0
        score = float(decision.score["total"])
        return (int(decision.penalized), override, tier, blood_priority(donor, candidate, decision.mismatches), -score, -decision.urgency, -decision.waiting_days, decision.mismatches, candidate.age, candidate.listing_at, candidate.candidate_id)

    def apply_multi_organ_override(self, donor: DonorOffer, ranked: list[Decision], candidates: dict[str, Candidate]) -> list[Decision]:
        if donor.organ != Organ.LIVER or Organ.KIDNEY not in donor.available_organs or not ranked:
            return ranked
        first = candidates[ranked[0].candidate_id]
        if Organ.KIDNEY in first.organs:
            ranked[0].score["multi_organ_override"] = "BR-09 liver-kidney atomic allocation eligible"
        return ranked

    def run(self, run_id: str, donor: DonorOffer, candidates: Iterable[Candidate], at: datetime) -> dict:
        pool = sorted(candidates, key=lambda c: c.candidate_id)
        ids = [c.candidate_id for c in pool]
        if len(ids) != len(set(ids)): raise ValueError("Duplicate candidate IDs")
        candidate_map = {c.candidate_id: c for c in pool}
        decisions = [self._decision(c, donor, at) for c in pool]
        ranked = [d for d in decisions if d.eligible]
        ranked.sort(key=lambda d: self._sort_key(candidate_map[d.candidate_id], donor, d))
        ranked = self.apply_multi_organ_override(donor, ranked, candidate_map)
        for index, decision in enumerate(ranked, start=1): decision.rank = index
        audit = {"run_id": run_id, "run_at": at.isoformat(), "donor": canonical(donor), "policy_version": self.policy_version,
                 "transport_matrix_version": self._transport_version(), "candidate_input_snapshot": canonical(pool),
                 "decisions": [d.output() for d in decisions], "ranked_candidate_ids": [d.candidate_id for d in ranked],
                 "primary": ranked[0].candidate_id if ranked else None, "backups": [d.candidate_id for d in ranked[1:3]],
                 "offer_history": [], "allocations": [], "rule_trace": [f"BR-{i:02d}" for i in range(1, 13)]}
        return audit

    def process_events(self, audit: dict, events: Iterable[OfferEvent]) -> dict:
        if audit["allocations"]:
            raise ValueError("This donor offer has already been allocated in this match run")
        start = datetime.fromisoformat(audit["run_at"]); ranked = audit["ranked_candidate_ids"]
        current_index = 0
        offer_started_at = start
        for event in sorted(events, key=lambda e: (e.at, e.event_id, e.candidate_id)):
            if event.candidate_id not in ranked: continue
            index = ranked.index(event.candidate_id)
            # Candidates are approached in ranked order.  A fallback's window begins
            # when the preceding candidate's terminal event is processed, not at run start.
            if index != current_index:
                continue
            deadline = offer_started_at + timedelta(minutes=60 if index == 0 else 30)
            record = canonical(event); record["deadline"] = deadline.isoformat()
            if event.at > deadline and event.type not in {EventType.TIMEOUT, EventType.CANCELLED}:
                record["effective_type"] = EventType.TIMEOUT.value
            else: record["effective_type"] = event.type.value
            audit["offer_history"].append(record)
            if record["effective_type"] == EventType.ACCEPTED.value:
                audit["allocations"] = [{"candidate_id": event.candidate_id, "organ": audit["donor"]["organ"], "at": event.at.isoformat()}]
                donor_organs = set(audit["donor"]["available_organs"])
                # Atomic BR-09: append kidney only if it was actually offered and documented available.
                if audit["donor"]["organ"] == "LIVER" and "KIDNEY" in donor_organs:
                    audit["allocations"].append({"candidate_id": event.candidate_id, "organ": "KIDNEY", "at": event.at.isoformat(), "reason": "BR-09"})
                break
            if record["effective_type"] in {EventType.REFUSED.value, EventType.TIMEOUT.value, EventType.CROSSMATCH_FAILED.value, EventType.CANCELLED.value}:
                current_index += 1
                offer_started_at = event.at
        return audit

    def persist(self, audit: dict) -> Path | None:
        return self.audit_repository.save(audit) if self.audit_repository else None

    def replay(self, run_id: str) -> dict:
        if not self.audit_repository: raise ValueError("Replay requires an audit repository")
        return self.audit_repository.load(run_id)

    def _transport_version(self) -> str:
        serial = json.dumps(sorted((a, b, m) for (a, b), m in self.transport_minutes.items()))
        return hashlib.sha256(serial.encode()).hexdigest()[:12]
