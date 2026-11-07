# N/P packed-Ws candidate v1

Identity: `r3-dot16-np-packed-ws-v1`. This source/GNU stage does not run a guest.
Fixed RV64/lp64d, VLEN128, M288, K288/K768, GS32, RNE, disjoint buffers.
The typed scale buffers are 64-byte aligned and contain all original binary32
object representations, including padded rows, reordered as
`packed[(tile*G+group)*8+lane] = bits(Ws[(tile*8+lane)*G+group])`.
The original q288/w2 row-major context types and entrypoints remain unchanged.
The new contexts keep offsets 0/8/16/24/32/40/48 and size 56, with a distinct
typed scale pointer and distinct function declarations. No incompatible cast.

Four functions derive from the completed N/P common forward build, result
`3d855fa040c05c91e079a5b7c52e6ce783510332369e297150f301fb3d64b4c7`, ELF
`62a73b9d16cea43ad03eec3ec09b27edfab7da90ce895d33baa72bf9d84723c4`.
Each N changes exactly three words; each P changes six including its fallback.
Only the stride load becomes a unit-stride load, per-group scale step 4 becomes
32, and the tile extra step 252/672 becomes zero. Retain stride initialization
and zero addi to keep the entire function length fixed (312/1096 bytes).
Keep all other machine words, branches, integer and FP order, CSR setup/exit,
P's complete -128 guard/fallback and final full register slots byte-identical.
Symbol names differ. Local labels stay object-local; compile packed.S as its
own object when linking with original functions.

The prepare functions use character accesses to copy four bytes per scale;
they perform no FP evaluation, conversion, pre-multiplication, or FMA. Prepare
before first use and after every weight-scale update. Preparation has a cost,
which is excluded only from explicitly prepared-kernel timing and must be
reported separately before any end-to-end claim. Full-consumer integration,
memory allocation and amortization are not yet implemented or qualified.

One finite GNU stage: CPU1 with absolute nice5, one worker within CPU0..3,
180s total and 30s per command, 32MiB per log, no automatic retry/extension.
Use the existing unchanged process-group cleanup helper and ELF reader.
Rebuild original and candidate standalone functions, compare the original
bodies directly with the frozen actual common ELF, and derive expected new
machine words independently from the ISA bit fields. Verify complete function
bytes and independent GNU nm extents. Compile pack.c with strict warnings and
the real RV64 compiler to enforce all layout assertions. Retain all failed
outputs; all source/tool/frozen-input hashes must remain unchanged.

Host packing/source review can establish finite index coverage and bit-copy
behavior. It does not substitute for NEMU, XiangShan, or application timing.
A later reference/target stage needs its own fixed fixture/case/budget plan;
no new complete-forward run is launched by this contract. Existing active
four-arm N/P input/output ownership and runtime policy remain unchanged.
