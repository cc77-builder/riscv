#!/usr/bin/env bash
set -euo pipefail
cd /home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9
for name in vdot-core-smoke.sh vdot_core_checks.py vdot-decode-tests.sh; do
  cp "/mnt/c/Code/RVInno/riscv/team/scripts/$name" "team/scripts/$name"
done
export TEAM_EVIDENCE_DIR=/mnt/c/Code/RVInno/riscv/team/out/t10-audit-fixes-20261014-v2
export CORE_SOURCE_PACK=/mnt/c/Code/RVInno/riscv/team/out/t10-source-pack-20261014-v5
export CORE_BUILD_EVIDENCE=/mnt/c/Code/RVInno/riscv/team/out/t10-core-final-20261014
export NEMU_HOME=../nemu-compatible/reference
export AM_HOME=/home/amesotten/.cache/codex-t05/nexus-am-086a238
export PYTHONOPTIMIZE=1
bash -n team/scripts/vdot-core-smoke.sh
bash -n team/scripts/vdot-decode-tests.sh
bash team/scripts/vdot-core-smoke.sh build
bash team/scripts/vdot-core-smoke.sh run
