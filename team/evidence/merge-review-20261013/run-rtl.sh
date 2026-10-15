#!/usr/bin/env bash
set -euo pipefail
run=/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/validation-20261013
source "$run/env.sh"
cd /home/lizufan/xiangshan-validation-20261013/repo
test "$(git rev-parse HEAD)" = 45bea984445e6f07d0d9c0ee8e42302e225ba0b3
test -z "$(git status --porcelain=v1)"
stamp=$(date +%Y%m%d-%H%M%S)-$$
outbase=/home/lizufan/xiangshan-validation-20261013/runs/$stamp
mkdir -p "$outbase"
printf '%s\n' "$outbase" > "$run/rtl-output-path.txt"
exec > >(tee "$run/rtl-runner.log") 2>&1
trap 'rc=$?; echo "exit_code=$rc end=$(date -Is)" > "$run/rtl-runner.status"' EXIT
for script in team/scripts/check-vdot-{model,datapath,fu}.sh; do bash -n "$script"; done
set +e
VDOT_OUT_DIR="$outbase/datapath" bash team/scripts/check-vdot-datapath.sh
dp=$?
printf 'datapath_exit=%s\n' "$dp"
VDOT_OUT_DIR="$outbase/fu" bash team/scripts/check-vdot-fu.sh
fu=$?
printf 'fu_exit=%s\n' "$fu"
printf 'datapath_exit=%s\nfu_exit=%s\n' "$dp" "$fu" > "$run/rtl-exits.txt"
test "$dp" -eq 0 && test "$fu" -eq 0
