"""Current-round handoff after the protected 28-process extension ends.

This driver only installs new, disjoint adapters and audits completed evidence.
It cannot resume a campaign or start EMU; C adoption remains a separate decision.
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
for name in ("root", "windows-repo", "pending", "identity"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args()
root, windows, pending, identity = [getattr(args, name).resolve()
    for name in ("root", "windows_repo", "pending", "identity")]
repo = root / "source"
module = Path("team/optimizations/o2/r2-config-reuse")
require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() ==
        "43e562d5e174763d9469b6c1c2124df0d60dc576", "runtime source base changed")
for name, status, processes in (("run-probe-01", "S3_PAIRED_C_ABI_SCREEN_PASS", 5),
                                ("run-extend-01", "S3_PARTIAL_PASS", 28)):
    state = read(root / name / "state.json")
    require(state["status"] == status and state["new_emu_runs"] == processes and state.get("finished") and
            state["active_pid"] is None and state["active_result"] is None, "campaign not finished: " + name)
processes = subprocess.check_output(["ps", "-eo", "pid,comm,args"], text=True).splitlines()[1:]
require(not [p for p in processes if p.split(None, 2)[1] in
        {"emu", "cc1", "cc1plus", "java", "verilator_bin", "yosys", "openroad"}], "other heavy task present")
frozen = {
    "runtime_candidate.py": "7d98abce6aaad40639c935e49b6d5c6f6663d992d8227d62b3d804ae4118f2a6",
    "runtime_gate.py": "5a9be8bf244a35a878964b0716ee32ed9a3faed16fd3da7938ed30f511d5d72c",
    "runtime_experiment.py": "56c25151b591d98a87a16f6cedb8afa65dbadde8ff0cca88b5113e2157e798f3",
    "runtime_evidence.py": "bf22885499d30d9e732981bb3cb22c093b5ab349c669cfe9eb7a90da9f834f54",
}
for name, digest in frozen.items():
    require(sha(repo / module / name) == sha(windows / module / name) == digest, "frozen runtime drift: " + name)
new = {
    "c_api.py": "5d3f969c77ec5e686004a46ed9a5ad68e031b610b400d70f2777f4661e138999",
    "c_evidence.py": "43e8afdab72ed2bae124806cd27b19d57af974407ebeda84fb03d01e913411b6",
    "library.py": "09807ff349f6f956de1f478d3bad4527d118d1bd2408ee127b093cc10aae983d",
    "test_c_api.py": "3fd521655f776c752c5006551c544639ecab14aff85108f4965e0d60630552d7",
    "C_CONTRACT.md": "551791285a2a2a709c0b6007df29688e9de979b362d75342f9764a72f5141102",
    "test_runtime_evidence.py": "8816576f8ab212daea0dbc599b697730fa49562f9b157ba33abdbf0eb17ec0fd",
    "RUNTIME_README.md": "636e981fae30210f49b57e4f65ae31a0918098a84d6d200523538096492a0e94",
    "usage_check.py": "f776afde092364c6e42cca34c5ccc7c1e63052dd814b8877a834643e22207ec2",
}
for name, digest in new.items():
    require(sha(pending / name) == digest and not (repo / module / name).exists() and
            not (windows / module / name).exists(), "fresh exact candidate files required: " + name)
for name, digest in new.items():
    raw = (pending / name).read_bytes()
    for target in (repo / module / name, windows / module / name):
        with target.open("xb") as stream:
            stream.write(raw)
        require(sha(target) == digest, "source transfer failed")
save(root / "source-delta-03.json", dict(created=now(), source=str(pending), native=str(repo),
    windows=str(windows), files={str(module / n): digest for n, digest in new.items()},
    frozen_runtime_unchanged=frozen))
sys.path.insert(0, str(repo / module))
import runtime_experiment as a
a.parent_identity(repo, identity)


def command(label, argv):
    stdout, stderr, receipt = [root / (label + suffix) for suffix in (".stdout.log", ".stderr.log", "-driver.json")]
    require(not any(p.exists() for p in (stdout, stderr, receipt)), "fresh driver logs required")
    started = now()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        completed = subprocess.run(list(map(str, argv)), cwd=repo, stdout=out, stderr=err)
    record = dict(command=list(map(str, argv)), cwd=str(repo), started=started, finished=now(),
        exit_code=completed.returncode, raw_sha256={"stdout.log": sha(stdout), "stderr.log": sha(stderr)})
    save(receipt, record)
    print(json.dumps(dict(label=label, **record, stdout_tail=stdout.read_text()[-3500:],
                          stderr_tail=stderr.read_text()[-3500:])), flush=True)
    require(completed.returncode == 0, "stage failed; prior outputs retained: " + label)


def run(label, script, arguments):
    command(label, [sys.executable, "-B", repo / module / script, "--repo", repo, *arguments])


run("probe-evidence-tests-01", "test_runtime_evidence.py", ["--archive", root / "probe-archive-01",
    "--output", root / "probe-evidence-tests-01.json"])
run("matrix-pack-01", "runtime_evidence.py", ["--action", "pack", "--identity", identity,
    "--run", root / "run-probe-01", "--run", root / "run-extend-01", "--scope", "matrix",
    "--support", root / "runtime-gate-tests-01.json", "--support", root / "probe-evidence-tests-01.json",
    "--support", repo / module / "test_runtime_evidence.py", "--support", root / "source-delta-01.json",
    "--support", root / "source-delta-02.json", "--archive", root / "matrix-archive-01"])
run("matrix-audit-01", "runtime_evidence.py", ["--action", "audit", "--archive", root / "matrix-archive-01",
    "--output", root / "matrix-audit-01.json"])
run("c-host-01", "test_c_api.py", ["--identity", identity, "--output", root / "c-host-01.json"])
proof = read(root / "matrix-audit-01.json")
require(proof["qualification_scope"] == "matrix" and proof["formal_images"] == 24 and
        proof["original_emu_processes"] == 33 and proof["measured_windows"] == 384 and
        proof["all_window_replay_comparisons"] == 192, "incomplete final matrix proof")
summary = dict(status="S3_MATRIX_AUDITED_C_ADAPTER_HOST_READY", created=now(),
    matrix_sha256=sha(root / "matrix-audit-01.json"), matrix_manifest_sha256=sha(root / "matrix-archive-01/archive-manifest.json"),
    rows=proof["rows"], c_host=read(root / "c-host-01.json"), new_emu_runs=0,
    c_runtime_qualified=False, stable_default_changed=False)
save(root / "post-matrix-summary-01.json", summary)
print(json.dumps(summary, indent=2), flush=True)
