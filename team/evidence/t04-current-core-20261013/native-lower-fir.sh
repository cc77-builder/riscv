#!/usr/bin/env bash
set -euo pipefail
root=/home/amesotten/.cache/codex-rvinno/t04/source-e8bd8d763650fc4f
evidence=/mnt/c/Code/RVInno/riscv/team/out/t04-current-20261013
cd "$root"
exec > >(tee "$evidence/lower-fir.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$evidence/lower-fir.status"' EXIT
python3 team/scripts/prepare-core-baseline.py verify --source /mnt/c/Code/RVInno/riscv \
  --pack /mnt/c/Code/RVInno/riscv/team/out/t04-source-pack-20261013-v3 --target "$root"
sha256sum build/rtl/SimTop.fir > "$evidence/fir-input.sha256"
command=(/home/amesotten/.cache/llvm-firtool/1.62.1/bin/firtool build/rtl/SimTop.fir
         --format=fir --split-verilog -o build/rtl --mlir-disable-threading
         --repl-seq-mem --repl-seq-mem-file=SimTop.sv.conf -O=release
         --disable-annotation-unknown
         --lowering-options=explicitBitcast,disallowLocalVariables,disallowPortDeclSharing,locationInfoStyle=none)
printf '%q ' "${command[@]}" > "$evidence/lower-fir-command.txt"; printf '\n' >> "$evidence/lower-fir-command.txt"
/usr/bin/time -v "${command[@]}"
sha256sum -c "$evidence/fir-input.sha256"
test -s build/rtl/SimTop.sv
test -s build/rtl/SimTop.sv.conf
echo CORE_FIR_LOWERING_PASS
