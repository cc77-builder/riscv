#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
evidence=${TEAM_EVIDENCE_DIR:-"$root/team/out/vdot-hardware"}
mkdir -p "$evidence"
evidence=$(cd "$evidence" && pwd)
# A failed rerun must not leave a previous successful conclusion available.
rm -f -- "$evidence/check.json"
python3 team/tests/generate_vdot_hardware_vectors.py --output "$evidence" > "$evidence/generation.json"
git rev-parse HEAD > "$evidence/team.sha"
git status --short > "$evidence/working-tree.txt"
java -version > "$evidence/java-version.txt" 2>&1
verilator --version > "$evidence/verilator-version.txt"
g++ --version > "$evidence/compiler-version.txt"

if test -n "${VDOT_SBT_LAUNCH_JAR:-}"; then
  sbt_command=(java -XX:ActiveProcessorCount="${BUILD_JOBS:-2}" -Xmx2g)
  if test -n "${VDOT_SBT_REPOSITORIES:-}"; then
    sbt_command+=(-Dsbt.override.build.repos=true "-Dsbt.repository.config=$VDOT_SBT_REPOSITORIES")
  fi
  sbt_command+=(-jar "$VDOT_SBT_LAUNCH_JAR")
else
  command -v sbt >/dev/null
  sbt_command=(sbt -batch -J-XX:ActiveProcessorCount="${BUILD_JOBS:-2}" -J-Xmx2g)
fi
export VDOT_HW_VECTORS="$evidence/vectors.tsv"
emit_command="runMain EmitVdot \"$evidence/rtl\""
printf '%q ' "${sbt_command[@]}" "$emit_command" > "$evidence/commands.txt"
printf '\n' >> "$evidence/commands.txt"
(cd team/hardware/vdot && "${sbt_command[@]}" "$emit_command") > "$evidence/emit.log" 2>&1
printf '%q ' verilator --lint-only --top-module VdotExec "$evidence/rtl/VdotExec.sv" >> "$evidence/commands.txt"
printf '\n' >> "$evidence/commands.txt"
verilator --lint-only --top-module VdotExec "$evidence/rtl/VdotExec.sv" > "$evidence/lint.log" 2>&1
printf 'VDOT_HW_VECTORS=%q ' "$VDOT_HW_VECTORS" >> "$evidence/commands.txt"
printf '%q ' "${sbt_command[@]}" test >> "$evidence/commands.txt"
printf '\n' >> "$evidence/commands.txt"
(cd team/hardware/vdot && "${sbt_command[@]}" test) > "$evidence/test.log" 2>&1

python3 - "$evidence" <<'PY'
import hashlib, json, re, sys
from pathlib import Path
evidence=Path(sys.argv[1]);root=Path.cwd()
def require(ok,message):
    if not ok: raise RuntimeError(message)
metadata=json.loads((evidence/'vectors-manifest.json').read_text())
require(hashlib.sha256((evidence/'vectors.tsv').read_bytes()).hexdigest()==metadata['vectors_sha256'],'Vectors changed during run')
for name,digest in metadata['source_sha256'].items():
    require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Source changed during run: '+name)
log=(evidence/'test.log').read_text()
markers=['VDOT_HW_MODEL_PASS','VDOT_HW_BACKPRESSURE_PASS','VDOT_HW_CANCEL_PASS','VDOT_HW_SCOREBOARD_PASS']
for marker in markers: require(log.count(marker)==1,'Missing/duplicate hardware check: '+marker)
require('All tests passed.' in log and 'Tests: succeeded 4, failed 0' in log,'Incomplete ScalaTest result')
counts=re.search(r'cycles=4000 accepted=(\d+) returned=(\d+) cancelled=(\d+) stalled=(\d+)',log)
require(counts is not None,'Missing actual scoreboard counts')
accepted,returned,cancelled,stalled=map(int,counts.groups())
require(accepted==returned+cancelled and cancelled>0 and stalled>0,'Incorrect request conservation')
result=dict(status='VDOT_STANDALONE_RTL_PASS',vectors=metadata['vectors'],legal=metadata['legal'],illegal=metadata['illegal'],
            vectors_sha256=metadata['vectors_sha256'],source_sha256=metadata['source_sha256'],
            scoreboard=dict(cycles=4000,accepted=accepted,returned=returned,cancelled=cancelled,stalled=stalled),
            systemverilog_sha256=hashlib.sha256((evidence/'rtl/VdotExec.sv').read_bytes()).hexdigest(),
            core_integrated=False,guest_difftest=False,frequency_or_area_measured=False)
(evidence/'check.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(result,sort_keys=True))
PY
