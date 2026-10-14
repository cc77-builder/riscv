#!/usr/bin/env bash
set -euo pipefail
folder=/mnt/c/Code/RVInno/riscv/team/out/t10-positive-wave-20261014
smoke=/mnt/c/Code/RVInno/riscv/team/out/t10-smoke-final-20261014
reader=/home/amesotten/.cache/codex-rvinno/t04/wave-reader
mkdir -p "$folder"
pattern='(funcUnits_4\.io_(in|out)_(valid|ready|bits_(data_src_[014]|res_data|ctrl_(robIdx_(flag|value)|pdest|vecWen|v0Wen|exceptionVec_2)))|\.csrMod\.(io_fromRob_trap_valid|diffArchEvent_delayer\.[io]_(valid|exception|exceptionPC|exceptionInst)|diffCSRState_module\.io_bits_(mepc|mcause|mtval))|\.rob\.difftest_delayer(_[0-9]+)?\.i_(valid|pc|instr)|cycleCnt)'
"$reader" "$smoke/vdot-integration.fst" list "$pattern" > "$folder/signals.csv"
"$reader" "$smoke/vdot-integration.fst" events "$pattern" > "$folder/events.csv"
sha256sum "$smoke/vdot-integration.fst" "$folder/events.csv" "$reader" /home/amesotten/.cache/codex-rvinno/t04/libfst-reader.so > "$folder/raw-artifacts.sha256"
echo T10_POSITIVE_WAVE_EXTRACT_PASS
