# O1 FTQ / CSR / matrix evidence, 2026-10-18

Actual hardware: `02e46c5c915bedf02b0ba17ebb9da64958f34d57` plus the three Scala observer changes in `changes.patch`. Production O1 remains disabled. Test flags explicitly enable T14, O1 and the O1/O2 observer; frozen T12/T13 observers remain disabled. Detailed outcomes and limits: [report](../../docs/o1-complete-20261018.md).

## Recorded executions

All 13 actual full-core launches meet their expectations: hello/vadd, control, calibration, batch128 and eight matrix shards exit 0; the real DiffTest bit100 injection exits 1. The same matrix-0 image subsequently passes with the normal reference. The matrix contains 117 unique cases (80 legal, 37 exception), executed 124 times, with only D00 repeated.

Control records 2157 VDot commits, 384 handoffs, 7 in-flight cancellations, 41 stalled writebacks and 329 observed committed-path FTQ wraps. All eight control requirements pass. Calibration and batch validate 13 + 12 windows and 52 + 48 actual CSR samples against ownership, writeback, independent clocks, retired instructions, compiled ELF paths and UART. Batch records 768 VDot commits and 719 handoffs.

The final host suite passes 72 tests. All 15 real-log mutations are rejected, including consistently altered CSR sample/commit/retire values. No unexpected build or runtime failures occurred in this campaign. The expected injection retains its actual nonzero exit code.

## Frozen artifacts

| Artifact | Contents |
| --- | --- |
| `validation.tar.gz` | 524 files: complete build receipts/logs, all 13 raw stdout/stderr streams and runtime receipts, exact software/ELF/data, reference provenance before/after, host log and recomputation summaries |
| `compiler-inputs.tar.gz` | 437 physical compiler inputs plus source binding; 126 dependency identities are pinned in the binding/source pack |
| `review-inputs.tar.gz` | 28 frozen checker/protocol/build-driver files; no executable supplied by an unreviewed archive is trusted |
| `instrumented-rtl/` | Rob, CSR, NewCSR and shared EXU snapshots, checked against the build RTL manifest |
| `recheck.py` | Authenticates all three archives, checks source/build/runtime identities, then independently recomputes raw-log results and all 15 mutations in a fresh directory |
| `archive-recheck.json` | Actual successful fresh-directory replay receipt; 13 archived launches, zero new launches |
| `files.json` | Final SHA256 inventory of every evidence file except this inventory itself |

Build and runtime hashes:

- Source pack: `7c4d9c4306703ce95a1aa20ac8d070327f7c7a852cb03f279f30c4799f45bb9d`.
- EMU: `fd401bcc1538bdfc01c2c1f6c2dde024417af0182f08905d1853736475533811`.
- Normal NEMU 1.1.0: `e8c9c9be7d798a348a0f8c5ad3a4c601c27511a1967ca3c4cc0af576233f52a1`.
- Frozen software source archive: `d7717d1ef9d36b40d92c39aa6b8534e8ac1a0f968e57c1a45a4c13d9c39a53fb`.
- Validation archive: `ebfb0b7302017699c50a106988944be8038a9c4d8cbdb68f67bbfc3889d84a2c`.

Java 21, Mill 0.12.3, firtool 1.62.1, Verilator 5.020 and clang 19 were reused; no new environment packages were installed. The native build and EMU remain under `/home/amesotten/.cache/codex-rvinno/o1-complete-20261018`; the large executable is not duplicated here. All compiler inputs, dependency pins, commands, flags and binary/RTL hashes required to audit its identity are recorded. Offline replay needs neither this cache nor an EMU/NEMU installation.

From the repository checkout in WSL, with the reviewed checker sources and existing independent matrix parent corpus present, choose a fresh output directory:

```sh
python3 -OO -B team/evidence/o1-complete-20261018/recheck.py --output /tmp/o1-complete-recheck
```

Expected: `O1_EXTENDED_ARCHIVE_RECHECK_PASS`. Reusing an output directory is rejected. This recomputes recorded evidence; it is not another hardware execution, rebuild or formal equivalence proof. Historical archives are unchanged. Current O1 original/lean plans, full same-source baseline/T14/O1 performance A/B, STA/PPA, virtualization and official ISA acceptance remain separate work.
