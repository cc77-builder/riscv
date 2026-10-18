# O1 schema 1 evidence

Engineering report: [o1-trace-20261018.md](../../docs/o1-trace-20261018.md).
This record extends the earlier real-parent clock fix. It does not replace the
frozen T12/T13 archives or promote O1 to the default configuration.

`parent-validation.tar.gz` contains 466 files: three modes of real VFEX4 RTL,
lint/build/runtime logs, executable harnesses, compiler/test inputs, the initial
line-guard rejection, the five successful elaboration negatives and their two
earlier classpath failures, trace-off RTL comparisons, final parser checks,
and eight real-log mutations. Archive SHA-256:
`e2b4b01a76bbfe07de9d5d7b6e1b40cb7902b9e16655aeee810f625c9ed481a2`.

`parent-payload.json` inventories individual archive bytes. `host-tests.log`
records the initial 45 host contract/protocol/entry tests; `host-tests-final.log`
and its source-hash receipt record the final 46 tests. Host fixtures are not DUT
execution evidence. `drivers/` retains the actual build/diagnostic helpers;
their local paths describe this run, not a requirement to overwrite a user's
cache. The failed attempts remain in the archive and are excluded from passing
case counts.

On Linux, replay the archived parent binaries into a **new** directory:

```bash
python3 -OO -B team/evidence/o1-trace-20261018/replay-parent.py /absolute/new/replay
```

This verifies the fixed archive digest and exact file inventory, reruns all
three binaries with strict idle clocks, requires byte-identical raw logs,
re-audits them with the reviewed parser, and repeats the eight corruption
negatives. `parent-02/inputs.tar.gz` is the actual compiler/test input snapshot
at parent build time. Later parser tightening is checked against those same
immutable logs; it does not claim to rebuild the hardware.

`core-validation.tar.gz` contains 61 files: completed build/source/RTL receipts,
the actual raw logs and exit records of hello/vadd, control-pressure-v2 and
frozen batch128, selected software images, and before/after reference checks.
SHA-256: `0fc1f1b3a164683fbdd319f86a8b2308e4cf059c58266a77e02453ed3cc0d302`.
`compiler-inputs.tar.gz` freezes all 437 physical compiler inputs; dependency
revisions and canonical workspace hashes are recorded in `source-pack.json`.
`instrumented-rtl/` preserves the generated EXU and ROB modules with the new
observers; the complete RTL manifest remains in the build archive.

The control run commits 2157 VDots with 384 handoffs, 7 in-flight VDot kills,
41 VDot response stalls and 288 ROB wraps. Batch128 commits 768 VDots with 719
handoffs. All three CPU runs finish with real exit 0 and live DiffTest. These
are observation results; the batch's UART counter values are not accepted as a
calibrated performance comparison.

```bash
python3 -OO -B team/evidence/o1-trace-20261018/recheck-core.py /absolute/new/recheck
```

This independently extracts and recomputes the archived protocol/control/ELF
checks. It does not launch a CPU or count another run. `core-recheck.json` and
`parent-replay-final.json` record the actual independent-directory rechecks.
The full EMU binary stays in the local build cache; its exact SHA-256 and build
commands are archived. `review-inputs.tar.gz` binds the final checker/runner/test
sources, including changes after the initial parent compilation. `files.json`
seals this evidence directory; archives and failure logs are not overwritten.

Schema 1 explicitly lacks FTQ wrap and CSR counter-window observations. Full T12 coverage, the complete
exception matrix, CPU DiffTest fault injection and calibrated T13 performance
comparisons remain distinct gates.
