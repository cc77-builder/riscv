#!/usr/bin/env python3
"""Bounded K13 endtoend probe: unchanged S2 vdot versus qualified S1 RVV.

Two real AM images differ only in the two RVV slots. This is a dataset-0
selection probe, never the three-dataset/four-shape final acceptance matrix.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import fixed_layout as l
import fixed_screen as fixed

g, f, m = l.g, l.f, l.m
ENTRY = g.REL / "rvv_probe.py"
S1 = Path("team/optimizations/o2/r2-vector-accum/candidate.py")
S1_SHA = "0270736b5c09e160626eb7b32d8e760faa193bf05761fea824a979108c3717b9"
LAYOUT_SHA = "92e025d334c71c3720a92beb4f92314fbe8fabc3c5722b8a733f1cb6c0f7bc29"
SCREEN_SHA = "958dcb5303f09ddcf9ebf2f3a8e1225b5541d76f3f86a4aabf9c540ed9757e1d"
CONTRACT = "r2-s2-k13-strong-rvv-probe-v1"
BUILD_PASS = "R2_STRONG_RVV_TWO_ELFS_STATIC_PASS_NOT_RUNTIME"
PASS = "R2_STRONG_RVV_DATASET0_ENDTOEND_PROBE_PASS"
_bound = False


def source_identity(repo):
    repo = Path(repo).resolve()
    g.require(Path(__file__).resolve() == (repo / ENTRY).resolve(), "probe entry outside repository")
    g.require(g.sha(repo / S1) == S1_SHA and g.sha(repo / l.ADAPTER) == LAYOUT_SHA and
              g.sha(repo / l.ENTRY) == SCREEN_SHA, "probe dependency source drift")
    return g.sha(repo / ENTRY)


def generate(repo, output, variant, dataset, shard, suite="performance"):
    repo, output = Path(repo).resolve(), Path(output)
    g.require(variant in ("rvv0", "rvv1") and type(dataset) is int and dataset == 0 and
              type(shard) is int and shard == 7 and suite == "performance", "bounded probe selection")
    g.require(g.sha(repo / S1) == S1_SHA and (repo / ENTRY).read_bytes() == Path(__file__).read_bytes(),
              "probe snapshot source drift")
    g.verify_sources(repo)
    s2 = g.load("rvv_probe_s2_source", repo / g.REL / "candidate.py")
    s1 = g.load("rvv_probe_s1_source", repo / S1)
    base = s2.load_base(repo)
    original_case = base.case

    def case(m_, k, ds, method, software, scope):
        row = original_case(m_, k, ds, method, software, scope)
        if method == "vdot":
            row["body"] = s2.kernel(base, m_, k, method, software, scope, "s2")
            row["dots"] = sum(line.startswith(".word ") for line in row["body"])
        else:
            row["body"] = s1.kernel(base, m_, k, method, software, scope,
                                    "s1" if variant == "rvv1" else "s0")
        row["r2_variant"] = variant
        return row

    base.case = case
    # Preserve the complete S2 harness/string image. The new executable/run
    # identity is explicit in manifest + input seals, not a longer UART string.
    base.CONTRACT = s2.CONTRACT
    value = base.generate(output, suite, dataset, shard, 8)
    asm = (output / "kernels.S").read_text()
    g.require(asm.count(".option norvc\n") == 1 and asm.count(".balign 4096\n") == 8 and
              ".option norelax" not in asm, "probe original assembly layout drift")
    asm = asm.replace(".option norvc\n", ".option norvc\n.option norelax\n")
    (output / "kernels.S").write_text(asm.replace(".balign 4096\n", ".balign 8192\n"))
    value.update(r2_variant=variant, probe_contract=CONTRACT,
                 probe_source_sha256=g.sha(repo / ENTRY), s1_candidate_sha256=S1_SHA,
                 s2_candidate_sha256=g.sha(repo / g.REL / "candidate.py"),
                 layout_contract=l.LAYOUT_CONTRACT, kernel_slot_bytes=l.SLOT,
                 layout_adapter_sha256=LAYOUT_SHA,
                 acceptance="dataset0 endtoend probe only; no final selection acceptance")
    value["files"] = {name: g.sha(output / name) for name in ("kernels.S", "cases.h")}
    g.save(output / "manifest.json", value)
    return value


@contextmanager
def bindings(repo):
    global _bound
    repo = Path(repo).resolve()
    source_identity(repo)
    g.require(not _bound, "nested probe binding")
    with l.bindings(repo):
        saved = g.PINNED, l.generate, m.CONTRACT
        _bound = True
        try:
            # Add exact source pins; never replace or remove a frozen pin.
            g.PINNED = dict(g.PINNED)
            for rel in (ENTRY, S1):
                g.require(str(rel) not in g.PINNED, "probe pin collision")
                g.PINNED[str(rel)] = g.blob((repo / rel).read_bytes())
            l.generate = generate
            m.CONTRACT = CONTRACT
            yield
        finally:
            g.PINNED, l.generate, m.CONTRACT = saved
            _bound = False


def inventory():
    return [dict(suite="performance", dataset=0, shard=7, variant=v) for v in ("rvv0", "rvv1")]


def compare(a, b, ma, mb, ba, bb):
    g.require(ma["r2_variant"] == "rvv0" and mb["r2_variant"] == "rvv1", "probe pair variants")
    for key in ("contract", "suite", "dataset", "shard", "m", "k", "scope", "plan", "probe_contract",
                "probe_source_sha256", "s1_candidate_sha256", "s2_candidate_sha256", "layout_contract",
                "kernel_slot_bytes", "layout_adapter_sha256"):
        g.require(ma[key] == mb[key], "probe pair metadata differs: " + key)
    g.require((ma["dataset"], ma["shard"], ma["m"], ma["k"], ma["scope"], ma["probe_contract"]) ==
              (0, 7, 4, 13, "endtoend", CONTRACT), "probe pair domain")
    for elf, manifest, binary in ((a, ma, ba), (b, mb, bb)):
        elf.executable()
        g.compiled_cases(elf, manifest)
        g.require(binary == elf.binary(), "probe ELF/bin differs")
        g.require([elf.symbols[f"t13_kernel_{i}"][0] for i in range(4)] ==
                  [g.RAM + (i + 1) * l.SLOT for i in range(4)], "probe slot addresses differ")
    g.require(a.entry == b.entry and a.segments == b.segments and
              l.allocated_layout(a) == l.allocated_layout(b) and len(ba) == len(bb), "probe loaded layout differs")
    g.require(a.symbols["main"][:2] == b.symbols["main"][:2] and
              a.symbol_data("main") == b.symbol_data("main"), "probe main differs")
    aa, ab = bytearray(ba), bytearray(bb)
    g.require(len(ma["rows"]) == len(mb["rows"]) == 4, "probe row inventory")
    for i, (ra, rb) in enumerate(zip(ma["rows"], mb["rows"])):
        expected = (("basic", "vdot"), ("basic", "rvv"), ("reuse", "vdot"), ("reuse", "rvv"))[i]
        g.require((ra["software"], ra["method"]) == (rb["software"], rb["method"]) == expected,
                  "probe case order")
        g.require({k: v for k, v in ra.items() if k not in ("body", "r2_variant")} ==
                  {k: v for k, v in rb.items() if k not in ("body", "r2_variant")},
                  "probe inputs/golden/CSR metadata differs")
        start = (i + 1) * l.SLOT
        if ra["method"] == "vdot":
            g.require(ra["body"] == rb["body"] and ra["dots"] == 8 and
                      ba[start:start + l.SLOT] == bb[start:start + l.SLOT], "probe vdot slot changed")
        else:
            aa[start:start + l.SLOT] = ab[start:start + l.SLOT] = bytes(l.SLOT)
    g.require(aa == ab, "probe byte changed outside RVV slots")
    return dict(status="R2_STRONG_RVV_EXACT_PAIR_PASS", main=hex(a.symbols["main"][0]),
                unchanged_vdot_slots=[0, 2], permitted_different_slots=[1, 3],
                non_rvv_bytes_sha256=hashlib.sha256(aa).hexdigest(), metadata_exceptions=0)


def pair_paths(a, b):
    a, b = Path(a), Path(b)
    return compare(g.ELF((a / "vdot-perf.elf").read_bytes()), g.ELF((b / "vdot-perf.elf").read_bytes()),
                   m.read_json(a / "data/manifest.json"), m.read_json(b / "data/manifest.json"),
                   (a / "vdot-perf.bin").read_bytes(), (b / "vdot-perf.bin").read_bytes())


def build(repo, cfg, out):
    out.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status="BUILDING", started=f.now(), new_emu_runs=0)
    g.save(out / "state.json", state)
    try:
        with bindings(repo):
            tools = fixed.build_tools(repo, cfg)
            images = [l.build_one(repo, cfg, out / "images" / f.image_name(i), i, tools) for i in inventory()]
            pair = pair_paths(*(i["path"] for i in images))
            g.save(out / "images.json", dict(images=images))
            g.save(out / "pair-layout.json", pair)
        state.update(status=BUILD_PASS, canonical_elfs=2, complete_layout_pairs=1)
    except BaseException as exc:
        state.update(status="FAILED", error=repr(exc))
        raise
    finally:
        state["finished"] = f.now()
        g.save(out / "state.json", state)
    return state


def canonical(repo, cfg):
    root = Path(cfg["canonical_build"])
    state = m.read_json(root / "state.json")
    g.require(state.get("status") == BUILD_PASS and state.get("contract") == CONTRACT and
              state.get("canonical_elfs") == 2 and state.get("new_emu_runs") == 0, "probe build incomplete")
    images = m.read_json(root / "images.json")["images"]
    g.require(len(images) == 2, "probe inventory length")
    identity = None
    for image, item in zip(images, inventory()):
        g.require(all(image[k] == v for k, v in item.items()) and image["name"] == f.image_name(item),
                  "probe image selection differs")
        path = root / "images" / image["name"]
        g.require(Path(image["path"]).resolve() == path.resolve(), "probe image location differs")
        g.verify_build(path, repo)
        g.require(g.sha(path / "vdot-perf.bin") == image["image_sha256"], "probe image hash differs")
        receipt = m.read_json(path / "build.json")
        current = {k: receipt[k] for k in ("kind", "source_base", "source_commit", "am_revision", "external_files", "toolchain")}
        if identity is None:
            identity = current
        g.require(current == identity, "probe cross-image build environment differs")
        m.verify_files(receipt["external_files"])
    g.require(pair_paths(*(i["path"] for i in images)) == m.read_json(root / "pair-layout.json"), "probe pair cache differs")
    return images


def summarize(records):
    samples = [s for r in records if r["replay"] == 0 for s in r["samples"] if s["phase"] == "measured"]
    keys = {}
    for s in samples:
        key = tuple(s[k] for k in ("variant", "software", "method", "repeat"))
        g.require(key not in keys and (s["dataset"], s["shard"], s["scope"], s["mode"]) ==
                  (0, 7, "endtoend", "merged") and type(s["cycles"]) is int and s["cycles"] > 0 and
                  type(s["instructions"]) is int and s["instructions"] > 0, "probe duplicate/invalid sample")
        keys[key] = s
    expected = {(v, w, method, repeat) for v in ("rvv0", "rvv1") for w in ("basic", "reuse")
                for method in ("vdot", "rvv") for repeat in range(2, 6)}
    g.require(set(keys) == expected and len(samples) == 32, "probe formal inventory incomplete")
    rows = []
    for v in ("rvv0", "rvv1"):
        for w in ("basic", "reuse"):
            row = dict(variant=v, software=w)
            for method in ("vdot", "rvv"):
                values = [keys[(v, w, method, n)]["cycles"] for n in range(2, 6)]
                row[method] = dict(samples=4, total=sum(values), mean=statistics.mean(values),
                                   minimum=min(values), maximum=max(values), pstdev=statistics.pstdev(values))
            rows.append(row)
    best = min(rows, key=lambda r: r["rvv"]["total"])
    return dict(samples=samples, rows=rows, fastest_rvv=dict(variant=best["variant"], software=best["software"], **best["rvv"]),
                scope="dataset0 K13 endtoend; 4 measured samples/cell, not full 12-sample qualification")


def runtime_files(repo, cfg, images):
    files = m.checker_files(repo)
    for rel in (ENTRY, S1):
        files[str(repo / rel)] = g.sha(repo / rel)
    for image in images:
        for name in ("build.json", "data/manifest.json"):
            path = Path(image["path"]) / name
            files[str(path)] = g.sha(path)
    for name in ("state.json", "images.json", "pair-layout.json"):
        path = Path(cfg["canonical_build"]) / name
        files[str(path)] = g.sha(path)
    return files


def run(repo, cfg, out):
    out.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status="PREFLIGHT", started=f.now(), new_emu_runs=0,
                 final_selection_qualified=False, historical_b0_h1_acceptance=False, whole_suite_acceptance=False)
    persist = lambda: g.save(out / "state.json", state)
    persist()
    try:
        with bindings(repo):
            images = canonical(repo, cfg)
            files = runtime_files(repo, cfg, images)
            hardware, detail = m.hardware_profile(repo, cfg)
            files.update(hardware)
            g.save(out / "configuration.json", cfg)
            g.save(out / "build-profile.json", detail)
            g.save(out / "runtime-inputs.json", files)
            g.save(out / "images.json", dict(images=images))
            fixture = m.build_negative(repo, cfg, out / "negative-fixture")
            def launch(image, name, negative=None, replay=0):
                dest = out / "runs" / name
                before = state["new_emu_runs"]
                def progress(record):
                    state["new_emu_runs"] = before + int(record.get("process_started") is True)
                    state["active_pid"] = record.get("pid") if "finished" not in record else None
                    state["active_result"] = str(dest / "result.json") if "finished" not in record else None
                    persist()
                return m.execute(repo, cfg, image, dest, files, negative, replay, progress)
            first, strong = images
            state.update(status="RUNNING", stage="negative-recovery")
            persist()
            negative = launch(strong, "negative-rvv1", fixture)
            records = [launch(strong, strong["name"] + "-r0")]
            m.validate_recovery(negative, records[0])
            records.append(launch(first, first["name"] + "-r0"))
            state["stage"] = "replay"
            persist()
            for image in images:
                record = launch(image, image["name"] + "-r1", replay=1)
                prior = next(r for r in records if r["name"] == image["name"] and r["replay"] == 0)
                g.require(m.signature(record) == m.signature(prior), "probe deterministic replay differs")
                records.append(record)
            stats = summarize(records)
            # Close the whole input set, including the image whose replay
            # finished first; per-process seals alone do not cover this tail.
            canonical(repo, cfg)
            m.hardware_profile(repo, cfg)
            m.verify_files(files)
            receipts = [m.read_json(path) for path in (out / "runs").glob("*/result.json")]
            g.require(len(receipts) == 5 and sum(r.get("negative") is True for r in receipts) == 1 and
                      all(r.get("process_started") is True and not r.get("timed_out") and
                          r.get("status") == (m.NEGATIVE_PASS if r.get("negative") else m.NORMAL_PASS) and
                          r.get("exit_code") == (1 if r.get("negative") else 0) for r in receipts),
                      "probe actual process inventory incomplete")
            g.save(out / "results.json", dict(status=PASS, contract=CONTRACT, negative=negative, runs=records, **stats))
            state.update(status=PASS, stage="complete", normal_runs_completed=4, formal_windows=32)
    except BaseException as exc:
        state.update(status="BLOCKED_OR_FAILED", error=repr(exc))
        raise
    finally:
        receipts = [m.read_json(p) for p in (out / "runs").glob("*/result.json")]
        state["new_emu_runs"] = sum(r.get("process_started") is True for r in receipts)
        state["failed_or_incomplete_emu_runs"] = sum(r.get("process_started") is True and
            r.get("status") != (m.NEGATIVE_PASS if r.get("negative") else m.NORMAL_PASS) for r in receipts)
        state["finished"] = f.now()
        persist()
    return state


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--action", choices=("build", "run"), required=True)
    a = p.parse_args()
    try:
        repo = a.repo.resolve()
        cfg = fixed.read_config(a.config, repo)
        result = build(repo, cfg, a.output.resolve()) if a.action == "build" else run(repo, cfg, a.output.resolve())
        print(json.dumps(result))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        p.exit(2, "R2_STRONG_RVV_PROBE_REJECTED: " + str(exc) + "\n")
