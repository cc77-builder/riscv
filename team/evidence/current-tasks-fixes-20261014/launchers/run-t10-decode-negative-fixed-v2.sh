#!/usr/bin/env bash
set -euo pipefail
unset PYTHONOPTIMIZE
python3 /mnt/c/Code/RVInno/riscv/team/tests/check_vdot_decode_failure_gate.py --repo /home/amesotten/.cache/codex-rvinno/t10/source-b657e0896a10d6c9 --evidence /mnt/c/Code/RVInno/riscv/team/out/t10-decode-negative-fixed-20261014-v2
