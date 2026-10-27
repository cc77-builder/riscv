"""Collect completed S3 evidence and independently audit a separate source checkout.

This driver starts no EMU, does not stage Git, and never edits frozen inputs.
The dependency guard is the existing Python audit-hook probe, not an OS sandbox.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


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


def now():
    return datetime.now(timezone.utc).isoformat()


parser = argparse.ArgumentParser(description=__doc__)
for name in ("root", "detached", "execution"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args()
root, detached, execution = [getattr(args, n).resolve() for n in ("root", "detached", "execution")]
require(root.name == "r2s3-runtime-20261024-1818" and
        detached.name == "r2s3-runtime-detached-20261024-1818" and
        root.parent == detached.parent and not detached.exists(), "selected independent work roots required")
repo = root / "source"
module_rel = Path("team/optimizations/o2/r2-config-reuse")
module = repo / module_rel
base = "43e562d5e174763d9469b6c1c2124df0d60dc576"
require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == base,
        "source base changed")
require(read(root / "post-c-summary-01.json")["status"] == "S3_C_PUBLIC_LIBRARY_AND_USAGE_QUALIFIED",
        "completed actual C/library/usage qualification required")
for name, expected in (("run-probe-01", 5), ("run-extend-01", 28), ("c-run-01", 3)):
    state = read(root / name / "state.json")
    require(state.get("finished") and state["active_pid"] is None and state["active_result"] is None and
            state["new_emu_runs"] == expected, "unfinished campaign: " + name)
evidence = module / "evidence/runtime-v1"
require(not evidence.exists(), "new publication evidence directory required")
evidence.mkdir()
copied = []


def copy_file(source, target):
    require(source.is_file() and not source.is_symlink() and not target.exists(), "fresh regular copy required")
    before = sha(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(source.read_bytes())
    require(sha(source) == sha(target) == before, "evidence transfer changed bytes")
    copied.append(dict(source=str(source), relative=target.relative_to(repo).as_posix(),
                       sha256=before, bytes=source.stat().st_size))


def tree(source, target):
    require(source.is_dir() and not source.is_symlink() and not target.exists(), "fresh regular tree required")
    target.mkdir(parents=True)
    for path in sorted(source.rglob("*")):
        require(not path.is_symlink(), "linked evidence is not allowed")
        if path.is_file():
            require("__pycache__" not in path.parts, "incidental cache in final payload")
            copy_file(path, target / path.relative_to(source))


for source, target in (("probe-archive-01", "probe-archive"), ("matrix-archive-01", "matrix-archive"),
                       ("c-archive-01", "c-archive"), ("library-01", "library"),
                       ("usage-check-01", "usage-check")):
    tree(root / source, evidence / target)
reports = {"runtime-gate-tests-01.json", "probe-audit-01.json", "probe-evidence-tests-01.json",
           "matrix-audit-01.json", "c-host-01.json", "c-library-host-01.json", "c-audit-01.json",
           "post-matrix-summary-01.json", "post-c-summary-01.json"}
for path in sorted(root.iterdir()):
    if not path.is_file():
        continue
    require(path.suffix != ".bundle", "source bundle must not become evidence payload")
    folder = "reports" if path.name in reports else "runtime"
    if path.name.startswith("build-probe-01."):
        folder = "prior-attempts"
    copy_file(path, evidence / folder / path.name)
require(all((evidence / "reports" / n).is_file() for n in reports), "missing required result")
for name in ("post-matrix-01.py", "post-matrix-02.py", "post-c-01.py", "publication-check-01.ps1"):
    copy_file(execution / name, evidence / "runtime" / name)
copy_file(Path(__file__).resolve(), evidence / "runtime/snapshot-detached-01.py")
copy_file(execution / "pending-01/manifest.json", evidence / "prior-attempts/pending-01-manifest.json")
copy_file(execution / "pending-01/usage_check.py", evidence / "prior-attempts/usage-check-before-header-pin.py")
copy_file(execution / "pending-02/manifest.json", evidence / "runtime/pending-02-manifest.json")
snapshot = dict(status="S3_NATIVE_PUBLICATION_SNAPSHOT", created=now(), source_base=base,
    files=copied.copy(), files_count=len(copied), bytes=sum(row["bytes"] for row in copied),
    snapshot_receipt_excluded_from_own_inventory=True)
save(root / "native-publication-snapshot-01.json", snapshot)
copy_file(root / "native-publication-snapshot-01.json", evidence / "runtime/native-publication-snapshot-01.json")
detached.mkdir()


def command(label, argv, cwd):
    stdout, stderr, receipt = [detached / (label + suffix)
                               for suffix in (".stdout.log", ".stderr.log", "-driver.json")]
    started = now()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        process = subprocess.run(list(map(str, argv)), cwd=cwd, stdout=out, stderr=err)
    record = dict(command=list(map(str, argv)), cwd=str(cwd), started=started, finished=now(),
                  exit_code=process.returncode, stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))
    save(receipt, record)
    print(json.dumps(dict(label=label, **record, stdout_tail=stdout.read_text()[-2500:],
                         stderr_tail=stderr.read_text()[-2500:])), flush=True)
    require(process.returncode == 0, "detached stage failed; all prior outputs retained: " + label)
    return stdout


target = detached / "source"
command("clone-01", ["git", "clone", "--no-hardlinks", "--no-checkout", repo, target], detached)
command("checkout-01", ["git", "checkout", "--detach", base], target)
require(not (target / ".git/objects/info/alternates").exists(), "detached checkout uses alternates")
new_names = (".gitattributes", "runtime_candidate.py", "runtime_gate.py", "runtime_experiment.py", "runtime_evidence.py",
             "test_runtime.py", "test_runtime_evidence.py", "RUNTIME_CONTRACT.md", "c_api.py",
             "c_evidence.py", "library.py", "test_c_api.py", "C_CONTRACT.md", "RUNTIME_README.md", "usage_check.py")
delta = []
for name in new_names:
    source, destination = module / name, target / module_rel / name
    require(not destination.exists(), "source delta overlaps base")
    shutil.copyfile(source, destination)
    require(sha(source) == sha(destination), "source delta bytes differ")
    delta.append(dict(path=source.relative_to(repo).as_posix(), sha256=sha(source)))
for rel in (module_rel / "public", module_rel / "evidence/runtime-v1"):
    source, destination = repo / rel, target / rel
    require(not destination.exists(), "new detached evidence required")
    shutil.copytree(source, destination)
    for path in sorted(source.rglob("*")):
        if path.is_file():
            require(sha(path) == sha(destination / path.relative_to(source)), "detached transfer changed bytes")
            delta.append(dict(path=path.relative_to(repo).as_posix(), sha256=sha(path)))
save(detached / "source-snapshot.json", dict(status="S3_SEPARATE_SOURCE_AND_EXPLICIT_DELTA_MATCH",
    created=now(), base=base, source=str(repo), target=str(target), files=delta,
    hardlinks_or_alternates=False, scope="source-only base checkout plus explicit uncommitted candidate delta"))
out = detached / "reports"
out.mkdir()
guard = target / "team/optimizations/o2/repro/evidence/clean-reproduction-v1/analysis/detached-audit.py"
require(sha(guard) == "57f31bb70dafa3154dc22e09c635dde1f4c140405717d98053d781dc2ca43cd4", "guard identity changed")
tm = target / module_rel
te = tm / "evidence/runtime-v1"
identity = target / "team/optimizations/o2/repro/evidence/clean-reproduction-v1/reports/identity-02.json"
require(sha(identity) == "4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb", "portable identity changed")
denied = (root, Path("/home/lizufan/riscv-lab/t17-clean-20261024-0854"),
          Path("/home/lizufan/riscv-lab/r2s1-firstdot-20261024-1458"),
          Path("/home/riscv/riscv-lab/t12-regression-20261013"))
deny_args = [value for path in denied for value in ("--deny-root", path)]
command("c-detached-audit", ["taskset", "-c", "0-3", sys.executable, "-B", guard,
    "--checkout", target, "--script", tm / "c_evidence.py", "--report", out / "c-detached-guard.json",
    *deny_args, "--", "--repo", target, "--identity", identity, "--matrix", te / "matrix-archive",
    "--action", "audit", "--archive", te / "c-archive", "--output", out / "c-detached-audit.json"], target)
require(read(out / "c-detached-audit.json") == read(root / "c-audit-01.json"), "detached raw proof differs")
byte_output = command("library-detached-bytes", ["taskset", "-c", "0-3", sys.executable, "-B",
    tm / "library.py", "--repo", target, "--action", "bytes", "--output", te / "library"], target)
require(json.loads(byte_output.read_bytes()) == read(root / "library-01/library-check.json"),
        "detached library proof differs")
summary = dict(status="S3_DETACHED_C_MATRIX_AND_LIBRARY_PASS", created=now(),
    c_proof_sha256=sha(out / "c-detached-audit.json"), original_c_proof_sha256=sha(root / "c-audit-01.json"),
    proofs_identical=True, guard=read(out / "c-detached-guard.json"),
    library=read(root / "library-01/library-check.json"), new_emu_runs=0, new_nemu_runs=0,
    independent_human_ack=False, new_machine_installation=False,
    scope="same-host independent source checkout and explicit evidence delta; Python dependency probe, not OS sandbox")
save(detached / "detached-summary.json", summary)
for path in sorted(out.iterdir()):
    copy_file(path, evidence / "reports" / path.name)
for path in sorted(detached.iterdir()):
    if path.is_file():
        copy_file(path, evidence / "runtime" / ("detached-" + path.name))
print(json.dumps(dict(status="S3_PUBLICATION_SNAPSHOT_AND_DETACHED_AUDIT_PASS",
    snapshot_files=snapshot["files_count"], snapshot_bytes=snapshot["bytes"], detached=summary), indent=2), flush=True)
