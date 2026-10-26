"""Strict current-0f input contract; unrelated historical T17 locks stay unchanged."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

CONTRACT = "zjh-current-clean-build-v1"
BASELINE_SOURCE = "0f12df675378556670afd0dd2153f47fcb330610"
BASELINE_SHA = "388e286327006c7a58494d434370aaaf7c36815f1abeaa517c40754c4e620bc5"
HELPER = "8a66fb75324ee1834401ec71b5c578141de6268a074253d37eb5494046c932d0"
EXEUNIT = "src/main/scala/xiangshan/backend/exu/ExeUnit.scala"
EXEUNIT_SHA = "fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa"
AUX = {"constantin.txt": "a1fd1d4de05919fec0257bacb550a3622c0f4ec2373e5cf230fc4233fb98c1bf",
       "plusArgs": "160d9702d313cbe66be84ae88c2f45c3df9ed7b61b65e3ddeea25133ac6765ff"}
FLASH = "a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994"
FLAGS = {"VDOT_O2_ELASTIC": "1", "VDOT_O1_HANDOFF": "0", "VDOT_O1_TRACE": "0",
         "VDOT_T14_FUSED_INPUT": "1", "VDOT_O2_TRACE": "1", "VDOT_T12_TRACE": "0", "VDOT_T13_TRACE": "1"}
GENERATED_SCOPE = "all regular files recursively below build; symlinks forbidden"
ADAPTER_NAMES = ("current_clean_common.py", "current_clean_build.py", "current_clean_profile.py")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for raw in iter(lambda: stream.read(1048576), b""):
            digest.update(raw)
    return digest.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])

def baseline(path):
    require(sha(path) == BASELINE_SHA, "current 0f baseline inventory SHA differs")
    value = read(path)
    require(value["source_commit"] == BASELINE_SOURCE and
            len(value["files"]) == 429 and len(value["dependency_files"]) == 21236 and
            value["files"][EXEUNIT] == EXEUNIT_SHA, "not selected current 0f hardware baseline")
    return value

def helper(repo):
    path = Path(repo) / "team/optimizations/o2/fullcore/build_fullcore.py"
    require(sha(path) == HELPER, "frozen snapshot helper changed")
    spec = importlib.util.spec_from_file_location("current_clean_snapshot", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    require(value.ROOT == Path(repo).resolve(), "snapshot helper checkout differs")
    return value

def snapshot(repo, expected, require_clean=True):
    repo = Path(repo).resolve()
    b = helper(repo)
    if require_clean:
        require(not git(repo, "diff", "HEAD", "--", *b.HARDWARE), "uncommitted hardware input")
        require(not git(repo, "ls-files", "--others", "--exclude-standard", "--", *b.HARDWARE),
                "untracked hardware input")
    files = {}
    for raw in git(repo, "ls-files", "-z", "--", *b.HARDWARE).split(b"\0"):
        if raw and (repo / raw.decode()).is_file():
            files[raw.decode()] = sha(repo / raw.decode())
    dependencies, dependency_files = b.dependency_snapshot()
    require(files == expected["files"] and dependency_files == expected["dependency_files"],
            "hardware/recursive dependencies differ from selected 0f baseline")
    require(len(dependencies) == 126, "dependency repository inventory differs")
    return dict(sorted(files.items())), dependencies, dependency_files

def generated_inventory(repo):
    repo = Path(repo).resolve()
    require((repo / "build").is_dir(), "missing generated build directory")
    values = []
    for path in sorted((repo / "build").rglob("*")):
        require(not path.is_symlink(), "generated symlink is not self-contained: " + str(path))
        if path.is_file():
            values.append(dict(path=path.relative_to(repo).as_posix(),
                               bytes=path.stat().st_size, sha256=sha(path)))
    require(any(row["path"] == "build/emu" for row in values), "inventory omits EMU")
    return sorted(values, key=lambda row: row["path"])

def validate_generated(rows):
    require(isinstance(rows, list) and bool(rows), "empty generated inventory")
    paths = []
    for row in rows:
        rel = Path(row["path"])
        require(set(row) == {"path", "bytes", "sha256"} and not rel.is_absolute()
                and ".." not in rel.parts and len(rel.parts) >= 2 and rel.parts[0] == "build"
                and type(row["bytes"]) is int and row["bytes"] >= 0
                and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]), "invalid generated inventory row")
        paths.append(row["path"])
    require(len(paths) == len(set(paths)) and paths == sorted(paths) and "build/emu" in paths,
            "duplicate, unsorted or missing generated inventory")
    require(all("build/" + name in paths for name in AUX), "generated inventory omits required AUX")

def adapter_sources(directory):
    directory = Path(directory)
    return {name: sha(directory / name) for name in ADAPTER_NAMES}
