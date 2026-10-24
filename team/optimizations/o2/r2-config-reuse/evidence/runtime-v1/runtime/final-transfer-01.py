"""Copy the final explicit S3 deliverable to the Windows worktree, preserving bytes.

Documentation is authored in Windows only after actual qualification, then
copied into the native source. This driver never invokes Git on a Windows tree.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--windows-repo", type=Path, required=True)
args = parser.parse_args()
root, windows = args.root.resolve(), args.windows_repo.resolve()
require(root.name == "r2s3-runtime-20261024-1818" and windows.name == "working-r2s3-runtime-20261024-1818",
        "selected worktrees required")
repo = root / "source"
module = Path("team/optimizations/o2/r2-config-reuse")
evidence = module / "evidence/runtime-v1"
base = "43e562d5e174763d9469b6c1c2124df0d60dc576"
require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == base,
        "native source base changed")
require(read(root / "post-c-summary-01.json")["status"] == "S3_C_PUBLIC_LIBRARY_AND_USAGE_QUALIFIED" and
        read(repo / evidence / "runtime/detached-detached-summary.json")["status"] == "S3_DETACHED_C_MATRIX_AND_LIBRARY_PASS",
        "actual qualification and detached audit required")
require(not (windows / evidence).exists() and not (root / "windows-publication-transfer-01.json").exists(),
        "fresh Windows evidence and transfer receipt required")
documents = [module / "README.md", Path("team/docs/development-route-current.md"), Path("开发计分板.md")]
new_result = module / "RUNTIME_RESULT.md"
for rel in documents:
    original = subprocess.check_output(["git", "show", base + ":" + rel.as_posix()], cwd=repo)
    require((repo / rel).read_bytes() == original, "native existing document drift: " + str(rel))
require(not (repo / new_result).exists(), "new native result document required")
for rel in [*documents, new_result]:
    source = windows / rel
    require(source.is_file() and not source.is_symlink() and b"@@" not in source.read_bytes(),
            "complete authored documentation required: " + str(rel))
for rel in documents:
    (repo / rel).write_bytes((windows / rel).read_bytes())
with (repo / new_result).open("xb") as stream:
    stream.write((windows / new_result).read_bytes())
executed = repo / evidence / "runtime/final-transfer-01.py"
require(not executed.exists(), "fresh final transfer script snapshot required")
executed.write_bytes(Path(__file__).read_bytes())
fixed = [module / n for n in (
    ".gitattributes", "runtime_candidate.py", "runtime_gate.py", "runtime_experiment.py", "runtime_evidence.py",
    "test_runtime.py", "test_runtime_evidence.py", "RUNTIME_CONTRACT.md", "c_api.py", "c_evidence.py", "library.py",
    "test_c_api.py", "C_CONTRACT.md", "RUNTIME_README.md", "usage_check.py", "RUNTIME_RESULT.md",
    "public/gemv.S", "public/gemv.h", "public/manifest.json", "README.md")]
fixed += [Path("team/docs/development-route-current.md"), Path("开发计分板.md")]
inventory = set(fixed)
for path in sorted((repo / evidence).rglob("*")):
    require(not path.is_symlink() and "__pycache__" not in path.parts, "unexpected evidence link/cache")
    if path.is_file():
        inventory.add(path.relative_to(repo))
rows = []
for rel in sorted(inventory):
    source, target = repo / rel, windows / rel
    require(source.is_file() and not source.is_symlink() and not target.is_symlink(), "regular transfer files required")
    digest = sha(source)
    if target.exists():
        require(target.is_file() and sha(target) == digest, "existing Windows bytes differ: " + str(rel))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
    require(sha(source) == sha(target) == digest, "transfer changed bytes")
    rows.append(dict(path=rel.as_posix(), sha256=digest, bytes=source.stat().st_size))
report = dict(status="S3_NATIVE_WINDOWS_EXPLICIT_DELIVERABLE_BYTES_PASS", created=datetime.now(timezone.utc).isoformat(),
    native=str(repo), windows=str(windows), native_source_base=base, files=len(rows), bytes=sum(r["bytes"] for r in rows),
    source_sha256=sha(Path(__file__)), all_file_bytes_identical=True, no_linux_git_on_windows=True,
    transfer_receipt_excluded_from_own_inventory=True, later_publication_report_not_yet_created=True, rows=rows)
path = root / "windows-publication-transfer-01.json"
save(path, report)
rel = evidence / "runtime/windows-publication-transfer-01.json"
for destination in (repo / rel, windows / rel):
    with destination.open("xb") as stream:
        stream.write(path.read_bytes())
    require(sha(destination) == sha(path), "transfer receipt copy differs")
print(json.dumps({k:v for k,v in report.items() if k != "rows"}, indent=2))
