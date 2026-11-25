# Decision log

| ID | Rule | Ambiguity | Temporary choice | Confirmation |
|---|---|---|---|---|
| DL-01 | BR-01 | Paediatric/zero-HLA O-kidney exception precedence | identical O first, then paediatric or zero-HLA compatible candidates, then other compatible candidates; isolated policy | pending |
| DL-02 | BR-02 | Kidney point rounding | retain full precision; `kidney_round_digits` policy controls output | pending |
| DL-03 | BR-04 | Regional geography | any valid route outside same zone is Tier 4 | pending |
| DL-04 | BR-07 | 12 months | 365 rolling days inclusive, so day 365 counts | pending |
| DL-05 | BR-07 | Deadline equality | event at deadline is timely; later is timeout | pending |
| DL-06 | BR-07 | Repeat penalties | qualifying new third-refusal sequence extends penalty from latest qualifying event | pending |
| DL-07 | BR-08 | Four-hour clock | measured from match-run timestamp; exactly four hours does not rerun | pending |
| DL-08 | BR-08 | Backup acceptance and crossmatch | accepted backup allocates only after supplied crossmatch pass; failures advance in original ranking | pending |
| DL-09 | BR-06 | Complete tie fallback | candidate ID ascending is a visible configurable fallback and is recorded | pending |
| DL-10 | BR-12 | Penalty scope | demoted after eligible non-penalized candidates, regardless of tier; configurable | pending |
| DL-11 | Sample pack | Sample-schema conventions | Adapter uses supplied hospital/history/refusal schemas; command event stream is retained unchanged | confirmed for ingestion |
