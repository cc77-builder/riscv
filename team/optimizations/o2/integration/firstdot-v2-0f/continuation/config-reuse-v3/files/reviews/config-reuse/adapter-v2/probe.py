"""Draft, separately bound 8x32/d0 config-reuse probe; no default or RTL changes.

Install only after review and current-combination + clean qualification.
Old upstream generators/contracts/locks remain byte-identical.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

CONTRACT = "zjhwork-clean-config-reuse-8x32-d0-probe-v2"
CLEAN_CONTRACT = "zjhwork-0f-firstdot-v2-clean-identity-v1"
UPSTREAM = "fcf4a11fc569cb2a8fcb4e18d96ec2764b228557"
BUILD_PASS = "CURRENT_CONFIG_REUSE_PROBE_STATIC_PASS"
HERE = Path(__file__).resolve().parent
S3 = Path("team/optimizations/o2/r2-config-reuse")
COMBO = Path("team/optimizations/o2/integration/firstdot-v2-0f")
VARIANTS = ("firstdot", "config-reuse")


def require(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def load(label, path):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def imports(repo):
    value = read(HERE / "import-manifest.json")
    require(value["upstream_ref"] == UPSTREAM, "upstream identity")
    files, seen = {}, set()
    for row in value["files"] + value["already_present_dependencies"]:
        rel = Path(row["path"])
        require(not rel.is_absolute() and ".." not in rel.parts and row["path"] not in seen,
                "unsafe or duplicate imported source")
        seen.add(row["path"])
        target = repo / rel
        require(target.is_file() and not target.is_symlink() and target.stat().st_size == row["bytes"]
                and sha(target) == row["sha256"], "source drift: " + str(rel))
        files[str(target)] = row["sha256"]
    require(len(value["files"]) == 26 and len(value["already_present_dependencies"]) == 39,
            "source closure inventory")
    for name in ("probe.py", "raw_audit.py", "CONTRACT.md", "import-manifest.json"):
        files[str(HERE / name)] = sha(HERE / name)
    return files


def assess(rows, controls, replay_equal):
    """Pure decision; four measured samples are descriptive, not significance."""
    require(type(replay_equal) is bool and isinstance(controls, list)
            and all(isinstance(v, str) for v in controls), "decision control types")
    require(len(rows) == 8, "expected eight variant/software/method cells")
    indexed = {(r["variant"], r["software"], r["method"]): r for r in rows}
    expected = {(v, sw, m) for v in VARIANTS for sw in ("basic", "reuse") for m in ("vdot", "rvv")}
    require(len(indexed) == 8 and set(indexed) == expected, "cell inventory")
    require(all(type(r["total"]) is int and r["total"] > 0 and r["samples"] == 4 for r in rows),
            "four positive measured samples required")
    candidate = indexed[("config-reuse", "reuse", "vdot")]["total"]
    baseline = indexed[("firstdot", "reuse", "vdot")]["total"]
    rvv = min(r["total"] for r in rows if r["method"] == "rvv")
    issues = list(controls)
    for sw in ("basic", "reuse"):
        for method in ("vdot", "rvv"):
            left = indexed[("firstdot", sw, method)]["total"]
            right = indexed[("config-reuse", sw, method)]["total"]
            # A failed main candidate is REJECT, but an independent regression
            # in any other paired cell is unexplained whether it wins or loses.
            if (sw, method) != ("reuse", "vdot") and right > left:
                issues.append("unexplained paired cell regression: " + sw + "/" + method)
    if not replay_equal:
        issues.append("independent full-24-window replay differs")
    decision = "INCONCLUSIVE" if issues else (
        "PERFORMANCE_CANDIDATE" if candidate < min(baseline, rvv) else "REJECT")
    return dict(decision=decision, candidate_total=candidate, firstdot_total=baseline,
                fastest_current_rvv_total=rvv, reduction_vs_firstdot=1-candidate/baseline,
                reduction_vs_fastest_rvv=1-candidate/rvv, unexplained_controls=issues,
                threshold="strictly_less_than_both_totals; no percentage threshold",
                scope="8x32/dataset0 only; eligible for a separate expansion decision",
                default_changed=False, full_matrix_qualified=False)


class Probe:
    def __init__(self, repo, identity, matrix, matrix_run):
        self.repo = Path(repo).resolve()
        self.identity_path, self.matrix, self.matrix_run = [
            Path(p).resolve() for p in (identity, matrix, matrix_run)]
        # Single-purpose fresh process. Distinct private outer modules; upstream's
        # unmodified imports retain their required canonical module instances.
        sys.path.insert(0, str(self.repo / COMBO))
        self.combo = load("current_firstdot_precondition", self.repo / COMBO / "combination.py")
        sys.path.insert(0, str(self.repo / S3))
        self.a = load("current_s3_probe_upstream", self.repo / S3 / "runtime_experiment.py")
        self.g = self.a.g
        require(Path(self.g.__file__).resolve() == self.repo / S3 / "runtime_gate.py"
                and Path(self.a.c.__file__).resolve() == self.repo / S3 / "runtime_candidate.py",
                "canonical module name collision")
        self.g.bind(self.repo)
        require(self.combo.ROOT == self.repo and self.a.ROOT == self.repo, "module root")
        self.identity = read(self.identity_path)
        require(self.identity["contract"] == CLEAN_CONTRACT, "requires current clean identity")
        self.hw = self.combo.hardware_module(self.identity)
        self.hw.validate_identity(self.repo, self.identity_path)
        self.precondition = self.combo.matrix_qualification(
            self.identity_path, self.matrix, self.matrix_run)
        self.fixed = imports(self.repo) | self.combo.adapter_files() | self.hw.adapters()
        self.baseline_images = read(self.matrix / "images.json")["images"]
        self.baseline_records = read(self.matrix_run / "results.json")["runs"]
        # matrix_qualification checks typed inventory and all 33 actual results.
        # Re-run unchanged GNU gates for all baseline objects before using them.
        for image in self.baseline_images:
            self.combo.g.verify_build(Path(image["path"]), self.repo)
        for path in (self.identity_path, self.matrix / "images.json",
                     self.matrix / "combination-build.json", self.matrix / "state.json",
                     self.matrix_run / "state.json", self.matrix_run / "results.json"):
            self.fixed[str(path)] = sha(path)

    def physical(self):
        return self.hw.validate_identity(self.repo, self.identity_path, physical=True)

    def external(self, output, extra=()):
        cfg = self.identity["configuration"]
        roots = [self.repo, self.identity_path.parent, self.matrix, self.matrix_run,
                 HERE, cfg["hardware_source"], cfg["build_record"], cfg["am_home"], *extra]
        self.a.outside_inputs(Path(output).resolve(), roots)
        require(not Path(output).exists(), "new external output required")

    def anchor(self, image):
        path = Path(image["path"])
        baseline = next(i for i in self.baseline_images if
                        (i["variant"], i["shard"], i["dataset"]) == ("firstdot", 3, 0))
        s1 = next(i for i in self.baseline_images if
                  (i["variant"], i["shard"], i["dataset"]) == ("s1", 3, 0))
        source, s1_path = Path(baseline["path"]), Path(s1["path"])
        self.combo.g.verify_build(source, self.repo)
        self.combo.g.verify_build(s1_path, self.repo)
        receipts = [read(p / "build.json") for p in (path, source)]
        for key in ("am_revision", "external_files", "toolchain"):
            require(receipts[0][key] == receipts[1][key], "current baseline build input differs: " + key)
        artifacts = {}
        # ELF bytes can carry provenance/symbol differences. Compare all ALLOC
        # sections plus exact BIN and independent authoritative machine objects.
        elves = [self.g.ELF((p / "vdot-perf.elf").read_bytes()) for p in (path, source)]
        def allocation(elf):
            return {name: dict(kind=sec[1], flags=sec[2], address=sec[3], size=sec[5],
                               align=sec[8], data=elf.section(sec) if sec[1] != 8 else None)
                    for name,sec in elf.named.items() if sec[2] & 2}
        require(elves[0].entry == elves[1].entry and allocation(elves[0]) == allocation(elves[1]),
                "current baseline complete ELF allocation differs")
        left = read(path / "data/manifest.json")
        right = read(source / "data/manifest.json")
        require(len(left["rows"]) == len(right["rows"]) == 4 and left["plan"] == right["plan"] and left["dataset"] == right["dataset"] == 0
                and left["shard"] == right["shard"] == 3, "baseline plan/selection")
        for filename in ("vdot-perf.bin", "kernels-reference.o", "gemv-reference.o",
                         "data/cases.h", "data/gemv.h", "data/kernels.S", "data/gemv.S"):
            require((path / filename).read_bytes() == (source / filename).read_bytes(),
                    "current baseline payload differs: " + filename)
            artifacts[filename] = sha(source / filename)
            self.fixed[str(source / filename)] = artifacts[filename]
        for lrow, rrow in zip(left["rows"], right["rows"]):
            require(all(lrow[k] == rrow[k] for k in
                        ("m", "k", "software", "method", "api_symbol")), "baseline row identity")
            symbol = lrow["api_symbol"]
            require(elves[0].symbols[symbol] == elves[1].symbols[symbol] and
                    elves[0].symbol_data(symbol) == elves[1].symbol_data(symbol), "baseline ELF leaf")
        # Same S1 algorithms in whole 8-KiB RVV slots; historical cycles unused.
        rb, sb = (source / "vdot-perf.bin").read_bytes(), (s1_path / "vdot-perf.bin").read_bytes()
        rvv = []
        for n, row in enumerate(right["rows"]):
            if row["method"] == "rvv":
                lo, hi = 8192*(n+1), 8192*(n+2)
                require(len(rb[lo:hi]) == 8192 and rb[lo:hi] == sb[lo:hi], "current S1 RVV slot")
                rvv.append(row["api_symbol"])
        require(len(rvv) == 2, "both current S1 RVV slots")
        return dict(baseline_image=baseline["name"], baseline_path=baseline["path"],
                    same_payload=artifacts, rvv_slots=rvv, qualified_current=self.precondition,
                    historical_pass_reused=False)

    def build(self, output):
        output = Path(output).resolve()
        self.external(output)
        before = self.physical()
        cfg = self.identity["configuration"]
        builder = self.a.builder(self.repo)
        builder.frozen_f.pinned_modules(self.repo)
        am = Path(cfg["am_home"])
        require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=am, text=True).strip()
                == builder.frozen_f.AM_COMMIT, "AM revision")
        require(not subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"],
                                            cwd=am, text=True).strip(), "modified official AM")
        tools = {k: shutil.which(cfg["cross_prefix"] + k) for k in
                 ("gcc", "ld", "ar", "objcopy", "objdump", "readelf")}
        tools["make"] = shutil.which("make")
        require(all(tools.values()), "toolchain")
        output.mkdir(parents=True)
        state = dict(contract=CONTRACT, status="BUILDING", new_emu_runs=0, images_completed=0)
        save(output / "state.json", state)
        try:
            images = []
            for item in self.a.inventory([3], [0]):
                images.append(builder.build_one(self.repo, cfg, output / "images" / self.a.name(item), item, tools))
                state["images_completed"] = len(images)
                save(output / "state.json", state)
            save(output / "images.json", dict(images=images))
            save(output / "pairs.json", self.a.pairs(images, self.repo))
            anchor = self.anchor(next(i for i in images if i["variant"] == "firstdot"))
            save(output / "baseline-current.json", anchor)
            require(self.physical() == before, "clean build identity changed")
            self.a.runtime(self.repo, self.identity)[1].verify_files(self.fixed)
            save(output / "probe-build.json", dict(contract=CONTRACT, parent_identity_sha256=sha(self.identity_path),
                images={i["name"]:i["image_sha256"] for i in images}, sources=self.fixed,
                current_precondition=self.precondition))
            state["status"] = BUILD_PASS
        except BaseException as exc:
            state.update(status="FAILED", error=repr(exc))
            raise
        finally:
            save(output / "state.json", state)

    def selected(self, build):
        value = read(build / "probe-build.json")
        images = read(build / "images.json")["images"]
        require(read(build / "state.json")["status"] == BUILD_PASS and value["contract"] == CONTRACT,
                "incomplete or wrong probe build")
        require(value["parent_identity_sha256"] == sha(self.identity_path)
                and value["current_precondition"] == self.precondition, "build/precondition identity")
        expected = self.a.inventory([3], [0])
        require(len(images) == 2 and {(i["suite"], i["shard"], i["dataset"], i["variant"]) for i in images}
                == {(i["suite"], i["shard"], i["dataset"], i["variant"]) for i in expected}, "probe pair inventory")
        for image in images:
            self.a.validate_image(image, build)
            self.g.verify_build(Path(image["path"]), self.repo)
            require(sha(Path(image["path"]) / "vdot-perf.bin") == image["image_sha256"], "image digest")
        require(value["images"] == {i["name"]:i["image_sha256"] for i in images}, "build image identity")
        self.a.pairs(images, self.repo)
        anchor = self.anchor(next(i for i in images if i["variant"] == "firstdot"))
        require(anchor == read(build / "baseline-current.json"), "current baseline receipt drift")
        require(value["sources"] == self.fixed, "probe source inventory drift")
        return images

    def runtime(self):
        f, m = self.a.runtime(self.repo, self.identity)
        m.SOURCE = self.identity["source_commit"]
        m.EMU = self.identity["hardware_profile"]["emu_sha256"]
        m.META = dict(self.identity["metadata_sha256"])
        m.CONTRACT = CONTRACT
        def profile(repo, cfg):
            require(cfg == self.identity["configuration"], "runtime configuration drift")
            identity, files, value = self.physical()
            require(identity == self.identity, "runtime identity drift")
            return files, value
        m.hardware_profile = profile
        original = m.checker_files
        m.checker_files = lambda root: original(root) | self.fixed
        return f, m

    def evaluate(self, records, images, m):
        first = next(i for i in images if i["variant"] == "firstdot")
        candidate = next(i for i in images if i["variant"] == "config-reuse")
        require(len(records) == 4, "four ordered normal records")
        require([(r["variant"], r["replay"]) for r in records] ==
                [("config-reuse",0),("firstdot",0),("firstdot",1),("config-reuse",1)],
                "normal/replay order")
        replay_equal = all(m.signature(records[i]) == m.signature(records[j]) for i,j in ((0,3),(1,2)))
        summary = self.a.summarize(records)
        require(summary["measured_windows"] == 32 and len(summary["rows"]) == 1, "probe statistics scope")
        controls = []
        baseline = next(r for r in self.baseline_records if
                        (r["variant"],r["shard"],r["dataset"],r["replay"]) == ("firstdot",3,0,0))
        if m.signature(baseline) != m.signature(records[1]):
            controls.append("identical current qualified firstdot BIN changed full-window signature")
        manifests = [read(Path(i["path"]) / "data/manifest.json") for i in (first,candidate)]
        for left, right in zip(manifests[0]["rows"], manifests[1]["rows"]):
            if left["method"] == "rvv" and not right["config_reuse_proof"]["removed"]:
                sw = left["software"]
                signatures = [[(s["seq"],s["cycles"],s["instructions"]) for s in r["samples"]
                               if s["method"]=="rvv" and s["software"]==sw] for r in (records[1], records[0])]
                require(all(len(s)==6 for s in signatures), "unchanged RVV control windows")
                if signatures[0] != signatures[1]:
                    controls.append("unchanged " + sw + " RVV six-window signature differs")
        decision = assess(summary["rows"][0]["candidates"], controls, replay_equal)
        return summary, decision, replay_equal

    def run(self, build, output, operation):
        build, output = Path(build).resolve(), Path(output).resolve()
        self.external(output, [build])
        images = self.selected(build)
        before = self.physical()
        cfg = self.identity["configuration"]
        f, m = self.runtime()
        require(1 <= len(os.sched_getaffinity(0)) <= 4, "run with <=4 CPU affinity")
        files = before[1] | m.checker_files(self.repo)
        for filename in ("probe-build.json", "state.json", "images.json", "pairs.json", "baseline-current.json"):
            files[str(build / filename)] = sha(build / filename)
        for image in images:
            for filename in ("build.json", "data/manifest.json"):
                files[str(Path(image["path"]) / filename)] = sha(Path(image["path"]) / filename)
        output.mkdir(parents=True)
        state = dict(contract=CONTRACT, status="PREFLIGHT", new_emu_runs=0, active_pid=None,
                     operation_id=operation, started=f.now(), hardware_changed=False, default_changed=False)
        save(output / "state.json", state)
        save(output / "runtime-inputs.json", files)
        save(output / "configuration.json", cfg)
        save(output / "hardware-profile.json", before[2])
        shutil.copyfile(self.identity_path, output / "parent-identity.json")
        records = []
        def launch(image, label, fixture=None, replay=0):
            previous = state["new_emu_runs"]
            def progress(receipt):
                state.update(new_emu_runs=previous + int(receipt.get("process_started") is True),
                             active_pid=receipt.get("pid") if "finished" not in receipt else None)
                save(output / "state.json", state)
            record = m.execute(self.repo, cfg, image, output / "runs" / label, files, fixture, replay, progress)
            require(all(record[k] == image[k] for k in
                        ("name", "suite", "shard", "dataset", "variant", "image_sha256", "path")), "run image identity")
            return record
        try:
            first = next(i for i in images if i["variant"] == "firstdot")
            candidate = next(i for i in images if i["variant"] == "config-reuse")
            fixture = m.build_negative(self.repo, cfg, output / "negative-fixture")
            rejected = launch(candidate, "negative-config-reuse", fixture)
            detail = rejected["negative_details"]
            require(int(detail["pc"], 16) == self.a.negative_target(candidate)
                    and detail["vd"] == 0 and detail["word"] == "0x0388000b" and detail["bit"] == 100,
                    "negative actual first vdot destination")
            recovery = launch(candidate, "recovery-config-reuse")
            m.validate_recovery(rejected, recovery)
            records.append(recovery)
            save(output / "completed-runs.json", records)
            records.append(launch(first, "formal-firstdot"))
            save(output / "completed-runs.json", records)
            # Reverse order of the normal pair: candidate->firstdot,
            # followed by firstdot->candidate; fresh PID each time.
            for image in (first, candidate):
                records.append(launch(image, "replay-" + image["variant"], replay=1))
                save(output / "completed-runs.json", records)
            require(state["new_emu_runs"] == 5 and len(records) == 4 and
                    all(len(r["samples"]) == 24 for r in records), "exact five-process/all-window inventory")
            replay_equal = all(m.signature(records[i]) == m.signature(records[j]) for i,j in ((0,3),(1,2)))
            self.g.verify_build(Path(first["path"]), self.repo)
            self.g.verify_build(Path(candidate["path"]), self.repo)
            self.a.pairs(images, self.repo)
            require(self.selected(build) == images, "probe inputs changed during execution")
            require(self.physical() == before, "clean runtime identity drift")
            m.verify_files(files)
            summary, decision, replay_equal = self.evaluate(records, images, m)
            state.update(status=decision["decision"], functional_status="FUNCTIONAL_PASS",
                         all_window_replay=replay_equal)
            result = dict(contract=CONTRACT, status=state["status"], functional_status="FUNCTIONAL_PASS",
                parent_identity_sha256=sha(self.identity_path), current_precondition=self.precondition,
                runs=records, negative=rejected, **summary, performance=decision,
                default_changed=False, historical_pass_reused=False, new_emu_runs=5)
            save(output / "results.json", result)
            return result
        except BaseException as exc:
            state.update(status="FAILED", error=repr(exc))
            raise
        finally:
            state["finished"] = f.now()
            save(output / "state.json", state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("repo", "identity", "matrix", "matrix-run", "output"):
        parser.add_argument("--" + flag, required=True, type=Path)
    parser.add_argument("--action", required=True, choices=("build", "run", "audit"))
    parser.add_argument("--build", type=Path)
    parser.add_argument("--campaign", type=Path)
    parser.add_argument("--operation-id", default="current-clean-config-reuse-probe")
    args = parser.parse_args()
    p = Probe(args.repo, args.identity, args.matrix, args.matrix_run)
    if args.action == "build":
        p.build(args.output)
    elif args.action == "run":
        require(args.build is not None, "--build required for run")
        print(json.dumps(p.run(args.build, args.output, args.operation_id), indent=2))
    else:
        require(args.build is not None and args.campaign is not None, "--build and --campaign required for audit")
        import raw_audit
        p.external(args.output, [args.build, args.campaign])
        value = raw_audit.audit_probe(p, args.build, args.campaign)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
        print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
