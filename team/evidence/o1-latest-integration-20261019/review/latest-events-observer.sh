#!/usr/bin/env bash
set -euo pipefail
base=/home/amesotten/.cache/codex-rvinno/latest-integration-20261018
root="$base/source-8fb056f7b742ffc4"
out="$base/events-observer-01"
mkdir "$out"
exec > "$out/runner.log" 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$out/runner.status"' EXIT
cd "$root"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=2
export JAVA_OPTS='-Xmx6G -Xss16m' COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export PATH=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$PATH
source team/scripts/activate.sh
export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"
export VDOT_O1_HANDOFF=1 VDOT_T14_FUSED_INPUT=1 VDOT_O1_TRACE=1 VDOT_O1_TRACE_PROFILE=events
export VDOT_T12_TRACE=0 VDOT_T13_TRACE=1
env | sort | grep '^VDOT_' > "$out/flags.txt"
mill -i -j 2 vdotParent.runMain team.vdot.GenerateVDotParent "$out/rtl" > "$out/elaboration.log" 2>&1
mapfile -t rtl < <(find "$out/rtl" -type f \( -name '*.sv' -o -name '*.v' \) | sort)
python3 -B - "$out/rtl/IterBlockI8Nr4.sv" <<'PY'
from pathlib import Path
import sys
if Path(sys.argv[1]).read_text().splitlines()[45].strip() != "_GEN[{1'h0, io_pre_w[8]} + 2'h1] + {io_pre_w[7:0], io_pre_w_low[7]};":
    raise SystemExit('Reviewed divider width waiver no longer matches')
PY
waiver="$root/team/optimizations/o1/parent-trace.vlt"
verilator --lint-only --assert --top-module VDotParentTestTop "$waiver" "${rtl[@]}" > "$out/lint.log" 2>&1
verilator --cc --exe --build --assert --top-module VDotParentTestTop --Mdir "$out/obj" -j 2 \
  -CFLAGS '-std=c++17 -O2 -DO1_PARENT_HANDOFF=1' "$waiver" "${rtl[@]}" \
  "$root/team/optimizations/o1/parent/parent_test.cpp" > "$out/build.log" 2>&1
"$out/obj/VVDotParentTestTop" "$base/events-parent-01/vectors.tsv" > "$out/result.log" 2>&1
python3 -B - "$out" <<'PY'
from pathlib import Path
import hashlib,json,re,sys
out=Path(sys.argv[1]);raw=(out/'result.log').read_bytes();text=raw.decode()
def require(ok,message):
    if not ok:raise ValueError(message)
require(len(re.findall(r'^O1_PARENT_PASS mode=1 ',text,re.M))==1,'missing parent pass')
require('O1_SCHEMA version=' in text and 'O1_HANDOFF cycle=' in text,'missing event observer')
require('O1_EXU' not in text and 'O2_' not in text,'mixed observer protocols')
require('O1_PARENT_FAIL' not in text,'parent failed')
files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'rtl').rglob('*') if p.is_file()}
files['obj/VVDotParentTestTop']=hashlib.sha256((out/'obj/VVDotParentTestTop').read_bytes()).hexdigest()
(out/'artifacts.json').write_text(json.dumps(files,indent=2)+'\n')
(out/'verification.json').write_text(json.dumps(dict(status='EVENTS_PARENT_OBSERVER_PASS',
  raw_sha256=hashlib.sha256(raw).hexdigest(),event_frames=len(re.findall(r'^O1_',text,re.M)),
  scope='parent execution and event-only emission; not full-core ROB/CSR or performance validation'),indent=2)+'\n')
print('EVENTS_PARENT_OBSERVER_PASS')
PY
