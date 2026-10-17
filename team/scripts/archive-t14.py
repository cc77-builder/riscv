"""Archive a completed T14 campaign without modifying live simulation evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save(path, value):
    path.write_bytes((json.dumps(value, indent=2) + "\n").encode())


def archive(base, output):
    run = base / "runs/fullcore-02"
    require(load(run / "campaign-state.json")["status"] == "T14_CANDIDATE_FULLCORE_PASS", "campaign incomplete")
    require(load(base / "runs/ablation-01/result.json")["status"] == "T14_IDENTICAL_IMAGE_ABLATION_PASS", "ablation incomplete")
    require(load(base / "runs/structure-01.json")["status"] == "T14_STRUCTURE_AUDIT_PASS", "structure incomplete")
    state = load(run / "campaign-state.json")
    require(sha(ROOT / "team/scripts/t14-resume.py") == state["driver_sha256"], "campaign driver changed")
    for name, digest in state["external_files"].items():
        require(sha(Path(name)) == digest, "runtime external artifact changed")
    output.mkdir(parents=True, exist_ok=False)
    copied = []

    def copy(source, relative, compress=False):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        if compress:
            target = Path(str(target) + ".gz")
            target.write_bytes(gzip.compress(raw, mtime=0))
        else:
            target.write_bytes(raw)
        if not compress and source.suffix == ".gz":
            raw = gzip.decompress(raw)
        copied.append(dict(path=target.relative_to(output).as_posix(), sha256=sha(target),
                           raw_sha256=hashlib.sha256(raw).hexdigest(), raw_bytes=len(raw)))

    def tree(source, relative, predicate=lambda path: True):
        for path in sorted(source.rglob("*")):
            if path.is_file() and predicate(path.relative_to(source)):
                copy(path, Path(relative) / path.relative_to(source), path.suffix == ".log")

    # T12 keeps its existing checker layout; inputs are the frozen original corpus.
    old_t12 = ROOT / "team/evidence/t12-regression-20261014"
    tree(old_t12 / "matrix", "t12/matrix")
    control = base / "runs/control-sweep-02"
    for name in ("manifest.json", "sequences.S", "sequences.h"):
        copy(control / "data" / name, Path("t12/control") / name, True)
    tree(control, "control-sweep/build", lambda rel: "objects" not in rel.parts)
    for variant in ("baseline", "candidate"):
        tree(base / ("runs/control-sweep-" + variant + "-02"), Path("control-sweep") / variant)
    tree(base / "runs/fullcore-01/t12/control", "historical/original-control")
    for name in ("campaign-state.json", "t12/result.json", "t12-command.json", "t12-driver.log"):
        copy(base / "runs/fullcore-01" / name, Path("historical/original-campaign") / name, name.endswith(".log"))
    for path in sorted((run / "t12").rglob("*")):
        if path.is_file():
            copy(path, Path("t12/suite") / path.relative_to(run / "t12"),
                 path.suffix == ".log" or path.name == "hardware-pins.json")
    for group in ("calibration", "analysis", "performance"):
        tree(run / group, Path("fullcore") / group)
    for name in ("campaign-state.json", "calibration-check.json", "t12-reuse-receipt.json"):
        copy(run / name, Path("fullcore") / name, name.endswith(".log"))
    for group in ("input", "calibration-input"):
        tree(run / group, Path("fullcore") / group)
    tree(base / "runs/ablation-01", "ablation")
    tree(base / "build-evidence", "hardware-build")
    for variant in ("baseline", "fused"):
        source = base / ("runs/fu-" + variant + "-01")
        tree(source, Path("fu") / variant,
             lambda rel: not any(part in ("obj_dir", "__pycache__") for part in rel.parts))
    old_fu = Path(load(base / "runs/structure-01.json")["source_files"]["old"]["path"])
    copy(old_fu, "fu/original/VDotFuTestTop.sv")
    for path in sorted((base / "runs").iterdir()):
        if path.is_file() and path.suffix in (".json", ".log", ".txt"):
            copy(path, Path("support") / path.name, path.suffix == ".log")

    t12_entries = [item for item in copied if item["path"].startswith("t12/")]
    save(output / "t12/archive-manifest.json", dict(
        files={item["path"][4:]: item["sha256"] for item in t12_entries},
        raw_log_sha256={item["path"][4:]: item["raw_sha256"] for item in t12_entries
                        if item["path"].endswith(".log.gz")}))
    save(output / "external-artifacts.json", state["external_files"])
    dependencies = {
        name: sha(ROOT / "team/evidence" / name / manifest)
        for name, manifest in (("t12-regression-20261014", "archive-manifest.json"),
                               ("t13-performance-20261015", "file-manifest.json"))
    }
    save(output / "dependencies.json", dependencies)
    save(output / "archive-files.json", dict(version=1, files=copied,
         scope="Lossless raw streams and receipts. EMU/NEMU/flash are external SHA pins. Existing T13 archive supplies identical compiled images."))
    (output / ".gitattributes").write_bytes(b"* -text -whitespace\n")
    (output / ".gitignore").write_bytes(b"!**/\n!*.log.gz\n!*.json\n!*.csv\n!*.txt\n!*.sv\n!*.tsv\n")
    (output / "README.md").write_text(
        "# T14 本地消融证据\n\n"
        "入口：../../scripts/verify-t14-archive.py。原始日志无损 gzip 压缩，mtime=0。\n"
        "fu/ 为两模式单元验证；t12/ 为候选全核回归；fullcore/ 为校准与固定镜像性能运行；ablation/ 为同镜像比较。\n"
        "hardware-build/ 固定实际硬件源码、构建命令和 EMU 摘要；support/ 保留主机检查与结构审计。\n"
        "编译镜像复用相邻 t13-performance-20261015；不重复打包构建缓存或大型模拟器。\n"
        "离线复算只检查已保存的运行证据，不等于重新运行硬件。未经综合/STA，不能推导面积、Fmax 或功耗。\n",
        encoding="utf-8")
    save(output / "file-manifest.json", dict(files={
        path.relative_to(output).as_posix(): sha(path)
        for path in sorted(output.rglob("*")) if path.is_file()}))
    return dict(status="T14_ARCHIVED", files=len(copied),
                bytes=sum(p.stat().st_size for p in output.rglob("*") if p.is_file()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(archive(args.base.resolve(), args.output.resolve())))
