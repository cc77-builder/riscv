#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/activate.sh"
source "$TEAM_PROJECT_ROOT/team/versions.env"
test "$(git -C "$NEMU_HOME" rev-parse HEAD)" = "$NEMU_REV"
restore() {
  local rel=$1 url=$2 sha=$3 target="$NEMU_HOME/$1"
  if test -e "$target/.git"; then
    test "$(git -C "$target" rev-parse HEAD)" = "$sha" || {
      echo "Existing dependency differs; inspect it without discarding edits: $target" >&2
      return 1
    }
    test -z "$(git -C "$target" status --porcelain --untracked-files=no)"
  else
    if test -d "$target" && test -n "$(ls -A "$target")"; then
      echo "Nonempty dependency directory: $target" >&2
      return 1
    fi
    git init "$target"
    git -C "$target" remote add origin "$url"
    git -C "$target" fetch --depth 1 origin "$sha"
    git -C "$target" checkout --detach "$sha"
  fi
  printf '%s %s\n' "$rel" "$sha"
}
restore resource/nanopb https://github.com/nanopb/nanopb.git 26e4b21317f88a66fb351f5aa3d8cc0083622b25
restore resource/LibCheckpoint https://github.com/OpenXiangShan/LibCheckpoint.git 1d8905cc2803c242ef257569128c2e68bf4272aa
restore resource/LibCheckpoint/resource/nanopb https://github.com/nanopb/nanopb 671672b4d7994a9b07a307ae654885c7202ae886
restore resource/gcpt_restore https://github.com/OpenXiangShan/LibCheckpointAlpha.git 5169da768d18f4682a489eaabe7c071df6d6ef88
restore resource/softfloat/repo https://github.com/ucb-bar/berkeley-softfloat-3 a0c6494cdc11865811dec815d5c0049fba9d82a8
echo NEMU_EXTRA_DEPS_LOCK_PASS
