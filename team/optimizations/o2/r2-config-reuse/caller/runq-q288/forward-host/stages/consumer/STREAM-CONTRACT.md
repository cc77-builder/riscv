# Bounded O2 streaming audit, version 1

Identity: `r2-s3-consumer-stream-audit-v1`. The original team auditor
`team/optimizations/o2/fullcore/analyze.py` remains byte-for-byte unchanged at
SHA256 `27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496`.
No official reference, validator, RTL or frozen input is changed.

The new auditor reuses the original strict field parser, pointer-age relation,
full128 arithmetic oracle and coverage calculation. Its cycle state machine
retains the same validation predicates/order: commit by ROB age, cancellation,
allocation, then complete P/R/DIV transitions. It consumes complete cycles and
rejects cycle reversal. Unknown, malformed, duplicate, missing or truncated
events and unsupported reset epochs continue to reject. A partial run retains
partial status, live requests and unfinished allocations; it cannot earn a
complete-run or performance qualification.

Storage changes only: keep one cycle; signatures are local to that cycle;
retain at most the 96 flag:index ROB keys and pending ordered VDot requests;
fold finalized ROB history when safely reused; accumulate histograms and emit
an ordered canonical JSON transaction SHA256. DIV sequence gaps and dual kills
use actual VDot acceptance order, not `seq+1`. Stalls are counted while every
observed stalled packet is still checked for identity, full data and stability.
The small-fixture compatibility helper alone collects a transaction list.

All original raw log bytes remain available. Parsing views are opened in the
same order as the prior target auditor: independently newline-normalized
stderr, then stdout. Known O2 records may interrupt UART text; residual bytes
are reconstructed before the original T13/UART allowlist check. Raw T13 match
rows are also retained separately for the original counter-chain semantics.
The SHA of normalized parsing text is distinct from each raw file's byte SHA.

This consumer-specific profile additionally bounds a physical line to 65,536
characters, a cycle to 4,096 records, non-O2 residue to 16 MiB, raw T13 rows
to 4,096 and the ordered transaction-completion backlog to 4,096. A completed
younger kill can wait behind an older stalled transaction, so this backlog is
not falsely assumed to equal the two hardware slots. Exceeding a bound rejects
the input; it never truncates or drops it.
These are explicit limits for this consumer audit profile. Actual validated
logs must fit within them; a future complete forward log has not yet been
qualified. They do not claim unrestricted interchangeability with every
possible legacy logging workload.

Required qualification: run the unchanged original directed test suite with
new/old acceptance and complete-result comparisons; test fragmented records,
UART interruption, non-ASCII residue and separate-file newline boundaries;
then process frozen actual positive and negative logs and compare all protocol
summary fields and every ordered transaction with the original saved result.
Measure actual peak RSS/time. A memory improvement is an observed engineering
result only after this differential verification, not an untested estimate.
