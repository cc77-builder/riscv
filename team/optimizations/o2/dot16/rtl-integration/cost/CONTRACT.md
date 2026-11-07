# Production CommonFuCostTop nominal cost v2

Status at creation: **prepared, not mapped**. Contract identity:
`dot16-production-common-fu-cost-v2`. This finite experiment records one nominal
feature0/feature1 standard-cell area and STA comparison at the same complete
production FU interface. It does not qualify power, parent/core PPA, a chip
frequency, or application performance.

## Source and generation evidence

The original direct-leaf v1 proposal could not be used: installed Yosys 0.9
rejected the unchanged previously generated feature0 SV at `automatic` on line
209. The bounded `frontend-check-01` preserves that real failure; no mapping/STA
was attempted by that probe. Do not edit its source or delete the failure.

The successful replacement generation is separately defined in
[GENERATION_CONTRACT.md](GENERATION_CONTRACT.md). Its actual 2026-11-07 attempt
`dot16-production-cost-20261107-main/generation-01` completed with:

- Generation result SHA256
  `7b45921ee1b5ff564113daa61403c4e52ecb598305aad6c093f4ab5768fe0a09`;
  status `TWO_COST_INPUTS_GENERATED_AND_PARSED`.
- All four old feature1 SV files reproduced byte for byte before new generation;
  the existing complete compiled classpath and 433-file production source map
  remained unchanged. No Mill or resident/cache writes occurred.
- Unchanged O4 `GenerateVDotCost.scala` SHA
  `de06a6f46d19d6d4a42cbcff19f081e7423747578951c9b341d50076a913e97b`,
  compiled independently into the external output and using its existing
  `disallowLocalVariables,disallowPackedArrays` lowering options.
- Both new top SV files have the same SHA
  `60fea45c63aa9d172a3e26d091ba13ac24241888792a50cc9b9ccbb5eb48e943`.
  Feature0/1 leaf SV SHAs are respectively
  `c597e1bef4e06478d459c5c6a3ab727fe135816195011c59773b879a4839e7e4`
  and `18dc26ef821c0f2561214f66e09f8a373675b584a8f7246f38e9c56c3e937087`.
- Eight recorded commands exited 0 and were reaped with absent process groups;
  successful completion independently read back after outer exit0/cleanuptrue.
  The new outputs retain `functional_qualified=false`.

`run.py` requires an explicit full SHA for the completed generation result,
checks the fixed generation controller/contract/generator/source snapshot pins,
the ordered feature0/1 inventory, exact eight-command completion, all new SV
bytes, and identical top connections. Inputs and helper copies are checked again
at the end. A new generation can be consumed only with its explicitly reviewed
new receipt SHA; the old result identity cannot be transferred automatically.

## Boundary and configuration

Top: **CommonFuCostTop**, generated independently from the actual
`VDotElastic(FuConfig.VDotCfg)` source using `MinimalConfig(1)`. Clock is the
posedge `clock`; reset is synchronous. The source's no-stall arithmetic pipeline
remains two cycles with an intended steady-state acceptance interval of one
cycle, as established by the earlier FU harness evidence. This experiment does
not independently re-test those timing/functional properties at the new top.

The top preserves the complete real `dut.io`, including ROB/redirect inputs,
vector controls and write enables, result, all performance metadata and all
production data slots. The actual two 128-bit dot operands are `src_0/src_1`;
other production slots remain ports. No FuTestTop input correlation, observer,
occupancy output, trace tap or monitor is part of this cost top.

Both points use O2=1, T14=1, O1 handoff=0, T12/T13/O1/O2 tracing=0. Only
`VDOT_DOT16` changes from 0 to 1. New generated RTL is copied unchanged;
`SYNTHESIS` disables assertion-only code during frontend reading. No production
Scala or generated RTL is patched for synthesis.

**Do not mix boundaries.** The original harness-derived leaf exposed fewer
independent production metadata/control signals plus observation outputs. Its
cost would not be interchangeable with CommonFuCostTop. Likewise, old O4 O1/O2
or independent prototype numbers are historical context, not a denominator for
this new feature1-minus-feature0 comparison.

