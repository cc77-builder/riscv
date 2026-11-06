#!/usr/bin/env python3
"""Run the frozen candidate's actual ISS/API matrix in independent processes."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

spec = importlib.util.spec_from_file_location("dot16_reference_builder",
                                             Path(__file__).with_name("build_reference.py"))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
require, sha, write_json, utc = helper.require, helper.sha, helper.write_json, helper.utc
LEGACY = "8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--variant", choices=("legacy", "feature0", "feature1"), required=True)
    parser.add_argument("--legacy-reference", type=Path)
    parser.add_argument("--cpu", type=int, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, {args.cpu})
    work = args.workspace.resolve()
    identity = helper.verify_controls(work)
    require(sha(Path(__file__)) == identity["sha256"]["run_reference_api.py"], "running API controller drift")
    prepare = json.loads((work / "prepare-01/state.json").read_text())
    require(prepare["status"] == "PREPARE_PASS", "candidate preparation incomplete")
    probe = work / "reference-api"
    require(sha(probe) == prepare["probe_sha256"], "actual API checker changed")
    expected_feature = int(args.variant == "feature1")
    if args.variant == "legacy":
        require(args.legacy_reference is not None, "legacy reference path required")
        library = args.legacy_reference.resolve()
        require(sha(library) == LEGACY, "frozen old reference mismatch")
        library_identity = {"kind": "frozen-dot8", "sha256": LEGACY}
    else:
        build_dir = work / (args.variant + "-01")
        build = json.loads((build_dir / "state.json").read_text())
        require(build["status"] == "BUILD_PASS" and build["feature"] == expected_feature, "wrong build identity")
        require(build["controls_sha256"] == sha(work / "inputs/control.json"), "build controls changed")
        library = Path(build["library"]).resolve()
        require(library.is_relative_to(build_dir) and sha(library) == build["library_sha256"], "library drift")
        require(sha(build_dir / "nemu.config") == build["config_sha256"], "frozen configuration drift")
        library_identity = {"kind": args.variant, "sha256": sha(library),
                            "build_state_sha256": sha(build_dir / "state.json"),
                            "config_sha256": build["config_sha256"]}
    output = work / ("api-" + args.variant + "-01")
    require(not output.exists(), "API output exists; inspect original receipt instead of replaying")
    output.mkdir()
    state = {"status": "RUNNING", "started": utc(), "variant": args.variant,
             "library": str(library), "library_identity": library_identity,
             "probe_sha256": sha(probe), "controls_sha256": sha(work / "inputs/control.json"),
             "cpu_affinity": sorted(os.sched_getaffinity(0)), "commands": [],
             "fullcore_qualified": False, "dot16_platform_tval_qualified": False}

    def flush():
        write_json(output / "state.json", state)

    def run(name, feature, negative=False):
        argv = [str(probe), str(library), str(feature)] + (["negative-oracle"] if negative else [])
        record = {"name": name, "argv": argv, "started": utc(), "process_started": False}
        state["commands"].append(record)
        flush()
        start = time.monotonic()
        with (output / (name + ".stdout.log")).open("wb") as stdout, \
                (output / (name + ".stderr.log")).open("wb") as stderr:
            process = None
            try:
                process = subprocess.Popen(argv, cwd=output, stdout=stdout, stderr=stderr,
                                           start_new_session=True)
                record.update(process_started=True, pid=process.pid)
                flush()
                try:
                    process.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
            finally:
                record["process_group_absent"] = process is None or helper.reap_group(process)
                flush()
            require(record["process_group_absent"], "API process group still present: " + name)
            rc = process.returncode
        record.update(returncode=rc, finished=utc(), seconds=time.monotonic() - start,
                      stdout_sha256=sha(output / (name + ".stdout.log")),
                      stderr_sha256=sha(output / (name + ".stderr.log")))
        flush()
        require(not record.get("timed_out"), "API progress observation expired: " + name)
        objects = []
        for suffix in ("stdout", "stderr"):
            for line in (output / (name + "." + suffix + ".log")).read_text(errors="replace").splitlines():
                if line.startswith("{"):
                    try:
                        objects.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if name == "normal":
            reports = [r for r in objects if r.get("status") == "PASS_NEMU_REFERENCE_API"]
            require(rc == 0 and len(reports) == 1, "actual normal API did not pass")
            report = reports[0]
            require(report["expected_feature"] == expected_feature and report["regcpy_arguments"] == 2,
                    "wrong API report identity")
            expected_counts = ({"addi": 1, "ebreak": 1, "vadd": 1, "dot8_legal": 1168, "illegal": 82}
                               if not expected_feature else
                               {"addi": 1, "ebreak": 1, "vadd": 1, "dot8_legal": 1168,
                                "dot16_legal": 132240, "illegal": 50})
            require(report["counts"] == expected_counts, "incomplete API matrix")
            state["api_report"] = report
        else:
            errors = [r for r in objects if r.get("status") == "DOT16_API_FAIL"]
            wanted_field = "full-vector-result" if negative else ("trap-pc" if expected_feature else "legal-pc")
            require(rc == 2 and len(errors) == 1 and errors[0]["field"] == wanted_field,
                    "negative control failed for an unexpected reason: " + name)
            state.setdefault("negative_controls", {})[name] = errors[0]
        flush()
        print(json.dumps(record), flush=True)

    flush()
    try:
        run("normal", expected_feature)
        run("negative-oracle", expected_feature, negative=True)
        run("wrong-feature-identity", 1 - expected_feature)
        require(sha(library) == library_identity["sha256"] and sha(probe) == state["probe_sha256"],
                "runtime input changed during API run")
        state.update(status="PASS_REFERENCE_API_STAGE", finished=utc())
        flush()
        print(json.dumps({k: v for k, v in state.items() if k != "commands"}), flush=True)
    except BaseException as error:
        state.update(status="REFERENCE_API_INCOMPLETE", error=repr(error), finished=utc())
        flush()
        raise


if __name__ == "__main__":
    main()
