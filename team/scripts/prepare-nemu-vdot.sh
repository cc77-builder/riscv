#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
mode=${1:-standalone}
case "$mode" in standalone|reference) ;; *) echo 'Usage: prepare-nemu-vdot.sh {standalone|reference}' >&2; exit 2;; esac
source "$root/team/versions.env"
cache=${TEAM_NEMU_VDOT_ROOT:-"$HOME/riscv-lab/vdot-nemu"}
base=${TEAM_NEMU_BASE_ROOT:-"$cache/base"}
target="$cache/$mode"
patch="$root/team/patches/nemu/vdot-s8x8-r32-v0.1.patch"
manifest="$root/team/patches/nemu/manifest.json"
evidence=${TEAM_EVIDENCE_DIR:-"$root/team/out/t08-$mode-build"}
mkdir -p "$evidence" "$cache"
python3 - "$patch" "$manifest" "$NEMU_REV" <<'PY'
import hashlib,json,sys
from pathlib import Path
patch,manifest,revision=sys.argv[1:]
m=json.loads(Path(manifest).read_text())
assert m['base_rev']==revision
assert m['contract_id']=='vdot-s8x8-r32-v0.1'
assert hashlib.sha256(Path(patch).read_bytes()).hexdigest()==m['patch_sha256']
PY
if ! test -e "$base/.git"; then
  if test -d "$base" && test -n "$(ls -A "$base")"; then echo "Nonempty base directory: $base" >&2; exit 2; fi
  git init "$base"
  git -C "$base" fetch --depth 1 https://github.com/OpenXiangShan/NEMU.git "$NEMU_REV"
  git -C "$base" checkout --detach "$NEMU_REV"
fi
test "$(git -C "$base" rev-parse HEAD)" = "$NEMU_REV"
# Clone committed objects only; never copy another checkout's uncommitted source.
if ! test -e "$target/.git"; then
  if test -d "$target" && test -n "$(ls -A "$target")"; then echo "Nonempty target directory: $target" >&2; exit 2; fi
  git clone --no-hardlinks --no-checkout "$base" "$target"
  git -C "$target" checkout --detach "$NEMU_REV"
fi
test "$(git -C "$target" rev-parse HEAD)" = "$NEMU_REV"
if git -C "$target" apply --check "$patch" 2>/dev/null; then
  if ! git -C "$target" diff --quiet HEAD --; then echo 'Inspect existing source edits before applying vdot' >&2; exit 2; fi
  git -C "$target" apply "$patch"
fi
# Exact source verification makes a repeated invocation safe and rejects partial/drifted patches.
python3 - "$target" "$manifest" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
target=Path(sys.argv[1]);m=json.loads(Path(sys.argv[2]).read_text())
for name,digest in m['patched_source_sha256'].items():
    assert hashlib.sha256((target/name).read_bytes()).hexdigest()==digest,name
changed=subprocess.check_output(['git','-C',str(target),'diff','HEAD','--name-only']).decode().splitlines()
assert set(changed)<=set(m['patched_source_sha256']),changed
PY
bash "$root/team/scripts/lock-nemu-extra-deps.sh" "$base" > "$evidence/dependencies.txt" 2>&1
for rel in nanopb LibCheckpoint gcpt_restore softfloat/repo; do
  if ! test -e "$target/resource/$rel/.git"; then
    if test -d "$target/resource/$rel" && test -n "$(ls -A "$target/resource/$rel")"; then
      echo "Inspect nonempty dependency directory: $target/resource/$rel" >&2; exit 2
    fi
    mkdir -p "$target/resource/$rel"
    cp -a "$base/resource/$rel/." "$target/resource/$rel/"
  fi
done
bash "$root/team/scripts/lock-nemu-extra-deps.sh" "$target" >> "$evidence/dependencies.txt" 2>&1
export NEMU_HOME="$target"
if test "$mode" = standalone; then config=riscv64-xs_defconfig; else config=riscv64-xs-ref_defconfig; fi
cd "$target"
make "$config" > "$evidence/configure.txt" 2>&1
python3 - <<'PY'
from pathlib import Path
p=Path('.config');s=p.read_text();old='# CONFIG_CUSTOM_VDOT is not set'
assert s.count(old)==1
p.write_text(s.replace(old,'CONFIG_CUSTOM_VDOT=y'))
PY
tools/kconfig/build/conf --syncconfig Kconfig >> "$evidence/configure.txt" 2>&1
grep -qx 'CONFIG_CUSTOM_VDOT=y' .config
grep -qx 'CONFIG_RVV=y' .config
# An empty value also overrides an inherited flag that would enable auto-commit.
make -j"${BUILD_JOBS:-2}" __NOT_DEFINED= CPT_CROSS_COMPILE=riscv64-linux-gnu- > "$evidence/build.txt" 2>&1
if test "$mode" = standalone; then binary=build/riscv64-nemu-interpreter; else binary=build/riscv64-nemu-interpreter-so; fi
test -s "$binary"
cp .config "$evidence/nemu.config"
sha256sum "$binary" > "$evidence/binary.sha256"
git rev-parse HEAD > "$evidence/base.sha"
git status --short > "$evidence/working-tree.txt"
cp "$manifest" "$evidence/patch-manifest.json"
python3 - "$mode" "$manifest" "$binary" <<'PY'
import hashlib,json,sys
from pathlib import Path
mode,manifest,binary=sys.argv[1:]
result=json.loads(Path(manifest).read_text())
result.update(build_mode=mode,config_sha256=hashlib.sha256(Path('.config').read_bytes()).hexdigest(),
              binary_sha256=hashlib.sha256(Path(binary).read_bytes()).hexdigest())
Path('build/vdot-provenance.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
PY
cp build/vdot-provenance.json "$evidence/provenance.json"
if test "$mode" = reference; then
  nm -D "$binary" > "$evidence/exported-symbols.txt"
  ldd -r "$binary" > "$evidence/link-check.txt" 2>&1
  if grep -q 'undefined symbol' "$evidence/link-check.txt"; then exit 1; fi
fi
echo "NEMU_VDOT_BUILD_PASS mode=$mode binary=$target/$binary evidence=$evidence"
