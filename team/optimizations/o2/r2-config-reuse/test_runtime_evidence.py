"""Reject coherently rehashed S3 probe archives without running a simulator."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timedelta
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import runtime_evidence as e

g, a = e.g, e.a


def reject(action, expected):
    try:
        action()
    except ValueError as exc:
        message = str(exc)
        g.require(expected in message, "unexpected rejection: " + message)
        return message
    raise ValueError("corrupted archive accepted: " + expected)


class EditedArchive:
    def __init__(self, path, portable):
        self.path, self.portable = path, portable
        self.meta = a.read(path / "archive-manifest.json")
        self.records = portable.Archive(path).records

    def json(self, logical):
        return json.loads(self.raw(logical))

    def raw(self, logical):
        row = self.records[logical]
        raw = (self.path / row["stored"]).read_bytes()
        return gzip.decompress(raw) if row["encoding"] == "gzip" else raw

    def replace(self, logical, raw):
        old = self.records[logical]
        row = next(r for r in self.meta["files"] if r["stored"] == old["stored"])
        encoded = gzip.compress(raw, compresslevel=9, mtime=0) if row["encoding"] == "gzip" else raw
        (self.path / row["stored"]).write_bytes(encoded)
        row.update(raw_bytes=len(raw), raw_sha256=e.digest(raw),
                   stored_bytes=len(encoded), stored_sha256=e.digest(encoded))

    def replace_json(self, logical, value):
        self.replace(logical, e.json_bytes(value))

    def reseal(self):
        raw = e.json_bytes(self.meta)
        (self.path / "archive-manifest.json").write_bytes(raw)
        (self.path / "archive-manifest.sha256").write_text(e.digest(raw) + "  archive-manifest.json\n")
        proof = dict(status=e.BYTE_PASS, **self.portable.Archive(self.path).bytes_result)
        g.save(self.path / "archive-check.json", proof)
        return proof


def check(repo, archive):
    good = e.audit(repo, archive)
    g.require(good["qualification_scope"] == "probe", "rejection fixture must be the real probe")
    portable = g.load("s3_evidence_test_portable", repo / e.PORTABLE)
    metadata = a.read(archive / "archive-manifest.json")
    campaign = "campaigns/" + next(iter(metadata["campaigns"]))
    outcomes = []

    def promote(value):
        value.meta["qualification_scope"] = "matrix"

    def summary(value):
        logical = campaign + "/results.json"
        data = value.json(logical)
        data["rows"][0]["fastest_rvv"]["total"] += 1
        value.replace_json(logical, data)

    def baseline_payload(value):
        logical = next(n for n in value.records if n.startswith("tools/") and
                       "/matrix-archive/" in n and n.endswith("vdot-perf.bin.gz"))
        raw = bytearray(value.raw(logical))
        raw[-1] ^= 1
        value.replace(logical, bytes(raw))

    def closure(value):
        logical = campaign + "/runtime-inputs.json"
        data = value.json(logical)
        key = next(n for n in data if "/matrix-archive/" in n and n.endswith("vdot-perf.bin.gz"))
        del data[key]
        value.replace_json(logical, data)

    def replay_overlap(value):
        logical = campaign + "/results.json"
        cached = value.json(logical)
        replay = next(r for r in cached["runs"] if r["replay"] == 1)
        formal = next(r for r in cached["runs"] if r["name"] == replay["name"] and r["replay"] == 0)
        replay["started"] = (datetime.fromisoformat(formal["finished"]) - timedelta(microseconds=1)).isoformat()
        label = Path(replay["cwd"]).parent.name
        value.replace_json(campaign + "/runs/" + label + "/result.json", replay)
        value.replace_json(logical, cached)
        value.replace_json(campaign + "/completed-runs.json", cached["runs"])

    cases = (
        ("probe-promoted-to-matrix", promote, "archive cohort differs"),
        ("forged-fastest-rvv-summary", summary, "cached statistics differ"),
        ("changed-sealed-baseline-payload", baseline_payload, "sealed association"),
        ("missing-baseline-runtime-input", closure, "runtime input inventory differs"),
        ("overlapping-normal-replay", replay_overlap, "execution order differs"),
    )
    with tempfile.TemporaryDirectory(prefix="s3-evidence-rejections-") as temp:
        for label, mutate, expected in cases:
            target = Path(temp) / label
            shutil.copytree(archive, target)
            edited = EditedArchive(target, portable)
            mutate(edited)
            bytes_pass = edited.reseal()
            reason = reject(lambda: e.audit(repo, target), expected)
            outcomes.append(dict(case=label, self_consistent_bytes_pass=bytes_pass["status"], rejection=reason))

    before = {p.relative_to(archive).as_posix(): g.sha(p) for p in archive.rglob("*") if p.is_file()}
    result = subprocess.run([sys.executable, "-B", str(repo / g.S3 / "runtime_evidence.py"),
        "--repo", str(repo), "--action", "audit", "--archive", str(archive),
        "--output", str(archive / "forbidden-audit.json")], capture_output=True, text=True)
    g.require(result.returncode != 0 and "output overlaps protected input" in result.stderr,
              "archive output protection not enforced")
    after = {p.relative_to(archive).as_posix(): g.sha(p) for p in archive.rglob("*") if p.is_file()}
    g.require(before == after, "rejected CLI wrote into archive")
    return dict(status="S3_RUNTIME_EVIDENCE_REJECTIONS_PASS", source_sha256=g.sha(Path(__file__)),
                reference_manifest_sha256=g.sha(archive / "archive-manifest.json"),
                valid_archive_pass=good["status"], coherently_rehashed_cases=outcomes,
                cli_archive_output_rejected_without_write=True, new_emu_runs=0, new_compilations=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, archive, output = [p.resolve() for p in (args.repo, args.archive, args.output)]
    g.require(repo == a.ROOT and not output.exists(), "selected source and fresh test output required")
    portable = g.load("s3_evidence_test_input", repo / e.PORTABLE)
    cfg = portable.Archive(archive).json("parent-identity.json")["configuration"]
    a.outside_inputs(output, [repo, archive, cfg["hardware_source"], cfg["build_record"], cfg["am_home"]])
    result = check(repo, archive)
    g.save(output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
