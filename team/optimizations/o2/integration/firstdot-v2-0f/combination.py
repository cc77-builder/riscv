"""Current 0f + firstdot V2: independently bound integration contract.

Reuse upstream generators, full128 models, paired layout, instruction/CSR/O2
observers and fault/recovery checks unchanged. Historical T17 hardware and
archived S1 image qualification is deliberately not claimed by this contract.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "team/optimizations/o2/r2-vector-accum"))
import firstdot_experiment as upstream
import firstdot_c_api as upstream_c
import current_hardware as hardware

g, c = upstream.g, upstream.c
REPRO = upstream.REPRO
VARIANTS = upstream.VARIANTS
CONTRACT = "zjhwork-0f-firstdot-v2-integration-v1"
BUILD_PASS = "CURRENT_FIRSTDOT_STATIC_PASS_RUNTIME_NOT_RUN"
RUN_PASS = "CURRENT_FIRSTDOT_PAIRED_C_ABI_PASS"
read, name, inventory = upstream.read, upstream.name, upstream.inventory
outside_inputs, validate_image = upstream.outside_inputs, upstream.validate_image
pairs, summarize, qualification = upstream.pairs, upstream.summarize, upstream.qualification

def verify_imports():
    manifest = read(HERE / "import-manifest.json")
    g.require(manifest["upstream_ref"] == "fcf4a11fc569cb2a8fcb4e18d96ec2764b228557"
              and manifest["historical_pass_reused"] is False, "import source identity")
    seen = set()
    for row in manifest["files"]:
        rel = Path(row["path"])
        g.require(not rel.is_absolute() and ".." not in rel.parts and row["path"] not in seen,
                  "unsafe/duplicate imported file")
        seen.add(row["path"])
        path = ROOT / rel
        g.require(path.is_file() and not path.is_symlink() and path.stat().st_size == row["bytes"]
                  and g.sha(path) == row["sha256"], "imported source drift: " + row["path"])
    g.require(len(seen) == 45, "incomplete imported source inventory")

def adapter_files():
    verify_imports()
    names = ("combination.py","current_hardware.py","import-manifest.json","CONTRACT.md")
    return {str(HERE / name): g.sha(HERE / name) for name in names}

def hardware_module(identity):
    if identity["contract"] == hardware.ANCHOR["contract"]:
        return hardware
    # A separately sealed clean-build contract; no historical T17 identity is accepted.
    sys.path.insert(0, str(HERE / "clean"))
    import current_clean_identity
    g.require(identity["contract"] == current_clean_identity.CONTRACT, "unknown hardware contract")
    return current_clean_identity

def parent_identity(repo, path, physical=False):
    verify_imports()
    return hardware_module(read(path)).validate_identity(repo, path, physical=physical)


def runtime(repo, identity):
    f, m = upstream.runtime(repo, identity)
    m.SOURCE = identity["source_commit"]
    m.EMU = identity["hardware_profile"]["emu_sha256"]
    m.META = dict(identity["metadata_sha256"])
    m.CONTRACT = CONTRACT
    def profile(root, cfg):
        files, value = hardware_module(identity).hardware_profile(root, cfg)
        g.require(value == identity["hardware_profile"], "current hardware profile drift")
        return files, value
    m.hardware_profile = profile
    original = m.checker_files
    def checker_files(root):
        return original(root) | adapter_files()
    m.checker_files = checker_files
    return f, m

def verify_build_scope(repo, output, images, identity_path=None):
    receipt = read(output / "combination-build.json")
    g.require(receipt["contract"] == CONTRACT and receipt["historical_pass_reused"] is False,
              "wrong integration build contract")
    g.require(receipt["images"] == {i["name"]: i["image_sha256"] for i in images},
              "current paired image inventory drift")
    g.require(receipt["adapter_files"] == adapter_files(), "integration adapter drift")
    if identity_path is not None:
        g.require(receipt["parent_identity_sha256"] == g.sha(identity_path), "build hardware identity differs")

def build(repo, identity_path, output, shards, datasets):
    identity = parent_identity(repo, identity_path)
    cfg = identity["configuration"]
    outside_inputs(output, [repo, identity_path.parent, cfg["hardware_source"], cfg["build_record"], cfg["am_home"]])
    a = upstream.builder(repo)
    a.frozen_f.pinned_modules(repo)
    am = Path(cfg["am_home"])
    g.require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=am, text=True).strip()
              == a.frozen_f.AM_COMMIT, "AM revision")
    g.require(not subprocess.check_output(["git","status","--porcelain","--untracked-files=no"],
              cwd=am,text=True).strip(), "modified AM source")
    tools = {k: shutil.which(cfg["cross_prefix"]+k) for k in ("gcc","ld","ar","objcopy","objdump","readelf")}
    tools["make"] = shutil.which("make")
    g.require(all(tools.values()), "missing cross toolchain")
    output.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status="BUILDING", started=a.frozen_f.now(), images_completed=0, new_emu_runs=0)
    g.save(output / "state.json", state)
    images = []
    try:
        for item in inventory(shards, datasets):
            image = a.build_one(repo, cfg, output / "images" / name(item), item, tools)
            images.append(image)
            state["images_completed"] = len(images)
            g.save(output / "state.json", state)
            print(image["name"], "BUILD_AND_MODEL_PASS", flush=True)
        images.sort(key=lambda i: i["name"])
        g.save(output / "images.json", dict(images=images))
        g.save(output / "pairs.json", pairs(images, repo))
        g.save(output / "combination-build.json", dict(contract=CONTRACT,
            images={i["name"]:i["image_sha256"] for i in images}, adapter_files=adapter_files(),
            parent_identity_sha256=g.sha(identity_path), historical_pass_reused=False,
            scope="Fresh S1 and firstdot payloads under unchanged software generators; no old T17 run reused"))
        verify_build_scope(repo, output, images, identity_path)
        state["status"] = BUILD_PASS
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = a.frozen_f.now()
        g.save(output / "state.json", state)
    return state

def c_adapter(repo, identity):
    f, m = runtime(repo, identity)
    check_negative = m.negative_check
    def checked_negative(*args):
        detail = check_negative(*args)
        g.require(detail["vd"] == 0 and detail["word"] == "0x0388000b" and detail["bit"] == 100,
                  "ordinary C firstdot negative destination")
        return detail
    m.negative_check = checked_negative
    base = g.load("current_firstdot_c_application", repo / upstream_c.PARENT)
    base.CONTRACT = upstream_c.CONTRACT
    base.generate, base.source_files = upstream_c.generate, upstream_c.source_files
    base.a = types.SimpleNamespace(read=read, frozen_f=f, frozen_m=m)
    return base

def library_anchor(repo, build, matrix):
    images = read(matrix / "images.json")["images"]
    verify_build_scope(repo, matrix, images)
    public = g.ELF((build / "gemv-reference.o").read_bytes())
    manifest = read(build / "source/manifest.json")
    expected = {(s,d) for s in (1,3,5,7) for d in range(3)}
    seen, rows = set(), []
    for image in images:
        if image["variant"] != "firstdot": continue
        key = image["shard"], image["dataset"]
        g.require(key not in seen, "duplicate C matrix anchor")
        seen.add(key)
        path = Path(image["path"])
        g.verify_build(path, repo)
        linked = g.ELF((path / "gemv-reference.o").read_bytes())
        for row in read(path / "data/manifest.json")["rows"]:
            symbol = upstream_c.public_name(row["api_symbol"])
            g.require(linked.symbol_data(row["api_symbol"]) == public.symbol_data(symbol),
                      "ordinary C leaf differs from current matrix object")
            rows.append(dict(image=image["name"],symbol=symbol))
    g.require(seen == expected and len(rows) == 48 and len(manifest["rows"]) == 16,
              "incomplete C matrix anchor")
    return dict(status="CURRENT_FIRSTDOT_48_LEAF_ANCHORS_PASS", rows=rows,
                matrix_images_sha256=g.sha(matrix / "images.json"))

def run(repo, identity_path, builds, output, operation_id, negative, replay):
    initial = parent_identity(repo, identity_path)
    cfg = initial["configuration"]
    outside_inputs(output, [repo, identity_path.parent, *builds, cfg["hardware_source"], cfg["build_record"], cfg["am_home"]])
    identity, hardware_files, profile = parent_identity(repo, identity_path, physical=True)
    cfg = identity["configuration"]
    f, m = runtime(repo, identity)
    output.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status="PREFLIGHT", operation_id=operation_id, started=f.now(),
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
        files.update(adapter_files())
        files[str(identity_path)] = g.sha(identity_path)
        images = []
        for b in builds:
            g.require(read(b / "state.json")["status"] == BUILD_PASS, "incomplete firstdot build")
            for file in ("state.json", "images.json", "pairs.json", "combination-build.json"):
                files[str(b / file)] = g.sha(b / file)
            built_images = read(b / "images.json")["images"]
            verify_build_scope(repo, b, built_images, identity_path)
            for image in built_images:
                validate_image(image, b)
                p = Path(image["path"])
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
        g.require(originals == {i["name"] for i in images} and state["new_emu_runs"] == len(records) + int(negative),
                  "firstdot launch cardinality")
        coverage = qualification(images, records, bool(negative and rejected), replay)
        qualified = coverage["negative_and_recovery"] and coverage["all_window_replay"]
        state["status"] = RUN_PASS if qualified else "FIRSTDOT_PARTIAL_PASS"
        result = dict(status=state["status"], contract=CONTRACT, parent_identity_sha256=g.sha(identity_path),
            hardware_source_commit=identity["source_commit"], emu_sha256=profile["emu_sha256"],
            historical_pass_reused=False, runs=records, negative=rejected, qualification=coverage, **summary)
        g.save(output / "results.json", result)
        return result
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = f.now()
        persist()




def matrix_qualification(identity_path, matrix, matrix_run):
    state, result = read(matrix_run / "state.json"), read(matrix_run / "results.json")
    g.require(state["status"] == result["status"] == RUN_PASS and state["new_emu_runs"] == 33,
              "current matrix did not complete all 33 runs")
    g.require(state["contract"] == result["contract"] == CONTRACT, "matrix outer contract differs")
    q = result["qualification"]
    g.require(all(q[k] for k in ("negative_and_recovery","all_window_replay","full_matrix")) and
              q["historical_pass_reused"] is False and result["historical_pass_reused"] is False,
              "matrix lacks independent current qualification")
    g.require(result["parent_identity_sha256"] == g.sha(identity_path), "matrix hardware identity differs")
    images = read(matrix / "images.json")["images"]
    verify_build_scope(ROOT, matrix, images, identity_path)
    expected = {i["name"]:i["image_sha256"] for i in images}
    normal = [r for r in result["runs"] if r["replay"] == 0]
    g.require(len(expected) == len(normal) == 24 and
              {r["name"]:r["image_sha256"] for r in normal} == expected,
              "C anchor matrix differs from executed images")
    m = g.load("current_matrix_status", ROOT / g.REL / "merged_screen.py")
    g.require(result["measured_windows"] == 384 and
              all(r["status"] == m.NORMAL_PASS for r in normal),
              "matrix runtime/window inventory incomplete")
    repeats = [r for r in result["runs"] if r["replay"] == 1]
    expected_repeats = {i["name"] for i in images if i["dataset"] == 0}
    g.require(len(result["runs"]) == 32 and len(repeats) == len(expected_repeats) == 8
              and {r["name"] for r in repeats} == expected_repeats
              and all(r["status"] == m.NORMAL_PASS for r in repeats), "incomplete or duplicate matrix replay")
    by = {r["name"]:r for r in normal}
    selected = {i["name"]:i for i in images}
    for record in result["runs"]:
        image = selected[record["name"]]
        g.require(all(record[k] == image[k] for k in ("suite","shard","dataset","variant","name","image_sha256","path")),
                  "runtime image selection differs")
    for repeated in repeats:
        g.require(repeated["dataset"] == 0, "replay dataset differs")
        g.require(m.signature(repeated) == m.signature(by[repeated["name"]]), "matrix replay differs")
    rejected = result["negative"]
    g.require(rejected["status"] == m.NEGATIVE_PASS and rejected["negative"] is True
              and rejected["negative_details"]["vd"] == 0 and rejected["negative_details"]["bit"] == 100
              and rejected["negative_details"]["word"] == "0x0388000b", "matrix negative incomplete")
    m.validate_recovery(rejected, by[rejected["name"]])
    summary = summarize(result["runs"])
    g.require(all(result[k] == v for k,v in summary.items()), "matrix summary differs from complete records")
    return dict(results_sha256=g.sha(matrix_run / "results.json"),
                state_sha256=g.sha(matrix_run / "state.json"), images_sha256=g.sha(matrix / "images.json"),
                parent_identity_sha256=g.sha(identity_path), path=str(matrix_run))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--action", choices=("build","run","build-c","run-c","audit-c"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--build", type=Path)
    p.add_argument("--matrix", type=Path)
    p.add_argument("--matrix-run", type=Path)
    p.add_argument("--run", type=Path)
    p.add_argument("--shards", nargs="+", type=int, default=[1,3,5,7])
    p.add_argument("--datasets", nargs="+", type=int, default=[0,1,2])
    p.add_argument("--operation-id", default="20261026-cc77-builder-firstdot-combination")
    args = p.parse_args()
    if os.name == "posix": os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    repo, identity_path, output = ROOT, args.identity.resolve(), args.output.resolve()
    verify_imports()
    g.require(not output.exists(), "fresh output required; preserve prior attempts")
    if args.action == "build":
        result = build(repo, identity_path, output, args.shards, args.datasets)
    elif args.action == "run":
        g.require(args.build, "matrix build required")
        result = run(repo, identity_path, [args.build.resolve()], output, args.operation_id, True, True)
    else:
        identity = parent_identity(repo, identity_path)
        base = c_adapter(repo, identity)
        cfg = identity["configuration"]
        outside_inputs(output, [repo, identity_path.parent, cfg["hardware_source"], cfg["build_record"], cfg["am_home"],
                               *[x.resolve() for x in (args.build,args.matrix,args.matrix_run,args.run) if x]])
        if args.action == "build-c":
            g.require(args.matrix, "matrix required")
            result = base.build(repo, cfg, output)
            g.save(output / "combination-c-build.json", dict(contract=CONTRACT, adapter_files=adapter_files()))
            g.save(output / "matrix-anchor.json", library_anchor(repo, output, args.matrix.resolve()))
        elif args.action == "run-c":
            g.require(args.build and args.matrix and args.matrix_run, "C and qualified matrix required")
            matrix_proof = matrix_qualification(identity_path, args.matrix.resolve(), args.matrix_run.resolve())
            anchor = library_anchor(repo, args.build.resolve(), args.matrix.resolve())
            g.require(anchor == read(args.build / "matrix-anchor.json"), "C matrix anchor drift")
            g.require(read(args.build / "combination-c-build.json")["adapter_files"] == adapter_files(), "C adapter drift")
            result = base.run(repo,cfg,args.build.resolve(),output,args.operation_id+"-c")
            g.save(output / "combination-c-qualification.json", dict(contract=CONTRACT, matrix_proof=matrix_proof,
                hardware_identity_sha256=g.sha(identity_path), historical_pass_reused=False,
                public_functions=16, distinct_cases=48, normal_case_executions=96, new_emu_runs=3,
                status="CURRENT_FIRSTDOT_C_APPLICATION_PASS"))
        else:
            g.require(args.build and args.run and args.matrix and args.matrix_run, "C build/run and matrix proof required")
            matrix_proof = matrix_qualification(identity_path,args.matrix.resolve(),args.matrix_run.resolve())
            g.require(read(args.run / "combination-c-qualification.json")["matrix_proof"] == matrix_proof, "C matrix proof drift")
            g.require(library_anchor(repo,args.build.resolve(),args.matrix.resolve()) ==
                      read(args.build / "matrix-anchor.json"), "C matrix anchor drift")
            result = base.audit_run(repo,args.build.resolve(),args.run.resolve())
            g.save(output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ("runs","samples","rows","functions")},indent=2))

if __name__ == "__main__":
    main()
