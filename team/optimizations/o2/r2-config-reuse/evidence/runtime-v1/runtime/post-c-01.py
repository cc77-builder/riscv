"""Package a completed S3 C campaign and check the documented consumer.

Never starts EMU. Every output must be new; a failed stage is preserved and
must be inspected before separately invoking any remaining stage.
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


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def now():
    return datetime.now(timezone.utc).isoformat()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--identity", type=Path, required=True)
args = parser.parse_args()
root, identity = args.root.resolve(), args.identity.resolve()
repo = root / "source"
module = repo / "team/optimizations/o2/r2-config-reuse"
state = read(root / "c-run-01/state.json")
qualification = read(root / "c-run-01/config-reuse-qualification.json")
require(state["status"] == "R4_C_APPLICATION_CALLS_PASS" and state["new_emu_runs"] == 3 and
        state["active_pid"] is None and state["active_result"] is None and state.get("finished"),
        "C campaign has not finished successfully")
require(qualification["status"] == "S3_C_APPLICATION_CALLS_PASS" and
        qualification["contract"] == "r2-s3-config-reuse-c-application-v1", "foreign C qualification")
processes = subprocess.check_output(["ps", "-eo", "pid,comm,args"], text=True).splitlines()[1:]
require(not [p for p in processes if p.split(None, 2)[1] in
        {"emu", "cc1", "cc1plus", "java", "verilator_bin", "yosys", "openroad"}], "other heavy task present")
sys.path.insert(0, str(module))
import c_api as c
identity_value = c.a.parent_identity(repo, identity)


def command(label, script, arguments):
    stdout, stderr, receipt = [root / (label + suffix) for suffix in (".stdout.log", ".stderr.log", "-driver.json")]
    require(not any(p.exists() for p in (stdout, stderr, receipt)), "fresh stage logs required")
    argv = [sys.executable, "-B", str(module / script), "--repo", str(repo), *map(str, arguments)]
    started = now()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        result = subprocess.run(argv, cwd=repo, stdout=out, stderr=err)
    record = dict(command=argv, cwd=str(repo), started=started, finished=now(), exit_code=result.returncode,
                  raw_sha256={"stdout.log": sha(stdout), "stderr.log": sha(stderr)})
    save(receipt, record)
    print(json.dumps(dict(label=label, **record, stdout_tail=stdout.read_text()[-2500:],
                         stderr_tail=stderr.read_text()[-2500:])), flush=True)
    require(result.returncode == 0, "stage failed; completed outputs retained: " + label)


base = ["--identity", identity, "--matrix", root / "matrix-archive-01"]
command("c-export-01", "c_api.py", [*base, "--action", "export", "--build", root / "c-build-01",
    "--run", root / "c-run-01", "--output", root / "qualified-public-01"])
public = module / "public"
require(not public.exists(), "published source already exists")
shutil.copytree(root / "qualified-public-01", public)
files = {p.name: sha(p) for p in (root / "qualified-public-01").iterdir()}
require(files == {p.name: sha(p) for p in public.iterdir()}, "public source transfer changed bytes")
save(root / "public-transfer-01.json", dict(created=now(), source=str(root / "qualified-public-01"),
    destination=str(public), files=files, identical=True))
command("c-pack-01", "c_evidence.py", [*base, "--action", "pack", "--build", root / "c-build-01",
    "--run", root / "c-run-01", "--archive", root / "c-archive-01"])
command("library-build-01", "library.py", [*base, "--action", "build", "--build", root / "c-build-01",
    "--run", root / "c-run-01", "--c-archive", root / "c-archive-01", "--output", root / "library-01"])
# library.build performs the full C archive + matrix raw audit. Preserve that
# actual returned proof instead of executing the same audit a second time here.
library_record = read(root / "library-01/library.json")
c_audit = dict(status="S3_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS", contract=c.CONTRACT,
               proof=library_record["c_archive_proof"])
save(root / "c-audit-01.json", c_audit)
command("c-library-host-01", "test_c_api.py", ["--identity", identity,
    "--library", root / "library-01", "--output", root / "c-library-host-01.json"])
command("usage-check-01", "usage_check.py", ["--identity", identity, "--build", root / "c-build-01",
    "--library", root / "library-01", "--output", root / "usage-check-01"])
summary = dict(status="S3_C_PUBLIC_LIBRARY_AND_USAGE_QUALIFIED", created=now(), c_state=state,
    qualification={k: v for k, v in qualification.items() if k != "matrix_anchor"},
    c_archive_audit_execution="library.build -> frozen C archive audit -> current matrix and C raw audit",
    c_audit=c_audit, library=read(root / "library-01/library-check.json"),
    host=read(root / "c-library-host-01.json"),
    negative=read(root / "c-run-01/runs/negative/result.json")["negative_details"],
    artifacts={n: sha(root / n) for n in ("c-audit-01.json", "c-archive-01/archive-manifest.json",
        "library-01/library.json", "library-01/library-check.json", "c-library-host-01.json", "usage-check-01/report.json")},
    new_emu_runs=0, c_original_emu_processes=3, stable_default_changed=False,
    full_application_performance_measured=False, new_asic_ppa=False)
save(root / "post-c-summary-01.json", summary)
print(json.dumps(summary, indent=2), flush=True)
