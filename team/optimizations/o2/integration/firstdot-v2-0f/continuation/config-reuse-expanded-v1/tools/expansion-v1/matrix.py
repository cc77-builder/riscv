"""Current clean-hardware configuration reuse: fixed 4-shape x 3-dataset matrix.

Frozen generators and semantic gates are reused unchanged. Output directories
must be new; this controller never resumes a partial campaign or changes RTL.
"""
from __future__ import annotations
import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
BASE_DIR = HERE.parent / "adapter-v3"
CONTRACT = "zjhwork-clean-config-reuse-4shape-3dataset-matrix-v1"
BUILD_PASS = "CURRENT_CONFIG_REUSE_MATRIX_STATIC_PASS"
RUN_PASS = "CURRENT_CONFIG_REUSE_MATRIX_SCREEN_COMPLETE"
SHARDS = (1, 3, 5, 7)
DATASETS = (0, 1, 2)
VARIANTS = ("firstdot", "config-reuse")
SHAPES = {1: (4, 8), 3: (8, 32), 5: (16, 64), 7: (4, 13)}
NEGATIVE_PASS = "EXPECTED_VDOT_HIGHBIT_REJECTION"
NORMAL_PASS = "R2_DIFFTEST_WINDOWS_AND_O2_PROTOCOL_PASS"
BASE_PINS = {
    "probe.py": "5c29a1a681e77c13e7342197993d4cc73e4f47b6457a3ea9efff972ee2c01cda",
    "raw_audit.py": "f21e9d8c76f18ed51739c2c9a3843ee913879f1276e461c612df84d30d51d599",
    "CONTRACT.md": "d81a745de39e96d648095e6db9861ede4e129560097ff1673006601fcb91fd13",
    "import-manifest.json": "f39b073c554fe063d727cc2229967420cd523d5316edcd2fc6cc2083664a7590",
}


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


def validate_base():
    for name, digest in BASE_PINS.items():
        path = BASE_DIR / name
        require(path.is_file() and not path.is_symlink() and sha(path) == digest,
                "frozen probe source changed: " + name)


validate_base()
base = load("matrix_frozen_probe", BASE_DIR / "probe.py")
require(base.CONTRACT == "zjhwork-clean-config-reuse-8x32-d0-probe-v3", "base contract")


def inventory():
    return [dict(suite="performance", shard=s, dataset=d, variant=v)
            for s in SHARDS for d in DATASETS for v in VARIANTS]


def item_key(item):
    require(item["suite"] == "performance" and type(item["shard"]) is int
            and type(item["dataset"]) is int and item["shard"] in SHARDS
            and item["dataset"] in DATASETS and item["variant"] in VARIANTS,
            "matrix selection identity")
    return item["shard"], item["dataset"], item["variant"]


def image_name(item):
    item_key(item)
    return f"performance-{item['variant']}-d{item['dataset']}-s{item['shard']:02d}"


def validated_images(images):
    require(isinstance(images, list) and len(images) == 24, "exactly 24 matrix images")
    by = {}
    for image in images:
        key = item_key(image)
        require(key not in by and image["name"] == image_name(image), "duplicate/noncanonical image")
        by[key] = image
    require(set(by) == {item_key(i) for i in inventory()}, "complete 4x3x2 matrix inventory")
    return by


def run_specs(images):
    """Exact canonical 33-process schedule; output order is independent of finish order."""
    by = validated_images(images)
    selected = by[(3, 0, "config-reuse")]
    specs = [
        dict(label="negative-config-reuse-8x32-d0", image=selected, replay=0,
             negative=True, phase="negative"),
        dict(label="recovery-config-reuse-8x32-d0", image=selected, replay=0,
             negative=False, phase="recovery"),
    ]
    ordered = sorted(images, key=lambda i: (i["shard"], i["dataset"],
                     VARIANTS.index(i["variant"]) ^ ((i["shard"] + i["dataset"]) % 2)))
    for image in ordered:
        if item_key(image) != (3, 0, "config-reuse"):
            specs.append(dict(label="formal-" + image["name"], image=image, replay=0,
                              negative=False, phase="formal"))
    for image in sorted(images, key=lambda i: (i["shard"], -VARIANTS.index(i["variant"]))):
        if image["dataset"] == 0:
            specs.append(dict(label="replay-" + image["name"], image=image, replay=1,
                              negative=False, phase="replay"))
    require(len(specs) == 33 and len({s["label"] for s in specs}) == 33, "schedule cardinality")
    return specs


