"""Bounded S1/firstdot paired C-ABI experiment on the verified T17 hardware.

Old software gates, hardware pins and results are never rewritten. Build and
run require fresh output directories; a failed/interrupted run is not resumed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import types

import firstdot_gate as g
import firstdot_candidate as c

ROOT = Path(__file__).resolve().parents[4]
REPRO = Path("team/optimizations/o2/repro")
sys.path.insert(0, str(ROOT / REPRO))
import clean_entry as t17

PARENT_IDENTITY_SHA = "4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb"
PROFILE_SHA = "1c4c467f43ede68fd30b1063868d8f02d71fbe8a5442f2da180210468db9a642"
VARIANTS = ("s1", "firstdot")
BUILD_PASS = "FIRSTDOT_STATIC_PASS_RUNTIME_NOT_RUN"
RUN_PASS = "FIRSTDOT_PAIRED_C_ABI_SCREEN_PASS"
SCOPE = "firstdot full128 live DiffTest; complete C-ABI call/return and exact retirement/counters"


def read(path):
    return json.loads(Path(path).read_text())


def name(item):
    return f"{item['suite']}-{item['variant']}-d{item['dataset']}-s{item['shard']:02d}"


def inventory(shards, datasets):
    g.require(shards and len(set(shards)) == len(shards) and set(shards) <= {1, 3, 5, 7}, "firstdot shards")
    g.require(datasets and len(set(datasets)) == len(datasets) and set(datasets) <= {0, 1, 2}, "firstdot datasets")
    return [dict(suite="performance", shard=s, dataset=d, variant=v)
            for s in shards for d in datasets for v in VARIANTS]


def parent_identity(repo, path, physical=False):
    g.bind(repo)
    g.require(g.sha(path) == PARENT_IDENTITY_SHA, "unrecognized T17 parent identity")
    g.require(g.sha(repo / REPRO / "clean_profile.py") == PROFILE_SHA, "T17 profile gate drift")
    value = read(path)
    t17.validate_identity(repo, value)
    if physical:
        files, profile = t17.p.hardware_profile(repo, value["configuration"])
        g.require(profile == value["hardware_profile"], "physical T17 hardware profile drift")
        g.require({n: files[str(Path(value["configuration"]["build_record"]) / n)] for n in t17.p.META_NAMES}
                  == value["metadata_sha256"], "physical T17 build metadata drift")
        return value, files, profile
    return value


def builder(repo):
    a = g.load("firstdot_private_builder", repo / g.ENTRY / "entry_experiment.py")
    proxy = types.SimpleNamespace(**vars(g))
    def load(label, path):
        path = Path(path)
        if path.name == "entry_candidate.py" and path.parent.name == "r2-select":
            return g.load(label, path.parents[4] / g.S1 / "firstdot_candidate.py")
        return g.load(label, path)
    proxy.load = load
    a.g, a.candidate = proxy, c
    return a


def pairs(images, repo, physical=True):
    by = {i["name"]: i for i in images}
    g.require(len(by) == len(images), "duplicate firstdot image")
    common, layouts = None, []
    for image in images:
        record = read(Path(image["path"]) / "build.json")
        identity = {k: record[k] for k in ("kind", "source_commit", "am_revision", "external_files",
                                          "toolchain", "snapshot_files", "contract")}
        common = identity if common is None else common
        g.require(identity == common, "firstdot cross-image build identity")
        if physical:
            for p, digest in record["external_files"].items():
                g.require(g.sha(p) == digest, "firstdot external build input drift")
            for tool in record["toolchain"].values():
                g.require(g.sha(tool["path"]) == tool["sha256"], "firstdot toolchain drift")
        if image["variant"] == "s1":
            key = name(dict(image, variant="firstdot"))
            g.require(key in by, "missing firstdot counterpart")
            layouts.append(dict(s1=image["name"], firstdot=key,
                                **g.paired_layout(image["path"], by[key]["path"])))
    g.require(2 * len(layouts) == len(images), "unpaired firstdot images")
    return dict(status="FIRSTDOT_FIXED_LAYOUT_PASS", pairs=len(layouts), build_identity=common, layouts=layouts)


def build(repo, identity_path, baseline, output, shards, datasets, jobs):
    identity = parent_identity(repo, identity_path)
    cfg = identity["configuration"]
    a = builder(repo)
    a.frozen_f.pinned_modules(repo)
    am = Path(cfg["am_home"])
    g.require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=am, text=True).strip() ==
              a.frozen_f.AM_COMMIT, "AM revision")
    g.require(not subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                         cwd=am, text=True).strip(), "modified official AM")
    tools = {k: shutil.which(cfg["cross_prefix"] + k) for k in ("gcc", "ld", "ar", "objcopy", "objdump", "readelf")}
    tools["make"] = shutil.which("make")
    g.require(all(tools.values()) and 1 <= jobs <= 4, "toolchain/CPU budget")
    output.mkdir(parents=True, exist_ok=False)
    state = dict(contract=c.CONTRACT, status="BUILDING", started=a.frozen_f.now(), jobs=jobs,
                 parent_identity_sha256=g.sha(identity_path), images_completed=0, new_emu_runs=0)
    g.save(output / "state.json", state)
    images = []
    try:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            work = [pool.submit(a.build_one, repo, cfg, output / "images" / name(i), i, tools)
                    for i in inventory(shards, datasets)]
            for future in as_completed(work):
                image = future.result()
                images.append(image)
                state["images_completed"] = len(images)
                g.save(output / "state.json", state)
                print(image["name"], "FIRSTDOT_BUILD_MODEL_PASS", flush=True)
        images.sort(key=lambda i: i["name"])
        g.save(output / "images.json", dict(images=images))
        g.save(output / "pairs.json", pairs(images, repo))
        baseline_checks = []
        for image in images:
            if image["variant"] != "s1":
                continue
            original = baseline / "images" / image["name"]
            g.parent.verify_build(original, repo)
            actual = Path(image["path"])
            for file in ("vdot-perf.bin", "kernels-reference.o", "gemv-reference.o"):
                g.require((original / file).read_bytes() == (actual / file).read_bytes(),
                          "new S1 baseline differs from qualified T17: " + file)
            baseline_checks.append(dict(image=image["name"], original=str(original),
                                        image_sha256=g.sha(actual / "vdot-perf.bin")))
        g.save(output / "baseline-identity.json", dict(status="T17_S1_PAYLOAD_EXACT", images=baseline_checks,
                                                       execution_pass_reused=False))
        state["status"] = BUILD_PASS
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = a.frozen_f.now()
        g.save(output / "state.json", state)
    return state


def runtime(repo, identity):
    f = g.load("firstdot_private_fullcore", repo / g.REL / "fullcore_screen.py")
    proxy = types.SimpleNamespace(**vars(g))
    proxy.load = lambda label, path: (g.counter_adapter(repo) if Path(path).resolve() ==
        (repo / g.O3 / "check.py").resolve() else g.load(label, path))
    f.g = proxy
    f.REFERENCE, f.FLASH = identity["reference_sha256"], identity["flash_sha256"]
    verify = f.verify_runtime
    def checked(*args):
        windows, observation = verify(*args)
        windows["scope"] = SCOPE
        return windows, observation
    f.verify_runtime = checked
    m = g.load("firstdot_private_merged", repo / g.REL / "merged_screen.py")
    m.g, m.f, m.CONTRACT = g, f, c.CONTRACT
    return f, m


def summarize(records):
    originals = [r for r in records if r["replay"] == 0]
    samples = [dict(s, dataset=r["dataset"]) for r in originals for s in r["samples"] if s["phase"] == "measured"]
    key = lambda s: tuple(s[k] for k in ("variant", "shard", "dataset", "software", "method", "repeat"))
    by = {key(s): s for s in samples}
    expected = {(r["variant"], r["shard"], r["dataset"], sw, method, repeat)
                for r in originals for sw in ("basic", "reuse") for method in ("vdot", "rvv") for repeat in range(2, 6)}
    g.require(len(by) == len(samples) and set(by) == expected, "incomplete/duplicate firstdot samples")
    g.require(all(type(s["cycles"]) is int and s["cycles"] > 0 for s in samples), "invalid firstdot cycles")
    rows = []
    for shard in sorted({r["shard"] for r in originals}):
        datasets = sorted({r["dataset"] for r in originals if r["shard"] == shard})
        candidates = []
        for variant in VARIANTS:
            for software in ("basic", "reuse"):
                for method in ("vdot", "rvv"):
                    data = [by[(variant, shard, d, software, method, rep)] for d in datasets for rep in range(2, 6)]
                    values = [s["cycles"] for s in data]
                    candidates.append(dict(variant=variant, software=software, method=method, samples=len(data),
                        total=sum(values), mean=statistics.mean(values), minimum=min(values), maximum=max(values),
                        instructions=sorted({s["instructions"] for s in data})))
        rvv = min((r for r in candidates if r["method"] == "rvv"), key=lambda r: r["total"])
        selected = next(r for r in candidates if (r["variant"], r["software"], r["method"]) == ("firstdot", "reuse", "vdot"))
        baseline = next(r for r in candidates if (r["variant"], r["software"], r["method"]) == ("s1", "reuse", "vdot"))
        rows.append(dict(shard=shard, shape=list(((4, 8), (8, 32), (16, 64), (4, 13))[shard // 2]),
            datasets=datasets, scope="endtoend-with-c-abi-call", candidates=candidates, fastest_rvv=rvv,
            firstdot_reuse_vdot=selected, s1_reuse_vdot=baseline,
            reduction_vs_s1=1 - selected["total"] / baseline["total"],
            reduction_vs_rvv=1 - selected["total"] / rvv["total"],
            firstdot_beats_s1_and_rvv=selected["total"] < min(baseline["total"], rvv["total"])))
    return dict(rows=rows, samples=samples, measured_windows=len(samples))


def run(repo, identity_path, builds, output, operation_id, negative, replay):
    identity, hardware_files, profile = parent_identity(repo, identity_path, physical=True)
    cfg = identity["configuration"]
    f, m = runtime(repo, identity)
    output.mkdir(parents=True, exist_ok=False)
    state = dict(contract=c.CONTRACT, status="PREFLIGHT", operation_id=operation_id, started=f.now(),
                 new_emu_runs=0, active_pid=None, active_result=None, hardware_changed=False,
                 stable_default_changed=False, historical_performance_reused=False)
    persist = lambda: g.save(output / "state.json", state)
    persist()
    records, rejected = [], None
    try:
        files = dict(hardware_files)
        files.update(m.checker_files(repo))
        for rel in g.SOURCES | set(g.FROZEN) | {str(g.S1 / "gate.py"), str(g.REL / "machine_model.py"),
                                               str(REPRO / "clean_entry.py"), str(REPRO / "clean_profile.py")}:
            files[str(repo / rel)] = g.sha(repo / rel)
        files[str(identity_path)] = g.sha(identity_path)
        images = []
        for b in builds:
            g.require(read(b / "state.json")["status"] == BUILD_PASS, "incomplete firstdot build")
            for file in ("state.json", "images.json", "pairs.json", "baseline-identity.json"):
                files[str(b / file)] = g.sha(b / file)
            for image in read(b / "images.json")["images"]:
                p = Path(image["path"])
                g.require(p.resolve() == (b / "images" / image["name"]).resolve(), "firstdot image path")
                g.verify_build(p, repo)
                m.validate_selection(image, read(p / "data/manifest.json"), read(p / "build.json"))
                g.require(g.sha(p / "vdot-perf.bin") == image["image_sha256"], "firstdot image drift")
                for file in ("build.json", "data/manifest.json"):
                    files[str(p / file)] = g.sha(p / file)
                images.append(image)
        g.save(output / "pairs.json", pairs(images, repo))
        g.save(output / "configuration.json", dict(cfg, canonical_builds=[str(p) for p in builds]))
        g.save(output / "hardware-profile.json", profile)
        g.save(output / "runtime-inputs.json", files)
        shutil.copyfile(identity_path, output / "parent-identity.json")
        def launch(image, label, fixture=None, repeated=0):
            before, dest = state["new_emu_runs"], output / "runs" / label
            def progress(record):
                state.update(new_emu_runs=before + int(record.get("process_started") is True),
                    active_result=str(dest / "result.json") if "finished" not in record else None,
                    active_pid=record.get("pid") if "finished" not in record else None)
                persist()
            result = m.execute(repo, cfg, image, dest, files, fixture, repeated, progress)
            print(label, result["status"], flush=True)
            return result
        if negative:
            selected = next(i for i in images if (i["shard"], i["dataset"], i["variant"]) == (3, 0, "firstdot"))
            state["status"] = "NEGATIVE_AND_RECOVERY"
            persist()
            fixture = m.build_negative(repo, cfg, output / "negative-fixture")
            rejected = launch(selected, "negative-firstdot-8x32", fixture)
            detail = rejected["negative_details"]
            g.require(detail["vd"] == 0 and detail["word"] == "0x0388000b" and detail["bit"] == 100,
                      "negative did not exercise changed firstdot destination")
            recovered = launch(selected, "recovery-firstdot-8x32")
            m.validate_recovery(rejected, recovered)
            records.append(recovered)
            g.save(output / "completed-runs.json", records)
        state["status"] = "PERFORMANCE"
        persist()
        for image in sorted(images, key=lambda i: (i["shard"], i["dataset"],
                               VARIANTS.index(i["variant"]) ^ ((i["shard"] + i["dataset"]) % 2))):
            if not any(r["name"] == image["name"] for r in records):
                records.append(launch(image, "formal-" + image["name"]))
                g.save(output / "completed-runs.json", records)
        if replay:
            state["status"] = "REPLAY"
            persist()
            for image in images:
                if image["dataset"] == 0:
                    repeated = launch(image, "replay-" + image["name"], repeated=1)
                    prior = next(r for r in records if r["name"] == image["name"] and r["replay"] == 0)
                    g.require(m.signature(prior) == m.signature(repeated), "firstdot all-window replay differs")
                    records.append(repeated)
                    g.save(output / "completed-runs.json", records)
        summary = summarize(records)
        final_identity, final_files, final_profile = parent_identity(repo, identity_path, physical=True)
        g.require(identity == final_identity and hardware_files == final_files and profile == final_profile,
                  "firstdot hardware identity drift")
        m.verify_files(files)
        pairs(images, repo)
        originals = {r["name"] for r in records if r["replay"] == 0}
        repeats = {r["name"] for r in records if r["replay"] == 1}
        g.require(originals == {i["name"] for i in images} and state["new_emu_runs"] == len(records) + int(negative),
                  "firstdot launch cardinality")
        qualified = bool(negative and rejected and replay and
                         repeats == {i["name"] for i in images if i["dataset"] == 0})
        state["status"] = RUN_PASS if qualified else "FIRSTDOT_PARTIAL_PASS"
        result = dict(status=state["status"], contract=c.CONTRACT, parent_identity_sha256=g.sha(identity_path),
            runs=records, negative=rejected, qualification=dict(negative_and_recovery=bool(negative and rejected),
            all_window_replay=bool(replay), stable_default_changed=False, hardware_changed=False,
            full_matrix={i["shard"] for i in images} == {1, 3, 5, 7} and
                        {i["dataset"] for i in images} == {0, 1, 2}, historical_pass_reused=False), **summary)
        g.save(output / "results.json", result)
        return result
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = f.now()
        persist()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--action", choices=("build", "run"), required=True)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--baseline-build", type=Path)
    p.add_argument("--build", type=Path, action="append")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--shards", type=int, nargs="+", default=[3])
    p.add_argument("--datasets", type=int, nargs="+", default=[0])
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--negative", action="store_true")
    p.add_argument("--replay", action="store_true")
    p.add_argument("--operation-id")
    a = p.parse_args()
    repo, output = a.repo.resolve(), a.output.resolve()
    g.require(repo == ROOT and not output.exists() and not output.is_relative_to(repo), "new external output required")
    if os.name == "posix":
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    if a.action == "build":
        g.require(a.baseline_build is not None, "T17 baseline build required")
        result = build(repo, a.identity.resolve(), a.baseline_build.resolve(), output, a.shards, a.datasets, a.jobs)
    else:
        g.require(a.build and a.operation_id, "run build/operation required")
        result = run(repo, a.identity.resolve(), [b.resolve() for b in a.build], output, a.operation_id, a.negative, a.replay)
    print(json.dumps({k: v for k, v in result.items() if k not in ("runs", "samples")}, indent=2))


if __name__ == "__main__":
    main()
