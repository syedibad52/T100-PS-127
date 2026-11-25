# PS-127 Architecture

## Scope

PS-127 is an offline, deterministic academic simulation. It is not a clinical decision system.

## Layers

`CLI -> services/engine -> rules and policies -> domain models -> CSV/JSON repositories -> audit/reporting`.

The command-line interface only translates input into service calls. The allocation engine owns all ranking and state changes. Policy objects expose provisional interpretations so that official samples can replace them without rewriting the engine.

## Match-run flow

1. Validate donor offer and load the candidate snapshot as of the run time.
2. Filter candidates by requested organ and lifecycle status.
3. Evaluate independent compatibility checks (blood, HLA, size/age, transport/ischemia, consent).
4. Calculate waiting time, urgency, geographic tier, and organ-specific scores.
5. Apply explicit ranking keys: penalty, urgency override, geographic tier, blood priority, score, and BR-06 tie-breaks.
6. Apply eligible multi-organ override atomically.
7. Designate the first three eligible candidates, then simulate supplied offer events.
8. Persist a canonical JSON audit snapshot for replay.

## Reproducibility

No clock or random source is used by a match run. Every timestamp is passed in, event processing is ordered by timestamp and event id, and JSON serialization uses sorted keys. Audit snapshots store inputs, configuration version, ranking, exclusions, outcomes, and rule trace.

## Entities

Candidate has organ registrations, status intervals, clinical data, refusal history and consent. DonorOffer has immutable donor details, available organs, a cross-clamp time, and allocation state. MatchRun stores a candidate snapshot, decisions, offer events and final allocations. Hospitals are referenced by identifiers and a transport matrix is versioned input.

## State transitions

Candidate lifecycle: ACTIVE <-> INACTIVE; ACTIVE/INACTIVE -> DELISTED, TRANSPLANTED, or DECEASED. Terminal statuses cannot be reactivated. Statuses can be organ-specific. Offer events follow OFFERED -> ACCEPTED/REFUSED/TIMEOUT/CROSSMATCH_FAILED/CANCELLED -> ALLOCATED where applicable.

## Provisional schema boundary

CSV parsing is isolated in `storage.py`; it maps provisional fields to models. JSON stores rich histories and audits. Official files can be adapted by changing parsers only.
