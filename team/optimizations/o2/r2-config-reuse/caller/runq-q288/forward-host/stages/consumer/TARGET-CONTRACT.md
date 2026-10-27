# Shared-object API and full-forward target contract v1

Identity: `r2-s3-forward-consumer-target-v1`. This is a new input and observation
profile. Earlier projection-boundaries-v1 and its full O2-log requirement stay
unchanged; their local timing results are not transferred to complete forward.

## Exact implementation and scope

Link the actually reference-qualified `consumer.o` without recompilation.
Retain the complete qualified FR/TA machine-code bytes. Official AM, libm, T17
EMU, normal NEMU and DiffTest remain unmodified. A separate caller provides
the previously validated TLS entry and original AM UART implementation; there
is no official-startup patch or emulated UART-success workaround.

The API harness uses two disjoint guarded states under one immutable model.
It exercises uninitialized/range/null rejection, invalid-init fail-closed and
reinitialization, then A=TA_CACHE p0, B=FR_CACHE p0, A p1, reset B, B p0, A p2.
Six paired complete snapshots must equal independent original-host gold or
all-zero reset state as appropriate. Both guards, full final live states and
all model bytes must remain valid. A nonoverlap precondition is not claimed as
an automatically detected error; model content/packing identity is checked by
the build and runtime wrapper, not by `r2_consumer_init()` itself.

## Target call and validation

Target methods are strong FR+cache and TA+cache. A fresh process naturally
executes one complete p0/token1 call from zero state, same ELF and addresses,
same prepacked model, no prewarm. Only explicit method/negative/UART data words
may differ. Initialization/model binding and model loading are outside timing;
the full call's Transformer/state binding, cache preparation, quantization,
all 172 Q calls, tail copy, all W2 and remaining Transformer math are inside.
The four cycle/instret reads have IORW fences on both sides, decoded from the
actual final ELF. Post-call validation/UART are outside the interval.

Every one of the 3,691,424 state bytes must equal the embedded independent
original-host p0 state, including all logits, full KV and scratch. An exact
word comparison covers the whole state; it reports the first differing byte.
The negative flips bit0 of the actual last logit and must reject byte152476
with code94. In standalone-reference qualification only, UART is disabled by
an explicit image data control because the fixed reference alone faults on
UART. This does not modify the consumer or skip any reference instruction.
The actual target enables UART and requires the original complete DiffTest.

## Runtime profile, bounds and claims

Before starting a target run, record exact CLI, image/input hashes, affinity,
seed, RAM, maximum cycles, wall time and per-file size. A short cost probe may
use a smaller cycle budget; it remains partial unless it actually finishes.
No `--no-diff`, modified validator, removed fatal check or official patch is
permitted. CLI log-range controls may suppress optional debug printing only
after their implementation is checked; the effective profile is recorded.
Raw output produced by that profile is retained in full. A low-log execution
does not inherit an unobserved O2 protocol or counter-enqueue/retire audit.

Require unique canonical GOOD TRAP, complete application transcript and whole
state PASS, original reference initialization, no fatal/error markers, exact
process receipts and unchanged inputs for a complete DiffTest result.
Counter values without an actual matching observer chain are explicitly
reported-only, not the previously qualified counter-sample/retire profile.
A performance claim additionally requires matched resource/profile conditions,
actual counter validation and independent repeatability; never infer it from
host elapsed time, standalone-reference counters, a partial probe or old local
gains. First-token cost does not establish steady-state token/s, arbitrary
sequence performance, model-loading amortization or trained-model quality.

Use no more than four CPUs in total, isolated output/cwd and process groups.
Freeze inputs while running. A missing terminal receipt remains unresolved;
partial/failed evidence is preserved, never rewritten into a completed run.
