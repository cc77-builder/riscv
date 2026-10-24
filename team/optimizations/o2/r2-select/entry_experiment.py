"""Build/run the independent R4 callable-entry experiment; no implicit resume."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import types

import entry_gate as g
import entry_candidate as candidate
import fullcore_screen as frozen_f
import merged_screen as frozen_m


def read(path):
    return json.loads(Path(path).read_text())


def name(item):
    return frozen_f.image_name(item)


def inventory(shards, datasets):
    g.require(len(set(shards)) == len(shards) and set(shards) <= {1, 3, 5, 7} and shards,
              "R4 endtoend shape selection")
    g.require(len(set(datasets)) == len(datasets) and set(datasets) <= {0, 1, 2} and datasets,
              "R4 dataset selection")
    return [dict(suite="performance", dataset=d, shard=s, variant=v)
            for s in shards for d in datasets for v in ("s0", "s1")]


def config(path):
    result = read(path)
    fields = {"am_home", "cross_prefix", "hardware_source", "build_record", "build_driver", "reference", "flash"}
    g.require(set(result) == fields and all(isinstance(v, str) and v.strip() for v in result.values()),
              "R4 configuration fields")
    for key in fields - {"cross_prefix"}:
        result[key] = str(Path(result[key]).expanduser().resolve())
    return result


def build_one(repo, cfg, out, item, tools):
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / "source/repo"
    for rel in sorted(g.SOURCES):
        target = snapshot / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / rel, target)
    for filename in ("main.c", "Makefile", "fixed-layout.ld"):
        shutil.copyfile(snapshot / g.O3 / filename, out / "source" / filename)
    generator = g.load("r4_build_snapshot_" + name(item), snapshot / g.ENTRY / "entry_candidate.py")
    generator.generate(snapshot, out / "data", item["variant"], item["dataset"], item["shard"], item["suite"])
    am = Path(cfg["am_home"])
    libraries = [am / "am/build/am-riscv64-xs.a", am / "libs/klib/build/klib-riscv64-xs.a"]
    external = {str(p): g.sha(p) for p in libraries}
    env = dict(os.environ)
    for key in ("CFLAGS", "CPPFLAGS", "CXXFLAGS", "ASFLAGS", "LDFLAGS", "CC_OPT", "MAKEFLAGS", "MFLAGS",
                "CC", "AS", "LD", "OBJCOPY", "OBJDUMP", "ARCH", "MARCH", "LIBS", "PREBUILD"):
        env.pop(key, None)
    env.update(AM_HOME=str(am), LINUX_GNU_TOOLCHAIN="1")
    prefix = str(Path(tools["gcc"]))[:-3]
    argv = [tools["make"], "-C", str(out / "source"), "ARCH=riscv64-xs", "MARCH=rv64gcv",
            "CROSS_COMPILE=" + prefix, "T13_DATA=" + str(out / "data"),
            "T13_OBJ_ROOT=" + str(out / "objects"), "BINARY=" + str(out / "vdot-perf"),
            "-o", "am", "-o", "klib", "-j1", "image"]
    record = dict(kind="nexus-am-riscv64-xs", contract=candidate.CONTRACT,
                  source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
                  selection=item, snapshot_files={p: g.sha(snapshot / p) for p in sorted(g.SOURCES)},
                  am_revision=frozen_f.AM_COMMIT, external_files=external, exit_code=None, commands=[], artifacts={})
    g.save(out / "build.json", record)
    try:
        record["commands"].append(frozen_f.command(argv, repo, out / "make-command", env))
        for source, obj, label in (("kernels.S", "kernels-reference.o", "reference-command"),
                                   ("gemv.S", "gemv-reference.o", "public-reference-command")):
            command = [tools["gcc"], "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-c",
                       str(out / "data" / source), "-o", str(out / obj)]
            record["commands"].append(frozen_f.command(command, repo, out / label, env))
        # A separately compiled ordinary C caller verifies the installed header
        # and public symbols; target runtime qualification uses the actual leaf
        # bytes in the measured executable, not this relocatable smoke object.
        manifest = read(out / "data/manifest.json")
        caller = '#include "gemv.h"\nvoid r4_header_link_test(const int8_t *a, void *b) {\n' + \
                 "".join(f"  {r['api_symbol']}(a, b);\n" for r in manifest["rows"]) + "}\n"
        (out / "api-c-smoke.c").write_text(caller)
        command = [tools["gcc"], "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-ffreestanding", "-O2",
                   "-I" + str(out / "data"), "-c", str(out / "api-c-smoke.c"), "-o", str(out / "api-c-smoke.o")]
        record["commands"].append(frozen_f.command(command, repo, out / "api-c-compile", env))
        command = [tools["ld"], "-r", "--no-relax", str(out / "api-c-smoke.o"),
                   str(out / "gemv-reference.o"), "-o", str(out / "api-c-linked.o")]
        record["commands"].append(frozen_f.command(command, repo, out / "api-c-link", env))
        linked = g.ELF((out / "api-c-linked.o").read_bytes())
        g.require(all(r["api_symbol"] in linked.symbols for r in manifest["rows"]), "C API missing symbol")
        for p, digest in external.items():
            g.require(g.sha(p) == digest, "AM library changed")
        record.update(exit_code=0, artifacts={p: g.sha(out / p) for p in sorted(g.ARTIFACTS)},
                      toolchain={key: {"path": p, "sha256": g.sha(p)} for key, p in tools.items()},
                      public_c_link_test={p: g.sha(out / p) for p in
                                          ("api-c-smoke.c", "api-c-smoke.o", "api-c-linked.o")})
        g.save(out / "build.json", record)
        g.save(out / "elf-validation.json", g.verify_build(out, repo))
        record["accepted"] = True
    except BaseException as exc:
        record.update(accepted=False, error=repr(exc))
        raise
    finally:
        g.save(out / "build.json", record)
    return dict(item, name=name(item), path=str(out), image_sha256=g.sha(out / "vdot-perf.bin"))


def validate_pairs(images, repo):
    indexed = {i["name"]: i for i in images}
    g.require(len(indexed) == len(images), "duplicate R4 image")
    common, layouts = None, []
    for image in images:
        record = read(Path(image["path"]) / "build.json")
        identity = {key: record[key] for key in ("kind", "source_commit", "am_revision", "external_files",
                                                "toolchain", "snapshot_files", "contract")}
        common = identity if common is None else common
        g.require(identity == common, "R4 cross-image build identity differs")
        frozen_m.verify_files(record["external_files"])
        for tool in record["toolchain"].values():
            g.require(g.sha(tool["path"]) == tool["sha256"], "R4 toolchain drift")
        if image["variant"] == "s0":
            other = name({key: ("s1" if key == "variant" else image[key])
                          for key in ("suite", "dataset", "shard", "variant")})
            g.require(other in indexed, "missing R4 counterpart")
            layouts.append(dict(s0=image["name"], s1=other,
                                **g.paired_layout(image["path"], indexed[other]["path"])))
    g.require(len(layouts) * 2 == len(images), "unpaired R4 image")
    return dict(status="R4_COMPLETE_LAYOUT_AND_INPUTS_PASS", pairs=len(layouts),
                build_identity=common, layouts=layouts, historical_samples_reused=False)


def build(repo, cfg, out, shards, datasets, jobs):
    g.require(1 <= jobs <= 4, "total build worker budget")
    out.mkdir(parents=True, exist_ok=False)
    state = dict(status="BUILDING", contract=candidate.CONTRACT, started=frozen_f.now(), jobs=jobs,
                 images_completed=0, new_emu_runs=0)
    g.save(out / "state.json", state)
    try:
        g.verify_sources(repo)
        frozen_f.pinned_modules(repo)
        am = Path(cfg["am_home"])
        g.require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=am, text=True).strip() == frozen_f.AM_COMMIT,
                  "AM revision")
        g.require(not subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                             cwd=am, text=True).strip(), "modified tracked AM source")
        tools = {k: shutil.which(cfg["cross_prefix"] + k) for k in ("gcc", "ld", "ar", "objcopy", "objdump", "readelf")}
        tools["make"] = shutil.which("make")
        g.require(all(tools.values()), "GNU toolchain unavailable")
        items, images = inventory(shards, datasets), []
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(build_one, repo, cfg, out / "images" / name(i), i, tools): i for i in items}
            for future in as_completed(futures):
                image = future.result()
                images.append(image)
                state["images_completed"] = len(images)
                g.save(out / "state.json", state)
                print(image["name"], "R4_BUILD_AND_MODEL_PASS", flush=True)
        images.sort(key=lambda x: x["name"])
        g.save(out / "images.json", dict(images=images))
        g.save(out / "pairs.json", validate_pairs(images, repo))
        state["status"] = "R4_CANONICAL_CALLABLE_ELFS_STATIC_PASS_RUNTIME_NOT_RUN"
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = frozen_f.now()
        g.save(out / "state.json", state)
    return state


def summarize(records):
    originals = [r for r in records if r["replay"] == 0]
    samples = [s for r in originals for s in r["samples"] if s["phase"] == "measured"]
    expected = {(r["variant"], r["shard"], r["dataset"], sw, method, repeat)
                for r in originals for sw in ("basic", "reuse") for method in ("vdot", "rvv") for repeat in range(2, 6)}
    keys = {}
    for s in samples:
        key = tuple(s[k] for k in ("variant", "shard", "dataset", "software", "method", "repeat"))
        g.require(key not in keys and type(s["cycles"]) is int and s["cycles"] > 0, "duplicate/invalid formal sample")
        keys[key] = s
    g.require(set(keys) == expected and len(expected) == len(originals) * 16, "incomplete R4 samples")
    rows = []
    for shard in sorted({r["shard"] for r in originals}):
        datasets = sorted({r["dataset"] for r in originals if r["shard"] == shard})
        candidates = []
        for variant in ("s0", "s1"):
            for software in ("basic", "reuse"):
                for method in ("vdot", "rvv"):
                    data = [keys[(variant, shard, d, software, method, rep)] for d in datasets for rep in range(2, 6)]
                    values = [s["cycles"] for s in data]
                    candidates.append(dict(variant=variant, software=software, method=method, samples=len(data),
                                           total=sum(values), mean=statistics.mean(values),
                                           minimum=min(values), maximum=max(values),
                                           instructions=sorted({s["instructions"] for s in data})))
        fastest = min((c for c in candidates if c["method"] == "rvv"), key=lambda c: c["total"])
        selected = next(c for c in candidates if c["variant"] == "s1" and c["software"] == "reuse" and c["method"] == "vdot")
        rows.append(dict(shard=shard, shape=list(((4, 8), (8, 32), (16, 64), (4, 13))[shard // 2]),
                         datasets=datasets, scope="endtoend-with-c-abi-call", candidates=candidates,
                         fastest_rvv=fastest, s1_reuse_vdot=selected,
                         fastest_rvv_over_s1_reuse=fastest["total"] / selected["total"],
                         s1_reuse_beats_fastest_rvv=selected["total"] < fastest["total"]))
    return dict(samples=samples, rows=rows, measured_windows=len(samples))


def run(repo, cfg, build_dirs, out, operation_id, negative, replay):
    out.mkdir(parents=True, exist_ok=False)
    state = dict(status="PREFLIGHT", contract=candidate.CONTRACT, operation_id=operation_id,
                 started=frozen_f.now(), new_emu_runs=0, active_result=None, active_pid=None,
                 hardware_changed=False, historical_b0_h1_acceptance=False, whole_suite_acceptance=False)
    persist = lambda: g.save(out / "state.json", state)
    persist()
    f = g.load("r4_private_fullcore_runner", repo / g.REL / "fullcore_screen.py")
    proxy = types.SimpleNamespace(**vars(g))
    proxy.load = lambda module_name, path: (g.counter_adapter(repo) if Path(path).resolve() ==
                    (repo / g.O3 / "check.py").resolve() else g.load(module_name, path))
    f.g = proxy
    old_runtime = f.verify_runtime
    def verify_runtime(repo_, build_, run_):
        windows, analysis = old_runtime(repo_, build_, run_)
        windows["scope"] = "R4 full-width live DiffTest, one C-ABI call/return, exact retirement and calibrated counters"
        return windows, analysis
    f.verify_runtime = verify_runtime
    m = g.load("r4_private_merged_runner", repo / g.REL / "merged_screen.py")
    m.g, m.f, m.CONTRACT = g, f, candidate.CONTRACT
    def launch(image, label, fixture=None, repeat=0):
        before, run_dir = state["new_emu_runs"], out / "runs" / label
        def progress(record):
            state.update(new_emu_runs=before + int(record.get("process_started") is True),
                         active_result=str(run_dir / "result.json") if "finished" not in record else None,
                         active_pid=record.get("pid") if "finished" not in record else None)
            persist()
        result = m.execute(repo, cfg, image, run_dir, files, fixture, repeat, progress)
        print(label, result["status"], flush=True)
        return result
    try:
        files = frozen_m.checker_files(repo)
        for rel in g.SOURCES | {str(g.S1 / "gate.py"), str(g.REL / "machine_model.py")}:
            files[str(repo / rel)] = g.sha(repo / rel)
        hardware_files, profile = frozen_m.hardware_profile(repo, cfg)
        files.update(hardware_files)
        g.save(out / "hardware-profile.json", dict(profile, software_contract=candidate.CONTRACT))
        g.save(out / "configuration.json", dict(cfg, canonical_builds=[str(p) for p in build_dirs]))
        images = []
        for build_dir in build_dirs:
            g.require(read(build_dir / "state.json")["status"] == "R4_CANONICAL_CALLABLE_ELFS_STATIC_PASS_RUNTIME_NOT_RUN",
                      "R4 canonical build incomplete")
            for filename in ("state.json", "images.json", "pairs.json"):
                files[str(build_dir / filename)] = g.sha(build_dir / filename)
            for image in read(build_dir / "images.json")["images"]:
                b = Path(image["path"])
                g.require(b.resolve() == (build_dir / "images" / image["name"]).resolve(), "R4 image path")
                g.verify_build(b, repo)
                m.validate_selection(image, read(b / "data/manifest.json"), read(b / "build.json"))
                g.require(g.sha(b / "vdot-perf.bin") == image["image_sha256"], "R4 selected BIN changed")
                for filename in ("build.json", "data/manifest.json"):
                    files[str(b / filename)] = g.sha(b / filename)
                images.append(image)
        g.save(out / "pair-layout.json", validate_pairs(images, repo))
        g.save(out / "runtime-inputs.json", files)
        records, rejected = [], None
        chosen = {i["name"]: i for i in images}
        if negative:
            key = name(dict(suite="performance", variant="s1", dataset=0, shard=3))
            g.require(key in chosen, "negative probe requires 8x32/d0/S1")
            state["status"] = "NEGATIVE_AND_RECOVERY"
            persist()
            fixture = frozen_m.build_negative(repo, cfg, out / "negative-fixture")
            rejected = launch(chosen[key], "negative-s1-8x32", fixture)
            recovered = launch(chosen[key], "recovery-s1-8x32")
            m.validate_recovery(rejected, recovered)
            records.append(recovered)
            g.save(out / "completed-runs.json", records)
        state["status"] = "PERFORMANCE"
        persist()
        for image in sorted(images, key=lambda i: (i["shard"], i["dataset"],
                           i["variant"] if (i["shard"] + i["dataset"]) % 2 == 0 else i["variant"] == "s0")):
            if any(r["name"] == image["name"] for r in records):
                continue
            records.append(launch(image, "formal-" + image["name"]))
            g.save(out / "completed-runs.json", records)
        if replay:
            state["status"] = "REPLAY"
            persist()
            for image in images:
                if image["dataset"] == 0:
                    repeated = launch(image, "replay-" + image["name"], repeat=1)
                    previous = next(r for r in records if r["name"] == image["name"] and r["replay"] == 0)
                    g.require(m.signature(previous) == m.signature(repeated), "R4 all-window cycle/instret replay differs")
                    records.append(repeated)
                    g.save(out / "completed-runs.json", records)
        summary = summarize(records)
        final_files, final_profile = frozen_m.hardware_profile(repo, cfg)
        g.require(profile == final_profile and hardware_files == final_files, "R4 hardware provenance drift")
        frozen_m.verify_files(files)
        validate_pairs(images, repo)
        formal_names = {r["name"] for r in records if r["replay"] == 0}
        replay_names = {r["name"] for r in records if r["replay"] != 0}
        expected_replays = {i["name"] for i in images if i["dataset"] == 0}
        shapes = {i["shard"] for i in images}
        replay_shapes = {r["shard"] for r in records if r["replay"] != 0}
        replay_complete = bool(replay) and replay_names == expected_replays and replay_shapes == shapes
        qualification = dict(real_negative_and_same_image_recovery=bool(negative and rejected),
                             all_shape_replay_complete=replay_complete,
                             normal_image_count=len(formal_names), replay_image_count=len(replay_names),
                             new_execution_path=True, whole_suite_acceptance=False,
                             historical_performance_reused=False)
        qualified = qualification["real_negative_and_same_image_recovery"] and replay_complete
        status = "R4_CALLABLE_ENTRY_SCREEN_PASS" if qualified else "R4_CALLABLE_ENTRY_PARTIAL_PASS"
        g.require(len(formal_names) == len(images) and state["new_emu_runs"] == len(records) + int(negative),
                  "R4 actual launch/cardinality mismatch")
        g.save(out / "results.json", dict(status=status, contract=candidate.CONTRACT,
                                          runs=records, negative=rejected, qualification=qualification, **summary))
        state.update(status=status, normal_runs=len(records), qualification=qualification,
                     negative_runs=int(negative), measured_windows=summary["measured_windows"])
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = frozen_f.now()
        persist()
    return state


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--action", choices=("build", "run"), required=True)
    p.add_argument("--shards", type=int, nargs="+", default=[3])
    p.add_argument("--datasets", type=int, nargs="+", default=[0])
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--build", type=Path, action="append")
    p.add_argument("--operation-id")
    p.add_argument("--negative", action="store_true")
    p.add_argument("--replay", action="store_true")
    a = p.parse_args()
    repo, cfg = a.repo.resolve(), config(a.config)
    g.require(Path(__file__).resolve() == (repo / g.ENTRY / "entry_experiment.py").resolve() and
              Path(candidate.__file__).resolve() == (repo / g.ENTRY / "entry_candidate.py").resolve() and
              Path(g.__file__).resolve() == (repo / g.ENTRY / "entry_gate.py").resolve(),
              "entry CLI and --repo are different checkouts")
    if a.action == "build":
        result = build(repo, cfg, a.output.resolve(), a.shards, a.datasets, a.jobs)
    else:
        g.require(a.build and a.operation_id, "R4 run requires canonical build and operation identity")
        result = run(repo, cfg, [b.resolve() for b in a.build], a.output.resolve(), a.operation_id, a.negative, a.replay)
    print(json.dumps(result, indent=2))
