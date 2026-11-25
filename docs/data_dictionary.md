# Provisional data dictionary

| Dataset | Field | Type | Required | Validation/example |
|---|---|---|---|---|
| candidates | candidate_id | string | yes | unique, `C001` |
| candidates | organs | JSON/string list | yes | `KIDNEY;LIVER` |
| candidates | blood_group | enum | yes | O, A, B, AB |
| candidates | hla | string/list | yes | six validated loci, `A1,A2,B1,B2,DR1,DR2` |
| candidates | age / weight | int / decimal | yes | age >= 0, weight > 0 |
| candidates | hospital/city/zone | string | yes | known hospital reference |
| candidates | listing_at | ISO datetime | yes | timezone-naive ISO accepted provisionally |
| candidates | status history | JSON list | yes | timestamped non-overlapping intervals |
| candidates | meld / heart_status / dialysis_days | numeric | organ specific | MELD 6-40; heart 1-3; days >= 0 |
| donors | donor_id / offer_id | string | yes | unique identifiers |
| donors | organ / blood_group | enum | yes | KIDNEY/LIVER/HEART; O/A/B/AB |
| donors | cross_clamp_at | ISO datetime | yes | valid timestamp |
| transport | from/to/duration_minutes | string/string/int | yes | duration >= 0 |
| events | run_id/candidate_id/type/at | values | yes | event time ordered during processing |

All input formats are provisional, labelled synthetic, and replaced/adapted when official schemas arrive.

## Supplied sample pack

`data/sample/` contains the received evaluation-style source CSV files unchanged. `supplied_sample_dataset()` adapts `hla_typing`, date-of-birth, hospital IDs, historical inactive ranges, refusals, donor-offer fields, and the transport matrix into the engine's domain models. The source `commands.txt` stays separate so its ordered clinical and status changes can be replayed without altering raw input.
