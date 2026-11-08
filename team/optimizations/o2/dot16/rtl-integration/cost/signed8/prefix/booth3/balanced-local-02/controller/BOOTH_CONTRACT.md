# Unchanged Booth3 DUT, one balanced-Gold verification recipe

Contract: `dot16-prefix-booth3-balanced-gold-v1`. Date:2026-11-08 UTC.

## Reason and decision

Original `dot16-prefix-booth3-local-v1` local-01 remains FAILED. Its actual P arithmetic proof and R19/3 unconstrained SAT passed; R20/6 timed out at30s without a counterexample, and FU/cost never ran. Preserve result110068B SHA7eb958143cc41f98cad195e0e7089b8924f827af340c51abca18ba573174d050 and the complete129-payload failure archive. No previous operation is replayed or relabelled.

Root and independent Pro2 review support exactly one distinct reference formulation: replace the six-input left-associated Gold expression with `(a0+a1+a2)+(a3+a4+a5)`. For six independent unsigned20-bit inputs and a20-bit result, both expressions compute the same sum modulo2^20 for all2^120 inputs. Associativity needs no range assumption. Gold remains behavioral addition; it does not copy the DUT's CSA or prefix equations. R19 Gold remains `a0+a1+a2`. The new record explicitly reports formulation_attempt2 and retried=true; that does not mean a replay of the failed operation.

No DUT, P/R boundary, mapper parameter or test standard changes are included. If this one new recipe also produces UNKNOWN/timeout, stop this P3 branch without a further formulation, timeout increase or grouping sweep. No success is predicted from the earlier fast three-input proof.

## Frozen design and verification obligation

Both Scala source bytes and the P verifier remain exactly those of the failed point: datapath880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680; wrapper1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238; verifierc0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587. Source derivation remains202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876 under its original source contract. The new controller derives reversibly from original controllerbcde44c580003a0a99e18cc30a2795a9c7a9af08ed56ef38a8f740987ec8241f.

Retain the128-bit architecture interface, original rising-edge clock and synchronous valid reset, two elastic slots, unreset data protected by valid, accepted request control/performance identity, flush/kill/illegal/backpressure behavior, E0accept/E1move/E2response and II1. P remains3×19bits for feature0 and6×20bits for feature1, per-half biased sum S8+2^19 and dot8 high-half(2^19,0,0). R and exact signed result ranges remain19/20bits. The whole old clock/reset/interface/arithmetic contract still applies.

Pin the exact failed result, timeout log and prior generated SV. Generate anew into a fresh isolated output and require all actual DUT/public-top SV bytes to match the failed point, including actual R20 SHAbee47acb860892ca52e081750a29eb8668ecf7551b4e46404d68a5748c6a18e2. The existing extern_modules.sv rule allows only the exact producer header and two exact external-module comments in either order; comment order is metadata and does not change DUT logic. Preserve original resident source/cache/classpath and inputs read-only.

Run the same strict actual P structural verifier and all four wrapper bindings. Fresh R19/3 and R20/6 miters must use every independent input bit and every result bit, unchanged width, DUT, Yosys solver options and30s solver/60s command limits. No assume, input constraint, biased-domain restriction, omitted output or reduced width is permitted. Require exit0, exactly one explicit SUCCESS, no counterexample and no ERROR for both. Timeout/tool error remains FAILED and blocks FU/cost; a missing counterexample is not an equivalence proof.

Only after those new gates pass, run the original two feature FU campaigns and eight intentional fault classifications, then the same Nangate45/ABC D1000/1ns STA templates and five path classes. Area, actual DFFs and all slacks retain their measured sign. This earns only the source-specific local arithmetic/FU/cost scope. It does not adopt a production default, establish1ns closure, or grant parent/core/application/power/physical PPA qualification.

## Bound and preservation

This is a separately registered finite engineering decision after the original failure, not automatic retry. New input-02/local-02 only; CPU2/nice5/make-j1; absolute total success budget300s, outer360s including cleanup; latest real launch06:45 UTC. Do not reuse the original1200s budget or extend the new budget. Check live occupancy and aggregate≤4CPUs before launch.

Each child records status/logs/reaping/group absence. New generated artifacts, snapshot, old failure, source/tool and classpath identities are checked at completion. Old input-01/local-01 and archive-01 remain untouched. New success, failure and all raw evidence go to a distinct archive-02 with its own manifest. No official program or checker is modified.
