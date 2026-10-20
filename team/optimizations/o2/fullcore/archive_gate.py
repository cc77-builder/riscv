"""Fail-closed byte archive validation, including optimized Python execution."""
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(name):
    require(isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name,
            "unsafe archive path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == name
            and len(path.parts) > 1 and path.parts[0] == "files", "unsafe archive path")
    return Path(*path.parts)


def verify(output):
    output = Path(output)
    require((output / "archive-manifest.json").is_file() and
            (output / "archive-manifest.sha256").is_file(), "archive metadata missing")
    data = (output / "archive-manifest.json").read_bytes()
    digest = (output / "archive-manifest.sha256").read_text(encoding="ascii")
    require(digest == sha(data) + "  archive-manifest.json\n", "archive manifest digest mismatch")
    manifest = json.loads(data)
    require(isinstance(manifest, dict) and type(manifest.get("version")) is int
            and manifest["version"] == 1 and isinstance(manifest.get("files"), list)
            and bool(manifest["files"]), "invalid archive manifest schema")
    expected = set()
    for record in manifest["files"]:
        require(isinstance(record, dict), "invalid archive record")
        relative = safe_path(record.get("stored"))
        name = relative.as_posix()
        require(name not in expected, "duplicate archive path")
        expected.add(name)
        require(record.get("encoding") in ("identity", "gzip"), "unknown archive encoding")
        for key in ("raw_bytes", "stored_bytes"):
            require(type(record.get(key)) is int and record[key] >= 0, "invalid archive byte count")
        for key in ("raw_sha256", "stored_sha256"):
            require(isinstance(record.get(key), str) and re.fullmatch("[0-9a-f]{64}", record[key]),
                    "invalid archive payload digest")
        path = output / relative
        require(not any(parent.is_symlink() for parent in (path, *path.parents) if parent != output.parent),
                "archive contains symlink")
        require(path.is_file(), "archive payload missing")
        stored = path.read_bytes()
        require(len(stored) == record["stored_bytes"] and sha(stored) == record["stored_sha256"],
                "stored archive bytes differ")
        try:
            raw = gzip.decompress(stored) if record["encoding"] == "gzip" else stored
        except (OSError, EOFError) as exc:
            raise ValueError("invalid gzip archive payload") from exc
        require(len(raw) == record["raw_bytes"] and sha(raw) == record["raw_sha256"],
                "raw archive bytes differ")
    actual = set()
    for path in (output / "files").rglob("*"):
        require(not path.is_symlink(), "archive contains symlink")
        if path.is_file():
            actual.add(path.relative_to(output).as_posix())
    require(actual == expected, "missing or unexpected archive file")
    return dict(files=len(expected), raw_bytes=sum(r["raw_bytes"] for r in manifest["files"]),
                stored_bytes=sum(r["stored_bytes"] for r in manifest["files"]),
                archive_manifest_sha256=sha(data))
