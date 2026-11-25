from __future__ import annotations

import argparse
import json
import shlex
from datetime import datetime
from pathlib import Path

from .engine import AuditRepository, MatchEngine
from .models import EventType, OfferEvent
from .reporting import allocation_summary, match_summary
from .storage import candidates_from_csv, donors_from_csv, supplied_sample_dataset, transport_from_csv
from .synthetic import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PS-127 deterministic allocation simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("--data-dir", required=True)
    synth = sub.add_parser("generate-synthetic"); synth.add_argument("--output", default="data/synthetic"); synth.add_argument("--seed", type=int, default=127)
    match = sub.add_parser("match", help="Run one donor offer and display an easy-to-read ranking"); match.add_argument("--data-dir", required=True); match.add_argument("--donor", required=True); match.add_argument("--as-of", required=True); match.add_argument("--run-id", default="RUN001"); match.add_argument("--output-dir", default="outputs/match_runs"); match.add_argument("--json", action="store_true", help="Print raw JSON rather than the friendly summary")
    report = sub.add_parser("report", help="Display a saved match-run summary"); report.add_argument("--run-id", required=True); report.add_argument("--output-dir", default="outputs/match_runs"); report.add_argument("--json", action="store_true", help="Print the complete raw audit JSON")
    replay = sub.add_parser("replay", help="Reload a saved result deterministically"); replay.add_argument("--run-id", required=True); replay.add_argument("--output-dir", default="outputs/match_runs"); replay.add_argument("--json", action="store_true", help="Print the complete raw audit JSON")
    offers = sub.add_parser("process-offers"); offers.add_argument("--run-id", required=True); offers.add_argument("--events", required=True, help="JSON event-list path"); offers.add_argument("--output-dir", default="outputs/match_runs")
    command_file = sub.add_parser("run"); command_file.add_argument("--commands", required=True)
    args = parser.parse_args(argv)
    if args.command == "generate-synthetic": generate(args.output, args.seed); print(f"Generated synthetic dataset: {args.output}"); return 0
    if args.command == "validate":
        data_dir = Path(args.data_dir)
        if (data_dir / "hospitals.csv").exists():
            candidates, donors, routes = supplied_sample_dataset(data_dir, datetime(2026, 8, 3, 5)); print(f"\nData check passed.\n  Candidates: {len(candidates)}\n  Donor offers: {len(donors)}\n  Transport routes: {len(routes)}\n  Status: ready for a match run"); return 0
        candidates_from_csv(data_dir / "candidates.csv"); transport_from_csv(data_dir / "transport.csv"); print("Data check passed. Status: ready for a match run."); return 0
    if args.command == "run":
        for line_number, raw in enumerate(Path(args.commands).read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"): continue
            exit_code = main(shlex.split(line))
            if exit_code: print(f"Command file stopped at line {line_number}"); return exit_code
        return 0
    repo = AuditRepository(args.output_dir)
    if args.command in {"report", "replay"}:
        audit = repo.load(args.run_id)
        print(json.dumps(audit, indent=2, sort_keys=True) if args.json else match_summary(audit, str(repo.directory / f"{args.run_id}.json")))
        return 0
    if args.command == "process-offers":
        audit = repo.load(args.run_id)
        raw_events = json.loads(Path(args.events).read_text(encoding="utf-8"))
        events = [OfferEvent(x["candidate_id"], EventType(x["type"]), datetime.fromisoformat(x["at"]), x.get("reason", ""), x.get("category", "NON_MEDICAL"), x.get("event_id", "")) for x in raw_events]
        # Event processing is deterministic and updates the same audit atomically.
        engine = MatchEngine({}, repo); engine.process_events(audit, events); repo.save(audit); print(allocation_summary(audit)); return 0
    data_dir = Path(args.data_dir); as_of = datetime.fromisoformat(args.as_of)
    supplied_pack = (data_dir / "hospitals.csv").exists()
    if supplied_pack: candidates, donors, routes = supplied_sample_dataset(data_dir, as_of)
    else: candidates, donors, routes = candidates_from_csv(data_dir / "candidates.csv"), donors_from_csv(data_dir / "donors.csv"), transport_from_csv(data_dir / "transport.csv")
    donor = next((d for d in donors if d.offer_id == args.donor or d.donor_id == args.donor), None)
    if donor is None: parser.error("donor offer not found")
    engine = MatchEngine(routes, repo, whole_unit_kidney_points=supplied_pack); audit = engine.run(args.run_id, donor, candidates, as_of); path = engine.persist(audit); print(json.dumps(audit, indent=2, sort_keys=True) if args.json else match_summary(audit, str(path))); return 0
