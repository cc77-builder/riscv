# Production FU cost generation v2

Status at creation: **prepared, not executed**. This is a new generation identity,
`dot16-production-fu-cost-generation-v2`, after the direct reuse v1 route was
actually rejected by the installed Yosys 0.9 frontend. It does not amend the old
FU PASS, change frozen RTL, or change the currently running EMU experiments.

## Reason and scope

On 2026-11-07, unchanged feature0 `VDotElastic.sv` SHA
`f28ac5bc52d2e0736b3733f8a69756daf860480b72812472abad0bc1306eba2d`
failed `read_verilog -sv -DSYNTHESIS` at line 209 with `unexpected TOK_AUTOMATIC`.
The bounded probe and its failure are retained in
`dot16-production-cost-20261107-main/frontend-check-01`. No synthesis mapping or
STA was run in that probe. This is a tool input compatibility failure, not a new
functional counterexample.

The existing, unchanged `team/optimizations/o4/GenerateVDotCost.scala` SHA
`de06a6f46d19d6d4a42cbcff19f081e7423747578951c9b341d50076a913e97b`
already requests `disallowLocalVariables,disallowPackedArrays`. Its
`CommonFuCostTop` connects the complete real production `dut.io`, with clock and
synchronous reset, and no test tap or `pipelineStatus` observation output.
This boundary differs from the originally planned direct generated leaf. Any
later area delta must compare two **new CommonFuCostTop** points, never a mixed
v1/v2 or historical O4 pair.

This stage only reproduces the old generated feature1 RTL, compiles the existing
cost generator, generates feature0/1, and checks frontend parsing/hierarchy. It
does not run a new FU simulation, technology mapping, timing, power, parent,
core, or application performance measurement. `functional_qualified`,
`synthesis_complete`, and `sta_complete` remain false.

## Fixed source and cached classes

Use the existing resident checkout and its existing
`out/dot16-fu-20261106-pro2` cache **read-only**. No new checkout, Mill invocation,
dependency download, cache update, production source edit or Git mutation is
permitted. New classes, temporary files, logs and RTL go to a fresh external
output directory.

The source map is the original successful feature1 FU campaign's 433-file
`campaign/source.json` (SHA
`80637d38348fbecd928f6442fd0c69fab763a918ac8da8642a5a3667dacdc9c2`).
Every listed resident source must still match. This explicitly includes the
known production dot16 changes; the clean commit alone is not the input identity.

The old decode campaign's `classpath-before.json` SHA
`ab6aaa12cb8b9508d1a1bf994d63561a08f2112ea6d9d48b30ac7916fc1dfdde`
binds 135 runtime entries, including jars, complete class/resource directories
and 23 intentionally absent resource paths. Reuse the unchanged decode runner's
`parse_classpath` and `classpath_identity` functions to verify that evidence.
The FU run classpath adds only its compiled harness directory and two explicitly
absent FU resource paths. The Scala compiler, Chisel plugin, options, Java and
firtool are also recorded and held unchanged through the attempt.

Before using the new cost generator, invoke the existing compiled
`GenerateVDotElasticFu` with feature1 and the original flags. All four resulting
SV files must reproduce the original successful FU campaign **byte for byte**.
Failure stops the attempt. This establishes applicability of the reused compiled
classes; it does not turn the subsequent new cost outputs into old test outputs.

Compile only the 3,107-byte unchanged cost-generator Scala source into the new
output, using the already recorded Scala 2.13.15 compiler and Chisel 6.6.0 plugin.
The compiler options come from the pinned cached `allScalacOptions.json`.

## Configuration and generated boundary

Both new generations use `fu`, `MinimalConfig(1)`, O2=1, T14=1, O1 handoff=0 and
all T12/T13/O1/O2 tracing=0. Only `VDOT_DOT16` changes from 0 to 1. The same
firtool 1.62.1 and the generator's original lowering options apply to both.

Each output must contain exactly `CommonFuCostTop.sv`, `VDotElastic.sv`,
`VDotProducts.sv`, and `VDotReduce.sv`. Record complete SHA256 and byte counts.
Run the fixed installed Yosys frontend with `-sv -DSYNTHESIS` and
`hierarchy -check -top CommonFuCostTop`; complete feature0 first, then feature1.
No editing or canonicalization of generated RTL is allowed.

The production arithmetic and handshake design is unchanged. Existing source
evidence includes feature0/1 operation legality, dot8/dot16 arithmetic,
two-cycle no-stall FU latency, one-operation-per-cycle steady state, metadata,
backpressure, redirects, cancellation and synchronous reset. Those facts belong
to the old tested harness boundary. The new CommonFuCostTop exposes independent
production IO, including the two 128-bit operands, 128-bit result, operation,
ROB/redirect, vector controls and metadata. Later synthesis may remove internal
observation logic; that is part of the newly named production IO cost boundary.

## Resource and failure contract

For this round use CPU1, nice=5, one active processor for Java/GC, no Mill jobs,
and new output-local temporary storage. All children inherit CPU affinity; this
shares an already authorized core and does not use CPU4 or higher. Existing Q288
and four-arm EMU operations retain their original ownership and frozen inputs.

Default and maximum total budget: 900 seconds, measured from before input
preflight. Every subprocess has at most 300 seconds or the remaining total
budget. The retained process helper performs TERM, bounded wait, KILL if needed,
reaping and process-group absence checks. No timeout extension or automatic
retry. An outer operation limit must leave cleanup time after this inner budget.

Record raw commands, versions, failures, input/classpath snapshots and output
identities. Successful completion requires all original and copied inputs,
classpath entries and absent optional resource paths to remain unchanged.
The success label is **TWO_COST_INPUTS_GENERATED_AND_PARSED**, not FU_PASS or
PPA_PASS. If reuse fails or substantial dependency rebuilding is required, stop
this finite branch and retain the failure; do not change the main software
optimization acceptance criteria.

## Invocation

```text
python3 -B elaborate.py --repo <resident-source> --fu-root <original-FU-run-root>
    --output <fresh-external-generation-directory> --cpu 1 --budget-seconds 900
```

The direct reuse v1 proposal and actual parser failure remain distinct evidence.
Any subsequent nominal mapping/STA requires the v2 generated inputs and their
complete result identity; no feature1-minus-feature0 result exists at this stage.
