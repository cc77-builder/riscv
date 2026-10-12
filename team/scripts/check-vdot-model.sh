#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
model_root="$repo_root/team/models/vdot"

python3 -B -m unittest discover -s "$model_root/tests" -v
python3 -B "$model_root/generate.py" --check
printf '%s\n' 'VDOT_MODEL_CHECK_PASS (host model and data only; no RTL/NEMU run)'
