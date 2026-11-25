import pytest

from allocation_engine.models import Candidate, CandidateStatus, Organ, StatusInterval, ValidationError


def test_invalid_hla_rejected():
    with pytest.raises(ValidationError, match="HLA"):
        Candidate("C", {Organ.KIDNEY}, "O", ("A",), 30, 70, "H", "C", "Z", __import__("datetime").datetime.now(), __import__("datetime").datetime.now(), [StatusInterval(CandidateStatus.ACTIVE, __import__("datetime").datetime.now())])
