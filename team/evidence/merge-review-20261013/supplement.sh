#!/usr/bin/env bash
set -euo pipefail
run=/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/validation-20261013
source "$run/env.sh"
cd /home/lizufan/xiangshan-validation-20261013/repo
out=/home/lizufan/xiangshan-validation-20261013/runs/vlen-exit-$(date +%Y%m%d-%H%M%S)-$$
mkdir -p "$out"
exec > >(tee "$run/supplement.log") 2>&1
date -Is
for script in team/scripts/check-vdot-{model,datapath,fu}.sh; do
  bash -n "$script"
  echo "SYNTAX_PASS exit=0 script=$script"
done
set +e
mill -i -j 2 vdotFu.runMain team.vdot.GenerateVDotFu "$out/rtl" --invalid-vlen > "$out/invalid-vlen.log" 2>&1
rc=$?
set -e
printf 'command=mill -i -j 2 vdotFu.runMain team.vdot.GenerateVDotFu %s/rtl --invalid-vlen\nexit_code=%s\nend=%s\n' "$out" "$rc" "$(date -Is)" > "$out/check.status"
cat "$out/check.status"
test "$rc" -eq 1
rg 'VDot requires VLEN=128' "$out/invalid-vlen.log"
cp "$out/invalid-vlen.log" "$run/invalid-vlen-explicit.log"
cp "$out/check.status" "$run/invalid-vlen-explicit.status"
git diff --exit-code
git submodule status --recursive > "$run/submodules-after.txt"
cmp "$run/submodules.txt" "$run/submodules-after.txt"
git status --porcelain=v1 > "$run/checkout-after.txt"
test ! -s "$run/checkout-after.txt"
echo 'SUPPLEMENT_PASS clean_checkout=true submodules_unchanged=true'
