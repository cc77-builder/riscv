#!/usr/bin/env bash
# Candidate T10 tests instantiate the production DecodeStage and the T06 FU.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
evidence=${TEAM_EVIDENCE_DIR:?Set TEAM_EVIDENCE_DIR}
mkdir -p "$evidence"
evidence=$(cd "$evidence" && pwd)
rm -f -- "$evidence/check.json"
mill_bin=${VDOT_MILL:?Set VDOT_MILL to Mill0.12.3}
"$mill_bin" --version > "$evidence/mill-version.txt" 2>&1
grep -q 'Mill Build Tool version 0.12.3' "$evidence/mill-version.txt"
verilator --version > "$evidence/verilator-version.txt"
java -version > "$evidence/java-version.txt" 2>&1
export COURSIER_REPOSITORIES=${COURSIER_REPOSITORIES:-https://repo.maven.apache.org/maven2}
export JAVA_OPTS=${JAVA_OPTS:--Xmx3g -XX:ActiveProcessorCount=2}
export JAVA_TOOL_OPTIONS=${JAVA_TOOL_OPTIONS:--XX:ActiveProcessorCount=2}
# Per-process only: Windows checkout normalization and fast status resources.
export GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_0=diff.ignoreSubmodules GIT_CONFIG_VALUE_0=dirty
export GIT_CONFIG_KEY_1=core.autocrlf GIT_CONFIG_VALUE_1=true
git rev-parse HEAD > "$evidence/team.sha"
git submodule status --recursive > "$evidence/submodules.txt"
if grep -q '^[-+U]' "$evidence/submodules.txt"; then exit 1; fi
snapshot() {
  python3 - "$1" <<'PY'
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path.cwd(); paths={root/'build.sc',root/'.gitmodules',root/'team/scripts/vdot-decode-tests.sh',root/'team/scripts/vdot_core_checks.py',root/'team/scripts/artifact_guard.py'}
for folder in ('src/main/scala','src/test/scala','macros','rocket-chip','utility','yunsuan',
               'difftest','fudian','huancun','coupledL2','openLLC'):
    for directory,dirs,files in os.walk(root/folder):
        dirs[:]=[d for d in dirs if d not in ('out','target','.git')]
        paths.update(Path(directory)/f for f in files if Path(f).suffix in ('.scala','.sc','.sbt'))
record={'sources':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
        'submodules':subprocess.check_output(['git','submodule','status','--recursive']).decode()}
Path(sys.argv[1]).write_bytes((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
PY
}
snapshot "$evidence/source-before.json"
command=("$mill_bin" --no-server -j 1 -Djvm-xmx=3G -Djvm-xss=8m xiangshan.test.testOnly
         xiangshan.backend.decode.VdotDecodeSpec xiangshan.backend.fu.vector.VdotFuSpec
         xiangshan.backend.fu.vector.VdotTrapInstructionSpec)
printf '%q ' "${command[@]}" > "$evidence/command.txt"; printf '\n' >> "$evidence/command.txt"
set +e
"${command[@]}" > "$evidence/test.log" 2>&1
rc=$?
set -e
printf 'exit_code=%s\n' "$rc" > "$evidence/test.status"
test "$rc" = 0
mkdir -p "$evidence/rtl"
python3 team/scripts/vdot_core_checks.py select-decode-rtl --root "$root" --evidence "$evidence"
verilator --lint-only --top-module VdotDecodeHarness "$evidence/rtl/VdotDecodeHarness.sv" > "$evidence/lint.log" 2>&1
snapshot "$evidence/source-after.json"
cmp "$evidence/source-before.json" "$evidence/source-after.json"
python3 - "$evidence" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]); log=(p/'test.log').read_text()
markers=('VDOT_DECODE_TABLE_PASS register_encodings=32768 overlap=0 owners=1',
         'VDOT_DECODE_STAGE_PASS requests=161 aliases=27 configs=128 stalled=27',
         'VDOT_FU_CONFIG_PASS','VDOT_FU_AGE_PASS','VDOT_FU_SCOREBOARD_PASS',
         'VDOT_TRAP_INSTRUCTION_PASS checks=65586 original_words=32768 buffered_priorities=2')
if not all(log.count(m)==1 for m in markers) or 'Tests: succeeded 6, failed 0' not in log or 'All tests passed.' not in log:
    raise RuntimeError('Incomplete actual decode/FU test coverage')
record=dict(status='VDOT_T10_DECODE_FU_PASS',tests=6,register_encodings=32768,decode_requests=161,trap_instruction_checks=65586,
            source_sha256=hashlib.sha256((p/'source-before.json').read_bytes()).hexdigest(),
            systemverilog_sha256=hashlib.sha256((p/'rtl/VdotDecodeHarness.sv').read_bytes()).hexdigest(),
            core_difftest=False,team_review_signed=False)
(p/'check.json').write_bytes((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(record,sort_keys=True))
PY
