# PS-127 – Organ Transplant Waitlist Allocation Engine with Urgency Scoring, Compatibility and Geography — Sample Data Pack

Prepared by 10 SECONDS for Team T100.

## Files

| File | What it holds | Row count |
|---|---|---|
| `hospitals.csv` | 12 transplant hospitals with city and zone | 12 data rows |
| `transport_matrix.csv` | Transport minutes between every pair of hospitals (144 rows) | 144 data rows |
| `candidates.csv` | 250 waitlisted candidates (kidney, liver, heart, 5 liver+kidney) | 250 data rows |
| `status_history.csv` | Past INACTIVE periods (excluded from waiting time) | 24 data rows |
| `refusal_history.csv` | Earlier refusals within the last 12 months | 2 data rows |
| `donor_offers.csv` | 20 organ offers from deceased donors with cross-clamp time | 20 data rows |
| `commands.txt` | ~300 clinical updates, status changes, match runs, responses, timeouts, cross-match results and prints | 350 command lines (excluding comments) |

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with 2 places (no commas, no symbol); percentages as plain numbers (12.5 means 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix. An empty cell means "not applicable" and is only allowed where the notes say so.

### `hospitals.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| hospital_id | string | HSP-nn | — | — |
| hospital_name | string | — | — | — |
| city | string | — | — | tier 2 = same city |
| zone | enum | — | SOUTH, WEST, NORTH | tier 3 = same zone; tier 4 = rest of region |

### `transport_matrix.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| from_hospital_id | string | — | hospitals.csv | donor hospital |
| to_hospital_id | string | — | hospitals.csv | candidate hospital |
| transport_minutes | int | min | — | 0 for the same hospital |

### `candidates.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| candidate_id | string | CND-nnnn | — | — |
| candidate_name | string | — | — | — |
| gender | enum | — | M, F | — |
| dob | date | — | — | age at run time; < 18 = paediatric |
| organs | string | semicolon list | KIDNEY, LIVER, HEART | LIVER;KIDNEY = multi-organ |
| blood_group | enum | — | O, A, B, AB | — |
| hla_typing | string | 6 antigens ;-separated | — | 2 x HLA-A, 2 x HLA-B, 2 x DRB1 |
| weight_kg | decimal | kg | — | — |
| hospital_id | string | — | hospitals.csv | — |
| listing_ts | timestamp | — | — | waiting time start (see prior_* columns) |
| status | enum | — | ACTIVE, INACTIVE | status at pack start |
| meld | int | 6-40 | — | liver only |
| heart_status | int | — | 1, 2, 3 | heart only |
| dialysis_start | date | — | — | kidney only; empty = not on dialysis |
| consent_older_donor | bool | — | — | accept donors over 60 when under 40 |
| last_clinical_update | timestamp | — | — | > 90 days before a run = STALE |
| prior_transplant_date | date | — | — | relisted candidates only |
| original_listing_ts | timestamp | — | — | relisted candidates only |

### `status_history.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| candidate_id | string | — | candidates.csv | — |
| status | enum | — | INACTIVE | — |
| from_date | date | — | — | inclusive |
| to_date | date | — | — | inclusive |
| reason | string | — | — | — |

### `refusal_history.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| candidate_id | string | — | candidates.csv | — |
| refusal_date | date | — | — | — |
| offer_ref | string | — | — | external offer reference |
| reason_type | enum | — | MEDICAL, NON_MEDICAL | — |
| reason | string | — | — | — |

### `donor_offers.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| offer_id | string | OFR-nnn | — | — |
| donor_id | string | DNR-nn | — | one donor may offer several organs |
| organ | enum | — | KIDNEY, LIVER, HEART | — |
| donor_blood_group | enum | — | O, A, B, AB | — |
| donor_hla_typing | string | — | — | — |
| donor_age | int | years | — | — |
| donor_weight_kg | decimal | kg | — | — |
| donor_hospital_id | string | — | hospitals.csv | — |
| cross_clamp_ts | timestamp | — | — | cold-ischemia clock start |

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands must be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. An argument written as `-` means "not applicable". Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `CLINICAL_UPDATE` | `candidate_id|ts|field|value` | field MELD, HEART_STATUS or WEIGHT; any update refreshes last_clinical_update |
| `STATUS_CHANGE` | `candidate_id|ts|new_status` | ACTIVE, INACTIVE, DELISTED, DECEASED |
| `MATCH_RUN` | `offer_id|run_ts` | Rank compatible candidates for the offer at run_ts; the first offer goes out at run_ts |
| `OFFER_RESPONSE` | `offer_id|candidate_id|ts|response` | ACCEPT, REFUSE_MEDICAL or REFUSE_NON_MEDICAL |
| `TIMEOUT` | `offer_id|candidate_id|ts` | No response in the window (60 min first offer, 30 min after) — counts as a non-medical refusal |
| `CROSSMATCH` | `offer_id|candidate_id|ts|result` | POSITIVE = incompatible (fail), NEGATIVE = proceed |
| `PRINT_MATCH_RUN` | `offer_id` | — |
| `PRINT_OFFER_LOG` | `offer_id` | — |
| `PRINT_AUDIT` | `from_date|to_date` | — |

## Planted scenarios

Every edge case in the brief, mapped to the exact record where it occurs, followed by extra traps.

- **EC-01 Two candidates with identical score, mismatches and age**
  - OFR-006 (A donor at HSP-07): CND-0091 and CND-0092 — same hospital (tier 1), blood group, waiting/dialysis points, HLA mismatches and age (45) — identical score; the earlier listing timestamp (2024-03-11 09:00:00 vs 2024-03-11 14:30:00) ranks CND-0091 first — `candidates.csv row 91, candidates.csv row 92; run commands.txt line 106`
- **EC-02 MELD exactly 35**
  - CND-0100 (liver, HSP-06 Mysuru, MELD exactly 35 = SUPER_URGENT): for donor DNR-05 at HSP-05 (same city, tier 2) the super-urgent override puts it above every non-super-urgent candidate, including tier-1 ones — `candidates.csv row 100; commands.txt line 130`
- **EC-03 Transport time making the cold-ischemia limit exact**
  - OFR-005 (heart, cross-clamp 2026-08-17 03:00:00, match run 95 min later): CND-0228 at HSP-05 is 145 min away -> 95 + 145 = exactly 240 min = the heart cold-ischemia limit (not breached); CND-0178 at HSP-07 is excluded (limit breached) — `transport_matrix.csv row 5 (from HSP-01); candidates.csv row 228`
- **EC-04 Candidate inactive for part of the waiting period**
  - CND-0087 (kidney, listed 2024-01-15): INACTIVE 2024-09-01 to 2025-02-28 (181 days) — excluded from waiting time — `status_history.csv row 10`
- **EC-05 Donor weight at exactly 70% of heart candidate weight**
  - CND-0035 (heart, 80.00 kg): donor DNR-02 weighs 56.00 kg = exactly 70% — inside the 70–130% window — `candidates.csv row 35; commands.txt line 30`
- **EC-06 Third non-medical refusal on the 365th day after the first**
  - CND-0002: non-medical refusals on 2025-09-12 and 2026-02-03 (refusal_history), and a third NON_MEDICAL refusal on 2026-09-12 = 365 days after the first — whether that is 'within 12 months' decides the 90-day drop to the bottom — `refusal_history.csv row 1; commands.txt line 191`
- **EC-07 Backup receiving the organ at exactly 4 hours elapsed**
  - OFR-010: primary CND-0001 accepts but cross-match is POSITIVE at exactly 4 h after the match run; backup CND-0036 receives the organ without a re-run (only MORE than 4 h forces a re-run) — `commands.txt lines 217, 218, 219, 220`
- **EC-08 Multi-organ candidate ranked 1 for liver and 50 for kidney**
  - CND-0201 (listed LIVER;KIDNEY, MELD 40, HSP-05, same zone as the donor): donor DNR-01 (B, HSP-01) — rank 1 on the liver run OFR-001 and rank 50 on the kidney run OFR-002; the life-saving-organ override gives both organs to this candidate — `commands.txt lines 2, 3, 4`
- **Extra traps (not in the brief, but realistic):**
  - CND-0101: last clinical update 120 days before the first run — STALE, skipped until updated — `candidates.csv row 101`
  - CND-0242: transplanted 2026-06-01, relisted 2026-07-20 (49 days, graft failure) — keeps the original 2023-03-01 waiting time; CND-0246 relisted 130 days after transplant — waiting time restarts — `candidates.csv row 242, candidates.csv row 246`
  - Donor DNR-08 is 66: CND-0174 (31, no consent) is excluded; CND-0177 (34, consent_older_donor = true) stays — `candidates.csv row 174, candidates.csv row 177`
  - Donor DNR-09 is 14 (paediatric): paediatric candidates such as CND-0153 (age 11) are offered first — `candidates.csv row 153; commands.txt line 268`
  - CND-0236 is INACTIVE — skipped in every run but keeps its position — `candidates.csv row 236`

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these CSV files (header row, same conventions as above, rows sorted as stated). Where the brief is silent on a format detail the choice below is binding for evaluation.

### `match_runs.csv`

One row per candidate considered per run (excluded ones too), in rank order then excluded.

Columns, in order: `offer_id`, `run_ts`, `rank`, `candidate_id`, `tier`, `blood_match`, `urgency`, `waiting_days`, `dialysis_points`, `hla_mismatches`, `hla_points`, `score`, `exclusion_reason`

### `offer_log.csv`

One row per offer sent, in time order.

Columns, in order: `offer_id`, `seq`, `candidate_id`, `offered_ts`, `deadline_ts`, `outcome`, `outcome_ts`, `penalty_applied`

### `allocation_audit.csv`

One row per offer.

Columns, in order: `offer_id`, `donor_id`, `organ`, `allocated_to`, `allocation_basis`, `run_ts`, `allocation_ts`, `reran`

Binding choices: waiting days = whole days from the waiting-time start date to the run date minus inactive days (inclusive ranges); kidney points use whole 30-day / 90-day units (floor); HLA mismatches = donor antigens absent from the candidate's typing (0–6). Cold-ischemia check: (run_ts - cross_clamp_ts) + transport_minutes must not exceed the limit. `exclusion_reason` BLOOD, SIZE, AGE, ISCHEMIA, INACTIVE, STALE, REMOVED or empty; `allocation_basis` RANKED, BACKUP, MULTI_ORGAN, NONE; `outcome` ACCEPT, REFUSE_MEDICAL, REFUSE_NON_MEDICAL, TIMEOUT, CROSSMATCH_FAIL.
