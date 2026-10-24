"""T17 transport v2: keep runtime products out of the source-tool namespace.

The original packers and raw auditors remain unchanged. Repacking only moves
the exact EMU and, for C, the two global AUX inputs to their existing external
or matrix identities. Private per-run AUX, logs, images and receipts retain
their original bytes. Source archives are preserved outside the new archive.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil

import clean_evidence as base

p, g, e, ce = base.p, base.g, base.e, base.ce
CONTRACT = "t17-portable-entry-v2"
SELF = "team/optimizations/o2/repro/clean_portable_evidence.py"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def targets(identity, kind, matrix=None):
    cfg = identity["configuration"]
    hardware = PurePosixPath(cfg["hardware_source"]) / "build"
    emu = str(hardware / "emu")
    result = {emu: dict(sha256=identity["hardware_profile"]["emu_sha256"], logical=None)}
    if kind == "c":
        p.require(matrix is not None, "C transport needs matrix")
        result[emu]["archive"] = "external"
        sealed = matrix.json("sealed-inputs.json")
        p.require(sealed.get(emu) == dict(sha256=result[emu]["sha256"], logical=None), "matrix EMU identity")
        for name, sha in p.AUX.items():
            path, logical = str(hardware / name), "hardware/" + name
            p.require(sealed.get(path) == dict(sha256=sha, logical=logical) and
                      matrix.records[logical]["original"] == path and digest(matrix.raw(logical)) == sha,
                      "matrix global AUX identity: " + name)
            result[path] = dict(sha256=sha, archive="matrix", logical=logical)
    return result


def validate(repo, archive, identity, kind, matrix=None):
    transport = archive.manifest["transport"]
    p.require(transport["contract"] == CONTRACT and transport["kind"] == kind and
              transport["source_tool_sha256"] == p.sha(__file__) and
              re.fullmatch(r"[0-9a-f]{64}", transport["source_manifest_sha256"]) is not None and
              PurePosixPath(transport["source_archive"]).is_absolute(), "transport identity")
    p.require(Path(__file__).resolve() == repo / SELF and
              digest(archive.raw("tools/" + SELF)) == p.sha(__file__), "transport source identity")
    wanted, sealed = targets(identity, kind, matrix), archive.json("sealed-inputs.json")
    p.require(set(transport["relocations"]) == set(wanted), "transport relocation inventory")
    originals = {r["original"] for r in archive.records.values()}
    for path, target in wanted.items():
        row = transport["relocations"][path]
        p.require(path not in originals and sealed.get(path) == target and row["after"] == target and
                  row["before"]["sha256"] == target["sha256"], "transport changed runtime identity: " + path)
    p.require(not any(name.startswith("tools/build/") for name in archive.records), "runtime product in source tools")
    if kind == "c":
        p.require(archive.manifest["matrix_manifest_sha256"] == matrix.manifest_sha256, "transport matrix anchor")
    return dict(status="T17_PORTABLE_NAMESPACE_PASS", contract=CONTRACT,
                source_manifest_sha256=transport["source_manifest_sha256"],
                source_archive=transport["source_archive"], relocations=transport["relocations"],
                runtime_input_hashes_changed=False, raw_auditor_sources_changed=False)


def repack(repo, source, output, identity, kind, matrix=None):
    portable, _, _ = e.modules(repo)
    saved = portable.Archive(source)
    p.require("transport" not in saved.manifest, "transport source must be an original pack")
    if kind == "matrix":
        p.require(saved.manifest["qualification_scope"] == "matrix", "complete matrix required")
        p.require(saved.manifest["contract"] == ce.a.candidate.CONTRACT, "matrix contract")
    else:
        p.require(saved.manifest["contract"] == ce.c_evidence.CONTRACT and
                  saved.manifest["matrix_manifest_sha256"] == matrix.manifest_sha256, "C source matrix anchor")
    p.require(not output.exists() and not output.is_relative_to(source) and not source.is_relative_to(output),
              "new transport output overlaps source")
    wanted, sealed = targets(identity, kind, matrix), saved.json("sealed-inputs.json")
    relocations = {}
    for path, target in wanted.items():
        p.require(path in sealed and sealed[path]["sha256"] == target["sha256"], "source runtime identity")
        relocations[path] = dict(before=sealed[path], after=target)
        sealed[path] = target
    output.mkdir(parents=True)
    entries = []
    own_logical = "tools/" + SELF
    retained = []
    for logical, record in saved.records.items():
        if record["original"] in wanted:
            p.require(logical.startswith("tools/") and record["raw_sha256"] == wanted[record["original"]]["sha256"],
                      "unexpected runtime payload namespace")
            continue
        if logical in ("sealed-inputs.json", own_logical):
            if logical == own_logical:
                p.require(saved.raw(logical) == Path(__file__).read_bytes(), "source transport tool differs")
            continue
        target = output / record["stored"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / record["stored"], target)
        p.require(p.sha(target) == record["stored_sha256"], "retained stored byte drift")
        entries.append(record)
        retained.append(logical)
    def add(raw, logical, original):
        portable.safe_relative(logical)
        stored, body, encoding = Path("files") / logical, raw, "identity"
        if len(raw) >= 4096:
            compressed = gzip.compress(raw, compresslevel=6, mtime=0)
            if len(compressed) + 64 < len(raw):
                stored, body, encoding = stored.with_name(stored.name + ".gz"), compressed, "gzip"
        destination = output / stored
        p.require(not destination.exists(), "duplicate transport destination")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        entries.append(dict(original=original, stored=stored.as_posix(), encoding=encoding,
                            raw_bytes=len(raw), raw_sha256=digest(raw), stored_bytes=len(body), stored_sha256=digest(body)))
    add(e.json_bytes(sealed), "sealed-inputs.json", "generated:sealed-inputs")
    add(Path(__file__).read_bytes(), own_logical, str(PurePosixPath(saved.manifest["source_root"]) / SELF))
    manifest = dict(saved.manifest, files=entries, transport=dict(contract=CONTRACT, kind=kind,
                    source_archive=str(source), source_manifest_sha256=saved.manifest_sha256,
                    source_tool_sha256=p.sha(__file__), relocations=relocations))
    raw = e.json_bytes(manifest)
    (output / "archive-manifest.json").write_bytes(raw)
    (output / "archive-manifest.sha256").write_text(digest(raw) + "  archive-manifest.json\n", encoding="ascii")
    final = portable.Archive(output)
    p.require(all(final.records[n] == saved.records[n] for n in retained), "retained payload metadata changed")
    status = e.BYTE_PASS if kind == "matrix" else "R4_C_APPLICATION_ARCHIVE_BYTES_PASS"
    checked = dict(status=status, **final.bytes_result)
    g.save(output / "archive-check.json", checked)
    return checked, validate(repo, final, identity, kind, matrix)


def main(args):
    repo, output, archive = args.repo.resolve(), args.output.resolve(), args.archive.resolve()
    protected = [v.resolve() for v in (args.source, args.matrix, args.build, *(args.run or ())) if v is not None]
    p.require(not output.exists() and all(not output.is_relative_to(v) for v in [archive] + protected),
              "report must be new/outside archives and runtime inputs")
    if args.action in ("pack-matrix", "repack-matrix", "pack-c"):
        p.require(all(not archive.is_relative_to(v) and not v.is_relative_to(archive) for v in [repo] + protected),
                  "transport archive overlaps source, matrix or runtime inputs")
    identity = p.read(args.identity)
    base.install(repo, identity, physical=args.action in ("pack-matrix", "pack-c"))
    portable, _, _ = e.modules(repo)
    matrix = None
    kind = "c" if args.action.endswith("-c") else "matrix"
    if kind == "c":
        p.require(args.matrix is not None, "C action needs matrix")
        matrix = base.archive_identity(repo, args.matrix.resolve(), args.identity.resolve(), identity)
        validate(repo, matrix, identity, "matrix")
    if args.action == "pack-matrix":
        p.require(args.source is not None and args.support.name == "support-proof.json", "original pack/support required")
        base.validate_support(p.read(args.support), identity)
        e.pack(repo, [r.resolve() for r in args.run], args.source.resolve(), "matrix",
               support=[args.identity.resolve(), args.support.resolve()])
    elif args.action == "pack-c":
        p.require(args.source is not None and args.build is not None and len(args.run) == 1, "C pack source/build/run")
        ce.c_evidence.pack(repo, args.build.resolve(), args.run[0].resolve(), args.source.resolve(), args.matrix.resolve())
    if args.action in ("pack-matrix", "repack-matrix", "pack-c"):
        p.require(args.source is not None, "original source archive required")
        if kind == "matrix":
            base.archive_identity(repo, args.source.resolve(), args.identity.resolve(), identity)
        result, transport = repack(repo, args.source.resolve(), archive, identity, kind, matrix)
    else:
        if kind == "matrix":
            base.archive_identity(repo, archive, args.identity.resolve(), identity)
        transport = validate(repo, portable.Archive(archive), identity, kind, matrix)
        e.EXTRA.add(SELF)
        ce.c_evidence.EXTRA.add(SELF)
        if args.action == "audit-matrix":
            result = e.audit(repo, archive)
        elif args.action == "index-matrix":
            result = e.index_check(repo, archive)
        elif args.action == "audit-c":
            result = ce.c_evidence.audit_archive(repo, archive, args.matrix.resolve())
        else:
            result = ce.c_evidence.index_check(repo, archive)
    outer = dict(contract=base.CONTRACT, transport_contract=CONTRACT, identity_sha256=p.sha(args.identity),
                 hardware_contract=p.CONTRACT, emu_sha256=identity["hardware_profile"]["emu_sha256"],
                 audit_source_sha256=p.sha(base.__file__), transport_source_sha256=p.sha(__file__),
                 historical_fixed_hardware_acceptance=False, historical_b0_h1_acceptance=False,
                 whole_suite_acceptance=False, transport=transport, software_gate_result=result)
    g.save(output, outer)
    return outer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--action", required=True, choices=("pack-matrix", "repack-matrix", "pack-c",
                        "audit-matrix", "audit-c", "index-matrix", "index-c"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--matrix", type=Path)
    parser.add_argument("--build", type=Path)
    parser.add_argument("--run", type=Path, action="append")
    print(json.dumps(main(parser.parse_args()), indent=2))
