#!/usr/bin/env bash
set -euo pipefail
base=/home/amesotten/.cache/codex-rvinno/o1-integration-20261018
cd "$base/source-6ee2e8f10475549e"
export PATH="$base/tools:$PATH"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export JAVA_OPTS='-Xmx6G -Xss16m -XX:ActiveProcessorCount=2'
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2'
export COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2
source team/scripts/activate.sh
export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"
out=$base/switch-validation
mkdir "$out"
exec > >(tee "$out/runner.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\n" "$rc" > "$out/runner.status"' EXIT
unset VDOT_O1_HANDOFF VDOT_T14_FUSED_INPUT VDOT_T12_TRACE VDOT_T13_TRACE
mill -i -j 2 vdotFu.runMain team.vdot.GenerateVDotFu "$out/default-rtl" > "$out/default.log" 2>&1
cmp "$out/default-rtl/VDotFuTestTop.sv" "$base/fu-attempt-03/legacy-0/rtl/VDotFuTestTop.sv"
echo DEFAULT_UNSET_EQUALS_EXPLICIT_OFF_RTL_PASS
for label in missing-t14 invalid-switch t12-trace t13-trace; do
  export VDOT_O1_HANDOFF=1 VDOT_T14_FUSED_INPUT=1 VDOT_T12_TRACE=0 VDOT_T13_TRACE=0
  case "$label" in
    missing-t14) VDOT_T14_FUSED_INPUT=0; expected='requires VDOT_T14_FUSED_INPUT=1' ;;
    invalid-switch) VDOT_O1_HANDOFF=invalid; expected='VDOT_O1_HANDOFF must be 0 or 1' ;;
    t12-trace) VDOT_T12_TRACE=1; expected='cannot use the frozen T12/T13 observer schema' ;;
    t13-trace) VDOT_T13_TRACE=1; expected='cannot use the frozen T12/T13 observer schema' ;;
  esac
  if mill -i -j 2 vdotFu.runMain team.vdot.GenerateVDotFu "$out/$label" > "$out/$label.log" 2>&1; then
    echo "INVALID_MODE_ACCEPTED=$label"; exit 1
  fi
  grep -Fq "$expected" "$out/$label.log"
  echo "INVALID_MODE_REJECTED=$label"
done
echo O1_SWITCH_VALIDATION_PASS
