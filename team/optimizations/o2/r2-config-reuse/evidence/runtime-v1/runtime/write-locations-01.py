"""Write final physical locations from completed receipts; does not grant qualification."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--tool-receipts", type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve()
require(root.name == "r2s3-runtime-20261024-1818", "selected physical root required")
repo = root / "source"
module = repo / "team/optimizations/o2/r2-config-reuse"
require(read(root / "post-c-summary-01.json")["status"] == "S3_C_PUBLIC_LIBRARY_AND_USAGE_QUALIFIED",
        "actual completed C/library/usage qualification required")
require(read(root / "library-01/library.json")["library_builder_sha256"] == sha(module / "library.py"),
        "qualified library builder changed")
usage = read(root / "usage-check-01/report.json")
require(usage["source_sha256"] == sha(module / "usage_check.py") and
        usage["readme_sha256"] == sha(module / "RUNTIME_README.md"), "documented usage source changed")
states = {name: read(root / name / "state.json") for name in ("run-probe-01", "run-extend-01", "c-run-01")}
require(all(state.get("finished") and state["active_pid"] is None and state["active_result"] is None
            for state in states.values()), "an original campaign remains active")
require(sum(s["new_emu_runs"] for s in states.values()) == 36, "unexpected original process count")
output = root / "locations.json"
tool_copy = root / "selected-tool-receipts.json"
require(not output.exists() and not tool_copy.exists(), "new location and selected receipt outputs required")
with tool_copy.open("xb") as stream:
    stream.write(args.tool_receipts.read_bytes())
require(sha(tool_copy) == sha(args.tool_receipts), "tool receipt transfer failed")
archives = {}
for name in ("probe", "matrix", "c"):
    path = root / (name + "-archive-01")
    archives[name] = dict(physical=str(path), delivered="team/optimizations/o2/r2-config-reuse/evidence/runtime-v1/" + name + "-archive",
                         manifest_sha256=sha(path / "archive-manifest.json"), bytes_receipt=read(path / "archive-check.json"))
new_sources = [".gitattributes", "runtime_candidate.py", "runtime_gate.py", "runtime_experiment.py", "runtime_evidence.py",
               "RUNTIME_CONTRACT.md", "test_runtime.py", "test_runtime_evidence.py", "c_api.py", "c_evidence.py",
               "C_CONTRACT.md", "test_c_api.py", "library.py", "usage_check.py", "RUNTIME_README.md"]
identity_path = root / "run-probe-01/parent-identity.json"
identity = read(identity_path)
report = dict(status="S3_COMPLETED_CAMPAIGN_LOCATIONS", created=datetime.now(timezone.utc).isoformat(),
    operation_id="20261024-LiZufan001-r2s3-runtime-1818", round_started_utc="2026-10-24T10:18:11+00:00",
    source_base=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
    native_source=str(repo), native_work_root=str(root),
    windows_source="D:\\Projects\\competitions\\2026-10-CIE-RISCV-XiangShan\\working-r2s3-runtime-20261024-1818",
    windows_branch="work/r2s3-runtime-20261024-1818",
    windows_execution="D:\\Projects\\competitions\\2026-10-CIE-RISCV-XiangShan\\execution-r2s3-runtime-20261024-1818",
    original_windows_entry=dict(path="D:\\Projects\\competitions\\2026-10-CIE-RISCV-XiangShan\\working-zufan-full-20261022",
        initially_observed_head="ff58e519091f273c4bc177f5e82cfbbfaf102cc5", initial_worktree_clean=True,
        scope="read-only entry observation; this round used an independent worktree"),
    detached_root=str(root.with_name("r2s3-runtime-detached-20261024-1818")),
    publication_target="https://github.com/cc77-builder/riscv.git refs/heads/zufan",
    publication_commit_lookup="containing Git commit and Issue #2; not self-embedded in this pre-commit file",
    sources={name: sha(module / name) for name in new_sources},
    source_deltas={name: sha(root / name) for name in ("source-delta-01.json", "source-delta-02.json",
        "source-delta-03.json", "source-delta-04.json")},
    builds={name: str(root / name) for name in ("build-probe-02", "build-extra-01", "build-middle-01", "c-build-01")},
    campaigns={name: dict(path=str(root / name), state=state) for name, state in states.items()},
    archives=archives, qualified_public=str(root / "qualified-public-01"), library=str(root / "library-01"),
    usage_check=str(root / "usage-check-01"), parent_identity_sha256=sha(identity_path),
    fixed_physical_inputs=identity["configuration"],
    hardware_profile=identity["hardware_profile"], reference_sha256=identity["reference_sha256"],
    control_observation=str(root / "control-context-observation-01.json"),
    runtime_scope="fixed GEMV C ABI windows; 16 public functions with ordinary C correctness; optional library",
    total_new_emu_processes=36, normal_processes=34, expected_negative_processes=2,
    resource_policy="at most four CPU cores; parallel isolated GNU images; serial performance and ordinary C campaigns",
    bound_input_closure_changed_during_live_runs=False, stable_default_changed=False, hardware_changed=False,
    full_application_performance_measured=False, new_asic_ppa=False, human_ack=False, new_machine_installation=False,
    prepared_attempts=[
        dict(name="initial Windows checkout", result="long path failure", resolution="core.longpaths enabled only in the new worktree; successful checkout before experiments", evidence="Issue #2 comment 6383132445"),
        dict(name="build-probe-01", result="cross-shell root argument rejected before construction", resolution="explicit verified paths in build-probe-02", evidence="prior-attempts/build-probe-01.stderr.log"),
        dict(name="pending-01", result="unexecuted C/usage draft", resolution="pending-02 adds direct qualified public-header identity check", evidence="prior-attempts/pending-01-manifest.json"),
    ],
    locations_writer_sha256=sha(Path(__file__)), selected_tool_receipts_sha256=sha(tool_copy))
require(report["source_base"] == "43e562d5e174763d9469b6c1c2124df0d60dc576", "execution source base changed")
with output.open("x", encoding="utf-8") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps(dict(status=report["status"], source_base=report["source_base"],
    campaigns={k: {n:v["state"][n] for n in ("status", "started", "finished", "new_emu_runs")} for k,v in report["campaigns"].items()},
    manifest_sha256={k:v["manifest_sha256"] for k,v in archives.items()}, output=str(output), sha256=sha(output)), indent=2))
