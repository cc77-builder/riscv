#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
action=${1:-help}
shift || true
case "$action" in
  check)
    python3 -B submission/verify.py
    bash team/scripts/check-vdot-model.sh
    python3 -B team/scripts/check-vdot-integration-source.py
    ;;
  logs-check)
    python3 -B submission/logs/read_log.py verify
    ;;
  environment)
    source team/scripts/activate.sh
    bash team/scripts/check-environment.sh
    ;;
  o2-fu|o2-parent)
    bash team/scripts/check-vdot-o2.sh "${action#o2-}"
    ;;
  build-emu)
    source team/scripts/activate.sh
    python3 -B team/optimizations/o2/fullcore/build_fullcore.py "$@"
    ;;
  c8|firstdot)
    out=${1:?Provide a fresh absolute output directory outside the repository}
    python3 - "$root" "$out" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve(); raw=Path(sys.argv[2]); out=raw.resolve()
if not raw.is_absolute() or out.exists() or out.is_relative_to(root) or root.is_relative_to(out):
    raise SystemExit('Use a fresh absolute output directory outside the repository')
PY
    if [[ "$action" == c8 ]]; then
      c8="$root/team/optimizations/o2/integration/firstdot-v2-0f/package/c8"
      src="$root/team/optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-c8-v2/public"
      make -f "$c8/public/Makefile" SOURCE_DIR="$src" OUT="$out" CROSS_COMPILE="${CROSS_COMPILE:-/usr/bin/riscv64-linux-gnu-}" -j1
    else
      make -f "$root/team/optimizations/o2/r2-select/public/firstdot/Makefile" OUT="$out" CROSS_COMPILE="${CROSS_COMPILE:-/usr/bin/riscv64-linux-gnu-}" -j1
    fi
    ;;
  help)
    printf '%s\n' 'Usage: bash submission/reproduce.sh check|logs-check|environment|o2-fu|o2-parent' \
      '       bash submission/reproduce.sh c8|firstdot /absolute/new/output' \
      '       bash submission/reproduce.sh build-emu --output /absolute/new/build-record [--firtool-dir PATH] [--profile observe|cost]'
    ;;
  *) echo "Unknown action: $action" >&2; exit 2 ;;
esac
