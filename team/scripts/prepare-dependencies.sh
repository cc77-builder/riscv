#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
source "$TEAM_PROJECT_ROOT/team/versions.env"
if test -e "$TEAM_XS_ENV_ROOT/.git"; then
  test "$(git -C "$TEAM_XS_ENV_ROOT" rev-parse HEAD)" = "$XSENV_REV"
  git -C "$TEAM_XS_ENV_ROOT" diff --quiet --ignore-submodules=all
  git -C "$TEAM_XS_ENV_ROOT" diff --cached --quiet --ignore-submodules=all
else
  if test -d "$TEAM_XS_ENV_ROOT" && test -n "$(ls -A "$TEAM_XS_ENV_ROOT")"; then
    echo "Dependency directory is not an empty Git checkout: $TEAM_XS_ENV_ROOT" >&2
    exit 1
  fi
  git init "$TEAM_XS_ENV_ROOT"
  git -C "$TEAM_XS_ENV_ROOT" remote add origin https://github.com/OpenXiangShan/xs-env.git
  git -C "$TEAM_XS_ENV_ROOT" fetch --depth 1 origin "$XSENV_REV"
  git -C "$TEAM_XS_ENV_ROOT" checkout --detach "$XSENV_REV"
fi
check_existing() {
  local target="$TEAM_XS_ENV_ROOT/$1" revision=$2
  if test -e "$target/.git"; then
    test "$(git -C "$target" rev-parse HEAD)" = "$revision"
    test -z "$(git -C "$target" status --porcelain --untracked-files=no)"
  fi
}
check_existing NEMU "$NEMU_REV"
check_existing nexus-am "$AM_REV"
check_existing DRAMsim3 "$DRAMSIM3_REV"
git -C "$TEAM_XS_ENV_ROOT" submodule update --init --recursive --jobs 1 -- NEMU nexus-am DRAMsim3
# Team XiangShan source remains in NOOP_HOME; do not initialize xs-env/XiangShan here.
bash "$TEAM_PROJECT_ROOT/team/scripts/lock-nemu-extra-deps.sh"
echo COMPANION_DEPENDENCIES_READY