def process_inputs(common, comparison_bins):
    """Remove only exact comparison BIN roles, retaining/checking the complete outer map."""
    expected = {str(p) for p in comparison_bins}
    require(len(expected) == 12, "exactly twelve comparison BINs required")
    actual = {p for p in common if p.endswith("/vdot-perf.bin")}
    require(actual == expected, "comparison BIN role inventory differs")
    for path in expected:
        p = Path(path)
        require(p.is_file() and not p.is_symlink() and sha(p) == common[path],
                "comparison BIN changed: " + path)
    return {p: digest for p, digest in common.items() if p not in expected}


def assess(rows, controls, replay_equal, samples_per_cell=12):
    require(type(samples_per_cell) is int and samples_per_cell in (4, 12),
            "supported sample cardinality")
    require(type(replay_equal) is bool and isinstance(controls, list)
            and all(isinstance(v, str) for v in controls), "decision control types")
    require(isinstance(rows, list) and len(rows) == 8, "eight decision cells required")
    indexed = {(r["variant"], r["software"], r["method"]): r for r in rows}
    expected = {(v, sw, method) for v in VARIANTS for sw in ("basic", "reuse")
                for method in ("vdot", "rvv")}
    require(len(indexed) == 8 and set(indexed) == expected, "decision cell inventory")
    require(all(type(r["total"]) is int and r["total"] > 0
                and type(r["samples"]) is int and r["samples"] == samples_per_cell
                for r in rows), "positive typed totals and exact samples")
    candidate = indexed[("config-reuse", "reuse", "vdot")]["total"]
    baseline = indexed[("firstdot", "reuse", "vdot")]["total"]
    rvv = min(r["total"] for r in rows if r["method"] == "rvv")
    issues = list(controls)
    for sw in ("basic", "reuse"):
        for method in ("vdot", "rvv"):
            if (sw, method) != ("reuse", "vdot") and (
                    indexed[("config-reuse", sw, method)]["total"] >
                    indexed[("firstdot", sw, method)]["total"]):
                issues.append("unexplained paired cell regression: " + sw + "/" + method)
    if not replay_equal:
        issues.append("independent full-24-window replay differs")
    decision = "INCONCLUSIVE" if issues else (
        "PERFORMANCE_CANDIDATE" if candidate < min(baseline, rvv) else "REJECT")
    return dict(decision=decision, candidate_total=candidate, firstdot_total=baseline,
                fastest_current_rvv_total=rvv, reduction_vs_firstdot=1-candidate/baseline,
                reduction_vs_fastest_rvv=1-candidate/rvv, unexplained_controls=issues,
                samples_per_cell=samples_per_cell, default_changed=False)


def decide_shape(aggregate_rows, dataset_rows, controls, replay_equal):
    require(isinstance(dataset_rows, dict) and set(dataset_rows) == set(DATASETS)
            and all(type(k) is int for k in dataset_rows), "three typed datasets required")
    per_dataset = {d: assess(dataset_rows[d], [], replay_equal, 4) for d in DATASETS}
    aggregate = assess(aggregate_rows, controls, replay_equal, 12)
    # Every reported total must correspond to the three independently assessed datasets.
    for row in aggregate_rows:
        key = (row["variant"], row["software"], row["method"])
        total = sum(next(x["total"] for x in dataset_rows[d]
                         if (x["variant"], x["software"], x["method"]) == key) for d in DATASETS)
        require(total == row["total"], "aggregate does not equal three dataset totals")
    issues = list(aggregate["unexplained_controls"])
    for d, detail in per_dataset.items():
        issues += [f"dataset{d}: " + s for s in detail["unexplained_controls"]]
    decision = "INCONCLUSIVE" if issues else (
        "PERFORMANCE_CANDIDATE" if aggregate["decision"] == "PERFORMANCE_CANDIDATE"
        and all(v["decision"] == "PERFORMANCE_CANDIDATE" for v in per_dataset.values()) else "REJECT")
    return dict(aggregate, decision=decision, dataset_decisions={str(d): v for d, v in per_dataset.items()},
                unexplained_controls=issues,
                threshold="strictly below both baselines in aggregate AND each dataset; no percentage threshold",
                measurement_scope="one shape across three datasets", ordinary_public_C_application="NOT_TESTED",
                stable_default_changed=False)

