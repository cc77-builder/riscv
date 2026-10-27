# Pure complete forward consumer, version 1

Contract: `r2-s3-forward-consumer-v1`. Base: `7b358d98c95dacf1897fe9169b1f16d6f0ae76d9`.

## Purpose and fixed semantics

Remove observer/oracle work from the actual computation path and validate the
combination of the qualified TA/FR kernels with the RoPE table reuse. The pinned
upstream `runq.c` is unchanged (SHA256
`ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548`).
This is a fixed deterministic, untrained D288/H768/L6/HQ6/HKV6/V32000/S256,
GS32 consumer; there is no trained-model quality claim.

Methods 0..4 are original scalar, FR, TA, FR+cache, TA+cache. All 37 K288
matrices use the same 172 complete Q calls and 13 padded tail blocks. Six
K768 W2 matrices remain original scalar; no regrouping of FP32 accumulation,
FMA, reciprocal substitution, approximate transcendental, or official code
change is permitted. Cache preparation is inside each full forward invocation.

Weights and embeddings are the prior full-build-06 fixtures. Offline packing
is independently reconstructed from the complete 17,101,440-byte weight file.
172 packed blocks (14,266,368 bytes) and 13 tail-scale arrays (134,784 bytes)
are read-only model inputs. This interface assumes a prepacked fixed model;
offline preparation must be reported separately from forward cost. It does
not claim cold model-loading latency or amortization over an unspecified N.

## Shared implementation and ABI

`consumer.h` exposes initialization with exact lengths/alignment, explicit
reset, and an ordinary C full-forward call with caller-owned state. Model
binding is single-instance and immutable after initialization. Separate states
may advance independently; rebinding during calls is unsupported. Each state
must progress through consecutive valid positions from zero.
States must be properly aligned, mutually disjoint and disjoint from model
buffers. Invalid initialization clears the binding and requires a successful
initialization before subsequent calls. Upstream quantize
requires finite, nonzero per-group maxima and representable casts, inherited
from the fixed fixture's validated domain. This is not an arbitrary-checkpoint
loader. Invalid method and out-of-range token/position return NULL without
executing a forward; the caller, not the interface, enforces position sequence.

Every normal validation/performance path links the exact same `consumer.o` and
FR/TA functions. The core contains no reference recomputation, guard loop,
CSR/timing read, trace, snapshot, comparison, or application-negative hook.
Validation is performed outside the call using complete independent states.
The four derived functions are mechanically reversed to the complete original
forward text, with only routing and the existing exact cache transformation.

Hardware is unchanged T17 (`ff840528...10e30f`) with the pinned normal NEMU
reference and original AM/libm. RV64 LP64D, VLEN128, RNE, FS/VS enabled;
the software calls have variable latency and no new clock/reset/interface
or hardware throughput claim. Existing O2 II=1/first-response=2 remain
historical hardware qualifications, not new complete-forward measurements.

## Required new validation

1. Exact source/fixture/tool/ELF identity and complete FR 592-byte / TA
   764-byte function equality to the accepted previous ELF.
2. Five independent actual reference processes, one per method, each naturally
   executing token sequence `[1,7,19]` at p0..2 from zero state. Compare all
   3,691,424 state bytes for each position against prior independent upstream
   host gold, including 32,000 logits, both full KV caches and scratch spans.
3. Complete model/packed/tail-scale bytes remain unchanged. RNE, TLS guards,
   errno, flags, terminal state, distinct process receipts, and reference ABI
   are validated. Counters under standalone NEMU are not XiangShan cycles.
4. Real application negative flips bit0 of the last logit's actual live state
   after p0, saves that state, and terminates with code94. The validator must
   prove exactly that one-byte XOR and untouched later snapshots. Recovery and
   independent replay must reproduce the same full raw states and flags.
5. API misuse and object/source identity controls must reject actual bad input;
   no unrelated regression or unchanged RTL rebuild is required.

Optional longer runs use the same first three tokens then `(p*17+5)%32000`,
with selected complete states p0,1,2,31,127,255. They require new original-host
gold naturally advanced from p0, explicit run limits, and actual completion.
No long-position qualification is inferred from the three-position result.

## Target cost decision

After new reference qualification, inspect target CLI and run a bounded
new-identity cost probe if feasible. Fix wall/cycle/log limits before launch;
preserve timeout, partial output, and last real progress. A partial probe
provides execution cost observations only. Complete-forward DiffTest and
performance require terminal success and complete output/counter evidence.
Any performance comparison uses a matched strong FR path, the same cache
policy, weights/state/ELF and execution conditions; local historical gains
are neither transferred nor multiplied. No R5 default change in this leaf.

All build/run outputs are outside the source tree. Existing official files,
frozen sources, failures, and dependent Git object stores remain unchanged.
This leaf uses at most four total CPUs; reference processes may run in
isolated slots and performance samples must have comparable resource policy.
Runtime source bytes are snapshotted before launch. Campaign ownership is not
released merely because a launcher exits: both its process group and the
independently grouped reference child require a terminal receipt and an actual
absence check. Missing/incomplete receipts remain explicitly cleanup-unknown.
