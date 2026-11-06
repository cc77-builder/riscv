#!/usr/bin/env python3
"""Package existing dot16 raw evidence once; never run a validator or test."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(value, out, indent=2, ensure_ascii=False)
        out.write("\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--runs", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--windows-output", type=Path, required=True)
    p.add_argument("--receipts", type=Path, required=True)
    args = p.parse_args()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert os.sched_getaffinity(0) == {1}, "archive must use assigned CPU1"
    assert not args.output.exists(), "refuse to replace an existing archive directory"
    assert args.windows_output.is_dir(), "Windows metadata staging directory must exist"
    runs = ["flag0-01", "flag0-02", "flag1-01", "parent-flag0-01", "parent-flag1-01",
            "decode-flag0-01", "decode-flag0-02", "decode-flag1-01"]
    receipts = json.loads(args.receipts.read_text(encoding="utf-8-sig"))
    assert set(receipts["runs"]) == set(runs)
    selected = {}
    omitted = {}
    run_summary = {}

    def add(path, name):
        assert path.is_file() and not path.is_symlink(), str(path)
        assert name not in selected, name
        selected[name] = path

    for run in runs:
        root = args.runs / run
        assert root.is_dir() and not root.is_symlink(), str(root)
        status = json.loads((root / "status.json").read_text())
        binaries = []
        for rel in ("campaign/artifacts.json", "artifact.json"):
            f = root / rel
            if f.exists():
                a = json.loads(f.read_text())
                rows = a if isinstance(a, list) else [a]
                for row in rows:
                    if isinstance(row, dict) and "path" in row:
                        candidate = Path(row["path"])
                        if not candidate.is_absolute():
                            candidate = f.parent / candidate
                        candidate = candidate.resolve()
                        candidate.relative_to(root)
                        assert digest(candidate) == row["sha256"], str(candidate)
                        if "obj" in candidate.relative_to(root).parts:
                            binaries.append(candidate)
        excluded_count = excluded_bytes = 0
        for f in sorted(root.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(root)
            excluded = any(part in ("obj", "probe-output", "__pycache__") for part in rel.parts)
            if excluded and f not in binaries:
                excluded_count += 1
                excluded_bytes += f.stat().st_size
                continue
            add(f, "runs/" + run + "/" + rel.as_posix())
        omitted[run] = {"file_count": excluded_count, "bytes": excluded_bytes,
                        "rule": "obj/** except manifest-bound DUT executable; probe-output/**; __pycache__/**"}
        outer = receipts["runs"][run]
        result = outer.get("shell", {}).get("result", outer.get("result", {}))
        assert result["cleanup_complete"] and not result["timed_out"] and not result["cancelled"]
        expect = 1 if run in ("flag0-01", "decode-flag0-01") else 0
        assert result["exit_code"] == expect
        run_summary[run] = {"source_directory": str(root), "original_operation_id": outer["operation_id"],
                            "original_exit_code": result["exit_code"], "original_terminal_status": outer["status"],
                            "controller_status_sha256": digest(root / "status.json"),
                            "controller_qualification": status.get("qualification"),
                            "included_executables": [str(f.relative_to(root)) for f in binaries]}

    # Fixed helper records are small and preserve the initial source application/recovery.
    for folder in ("apply", "recovery-02"):
        root = args.runs / folder
        if root.exists():
            for f in sorted(root.rglob("*")):
                if f.is_file():
                    assert f.stat().st_size < 8 * 1024 * 1024, "unexpected large recovery file"
                    add(f, "preparation/" + folder + "/" + f.relative_to(root).as_posix())

    delivery = args.repo / "team/optimizations/o2/dot16/rtl-integration"
    names = ["candidate.patch", "source-manifest.json", "README.md", "review.json", "derive_fu_test.py",
             "run_fu.py", "VALIDATION_CONTRACT.md", "VALIDATION_RESULT.md", "validation-result.json"]
    for sub in ("parent", "decode"):
        names.extend(f.relative_to(delivery).as_posix() for f in sorted((delivery / sub).iterdir()) if f.is_file())
    for name in names:
        add(delivery / name, "delivery/" + name)
    add(args.receipts, "operation-receipts.json")
    add(Path(__file__).resolve(), "archive_raw.py")
    members = [{"name": name, "source": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
               for name, path in sorted(selected.items())]

    args.output.mkdir(parents=True, exist_ok=False)
    archive = args.output / "raw.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for member in members:
            z.write(selected[member["name"]], member["name"])
    with zipfile.ZipFile(archive, "r") as z:
        assert sorted(z.namelist()) == [m["name"] for m in members]
        for m in members:
            data = z.read(m["name"])
            assert len(data) == m["bytes"] and hashlib.sha256(data).hexdigest() == m["sha256"], m["name"]
            assert digest(selected[m["name"]]) == m["sha256"], "original changed: " + m["name"]

    manifest = {"schema": 1, "kind": "dot16-existing-raw-evidence-archive-v1", "started_utc": started,
        "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "cpu_affinity": [1],
        "archive": {"name": archive.name, "bytes": archive.stat().st_size, "sha256": digest(archive)},
        "member_count": len(members), "member_uncompressed_bytes": sum(m["bytes"] for m in members),
        "verification": "all ZIP members read, byte counts and SHA256 compared; every source SHA256 rechecked",
        "tests_rerun": False, "original_run_directories_modified": False, "runs": run_summary,
        "exclusions": {"per_run": omitted, "external": ["failed external Mill cache",
            "current Mill cache", "physical JAR/classpath dependency files (identities retained in run manifests)"]},
        "members": members}
    write_json(args.output / "manifest.json", manifest)
    shutil.copyfile(args.receipts, args.output / "operation-receipts.json")
    shutil.copyfile(Path(__file__).resolve(), args.output / "archive_raw.py")
    (args.output / ".gitattributes").write_text("raw.zip -text\n", encoding="utf-8")
    readme = """# FU、父级与解码原始证据归档

