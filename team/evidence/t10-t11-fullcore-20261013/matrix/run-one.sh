#!/bin/bash
set -euo pipefail
b=/home/lizufan/xiangshan-t10-t11-supervisor-20261013
r="$b/closure-tval-repo";j="$b/runs/final-acceptance-20261013-2155";i=$1
case "$i" in 0|1|2|3|4|5|6|7) ;;*)exit 2;;esac
out="$j/run-$i";test ! -e "$out";mkdir "$out"
exec > "$out/driver.log" 2>&1
trap 'exit 143' TERM
trap 'exit 130' INT
trap 'rc=$?; printf "exit_code=%s\nfinished_at=%s\n" "$rc" "$(date -Is)" > "$out/status"' EXIT
root="$b/tools/ubuntu-root"
export PATH="$root/usr/bin:$PATH" LD_LIBRARY_PATH="$root/usr/lib/x86_64-linux-gnu:$root/usr/lib/x86_64-linux-gnu/pulseaudio"
export VDOT_DATA="$b/runs/closure-final-matrix/data-$i" VDOT_IMAGE="$b/runs/closure-final-matrix/build-$i/vdot-exceptions.bin"
export NEMU_HOME="$b/nemu-xs-tval/reference" VDOT_NEMU_REF="$b/nemu-xs-tval/reference/build/riscv64-nemu-interpreter-so"
export VDOT_EMU_BIN="$b/repo/build/emu" TEAM_EVIDENCE_DIR="$out/evidence" VDOT_LOG_COMPACT=1
export VDOT_RUN_TIMEOUT=2100s VDOT_MAX_CYCLES=5000000
cd "$r";test "$(git rev-parse HEAD)" = 1bd6f1d9c9485695876ff37a77fbb175a5125983
git diff --exit-code;git diff --cached --exit-code
git diff --exit-code fcb16a876 -- src build.sc .gitmodules team/versions.env
printf 'started_at=%s\nshard=%s\nsource=%s\n' "$(date -Is)" "$i" "$(git rev-parse HEAD)" > "$out/input.txt"
/usr/bin/time -v -o "$out/resources.txt" bash team/scripts/vdot-tests.sh run-rtl full
echo SHARD_FULLCORE_PASS
