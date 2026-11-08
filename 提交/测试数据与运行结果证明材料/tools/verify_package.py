"""校验证明材料包。

python tools/verify_package.py            按 包文件校验清单.json 核对全部文件，并检查原始日志与波形是否齐全
python tools/verify_package.py --update   补入或更换文件后重新生成清单（只在确认文件无误后使用）

原始日志和波形文件既可以是原文件，也可以是 .gz 压缩文件；压缩文件按解压后的内容与原始运行记录中的 SHA-256 比较。
"""
from pathlib import Path
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "包文件校验清单.json"

# 文中引用的原始文件，及其在原始运行记录中登记的 SHA-256。
REQUIRED = [
    ("evidence/F10_basic-test-logs/functional-0-run.log",
     "5bd56636056d7b8c77ab976511522c6654c112644f0ea024dfac99bb92f855f7", "evidence/F01__result.json"),
    ("evidence/F10_basic-test-logs/functional-2-run.log",
     "90b36b19e9d141e1b0bdad6bed461b4dbde4e534798f5fbdaa8819d9e2ef3211", "evidence/F02__result.json"),
    ("evidence/W01_vdot-wave-20261105/vdot-positive.fst",
     "14822fb02ea28319253cb9ea118c6df143844f1c057c54a610c34865ff03bcb2",
     "evidence/W01_vdot-wave-20261105/wave-capture-verification.json"),
    ("evidence/W01_vdot-wave-20261105/run.log",
     "0b34ad0216a726d9cff45c28f41dbbf3dcce437d49e20fa0709de703bd5ebdcf",
     "evidence/W01_vdot-wave-20261105/wave-capture-verification.json"),
]


def sha256(path, decompress=False):
    h = hashlib.sha256()
    opener = gzip.open if decompress else open
    with opener(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p != MANIFEST and "__pycache__" not in p.parts:
            yield p


def update():
    entries = [{"path": p.relative_to(ROOT).as_posix(), "size": p.stat().st_size, "sha256": sha256(p)} for p in files()]
    MANIFEST.write_text(json.dumps({"files": entries}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("MANIFEST_UPDATED", len(entries))


def check_required():
    ok = True
    for rel, expected, source in REQUIRED:
        plain, packed = ROOT / rel, ROOT / (rel + ".gz")
        if plain.is_file():
            actual = sha256(plain)
        elif packed.is_file():
            actual = sha256(packed, decompress=True)
        else:
            print(f"MISSING  {rel}（SHA-256 见 {source}）")
            ok = False
            continue
        if actual != expected:
            print(f"MISMATCH {rel}: {actual}，原始记录为 {expected}")
            ok = False
        else:
            print(f"OK       {rel}")
    return ok


def verify():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    listed = {e["path"] for e in manifest}
    for e in manifest:
        p = ROOT / e["path"]
        if not p.is_file():
            sys.exit("MISSING: " + e["path"])
        if p.stat().st_size != e["size"] or sha256(p) != e["sha256"]:
            sys.exit("CHANGED: " + e["path"])
    extra = [p.relative_to(ROOT).as_posix() for p in files() if p.relative_to(ROOT).as_posix() not in listed]
    if extra:
        sys.exit("NOT IN MANIFEST: " + ", ".join(extra[:10]))
    print("PACKAGE_FILES_PASS", len(manifest))
    if not check_required():
        sys.exit("REQUIRED_FILES_INCOMPLETE")
    print("REQUIRED_FILES_PASS", len(REQUIRED))


if __name__ == "__main__":
    update() if "--update" in sys.argv else verify()
