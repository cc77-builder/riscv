"""Reject semantically damaged evidence even after its archive hashes refresh."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import shutil
import tempfile

import firstdot_evidence as e


def alter(archive, logical, change):
    path = archive / "archive-manifest.json"
    manifest = e.a.read(path)
    selected = []
    for row in manifest["files"]:
        name = str(Path(row["stored"]).relative_to("files"))
        if row["encoding"] == "gzip":
            name = name[:-3]
        if name == logical:
            selected.append(row)
    assert len(selected) == 1
    row = selected[0]
    target = archive / row["stored"]
    raw = target.read_bytes()
    if row["encoding"] == "gzip":
        raw = gzip.decompress(raw)
    value = json.loads(raw)
    change(value)
    raw = e.json_bytes(value)
    encoded = gzip.compress(raw, compresslevel=9, mtime=0) if row["encoding"] == "gzip" else raw
    target.write_bytes(encoded)
    row.update(raw_bytes=len(raw), raw_sha256=e.digest(raw), stored_bytes=len(encoded), stored_sha256=e.digest(encoded))
    raw = e.json_bytes(manifest)
    path.write_bytes(raw)
    (archive / "archive-manifest.sha256").write_text(e.digest(raw) + "  archive-manifest.json\n")


def check(repo, source):
    good = e.audit(repo, source)
    meta = e.a.read(source / "archive-manifest.json")
    probe = next(name for name in meta["campaigns"] if any(
        row["original"] == meta["campaigns"][name] + "/negative-fixture/fixture.json" for row in meta["files"]))
    prefix = "campaigns/" + probe
    changes = {
        "cached-performance": (prefix + "/results.json", lambda value: value["rows"][0]["firstdot_reuse_vdot"].update(mean=-1)),
        "normal-exit": (prefix + "/runs/recovery-firstdot-8x32/result.json", lambda value: value.update(exit_code=1)),
        "negative-destination": (prefix + "/runs/negative-firstdot-8x32/negative.json", lambda value: value.update(vd=20)),
        "false-full-matrix": (prefix + "/results.json", lambda value: value["qualification"].update(full_matrix=True)),
    }
    rejected = []
    with tempfile.TemporaryDirectory(prefix="firstdot-evidence-reject-") as temp:
        for name, (logical, change) in changes.items():
            dest = Path(temp) / name
            shutil.copytree(source, dest)
            alter(dest, logical, change)
            try:
                e.audit(repo, dest)
            except ValueError as exc:
                rejected.append(dict(case=name, reason=str(exc)))
            else:
                raise AssertionError("semantic corruption accepted: " + name)
    return dict(status="FIRSTDOT_EVIDENCE_REJECTION_PASS", valid_archive_status=good["status"],
                archive_manifest_sha256=good["archive"]["archive_manifest_sha256"],
                rehashed_semantic_corruptions=rejected, new_emu_runs=0, new_nemu_runs=0)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    value = check(a.repo.resolve(), a.archive.resolve())
    e.g.save(a.output, value)
    print(json.dumps(value, indent=2))
