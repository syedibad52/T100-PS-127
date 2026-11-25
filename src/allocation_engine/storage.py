from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from .models import Candidate, CandidateStatus, DonorOffer, Organ, StatusInterval, TransportRoute, ValidationError, parse_time


def _organs(value: str) -> set[Organ]:
    try: return {Organ(item.strip().upper()) for item in value.replace(",", ";").split(";") if item.strip()}
    except ValueError as exc: raise ValidationError(f"Invalid organ list: {value}") from exc


def _hla(value: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in value.replace(";", ",").split(",") if x.strip())


def candidates_from_csv(path: str | Path) -> list[Candidate]:
    required = {"candidate_id", "organs", "blood_group", "hla", "age", "weight_kg", "hospital", "city", "zone", "listing_at", "last_clinical_update_at"}
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not required <= set(reader.fieldnames): raise ValidationError(f"Missing required candidate fields: {sorted(required - set(reader.fieldnames or []))}")
        output: list[Candidate] = []
        seen: set[str] = set()
        for row in reader:
            if row["candidate_id"] in seen: raise ValidationError(f"Duplicate candidate ID: {row['candidate_id']}")
            seen.add(row["candidate_id"])
            history_json = row.get("status_history") or ""
            history = [StatusInterval(CandidateStatus(x["status"]), parse_time(x["start"]), parse_time(x["end"]) if x.get("end") else None, Organ(x["organ"]) if x.get("organ") else None) for x in json.loads(history_json)] if history_json else [StatusInterval(CandidateStatus.ACTIVE, parse_time(row["listing_at"]))]
            output.append(Candidate(row["candidate_id"], _organs(row["organs"]), row["blood_group"], _hla(row["hla"]), int(row["age"]), float(row["weight_kg"]), row["hospital"], row["city"], row["zone"], parse_time(row["listing_at"]), parse_time(row["last_clinical_update_at"]), history, int(row["meld"]) if row.get("meld") else None, int(row["heart_status"]) if row.get("heart_status") else None, int(row.get("dialysis_days") or 0), str(row.get("extended_age_consent", "")).lower() == "true"))
    return output


def donors_from_csv(path: str | Path) -> list[DonorOffer]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream)); seen: set[str] = set(); output: list[DonorOffer] = []
        for row in rows:
            if row["offer_id"] in seen: raise ValidationError(f"Duplicate donor offer ID: {row['offer_id']}")
            seen.add(row["offer_id"])
            output.append(DonorOffer(row["donor_id"], row["offer_id"], Organ(row["organ"]), frozenset(_organs(row["available_organs"])), row["blood_group"], _hla(row["hla"]), int(row["age"]), float(row["weight_kg"]), row["hospital"], row["city"], row["zone"], parse_time(row["cross_clamp_at"])))
    return output


def transport_from_csv(path: str | Path) -> dict[tuple[str, str], int]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        routes = [TransportRoute(row["origin"], row["destination"], int(row["minutes"])) for row in csv.DictReader(stream)]
    return {(r.origin, r.destination): r.minutes for r in routes}


def supplied_sample_dataset(directory: str | Path, as_of: datetime) -> tuple[list[Candidate], list[DonorOffer], dict[tuple[str, str], int]]:
    """Load the 10 SECONDS sample pack without mutating its prescribed CSV schema."""
    root = Path(directory)
    with (root / "hospitals.csv").open(newline="", encoding="utf-8") as stream:
        hospitals = {row["hospital_id"]: row for row in csv.DictReader(stream)}
    with (root / "status_history.csv").open(newline="", encoding="utf-8") as stream:
        inactive = defaultdict(list)
        for row in csv.DictReader(stream):
            inactive[row["candidate_id"]].append((parse_time(row["from_date"]), parse_time(row["to_date"]) + timedelta(days=1)))
    with (root / "refusal_history.csv").open(newline="", encoding="utf-8") as stream:
        from .models import Refusal
        refusals = defaultdict(list)
        for row in csv.DictReader(stream):
            refusals[row["candidate_id"]].append(Refusal(parse_time(row["refusal_date"]), row["reason"], row["reason_type"], row["offer_ref"]))
    candidates: list[Candidate] = []
    with (root / "candidates.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            hospital = hospitals.get(row["hospital_id"])
            if hospital is None: raise ValidationError(f"Unknown hospital: {row['hospital_id']}")
            listing = parse_time(row["listing_ts"])
            # BR-03: retain entitlement only for relisting within 90 days of transplant.
            if row.get("prior_transplant_date") and row.get("original_listing_ts"):
                transplant = parse_time(row["prior_transplant_date"])
                if listing - transplant <= timedelta(days=90): listing = parse_time(row["original_listing_ts"])
            periods = sorted(inactive[row["candidate_id"]])
            history: list[StatusInterval] = []
            cursor = listing
            for start, end in periods:
                if start > cursor: history.append(StatusInterval(CandidateStatus.ACTIVE, cursor, start))
                history.append(StatusInterval(CandidateStatus.INACTIVE, max(start, cursor), end))
                cursor = max(cursor, end)
            current = CandidateStatus(row["status"])
            history.append(StatusInterval(current, cursor))
            dob = parse_time(row["dob"])
            age = as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))
            dialysis_days = max(0, (as_of - parse_time(row["dialysis_start"])).days) if row.get("dialysis_start") else 0
            candidates.append(Candidate(row["candidate_id"], _organs(row["organs"]), row["blood_group"], _hla(row["hla_typing"]), age, float(row["weight_kg"]), row["hospital_id"], hospital["city"], hospital["zone"], listing, parse_time(row["last_clinical_update"]), history, int(row["meld"]) if row.get("meld") else None, int(row["heart_status"]) if row.get("heart_status") else None, dialysis_days, row["consent_older_donor"].lower() == "true", refusals[row["candidate_id"]]))
    with (root / "donor_offers.csv").open(newline="", encoding="utf-8") as stream:
        donor_rows = list(csv.DictReader(stream))
    donor_organs = defaultdict(set)
    for row in donor_rows: donor_organs[row["donor_id"]].add(Organ(row["organ"]))
    donors: list[DonorOffer] = []
    for row in donor_rows:
        hospital = hospitals.get(row["donor_hospital_id"])
        if hospital is None: raise ValidationError(f"Unknown hospital: {row['donor_hospital_id']}")
        donors.append(DonorOffer(row["donor_id"], row["offer_id"], Organ(row["organ"]), frozenset(donor_organs[row["donor_id"]]), row["donor_blood_group"], _hla(row["donor_hla_typing"]), int(row["donor_age"]), float(row["donor_weight_kg"]), row["donor_hospital_id"], hospital["city"], hospital["zone"], parse_time(row["cross_clamp_ts"])))
    with (root / "transport_matrix.csv").open(newline="", encoding="utf-8") as stream:
        routes = [TransportRoute(row["from_hospital_id"], row["to_hospital_id"], int(row["transport_minutes"])) for row in csv.DictReader(stream)]
    return candidates, donors, {(route.origin, route.destination): route.minutes for route in routes}
