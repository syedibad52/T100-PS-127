# T100-PS-127 - Organ Transplant Waitlist Allocation Engine

An offline, deterministic academic simulation of regional deceased-donor allocation. It is not clinically validated and must never be used for real transplant decisions.

## Team

- Sharathkumar - 1AT24IS175
- Shashidhar Tiwari - 1AT24IS176
- Section ISE D

## Features

- Organ-specific candidate records, lifecycle history, waiting-time arithmetic and validation.
- Blood, HLA, age/size, transport and cold-ischemia compatibility explanations.
- Kidney, liver and heart scoring; geographic tiers and eligible urgent overrides.
- Explicit deterministic ranking and visible candidate-ID tie fallback.
- Primary plus two backups, event-driven offer logs, timeouts and refusal-penalty policy.
- Atomic liver-kidney allocation when the top liver candidate is eligible for both organs.
- CSV input, canonical JSON audit snapshots and replay retrieval.

## Install and run

Python 3.10+ is required. The engine itself uses the standard library; pytest is required for tests.

```powershell
python -m pip install -r requirements.txt
python main.py generate-synthetic --output data/synthetic --seed 127
python main.py validate --data-dir data/synthetic
python main.py match --data-dir data/synthetic --donor SYN-O001 --as-of 2026-11-25T10:00:00 --run-id DEMO001
python main.py report --run-id DEMO001
python -m pytest -v
```

## Layout

`src/allocation_engine` contains the typed models, policies, engine, storage adapter, synthetic generator and CLI. `tests` contains business-rule and edge-case tests. `docs` contains the architecture, registry, traceability matrix, decisions, data dictionary, design document, demo and viva preparation. `data/synthetic` is labelled development-only data. `outputs/match_runs` holds generated, reproducible audit artifacts.

## Supplied sample data

The provided PS-127 sample pack is preserved unchanged in `data/sample/`, including its 250 candidates, 20 donor offers, hospitals, routes, histories and ordered command stream. The CLI automatically detects this schema:

```powershell
python main.py validate --data-dir data/sample
python main.py match --data-dir data/sample --donor OFR-001 --as-of 2026-08-03T05:00:00 --run-id SAMPLE_OFR001
```

The adapter derives age, hospital geography, dialysis duration, historical inactive intervals, refusal history and same-donor available organs. The supplied command stream is retained as the integration fixture; processing its clinical/status update events is the next adapter extension.

Terminal commands now show a plain-English result by default: donor details, primary and backup candidates, top five rankings, score explanation and exclusion reasons. Add `--json` to `match`, `report`, or `replay` only when you need the full detailed audit file.

## Official sample status

Official files and expected outputs have not been supplied. The CSV schema, policy settings and outputs are therefore provisional. Do not claim official-format compatibility until visible official runs have been compared without modifying their expected output.

## Known limitations / next steps

The supplied policy deliberately documents unresolved interpretation choices. Event-file parsing, candidate registration/update commands, cross-match file ingestion, and official schema regression adapters await the official files. The optional dashboard has not been implemented because mandatory CLI correctness takes priority.
