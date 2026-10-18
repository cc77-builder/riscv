#!/usr/bin/env bash
set -euo pipefail
workspace=/mnt/c/Code/RVInno/riscv
cache=/home/amesotten/.cache/codex-rvinno/o1-trace-20261018
previous=/home/amesotten/.cache/codex-rvinno/o1-parent-20261018/source-a02cb6dc9e84c327
pack=$workspace/team/out/o1-trace-20261018-core-pack
mkdir -p "$cache/core-build"
exec > "$cache/core-build/launch.log" 2>&1
python3 -B "$workspace/team/scripts/prepare-core-baseline.py" materialize --source "$previous" --pack "$pack" --cache "$cache"
native=$(cat "$pack/build-copy.txt")
cp -a "$previous/out" "$native/out"
cd "$native"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$JAVA_HOME/bin:$PATH
export CORE_MILL=/home/amesotten/.cache/codex-rvinno/fullcore-20261016/mill
export CORE_FIRTOOL=/home/amesotten/.cache/llvm-firtool/1.62.1/bin/firtool
export CHISEL_FIRTOOL_PATH=/home/amesotten/.cache/llvm-firtool/1.62.1/bin
export JAVA_OPTS='-Xmx1G -XX:ActiveProcessorCount=2'
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export NEMU_HOME=/home/amesotten/.cache/codex-rvinno/t08/delivered/reference
export AM_HOME=/home/amesotten/.cache/codex-t05/nexus-am-086a238
export CORE_SOURCE_PACK=$pack TEAM_EVIDENCE_DIR=$cache/core-build
export CORE_OPT_FAST=-O3 CORE_COMPILE_JOBS=2
export VDOT_T14_FUSED_INPUT=1 VDOT_O1_HANDOFF=1 VDOT_O1_TRACE=1 VDOT_T12_TRACE=0 VDOT_T13_TRACE=0
env | sort | grep -E '^(VDOT_|CORE_|JAVA_|CHISEL_|NEMU_|AM_)' > "$cache/core-build/environment.txt"
bash team/scripts/core-baseline-split.sh
