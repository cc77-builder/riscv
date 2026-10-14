#!/usr/bin/env bash
# T06 adapter tests use the root Mill project and real XiangShan dependencies.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
evidence=${TEAM_EVIDENCE_DIR:-"$root/team/out/vdot-fu"}
mkdir -p "$evidence"
evidence=$(cd "$evidence" && pwd)
rm -f -- "$evidence/check.json"
mill_bin=${VDOT_MILL:-mill}
command -v "$mill_bin" >/dev/null
"$mill_bin" --version > "$evidence/mill-version.txt" 2>&1
grep -q 'Mill Build Tool version 0.12.3' "$evidence/mill-version.txt"
java -version > "$evidence/java-version.txt" 2>&1
verilator --version > "$evidence/verilator-version.txt"
# Recursive dirty scans over Windows-mounted submodules are very expensive.
# Check their pinned HEADs below and hash their real sources instead; apply this
# only to this run (including the root build's gitStatus resource task).
git_config_count=${GIT_CONFIG_COUNT:-0}
export "GIT_CONFIG_KEY_$git_config_count=diff.ignoreSubmodules"
export "GIT_CONFIG_VALUE_$git_config_count=dirty"
export GIT_CONFIG_COUNT=$((git_config_count + 1))
if test -n "${VDOT_GIT_AUTOCRLF:-}"; then
  export "GIT_CONFIG_KEY_$GIT_CONFIG_COUNT=core.autocrlf"
  export "GIT_CONFIG_VALUE_$GIT_CONFIG_COUNT=$VDOT_GIT_AUTOCRLF"
  export GIT_CONFIG_COUNT=$((GIT_CONFIG_COUNT + 1))
fi
git rev-parse HEAD > "$evidence/team.sha"
git status --short > "$evidence/working-tree.txt"
git submodule status --recursive > "$evidence/submodules.txt"
if grep -q '^[-+U]' "$evidence/submodules.txt"; then
  echo 'Initialize the locked submodules before running real-interface tests.' >&2
  exit 1
fi

# Hash all core/test Scala inputs and the actual dependency sources, including
# ignored or untracked sources. A successful run is bound to physical bytes.
python3 - "$evidence" <<'PY'
import hashlib, json, os, subprocess, sys
from pathlib import Path
root=Path.cwd(); evidence=Path(sys.argv[1])
paths={root/'build.sc',root/'.gitmodules',root/'team/scripts/vdot-fu-tests.sh'}
for folder in ('src/main/scala','src/test/scala','macros','rocket-chip','utility','yunsuan',
               'difftest','fudian','huancun','coupledL2','openLLC'):
    for directory, dirs, files in os.walk(root/folder):
        dirs[:]=[d for d in dirs if d not in ('out','target','.git')]
        for name in files:
            if Path(name).suffix in ('.scala','.sc','.sbt'):
                paths.add(Path(directory)/name)
