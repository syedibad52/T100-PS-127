from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from .models import Candidate, CandidateStatus, DonorOffer, Organ, Refusal, StatusInterval

BLOOD_MATRIX = {"O": {"O", "A", "B", "AB"}, "A": {"A", "AB"}, "B": {"B", "AB"}, "AB": {"AB"}}
ISCHEMIA_HOURS = {Organ.KIDNEY: 24, Organ.LIVER: 12, Organ.HEART: 4}


def blood_compatible(donor: str, recipient: str) -> bool:
    return recipient in BLOOD_MATRIX[donor]


def hla_mismatches(donor_hla: tuple[str, ...], candidate_hla: tuple[str, ...]) -> int:
    return sum(antigen not in set(candidate_hla) for antigen in donor_hla)


def status_as_of(candidate: Candidate, at: datetime, organ: Organ) -> CandidateStatus:
    intervals = [x for x in candidate.status_history if x.organ in (None, organ) and x.start <= at and (x.end is None or at < x.end)]
    if not intervals:
        return CandidateStatus.INACTIVE
    return max(intervals, key=lambda x: x.start).status


def eligible_waiting_days(candidate: Candidate, at: datetime, organ: Organ) -> float:
    """Sum ACTIVE intervals without overlap, bounded by listing and as-of time."""
    spans: list[tuple[datetime, datetime]] = []
    for interval in candidate.status_history:
        if interval.organ not in (None, organ) or interval.status != CandidateStatus.ACTIVE:
            continue
        start = max(candidate.listing_at, interval.start)
        end = min(at, interval.end or at)
        if end > start: spans.append((start, end))
    spans.sort()
    merged: list[list[datetime]] = []
    for start, end in spans:
        if not merged or start > merged[-1][1]: merged.append([start, end])
        elif end > merged[-1][1]: merged[-1][1] = end
    return sum((end - start).total_seconds() / 86400 for start, end in merged)


def stale(candidate: Candidate, at: datetime) -> bool:
    return at - candidate.last_clinical_update_at > timedelta(days=90)


def geographic_tier(donor: DonorOffer, candidate: Candidate) -> int:
    if donor.hospital == candidate.hospital: return 1
    if donor.city == candidate.city: return 2
    if donor.zone == candidate.zone: return 3
    return 4


def ischemia_eligible(donor: DonorOffer, candidate: Candidate, transport_minutes: int | None, at: datetime) -> tuple[bool, str]:
    if transport_minutes is None: return False, "BR-04 missing transport route"
    arrival = at + timedelta(minutes=transport_minutes)
    deadline = donor.cross_clamp_at + timedelta(hours=ISCHEMIA_HOURS[donor.organ])
    return (arrival <= deadline, "" if arrival <= deadline else "BR-04 cold-ischemia limit exceeded")


def size_age_eligible(donor: DonorOffer, candidate: Candidate) -> tuple[bool, str]:
    if donor.age > 60 and candidate.age < 40 and not candidate.extended_age_consent:
        return False, "BR-05 extended-age donor consent absent"
    if donor.organ == Organ.HEART:
        ratio = donor.weight_kg / candidate.weight_kg
        if not 0.7 <= ratio <= 1.3: return False, "BR-05 heart weight ratio outside 70%-130%"
    if donor.organ == Organ.LIVER:
        ratio = donor.weight_kg / candidate.weight_kg
        if not 0.8 <= ratio <= 1.5: return False, "BR-05 liver weight ratio outside 0.8-1.5"
    return True, ""


def urgency_and_score(candidate: Candidate, donor: DonorOffer, waiting_days: float, whole_unit_kidney_points: bool = False) -> tuple[int, dict[str, float | int | str]]:
    mismatch = hla_mismatches(donor.hla, candidate.hla)
    if donor.organ == Organ.KIDNEY:
        waiting_points = waiting_days // 30 if whole_unit_kidney_points else waiting_days / 30
        dialysis_points = candidate.dialysis_days // 90 if whole_unit_kidney_points else candidate.dialysis_days / 90
        components = {"waiting_time_points": waiting_points, "dialysis_points": dialysis_points, "hla_points": 6 - mismatch}
        return 0, {**components, "total": sum(components.values()), "urgency": "STANDARD"}
    if donor.organ == Organ.LIVER:
        meld = candidate.meld if candidate.meld is not None else -1
        urgency = "SUPER_URGENT" if meld >= 35 else "STANDARD"
        return (2 if meld >= 35 else 1), {"meld": meld, "total": meld, "urgency": urgency}
    status = candidate.heart_status if candidate.heart_status is not None else 99
    urgency = {1: "STATUS_1", 2: "STATUS_2", 3: "STATUS_3"}.get(status, "INVALID")
    return ({1: 3, 2: 2, 3: 1}.get(status, 0)), {"heart_status": status, "total": 4 - status if status <= 3 else -1, "urgency": urgency}


def penalty_active(refusals: Iterable[Refusal], at: datetime) -> bool:
    qualifying = sorted((r for r in refusals if not r.medical and at - timedelta(days=365) <= r.at <= at), key=lambda r: r.at)
    return len(qualifying) >= 3 and at < qualifying[-1].at + timedelta(days=90)


def blood_priority(donor: DonorOffer, candidate: Candidate, mismatches: int) -> int:
    # Lower ranks earlier; provisional O-kidney exception remains visible here.
    if donor.organ == Organ.KIDNEY and donor.blood_group == "O" and candidate.blood_group != "O":
        return 1 if (candidate.age < 18 or mismatches == 0) else 2
    return 0 if donor.blood_group == candidate.blood_group else 1
