#!/usr/bin/env bash
set -euo pipefail
src=/home/amesotten/.cache/codex-rvinno/o1-parent-20261018/source-a02cb6dc9e84c327
if [[ ! -d "$src/out" ]]; then
  cp -a /home/amesotten/.cache/codex-rvinno/o1-integration-20261018/source-6ee2e8f10475549e/out "$src/out"
fi
cp /mnt/c/Code/RVInno/riscv/team/optimizations/o1/parent_test.cpp /mnt/c/Code/RVInno/riscv/team/optimizations/o1/check-parent.sh "$src/team/optimizations/o1/"
cp /mnt/c/Code/RVInno/riscv/team/optimizations/o1/parent.vlt "$src/team/optimizations/o1/"
cp /mnt/c/Code/RVInno/riscv/team/rtl/vdot/GenerateVDotExu.scala "$src/team/rtl/vdot/"
cp /mnt/c/Code/RVInno/riscv/src/main/scala/xiangshan/backend/exu/ExeUnit.scala "$src/src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
export PATH="/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export JAVA_OPTS='-Xmx6G -Xss16m -XX:ActiveProcessorCount=2'
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export BUILD_JOBS=2
cd "$src"
bash team/optimizations/o1/check-parent.sh "/home/amesotten/.cache/codex-rvinno/o1-parent-20261018/$1"
