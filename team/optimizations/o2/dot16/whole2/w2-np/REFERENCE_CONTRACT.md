# Fixed K768 N/P reference campaign v1

Scope: M=288, K=768, GS=32, VLEN=128, RV64/lp64d, enabled FS/VS,
RNE. The 56-byte context and offsets 0/8/16/24/32/40/48 are unchanged.
Packed W is [36][24][8][32] (221184 bytes), row-major scales are [288][24],
X has 768 signed bytes and 24 FP32 scales; output is all 288 FP32 values,
slots are eight complete 128-bit values. Inputs and outputs are disjoint.
Every call retains the original per-group INT32 conversion, multiply Ws,
multiply Xs, then left-fold add, with no FMA. Kernels return vl=8, vtype=0,
vstart=0, and fixed profile vcsr=7. This is not arbitrary-vcsr preservation.

## Inputs and exact implementation

Consume the completed K768_N_P_GNU_GEOMETRY_VERIFIED stage. Reassemble the
actual w2_np.S and verify the complete final executable functions against
the independent GNU stage: N 312 bytes, P 1096 bytes including guard and
full fallback. No instruction/label patching occurs during this campaign.
The existing Q288 runtime qualification does not qualify these functions.

Use the existing real W2 build-06 fixture at position2/layer5. Its result,
eight fixture files and original main/scalar/entry/header/Makefile/upstream
sources are fixed by SHA. Reuse the already captured gold; do not rerun the
three-position host exporter. The original scalar includes the unchanged
authoritative upstream matmul. Official AM sources and libraries remain
read-only and original make uses -o am -o klib with fresh objects/output.

The team-owned new main is an inverse-checked four-edit derivation: declare
N/P and immutable expected_flags, select P/N in the existing method1/2
branches, and replace both literal FCSR=1 checks with that fixture's exact
expected word. Keep 0xa5 output/slot initialization, all byte comparators,
guards, vector CSR checks, two control words, report format, negative flip
at output byte1148, and nine-call order 0,1,2,2,1,2,1,1,2. Method0 is scalar.
Each normal case performs nine warm and nine measured functional calls.
Counter values in NEMU do not measure XiangShan performance.

## Whole fixture sets and four independent runs

normal/replay/negative use the exact frozen real input, W, packed W, input
scales, weight scales, full gold, full slot gold and expected-flags=1. The
real X has no -128; this is the intended P fast-path input domain.

edge uses wholly zero X and row-major W, except X[751]=X[767]=-128 and
W[287][751]=W[287][767]=-128. All input and weight scales are binary32 +1.
Packed W is freshly derived from the whole row-major matrix by the original
index formula; its only nonzero bytes are offsets221167 and221183. Expected
outputs0..286 are +0, output287 is32768.0 (0x47000000). Only the last of eight
INT32 slot low words is32768 (0x00008000); all high96 bits are zero. The exact
FCSR is0. Two16384 pair products overflow signed16 if an old nine-group guard
misses this tail group. This checks that boundary, not an instruction trace
proof of every guard lane or an arbitrary-input-domain proof.

Run exactly negative, normal, replay, edge in fresh independent processes.
negative must reject with BAD/code91 at the actual compiled reject site and
exact output byte1148; accept no arbitrary nonzero exit. normal/replay/edge
must GOOD/code0 at the actual compiled success trap, with no recorded
exception. Verify whole ELF/raw BIN, immutable fixture spans, all output/
slot bytes and guards, report extent, exact sample order/FCSR/FNV, and
complete 1400-byte register and32768-byte CSR dumps. normal/replay validation
objects must agree exactly. Every case selects one complete fixture set
from the external fixed plan, never from DUT output. Each image is checked
against its unique deterministic full byte construction, not just allowed
difference locations. All declared fixture/control ranges are disjoint.

Reuse the entire existing team W2 validate function, extracted without its
historical import chain. Only add expected-flags to full immutable fixture
checks and replace its sample flags literal with the exact selected record
value; inverse reconstruction must recover the original function. Additional
wrapper checks bind exact trap PCs, pc advance and zero exception CSRs.

The existing adapter is unchanged; verify its build receipt, original inputs,
artifacts and source against the frozen support source. Bind the current
dot16 reference through the existing hardware result, exact 1400-byte ABI,
feature flags and all runtime input SHA values. Do not obtain this binding
by replacing the old W2 reference SHA in its historical contract.

## Budget, protection and qualification

CPU1/nice5, one worker, make -j1; share the already authorized four CPU
indices without introducing a fifth. Total1200s includes preflight and final
hash audit; build180s, metadata/disassembly30s each, each adapter180s internal
and210s external, 100million API calls,32MiB per output file. Signal handlers
only latch; bounded waits and the existing process-group helper close child
trees and reap each process. Keep all failure inputs and logs. No automatic
budget extension or repeat campaign. Outputs are isolated from all original
sources, fixtures, tools, adapter and runtime files.

PASS qualifies these exact two linked K768 implementations on these two
fixture sets in the unchanged NEMU reference. It grants no new EMU, full
consumer, application performance, retirement-audit, ASIC or50% qualification.
Original four-arm forward operations and frozen inputs remain untouched.
