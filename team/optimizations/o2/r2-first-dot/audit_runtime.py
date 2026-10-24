"""Recompute the completed five-run first-dot screen from authenticated raw logs."""
import argparse
from pathlib import Path

import runtime as r


def bind_runtime(files):
    source = Path(r.__file__).resolve()
    r.g.require(source == r.ROOT / "team/optimizations/o2/r2-first-dot/runtime.py" and
                Path(r.a.__file__).resolve() == source.with_name("admit.py") and
                files.get(str(source)) == r.g.sha(source), "audited runtime is not the recorded execution source")


def validate_output(output, run):
    config = r.a.read(run / "configuration.json")
    roots = [run.resolve(), r.ROOT, Path(config["admission"]), Path(config["hardware_root"]),
             Path(config["hardware_pins"]).parent, Path(config["input_contract"]).parent]
    if config.get("negative_parent"):
        roots.append(Path(config["negative_parent"]))
    r.g.require(not output.exists() and not output.is_symlink() and
                all(not output.resolve().is_relative_to(p.resolve()) for p in roots),
                "new external audit output required")


def audit(run):
    run = Path(run).resolve()
    state, config, files = (r.a.read(run / name) for name in ("state.json", "configuration.json", "inputs.json"))
    r.g.require(state["contract"] == r.CONTRACT and state["status"] ==
                "FIRSTDOT_8X32_NEGATIVE_RECOVERY_PAIRED_SCREEN_PASS" and
                state["new_emu_runs"] + state["reused_emu_runs"] == 5 and
                state["active_pid"] is None and state["whole_matrix_qualified"] is False and
                state["defaults_changed"] is False and state["performance_measured"] is True,
                "five-run screen not completed")
    r.verify_files(files)
    bind_runtime(files)
    r.g.require(files[str(run / "configuration.json")] == r.g.sha(run / "configuration.json"), "configuration not bound")
    admission = Path(config["admission"])
    r.g.require(r.g.sha(admission / "state.json") == r.ADMISSION_SHA and
                r.g.sha(config["hardware_pins"]) == r.identity.PINS and
                r.g.sha(config["input_contract"]) == r.identity.INPUTS and
                r.g.sha(config["emu"]) == r.identity.EMU, "frozen source/hardware/input identity")
    r.a.verify_sources()
    r.a.verify_pair(admission / "inputs")
    records = []
    for index, (variant, replay, negative) in enumerate([
            ("firstdot", 0, True), ("firstdot", 0, False), ("s1", 0, False),
            ("firstdot", 1, False), ("s1", 1, False)]):
        label = str(index) + "-" + variant + ("-negative" if negative else "-normal")
        directory = run / "runs" / label
        if negative and config.get("negative_parent"):
            record, protected = r.import_negative(config["negative_parent"], config)
            r.g.require(state["new_emu_runs"] == 4 and state["reused_emu_runs"] == 1 and
                        all(files.get(k) == v for k,v in protected.items()), "parent not protected")
            imported = r.a.read(run / "negative-import.json")
            r.g.require(imported["rechecked"] == record and imported["parent_sha256"] == r.PARENT,
                        "imported negative receipt differs")
            records.append(record)
            continue
        record = r.a.read(directory / "result.json")
        r.validate_record(record, directory, config, variant, negative, index)
        r.g.require(record["replay"] == replay, "replay selection differs")
        if records:
            r.g.require(records[-1]["finished"] <= record["started"] and
                        all(record["pid"] != p["pid"] for p in records), "overlapping or reused process identity")
        build = admission / "inputs" / ("s03-" + variant)
        stdout, stderr = ((directory / name).read_text() for name in ("stdout.log", "stderr.log"))
        r.suite.validate_runtime(stdout + stderr, record["reference"])
        if negative:
            target = r.a.verify_image(build, variant)["first_custom_target"]
            r.g.require(target == config["target"], "negative target not bound to actual ELF")
            fresh = r.negative_check(stdout, stderr, record["exit_code"], target)
        else:
            fresh = r.normal_check(build, directory, variant)
        r.g.require(all(record.get(k) == value for k, value in fresh.items()), "cached result differs from raw recomputation")
        records.append(record)
    r.g.require(records[0]["image_sha256"] == records[1]["image_sha256"], "normal recovery image differs")
    summary = r.summarize(records[1:])
    cached = r.a.read(run / "result.json")
    r.g.require(cached["negative"] == records[0] and cached["normal"] == records[1:] and
                all(cached[k] == value for k, value in summary.items()), "cached campaign summary differs")
    r.verify_files(files)
    return dict(status="FIRSTDOT_FIVE_RUN_RAW_RECHECK_PASS", contract=r.CONTRACT,
                runtime_source_sha256=r.g.sha(r.__file__), auditor_sha256=r.g.sha(__file__),
                result_sha256=r.g.sha(run / "result.json"), new_emu_runs=0, **summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    validate_output(args.output, args.run)
    result = audit(args.run)
    with args.output.open("x") as stream:
        r.json.dump(result, stream, indent=2)
        stream.write("\n")
    print(result["status"])
