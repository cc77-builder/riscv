# O1 observation schema 1

The schema-1 records and this acceptance boundary are preserved. The current
observer additionally emits the versioned [O2 companion](TRACE-EXTENDED.md)
for FTQ and counter windows; only its separate strict entry checks that coverage.

`VDOT_O1_TRACE=1 VDOT_O1_TRACE_PROFILE=frames` selects a simulation observer at elaboration. The default is
off. It can observe baseline (mode 0), T14 (1), or T14+O1 (2). It does not enable
O1 itself. Invalid flag values and mixing with the frozen T12/T13 observers are
rejected. O1 still requires T14, and its legacy-observer guards remain intact.

This observer and parser currently support one hart, MinimalConfig, ROB size 48,
and 8-bit physical destination indices. They do not claim multi-core support.

## Sampling and ownership

EXU and ROB each use an ungated, 64-bit parent-clock counter, with the common
simulation reset required at elaboration. They print a version/configuration
header at cycle zero. All samples describe signals **before the active edge**.
The FU's gated local timer is not used or inferred.

`O1_EXU` is one atomic frame for every cycle with parent busy, input valid,
output valid, or redirect valid. Both sides of an II2 handoff are in that frame.
The parser checks the old owner's result, then applies cancellation/completion,
then records the new acceptance. Only vdot-to-vdot can overlap in mode 2.

| Fields | Meaning |
| --- | --- |
| `cycle`, `busy`, `iv`, `ir` | Parent cycle, pre-edge ownership and request handshake |
| `kind`, `irf`, `irv`, `id`, `iwv`, `iw0` | New request: kind 0/1/2 = VDot/VIDiv/VFDiv, ROB flag/index, destination and write class |
| `ca`, `cv` | Actual child acceptance/response-valid masks, in the same kind order |
| `a`, `b`, `vl`, `vill`, `vm`, `sew`, `lmul`, `start`, `op` | Actual VDot input operands and control; `vl` is the renamed physical source |
| `ov`, `ready`, `orf`, `orv`, `od`, `owv`, `ow0` | Old response validity, handshake and destination identity |
| `data`, `vec`, `v0`, `exc`, `ff` | Full 128-bit shared/vector/v0 outputs, exception mask and FP flags |
| `fv`, `frf`, `frv`, `self`, `kill` | Redirect valid, target ROB, flush-self and parent cancellation |

ROB prints `O1_ROB_ENQ`, `O1_ROB_COMMIT`, and `O1_ROB_REDIRECT`. Allocation uses
the real `canEnqueue && !redirect.valid` condition. Instruction encoding, PC,
physical destination and circular ROB identity remain bound through commit.
Same-cycle print order across modules is not an architectural order.

CtrlBlock sends ROB `s1_s3_redirect`, and sends EXU its registered
`s2_s4_redirect`. The parser requires an exact one-cycle shift with identical
ROB/self fields for **every** redirect. A request accepted on the earlier ROB
redirect cycle can be canceled at the following EXU edge. An already completed
response can also be architecturally squashed before commit. A reused ROB
pointer starts a new allocation; it does not inherit the previous response.

VDot suppresses a killed response combinationally. Production dividers may
still expose their raw response on the cancellation cycle; cancellation wins
over its handshake in the observer ledger.

## Checks and evidence boundaries

The parser rejects malformed/duplicate/missing fields, invalid widths, missing
busy cycles, duplicate timestamps, invalid ready/handshake combinations,
unsolicited or withdrawn outputs, identity changes, unfinished tails and
transaction-count disagreement. It independently calculates eight signed byte
products, the 32-bit result with zero high 96 bits, and VDot illegal controls.
All three writeback ports are compared, including while backpressured.

Parent scope requires the actual C++ harness's independent completion summary
and seven reset epochs, with six pending requests cleared by reset. Full-core
scope requires exactly one matching EXU/ROB epoch and complete ROB lifecycles.
It never treats a fabricated extra reset header as permission to discard a
CPU transaction. Divider numerical/ISA validation is outside this parser;
the real-parent C++ harness and CPU DiffTest provide separate checks.

`O1_TRACE_PROTOCOL_PASS_ARCHITECTURAL_VALIDATION_SEPARATE` certifies the parsed
protocol only. A software pass marker, source manifest or parser fixture alone
does not prove a CPU run. The separate `run_trace_core.py` entry checks the
completed build, exact images/reference, real return codes, live DiffTest and
the frozen control plan's expected retirement count.

Schema 1 does not record FTQ wrap. The full T12 gate, exception matrix, DiffTest
negative control, T13 calibrated performance A/B and PPA remain separate work.
Missing coverage is listed, never counted as observed coverage. None of these
entries changes the default O1 mode or the historical acceptance profiles.

## Commands

From a prepared Linux/WSL repository root with the existing Mill/Verilator tools:

```bash
VDOT_O1_TRACE=1 VDOT_O1_TRACE_PROFILE=frames bash team/optimizations/o1/check-parent.sh /absolute/fresh/output
python3 -OO -B -m unittest discover -s team/optimizations/o1 -p 'test_*.py' -v
python3 -OO -B team/optimizations/o1/audit_trace_negatives.py \
  /absolute/fresh/output/mode-2/results.log --output /absolute/negatives.json
python3 -OO -B team/optimizations/o1/check_trace.py /absolute/stderr.log \
  --mode 2 --scope fullcore --output /absolute/trace-check.json
```

The parent runner preserves compiler inputs, actual RTL, lint/build logs,
binary outputs and fault injections. `parent-trace.vlt` waives only the same
reviewed divider expression as `parent.vlt`; the extra nine printf-header lines
move it from line 37 to 46. The exact expression is checked before applying the
waiver. No general warning suppression was added.
