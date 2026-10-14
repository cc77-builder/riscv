#!/usr/bin/env bash
set -euo pipefail
folder=/mnt/c/Code/RVInno/riscv/team/out/t10-reference-api-final-20261014
mkdir -p "$folder"
binary=/mnt/c/Code/RVInno/riscv/team/out/nemu-reference-traps-final
old=/home/amesotten/.cache/codex-rvinno/t08/delivered/reference/build/riscv64-nemu-interpreter-so
fixed=/home/amesotten/.cache/codex-rvinno/t10/nemu-compatible/reference/build/riscv64-nemu-interpreter-so
sha256sum /mnt/c/Code/RVInno/riscv/team/tests/nemu_reference_traps.cpp /home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9/build/generated-src/*.h > "$folder/abi-inputs.sha256"
g++ --version > "$folder/compiler.txt"
g++ -std=c++17 -O2 -Wall -Wextra -Werror -MMD -MF "$folder/dependencies.txt" -I/home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9/build/generated-src /mnt/c/Code/RVInno/riscv/team/tests/nemu_reference_traps.cpp -ldl -o "$binary"
sha256sum "$binary" "$old" "$fixed" > "$folder/runtime.sha256"
set +e
"$binary" "$old" > "$folder/old-reset-rejection.log" 2>&1
rc=$?
set -e
printf 'exit_code=%s\n' "$rc" > "$folder/old-reset.status"
test "$rc" = 1
grep -q 'NMIE reset is 0' "$folder/old-reset-rejection.log"
"$binary" "$fixed" > "$folder/fixed-reference.log" 2>&1
printf 'exit_code=0\n' > "$folder/fixed-reference.status"
grep -q 'NEMU_REFERENCE_TRAPS_PASS cases=3' "$folder/fixed-reference.log"
sha256sum -c "$folder/runtime.sha256" > "$folder/runtime-after.log"
echo REFERENCE_RESET_AND_TRAP_CONTRACT_PASS
sha256sum -c "$folder/abi-inputs.sha256" > "$folder/abi-after.log"
