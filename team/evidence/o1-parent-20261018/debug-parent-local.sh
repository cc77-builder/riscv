#!/usr/bin/env bash
set -euo pipefail
base=/home/amesotten/.cache/codex-rvinno/o1-parent-20261018
obj="$base/attempt-06/mode-0/obj"
out="$base/$1"
mkdir "$out"
exec > >(tee "$out/run.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$out/run.status"' EXIT
cp /mnt/c/Code/RVInno/riscv/team/optimizations/o1/parent_test.cpp "$out/parent_test.cpp"
g++ -std=c++17 -O2 -I"$obj" -I/usr/share/verilator/include -I/usr/share/verilator/include/vltstd \
  "$out/parent_test.cpp" "$obj/VVDotExuTestTop__ALL.a" "$obj/verilated.o" "$obj/verilated_threads.o" \
  -pthread -latomic -o "$out/parent_test"
"$out/parent_test" "$base/attempt-06/vectors.tsv" 0 "${2:--}" "${3:-observe-idle}"
