#!/usr/bin/env bash
set -euo pipefail
workspace=/mnt/c/Code/RVInno/riscv
native=/home/amesotten/.cache/codex-rvinno/o1-parent-20261018/source-a02cb6dc9e84c327
for file in src/main/scala/xiangshan/backend/fu/wrapper/VDotO1Trace.scala src/main/scala/xiangshan/backend/exu/ExeUnit.scala src/main/scala/xiangshan/backend/rob/Rob.scala team/optimizations/o1/check_trace.py team/optimizations/o1/check-parent.sh team/optimizations/o1/parent-trace.vlt; do
  cp "$workspace/$file" "$native/$file"
done
cd "$native"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$JAVA_HOME/bin:$PATH
export JAVA_OPTS='-Xmx6G -Xss16m -XX:ActiveProcessorCount=2'
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export CHISEL_FIRTOOL_PATH=/home/amesotten/.cache/llvm-firtool/1.62.1/bin
export BUILD_JOBS=2 VDOT_O1_TRACE=1
bash team/optimizations/o1/check-parent.sh /home/amesotten/.cache/codex-rvinno/o1-trace-20261018/parent-02 > /home/amesotten/.cache/codex-rvinno/o1-trace-20261018/parent-02-terminal.log 2>&1
