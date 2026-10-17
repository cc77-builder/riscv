# Jade public implementation: preparation audit

## Fixed sources

- Public repository: https://github.com/Jade0x13157A6/cie2026-xiangshan-vdot
- Public commit: `a17e38128e589d745152f3ef4b595b4572b22b3d`, confirmed by `git rev-parse HEAD` and `git cat-file -t` (commit, not tree).
- XiangShan base: `16ae9ddcda54fc9a2fddffad73174cf793ac7814`, exactly the author's pinned base and the unified campaign base.
- YunSuan: `cadd3c2f43096e253d61296b33ac697be8354e29`; Rocket Chip: `bea0af5d855a871699b907c1988961141bbf28e7`.
- All populated dependencies were cloned independently with `--shared` from local fixed T15 dependencies, then checked out to the parent gitlink. Object storage is shared; working files are independent. Complete pins and command arrays are in `jade.json`.

## RTL and encoding

Original patches `01-yunsuan-vdot.patch`, `02-rocket-chip-vdot.patch`, and `03-xiangshan-vdot.patch` applied unchanged and passed `git apply --check`.

`vdot.vv` runs in existing `FuType.vialuF` / `VIAluFix`, whose ordinary latency is one cycle. Eight signed 8-bit products and a balanced three-level addition tree produce a signed 32-bit sum, then `Cat(0.U(96.W), result)` supplies all 128 output bits. The native old-destination merge is bypassed for this operation. Existing pipeline/control logic carries identity and cancellation. No separate scheduler port or parameter extension is introduced.

Machine word for arbitrary registers:

```text
word = 0xe6000057 | (vs2 << 20) | (vs1 << 15) | (vd << 7)
```

`funct6=111001`, `vm=1`, `funct3=000`, vector opcode `1010111`.

Unified supported domain: `VLEN=128, SEW=8, LMUL=1, vl=8, vstart=0, vm=1`. The hardware directly computes the first eight signed byte pairs and writes low32/high96=0. Source/target aliasing is mathematically safe because sources are read before writeback.

The author's exception/no-op semantics are broader than the team's strict contract: it explicitly rejects SEW/LMUL mismatch but uses existing `vstart >= vl` no-update behavior and does not require exactly `vl=8` in hardware. Therefore, the common benchmark must not claim identical ISA behavior outside the unified domain. Arithmetic equivalence and full-register output still require actual DiffTest validation.

## NEMU adaptation

The author pins NEMU `53bcb5686f8fd05248ae98546b7dc04bdca1bbb0`; the unified campaign uses `a48a11f208ff81ad765591d83271d1b339fb3861`. The old source reserved a `vdot` helper, but the common source removed it. Consequently the original NEMU patch does not directly apply.

The `vdot` helper body is copied verbatim from the author's patch into common-base `vcompute.h`; a `vopivv` decoder entry and `isa-all-instr.h` EXEC_ID entry are added. No arithmetic logic is changed. The complete adaptation is `jade-nemu-a48.patch`, distinct from the untouched author patch. The helper preserves alias safety, validates SEW/LMUL/vm, writes all sixteen destination bytes, clears vstart, and marks vector state dirty.

For common XS boot compatibility, generated NEMU configuration disables `CONFIG_MDT_INIT` and enables `CONFIG_NMIE_INIT`, matching the team's known-good reference configuration. Build command and hashes are stored under `variants/jade/nemu-build/`.

## Common measurement instrumentation

`common-observers.patch` is applied in `NewCSR.scala` and `Rob.scala` for the existing `VDOT_T13_TRACE=1` sample/retire observers. This does not change the author's datapath. Root agent owns the full-core build and all performance runs.

Expected unified hardware command (invoke with the same shared Java/tool environment):

```bash
VDOT_T13_TRACE=1 make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=12G OPT_FAST=-O3 OPT_SLOW=-O0 -j2
```

Use the same DRAMsim3/AM/flash/toolchain versions as all other variants. The author's published measurement used KunminghuV2Config and scalar C baseline, so its old 3.030x number is not a unified result.

## Status and limits

- Original patch application and independent source setup: complete.
- NEMU build: completed successfully (exit 0). Reference SHA256 `af5cd64938e0a1056843898a90e2ecaaf09fa457171cefd916aa0efbcf4d457f`; SoftFloat `a0c6494cdc11865811dec815d5c0049fba9d82a8`, identical to the team reference. Full build metadata is in `variants/jade/nemu-build/command.json`.
- Hardware build, full 128-bit correctness, and measurements: owned by root campaign; no passing result is asserted here.
- Single-cycle arithmetic may lengthen the physical critical path. Cycle counts alone do not establish clock frequency, physical timing, energy, or area benefits; no synthesis is part of this preparation.
