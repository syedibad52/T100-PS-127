# Design Document - PS-127

## Abstract

This project implements a transparent, deterministic, offline simulation of deceased-donor organ allocation for kidney, liver and heart waitlists. It records why candidates are eligible, excluded, ranked, offered or allocated. It is educational software, not clinical software.

## Objectives and requirements

The system maintains historical candidate status, validates donor offers, calculates organ-specific urgency and waiting time, assesses compatibility and geography, simulates offered outcomes, supports an atomic liver-kidney override, and creates reproducible audit files. Non-functional requirements are determinism, readable Python 3.10+ code, offline operation, safe validation and CSV/JSON portability.

## Architecture diagram

```text
CSV / JSON input -> Storage adapter -> Typed models -> Rules/policies
                                                   -> Match + offer engine -> JSON audit -> CLI reports
```

## Entity relationships

```text
Candidate 1 --- * StatusInterval
Candidate 1 --- * Refusal
DonorOffer 1 --- * MatchRun decision / OfferEvent
MatchRun 1 --- * Decision and allocation audit entries
Hospital * --- * Hospital through TransportRoute
```

## Match-run flow

```text
validate -> status -> blood/size/age/ischemia exclusions -> score + tier
-> urgency override -> stable ranking + BR-06 ties -> multi-organ policy
-> primary/backups -> supplied offer events -> audit snapshot
```

## State and offer sequence

Candidate states are ACTIVE, INACTIVE, DELISTED, TRANSPLANTED, DECEASED and STALE. A clinical update removes only staleness; it never implicitly reactivates an independently inactive or terminal registration. The first offer window is 60 minutes; subsequent windows are 30 minutes. The simulation uses event timestamps rather than real-time waits.

## Rule precedence and scoring

The implementation follows BR-12: exclusions, status skips, tier-limited urgency override, tier ordering, organ score, BR-06 ties, multi-organ policy, then offer events. Kidney score is waiting days/30 + dialysis days/90 + (6 - HLA mismatches). Liver MELD >= 35 is super urgent. Heart status 1 ranks above 2 and 3. Waiting-time spans are merged to avoid double counting and inactive intervals are not included.

## Validation and testing

Models reject invalid blood groups, HLA cardinality, malformed scores, bad weights and invalid status spans. CSV readers reject duplicates and missing required fields. The test suite covers all stated edge cases represented by provisional policy, core boundaries, determinism and replay. See the traceability matrix for direct test mapping.

## Limitations

Official data formats, transport semantics, precise event-file syntax, and ambiguous policy interpretations are pending confirmation. See the decision log. The optional dashboard is intentionally deferred.
