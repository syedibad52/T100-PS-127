# T100-PS-127

## Organ Transplant Waitlist Allocation Engine

Academic capstone project for **PS-127** at Atria Institute of Technology (ISE D).

This repository will contain a deterministic, command-line organ-allocation simulation. It is **not** a clinically validated or production medical system.

## Official sample data

The supplied evaluation inputs are preserved verbatim in [`data/official`](data/official):

- `candidates.csv` — 250 transplant candidates
- `donor_offers.csv` — 20 deceased-donor organ offers
- `hospitals.csv` and `transport_matrix.csv` — hospital geography and transport times
- `status_history.csv` and `refusal_history.csv` — historical candidate events
- `commands.txt` — ordered simulation command stream
- `README.md` — original data-pack schema, scenarios, and evaluation output contract

Do not modify files in `data/official`. Generated files, audits, and future synthetic test data must be stored separately.

## Current scope

The repository currently holds the official sample data only. Implementation will follow the supplied specification after unresolved allocation-policy decisions are confirmed.

## Team

- SHARATHKUMAR — 1AT24IS175
- SHASHIDHAR TIWARI — 1AT24IS176
