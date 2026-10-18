#!/usr/bin/env bash
set -euo pipefail
root=/mnt/c/Code/RVInno/riscv
out=/home/amesotten/.cache/codex-rvinno/o1-merge-20261018
old=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/fu-attempt-03
mkdir "$out"
exec > "$out/run.log" 2>&1
trap 'rc=$?; echo "$rc" > "$out/status"' EXIT
cp "$old/candidate-rtl/VDotFuTestTop.sv" "$out/VDotFuTestTop.sv"
cp "$old/vectors.tsv" "$out/vectors.tsv"
cp "$root/team/optimizations/o1/handoff_test.cpp" "$out/handoff_test.cpp"
sha256sum "$out/VDotFuTestTop.sv" "$out/vectors.tsv" "$out/handoff_test.cpp" > "$out/inputs.sha256"
verilator --version
verilator --lint-only --assert --top-module VDotFuTestTop "$out/VDotFuTestTop.sv"
verilator --cc --exe --build --assert --top-module VDotFuTestTop --Mdir "$out/obj" -j 2 -CFLAGS '-std=c++17 -O2' "$out/VDotFuTestTop.sv" "$out/handoff_test.cpp"
"$out/obj/VVDotFuTestTop" "$out/vectors.tsv" > "$out/result.log" 2>&1
for fault in identity wen high cancel; do
  rc=0
  "$out/obj/VVDotFuTestTop" "$out/vectors.tsv" "$fault" > "$out/$fault.log" 2>&1 || rc=$?
  echo "$rc" > "$out/$fault.status"
  python3 -OO -B "$root/team/optimizations/o1/check_negative.py" --fault "$fault" --return-code "$rc" --log "$out/$fault.log"
done
sha256sum -c "$out/inputs.sha256"
