# Fixed-layout campaign, independent ELF audit

Status: **PASS_LAYOUT_AUDIT — 64/64 images** across ours, Jade, Shishui and Redoop (`runs/*-images-02`). No shared harness files were changed by this reviewer.

## Actual linked layout

Every image has the actual ELF symbols:

| Symbol | Address |
|---|---|
| `cases` | `0x80120000` |
| `observed` | `0x80130000` |
| `sink` | `0x80131000` |

Every image has the exact five dedicated input/expected/case/result/sink output sections requested by the archived `fixed-layout.ld`, with section ends within their reserved address ranges. The `Makefile` snapshot replaces the nexus-am `loader64.ld` flag in `LDFLAGS` after including `Makefile.app`; the actual ELF locations prove this replacement took effect. Build logs use quiet `+ LD` output and do not echo the expanded linker command, so no claim is made that the raw logs contain that command.

For every same-name image and corresponding case across the four projects, this audit compared and found identical:

- Function entry addresses, all case input and expected-state pointers, stream and output pointers.
- `observed` and `sink` addresses (therefore their `value` fields also have identical addresses).
- Execution plans, operation counts, complete 128-bit expected states, initial register values and stream buffers.
- The complete compiled RVV baseline machine-code walk, including each PC and instruction word.

Each ELF also passed the current source-snapshot regeneration and compiled-case ABI/bytes checker. Evidence records include all ELF SHA256 values, archived linker-script hashes, section sizes and per-case pointers in `jade-layout-review.json`.

## Compact output

All suites now set compact output, and each manifest reflects `compact=true`. This only changes UART serialization after the timed kernel. The state checks remain before output: guards, iteration count, vector CSRs, every non-scratch full 128-bit register and every stream output. Negative controls remain enabled. The offline checker still reconciles printed counter deltas with CSR/ROB observations and requires DiffTest and GOOD TRAP. This audit does not substitute for those runtime checks.

## Suggested checker hardening

At audit time, `check_compiled_cases` enforced stream alignment and paired-stream aliasing but did not itself require the fixed `cases/observed/sink` addresses or the dedicated section ranges. The independent 64-image audit above supplies that check for this campaign. Adding these assertions to the shared checker would catch a future failure of the Makefile linker-flag substitution automatically.

The linker script leaves generic `.text.*` and `.srodata.*` as GNU ld orphan sections; their current locations do not overlap benchmark sections or change any compared kernel/data addresses. They are not used to claim the whole application binary is identical between implementations. Fixed measured-kernel addresses and required benchmark data addresses were verified directly.
