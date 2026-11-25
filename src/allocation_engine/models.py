from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ValidationError(ValueError):
    """Raised when a record cannot safely enter allocation calculations."""


class Organ(str, Enum):
    KIDNEY = "KIDNEY"
    LIVER = "LIVER"
    HEART = "HEART"


class CandidateStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELISTED = "DELISTED"
    TRANSPLANTED = "TRANSPLANTED"
    DECEASED = "DECEASED"
    STALE = "STALE"


class EventType(str, Enum):
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    REFUSED = "REFUSED"
    TIMEOUT = "TIMEOUT"
    CROSSMATCH_FAILED = "CROSSMATCH_FAILED"
    CANCELLED = "CANCELLED"
    ALLOCATED = "ALLOCATED"


def parse_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (AttributeError, ValueError) as exc:
        raise ValidationError(f"Invalid ISO timestamp: {value}") from exc


@dataclass(frozen=True)
class StatusInterval:
    status: CandidateStatus
    start: datetime
    end: datetime | None = None
    organ: Organ | None = None

    def __post_init__(self) -> None:
        if self.end and self.end < self.start:
            raise ValidationError("Status interval end is before start")


@dataclass(frozen=True)
class Refusal:
    at: datetime
    reason: str
    category: str
    run_id: str

    @property
    def medical(self) -> bool:
        return self.category.upper() == "MEDICAL"


@dataclass
class Candidate:
    candidate_id: str
    organs: set[Organ]
    blood_group: str
    hla: tuple[str, ...]
    age: int
    weight_kg: float
    hospital: str
    city: str
    zone: str
    listing_at: datetime
    last_clinical_update_at: datetime
    status_history: list[StatusInterval]
    meld: int | None = None
    heart_status: int | None = None
    dialysis_days: int = 0
    extended_age_consent: bool = False
    refusals: list[Refusal] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.blood_group = self.blood_group.upper()
        if not self.candidate_id or self.blood_group not in {"O", "A", "B", "AB"}:
            raise ValidationError("Candidate ID and valid blood group are required")
        if self.age < 0 or self.weight_kg <= 0 or self.dialysis_days < 0:
            raise ValidationError("Candidate age, weight, and dialysis duration are invalid")
        if len(self.hla) != 6 or len(set(self.hla)) != 6:
            raise ValidationError("HLA must contain six distinct loci")
        if not self.organs:
            raise ValidationError("Candidate must request at least one organ")
        if self.meld is not None and not 6 <= self.meld <= 40:
            raise ValidationError("MELD must be between 6 and 40")
        if self.heart_status is not None and self.heart_status not in {1, 2, 3}:
            raise ValidationError("Heart status must be 1, 2, or 3")


@dataclass(frozen=True)
class DonorOffer:
    donor_id: str
    offer_id: str
    organ: Organ
    available_organs: frozenset[Organ]
    blood_group: str
    hla: tuple[str, ...]
    age: int
    weight_kg: float
    hospital: str
    city: str
    zone: str
    cross_clamp_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "blood_group", self.blood_group.upper())
        if not self.donor_id or not self.offer_id or self.blood_group not in {"O", "A", "B", "AB"}:
            raise ValidationError("Donor/offer ID and valid blood group are required")
        if self.age < 0 or self.weight_kg <= 0 or len(self.hla) != 6:
            raise ValidationError("Invalid donor age, weight, or HLA")
        if self.organ not in self.available_organs:
            raise ValidationError("Offer organ must be available")


@dataclass(frozen=True)
class TransportRoute:
    origin: str
    destination: str
    minutes: int

    def __post_init__(self) -> None:
        if self.minutes < 0:
            raise ValidationError("Transport duration cannot be negative")


@dataclass(frozen=True)
class OfferEvent:
    candidate_id: str
    type: EventType
    at: datetime
    reason: str = ""
    category: str = "NON_MEDICAL"
    event_id: str = ""


def canonical(value: Any) -> Any:
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, Enum): return value.value
    if isinstance(value, set) or isinstance(value, frozenset): return sorted(canonical(x) for x in value)
    if isinstance(value, tuple) or isinstance(value, list): return [canonical(x) for x in value]
    if isinstance(value, dict): return {k: canonical(v) for k, v in sorted(value.items())}
    if hasattr(value, "__dataclass_fields__"): return canonical(asdict(value))
    return value
