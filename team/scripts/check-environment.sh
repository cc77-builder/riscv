#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
source "$TEAM_PROJECT_ROOT/team/versions.env"
cd "$NOOP_HOME"
git merge-base --is-ancestor "$XSHARDWARE_REV" HEAD
for pair in "$TEAM_XS_ENV_ROOT:$XSENV_REV" "$NEMU_HOME:$NEMU_REV" "$AM_HOME:$AM_REV" "$DRAMSIM3_HOME:$DRAMSIM3_REV" "$NOOP_HOME/difftest:$DIFFTEST_REV" "$NOOP_HOME/yunsuan:$YUNSUAN_REV"; do
  path=${pair%:*}
  revision=${pair##*:}
  test "$(git -C "$path" rev-parse HEAD)" = "$revision" || { echo "Revision mismatch: $path" >&2; exit 1; }
  printf '%s %s\n' "$path" "$revision"
done
while IFS= read -r module; do
  case "$module" in [-+U]*) echo "Submodule mismatch: $module" >&2; exit 1 ;; esac
done < <(git submodule status --recursive)
java_info=$(java -version 2>&1)
clang_info=$(clang --version)
verilator_info=$(verilator --version)
cross_info=$(riscv64-linux-gnu-gcc -dumpfullversion)
as_info=$(riscv64-linux-gnu-as --version)
mill_info=$(mill --version)
[[ "$java_info" == *'"21.0.12"'* && "$java_info" == *GraalVM* ]]
[[ "$clang_info" == *'19.1.7'* ]]
[[ "$verilator_info" == *'Verilator 5.052'* ]]
[[ "$cross_info" == '11.4.0' ]]
[[ "$as_info" == *'2.38'* ]]
[[ "$mill_info" == *'Mill Build Tool version 0.12.3'* ]]
for tool in make g++ python3 cmake ninja timeout; do command -v "$tool"; done
test -x /usr/bin/time
printf '%s\n' "$java_info" "$clang_info" "$verilator_info" "$cross_info" "$as_info" "$mill_info"
echo ENVIRONMENT_CHECK_PASS
