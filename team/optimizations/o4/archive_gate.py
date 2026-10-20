"""Portable, fail-closed O4 archive validation independent of Python assertions."""
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(value):
    require(isinstance(value, str) and bool(value) and "\\" not in value and ":" not in value,
            "unsafe evidence path")
    relative = PurePosixPath(value)
    require(not relative.is_absolute() and ".." not in relative.parts and bool(relative.parts)
            and relative.as_posix() == value, "unsafe evidence path")
    devices = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
        prefix + str(index) for prefix in ("COM", "LPT") for index in range(1, 10)}
    require(all(not part.endswith((".", " ")) and part.split(".", 1)[0].upper() not in devices
                for part in relative.parts), "unsafe portable evidence path alias")
    return Path(*relative.parts)


def assessment(work):
    path = Path(work) / "assessment.json"
    require(path.is_file() and not path.is_symlink(), "completed assessment missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict) and value.get("audit_pass") is True,
            "assessment audit has not passed")
    selection = value.get("selection")
    require(isinstance(selection, dict) and set(selection) == {"o1-fu", "o2-fu", "o1-parent", "o2-parent"},
            "incomplete assessment selection")
    names = []
    for pair in selection.values():
        require(isinstance(pair, list) and len(pair) == 2, "invalid assessment selection")
        for name in pair:
            relative = safe_path(name)
            require(len(relative.parts) == 1 and (Path(work) / relative).is_dir()
                    and not (Path(work) / relative).is_symlink(), "selected evidence directory missing or unsafe")
            names.append(name)
    require(len(set(names)) == len(names), "duplicate selected evidence directories")
    return value


def manifest(evidence):
    evidence = Path(evidence)
    require(evidence.is_dir() and not evidence.is_symlink(), "evidence directory missing or symlinked")
    metadata = evidence / "manifest.json"
    require(metadata.is_file() and not metadata.is_symlink(), "manifest missing or symlinked")
    value = json.loads(metadata.read_text(encoding="utf-8"))
    require(isinstance(value, dict) and type(value.get("format")) is int and value["format"] == 1
            and isinstance(value.get("entries"), list) and bool(value["entries"]), "invalid archive manifest")
    logical, stored, logical_folded, stored_folded = set(), set(), set(), set()
    for entry in value["entries"]:
        require(isinstance(entry, dict), "invalid manifest entry")
        path, payload = safe_path(entry.get("path")), safe_path(entry.get("stored"))
        require(path.as_posix() not in logical and payload.as_posix() not in stored,
                "duplicate logical or stored evidence path")
        require(path.as_posix().casefold() not in logical_folded and
                payload.as_posix().casefold() not in stored_folded,
                "case-insensitive evidence path collision")
        logical.add(path.as_posix()); stored.add(payload.as_posix())
        logical_folded.add(path.as_posix().casefold()); stored_folded.add(payload.as_posix().casefold())
        require(type(entry.get("gzip")) is bool, "invalid compression type")
        require(payload.as_posix() == path.as_posix() + (".gz" if entry["gzip"] else ""),
                "logical/stored path mismatch")
        for key in ("bytes", "stored_bytes"):
            require(type(entry.get(key)) is int and entry[key] >= 0, "invalid evidence byte count")
        for key in ("sha256", "stored_sha256"):
            require(isinstance(entry.get(key), str) and re.fullmatch("[0-9a-f]{64}", entry[key]),
                    "invalid evidence digest")
    # A file may not masquerade as another restored file's parent directory.
    for name in logical:
        require(not any(parent.as_posix().casefold() in logical_folded for parent in PurePosixPath(name).parents
                        if parent != PurePosixPath(".")), "conflicting restored evidence paths")
    files = evidence / "files"
    require(files.is_dir() and not files.is_symlink(), "payload directory missing or symlinked")
    actual = set()
    for path in files.rglob("*"):
        require(not path.is_symlink(), "evidence contains symlink")
        if path.is_file():
            actual.add(path.relative_to(files).as_posix())
    require(actual == stored, "missing or unexpected archive payload")
    return value


def restore(evidence, root):
    """Validate the complete inventory before writing only to a new restore root."""
    evidence, root = Path(evidence), Path(root)
    require(root.is_dir() and not root.is_symlink() and not any(root.iterdir()), "restore root must be empty")
    value = manifest(evidence)
    for entry in value["entries"]:
        payload = (evidence / "files" / safe_path(entry["stored"])).read_bytes()
        require(len(payload) == entry["stored_bytes"] and sha(payload) == entry["stored_sha256"],
                "stored evidence identity")
        try:
            raw = gzip.decompress(payload) if entry["gzip"] else payload
        except (OSError, EOFError) as exc:
            raise ValueError("invalid gzip evidence") from exc
        require(len(raw) == entry["bytes"] and sha(raw) == entry["sha256"], "original evidence identity")
        destination = root / safe_path(entry["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    return len(value["entries"])
