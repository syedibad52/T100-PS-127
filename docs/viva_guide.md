# Viva Guide

## Short answers

1. **Why this system?** It makes allocation rules transparent and reproducible for academic simulation.
2. **Why Python?** Typed dataclasses and the standard library keep it readable and offline.
3. **Why CSV and JSON?** CSV is easy for tabular import; JSON preserves nested history and audits.
4. **What is blood compatibility?** Donor and recipient groups must follow BR-01's directed matrix.
5. **What is HLA matching?** The engine counts position-wise mismatch across six supplied loci.
6. **What is MELD?** The supplied liver urgency score; 35 or above is super urgent here.
7. **What is cold ischemia?** Time from cross-clamp to projected arrival; it has organ-specific limits.
8. **Why exclude inactive time?** It implements BR-03's eligible waiting entitlement.
9. **What is deterministic sorting?** Every key is explicit; final equal ties use documented candidate ID.
10. **Why no random selection?** The same inputs must reproduce the same audit.
11. **Why geography tiers?** They express hospital, city, zone, then regional priority.
12. **What triggers a refusal penalty?** Three qualifying non-medical refusals in 365 days.
13. **What does stale mean?** No clinical update for more than 90 days; the candidate is skipped.
14. **What are backups?** The second and third eligible ranked candidates.
15. **What is multi-organ atomicity?** Both organs are recorded together or no partial secondary allocation occurs.
16. **Why inject timestamps?** It enables repeatable historical runs and tests.
17. **How are errors handled?** Validation raises meaningful errors before data reaches ranking.
18. **Why a rule trace?** It lets an examiner relate every decision to BR-01 through BR-12.
19. **What does a snapshot contain?** Candidate inputs, donor, transport version, decisions, events and allocations.
20. **How does replay work?** It loads the canonical persisted run audit.
21. **What is the kidney formula?** Waiting/30 + dialysis/90 + 6 minus mismatches.
22. **What happens on missing transport?** The candidate is excluded; missing is never treated as zero.
23. **Are boundary values included?** Yes: exact ischemia and size limits are eligible.
24. **Why separate storage?** Official parser formats can change without changing domain logic.
25. **What is a policy ambiguity?** A rule interaction not specified by the assignment; it is recorded, not hidden.
26. **How are duplicates stopped?** CSV adapters reject duplicate candidate and offer IDs.
27. **What is the main complexity?** Sorting eligible candidates is O(n log n); compatibility pass is O(n).
28. **Why no dashboard first?** The evaluation prioritizes correctness over appearance.
29. **Can this make clinical decisions?** No, it is explicitly an academic simulation.
30. **What remains before final submission?** Validate official samples, broaden command-file ingestion, and compare visible expected outputs.

## Practice exercises

Member 1: change the kidney point rounding policy, add a boundary test, then run `python -m pytest -v`.

Member 2: add an official CSV column mapping in `storage.py`, generate an audit, and compare its ranking with a confirmed expected output.
