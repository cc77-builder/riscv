# T12 / VDot performance review gate — 2026-10-14

**DRAFT: HOST-ONLY. No full-core T12 acceptance or measured performance.**
Base branch `zufan`, pinned parent `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`.
This review tree leaves production `src/`, `build.sc`, NEMU and T10/T11 results unchanged.

## Reproducible source and evidence
- New source-bound T12 assembly/C workload, generator, provenance-locked build/run driver, strict validator and tests. Plan: **190** records = 13 stress/fault cases, 75 vdot/RVV equivalence inputs each by two methods, 3 timing scenarios × (one empty window + 4 AB/BA pairs). Candidate ROB/FTQ wrap and young-instruction kill are **NOT_OBSERVED** microarchitecturally.
- Local implementation receipt reported **68 passing host methods** (16 new + 9 old model + 4 baseline + 4 artifact + 35 mathematical-model). An independent re-execution of the **16** new host tests using Windows Python 3.13.13 also passed, exit code 0. Host synthetic logs do **not** count as DUT evidence.
- Experimental input-stage fusion packet: default-disabled patch, Chisel reading copies, real-FU checker, A/B runner, and original host-model logs. Patch is not applied to production sources.
- Real new RISC-V target binaries, DiffTest logs, pairwise cycle/instret counters, timing/PPA data: **NOT_RUN**. Included `performance.json` has `samples=[]` and null measurements, `raw.csv` only a header.
- Original Windows hardware packet contains generated `vectors.tsv` (1,132,502 bytes; SHA256 `901a7be30e62b81bcd3df55b20538a5ba9c879ba9c7c34f28b8c0421d8e6a327`), deliberately **not committed** to avoid duplicate large derived data. Regenerate from the pinned 10022-vector model and verify the hash. Old local-path entries in `manifest.sha256` are historical provenance, **not** evidence every payload exists in this review tree.
- Previous Windows agents encountered WSL `E_ACCESSDENIED` and Git ownership/ref restrictions. They did not bypass either restriction; this separate GitHub review branch is not a claimed Windows/Linux build or local Git commit.

## Decision and experimental controls
1. First: proper Linux cross-compile/disassembly, fresh source-bound emulator run with DiffTest and all 190 expected records; run prior 117 unique T10/T11 regression cases again. Fail closed on logs/provenance.
2. For cancel, shared VFEX4 arbitration/WB, ROB/FTQ rollover, capture actual tagged issue/flush/response/grant/wrap events, not just instruction count or branch loops.
3. Compare normal state-preserving RVV and custom VDot, plus separately reported known-config and independent batch scenarios. Use all AB/BA repeats; distinguish instruction-retirement counters from FU latency.
4. Baseline local FU source-derived E0 accept / E2 post-edge valid / E3 response / II4; hypothetical input-stage fusion E0/E1/E2/II3. The VFEX4 external busy and writeback remain single-outstanding, and 8 multiplies move into an RF/bypass-to-products path, so no whole-core speedup is established.
5. Only promote after real two-variant Verilator `--assert` regression/negative controls, full-core DiffTest and observed control coverage, fair processor counters, and consistent full-path STA/PPA. Compare **C_candidate × T_candidate < C_baseline × T_baseline** for actual elapsed processor time; no contest score is claimed.
6. If data show insufficient gain or clock degradation, reject the experiment and retain the passing production implementation.

**Do not merge to `zufan` yet.** All work items requiring actual RISC-V/Chisel execution remain open; official ISA clarification and human signoff are pending.
