"""Ordinary C qualification and separately named firstdot GEMV public leaves.

The frozen R4 application, compiler checks, canaries, scalar oracle and runtime
gates are reused through private modules. The published R5 library is untouched.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import types

import firstdot_candidate as c
import firstdot_gate as g
import firstdot_experiment as a
import firstdot_evidence as evidence

CONTRACT = "r2-s1-firstdot-c-application-v1"
PARENT = g.ENTRY / "entry_c_api.py"
PARENT_SHA = "4e1ae340c5b122d09d634631d7fce322ad121838ba9a4affdf193d2a4d9105fd"
PUBLIC = g.S1 / "firstdot/public"


def public_name(name):
    g.require(name.startswith("r4_gemv_"), "unexpected parent public name")
    return name.replace("r4_gemv_", "firstdot_gemv_", 1)


def source_files(repo):
    g.bind(repo)
    g.require(g.sha(repo / PARENT) == PARENT_SHA and Path(__file__).resolve() == repo / g.S1 / "firstdot_c_api.py",
              "ordinary C adapter identity")
    paths = g.SOURCES | {str(PARENT), str(g.S1 / "firstdot_c_api.py"), str(g.S1 / "firstdot_evidence.py"), str(g.S1 / "gate.py"),
                         str(g.REL / "machine_model.py")}
    paths |= {str(a.REPRO / name) for name in a.t17.ADAPTERS}
    return {rel: g.sha(repo / rel) for rel in sorted(paths)}


def generate(repo, output):
    source_files(repo)
    base = g.load("firstdot_private_c_renderer", repo / PARENT)
    original_candidate = base.candidate
    def candidate(root, out, variant, dataset, shard, suite="performance"):
        g.require(variant == "s1", "ordinary C parent selection")
        return c.generate(root, out, "firstdot", dataset, shard, suite)
    base.CONTRACT = CONTRACT
    base.candidate = types.SimpleNamespace(source=original_candidate.source, generate=candidate)
    manifest = base.generate(repo, output)
    mapping = {r["api_symbol"]: public_name(r["api_symbol"]) for r in manifest["rows"]}
    for name in ("gemv.S", "gemv.h", "cases.h"):
        path = output / name
        text = path.read_text()
        for before, after in mapping.items():
            text = text.replace(before, after)
        if name == "gemv.h":
            text = text.replace("R4_PUBLIC_GEMV_H", "FIRSTDOT_PUBLIC_GEMV_H")
            text = text.replace("S1 leaves;", "Firstdot leaves;")
            text = text.replace("ENTRY_CONTRACT.md", "../../FIRSTDOT_C_CONTRACT.md")
        path.write_text(text)
    for row in manifest["rows"] + manifest["cases"]:
        row["api_symbol"] = mapping[row["api_symbol"]]
    manifest.update(variant="firstdot", stable_default_changed=False,
                    adapter_sha256=g.sha(Path(__file__)))
    g.save(output / "manifest.json", manifest)
    return manifest


def adapter(repo, identity):
    source_files(repo)
    f, m = a.runtime(repo, identity)
    m.SOURCE, m.EMU = identity["source_commit"], identity["hardware_profile"]["emu_sha256"]
    m.META = dict(identity["metadata_sha256"])
    def hardware_profile(root, cfg):
        files, profile = a.t17.p.hardware_profile(root, cfg)
        g.require(profile == identity["hardware_profile"] and
                  {n: files[str(Path(cfg["build_record"]) / n)] for n in a.t17.p.META_NAMES} == identity["metadata_sha256"],
                  "ordinary C physical T17 identity differs")
        return files, profile
    m.hardware_profile = hardware_profile
    negative_check = m.negative_check
    def checked_negative(*args):
        detail = negative_check(*args)
        g.require(detail["vd"] == 0 and detail["word"] == "0x0388000b" and detail["bit"] == 100,
                  "ordinary C firstdot negative destination")
        return detail
    m.negative_check = checked_negative
    parent = g.load("firstdot_private_c_application", repo / PARENT)
    parent.CONTRACT, parent.generate, parent.source_files = CONTRACT, generate, source_files
    parent.a = types.SimpleNamespace(read=a.read, frozen_f=f, frozen_m=m)
    return parent


def library_anchor(repo, build, matrix):
    """Compare every public leaf against all three measured dataset objects."""
    g.require(g.sha(repo / evidence.PORTABLE) == evidence.HELPERS[str(evidence.PORTABLE)], "archive helper drift")
    archive = g.load("firstdot_c_matrix_anchor", repo / evidence.PORTABLE).Archive(matrix)
    g.require(archive.manifest["contract"] == c.CONTRACT and archive.manifest["qualification_scope"] == "matrix", "full firstdot matrix required")
    public = g.ELF((build / "gemv-reference.o").read_bytes())
    manifest = a.read(build / "source/manifest.json")
    names = {r["api_symbol"] for r in manifest["rows"]}
    expected = {(s, d) for s in (1, 3, 5, 7) for d in range(3)}
    seen, comparisons = set(), []
    for collection in archive.manifest["builds"]:
        for image in archive.json("builds/" + collection + "/images.json")["images"]:
            if image["variant"] != "firstdot":
                continue
            key = image["shard"], image["dataset"]
            g.require(key not in seen, "duplicate firstdot library anchor")
            seen.add(key)
            prefix = "builds/" + collection + "/images/" + image["name"]
            parent = g.ELF(archive.raw(prefix + "/gemv-reference.o"))
            rows = archive.json(prefix + "/data/manifest.json")["rows"]
            for row in rows:
                symbol = public_name(row["api_symbol"])
                g.require(symbol in names and parent.symbol_data(row["api_symbol"]) == public.symbol_data(symbol),
                          "ordinary C leaf differs from measured firstdot")
                comparisons.append(dict(image=image["name"], symbol=symbol, sha256=evidence.digest(public.symbol_data(symbol))))
    g.require(seen == expected and len(comparisons) == 48 and len(names) == 16, "incomplete library anchor")
    return dict(status="FIRSTDOT_PUBLIC_LEAVES_MATCH_MATRIX", matrix_manifest_sha256=archive.manifest_sha256,
                public_functions=16, cross_dataset_leaf_comparisons=48, comparisons=comparisons)


def qualification(anchor):
    return dict(status="FIRSTDOT_C_APPLICATION_CALLS_PASS", contract=CONTRACT,
        parent_identity_sha256=a.PARENT_IDENTITY_SHA, matrix_anchor=anchor, ordinary_c_cases=48,
        normal_case_executions=96, new_emu_runs=3, performance_measured=False, stable_default_changed=False)


def validate_qualification(build, run, anchor):
    g.require(a.read(build / "matrix-anchor.json") == anchor and
              a.read(run / "firstdot-qualification.json") == qualification(anchor), "firstdot C qualification differs")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--action", choices=("build", "run", "audit", "export"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--build", type=Path)
    p.add_argument("--run", type=Path)
    p.add_argument("--matrix", type=Path, required=True)
    p.add_argument("--operation-id")
    args = p.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    g.require(repo == a.ROOT and not output.exists(), "new output in selected checkout required")
    identity = a.parent_identity(repo, args.identity.resolve())
    cfg = identity["configuration"]
    a.outside_inputs(output, [repo, args.identity.resolve().parent, args.matrix.resolve(),
        cfg["hardware_source"], cfg["build_record"], cfg["am_home"], *[x.resolve() for x in (args.build, args.run) if x]])
    if os.name == "posix":
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    base = adapter(repo, identity)
    if args.action == "build":
        proof = evidence.audit(repo, args.matrix.resolve())
        g.require(proof["qualification_scope"] == "matrix", "ordinary C needs complete matrix")
        result = base.build(repo, cfg, output)
        g.save(output / "matrix-anchor.json", library_anchor(repo, output, args.matrix.resolve()))
    elif args.action == "run":
        g.require(args.build and args.operation_id, "ordinary C run requires build and operation")
        anchor = library_anchor(repo, args.build.resolve(), args.matrix.resolve())
        g.require(anchor == a.read(args.build / "matrix-anchor.json"), "C matrix anchor drift")
        result = base.run(repo, cfg, args.build.resolve(), output, args.operation_id)
        g.save(output / "firstdot-qualification.json", qualification(anchor))
    else:
        g.require(args.build, "C build required")
        base.verify_build(repo, args.build.resolve())
        anchor = library_anchor(repo, args.build.resolve(), args.matrix.resolve())
        g.require(anchor == a.read(args.build / "matrix-anchor.json"), "C matrix anchor drift")
        if args.action == "audit":
            g.require(args.run, "C run required")
            validate_qualification(args.build.resolve(), args.run.resolve(), anchor)
            result = dict(status="FIRSTDOT_C_APPLICATION_RAW_AUDIT_PASS", proof=base.audit_run(repo, args.build.resolve(), args.run.resolve()),
                          matrix_anchor=anchor, stable_default_changed=False)
            g.save(output, result)
        else:
            g.require(args.run, "qualified C run required for export")
            validate_qualification(args.build.resolve(), args.run.resolve(), anchor)
            proof = base.audit_run(repo, args.build.resolve(), args.run.resolve())
            output.mkdir(parents=True)
            for name in ("gemv.S", "gemv.h"):
                (output / name).write_bytes((args.build / "source" / name).read_bytes())
            result = dict(status="FIRSTDOT_PUBLIC_SOURCE_QUALIFIED", contract=CONTRACT, matrix_anchor=anchor,
                          files={n: g.sha(output / n) for n in ("gemv.S", "gemv.h")}, ordinary_c_proof=proof,
                          stable_default_changed=False, performance_measured_in_c_application=False)
            g.save(output / "manifest.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("functions", "matrix_anchor")}, indent=2))


if __name__ == "__main__":
    main()
