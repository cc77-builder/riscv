#!/usr/bin/env bash
set -euo pipefail
swap=/home/amesotten/.cache/codex-rvinno/t04/core-baseline.swap
evidence=/mnt/c/Code/RVInno/riscv/team/out/t04-current-20261013
if ! test -f "$swap"; then
  fallocate -l 8G "$swap"
  chmod 600 "$swap"
  mkswap "$swap"
fi
swapon "$swap"
trap 'rc=$?; dmesg -T > "$evidence/kernel-final-build.log"; swapoff "$swap"; rm -- "$swap"; exit "$rc"' EXIT
cd /home/amesotten/.cache/codex-rvinno/t04/source-e8bd8d763650fc4f
runuser -u amesotten -- env \
  CORE_SOURCE_PACK=/mnt/c/Code/RVInno/riscv/team/out/t04-source-pack-20261013-v3 \
  CORE_OPT_FAST=-O1 CORE_COMPILE_JOBS=2 CORE_CXX=clang++-19 CORE_CC=clang-19 \
  CORE_MILL=/home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3 \
  NEMU_HOME=/home/amesotten/.cache/codex-rvinno/t08/delivered/reference \
  AM_HOME=/home/amesotten/.cache/codex-t05/nexus-am-086a238 \
  TEAM_EVIDENCE_DIR="$evidence" \
  bash /mnt/c/Code/RVInno/riscv/team/scripts/core-baseline-compile.sh