def validate_timing(records, workers, boot_id, bounds=None):
    require(type(workers) is int and 1 <= workers <= 4, "workers must be integer 1..4")
    require(isinstance(boot_id, str) and bool(boot_id), "nonempty boot identity")
    require(isinstance(records, list) and bool(records), "nonempty process records")
    if bounds is not None:
        require(len(bounds) == 2 and all(type(x) is int for x in bounds)
                and 0 <= bounds[0] < bounds[1], "typed campaign monotonic bounds")
    pids, events = set(), []
    for record in records:
        timing = record.get("monotonic", {})
        pid = record.get("pid")
        require(record.get("process_started") is True, "timing requires an actual started process")
        start, end = timing.get("start_ns"), timing.get("end_ns")
        require(type(pid) is int and pid > 0 and pid not in pids
                and type(timing.get("pid")) is int and timing["pid"] == pid,
                "positive unique actual PID bound to monotonic envelope")
        require(timing.get("boot_id") == boot_id and timing.get("scope") == "popen_wait_bracket",
                "monotonic clock domain/scope")
        require(type(start) is int and type(end) is int and 0 <= start < end,
                "positive duration typed monotonic envelope")
        if bounds is not None:
            require(bounds[0] <= start < end <= bounds[1], "process outside campaign bounds")
        pids.add(pid)
        events.extend(((start, 1), (end, -1)))
    active = peak = 0
    for _, delta in sorted(events):
        active += delta
        peak = max(peak, active)
        require(0 <= active <= workers, "conservative process envelope exceeds worker budget")
    require(active == 0, "unbalanced process envelopes")
    return dict(boot_id=boot_id, workers=workers, processes=len(records),
                peak_conservative_envelopes=peak, scope="popen_wait_bracket",
                exact_os_scheduling_overlap_claimed=False)


def validate_recovery(negative, normal):
    for record, status, is_negative in ((negative, NEGATIVE_PASS, True), (normal, NORMAL_PASS, False)):
        require(record.get("status") == status and record.get("negative") is is_negative
                and record.get("process_started") is True, "negative/recovery process status")
        require(record.get("contract") == CONTRACT and record.get("mode") == "merged",
                "negative/recovery contract")
        require(type(record.get("replay")) is int and record["replay"] == 0
                and type(record.get("exit_code")) is int, "typed replay/exit code")
        require((record["exit_code"] != 0) if is_negative else (record["exit_code"] == 0),
                "negative/recovery exit code")
    require(all(negative.get(k) == normal.get(k) and k in negative and k in normal for k in
                ("name", "suite", "shard", "dataset", "variant", "image_sha256", "path")),
            "same-BIN typed recovery identity")
    require(item_key(negative) == item_key(normal) == (3, 0, "config-reuse"), "recovery target selection")
    require(normal["name"] == image_name(normal), "recovery canonical image name")
    for key in ("reference", "image_sha256", "path"):
        require(all(isinstance(r.get(key), str) and r[key] for r in (negative, normal)),
                "nonempty recovery identity")
    golden = normal["reference"]
    require(golden != negative["reference"] and
            normal.get("files", {}).get(golden) is not None and
            normal["files"][golden] == negative.get("files", {}).get(golden),
            "golden reference byte binding")
    require(negative.get("environment_overrides") == {"XS_NEGATIVE_VECTOR_TARGET": "vdot"}
            and normal.get("environment_overrides") == {"XS_NEGATIVE_VECTOR_TARGET": None},
            "fault environment cleared during recovery")
    detail = negative.get("negative_details", {})
    require(detail.get("word") == "0x0388000b" and type(detail.get("vd")) is int
            and detail["vd"] == 0 and type(detail.get("bit")) is int and detail["bit"] == 100,
            "actual high-128-bit vdot negative control")
    boot_id = negative.get("monotonic", {}).get("boot_id")
    validate_timing([negative, normal], 1, boot_id)
    require(negative["monotonic"]["end_ns"] <= normal["monotonic"]["start_ns"],
            "normal recovery must begin after negative completion")
    return dict(same_bin=True, golden_reference=True, negative_bit=100, monotonic_serial=True)


