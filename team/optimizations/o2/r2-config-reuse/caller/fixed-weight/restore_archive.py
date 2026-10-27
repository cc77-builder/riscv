"""Reassemble the unchanged fixed-weight ZIP from its published byte fragments.

This is a transport step only. It copies the original archive metadata verbatim;
archive.py remains the authority for raw-evidence audit and qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path

FORMAT = "fixed-weight-archive-parts-v1"
FILES = (
    "archive-manifest.json", "original-audit.json",
    "history/commands.json", "history/manifest.json", "history/objects.pack",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_file(root, name):
    path = Path(name)
    require(not path.is_absolute() and ".." not in path.parts,
            "relative archive member required")
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root), "archive member escapes source")
    require(resolved.is_file(), "missing archive member: " + name)
    return resolved


def restore(source, output):
    source, output = source.resolve(), output.resolve()
    require(not output.exists(), "fresh output directory required")
    require(not output.is_relative_to(source), "output must be outside archive input")
    transport_path = source / "transport.json"
    transport_bytes = transport_path.read_bytes()
    transport = json.loads(transport_bytes)
    require(transport["format"] == FORMAT, "unsupported transport format")
    require(transport["artifact"] == "payload.zip", "fixed ZIP artifact")
    require(set(transport["metadata"]) == set(FILES), "exact original metadata inventory")

    metadata = {}
    for name in FILES:
        raw = source_file(source, name).read_bytes()
        pin = transport["metadata"][name]
        require(len(raw) == pin["bytes"] and digest(raw) == pin["sha256"],
                "original metadata identity: " + name)
        metadata[name] = raw
    manifest = json.loads(metadata["archive-manifest.json"])
    require(manifest["contract"] == "r2-s3-fixed-weight-8x32-v1" and
            manifest["format"] == "split-evidence-zip-v1", "original archive contract")
    require(transport["bytes"] == manifest["stored_bytes"] and
            transport["sha256"] == manifest["payload_sha256"], "original ZIP binding")
    parts = transport["parts"]
    require(bool(parts), "nonempty ordered fragment list")
    require([p["path"] for p in parts] ==
            [f"payload.zip.part-{i:04d}" for i in range(1, len(parts) + 1)],
            "exact ordered fragment names")
    require(all(isinstance(p["bytes"], int) and p["bytes"] > 0 for p in parts) and
            sum(p["bytes"] for p in parts) == transport["bytes"], "complete fragment sizes")
    paths = [source_file(source, part["path"]) for part in parts]
    for path, part in zip(paths, parts):
        require(path.stat().st_size == part["bytes"], "fragment size: " + part["path"])

    output.mkdir(parents=True, exist_ok=False)
    incomplete = output / "payload.zip.incomplete"
    full_hash = hashlib.sha256()
    total = 0
    with incomplete.open("xb") as dest:
        for path, part in zip(paths, parts):
            part_hash = hashlib.sha256()
            count = 0
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    part_hash.update(block)
                    full_hash.update(block)
                    count += len(block)
                    total += len(block)
                    dest.write(block)
            require(count == part["bytes"] and part_hash.hexdigest() == part["sha256"],
                    "fragment identity: " + part["path"])
    require(total == transport["bytes"] and full_hash.hexdigest() == transport["sha256"],
            "reassembled ZIP differs from original")
    incomplete.rename(output / "payload.zip")
    for name, raw in metadata.items():
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    receipt = dict(
        status="FIXED_WEIGHT_ORIGINAL_ARCHIVE_RESTORED",
        transport_format=FORMAT, source=str(source), output=str(output),
        transport_sha256=digest(transport_bytes),
        payload_sha256=full_hash.hexdigest(), payload_bytes=total,
        fragments=len(parts), metadata=transport["metadata"], new_emu_runs=0,
        qualification="Transport identity only; run unchanged archive.py for evidence audit",
    )
    (output / "transport-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path,
                        default=Path(__file__).resolve().parent / "evidence/qualified-v1/runtime")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(restore(args.archive, args.output), indent=2))
