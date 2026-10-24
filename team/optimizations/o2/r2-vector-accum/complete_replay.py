"""Complete S1 small-shape end-to-end process replay without editing its campaign."""
from __future__ import annotations
import argparse
from datetime import datetime
import json
import os
from pathlib import Path, PurePosixPath
import tempfile

import evidence as e

g, a = e.g, e.a
REL = a.S1 / "complete_replay.py"
CONTRACT = "r2-s1-small-endtoend-replay-v1"
PASS = "R2_S1_SMALL_ENDTOEND_REPLAY_PASS"


def plan():
    return [a.name(dict(suite="performance", dataset=0, shard=s, variant=v))
            for s in (1, 3) for v in ("s0", "s1")]


def bind(repo):
    repo = repo.resolve()
    g.require(os.name == "posix", "run and architectural replay require Linux/WSL")
    g.require(Path(__file__).resolve() == (repo / REL).resolve(), "supplement entry path")
    return e.modules(repo)


def complete(state):
    g.require(all(type(state.get(k)) is int for k in
                  ("new_emu_runs", "normal_runs", "replay_runs", "matched_windows", "additional_formal_windows")) and
              isinstance(state.get("operation_id"), str) and bool(state["operation_id"].strip()),
              "supplement count/operation schema")
    g.require(state.get("contract") == CONTRACT and state.get("status") == PASS and
              state.get("new_emu_runs") == 4 and state.get("normal_runs") == 4 and
              state.get("replay_runs") == 4 and state.get("matched_windows") == 96 and
              state.get("additional_formal_windows") == 0 and
              state.get("active_pid") is None and state.get("active_result") is None and
              state.get("hardware_changed") is False and state.get("whole_suite_acceptance") is False,
              "supplement incomplete or wrong scope")
    first, last = (datetime.fromisoformat(state[k]) for k in ("started", "finished"))
    g.require(first.utcoffset() is not None and last.utcoffset() is not None and first <= last,
              "supplement timestamps")


def selected_pairs(images, builds, repo):
    reports = []
    for image in images:
        g.verify_build(builds[image["name"]], repo)
    for shard in (1, 3):
        pair = [next(i for i in images if i["shard"] == shard and i["variant"] == v)
                for v in ("s0", "s1")]
        dirs = [builds[i["name"]] for i in pair]
        reports.append(g.paired_layout(*(g.ELF((p / "vdot-perf.elf").read_bytes()) for p in dirs),
                                       *((p / "vdot-perf.bin").read_bytes() for p in dirs)))
    return reports


def run(repo, parent, output, operation_id):
    repo, parent, output = repo.resolve(), parent.resolve(), output.resolve()
    _, m, f = bind(repo)
    parent_state = a.read_json(parent / "state.json")
    e.complete_state(parent_state)
    cfg = a.read_json(parent / "configuration.json")
    common = a.read_json(parent / "runtime-inputs.json")
    for name in ("candidate.py", "gate.py", "experiment.py"):
        source = repo / a.S1 / name
        g.require(common.get(str(source)) == g.sha(source), "run must use the parent source root")
    g.require(not output.exists() and not output.is_relative_to(parent) and
              not output.is_relative_to(Path(cfg["canonical_build"])), "new independent output required")
    output.mkdir(parents=True)
    state = dict(contract=CONTRACT, operation_id=operation_id, status="PREFLIGHT", started=f.now(),
                 new_emu_runs=0, active_pid=None, active_result=None, hardware_changed=False,
                 whole_suite_acceptance=False, additional_formal_windows=0)
    persist = lambda: g.save(output / "state.json", state)
    persist()
    try:
        original = a.read_json(parent / "results.json")
        g.require(original["status"] == a.PASS and original["contract"] == a.CONTRACT,
                  "parent summary not qualified")
        inventory = a.read_json(Path(cfg["canonical_build"]) / "images.json")["images"]
        images = [next(i for i in inventory if i["name"] == name) for name in plan()]
        for image in images:
            g.require(image["suite"] == "performance" and image["dataset"] == 0 and
                      image["shard"] in (1, 3), "supplement selection")
        builds = {i["name"]: Path(i["path"]) for i in images}
        layouts = selected_pairs(images, builds, repo)
        files = dict(common)
        for p in [repo / REL, repo / a.S1 / "evidence.py"] + [parent / n for n in
                  ("state.json", "results.json", "configuration.json", "runtime-inputs.json")]:
            digest = g.sha(p)
            g.require(str(p) not in files or files[str(p)] == digest, "mixed parent identity")
            files[str(p)] = digest
        hardware, profile = a.legacy_m.hardware_profile(repo, cfg)
        profile["software_contract"] = a.CONTRACT
        g.require(profile == a.read_json(parent / "hardware-profile.json") and
                  all(common.get(p) == digest for p, digest in hardware.items()), "parent hardware differs")
        m.verify_files(files)
        g.save(output / "configuration.json", cfg)
        g.save(output / "runtime-inputs.json", files)
        g.save(output / "images.json", images)
        g.save(output / "pair-layout.json", layouts)
        parent_identity = dict(path=str(parent), state_sha256=g.sha(parent / "state.json"),
                               results_sha256=g.sha(parent / "results.json"))
        g.save(output / "parent.json", parent_identity)
        records = []
        for image in images:
            original_run = next(r for r in original["runs"] if
                                r["name"] == image["name"] and r["replay"] == 0)
            g.require(original_run == a.read_json(parent / "runs" / ("formal-" + image["name"]) /
                                                 "result.json"), "parent formal receipt differs")
            run_dir = output / "runs" / ("replay-" + image["name"])
            before = state["new_emu_runs"]
            def progress(record):
                state.update(status="REPLAY", new_emu_runs=before + int(record.get("process_started") is True),
                             active_pid=record.get("pid") if "finished" not in record else None,
                             active_result=str(run_dir / "result.json") if "finished" not in record else None)
                persist()
            record = m.execute(repo, cfg, image, run_dir, files, replay=1, progress=progress)
            g.require(m.signature(record) == m.signature(original_run) and len(record["samples"]) == 24,
                      "small-shape process replay differs")
            records.append(record)
            g.save(output / "completed-runs.json", records)
        final_files, final_profile = a.legacy_m.hardware_profile(repo, cfg)
        final_profile["software_contract"] = a.CONTRACT
        g.require(final_files == hardware and final_profile == profile, "supplement hardware drift")
        m.verify_files(files)
        g.require(selected_pairs(images, builds, repo) == layouts and state["new_emu_runs"] == 4,
                  "supplement final identity/count")
        g.save(output / "results.json", dict(status=PASS, contract=CONTRACT, parent=parent_identity,
                                             runs=records, additional_formal_windows=0))
        state.update(status=PASS, normal_runs=4, replay_runs=4, matched_windows=96)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = f.now()
        persist()
    complete(state)
    return state


