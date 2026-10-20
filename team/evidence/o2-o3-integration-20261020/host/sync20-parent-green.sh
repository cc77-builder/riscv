#!/usr/bin/env bash
set -euo pipefail
base=/home/amesotten/.cache/codex-rvinno/sync20
workspace=/mnt/c/Code/RVInno/riscv
native=$(cat "$workspace/team/out/sync20-rtl-pack-red-windows/build-copy.txt")
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$JAVA_HOME/bin:$PATH
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export CHISEL_FIRTOOL_PATH=/home/amesotten/.cache/llvm-firtool/1.62.1/bin
cd "$native"
python3 -B - "$base" "$workspace" <<'PY'
from pathlib import Path
import hashlib,json,sys
base,root=map(Path,sys.argv[1:])
red=base/'parent-red-01'
assert json.loads((red/'runner.status.json').read_text())['passed'] is False
assert 'canceled DIV retained idle clock hold' in (red/'result.log').read_text()
commands=json.loads((red/'commands.json').read_text())
assert commands[-1]['log']=='result.log' and commands[-1]['exit_code']==1
copied={}
for name in ('src/main/scala/xiangshan/backend/exu/ExeUnit.scala',
             'team/optimizations/o2/parent/check_trace.py','team/optimizations/o2/parent/test_trace.py'):
    raw=(root/name).read_bytes().replace(b'\r\n',b'\n')
    Path(name).write_bytes(raw);copied[name]=hashlib.sha256(raw).hexdigest()
(base/'green-overlays.json').write_text(json.dumps(copied,indent=2)+'\n')
print('RED_CLOCK_HOLD_REPRODUCED',flush=True)
PY
python3 -B team/optimizations/o2/run_rtl.py parent "$base/parent-green-01"
python3 -B team/optimizations/o2/parent/check_trace.py --log "$base/parent-green-01/result.log" --output "$base/parent-green-01/independent-trace.json"
export VDOT_O2_ELASTIC=0 VDOT_O2_TRACE=0 VDOT_O1_TRACE=1
export JAVA_OPTS='-Xmx6G -Xss16m -XX:ActiveProcessorCount=2' BUILD_JOBS=2
bash team/optimizations/o1/check-parent.sh "$base/legacy-frames-01"
