#!/usr/bin/env bash
# Three real VFEX4 modes. Fresh outputs and fail-closed status, including lint.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
[[ $# == 1 && "$1" == /* && ! -e "$1" ]] || { echo 'Usage: check-parent.sh /absolute/new/output'; exit 2; }
out=$(realpath -m "$1")
case "$out/" in "$root/team/evidence/"*|"$root/team/optimizations/"*|"$root/src/"*) exit 2;; esac
mkdir -p "$out"
exec > >(tee "$out/runner.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$out/runner.status"' EXIT
cd "$root"
source team/scripts/activate.sh
for tool in python3 java mill verilator clang++ rg; do command -v "$tool"; done
export CHISEL_FIRTOOL_PATH=${CHISEL_FIRTOOL_PATH:-"$HOME/.cache/llvm-firtool/1.62.1/bin"}
export JAVA_OPTS=${JAVA_OPTS:-"-Xmx6G -Xss16m"}
jobs=${BUILD_JOBS:-2}
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || exit 2
export VDOT_T12_TRACE=0 VDOT_T13_TRACE=0
waiver=team/optimizations/o1/parent.vlt
waiver_line=37
if [[ "${VDOT_O1_TRACE:-0}" == 1 ]]; then
  waiver=team/optimizations/o1/parent-trace.vlt
  waiver_line=46
fi
git rev-parse HEAD > "$out/source.commit"
git diff --binary HEAD > "$out/working-tree.patch"
git submodule status --recursive > "$out/submodules.txt"
java -version
mill --version
verilator --version
clang++ --version
"$CHISEL_FIRTOOL_PATH/firtool" --version
# Save physical compiler/test inputs, including new files, and check them after execution.
python3 -B - "$out" <<'PY'
import hashlib, json, runpy, sys, tarfile
from pathlib import Path
root=Path.cwd(); out=Path(sys.argv[1])
helper=runpy.run_path('team/scripts/prepare-core-baseline.py')
dependencies=helper['modules'](root)
helper['verify_dependencies'](root,dependencies)
(out/'dependencies.json').write_text(json.dumps(dependencies,sort_keys=True,indent=2)+'\n')
names=set(helper['root_inputs'](root))
for directory in ('team/rtl/vdot','team/models/vdot','team/optimizations/o1'):
    names.update(p.as_posix() for p in Path(directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
with tarfile.open(out/'inputs.tar.gz','w:gz') as archive:
    for name in sorted(names): archive.add(name,arcname=name)
with (out/'source.sha256').open('w') as receipt:
    for name in sorted(names): receipt.write(hashlib.sha256(Path(name).read_bytes()).hexdigest()+'  '+name+'\n')
PY
python3 -B team/rtl/vdot/prepare_vectors.py team/models/vdot/data "$out/vectors.tsv"
set -x
for mode in 0 1 2; do
  export VDOT_T14_FUSED_INPUT=0 VDOT_O1_HANDOFF=0
  [[ "$mode" == 0 ]] || export VDOT_T14_FUSED_INPUT=1
  [[ "$mode" != 2 ]] || export VDOT_O1_HANDOFF=1
  dir="$out/mode-$mode"
  mkdir "$dir"
  mill -i -j "$jobs" vdotExu.runMain team.vdot.GenerateVDotExu "$dir/rtl" > "$dir/elaboration.log" 2>&1
  # Include the production latch-based ClockGate, never substitute an open gate.
  mapfile -d '' rtl < <(find "$dir/rtl" -maxdepth 1 -name '*.sv' -print0 | sort -z)
  python3 -B - "$dir/rtl/IterBlockI8Nr4.sv" "$waiver_line" <<'PY'
import sys
from pathlib import Path
lines=Path(sys.argv[1]).read_text().splitlines()
if lines[int(sys.argv[2])-1].strip() != "_GEN[{1'h0, io_pre_w[8]} + 2'h1] + {io_pre_w[7:0], io_pre_w_low[7]};":
    raise SystemExit('Reviewed divider width waiver no longer matches')
PY
  verilator --lint-only --assert --top-module VDotExuTestTop "$waiver" "${rtl[@]}" > "$dir/lint.log" 2>&1
  verilator --cc --exe --build --assert --top-module VDotExuTestTop \
    --Mdir "$dir/obj" -j "$jobs" -CFLAGS '-std=c++17 -O2' \
    "$waiver" "${rtl[@]}" "$root/team/optimizations/o1/parent_test.cpp" > "$dir/build.log" 2>&1
  "$dir/obj/VVDotExuTestTop" "$out/vectors.tsv" "$mode" - strict-idle 2>&1 | tee "$dir/results.log"
  grep -q "^VFEX4_PARENT_PASS mode=$mode " "$dir/results.log"
  if [[ "${VDOT_O1_TRACE:-0}" == 1 ]]; then
    python3 -B team/optimizations/o1/check_trace.py "$dir/results.log" --mode "$mode" --scope parent --output "$dir/trace-check.json"
  fi
done
for fault in identity wen high cancel; do
  rc=0
  "$out/mode-2/obj/VVDotExuTestTop" "$out/vectors.tsv" 2 "$fault" > "$out/inject-$fault.log" 2>&1 || rc=$?
  python3 -B team/optimizations/o1/check_parent_negative.py --fault "$fault" \
    --return-code "$rc" --log "$out/inject-$fault.log"
done
sha256sum -c "$out/source.sha256" > "$out/source-after.log"
python3 -B - "$out" <<'PY'
import json, runpy, sys
from pathlib import Path
helper=runpy.run_path('team/scripts/prepare-core-baseline.py')
helper['verify_dependencies'](Path.cwd(),json.loads((Path(sys.argv[1])/'dependencies.json').read_text()))
PY
echo 'VFEX4_PARENT_RUNNER_PASS_FULLCORE_PENDING'
