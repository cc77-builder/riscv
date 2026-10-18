#!/usr/bin/env bash
set -euo pipefail
cache=/home/amesotten/.cache/codex-rvinno/o1-trace-20261018
cd /home/amesotten/.cache/codex-rvinno/o1-parent-20261018/source-a02cb6dc9e84c327
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018/tools:$JAVA_HOME/bin:$PATH
export JAVA_OPTS='-Xmx2G -Xss16m -XX:ActiveProcessorCount=1'
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=1'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
export CHISEL_FIRTOOL_PATH=/home/amesotten/.cache/llvm-firtool/1.62.1/bin
mkdir "$cache/flag-checks"
for scenario in bad-trace mixed-t12 mixed-t13 o1-old-t12 o1-no-fusion; do
  export VDOT_O1_HANDOFF=0 VDOT_T14_FUSED_INPUT=0 VDOT_O1_TRACE=1 VDOT_T12_TRACE=0 VDOT_T13_TRACE=0
  case "$scenario" in
    bad-trace) export VDOT_O1_TRACE=TRUE; expected='VDOT_O1_TRACE must be 0 or 1';;
    mixed-t12) export VDOT_T12_TRACE=1; expected='O1 trace cannot be mixed';;
    mixed-t13) export VDOT_T13_TRACE=1; expected='O1 trace cannot be mixed';;
    o1-old-t12) export VDOT_O1_HANDOFF=1 VDOT_T14_FUSED_INPUT=1 VDOT_O1_TRACE=0 VDOT_T12_TRACE=1; expected='O1 handoff cannot use the frozen';;
    o1-no-fusion) export VDOT_O1_HANDOFF=1; expected='requires VDOT_T14_FUSED_INPUT=1';;
  esac
  rc=0
  mill -i -j 1 vdotExu.runMain team.vdot.GenerateVDotExu "$cache/flag-checks/$scenario-rtl" > "$cache/flag-checks/$scenario.log" 2>&1 || rc=$?
  printf 'exit_code=%s\n' "$rc" > "$cache/flag-checks/$scenario.status"
  test "$rc" -ne 0
  grep -F "$expected" "$cache/flag-checks/$scenario.log" > "$cache/flag-checks/$scenario.reason"
done
echo O1_TRACE_ELABORATION_GUARDS_PASS
