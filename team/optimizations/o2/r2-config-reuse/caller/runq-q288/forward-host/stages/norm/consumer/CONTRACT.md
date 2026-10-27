# Optional W2 + RMSNorm consumer v1

Identity: `r2-s3-forward-consumer-w2-norm-v1`; guarded API identity:
`r2-s3-forward-consumer-w2-norm-api-v1`.

This is a reference-correctness candidate, not a default or performance-qualified
application. The existing W2 consumer and the stable firstdot entry remain usable.
No upstream, official AM, NEMU, RTL, frozen experiment or old result is modified.

## Exact change and rollback

Use the qualified W2 consumer source whose consumer.c SHA256 is
`9f1cdab57add8b0088554625a032f0d9c3df98b5046e80fb3f4c8b63e354ec53`
and consumer.inc SHA256 is
`02f6abae8c48977289c8fb21abac8fc90a71a77259bc10644303a14aa1360367`.
Add only norm.h to consumer.c and replace the twelve rmsnorm call sites in the
four optimized forward functions. Reverse both changes to the exact parent.
R2_SCALAR still uses the unchanged upstream forward. FR, TA, FR-cache and
TA-cache all use the same norm policy. Preserve API, state layout, model bytes,
tokens, quantization, RoPE and K288/K768 routing.

Compile that core with the qualified parent's exact compiler arguments, changing
only source/include/output paths. Combine it with frozen candidate.o
`def02af4f87c85ba4ea5ce49cc02938f28afa9fefb69700c2b2a616c3694cb60`
and norm.o
`ef52d03e9691fc20289bf039a3a47dbafc81f1a22b964b2206ca8b55f90d0c4e`
using GNU ld -r --no-relax. All new harnesses link the resulting single
consumer-w2-norm.o without recompiling it. Rollback means linking the original
consumer-w2.o instead; the two complete consumer objects must not be linked
together. The original public consumer.h and consumer_w2.h remain the API.

RMSNorm retains the norm v1 contract: size 288, finite binary32 inputs/weights,
RNE, FS/VS enabled, VLEN128, vstart zero, exact in-place or disjoint output,
read-only disjoint weights. Ordered scalar sum, epsilon, sqrt and reciprocal
remain fixed. Only the two output multiplications use RVV; sticky flags and
VL/VTYPE restoration retain the v1 rules. This does not broaden that domain.

## Static and reference acceptance

Check whole K288/K768 FR/TA function bytes against the qualified W2 ELF and the
whole norm output leaf against the frozen norm ELF. For r2_rmsnorm_rvv, compare
every non-relocation instruction bit, resolve both call targets and both float
constants, and retain exactly the frozen input objects. Each of the four final
optimized functions must contain three calls to r2_rmsnorm_rvv. Upstream forward
must contain none. This is static routing evidence, not a dynamic call count.

Eight independent normal-NEMU reference processes execute negative, scalar, FR,
TA, FR-cache, TA-cache, recovery and replay. Negative runs first, then the five
methods, then recovery/replay. Use at most two isolated CPU slots alongside the
two norm EMUs, keeping the total host CPU budget at four. Each reference case
retains 2 billion API calls, 600 seconds internal / 630 seconds external, and
128 MiB per output file. Reference counters are not target cycle measurements.

Reuse the existing W2 whole-state validator with only its image-path dependency
bound to the new filename. It still checks p0..2 tokens 1/7/19, all 3,691,424
bytes of state per position, final live state, all five complete model buffers,
flags, unused storage and the real final-logit bit-flip rejection at byte152476.
All five methods must have identical scalar flags. Recovery and replay must
match TA-cache's complete validation record. W2 pack-fault qualification is
inherited only for the unchanged parent routing logic; no new pack-fault runs
or p0..255 qualification are claimed for this object.

After these eight cases pass, a distinct guarded API ELF links the exact same
new object. Reuse the existing W2 API harness and full numerical validator;
bind the explicit new build/campaign contracts and filename. Keep 13 rejected
forwards, 5 failed and 6 successful inits, 5 valid forwards, six complete state
pairs, guards and five unchanged models. Expected flags come from the new
eight-case campaign. Function dependency bindings do not mutate parent modules,
old JSON or old source, and do not loosen any numerical or process gate.

All new records state target_emu_runs=0 and performance_qualified=false. A norm
local HOLD or a W2 HOLD is not overturned by this combination. No whole-forward
target throughput, full sequence, model-quality or ASIC claim is made.
