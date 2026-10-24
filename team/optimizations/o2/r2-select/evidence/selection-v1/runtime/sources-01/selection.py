"""Select and export the exact qualified S1 v2 GEMV images; never run an emulator.

Qualification is reused from two pinned, published architecture audits. This
tool rechecks all archive bytes, formal sample identities, ranking, case/image
links and exported bytes. It does not qualify a new dispatcher or caller.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
REL = Path("team/optimizations/o2/r2-select")
S1 = Path("team/optimizations/o2/r2-vector-accum")
LEGACY = Path("team/optimizations/o2/r2-safe-tail")
PORTABLE = Path("team/optimizations/o2/fullcore/portable.py")
CONTRACT = "r2-select-qualified-original-images-v1"
PASS = "R2_SELECT_ORIGINAL_IMAGE_BUNDLE_PASS"
ARCHIVE_SHA = "a1af4314c83b29d97b58b7ae9fe65dbc96bb3d050530d2fe7378c022b9415d73"
S1_PUBLICATION = "ec221262ae29522dd9d1a2be7240b405cc23a549"
SHAPES = ((4, 8), (8, 32), (16, 64), (4, 13))
SCOPES = ("core", "endtoend")
PINS = {
    "candidate.py": "0270736b5c09e160626eb7b32d8e760faa193bf05761fea824a979108c3717b9",
    "gate.py": "ab07b578f5fe2dc7782ef9af64e722e051363d1dfddfcd0f1939efb209346b6d",
    "experiment.py": "75a26c36531b547ecb09c5ff19ecef1b338622779aedb2099f7775efd74cb7dd",
    "evidence.py": "2d07f72b78314a0775694c12124f793d452bb9a752ae722d6cc1c6182048c5fd",
    "complete_replay.py": "f68fe2978248776ba6556fe15d941fb32df02a5ceeb20247424fd08374babba7",
}
LEGACY_PINS = {
    "linked_gate.py": "96807465bfd97a483f31ce100e552e2b83c4d0edd59f9bf4d817c66abd80ec1f",
    "fullcore_screen.py": "5f5c719a9a5b675f4de166ca30a3d89bd52c944c667cee302f66da94fa2779f2",
    "merged_screen.py": "ff75464c5b0f75349fc4321bdd80a7a85985a54ae415ad347c3ce04fdf4bd885",
}
AUDITS = {
    "merged-v2-audit-linux.json": "b035c4b400a7d8cfbca6c45cf41c8582ee965fff1dede5cf59320199912d33be",
    "merged-v2-small-replay-audit-linux.json": "2165d95cda3282b6c81c0ce9164a42997bec9c0b4bd69d4ef469d505264e4d0c",
}
BOUNDARY = dict(new_emu_runs=0, new_nemu_runs=0, architecture_recomputed=False,
                qualified_evidence_reused=True, new_dispatcher_qualified=False,
                default_entry_changed=False, whole_suite_acceptance=False,
                physical_external_inputs_revalidated=False)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def now():
    return datetime.now(timezone.utc).isoformat()


def load_engine(repo):
    repo = Path(repo).resolve()
    require(Path(__file__).resolve() == repo / REL / "selection.py", "entry outside selected repository")
    for name, expected in PINS.items():
        require(digest((repo / S1 / name).read_bytes()) == expected, "frozen S1 source differs: " + name)
    for name, expected in LEGACY_PINS.items():
        require(digest((repo / LEGACY / name).read_bytes()) == expected, "frozen reusable source differs: " + name)
    require(digest((repo / PORTABLE).read_bytes()) ==
            "7a2fc8e9638b898cc8f2f24fcb7794cf7108ef4e625bf38bcd8cc423ef3ae17b", "portable checker differs")
    # A separate CLI process is preferred. Refuse an earlier incompatible
    # candidate/gate import rather than silently binding another contract.
    imports = [(name, S1) for name in ("candidate", "gate", "experiment")]
    imports += [(name, LEGACY) for name in ("linked_gate", "fullcore_screen", "merged_screen")]
    for name, relative in imports:
        if name in sys.modules:
            require(Path(sys.modules[name].__file__).resolve() == repo / relative / (name + ".py"),
                    "conflicting imported module: " + name)
    sys.path.insert(0, str(repo / S1))
    a = importlib.import_module("experiment")
    g = importlib.import_module("gate")
    for module, name in ((a, "experiment.py"), (g, "gate.py")):
        require(Path(module.__file__).resolve() == repo / S1 / name, "loaded source outside repository")
    for module, name in ((g.original, "linked_gate.py"), (a.legacy_f, "fullcore_screen.py"),
                         (a.legacy_m, "merged_screen.py")):
        require(Path(module.__file__).resolve() == repo / LEGACY / name, "loaded reusable source outside repository")
    require(g.ELF is g.original.ELF, "ELF decoder binding differs")
    g.verify_sources(repo)
    a.legacy_f.pinned_modules(repo)
    a.legacy_m.checker_files(repo)
    spec = importlib.util.spec_from_file_location("r2_select_portable", repo / PORTABLE)
    portable = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(portable)
    return a, g, portable


def checked_summary(records, experiment):
    """Retain the frozen 768-sample calculation and add identity checks."""
    inventory = {experiment.name(i): i for i in experiment.inventory()}
    expected = {(name, 0) for name in inventory}
    expected |= {(name, 1) for name, i in inventory.items()
                 if i["suite"] == "performance" and i["dataset"] == 0 and i["shard"] in (5, 7)}
    require(len(records) == len(expected) == 56, "normal record inventory differs")
    found = set()
    for record in records:
        key = (record["name"], record["replay"])
        require(type(record["replay"]) is int and key in expected and key not in found,
                "missing/extra/duplicate normal record")
        found.add(key)
        item = inventory[record["name"]]
        require(all(record[k] == v for k, v in item.items()) and
                type(record["dataset"]) is int and type(record["shard"]) is int and
                record["contract"] == experiment.CONTRACT and record["mode"] == "merged" and
                record["negative"] is False and type(record["exit_code"]) is int and
                record["exit_code"] == 0 and record["process_started"] is True,
                "record contract or execution identity differs")
        require(re.fullmatch(r"[0-9a-f]{64}", record["image_sha256"]) is not None, "invalid image identity")
        if item["suite"] != "performance":
            continue
        domain = set()
        sequences = set()
        m, k = SHAPES[item["shard"] // 2]
        scope = SCOPES[item["shard"] % 2]
        for sample in record["samples"]:
            sw, method, repeat = sample["software"], sample["method"], sample["repeat"]
            require(sw in ("basic", "reuse") and method in ("vdot", "rvv") and
                    type(repeat) is int and repeat in range(6), "invalid case/repeat")
            identity = (sw, method, repeat)
            require(identity not in domain, "duplicate case/repeat")
            domain.add(identity)
            require(type(sample["seq"]) is int and sample["seq"] in range(24) and
                    sample["seq"] not in sequences, "invalid sample sequence")
            sequences.add(sample["seq"])
            require(sample["phase"] == ("first" if repeat == 0 else "warmup" if repeat == 1 else "measured"),
                    "first/warmup/measured identity differs")
            require(all(sample[n] == record[n] for n in ("variant", "shard", "dataset", "image_sha256")) and
                    (sample["m"], sample["k"], sample["scope"]) == (m, k, scope) and
                    sample["id"] == f"gemv-{m}x{k}-{scope}-{sw}-{method}", "sample/case/image mismatch")
        require(domain == {(s, method, r) for s in ("basic", "reuse")
                           for method in ("vdot", "rvv") for r in range(6)}, "incomplete performance process")
    require(found == expected, "normal run coverage differs")
    return experiment.summarize(records)


def rank_rows(rows):
    """Choose whole 12-window implementations, never per-window winners.

    Equal totals prefer RVV, then S0, then basic. A tie is not a speedup.
    """
    expected = {(shard, v, sw) for shard in range(8) for v in ("s0", "s1") for sw in ("basic", "reuse")}
    require(len(rows) == 32 and {(r["shard"], r["variant"], r["software"]) for r in rows} == expected,
            "candidate matrix differs")
    choices = []
    for shard in range(8):
        candidates = []
        for row in rows:
            if row["shard"] != shard:
                continue
            require(row["shape"] == list(SHAPES[shard // 2]) and row["scope"] == SCOPES[shard % 2],
                    "candidate shape/scope differs")
            for method in ("vdot", "rvv"):
                stats = row[method]
                require(type(stats["samples"]) is int and stats["samples"] == 12 and
                        type(stats["total"]) is int and stats["total"] > 0 and
                        stats["mean"] == stats["total"] / 12, "candidate lacks 12-window total")
                candidates.append(dict(id=f"{row['variant']}:{row['software']}:{method}",
                                       variant=row["variant"], software=row["software"], method=method,
                                       statistics=dict(stats)))
        order = lambda c: (c["statistics"]["total"], c["method"] != "rvv", c["variant"] != "s0",
                           c["software"] != "basic")
        selected = min(candidates, key=order)
        rvv = min((c for c in candidates if c["method"] == "rvv"), key=order)
        fallback = min((c for c in candidates if c["variant"] == "s0" and c["method"] == "vdot"), key=order)
        choices.append(dict(shard=shard, shape=list(SHAPES[shard // 2]), scope=SCOPES[shard % 2],
                            candidates=candidates, selected=selected["id"], fastest_rvv=rvv["id"],
                            s0_vdot_fallback=fallback["id"],
                            fastest_rvv_over_selected=rvv["statistics"]["total"] / selected["statistics"]["total"],
                            strict_advantage_over_rvv=selected["statistics"]["total"] < rvv["statistics"]["total"]))
    return choices


def load_context(repo, archive_path):
    repo, archive_path = Path(repo).resolve(), Path(archive_path).resolve()
    a, g, portable = load_engine(repo)
    require(digest((archive_path / "archive-manifest.json").read_bytes()) == ARCHIVE_SHA,
            "not the qualified S1 merged-v2 archive")
    archive = portable.Archive(archive_path)
    require(archive.manifest["contract"] == a.CONTRACT, "archive software contract differs")
    expected_files = {r["stored"] for r in archive.records.values()} | {
        "archive-manifest.json", "archive-manifest.sha256", "archive-check.json"}
    require({p.relative_to(archive_path).as_posix() for p in archive_path.rglob("*") if p.is_file()} == expected_files,
            "archive metadata inventory differs")
    audits = {}
    for name, expected in AUDITS.items():
        raw = (repo / S1 / "evidence" / name).read_bytes()
        require(digest(raw) == expected, "published qualification report differs: " + name)
        value = json.loads(raw)
        require(value["archive"] == archive.bytes_result, "qualification uses another archive")
        audits[name] = raw
    main = json.loads(audits["merged-v2-audit-linux.json"])
    small = json.loads(audits["merged-v2-small-replay-audit-linux.json"])
    require(main["status"] == "R2_S1_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS" and
            main["formal_windows"] == 768 and main["normal_runs"] == 56 and main["expected_negative_runs"] == 1 and
            main["replay_runs"] == 4 and small["status"] == "R2_S1_SMALL_REPLAY_ARCHIVE_RECOMPUTE_PASS" and
            small["normal_runs"] == 4 and small["matched_windows"] == 96 and small["additional_formal_windows"] == 0,
            "qualification scope differs")
    cached = archive.json("campaign/results.json")
    require(cached["contract"] == a.CONTRACT and cached["status"] == a.PASS, "campaign contract differs")
    summary = checked_summary(cached["runs"], a)
    for key in ("rows", "comparisons", "samples"):
        require(cached[key] == summary[key], "cached formal statistics differ: " + key)
    require(main["rows"] == summary["rows"] and main["comparisons"] == summary["comparisons"],
            "statistics disagree with published architecture audit")
    return dict(repo=repo, archive=archive, experiment=a, gate=g, portable=portable,
                summary=summary, audits=audits, records=cached["runs"])


def make_plan(context):
    archive, g = context["archive"], context["gate"]
    choices = rank_rows(context["summary"]["rows"])
    inventory = {i["name"]: i for i in archive.json("canonical/images.json")["images"]}
    formal = {r["name"]: r for r in context["records"] if r["suite"] == "performance" and r["replay"] == 0}
    images = {}
    copies = {}
    for name, record in sorted(formal.items()):
        image = inventory[name]
        prefix = "canonical/images/" + name + "/"
        manifest = archive.json(prefix + "data/manifest.json")
        elf = g.ELF(archive.raw(prefix + "vdot-perf.elf"))
        require(image["image_sha256"] == record["image_sha256"] ==
                digest(archive.raw(prefix + "vdot-perf.bin")), "canonical/actual image mismatch")
        require(manifest["r2_variant"] == image["variant"] and manifest["dataset"] == image["dataset"] and
                manifest["shard"] == image["shard"] and len(manifest["rows"]) == 4,
                "canonical selection differs")
        plan = {p["seq"]: p for p in manifest["plan"]}
        for sample in record["samples"]:
            require(all(sample[k] == plan[sample["seq"]][k] for k in ("id", "phase", "repeat")),
                    "actual window not in original call plan")
        for logical in archive.records:
            if logical.startswith(prefix):
                copies["images/" + name + "/" + logical[len(prefix):]] = logical
        run_logical = "campaign/runs/formal-" + name + "/result.json"
        require(archive.json(run_logical) == record, "summary and original run receipt differ")
        copies["runs/formal-" + name + "/result.json"] = run_logical
        images[name] = (image, manifest, elf, record, run_logical)
    require(len(images) == 48, "formal image inventory differs")
    for choice in choices:
        for candidate in choice["candidates"]:
            links = []
            for dataset in range(3):
                name = context["experiment"].name(dict(suite="performance", variant=candidate["variant"],
                                                      shard=choice["shard"], dataset=dataset))
                image, manifest, elf, record, run_logical = images[name]
                matches = [(i, r) for i, r in enumerate(manifest["rows"])
                           if r["software"] == candidate["software"] and r["method"] == candidate["method"]]
                require(len(matches) == 1, "ambiguous case in original image")
                index, row = matches[0]
                require([row["m"], row["k"]] == choice["shape"] and row["scope"] == choice["scope"],
                        "case shape/scope differs")
                symbol = f"t13_kernel_{index}"
                selected = [s for s in record["samples"] if s["id"] == row["id"] and s["phase"] == "measured"]
                require(len(selected) == 4 and {s["repeat"] for s in selected} == set(range(2, 6)),
                        "case lacks four formal windows per dataset")
                links.append(dict(dataset=dataset, image=name, case_id=row["id"], case_index=index,
                                  symbol=symbol, entry_pc=hex(elf.symbols[symbol][0]),
                                  elf="images/" + name + "/vdot-perf.elf", bin="images/" + name + "/vdot-perf.bin",
                                  bin_sha256=image["image_sha256"],
                                  elf_sha256=archive.records["canonical/images/" + name + "/vdot-perf.elf"]["raw_sha256"],
                                  case_manifest="images/" + name + "/data/manifest.json",
                                  run_result="runs/formal-" + name + "/result.json", source_run_logical=run_logical,
                                  formal_windows=[{k: s[k] for k in ("seq", "repeat", "cycles", "instructions")}
                                                  for s in selected]))
            require(sum(s["cycles"] for link in links for s in link["formal_windows"]) ==
                    candidate["statistics"]["total"], "candidate total and linked windows differ")
            candidate["datasets"] = links
    selection = dict(contract=CONTRACT, status="R2_SELECT_QUALIFIED_ORIGINAL_IMAGE_MAPPING_PASS",
                     software_contract=context["experiment"].CONTRACT, archive_manifest_sha256=ARCHIVE_SHA,
                     original_source_commit_at_export=archive.manifest["source_commit_at_export"],
                     qualification_publication_commit=S1_PUBLICATION,
                     implementation_sha256=digest(Path(__file__).read_bytes()), source_pins=PINS,
                     legacy_source_pins=LEGACY_PINS,
                     qualification_reports={"qualification/" + n: h for n, h in AUDITS.items()},
                     qualification_mode="reuse exact published architecture audits after archive-byte and source checks",
                     formal_windows=768, windows_per_candidate=12, normal_processes_original=56,
                     expected_negative_processes_original=1, additional_small_replays_original=4,
                     additional_formal_windows=0, scope=BOUNDARY,
                     policy="minimum whole-cell total across S0/S1 basic/reuse vdot/RVV; ties: RVV, S0, basic",
                     supported_shapes=[list(s) for s in SHAPES], scopes=list(SCOPES), datasets=[0, 1, 2],
                     choices=choices,
                     execution_boundary="Each exported image retains all four cases and original first/warmup/order."
                                        " Mapping and symbol metadata do not authorize a changed call path or inherit its cycles.")
    artifacts = [dict(path=path, source_logical=logical, sha256=archive.records[logical]["raw_sha256"],
                      bytes=archive.records[logical]["raw_bytes"]) for path, logical in sorted(copies.items())]
    return selection, artifacts, copies


def check_payloads(context, bundle, selection, artifacts):
    bundle = Path(bundle).resolve()
    expected = {r["path"] for r in artifacts} | {"qualification/" + n for n in AUDITS} | {
        "selection.json", "artifacts.json", "bundle-state.json"}
    actual = set()
    for path in bundle.rglob("*"):
        require(not path.is_symlink(), "bundle contains symlink")
        if path.is_file():
            actual.add(path.relative_to(bundle).as_posix())
    require(actual == expected, "bundle file inventory differs")
    require((bundle / "selection.json").read_bytes() == json_bytes(selection), "selection mapping differs")
    require((bundle / "artifacts.json").read_bytes() == json_bytes(artifacts), "artifact map differs")
    for row in artifacts:
        path = bundle.joinpath(*PurePosixPath(row["path"]).parts)
        raw = path.read_bytes()
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "exported bytes differ: " + row["path"])
    for name, raw in context["audits"].items():
        require((bundle / "qualification" / name).read_bytes() == raw, "qualification copy differs")


def verify_bundle(context, bundle):
    selection, artifacts, _ = make_plan(context)
    check_payloads(context, bundle, selection, artifacts)
    state = json.loads((Path(bundle) / "bundle-state.json").read_bytes())
    require(state["contract"] == CONTRACT and state["status"] == PASS and state["scope"] == BOUNDARY and
            state["implementation_sha256"] == selection["implementation_sha256"] and
            state["archive_manifest_sha256"] == ARCHIVE_SHA and state["exported_artifacts"] == len(artifacts),
            "bundle state differs or incomplete")
    start, finish = (datetime.fromisoformat(state[k]) for k in ("started_utc", "finished_utc"))
    require(start.utcoffset() is not None and finish.utcoffset() is not None and start <= finish, "bundle time identity")
    return dict(status=PASS, archive_manifest_sha256=ARCHIVE_SHA, shape_scope_choices=8,
                candidate_cells=64, formal_windows=768, windows_per_candidate=12, images=48,
                exported_artifacts=len(artifacts), exported_raw_bytes=sum(r["bytes"] for r in artifacts),
                selection_sha256=digest(json_bytes(selection)), artifacts_sha256=digest(json_bytes(artifacts)),
                implementation_sha256=selection["implementation_sha256"], scope=BOUNDARY)


def validate_destination(context, destination, bundle=None):
    destination = Path(destination).resolve()
    # A read-only qualification archive and its published reports must never
    # become output parents, even when the requested child does not yet exist.
    for source in (context["archive"].path.resolve(), context["repo"] / S1):
        require(not destination.is_relative_to(source), "output would modify qualified input tree")
    if bundle is not None:
        require(not destination.is_relative_to(Path(bundle).resolve()), "report must be outside sealed bundle")
    return destination


def export_bundle(context, output):
    output = validate_destination(context, output)
    selection, artifacts, copies = make_plan(context)
    output.mkdir(parents=True, exist_ok=False)
    state = dict(contract=CONTRACT, status="EXPORTING", started_utc=now(), scope=BOUNDARY,
                 implementation_sha256=selection["implementation_sha256"], archive_manifest_sha256=ARCHIVE_SHA,
                 exported_artifacts=len(artifacts),
                 checkout_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=context["repo"], text=True).strip())
    state_path = output / "bundle-state.json"
    state_path.write_bytes(json_bytes(state))
    try:
        for path, logical in copies.items():
            target = output.joinpath(*PurePosixPath(path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(context["archive"].raw(logical))
        (output / "qualification").mkdir()
        for name, raw in context["audits"].items():
            (output / "qualification" / name).write_bytes(raw)
        (output / "selection.json").write_bytes(json_bytes(selection))
        (output / "artifacts.json").write_bytes(json_bytes(artifacts))
        check_payloads(context, output, selection, artifacts)
        state.update(status=PASS, finished_utc=now())
        state_path.write_bytes(json_bytes(state))
        return verify_bundle(context, output)
    except BaseException as exc:
        state.update(status="FAILED", finished_utc=now(), error=repr(exc))
        state_path.write_bytes(json_bytes(state))
        raise


def resolve(context, bundle, shape, scope, dataset, role="selected"):
    require(tuple(shape) in SHAPES and scope in SCOPES and type(dataset) is int and dataset in range(3) and
            role in ("selected", "fastest_rvv", "s0_vdot_fallback"), "unsupported shape/scope/dataset/role")
    verification = verify_bundle(context, bundle)
    selection = json.loads((Path(bundle) / "selection.json").read_bytes())
    choice = next(c for c in selection["choices"] if c["shape"] == list(shape) and c["scope"] == scope)
    candidate = next(c for c in choice["candidates"] if c["id"] == choice[role])
    link = dict(next(d for d in candidate["datasets"] if d["dataset"] == dataset))
    for key in ("elf", "bin", "case_manifest", "run_result"):
        link[key] = str(Path(bundle).resolve() / link[key])
    return dict(status="R2_SELECT_ORIGINAL_IMAGE_RESOLVED", choice=candidate["id"], role=role,
                shape=list(shape), scope=scope, dataset=dataset, original_12_window_statistics=candidate["statistics"],
                artifact=link, verification=verification, new_execution_path_qualified=False,
                notice="The full original image still executes all four cases. No emulator was started.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--action", choices=("export", "verify", "resolve"), required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--shape", choices=[f"{m}x{k}" for m, k in SHAPES])
    parser.add_argument("--scope", choices=SCOPES, default="endtoend")
    parser.add_argument("--dataset", type=int, choices=range(3), default=0)
    parser.add_argument("--role", choices=("selected", "fastest_rvv", "s0_vdot_fallback"), default="selected")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.action == "resolve" and args.shape is None:
        parser.error("--shape is required for resolve")
    context = load_context(args.repo, args.archive or args.repo / S1 / "evidence/merged-v2")
    if args.report:
        validate_destination(context, args.report, args.bundle)
        require(not args.report.exists() and args.report.parent.is_dir(), "report destination exists or parent is missing")
    if args.action == "export":
        result = export_bundle(context, args.bundle)
    elif args.action == "verify":
        result = verify_bundle(context, args.bundle)
    else:
        result = resolve(context, args.bundle, tuple(map(int, args.shape.split("x"))), args.scope, args.dataset, args.role)
    if args.report:
        with args.report.open("xb") as handle:
            handle.write(json_bytes(result))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
