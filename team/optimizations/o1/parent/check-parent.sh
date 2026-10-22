#!/usr/bin/env bash
# Real VFEX4 parent, including actual DIV units and actual ClockGate blackbox.
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd -P)
if [[ $# != 1 || "$1" != /* || -e "$1" ]]; then
  echo 'Usage: check-parent.sh /absolute/new/output-directory' >&2
  exit 2
fi
out=$(realpath -m "$1")
case "$out/" in "$root/"*) echo 'Output must be outside the source checkout' >&2; exit 2;; esac
mkdir -p "$out"
exec > >(tee "$out/runner.log") 2>&1
trap 'rc=$?; printf "exit_code=%s\nfinished_utc=%s\n" "$rc" "$(date -u +%FT%TZ)" > "$out/runner.status"' EXIT
cd "$root"
# Activation must precede every command lookup (in particular Java).
source team/scripts/activate.sh
for tool in python3 java mill verilator clang++ make git sha256sum; do
  command -v "$tool" || { echo "O1_PARENT_NOT_RUN_MISSING_TOOL=$tool"; exit 2; }
done
export CHISEL_FIRTOOL_PATH=${CHISEL_FIRTOOL_PATH:-"$HOME/.cache/llvm-firtool/1.62.1/bin"}
test -x "$CHISEL_FIRTOOL_PATH/firtool"
export JAVA_OPTS=${JAVA_OPTS:-"-Xmx12G -Xss16m"}
BUILD_JOBS=${BUILD_JOBS:-2}
[[ "$BUILD_JOBS" =~ ^[12]$ ]] || { echo 'BUILD_JOBS must be 1 or 2' >&2; exit 2; }
export BUILD_JOBS VDOT_T12_TRACE=0 VDOT_T13_TRACE=0 VDOT_T14_FUSED_INPUT=1
printf 'started_utc=%s\nsource_root=%s\noutput=%s\nJAVA_OPTS=%s\nBUILD_JOBS=%s\nVDOT_T12_TRACE=0\nVDOT_T13_TRACE=0\nVDOT_T14_FUSED_INPUT=1\n' \
  "$(date -u +%FT%TZ)" "$root" "$out" "$JAVA_OPTS" "$BUILD_JOBS" > "$out/run.env"
printf '%q ' bash "$root/team/optimizations/o1/parent/check-parent.sh" "$out" > "$out/invocation.txt"
printf '\n' >> "$out/invocation.txt"
printf 'index\tstarted_utc\tfinished_utc\texit_code\tlog\tcommand\n' > "$out/commands.tsv"
command_index=0
run() {
  local log=$1 start finish rc command_text
  shift
  command_index=$((command_index + 1))
  printf -v command_text '%q ' "$@"
  start=$(date -u +%FT%TZ)
  printf 'COMMAND %s %s\n' "$command_index" "$command_text"
  if "$@" > "$out/$log" 2>&1; then rc=0; else rc=$?; fi
  finish=$(date -u +%FT%TZ)
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$command_index" "$start" "$finish" "$rc" "$log" "$command_text" >> "$out/commands.tsv"
  printf 'RESULT %s exit=%s log=%s\n' "$command_index" "$rc" "$log"
  if (( rc != 0 )); then tail -n 12 "$out/$log"; fi
  return "$rc"
}
run git-version.log git --version
run java-version.log java -version
run mill-version.log mill --version
run verilator-version.log verilator --version
run clang-version.log clang++ --version
run make-version.log make --version
run firtool-version.log "$CHISEL_FIRTOOL_PATH/firtool" --version
{
  for tool in python3 java mill verilator clang++ make git; do printf '%s=%s\n' "$tool" "$(command -v "$tool")"; done
  printf 'firtool=%s\n' "$CHISEL_FIRTOOL_PATH/firtool"
  printf 'CXX=%s\nCC=%s\n' "${CXX:-unset (Verilator make default; inspect verilator log)}" "${CC:-unset}"
} > "$out/tool-paths.txt"
run source-commit.log git rev-parse HEAD
run source-status.log git status --short
run working-tree.patch git diff --binary HEAD
# Include new untracked harness sources; git diff alone cannot archive them.
python3 -B - "$out" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

out = Path(sys.argv[1])
root = Path.cwd()
required = ["team/optimizations/o1/parent/GenerateVDotParent.scala",
            "team/optimizations/o1/parent/parent_test.cpp"]
# Generator may live under team/rtl/vdot/parent; the target in build.sc is authoritative.
if not any(root.glob("team/**/GenerateVDotParent.scala")):
    raise SystemExit("missing real GenerateVDotParent.scala")
if not (root / required[1]).is_file():
    raise SystemExit("missing parent_test.cpp")
paths = subprocess.check_output([
    "git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
    "build.sc", "src", "team/scripts/activate.sh", "team/rtl/vdot",
    "team/models/vdot", "team/optimizations/o1/parent",
]).split(b"\0")
files = sorted({p.decode() for p in paths if p and (root / p.decode()).is_file()})
with (out / "source.sha256").open("w", encoding="utf-8", newline="\n") as stream:
    for name in files:
        stream.write(f"{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n")
(out / "source-files.json").write_text(json.dumps(files, indent=2) + "\n", encoding="utf-8")
# HEAD, pin and clean status for every recursively used dependency. A dirty
# dependency would need a separate content archive; fail rather than hide it.
modules = []
def visit(repo, prefix):
    tree = subprocess.check_output(["git", "-C", str(repo), "ls-tree", "-rz", "HEAD"])
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        meta, raw_path = entry.split(b"\t", 1)
        mode, _, pin = meta.decode().split()
        if mode != "160000":
            continue
        name = raw_path.decode()
        sub = repo / name
        full_name = (Path(prefix) / name).as_posix()
        head = subprocess.check_output(["git", "-C", str(sub), "rev-parse", "HEAD"], text=True).strip()
        status = subprocess.check_output(["git", "-C", str(sub), "status", "--porcelain=v1", "--untracked-files=normal"], text=True)
        record = {"path": full_name, "pin": pin, "head": head, "status": status}
        modules.append(record)
        if head != pin or status:
            (out / "dependencies.json").write_text(json.dumps(modules, indent=2) + "\n", encoding="utf-8")
            raise SystemExit(f"dependency is not clean at its pinned revision: {full_name}")
        visit(sub, full_name)
visit(root, "")
(out / "dependencies.json").write_text(json.dumps(modules, indent=2) + "\n", encoding="utf-8")
print(f"O1_PARENT_SOURCE_CAPTURE_PASS files={len(files)} dependencies={len(modules)}")
PY
run vectors.log python3 -B team/rtl/vdot/prepare_vectors.py team/models/vdot/data "$out/vectors.tsv"
run negative-gate-tests.log python3 -B -m unittest discover -s team/optimizations/o1/parent -p test_negative_gate.py -v
for mode in 0 1; do
  export VDOT_O1_HANDOFF="$mode"
  prefix="mode-$mode"
  rtl="$out/$prefix-rtl"
  obj="$out/$prefix-obj"
  run "$prefix-elaboration.log" mill -i -j "$BUILD_JOBS" vdotParent.runMain team.vdot.GenerateVDotParent "$rtl"
  # Resolve the actual FIRRTL inline blackboxes. Never substitute an empty gate
  # model or use a Verilator blackbox option to make elaboration pass.
  python3 -B - "$rtl" "$out/$prefix-resources.txt" "$out/$prefix-sources.txt" "$out/$prefix-generated-files.json" <<'PY'
import hashlib
import json
from pathlib import Path
import shlex
import sys
rtl = Path(sys.argv[1]).resolve()
manifest = rtl / "firrtl_black_box_resource_files.f"
if not manifest.is_file():
    raise SystemExit("missing generated FIRRTL blackbox manifest")
resources = []
for line in manifest.read_text(encoding="utf-8").splitlines():
    for token in shlex.split(line, comments=True):
        p = Path(token)
        p = (p if p.is_absolute() else rtl / p).resolve()
        if not p.is_relative_to(rtl) or not p.is_file() or p.suffix not in (".sv", ".v"):
            raise SystemExit(f"unsupported or external blackbox resource: {token}")
        if p not in resources:
            resources.append(p)
if not any(p.name == "ClockGate.sv" for p in resources):
    raise SystemExit("real ClockGate.sv was not generated")
Path(sys.argv[2]).write_text("".join(str(p) + "\n" for p in resources), encoding="utf-8")
# --split-verilog emits every module separately. Use each original generated
# source exactly once, including the ClockGate referenced by the manifest.
sources = sorted({p.resolve() for pattern in ("*.sv", "*.v") for p in rtl.rglob(pattern)})
if rtl / "VDotParentTestTop.sv" not in sources or not set(resources).issubset(sources):
    raise SystemExit("missing top or blackbox in generated source set")
for p in sources:
    if not p.is_relative_to(rtl) or not p.is_file():
        raise SystemExit(f"external or missing generated HDL source: {p}")
    if b'// ----- 8< ----- FILE "' in p.read_bytes():
        raise SystemExit(f"embedded virtual files remain; use native --split-verilog: {p.name}")
Path(sys.argv[3]).write_text("".join(str(p) + "\n" for p in sources), encoding="utf-8")
# Preserve all original emitted bytes and record their hashes before Verilator.
artifacts = [{"path": p.relative_to(rtl).as_posix(), "bytes": p.stat().st_size,
              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted(set(sources + [manifest]))]
Path(sys.argv[4]).write_text(json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
print("O1_PARENT_BLACKBOX_CAPTURE_PASS " + " ".join(p.name for p in resources))
print(f"O1_PARENT_NATIVE_SPLIT_CAPTURE_PASS sources={len(sources)}")
PY
  mapfile -t rtl_sources < "$out/$prefix-sources.txt"
  run "$prefix-verilator.log" verilator --cc --exe --build --assert --top-module VDotParentTestTop \
    --Mdir "$obj" -j "$BUILD_JOBS" -CFLAGS "-std=c++17 -O2 -DO1_PARENT_HANDOFF=$mode" \
    "${rtl_sources[@]}" "$root/team/optimizations/o1/parent/parent_test.cpp"
  binary="$obj/VVDotParentTestTop"
  run "$prefix-result.log" "$binary" "$out/vectors.tsv"
  # Exactly one positive completion marker must bind the executable's mode.
  python3 -B - "$out/$prefix-result.log" "$mode" <<'PY'
from pathlib import Path
import re
import sys
lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
passes = [line for line in lines if line.startswith("O1_PARENT_PASS")]
if len(passes) != 1 or not re.fullmatch(r"O1_PARENT_PASS mode=" + sys.argv[2] + r"(?: .*)?", passes[0]):
    raise SystemExit("missing, duplicate, or wrong-mode parent completion marker")
if any("O1_PARENT_FAIL" in line or "O1_PARENT_FAULT_ESCAPED" in line or "O1_PARENT_INJECT" in line for line in lines):
    raise SystemExit("unexpected failure or injection marker in positive run")
print(passes[0])
PY
  if [[ "$mode" == 1 ]]; then
    for fault in identity wen high cancel busy route clock; do
      rc=0
      run "$prefix-inject-$fault.log" "$binary" "$out/vectors.tsv" "$fault" || rc=$?
      run "$prefix-check-$fault.log" python3 -B team/optimizations/o1/parent/check_negative.py \
        --fault "$fault" --return-code "$rc" --log "$out/$prefix-inject-$fault.log"
    done
  fi
done
run source-after.log sha256sum -c "$out/source.sha256"
# Check dependency revisions and dirtiness again after both compilations.
python3 -B - "$out" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys
out = Path(sys.argv[1])
root = Path.cwd()
modules = json.loads((out / "dependencies.json").read_text(encoding="utf-8"))
for module in modules:
    repo = root / module["path"]
    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=normal"], text=True)
    if head != module["head"] or status != module["status"]:
        raise SystemExit(f"dependency changed during validation: {module['path']}")
(out / "dependencies-after.status").write_text("O1_PARENT_DEPENDENCIES_UNCHANGED\n", encoding="utf-8")
paths = [out / "vectors.tsv"]
for mode in (0, 1):
    paths += sorted((out / f"mode-{mode}-rtl").rglob("*.sv"))
    paths += sorted((out / f"mode-{mode}-rtl").rglob("*.v"))
    paths.append(out / f"mode-{mode}-obj/VVDotParentTestTop")
artifacts = [{"path": p.relative_to(out).as_posix(), "bytes": p.stat().st_size,
              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
(out / "artifacts.json").write_text(json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
print(f"O1_PARENT_ARTIFACT_CAPTURE_PASS artifacts={len(artifacts)}")
PY
echo 'O1_PARENT_RUNNER_PASS parent_not_fullcore'
