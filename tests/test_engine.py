from datetime import datetime, timedelta

import pytest

from allocation_engine.engine import AuditRepository, MatchEngine
from allocation_engine.models import Candidate, CandidateStatus, DonorOffer, EventType, OfferEvent, Organ, Refusal, StatusInterval
from allocation_engine.rules import (blood_compatible, eligible_waiting_days, ischemia_eligible,
                                     penalty_active, size_age_eligible)

NOW = datetime(2026, 11, 25, 10)
HLA = ("A1", "A2", "B1", "B2", "DR1", "DR2")


def candidate(cid="C1", organ=Organ.KIDNEY, blood="O", hospital="H1", city="C1", zone="Z1", **kwargs):
    return Candidate(cid, {organ}, blood, kwargs.pop("hla", HLA), kwargs.pop("age", 45), kwargs.pop("weight", 70), hospital, city, zone, kwargs.pop("listed", NOW - timedelta(days=180)), kwargs.pop("updated", NOW - timedelta(days=1)), kwargs.pop("history", [StatusInterval(CandidateStatus.ACTIVE, NOW - timedelta(days=180))]), **kwargs)


def donor(organ=Organ.KIDNEY, blood="O", organs=None, **kwargs):
    return DonorOffer("D1", "O1", organ, frozenset(organs or {organ}), blood, kwargs.pop("hla", HLA), kwargs.pop("age", 40), kwargs.pop("weight", 70), "H1", "C1", "Z1", kwargs.pop("clamp", NOW - timedelta(hours=1)))


@pytest.mark.parametrize("donor_blood,recipient,ok", [("O", x, True) for x in ["O", "A", "B", "AB"]] + [("A", "O", False), ("B", "A", False), ("AB", "O", False)])
def test_blood_matrix(donor_blood, recipient, ok):
    assert blood_compatible(donor_blood, recipient) is ok


def test_meld_boundary():
    run = MatchEngine({}).run("R", donor(Organ.LIVER), [candidate(organ=Organ.LIVER, meld=35)], NOW)
    assert run["decisions"][0]["score"]["urgency"] == "SUPER_URGENT"  # EC-02


def test_ischemia_boundary():
    d = donor(clamp=NOW - timedelta(hours=24)); c = candidate()
    assert ischemia_eligible(d, c, 0, NOW)[0]  # EC-03 equality


def test_inactive_waiting_period():
    history = [StatusInterval(CandidateStatus.ACTIVE, NOW - timedelta(days=30), NOW - timedelta(days=20)), StatusInterval(CandidateStatus.INACTIVE, NOW - timedelta(days=20), NOW - timedelta(days=10)), StatusInterval(CandidateStatus.ACTIVE, NOW - timedelta(days=10))]
    assert eligible_waiting_days(candidate(history=history, listed=NOW - timedelta(days=30)), NOW, Organ.KIDNEY) == 20  # EC-04


@pytest.mark.parametrize("ratio", [0.7, 1.3])
def test_heart_weight_boundaries(ratio):
    assert size_age_eligible(donor(Organ.HEART, weight=70 * ratio), candidate(organ=Organ.HEART))[0]  # EC-05


def test_third_refusal_day_365():
    refusals = [Refusal(NOW - timedelta(days=d), "x", "NON_MEDICAL", "R") for d in (365, 100, 1)]
    assert penalty_active(refusals, NOW)  # EC-06


def test_backup_at_four_hours():
    first, second = candidate("C1", listed=NOW - timedelta(days=190)), candidate("C2")
    audit = MatchEngine({}).run("R", donor(), [first, second], NOW)
    result = MatchEngine({}).process_events(audit, [OfferEvent("C1", EventType.CROSSMATCH_FAILED, NOW + timedelta(hours=3, minutes=45)), OfferEvent("C2", EventType.ACCEPTED, NOW + timedelta(hours=4))])
    assert result["allocations"][0]["candidate_id"] == "C2"  # EC-07 event engine does not rerun


def test_multi_organ_override():
    multi = candidate("C1", Organ.LIVER, meld=40); multi.organs.add(Organ.KIDNEY); other = candidate("C2", Organ.LIVER, listed=NOW - timedelta(days=400), meld=10)
    audit = MatchEngine({}).run("R", donor(Organ.LIVER, organs={Organ.LIVER, Organ.KIDNEY}), [multi, other], NOW)
    assert "multi_organ_override" in audit["decisions"][0]["score"]  # EC-08


def test_deterministic_tie():
    audit = MatchEngine({}).run("R", donor(), [candidate("C2"), candidate("C1")], NOW)
    assert audit["ranked_candidate_ids"] == ["C1", "C2"]  # EC-01 documented fallback


def test_stale_candidate():
    audit = MatchEngine({}).run("R", donor(), [candidate(updated=NOW - timedelta(days=91))], NOW)
    assert "stale" in audit["decisions"][0]["exclusions"][0]


def test_exclusion_precedes_ranking():
    audit = MatchEngine({}).run("R", donor(blood="A"), [candidate(blood="O")], NOW)
    assert not audit["decisions"][0]["eligible"] and audit["ranked_candidate_ids"] == []


def test_replay(tmp_path):
    repo = AuditRepository(tmp_path); engine = MatchEngine({}, repo); audit = engine.run("R", donor(), [candidate()], NOW); engine.persist(audit)
    assert engine.replay("R") == audit


def test_duplicate_allocation_attempt_rejected():
    engine = MatchEngine({}); audit = engine.run("R", donor(), [candidate()], NOW)
    engine.process_events(audit, [OfferEvent("C1", EventType.ACCEPTED, NOW + timedelta(minutes=1))])
    with pytest.raises(ValueError, match="already been allocated"):
        engine.process_events(audit, [OfferEvent("C1", EventType.ACCEPTED, NOW + timedelta(minutes=2))])
