# Traceability matrix

| Business rule | Function/module | Automated coverage | Expected behaviour |
|---|---|---|---|
| BR-01 | `blood_compatible`, `blood_priority` | `test_blood_matrix`, `test_o_kidney_priority` | compatible groups only; identical priority |
| BR-02 | `urgency_and_score` | `test_meld_boundary`, `test_kidney_score` | MELD 35 is super urgent |
| BR-03 | `eligible_waiting_days` | `test_inactive_waiting_period` | inactive days excluded |
| BR-04 | `geographic_tier`, `ischemia_eligible` | `test_ischemia_boundary` | equality is eligible |
| BR-05 | `size_age_eligible` | `test_heart_weight_boundaries` | inclusive weight bounds |
| BR-06 | `RankingEngine._sort_key` | `test_deterministic_tie` | explicit deterministic fallback |
| BR-07 | `OfferEngine`, `penalty_active` | `test_third_refusal_day_365` | third non-medical refusal triggers penalty |
| BR-08 | `MatchEngine.process_events` | `test_backup_at_four_hours` | no rerun at four hours |
| BR-09 | `apply_multi_organ_override` | `test_multi_organ_override` | liver-first candidate receives kidney atomically |
| BR-10 | `status_as_of` | `test_stale_candidate` | stale/inactive skipped |
| BR-11 | `AuditRepository`, `replay` | `test_replay` | canonical result repeats |
| BR-12 | `MatchEngine.run` | `test_exclusion_precedes_ranking` | exclusions precede ranking |
