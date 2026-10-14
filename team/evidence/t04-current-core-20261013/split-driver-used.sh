#!/usr/bin/env bash
# Lower a completed FIR dump separately, then resume the normal Make emu flow.
# Run from the source-bound native Linux checkout, not a different xs-env tree.
set -euo pipefail
root=$(pwd)
test -f "$root/build/source-binding.json"
test -f "$root/team/scripts/core-baseline.sh"
evidence=${TEAM_EVIDENCE_DIR:?Set TEAM_EVIDENCE_DIR}
mkdir -p "$evidence"
evidence=$(cd "$evidence" && pwd)
rm -f -- "$evidence/check.json"
exec > >(tee "$evidence/split-build.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$evidence/split-build.status"' EXIT
source_pack=${CORE_SOURCE_PACK:?Set CORE_SOURCE_PACK to the matching frozen pack directory}
source_repo=$(python3 -c 'import json; print(json.load(open("build/source-binding.json"))["source"])')
python3 "$root/team/scripts/prepare-core-baseline.py" verify --source "$source_repo" --pack "$source_pack" --target "$root"
firtool=${CORE_FIRTOOL:?Set CORE_FIRTOOL to the Chisel6.6-compatible firtool1.62.1}
"$firtool" --version > "$evidence/firtool-version.txt"
grep -q '1.62.1' "$evidence/firtool-version.txt"
# Prefer generating FIR in a fresh process, before starting native lowering.
# Make's FIR-only target deliberately skips its SystemVerilog post-processing.
if test "${CORE_REUSE_FIR:-0}" != 1; then
  mill_bin=${CORE_MILL:?Set CORE_MILL to Mill0.12.3}
  mkdir -p build/tools
  printf '#!/bin/sh\nexec "%s" "$@"\n' "$mill_bin" > build/tools/mill
  chmod +x build/tools/mill
  export PATH="$root/build/tools:$PATH"
  export NOOP_HOME="$root"
  export JAVA_OPTS=${JAVA_OPTS:--Xmx1g -XX:ActiveProcessorCount=2}
  export JAVA_TOOL_OPTIONS=${JAVA_TOOL_OPTIONS:--XX:ActiveProcessorCount=2}
  export COURSIER_REPOSITORIES=${COURSIER_REPOSITORIES:-https://repo.maven.apache.org/maven2}
  /usr/bin/time -v make sim-verilog CONFIG=MinimalConfig NUM_CORES=1 JVM_XMX=6G JVM_XSS=16m CHISEL_TARGET=chirrtl -j1
else
  # Explicit recovery only: preserve the original elaboration logs and binding.
  test -s "$evidence/fir-input.sha256"
  sha256sum -c "$evidence/fir-input.sha256"
fi
test -s build/rtl/SimTop.fir
sha256sum build/rtl/SimTop.fir > "$evidence/fir-input.sha256"
if test "${CORE_REUSE_LOWERED:-0}" != 1; then
  command=("$firtool" build/rtl/SimTop.fir --format=fir --split-verilog -o build/rtl
           --mlir-disable-threading --repl-seq-mem --repl-seq-mem-file=SimTop.sv.conf
           -O=release --disable-annotation-unknown
           --lowering-options=explicitBitcast,disallowLocalVariables,disallowPortDeclSharing,locationInfoStyle=none)
  printf '%q ' "${command[@]}" > "$evidence/lower-fir-command.txt"; printf '\n' >> "$evidence/lower-fir-command.txt"
  /usr/bin/time -v "${command[@]}"
  sha256sum build/rtl/*.sv build/rtl/SimTop.sv.conf > "$evidence/lowered-rtl.sha256"
else
  test "$(cat "$evidence/lower-fir.status")" = exit_code=0
  grep -q CORE_FIR_LOWERING_PASS "$evidence/lower-fir.log"
  sha256sum -c "$evidence/lowered-rtl.sha256" > "$evidence/reused-rtl-check.log"
fi
sha256sum -c "$evidence/fir-input.sha256"
test -s build/rtl/SimTop.sv
test -s build/rtl/SimTop.sv.conf
# These are the same memory generation and assertion handling as root Makefile.
bash ./scripts/gen_sep_mem.sh ./scripts/vlsi_mem_gen build/rtl/SimTop.sv.conf build/rtl
python3 - <<'PY'
from pathlib import Path
import subprocess
top=Path('build/rtl/SimTop.sv')
history=subprocess.check_output(['git','log','-n','1'])+subprocess.check_output(['git','diff'])
header=b''.join(b'//'+line+b'\n' for line in history.splitlines())
top.write_bytes(header+top.read_bytes())
for path in Path('build/rtl').glob('*.sv'):
    data=path.read_bytes().replace(b'$fatal', b'xs_assert_v2(`__FILE__, `__LINE__)')
    data=data.replace(b'$error(', b'$fwrite(32\'h80000002, ')
    path.write_bytes(data)
PY
sha256sum build/rtl/*.sv > "$evidence/rtl.sha256"
sha256sum "$0" > "$evidence/split-driver.sha256"
echo CORE_SPLIT_RTL_PREPARED
bash "$root/team/scripts/core-baseline.sh" build
echo CORE_SPLIT_BUILD_PASS
