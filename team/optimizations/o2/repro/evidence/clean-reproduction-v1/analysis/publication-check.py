"""Check the exact staged T17 source, documents and evidence before publication."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError("Run this staged-byte check without Python optimization")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--git", default="git")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
repo, output = args.repo.resolve(), args.output.resolve()
prefix = "team/optimizations/o2/repro/"
evidence = repo / prefix / "evidence/clean-reproduction-v1"
assert output.parent == evidence and not output.exists()
expected = {prefix + n for n in (
    ".gitattributes", "README.md", "CLEAN_CONTRACT.md", "CLEAN_REPRODUCE.md", "CLEAN_RESULT.md",
    "clean-config.example.json", "clean_prepare.py", "clean_build.py", "clean_support.py",
    "clean_profile.py", "clean_entry.py", "clean_fullcore.py", "clean_evidence.py",
    "clean_fullcore_evidence.py", "test_clean_evidence.py", "clean_portable_evidence.py")}
expected |= {"team/docs/development-route-current.md", "开发计分板.md"}
assert not any(p.is_symlink() for p in evidence.rglob("*"))
expected |= {p.relative_to(repo).as_posix() for p in evidence.rglob("*") if p.is_file()}


def git(*argv, data=None):
    return subprocess.check_output([args.git, "-C", str(repo), *argv], input=data)


changed = {p.decode() for p in git("diff", "--cached", "--name-only", "-z").split(b"\0") if p}
assert changed == expected, {"missing": sorted(expected - changed), "extra": sorted(changed - expected)}
entries = {}
for row in git("ls-files", "--stage", "-z", "--", prefix,
               "team/docs/development-route-current.md", "开发计分板.md").split(b"\0"):
    if not row:
        continue
    metadata, raw_name = row.split(b"\t", 1)
    mode, oid, stage = metadata.decode().split()
    name = raw_name.decode()
    if name not in expected:
        continue
    assert mode == "100644" and stage == "0" and name not in entries, name
    entries[name] = oid
assert set(entries) == expected
stream = io.BytesIO(git("cat-file", "--batch", data="".join(entries[n] + "\n" for n in sorted(entries)).encode()))
hashes, total = {}, 0
for name in sorted(entries):
    header = stream.readline().split()
    assert len(header) == 3 and header[0].decode() == entries[name] and header[1] == b"blob", name
    raw = stream.read(int(header[2]))
    assert stream.read(1) == b"\n" and raw == (repo / name).read_bytes(), name
    hashes[name] = hashlib.sha256(raw).hexdigest()
    total += len(raw)
assert not stream.read(), "extra staged object bytes"
result = dict(status="T17_COMPLETE_STAGED_DELIVERY_PASS", head=git("rev-parse", "HEAD").decode().strip(),
              checked_files=len(entries), checked_bytes=total, file_sha256=hashes, new_emu_runs=0,
              scope="Exact selected source/docs/archives/reports; this new report is staged and checked separately.")
output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode())
print(json.dumps({k: v for k, v in result.items() if k != "file_sha256"}, ensure_ascii=False))