本目录仅归档已完成的八次运行；没有重新构建、仿真或调用检查器。
`manifest.json` 列出 ZIP 每个成员的原路径、字节数和 SHA256；压缩后逐成员读取核验，随后复核原文件未变。
`operation-receipts.json` 保存八个原始 ChatPC 终态回执。`archive-receipt.json` 另记录本次归档作业的真实终态。

包含 FU 三次、父级两次、解码三次；两次失败分别为 FU 的 VCS 资源/缓存目录问题和解码的 classpath 预检问题。
各 run 保留原状态、命令、正/负运行日志、检查结果、源码快照、生成 RTL、来源/依赖清单及清单绑定的 DUT 可执行文件。
附带候选与当前结果文档快照；这些文档的资格仍以其各自运行时点和适用范围解释。

排除可再生成的 obj 中间文件、probe-output 编译缓存、Mill 缓存及外部 JAR/classpath 依赖实物。
精确排除计数、大小及保留原目录均见 manifest；未移动、删除或改写任何原始运行目录。
本归档不增加整核 DiffTest、应用性能或 ASIC PPA 资格。
"""
    (args.output / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    copied = []
    for f in sorted(args.output.iterdir()):
        dest = args.windows_output / f.name
        if dest.exists():
            assert digest(dest) == digest(f), "preexisting Windows staging differs: " + str(dest)
        else:
            shutil.copyfile(f, dest)
        assert digest(dest) == digest(f)
        copied.append({"name": f.name, "bytes": f.stat().st_size, "sha256": digest(f)})
    print(json.dumps({"status": "RAW_ARCHIVE_BYTE_VERIFIED", "output": str(args.output),
        "windows_output": str(args.windows_output), "members": len(members),
        "archive": manifest["archive"], "files": copied}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