def audit(repo, archive_path, supplement):
    reusable, m, _ = bind(repo)
    archive = reusable.portable(repo).Archive(archive_path)
    g.require(archive.manifest["contract"] == a.CONTRACT, "archive contract")
    g.require(len(PurePosixPath(supplement).parts) == 1 and supplement not in (".", "..") and
              "/" not in supplement and "\\" not in supplement, "supplement name")
    prefix = "support/" + supplement
    state, parent_state = archive.json(prefix + "/state.json"), archive.json("campaign/state.json")
    complete(state)
    e.complete_state(parent_state)
    cfg = archive.json("campaign/configuration.json")
    e.original_identity(archive, cfg, archive.json("sealed-inputs.json"), m)
    for logical in archive.records:
        if logical.startswith("tools/team/") and logical.endswith(".py"):
            g.require(g.sha(repo / Path(logical).relative_to("tools")) == e.digest(archive.raw(logical)),
                      "supplement checked-out tool differs: " + logical)
    g.require(archive.json(prefix + "/configuration.json") == cfg, "supplement configuration differs")
    source_root, work_root = map(PurePosixPath, (archive.manifest["source_root"], archive.manifest["work_root"]))
    own_logical = "support/complete_replay.py"
    g.require(archive.records[own_logical]["original"] == str(source_root / REL.as_posix()) and
              e.digest(archive.raw(own_logical)) == g.sha(repo / REL), "supplement executed source differs")
    g.require(e.digest(archive.raw("tools/" + (a.S1 / "evidence.py").as_posix())) ==
              g.sha(repo / a.S1 / "evidence.py"), "supplement evidence source differs")
    common = dict(archive.json("campaign/runtime-inputs.json"))
    common.update({str(source_root / REL.as_posix()): e.digest(archive.raw(own_logical)),
                   str(source_root / (a.S1 / "evidence.py").as_posix()): g.sha(repo / a.S1 / "evidence.py")})
    for name in ("state.json", "results.json", "configuration.json", "runtime-inputs.json"):
        common[str(work_root / name)] = e.digest(archive.raw("campaign/" + name))
    g.require(archive.json(prefix + "/runtime-inputs.json") == common, "supplement common input closure")
    parent_identity = dict(path=str(work_root), state_sha256=common[str(work_root / "state.json")],
                           results_sha256=common[str(work_root / "results.json")])
    g.require(archive.json(prefix + "/parent.json") == parent_identity, "supplement parent identity")
    inventory = archive.json("canonical/images.json")["images"]
    images = [next(i for i in inventory if i["name"] == name) for name in plan()]
    g.require(archive.json(prefix + "/images.json") == images, "supplement image inventory")
    expected_labels = ["replay-" + name for name in plan()]
    found = {p[len(prefix + "/runs/"):].split("/")[0] for p in archive.records
             if p.startswith(prefix + "/runs/") and p.endswith("/result.json")}
    g.require(found == set(expected_labels), "supplement run inventory")
    originals = {v["original"]: k for k, v in archive.records.items()}
    sealed = dict(archive.json("sealed-inputs.json"))
    all_records = [archive.json(prefix + "/runs/" + label + "/result.json") for label in expected_labels]
    for record in all_records:
        for name, digest in record["files"].items():
            if name in originals:
                logical = originals[name]
                g.require(e.digest(archive.raw(logical)) == digest, "supplement archived input differs")
                sealed[name] = dict(sha256=digest, logical=logical)
            else:
                g.require(name in sealed and sealed[name]["sha256"] == digest and
                          sealed[name]["logical"] is None, "supplement unsealed external input")
    original_output = PurePosixPath(archive.records[prefix + "/state.json"]["original"]).parent
    fixture = archive.json("campaign/negative-fixture/fixture.json")
    with tempfile.TemporaryDirectory(prefix="s1-small-replay-audit-") as temporary:
        extracted = Path(temporary)
        selected = ["canonical/images/" + i["name"] + "/" for i in images] + [prefix + "/runs/"]
        for logical in archive.records:
            if any(logical.startswith(p) for p in selected):
                target = extracted / logical
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.raw(logical))
        builds = {i["name"]: extracted / "canonical/images" / i["name"] for i in images}
        g.require(selected_pairs(images, builds, repo) == archive.json(prefix + "/pair-layout.json"),
                  "supplement pair layout differs")
        suite = g.load("s1_small_replay_runtime_banner", repo / "team/optimizations/o2/fullcore/run_suite.py")
        for image, label, record in zip(images, expected_labels, all_records):
            g.require(PurePosixPath(record["cwd"]) == original_output / "runs" / label / "cwd",
                      "supplement run directory identity")
            reusable.run_identity(record, image, 1, False, cfg, fixture, common, sealed)
            run_dir = extracted / prefix / "runs" / label
            g.require(record["raw_sha256"] == {p: g.sha(run_dir / p) for p in ("stdout.log", "stderr.log")},
                      "supplement raw log receipt differs")
            suite.validate_runtime((run_dir / "stdout.log").read_text() + (run_dir / "stderr.log").read_text(),
                                   record["reference"])
            reusable.normal_audit(repo, builds[image["name"]], run_dir,
                                  record, {p: v["sha256"] for p, v in sealed.items()})
            original = archive.json("campaign/runs/formal-" + image["name"] + "/result.json")
            g.require(m.signature(record) == m.signature(original) and len(record["samples"]) == 24,
                      "archived small-shape replay differs")
    ordered = sorted(all_records, key=lambda r: datetime.fromisoformat(r["started"]))
    g.require([r["name"] for r in ordered] == plan(), "supplement execution order")
    previous = datetime.fromisoformat(parent_state["finished"])
    g.require(previous <= datetime.fromisoformat(state["started"]), "supplement started before parent finished")
    previous = datetime.fromisoformat(state["started"])
    for record in ordered:
        g.require(previous <= datetime.fromisoformat(record["started"]), "overlapping supplement runs")
        previous = datetime.fromisoformat(record["finished"])
    g.require(previous <= datetime.fromisoformat(state["finished"]), "supplement finish excludes child")
    cached = archive.json(prefix + "/results.json")
    g.require(cached == dict(status=PASS, contract=CONTRACT, parent=parent_identity,
                            runs=all_records, additional_formal_windows=0), "supplement cached summary differs")
    return dict(status="R2_S1_SMALL_REPLAY_ARCHIVE_RECOMPUTE_PASS", contract=CONTRACT,
                archive=archive.bytes_result, normal_runs=4, matched_windows=96,
                additional_formal_windows=0, new_emu_runs=0, new_nemu_runs=0,
                physical_inputs_revalidated=False, whole_suite_acceptance=False,
                scope="Four additional dataset0 S0/S1 endtoend process replays for 4x8 and 8x32; parent audit remains separate")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--action", choices=("run", "audit"), required=True)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--operation-id")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--supplement", default="replay-small-01")
    args = parser.parse_args()
    if args.action == "run":
        g.require(args.parent is not None and bool(args.operation_id), "run requires parent and operation ID")
        result = run(args.repo, args.parent, args.output, args.operation_id)
    else:
        g.require(args.archive is not None, "audit requires archive")
        e.index_helper(args.repo).check_output_path(args.archive, args.output)
        result = audit(args.repo.resolve(), args.archive, args.supplement)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        g.save(args.output, result)
    print(json.dumps(result, indent=2))
