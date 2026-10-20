#!/usr/bin/env bash
set -euo pipefail
base=/home/amesotten/.cache/codex-rvinno/sync20
native=$base/source-d13def17dc8de4b8
workspace=/mnt/c/Code/RVInno/riscv
out=$base/o4-compile-02
mkdir "$out"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$JAVA_HOME/bin:$PATH
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export CHISEL_FIRTOOL_PATH=/home/amesotten/.cache/llvm-firtool/1.62.1/bin
cd "$native"
python3 -B - "$workspace" "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys
root,out=map(Path,sys.argv[1:]);record={}
for name in ('build.sc','team/optimizations/o4/GenerateVDotCost.scala'):
    data=(root/name).read_bytes().replace(b'\r\n',b'\n');dest=Path(name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);record[name]=hashlib.sha256(data).hexdigest()
(out/'overlays.json').write_text(json.dumps(record,indent=2)+'\n')
PY
set +e
mill -i -j 2 vdotCost.compile > "$out/compile.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$out/exit-code.txt"
cat "$out/compile.log"
exit "$rc"