def validate_records(records, images):
    expected = [s for s in run_specs(images) if not s["negative"]]
    require(isinstance(records, list) and len(records) == 32, "exact 32 normal/replay records")
    for record, spec in zip(records, expected):
        require(record.get("label") == spec["label"] and record.get("phase") == spec["phase"],
                "canonical record label/phase order")
        require(record.get("status") == NORMAL_PASS and record.get("negative") is False
                and record.get("process_started") is True and type(record.get("exit_code")) is int
                and record["exit_code"] == 0 and type(record.get("replay")) is int
                and record["replay"] == spec["replay"] and record.get("contract") == CONTRACT
                and record.get("mode") == "merged", "successful typed normal record")
        require(all(record.get(k) == spec["image"][k] for k in
                    ("name", "suite", "shard", "dataset", "variant", "image_sha256", "path")),
                "record identity differs from fixed image schedule")
        require(item_key(record) == item_key(spec["image"]), "typed record selection")
        require(isinstance(record.get("samples"), list) and len(record["samples"]) == 24,
                "all 24 normal windows")
    return expected


class Matrix(base.Probe):
    def __init__(self, repo, identity, matrix, matrix_run):
        validate_base()
        super().__init__(repo, identity, matrix, matrix_run)
        for name in ("matrix.py", "raw_audit.py", "CONTRACT.md"):
            path = HERE / name
            require(path.is_file() and not path.is_symlink(), "matrix tool absent: " + name)
            self.fixed[str(path)] = sha(path)

    def external(self, output, extra=()):
        super().external(output, [HERE, *extra])

    def comparison_bins(self):
        bins = {str(Path(i["path"]) / "vdot-perf.bin") for i in self.baseline_images
                if i["variant"] == "firstdot"}
        require(len(bins) == 12, "twelve qualified firstdot comparison BINs")
        return bins

    def anchor(self, image):
        path = Path(image["path"])
        shard, dataset, variant = item_key(image)
        require(variant == "firstdot", "baseline anchor only applies to firstdot")
        baseline = next(i for i in self.baseline_images if
                        (i["variant"], i["shard"], i["dataset"]) == ("firstdot", shard, dataset))
        s1 = next(i for i in self.baseline_images if
                  (i["variant"], i["shard"], i["dataset"]) == ("s1", shard, dataset))
        source, s1_path = Path(baseline["path"]), Path(s1["path"])
        self.combo.g.verify_build(source, self.repo)
        self.combo.g.verify_build(s1_path, self.repo)
        receipts = [read(p / "build.json") for p in (path, source)]
        for key in ("am_revision", "external_files", "toolchain"):
            require(receipts[0][key] == receipts[1][key], "baseline build input differs: " + key)
        elves = [self.g.ELF((p / "vdot-perf.elf").read_bytes()) for p in (path, source)]
        def allocation(elf):
            return {name: dict(kind=sec[1], flags=sec[2], address=sec[3], size=sec[5],
                               align=sec[8], data=elf.section(sec) if sec[1] != 8 else None)
                    for name, sec in elf.named.items() if sec[2] & 2}
        require(elves[0].entry == elves[1].entry and allocation(elves[0]) == allocation(elves[1]),
                "complete current baseline ELF allocation differs")
        left, right = [read(p / "data/manifest.json") for p in (path, source)]
        require(len(left["rows"]) == len(right["rows"]) == 4 and left["plan"] == right["plan"]
                and left["dataset"] == right["dataset"] == dataset
                and left["shard"] == right["shard"] == shard, "baseline plan/selection")
        artifacts = {}
        for filename in ("vdot-perf.bin", "kernels-reference.o", "gemv-reference.o",
                         "data/cases.h", "data/gemv.h", "data/kernels.S", "data/gemv.S"):
            require((path / filename).read_bytes() == (source / filename).read_bytes(),
                    "baseline payload differs: " + filename)
            artifacts[filename] = sha(source / filename)
            self.fixed[str(source / filename)] = artifacts[filename]
        for lrow, rrow in zip(left["rows"], right["rows"]):
            require(all(lrow[k] == rrow[k] for k in ("m", "k", "software", "method", "api_symbol")),
                    "baseline row identity")
            symbol = lrow["api_symbol"]
            require(elves[0].symbols[symbol] == elves[1].symbols[symbol] and
                    elves[0].symbol_data(symbol) == elves[1].symbol_data(symbol), "baseline ELF leaf")
        rb, sb = (source / "vdot-perf.bin").read_bytes(), (s1_path / "vdot-perf.bin").read_bytes()
        rvv = []
        for n, row in enumerate(right["rows"]):
            if row["method"] == "rvv":
                lo, hi = 8192 * (n + 1), 8192 * (n + 2)
                require(len(rb[lo:hi]) == 8192 and rb[lo:hi] == sb[lo:hi], "current S1 RVV slot")
                rvv.append(row["api_symbol"])
        require(len(rvv) == 2, "both current S1 RVV slots")
        return dict(baseline_image=baseline["name"], baseline_path=baseline["path"],
                    same_payload=artifacts, rvv_slots=rvv, qualified_current=self.precondition,
                    historical_pass_reused=False)

    def build(self, output):
        output = Path(output).resolve()
        self.external(output)
        physical_before = self.physical()
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
            for item in inventory():
                images.append(builder.build_one(self.repo, cfg, output / "images" / image_name(item), item, tools))
                state["images_completed"] = len(images)
                save(output / "state.json", state)
            validated_images(images)
            save(output / "images.json", dict(images=images))
            save(output / "pairs.json", self.a.pairs(images, self.repo))
            anchors = [self.anchor(i) for i in images if i["variant"] == "firstdot"]
            save(output / "baseline-current.json", anchors)
            require(self.physical() == physical_before, "clean build identity changed")
            self.runtime()[1].verify_files(self.fixed)
            save(output / "matrix-build.json", dict(contract=CONTRACT,
                parent_identity_sha256=sha(self.identity_path),
                images={i["name"]: i["image_sha256"] for i in images}, sources=self.fixed,
                current_precondition=self.precondition))
            state["status"] = BUILD_PASS
        except BaseException as exc:
            state.update(status="FAILED", error=repr(exc))
            raise
        finally:
            save(output / "state.json", state)
        return state

    def selected(self, build):
        build = Path(build).resolve()
        value = read(build / "matrix-build.json")
        images = read(build / "images.json")["images"]
        require(read(build / "state.json")["status"] == BUILD_PASS and value["contract"] == CONTRACT,
                "incomplete/wrong matrix build")
        require(value["parent_identity_sha256"] == sha(self.identity_path)
                and value["current_precondition"] == self.precondition, "build/precondition identity")
        validated_images(images)
        for image in images:
            self.a.validate_image(image, build)
            self.g.verify_build(Path(image["path"]), self.repo)
            require(sha(Path(image["path"]) / "vdot-perf.bin") == image["image_sha256"], "image digest")
        require(value["images"] == {i["name"]: i["image_sha256"] for i in images}, "build image identity")
        require(self.a.pairs(images, self.repo) == read(build / "pairs.json"), "matrix pair receipt drift")
        anchors = [self.anchor(i) for i in images if i["variant"] == "firstdot"]
        require(anchors == read(build / "baseline-current.json"), "current baseline receipt drift")
        require(value["sources"] == self.fixed, "matrix source inventory drift")
        self.runtime()[1].verify_files(self.fixed)
        return images

    def runtime(self):
        f, m = super().runtime()
        m.CONTRACT = CONTRACT
        return f, m

    def common_inputs(self, build, images, m, physical):
        files = physical[1] | m.checker_files(self.repo)
        for filename in ("matrix-build.json", "state.json", "images.json", "pairs.json", "baseline-current.json"):
            files[str(build / filename)] = sha(build / filename)
        for image in images:
            for filename in ("build.json", "data/manifest.json"):
                path = Path(image["path"]) / filename
                files[str(path)] = sha(path)
        require(set(p for p in files if p.endswith("/vdot-perf.bin")) == self.comparison_bins(),
                "complete shared comparison-BIN role map")
        return files

    def evaluate(self, records, images, m):
        validate_records(records, images)
        by_image = validated_images(images)
        by_record = {(item_key(r), r["replay"]): r for r in records}
        replay_by_shape = {}
        for shard in SHARDS:
            replay_by_shape[shard] = all(
                by_record[((shard, 0, variant), 0)]["samples"] ==
                by_record[((shard, 0, variant), 1)]["samples"] for variant in VARIANTS)
        replay_equal = all(replay_by_shape.values())
        summary = self.a.summarize(records)
        require(summary["measured_windows"] == 384 and len(summary["rows"]) == 4
                and sum(len(r["samples"]) for r in records) == 768, "exact matrix window inventory")
        dataset_summaries = {d: self.a.summarize([r for r in records if r["dataset"] == d])
                             for d in DATASETS}
        controls = {s: [] for s in SHARDS}
        for shard in SHARDS:
            for dataset in DATASETS:
                current = by_record[((shard, dataset, "firstdot"), 0)]
                baseline = next(r for r in self.baseline_records if
                    (r["variant"], r["shard"], r["dataset"], r["replay"]) ==
                    ("firstdot", shard, dataset, 0))
                if current["samples"] != baseline["samples"]:
                    controls[shard].append(f"dataset{dataset}: identical qualified firstdot full-24-window sample differs")
                pair = [by_image[(shard, dataset, v)] for v in VARIANTS]
                manifests = [read(Path(i["path"]) / "data/manifest.json") for i in pair]
                for left, right in zip(manifests[0]["rows"], manifests[1]["rows"]):
                    if left["method"] == "rvv" and not right["config_reuse_proof"]["removed"]:
                        software = left["software"]
                        signatures = [[(s["seq"], s["cycles"], s["instructions"]) for s in
                            by_record[((shard, dataset, v), 0)]["samples"]
                            if s["method"] == "rvv" and s["software"] == software] for v in VARIANTS]
                        require(all(len(s) == 6 for s in signatures), "unchanged RVV six-window control")
                        if signatures[0] != signatures[1]:
                            controls[shard].append(f"dataset{dataset}: unchanged {software} RVV six-window differs")
        decisions = {}
        for shard in SHARDS:
            rows = next(r["candidates"] for r in summary["rows"] if r["shard"] == shard)
            datasets = {d: next(r["candidates"] for r in dataset_summaries[d]["rows"]
                                if r["shard"] == shard) for d in DATASETS}
            shape = "x".join(map(str, SHAPES[shard]))
            decisions[shape] = decide_shape(rows, datasets, controls[shard], replay_by_shape[shard])
        return summary, decisions, replay_equal

    def run(self, build, output, operation, workers=1):
        require(type(workers) is int and 1 <= workers <= 4, "explicit workers integer 1..4")
        affinity = sorted(os.sched_getaffinity(0))
        require(workers <= len(affinity) <= 4, "workers <= allowed CPU affinity <=4")
        build, output = Path(build).resolve(), Path(output).resolve()
        self.external(output, [build])
        images = self.selected(build)
        physical_before = self.physical()
        cfg = self.identity["configuration"]
        f, m = self.runtime()
        files = self.common_inputs(build, images, m, physical_before)
        process_common = process_inputs(files, self.comparison_bins())
        m.verify_files(files)
        specs = run_specs(images)
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        output.mkdir(parents=True)
        state = dict(contract=CONTRACT, status="PREFLIGHT", new_emu_runs=0, active_pids={},
                     operation_id=operation, started=f.now(), workers=workers, cpu_affinity=affinity,
                     boot_id=boot_id, monotonic_start_ns=time.monotonic_ns(), monotonic_end_ns=None,
                     hardware_changed=False, default_changed=False)
        save(output / "state.json", state)
        save(output / "runtime-inputs.json", files)
        save(output / "configuration.json", cfg)
        save(output / "hardware-profile.json", physical_before[2])
        save(output / "run-plan.json", specs)
        shutil.copyfile(self.identity_path, output / "parent-identity.json")
        completed, started = {}, {}
        lock = threading.Lock()

        def ordered_normals():
            return [completed[s["label"]] for s in specs if not s["negative"] and s["label"] in completed]

        def launch(spec, fixture=None):
            # A fresh private f/m pair owns this spawn wrapper; no global or
            # thread-shared spawn/receipt/timing variable is replaced.
            job_f, job_m = self.runtime()
            original_spawn = job_f.spawn
            label = spec["label"]
            destination = output / "runs" / label

            def progress(receipt):
                receipt.update(label=label, phase=spec["phase"])
                if receipt.get("process_started") is True and "monotonic" in receipt:
                    receipt["monotonic"]["pid"] = receipt.get("pid")
                # execute persists before invoking this callback; persist these
                # controller-owned fields as well, including its first receipt.
                save(destination / "result.json", receipt)
                with lock:
                    if receipt.get("process_started") is True:
                        require(type(receipt.get("pid")) is int and receipt["pid"] > 0, "actual PID")
                        if label not in started:
                            require(receipt["pid"] not in started.values(), "actual PID reused")
                            started[label] = receipt["pid"]
                        require(started[label] == receipt["pid"], "process PID changed")
                        state["new_emu_runs"] = len(started)
                        timing = receipt.get("monotonic", {})
                        if timing.get("end_ns") is None and "finished" not in receipt:
                            state["active_pids"][label] = receipt["pid"]
                        else:
                            state["active_pids"].pop(label, None)
                    save(output / "state.json", state)

            def timed_spawn(argv, cwd, stdout, stderr, record, persist, **kwargs):
                record["monotonic"] = dict(boot_id=boot_id, pid=None, start_ns=time.monotonic_ns(),
                                           end_ns=None, scope="popen_wait_bracket")
                persist()
                try:
                    return original_spawn(argv, cwd, stdout, stderr, record, persist, **kwargs)
                finally:
                    record["monotonic"].update(pid=record.get("pid"), end_ns=time.monotonic_ns())
                    persist()

            job_f.spawn = timed_spawn
            job_m.verify_files(files)
            record = job_m.execute(self.repo, cfg, spec["image"], destination,
                                  process_common, fixture, spec["replay"], progress)
            job_m.verify_files(files)
            require(all(record[k] == spec["image"][k] for k in
                        ("name", "suite", "shard", "dataset", "variant", "image_sha256", "path")),
                    "run image identity")
            validate_timing([record], 1, boot_id)
            with lock:
                completed[label] = record
                save(output / "completed-runs.json", ordered_normals())
            return record

        def phase_pool(phase_specs):
            pending = deque(phase_specs)
            failure = None
            with ThreadPoolExecutor(max_workers=workers) as executor:
                running = {}
                while pending and len(running) < workers:
                    spec = pending.popleft()
                    running[executor.submit(launch, spec)] = spec
                while running:
                    done, _ = wait(running, return_when=FIRST_COMPLETED)
                    # Observe the whole completed batch before submitting more.
                    for future in done:
                        running.pop(future)
                        try:
                            future.result()
                        except BaseException as exc:
                            if failure is None:
                                failure = exc
                    while failure is None and pending and len(running) < workers:
                        spec = pending.popleft()
                        running[executor.submit(launch, spec)] = spec
                if failure is not None:
                    raise failure

        try:
            state["status"] = "RUNNING"
            save(output / "state.json", state)
            fixture = m.build_negative(self.repo, cfg, output / "negative-fixture")
            rejected = launch(specs[0], fixture)
            require(int(rejected["negative_details"]["pc"], 16) == self.a.negative_target(specs[0]["image"]),
                    "negative actual first custom instruction PC")
            recovery = launch(specs[1])
            validate_recovery(rejected, recovery)
            phase_pool([s for s in specs if s["phase"] == "formal"])
            # Full phase barrier: no dataset0 replay starts before every formal
            # process and semantic check has completed successfully.
            phase_pool([s for s in specs if s["phase"] == "replay"])
            records = ordered_normals()
            validate_records(records, images)
            require(len(completed) == state["new_emu_runs"] == 33 and not state["active_pids"],
                    "exact 33 new processes, no active target")
            require(self.selected(build) == images, "matrix inputs changed during execution")
            require(self.physical() == physical_before, "clean runtime identity drift")
            m.verify_files(files)
            summary, decisions, replay_equal = self.evaluate(records, images, m)
            state["monotonic_end_ns"] = time.monotonic_ns()
            all_records = [completed[s["label"]] for s in specs]
            proof = validate_timing(all_records, workers, boot_id,
                                    (state["monotonic_start_ns"], state["monotonic_end_ns"]))
            require(recovery["monotonic"]["end_ns"] <= min(
                r["monotonic"]["start_ns"] for r in all_records if r["phase"] in ("formal", "replay")),
                "recovery phase barrier")
            require(max(r["monotonic"]["end_ns"] for r in all_records if r["phase"] == "formal") <=
                    min(r["monotonic"]["start_ns"] for r in all_records if r["phase"] == "replay"),
                    "formal to replay phase barrier")
            proof["barriers_verified"] = True
            state.update(status=RUN_PASS, functional_status="FUNCTIONAL_PASS",
                         all_window_replay=replay_equal, monotonic_proof=proof)
            result = dict(contract=CONTRACT, status=RUN_PASS, functional_status="FUNCTIONAL_PASS",
                parent_identity_sha256=sha(self.identity_path), current_precondition=self.precondition,
                runs=records, negative=rejected, summary=summary, decisions=decisions,
                all_window_replay=replay_equal, monotonic_proof=proof, default_changed=False,
                historical_pass_reused=False, new_emu_runs=33, workers=workers, boot_id=boot_id)
            save(output / "results.json", result)
            return result
        except BaseException as exc:
            state.update(status="FAILED", error=repr(exc))
            raise
        finally:
            if state["monotonic_end_ns"] is None:
                state["monotonic_end_ns"] = time.monotonic_ns()
            state["finished"] = f.now()
            save(output / "state.json", state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("repo", "identity", "matrix", "matrix-run", "output"):
        parser.add_argument("--" + flag, required=True, type=Path)
    parser.add_argument("--action", required=True, choices=("build", "run"))
    parser.add_argument("--build", type=Path)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--operation-id", default="current-clean-config-reuse-matrix-v1")
    args = parser.parse_args()
    require(type(args.workers) is int and 1 <= args.workers <= 4, "workers must be 1..4")
    experiment = Matrix(args.repo, args.identity, args.matrix, args.matrix_run)
    if args.action == "build":
        result = experiment.build(args.output)
    else:
        require(args.build is not None, "--build required for run")
        result = experiment.run(args.build, args.output, args.operation_id, args.workers)
    # Full machine-readable results are already saved; terminal output remains concise.
    print(json.dumps(dict(contract=CONTRACT, status=result["status"], output=str(args.output)), indent=2))


if __name__ == "__main__":
    main()