## Mapping and nominal STA

Use only the installed, identified tools and the fixed library:

| Input | SHA256 |
|---|---|
| Nangate45 `NangateOpenCellLibrary_typical.lib` | `8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1` |
| `/usr/bin/yosys` | `dab84e88b53146fe22d675a142de32b1e545ee9b7fe1054238f6220245b24c8d` |
| `/usr/bin/berkeley-abc` | `9f8539df83c751324a16ee98878b0e7e200a7ed4916d5270da3d9b2390c5ffc7` |
| `/usr/bin/sta` | `9630070fdbcfd2a92a9d0dc6b6e5480f7be8e216b720f1fb32f447fb4cedc2ff` |

For each point, read all four SV files, check hierarchy, lower processes,
flatten/synthesize, map flops and logic to the same library, and require no
unmapped cells. The sum of library cell areas must agree with Yosys's reported
area. Preserve cell counts/histograms and the entire mapped JSON/netlist.

Both points use the same nominal constraints: 1.0 ns clock period, 0.05 ns clock
uncertainty and clock transition, 0.1 ns maximum input and output delays,
0.05 ns input transition, 5 fF output load, and `5K_hvratio_1_1` wire-load model.
ABC uses delay target 1000 ps, driving cell `BUF_X1` and load 5.0. These are
comparison assumptions, not a new contest requirement or measured chip clock.

Record one worst maximum-delay path in each class: register-to-register,
input-to-register, register-to-output, input-to-output, and output-ready to
input-ready. Parse both arrival and slack. Negative nominal slack is a valid
measurement and sets `nominal_setup_met=false`; it must not be called timing
PASS or hidden by selecting another constraint.

The installed OpenSTA previously rejected concat-LHS assignments emitted by this
Yosys. If that exact pattern occurs, reuse the unchanged team O4 canonical
netlist emitter. Its output must be re-read, original instance identities bound,
and port widths, cell histogram and complete topology hash checked equal to the
mapped design. This only serializes the mapped graph; it is not an RTL rewrite,
logic transformation or formal equivalence claim. If the pattern is absent,
feed the original mapped bytes to STA.

Unconstrained endpoints are acceptable only when the existing strict helper
proves they are constant output bits. Any other setup warning, tool error,
missing path class, changed input or incomplete process cleanup fails the
attempt. Preserve the original failure and do not relax the check to obtain a
result.

## Resource, ownership and output

For this round use CPU1, nice5 and one active command at a time, within the shared
CPU0-3 budget. Do not add compilation/reference work on CPU0 while the N-Q run
is active. All helpers, generation evidence and original repository inputs are
read-only; mapping outputs are a fresh external directory separate from them.
No worktree/index mutation, clone, parent sweep, clock sweep or extra simulation.

Total inner limit is 900 seconds from preflight; each subprocess gets at most
300 seconds or the remaining total budget. Reuse the fixed FU process helper
for TERM, bounded wait, KILL where needed, reap and process-group absence. An
outer 1200-second operation leaves cleanup time. No automatic retry or extension.

The only successful aggregate label is **TWO_COMMON_FU_COSTS_RECORDED**. It
requires both results and input stability and records feature1-minus-feature0
area. The individual `nominal_setup_met` fields remain independent measurements.
New-top functional qualification, parent/core qualification, power measurement
and application-performance qualification remain false.

## Invocation

```text
python3 -B run.py --repo <team-helper-repository>
    --generation <completed-generation-directory>
    --generation-sha256 <reviewed-result.json-sha256>
    --output <fresh-external-mapping-directory>
    --library <fixed-Nangate45-typical.lib> --cpu 1 --budget-seconds 900
```

Deliver raw success and failure logs, all command receipts and cleanup results,
new RTL, generated input manifests, mapping/STA scripts and reports, and an
engineering result explaining this new boundary. The result is nominal
pre-layout standard-cell cost for this FU scope; no power or place-and-route
claim follows from it.
