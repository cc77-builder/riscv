"""Build and run a source-bound, single-hardware S0/S1 full GEMV comparison."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess

import gate as g
import candidate
import fullcore_screen as legacy_f
import merged_screen as legacy_m

CONTRACT = "r2-s1-merged-software-screen-v2-fixed-layout"
PASS = "R2_S1_MERGED_SOFTWARE_SCREEN_PASS"
S1 = candidate.REL

def read_json(path):
    return json.loads(Path(path).read_text())

def inventory():
    return ([dict(suite="smoke", dataset=0, shard=s, variant=v) for s in (5, 7) for v in ("s0", "s1")] +
            [dict(suite="performance", dataset=d, shard=s, variant=v)
             for s in range(8) for d in range(3) for v in ("s0", "s1")])

def name(item):
    return legacy_f.image_name(item)

def config(path, repo):
    value = read_json(path)
    fields = {"am_home", "cross_prefix", "hardware_source", "build_record", "build_driver", "reference", "flash"}
    g.require(set(value) == fields, "S1 configuration fields")
    for key in fields:
        g.require(isinstance(value[key], str) and value[key].strip(), "invalid configuration " + key)
        if key != "cross_prefix":
            value[key] = str(Path(value[key].replace("${REPO}", str(repo))).expanduser().resolve())
    return value

def build_one(repo, cfg, out, item, tools):
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / "source/repo"
    sources = set(g.PINNED) | {str(S1 / "candidate.py")}
    for rel in sorted(sources):
        target = snapshot / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / rel, target)
    for filename in ("main.c", "Makefile", "fixed-layout.ld"):
        shutil.copyfile(snapshot / g.O3 / filename, out / "source" / filename)
    generator = g.load("s1_build_snapshot", snapshot / S1 / "candidate.py")
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
    record = dict(kind="nexus-am-riscv64-xs", source_commit=subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(), contract=CONTRACT,
        s1_candidate_sha256=g.sha(repo / S1 / "candidate.py"), selection=item,
        snapshot_files={rel: g.sha(snapshot / rel) for rel in sorted(sources)},
        am_revision=legacy_f.AM_COMMIT, external_files=external, exit_code=None, commands=[], artifacts={})
    g.save(out / "build.json", record)
    try:
        record["commands"].append(legacy_f.command(argv, repo, out / "make-command", env))
        reference = [tools["gcc"], "-march=rv64gcv", "-mabi=lp64d", "-mno-relax", "-c",
                     str(out / "data/kernels.S"), "-o", str(out / "kernels-reference.o")]
        record["commands"].append(legacy_f.command(reference, repo, out / "reference-command", env))
        for p, digest in external.items():
            g.require(g.sha(p) == digest, "private AM library changed")
        record.update(exit_code=0, artifacts={p: g.sha(out / p) for p in (
            "vdot-perf.elf", "vdot-perf.bin", "kernels-reference.o", "data/manifest.json")},
            toolchain={key: {"path": p, "sha256": g.sha(p)} for key, p in tools.items()})
        g.save(out / "build.json", record)
        g.save(out / "elf-validation.json", g.verify_build(out, repo))
        record["accepted"] = True
    except Exception as exc:
        record.update(accepted=False, error=repr(exc))
        raise
    finally:
        g.save(out / "build.json", record)
    return dict(item, name=name(item), path=str(out), image_sha256=g.sha(out / "vdot-perf.bin"))

def validate_pairs(images, repo):
    keys = {i["name"]: i for i in images}
    identity = None
    fields = ("kind", "source_commit", "am_revision", "external_files", "toolchain", "s1_candidate_sha256", "snapshot_files")
    for image in images:
        record = read_json(Path(image["path"]) / "build.json")
        current = {key: record[key] for key in fields}
        if identity is None:
            identity = current
        g.require(current == identity, "cross-image build identity changed")
        for path, digest in record["external_files"].items():
            g.require(g.sha(path) == digest, "AM library changed after build")
        for tool in record["toolchain"].values():
            g.require(g.sha(tool["path"]) == tool["sha256"], "toolchain changed after build")
    base = candidate.load_base(repo)
    layouts = []
    for item in inventory():
        if item["variant"] != "s0":
            continue
        other = dict(item, variant="s1")
        b0, b1 = [Path(keys[name(x)]["path"]) for x in (item, other)]
        e0, e1 = [g.ELF((b / "vdot-perf.elf").read_bytes()) for b in (b0, b1)]
        layout = g.paired_layout(e0, e1, (b0 / "vdot-perf.bin").read_bytes(), (b1 / "vdot-perf.bin").read_bytes())
        layouts.append(dict(s0=name(item), s1=name(other), **layout))
        m0, m1 = [read_json(b / "data/manifest.json") for b in (b0, b1)]
        g.require(m0["plan"] == m1["plan"], "paired ordering changed")
        g.require(all(e0.symbols[f"t13_kernel_{i}"][0] == e1.symbols[f"t13_kernel_{i}"][0]
                      for i in range(4)), "paired kernel entry address differs")
        for r0, r1 in zip(m0["rows"], m1["rows"]):
            g.require({k: v for k, v in r0.items() if k not in ("body", "r2_variant")} ==
                      {k: v for k, v in r1.items() if k not in ("body", "r2_variant")},
                      "paired math/input/output/CSR/scratch differs")
            g.require(r0["body"] == base.kernel(r0["m"], r0["k"], r0["method"], r0["software"], r0["scope"]),
                      "S0 body not frozen O3")
    return dict(status="S1_PAIR_LAYOUT_AND_FAIR_INPUTS_PASS", pairs=len(images) // 2, build_identity=identity,
                kernel_slot_bytes=8192, historical_samples_reused=False, layouts=layouts,
                nonkernel_loaded_bytes_identical=True)

def build(repo, cfg, out):
    out.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status="BUILDING", started=legacy_f.now(), new_emu_runs=0, images_completed=0)
    g.save(out / "state.json", state)
    try:
        g.verify_sources(repo)
        legacy_f.pinned_modules(repo)
        am = Path(cfg["am_home"])
        g.require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=am, text=True).strip() == legacy_f.AM_COMMIT,
                  "AM revision")
        g.require(not subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                             cwd=am, text=True).strip(), "modified tracked AM source")
        tools = {key: shutil.which(cfg["cross_prefix"] + key) for key in
                 ("gcc", "ld", "ar", "objcopy", "objdump", "readelf")}
        tools["make"] = shutil.which("make")
        g.require(all(tools.values()), "missing GNU tools")
        images = []
        for item in inventory():
            images.append(build_one(repo, cfg, out / "images" / name(item), item, tools))
            state["images_completed"] = len(images)
            g.save(out / "state.json", state)
            print(name(item), "S1_BUILD_AND_MODEL_PASS", flush=True)
        g.save(out / "images.json", dict(images=images))
        g.save(out / "pairs.json", validate_pairs(images, repo))
        state["status"] = "S1_52_CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN"
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = legacy_f.now()
        g.save(out / "state.json", state)
    return state

def summarize(records):
    samples = [s for r in records if r["suite"] == "performance" and r["replay"] == 0
               for s in r["samples"] if s["phase"] == "measured"]
    expected = {(v, shard, sw, method, dataset, repeat)
                for v in ("s0", "s1") for shard in range(8) for sw in ("basic", "reuse")
                for method in ("vdot", "rvv") for dataset in range(3) for repeat in range(2, 6)}
    keys = {}
    for s in samples:
        key = tuple(s[k] for k in ("variant", "shard", "software", "method", "dataset", "repeat"))
        g.require(key not in keys and s["mode"] == "merged" and type(s["cycles"]) is int and s["cycles"] > 0 and
                  type(s["instructions"]) is int and s["instructions"] > 0, "invalid/duplicate sample")
        keys[key] = s
    g.require(set(keys) == expected and len(samples) == 768, "missing/extra formal S1 matrix samples")
    rows, comparisons = [], []
    for shard in range(8):
        for variant in ("s0", "s1"):
            for sw in ("basic", "reuse"):
                row = dict(shard=shard, shape=list(((4, 8), (8, 32), (16, 64), (4, 13))[shard // 2]),
                           scope=("core", "endtoend")[shard % 2], variant=variant, software=sw)
                for method in ("vdot", "rvv"):
                    data = [keys[(variant, shard, sw, method, d, r)] for d in range(3) for r in range(2, 6)]
                    values = [s["cycles"] for s in data]
                    row[method] = dict(samples=12, total=sum(values), mean=statistics.mean(values),
                                       minimum=min(values), maximum=max(values), pstdev=statistics.pstdev(values),
                                       instructions_total=sum(s["instructions"] for s in data))
                row["rvv_over_vdot"] = row["rvv"]["total"] / row["vdot"]["total"]
                rows.append(row)
        eligible = [r for r in rows if r["shard"] == shard]
        rvv = min(eligible, key=lambda r: r["rvv"]["total"])
        for row in eligible:
            baseline = next(r for r in eligible if r["variant"] == "s0" and r["software"] == row["software"])
            comparisons.append(dict(shard=shard, variant=row["variant"], software=row["software"],
                                    s0_over_variant=baseline["vdot"]["total"] / row["vdot"]["total"],
                                    fastest_rvv_variant=rvv["variant"], fastest_rvv_software=rvv["software"],
                                    fastest_rvv_over_vdot=rvv["rvv"]["total"] / row["vdot"]["total"]))
    return dict(samples=samples, rows=rows, comparisons=comparisons)

def run(repo, cfg, build_dir, out, operation_id):
    out.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, operation_id=operation_id, status="PREFLIGHT", started=legacy_f.now(),
                 new_emu_runs=0, active_result=None, active_pid=None, hardware_changed=False,
                 historical_b0_h1_acceptance=False, whole_suite_acceptance=False)
    persist = lambda: g.save(out / "state.json", state)
    persist()
    # Private module instances inject strict S1 build/regeneration. The old
    # UART/CSR/retirement/O2 checks run unchanged; no old file is edited.
    f = g.load("s1_private_fullcore_runner", repo / g.REL / "fullcore_screen.py")
    f.g = g
    m = g.load("s1_private_merged_runner", repo / g.REL / "merged_screen.py")
    m.g, m.f, m.CONTRACT = g, f, CONTRACT
    def launch(image, label, negative=None, replay=0):
        before = state["new_emu_runs"]
        run_dir = out / "runs" / label
        def progress(record):
            state.update(new_emu_runs=before + int(record.get("process_started") is True),
                         active_result=str(run_dir / "result.json") if "finished" not in record else None,
                         active_pid=record.get("pid") if "finished" not in record else None)
            persist()
        return m.execute(repo, cfg, image, run_dir, files, negative, replay, progress)
    try:
        g.save(out / "configuration.json", dict(cfg, canonical_build=str(build_dir)))
        files = legacy_m.checker_files(repo)
        for rel in (S1 / "candidate.py", S1 / "gate.py", S1 / "experiment.py", g.REL / "machine_model.py"):
            files[str(repo / rel)] = g.sha(repo / rel)
        hardware_files, profile = legacy_m.hardware_profile(repo, cfg)
        files.update(hardware_files)
        profile["software_contract"] = CONTRACT
        g.save(out / "hardware-profile.json", profile)
        g.require(read_json(build_dir / "state.json")["status"] == "S1_52_CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN",
                  "canonical build incomplete")
        for filename in ("state.json", "images.json", "pairs.json"):
            files[str(build_dir / filename)] = g.sha(build_dir / filename)
        images = read_json(build_dir / "images.json")["images"]
        expected = {name(i): i for i in inventory()}
        g.require(len(images) == 52 and {i["name"] for i in images} == set(expected), "image inventory")
        for image in images:
            g.require(all(image[k] == v for k, v in expected[image["name"]].items()), "image selection")
            b = Path(image["path"])
            g.require(b.resolve() == (build_dir / "images" / image["name"]).resolve(), "image path outside build")
            g.verify_build(b, repo)
            m.validate_selection(image, read_json(b / "data/manifest.json"), read_json(b / "build.json"))
            g.require(g.sha(b / "vdot-perf.bin") == image["image_sha256"], "image changed")
            files[str(b / "build.json")] = g.sha(b / "build.json")
            files[str(b / "data/manifest.json")] = g.sha(b / "data/manifest.json")
        g.save(out / "pair-layout.json", validate_pairs(images, repo))
        g.save(out / "runtime-inputs.json", files)
        selected = {i["name"]: i for i in images}
        fixture = legacy_m.build_negative(repo, cfg, out / "negative-fixture")
        smoke = selected[name(dict(suite="smoke", variant="s1", dataset=0, shard=5))]
        state["status"] = "NEGATIVE_AND_SMOKE"
        persist()
        negative = launch(smoke, "negative-s1-s05", fixture)
        recovery = launch(smoke, "recovery-s1-s05")
        m.validate_recovery(negative, recovery)
        records = [recovery]
        for item in inventory()[:4]:
            if name(item) == smoke["name"]:
                continue
            records.append(launch(selected[name(item)], "smoke-" + name(item)))
        g.save(out / "smoke-result.json", dict(status="S1_FOUR_SMOKES_AND_RECOVERY_PASS",
                                              negative=negative, runs=records))
        state["status"] = "PERFORMANCE"
        persist()
        for shard in range(8):
            for dataset in range(3):
                order = ("s0", "s1") if (shard + dataset) % 2 == 0 else ("s1", "s0")
                for variant in order:
                    item = dict(suite="performance", variant=variant, dataset=dataset, shard=shard)
                    records.append(launch(selected[name(item)], "formal-" + name(item)))
                    g.save(out / "completed-runs.json", records)
        state["status"] = "REPLAY"
        persist()
        for shard in (5, 7):
            for variant in ("s0", "s1"):
                item = dict(suite="performance", variant=variant, dataset=0, shard=shard)
                replay = launch(selected[name(item)], "replay-" + name(item), replay=1)
                original = next(r for r in records if r["name"] == name(item) and r["replay"] == 0)
                g.require(m.signature(original) == m.signature(replay), "cycle/instret replay differs")
                records.append(replay)
        summary = summarize(records)
        g.require(state["new_emu_runs"] == 57 and len(records) == 56, "unexpected actual launch count")
        final_hardware_files, final_profile = legacy_m.hardware_profile(repo, cfg)
        final_profile["software_contract"] = CONTRACT
        g.require(final_profile == profile and all(files.get(p) == h for p, h in final_hardware_files.items()),
                  "hardware provenance changed during campaign")
        legacy_m.verify_files(files)
        validate_pairs(images, repo)
        g.save(out / "results.json", dict(status=PASS, contract=CONTRACT, runs=records, negative=negative, **summary))
        state.update(status=PASS, measured_windows=768, replay_runs=4, normal_runs=56,
                     negative_runs=1, performance_measured=True)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = legacy_f.now()
        persist()
    return state

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--action", choices=("build", "run"), required=True)
    p.add_argument("--build", type=Path)
    p.add_argument("--operation-id")
    a = p.parse_args()
    repo = a.repo.resolve()
    cfg = config(a.config, repo)
    if a.action == "build":
        value = build(repo, cfg, a.output.resolve())
    else:
        g.require(a.build is not None and bool(a.operation_id), "run requires build and operation ID")
        value = run(repo, cfg, a.build.resolve(), a.output.resolve(), a.operation_id)
    print(json.dumps(value, indent=2))