sources={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
snapshot={'source_sha256':sources,'submodules_sha256':hashlib.sha256((evidence/'submodules.txt').read_bytes()).hexdigest()}
(evidence/'source-manifest.json').write_bytes((json.dumps(snapshot,sort_keys=True,indent=2)+'\n').encode())
PY

export COURSIER_REPOSITORIES=${COURSIER_REPOSITORIES:-https://repo.maven.apache.org/maven2}
export JAVA_OPTS="${JAVA_OPTS:--Xmx6g -XX:ActiveProcessorCount=2}"
printf 'JAVA_OPTS=%q\nCOURSIER_REPOSITORIES=%q\ngit_status_policy=diff.ignoreSubmodules=dirty\n' \
  "$JAVA_OPTS" "$COURSIER_REPOSITORIES" > "$evidence/build-environment.txt"
printf 'VDOT_GIT_AUTOCRLF=%q\n' "${VDOT_GIT_AUTOCRLF:-}" >> "$evidence/build-environment.txt"
mill_command=("$mill_bin" --no-server -j 1 -Djvm-xmx=3G -Djvm-xss=8m)
emit_command=("${mill_command[@]}" xiangshan.test.runMain xiangshan.backend.fu.vector.EmitVdotFu "$evidence/rtl")
printf '%q ' "${emit_command[@]}" > "$evidence/commands.txt"; printf '\n' >> "$evidence/commands.txt"
"${emit_command[@]}" > "$evidence/emit.log" 2>&1
printf '%q ' verilator --lint-only --top-module VdotFu "$evidence/rtl/VdotFu.sv" >> "$evidence/commands.txt"
printf '\n' >> "$evidence/commands.txt"
verilator --lint-only --top-module VdotFu "$evidence/rtl/VdotFu.sv" > "$evidence/lint.log" 2>&1
test_command=("${mill_command[@]}" xiangshan.test.testOnly xiangshan.backend.fu.vector.VdotFuSpec)
printf '%q ' "${test_command[@]}" >> "$evidence/commands.txt"; printf '\n' >> "$evidence/commands.txt"
"${test_command[@]}" > "$evidence/test.log" 2>&1

python3 - "$evidence" <<'PY'
import hashlib, json, os, re, subprocess, sys
from pathlib import Path
root=Path.cwd(); evidence=Path(sys.argv[1])
def require(ok,message):
    if not ok: raise RuntimeError(message)
snapshot=json.loads((evidence/'source-manifest.json').read_bytes())
paths={root/'build.sc',root/'.gitmodules',root/'team/scripts/vdot-fu-tests.sh'}
for folder in ('src/main/scala','src/test/scala','macros','rocket-chip','utility','yunsuan',
               'difftest','fudian','huancun','coupledL2','openLLC'):
    for directory, dirs, files in os.walk(root/folder):
        dirs[:]=[d for d in dirs if d not in ('out','target','.git')]
        for name in files:
            if Path(name).suffix in ('.scala','.sc','.sbt'):
                paths.add(Path(directory)/name)
require({p.relative_to(root).as_posix() for p in paths}==set(snapshot['source_sha256']),'Source set changed during run')
for name,digest in snapshot['source_sha256'].items():
    require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'Source changed during run: '+name)
submodules=subprocess.check_output(['git','submodule','status','--recursive'])
require(hashlib.sha256(submodules).hexdigest()==snapshot['submodules_sha256'],'Submodules changed during run')
log=(evidence/'test.log').read_text()
for marker in ('VDOT_FU_CONFIG_PASS','VDOT_FU_AGE_PASS','VDOT_FU_SCOREBOARD_PASS'):
    require(log.count(marker)==1,'Missing/duplicate interface test: '+marker)
require('All tests passed.' in log and 'Tests: succeeded 3, failed 0' in log,'Incomplete ScalaTest result')
age=re.search(r'VDOT_FU_AGE_PASS pending=(\d+) incoming=(\d+) rob_entries=48',log)
config=re.search(r'VDOT_FU_CONFIG_PASS requests=(\d+) legal=(\d+) illegal=(\d+)',log)
require(age is not None and tuple(map(int,age.groups()))==(18432,18432),'Incomplete ROB-age checks')
require(config is not None,'Missing configuration counts')
requests,legal,illegal=map(int,config.groups())
require(requests==legal+illegal and legal==8 and illegal==28,'Incomplete configuration checks')
counts=re.search(r'cycles=4000 accepted=(\d+) returned=(\d+) cancelled=(\d+) stalled=(\d+) replaced=(\d+) resets=(\d+)',log)
require(counts is not None,'Missing actual scoreboard counts')
accepted,returned,cancelled,stalled,replaced,resets=map(int,counts.groups())
require(accepted==returned+cancelled and min(cancelled,stalled,replaced,resets)>0,'Missing interface-control coverage')
result={'status':'VDOT_XIANGSHAN_FU_INTERFACE_PASS','tests':3,'root_scala_compiled':True,
        'configuration':dict(requests=requests,legal=legal,illegal=illegal),
        'pending_age_checks':int(age.group(1)),'incoming_age_checks':int(age.group(2)),
        'scoreboard':dict(cycles=4000,accepted=accepted,returned=returned,cancelled=cancelled,stalled=stalled,replaced=replaced,resets=resets),
        'source_manifest_sha256':hashlib.sha256((evidence/'source-manifest.json').read_bytes()).hexdigest(),
        'systemverilog_sha256':hashlib.sha256((evidence/'rtl/VdotFu.sv').read_bytes()).hexdigest(),
        'core_integrated':False,'guest_difftest':False,'team_review_signed':False}
(evidence/'check.json').write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(result,sort_keys=True))
PY
