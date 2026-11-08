# Single three-row Booth P/R boundary screen

Contract: `dot16-prefix-booth3-local-v1`. Prepared 2026-11-08 UTC.

## Decision and scope

The completed Booth2 point has feature1 mapped area17190.516 but I2R slack−0.254728ns, 16.722ps worse than the original prefix point. Its measured critical I2R endpoint is a last-P-compression-layer carry. Test exactly one movement of that final compression layer across the existing P/R boundary. No mapping sweep, fourth-row variant, parent/core/EMU or new application run is authorized by this contract. A completed screen is evidence for a decision, not adoption or nominal timing closure.

Root authors the RTL and controller. Freeze the original Booth2 point. All official programs, original FU tests and helper standards remain unchanged. The team-owned strict heap verifier is derived only for the three-output interface and its stated identity.

## Microarchitecture and exact arithmetic

Retain the existing rising-edge clock, synchronous valid reset, two elastic slots, accepted-request control/performance capture, illegal handling, redirect/kill, reset suppression and output backpressure. Data registers remain unreset behind valid state. Unstalled request acceptance E0 moves into R at E1 and first responds at E2; initiation interval remains1 cycle. Input/result interfaces remain128bits; exact signed sum goes in low32 with upper96 zero. Dot8 uses low64 only; dot16 uses all128bits. There is no rounding, saturation or approximation.

The nine-bit radix4 recoder, sign-bit inversion, separate neg carries and constant350208 remain byte-identical to Booth2. Per half, the three unsigned20-bit P rows sum modulo2^20 to signed_dot8+2^19. Stop after limits28,19,13,9,6,4,3: expected272 FA/19 HA/seven layers, requiring proof from the actual emitted module. Feature0 stores3×19bits; feature1 stores6×20bits. For feature1 dot8, the accepted high half saves (2^19,0,0). Feature0 ignores bit19 of each row; bias vanishes modulo2^19. The two feature1 half-biases vanish modulo2^20. True sums still fit signed19/20: dot8[-130048,131072], dot16[-260096,262144].

Finish19 compresses its three saved rows to two, then uses the unchanged prefix network. Finish20 compresses low and high triples in parallel, then compresses four rows to two through the original two-CSA-layer pattern before the unchanged prefix network. There is no extra stage, mode-dependent correction after P, or carry propagation within the CSA steps. R modules have changed and MUST earn fresh unconstrained-input SAT proofs; old2/4-row SAT PASS cannot qualify new3/6-row modules.

## Required verification and fair comparison

Before running, preserve exact source/controller/checker derivations. The combined source inverse must recover the original prefix files; the controller inverse recovers the completed Booth2 controller including its absolute total-deadline fixes. Use resident cached classes read-only and a new isolated run/output root, no new checkout or source/index write.

Generate both features for both actual cost and FU consumers. Bind all three P outputs per half, exact operand slices, low19/full20 capture, accepted high-half biased zero, three/six saved rows into the R module and unchanged public tops/control assignments. The new strict verifier parses the entire actual emitted module, closes every recoder equation, 7168 digit cases, all256 signed byte decompositions, each FA/HA truth table, prior-layer dependency, arithmetic token use and bias. Its compositional conclusion covers binary operands, not X/Z or sequential state.

For each actual emitted Finish19/20 module, generate independent Gold=sum of unconstrained3/6 width19/20 inputs and Gate=actual DUT. Run the original Yosys miter recipe with30s solver limit/60s command limit. Require explicit SUCCESS, no counterexample, exit0, complete pinned gold/gate/script/log. Any timeout or error blocks FU and cost, stays failed, and is not retried. Historical multiplier SAT timeout remains UNKNOWN and is not repeated.

Run both existing FU campaigns and all four intentional negative controls per feature, retaining return codes and classification. Map the same CommonFuCostTop interfaces with the frozen Nangate45 library, Yosys/ABC D1000, BUF_X1/5fF and unchanged1ns OpenSTA template. Only RTL/module/output paths change. Independently sum cell area; record actual DFF count instead of assuming a40-bit estimate. Preserve all five timing classes R2R/I2R/R2O/I2O/ready, complete reports and setup warnings. Compare the entire actual slack set and area with original prefix and Booth2; do not judge from one improved path or structural counts.

No parent, full-core, application, production-default, physical-design, power, mapped-equivalence SAT or1ns-closure qualification is granted by this local screen. A negative slack remains negative. Arithmetic/FU success does not itself establish PPA superiority.

## Execution and closure

One local point only, CPU2 affinity, nice5, make-j1, one compiler processor. Total controller success budget1200s and outer timeout1500s including cleanup. Latest actual start07:00 UTC on2026-11-08; no automatic extension/retry. Check real live occupancy/free memory and aggregate≤4 CPU before launch. Every command is limited by its fixed individual timeout and remaining absolute total deadline. Cleanup and group-absence checks remain mandatory after errors; late success must be rewritten FAILED.

Recheck every original input, snapshot, generated artifact and cached classpath; retain all command logs, negative outcomes and failed evidence. Archive the complete finite run after child reaping/group absence. Record whether the result warrants any later integration; this contract itself does not permit a production default switch or authoritative-code modification.
