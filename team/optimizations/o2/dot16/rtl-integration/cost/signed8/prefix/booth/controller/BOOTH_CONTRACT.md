# Single Booth9 local arithmetic, FU and cost screen

Contract: `dot16-prefix-booth9-local-v1`.

## Purpose and limits

Test one structural replacement of the frozen prefix candidate's Baugh–Wooley P-stage heap with radix-4 Booth recoding. The independent feasibility review predicts 288 FA / 20 HA / 8 active compressor layers per half, versus the actual original 477 FA / 17 HA / 10 layers. These are structural counts, not a promised mapped area or timing improvement. No 10-bit/19-bit representation matrix, mapping sweep, new parent/core/EMU run or new application fixture is part of this contract. The stopped explicit-FA serialization/STA experiment remains stopped.

Root authored the candidate and controller. Existing authoritative programs and checker standards are unchanged. The reusable helpers and original FU vectors/C++/negative checkers remain exact frozen inputs; only the new team-owned arithmetic verifier and new candidate controller are introduced for the changed representation.

## Interface, state and arithmetic

The architectural request/result interface remains 128 bits. Dot8 sums eight signed 8-bit products in bits 63:0 and ignores operand bits 127:64. Dot16 sums all sixteen signed 8-bit products. The exact sum is sign-extended to low32, with bits127:32 zero. There is no saturation, rounding, mask/tail preservation or approximate arithmetic.

The original inherited rising-edge clock, synchronous valid reset, complete per-slot control/performance identity, flush/kill/illegal handling and output backpressure remain. P and R are the same two elastic slots. With no stalls or redirects, acceptance at E0 transfers to R at E1 and first responds at E2; initiation interval is one cycle. Data registers remain unreset and are protected by valid state. Feature0 P rows remain 19 bits; feature1 four P rows grow from19 to20 bits. R remains19/20 bits. This is an internal data-representation change, so the contract does not claim all state widths are unchanged.

For each signed byte a and radix-4 digit d, select a 9-bit signed magnitude m in {0,a,2a}. Raw multiplier window MSB n drives both bitwise complement and an independent heap carry. Before the carry, q=m if n=0, else q=-m-1; q fits signed9. Flip q bit8 to encode q+256 as an unsigned row. Add n separately at column2j. For a=-128,d=-2, this is row511 plus carry1, not a truncated 9-bit row addition. The111 negative-zero code keeps complement and carry together.

The four shifted rows have per-lane bias21760. Eight lanes plus constant350208 (bits18,16,14,12,11) encode S8+2^19 modulo2^20. Two unsigned20 output rows enter P. Feature0 explicitly stores each row's low19, cancelling its bias modulo2^19. Feature1 stores all20 bits; two half-biases cancel modulo2^20 in unchanged Finish20. A feature1 dot8 request saves high-half row0=2^19,row1=0 on the acceptance edge. No later isDot16 input repairs old P data.

S8 is in [-130048,131072], fitting signed19. S16 is in [-260096,262144], fitting signed20. Original prefix finish Scala and actual emitted Finish19/20 bytes must remain identical to the existing unconstrained-input SAT-proved modules.

## Required evidence

Before execution, freeze source, full inverse derivations, new checker and this contract. Recover the exact two prefix Scala baselines by inverse edits; recover the complete finished Pgroup controller from its new derivation. Use the resident cached compiler/classpath and isolated output; no resident/source/index write or new checkout.

Generate all four real cost/FU consumers (feature0/1) and verify closed file/resource lists, unchanged entire public tops, exact input slices and P capture, low19/full20 storage, accepted dot8 biased-zero and unsigned prefix connections. Non-data sequential assignments and architectural output extension must match frozen consumers. Failures remain failures; do not loosen acceptance based on a desired result.

Run the new strict verifier over the actual emitted VDotCarrySaveRows bytes. It must parse the complete module, bind every recode equation and byte slice, check7168 actual digit/multiplicand cases and all256 signed multiplier decompositions, then prove every FA/HA truth table, earlier-level dependency and single weighted destination. The conclusion is all binary operand assignments by composition; no X/Z or whole-FU sequential SAT claim. Require288 FA,20 HA,eight layers and exact bias. The checker does not itself qualify the wrapper.

Reuse the exact prior unconstrained Finish19/20 SAT artifacts only after actual emitted byte equality. Keep the historical monolithic multiplication SAT timeout as UNKNOWN; do not relabel it or repeat it. Run both feature FU campaigns with their existing full coverage and four intentional negative fault checks each. A new source must earn a new FU result; historical PASS does not transfer.

Map both CommonFuCostTop feature forms with the same frozen Nangate45 library, Yosys/ABC tools, ABC D1000, BUF_X1/5fF constraints, and existing 1ns OpenSTA template including uncertainty, input/output delay and wire load. Only module input paths/output paths change. Confirm all mapped cell types, independently sum library areas and preserve the exact220-port/2888-bit interface. Record actual DFF counts rather than asserting a four-DFF estimate. Require error-free completed STA and all five path classes (R2R,I2R,R2O,I2O,ready), with setup-check warnings evaluated by the existing helper. Preserve negative slack as measured; a screen completing does not mean1ns timing closure.

Compare area and the complete same-condition slack set to the original prefix result17965.374 for feature1. Decide from the actual tradeoff whether further integration is justified. Structural FA reduction alone, a single path improvement, ABC internal delay or unqualified mapped area cannot justify adoption. No new formal application performance, full-core frequency, physical design, power or ASIC PPA qualification is granted.

## Execution and closure

One local point, CPU2 only, absolute nice5, make-j1/one compiler processor, original cached classpath, total controller success budget1200s. Command timeouts remain bounded by the remaining total deadline: compile≤300s, generation≤180s, structural proof≤60s, FU build≤300s, map≤240s and STA≤60s. Outer launcher timeout1500s includes cleanup; latest actual start06:30 UTC on2026-11-08. K768 remains the separate original CPU1 operation. Check live occupancy, free memory and aggregate≤4 CPU before starting; do not count wall-clock runtime as hardware performance.

Every child is an isolated process group, and the coordinator records return codes, logs, timeouts, reaping and group absence. Final identity audits cover original inputs, snapshots, emitted artifacts and unchanged original classpath. Preserve any failure and its raw evidence; no automatic rerun, extension or new parameter point. Closed artifacts may be archived and published with exact qualifications. This contract does not authorize production default changes or official program edits.
