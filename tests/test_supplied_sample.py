from datetime import datetime
from pathlib import Path

from allocation_engine.engine import MatchEngine
from allocation_engine.storage import supplied_sample_dataset


def test_supplied_sample_pack_loads_and_planted_multi_organ_case_ranks_first():
    root = Path(__file__).resolve().parents[1] / "data" / "sample"
    at = datetime(2026, 8, 3, 5)
    candidates, donors, routes = supplied_sample_dataset(root, at)
    donor = next(item for item in donors if item.offer_id == "OFR-001")
    audit = MatchEngine(routes, whole_unit_kidney_points=True).run("SAMPLE", donor, candidates, at)
    assert (len(candidates), len(donors), len(routes)) == (250, 20, 144)
    assert audit["primary"] == "CND-0201"
