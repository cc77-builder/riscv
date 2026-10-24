"""Thin config-reuse ordinary-C archive adapter over the frozen R4 evidence code."""
from __future__ import annotations

import argparse
from pathlib import Path
import types
import json

import c_api as c
import runtime_evidence as e

g, a = c.g, c.a
PARENT = g.ENTRY / "entry_c_evidence.py"
PARENT_SHA = "166186d7e9114729bb042b2cee3e719f6fe56150077aca905b657fe0e703362f"


def adapter(repo, identity, matrix):
    g.require(g.sha(repo / PARENT) == PARENT_SHA and Path(__file__).resolve() == repo / g.S3 / "c_evidence.py",
              "ordinary C evidence adapter identity")
    portable, _, _, helpers, _ = e.modules(repo, identity)
    app = c.adapter(repo, identity)
    original_audit = app.audit_run
    def audit_run(root, build, run, external=None):
        proof = original_audit(root, build, run, external)
        anchor = c.library_anchor(root, build, matrix)
        c.validate_qualification(build, run, anchor)
        return proof
    app.audit_run = audit_run
    parent = g.load("s3_private_c_evidence", repo / PARENT)
    proxy = types.SimpleNamespace(**vars(g.parent))
    proxy.ENTRY = c.PUBLIC.parent
    parent.g, parent.a, parent.c, parent.CONTRACT = proxy, app.a, app, c.CONTRACT
    parent.EXTRA = {str(PARENT)} | {str(g.S3 / n) for n in
        ("c_api.py", "c_evidence.py", "C_CONTRACT.md", "test_c_api.py")}
    parent.EXTRA |= {str(c.PUBLIC / n) for n in ("gemv.S", "gemv.h")}
    def byte_check(root, path):
        opened = portable.Archive(path)
        g.require(opened.manifest["contract"] == e.c.CONTRACT and opened.manifest["qualification_scope"] == "matrix",
                  "config-reuse C needs full matrix anchor")
        result = dict(status=e.BYTE_PASS, **opened.bytes_result)
        g.require(a.read(path / "archive-check.json") == result, "matrix cached bytes differ")
        return result
    evidence = types.SimpleNamespace(digest=e.digest, json_bytes=e.json_bytes, include=e.include,
        byte_check=byte_check, audit=e.audit, fixture_identity=helpers.fixture_identity)
    def modules(root):
        g.require(root == repo, "C archive checkout changed")
        c.source_files(root)
        return evidence, portable
    parent.archive_modules = modules
    return parent, portable


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--matrix", type=Path, required=True)
    p.add_argument("--action", choices=("pack", "audit", "bytes"), required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--build", type=Path)
    p.add_argument("--run", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    repo, matrix, archive = args.repo.resolve(), args.matrix.resolve(), args.archive.resolve()
    g.require(repo == a.ROOT, "selected C evidence checkout differs")
    identity = a.parent_identity(repo, args.identity.resolve())
    parent, portable = adapter(repo, identity, matrix)
    if args.action == "pack":
        g.require(args.build and args.run and not archive.exists(), "new C archive/build/run required")
        cfg = identity["configuration"]
        a.outside_inputs(archive, [repo, matrix, args.build.resolve(), args.run.resolve(), args.identity.resolve().parent,
                                  cfg["hardware_source"], cfg["build_record"], cfg["am_home"]])
        proof = parent.pack(repo, args.build.resolve(), args.run.resolve(), archive, matrix)
        result = dict(status="S3_C_APPLICATION_ARCHIVE_SEALED", contract=c.CONTRACT, proof=proof)
    else:
        g.require(args.output and not args.output.exists(), "new C audit output required")
        a.outside_inputs(args.output.resolve(), [repo, matrix, archive])
        if args.action == "audit":
            proof = parent.audit_archive(repo, archive, matrix)
            result = dict(status="S3_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS", contract=c.CONTRACT, proof=proof)
        else:
            opened = portable.Archive(archive)
            g.require(opened.manifest["contract"] == c.CONTRACT and
                      opened.manifest["matrix_manifest_sha256"] == g.sha(matrix / "archive-manifest.json"), "C archive identity")
            proof = dict(status="R4_C_APPLICATION_ARCHIVE_BYTES_PASS", **opened.bytes_result)
            g.require(a.read(archive / "archive-check.json") == proof, "cached C byte check differs")
            result = dict(status="S3_C_APPLICATION_ARCHIVE_BYTES_PASS", contract=c.CONTRACT, proof=proof)
        g.save(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
