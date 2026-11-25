from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate(output: str | Path, seed: int = 127, count: int = 250) -> None:
    """Generate labelled synthetic-only CSV inputs with no patient information."""
    rng = random.Random(seed); directory = Path(output); directory.mkdir(parents=True, exist_ok=True)
    hospitals = [(f"H{i:02d}", f"City{(i - 1) // 3 + 1}", f"Zone{(i - 1) // 6 + 1}") for i in range(1, 13)]
    orgs = ["KIDNEY", "LIVER", "HEART"]; bloods = ["O", "A", "B", "AB"]; base = datetime(2026, 1, 1, 9)
    fields = ["candidate_id", "organs", "blood_group", "hla", "age", "weight_kg", "hospital", "city", "zone", "listing_at", "last_clinical_update_at", "meld", "heart_status", "dialysis_days", "extended_age_consent"]
    with (directory / "candidates.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for i in range(1, count + 1):
            organ = orgs[(i - 1) % 3]; hospital, city, zone = hospitals[(i - 1) % 12]; listed = base - timedelta(days=rng.randint(1, 1500))
            writer.writerow({"candidate_id": f"SYN-C{i:03d}", "organs": organ, "blood_group": bloods[i % 4], "hla": ",".join(f"L{(i+j)%20}" for j in range(6)), "age": rng.randint(1, 75), "weight_kg": rng.randint(25, 110), "hospital": hospital, "city": city, "zone": zone, "listing_at": listed.isoformat(), "last_clinical_update_at": "2026-11-01T09:00:00", "meld": rng.randint(6, 40) if organ == "LIVER" else "", "heart_status": rng.randint(1, 3) if organ == "HEART" else "", "dialysis_days": rng.randint(0, 1500) if organ == "KIDNEY" else 0, "extended_age_consent": "true" if i % 5 == 0 else "false"})
    with (directory / "transport.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["origin", "destination", "minutes"]); writer.writeheader()
        for origin, _, _ in hospitals:
            for destination, _, _ in hospitals:
                if origin != destination: writer.writerow({"origin": origin, "destination": destination, "minutes": 30 + 20 * abs(int(origin[1:]) - int(destination[1:]))})
    donor_fields = ["donor_id", "offer_id", "organ", "available_organs", "blood_group", "hla", "age", "weight_kg", "hospital", "city", "zone", "cross_clamp_at"]
    with (directory / "donors.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=donor_fields); writer.writeheader()
        for i in range(1, 21):
            hospital, city, zone = hospitals[(i - 1) % 12]; organ = orgs[(i - 1) % 3]
            available = "LIVER;KIDNEY" if organ == "LIVER" and i % 5 == 0 else organ
            writer.writerow({"donor_id": f"SYN-D{i:03d}", "offer_id": f"SYN-O{i:03d}", "organ": organ, "available_organs": available, "blood_group": bloods[i % 4], "hla": ",".join(f"L{(i+j)%20}" for j in range(6)), "age": rng.randint(18, 70), "weight_kg": rng.randint(35, 110), "hospital": hospital, "city": city, "zone": zone, "cross_clamp_at": "2026-11-25T06:00:00"})
    (directory / "README.txt").write_text(f"SYNTHETIC DEVELOPMENT DATA ONLY. seed={seed}; candidates={count}. Not official evaluation data.\n", encoding="utf-8")
