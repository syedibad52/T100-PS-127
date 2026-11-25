# Business-rule registry

| Rule | Implementation | Status |
|---|---|---|
| BR-01 Blood compatibility | `rules.py:blood_compatible`, `RankingEngine` | implemented |
| BR-02 Organ urgency | `rules.py:urgency_and_score` | implemented |
| BR-03 Waiting time | `rules.py:eligible_waiting_days` | implemented |
| BR-04 Geography/ischemia | `rules.py:geographic_tier`, `ischemia_eligible` | implemented |
| BR-05 Size/age | `rules.py:size_age_eligible` | implemented |
| BR-06 Tie breaking | `RankingEngine._sort_key` | implemented |
| BR-07 Offers/refusal penalty | `OfferEngine`, `rules.py:penalty_active` | implemented |
| BR-08 Primary/backups | `MatchEngine.process_events` | implemented |
| BR-09 Multi-organ | `MatchEngine.apply_multi_organ_override` | implemented |
| BR-10 Status management | `rules.py:status_as_of` | implemented |
| BR-11 Audit/replay | `AuditRepository`, `MatchEngine.replay` | implemented |
| BR-12 Precedence | `MatchEngine.run` ordered pipeline | implemented |

All implementations are provisional until official samples are supplied and compared.
