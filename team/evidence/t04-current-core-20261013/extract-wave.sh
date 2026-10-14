#!/usr/bin/env bash
set -euo pipefail
folder=/mnt/c/Code/RVInno/riscv/team/out/t04-current-20261013
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$folder/wave-extract.status"' EXIT
reader=/home/amesotten/.cache/codex-rvinno/t04/wave-reader
pattern='(\.VialuFix\.io_(in|out)_(valid|ready|bits_(ctrl_fuOpType|ctrl_vpu_vsew|data_src_[01]|res_data))|\.backend\.inner_ctrlBlock\.rob\.difftest_delayer(_[0-9]+)?\.(i_valid|i_pc|i_instr|i_vecwen|i_wdest)|cycleCnt)'
printf 'signal,handle,width\n' > "$folder/wave-signals.csv"
"$reader" "$folder/hello-vadd.fst" list "$pattern" >> "$folder/wave-signals.csv"
"$reader" "$folder/hello-vadd.fst" events "$pattern" > "$folder/wave-events.csv"
python3 /mnt/c/Code/RVInno/riscv/team/out/t04-summarize-wave.py > "$folder/wave-summary.log"
sha256sum "$folder/hello-vadd.fst" "$folder/wave-events.csv" "$reader" \
  /home/amesotten/.cache/codex-rvinno/t04/libfst-reader.so > "$folder/wave-artifacts.sha256"
