"""Seal completed paired evidence as exact original bytes; no EMU or publishing."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location("paired_compare", HERE / "compare.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)
TEXT = {".json", ".log", ".txt", ".md", ".py", ".sh", ".csv", ".patch"}
SKIP = {"products", "__pycache__", ".git"}
DEST = HERE.parent / "evidence/20261018-performance-ab"


def inventory(work):
    result, excluded = {}, []
    for path, dirs, names in os.walk(work):
        for name in list(dirs):
            if name in SKIP:
                excluded.append(str(Path(path) / name))
                dirs.remove(name)
        for name in names:
            p = Path(path) / name
            compare.require(not p.is_symlink(), "symlink in evidence")
            if p.suffix not in TEXT:
                excluded.append(str(p))
                continue
            result["work/" + p.relative_to(work).as_posix()] = p
    for p in sorted(HERE.iterdir()):
        if p.is_file() and p.suffix in TEXT:
            result["source/" + p.name] = p
    return result, sorted(excluded)


def main(work, campaign, results):
    require, save, sha = compare.require, compare.save, compare.sha
    require(not DEST.exists(), "sealed destination already exists")
    result = json.loads((campaign / "result.json").read_text())
    audit = json.loads((results / "verification.json").read_text())
    host = json.loads((work / "host-03/result.json").read_text())
    require(result["status"] == "T14_O1_PAIRED_PERFORMANCE_PASS" and result["new_emu_jobs"] == 36, "no complete campaign")
    require(audit["status"] == "OFFLINE_T14_O1_PAIRED_RECHECK_PASS" and audit["original_evidence_unchanged"]
            and not audit["new_emu_executed"], "no final offline recheck")
    require(host["status"] == "PAIRED_RUNNER_HOST_PASS" and host["source_unchanged"], "no final host PASS")
    require(re.findall(r"Ran (\d+) tests in", (work / "host-03/stderr.log").read_text()) == ["20"], "wrong host count")
    latest_host = json.loads((work / "host-04/result.json").read_text())
    require(latest_host["status"] == "PAIRED_RUNNER_AND_BUILD_SCOPE_HOST_PASS"
            and latest_host["source_unchanged"], "no final build-scope host PASS")
    require(re.findall(r"Ran (\d+) tests in", (work / "host-04/stderr.log").read_text()) == ["22"], "wrong final host count")
    require(json.loads((work / "launch-01/result.json").read_text())["exit_code"] == 0, "launcher incomplete")
    pins = json.loads((campaign / "artifact-pins.json").read_text())
    compare.verify_hashes(pins)
    files, excluded = inventory(work)
    before = {str(p): sha(p) for p in files.values()}
    stage = Path(tempfile.mkdtemp(prefix=DEST.name + ".INCOMPLETE-", dir=DEST.parent))
    try:
        mapping = []
        for rel, source in sorted(files.items()):
            body = source.read_bytes()
            require(hashlib.sha256(body).hexdigest() == before[str(source)], "source changed before packaging")
            zipped = source.suffix == ".log" or len(body) >= 262144
            stored = gzip.compress(body, compresslevel=9, mtime=0) if zipped else body
            relative = "files/" + rel + (".gz" if zipped else "")
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(stored)
            require((gzip.decompress(stored) if zipped else stored) == body, "round-trip differs")
            mapping.append(dict(source=str(source), source_sha256=before[str(source)], source_bytes=len(body),
                                archive=relative, archive_sha256=sha(target), archive_bytes=len(stored),
                                storage="gzip" if zipped else "identity"))
        save(stage / "file-map.json", mapping)
        save(stage / "excluded.json", excluded)
        (stage / ".gitattributes").write_text("** -text -whitespace\n")
        links = {row["source"]: row["archive"] for row in mapping}
        markdown = links[str(results / "性能结果与工程记录.md")]
        final = links[str(results / "verification.json")]
        (stage / "README.md").write_text(
            "# T14/O1 同镜像公平性能比较证据\n\n"
            "本次36项实际配对运行及离线全套重审通过，192个正式性能窗口；原始窗口共478个。\n\n"
            "- [性能结果与工程记录](" + markdown + ")\n"
            "- [最终离线复核](" + final + ")\n"
            "- [原始/存储字节映射](file-map.json)\n\n"
            "额外O1校准探针、主机检查初次失败、构建目录适配失败和恢复回执均原样保留。"
            "失败尝试不计入正式性能样本；压缩按原始字节验证，EMU/NEMU、对象和波形不进入归档。"
            "复现所需冻结工作负载已在原 unified-vdot-20261017 镜像tar中，输入摘要保存在campaign工件清单。\n\n"
            "本目录的专属Git属性禁止任何换行转换；提交前后另核对Git blob。"
            "打包不运行EMU，不代表新机器完整构建、PPA或人工ACK。本轮本地保存。\n",
            encoding="utf-8")
        require(inventory(work)[0] == files, "evidence inventory changed")
        compare.verify_hashes(before)
        compare.verify_hashes(pins)
        payload = {p.relative_to(stage).as_posix(): sha(p) for p in stage.rglob("*") if p.is_file()}
        manifest = dict(status="PERFORMANCE_EVIDENCE_ARCHIVE_COMPLETE", created_utc=compare.now(),
                        final_verdict=result["status"], final_recheck=audit["status"],
                        campaign_result_sha256=sha(campaign / "result.json"),
                        offline_recheck_sha256=sha(results / "verification.json"),
                        packager_sha256=sha(Path(__file__)), mapped_files=len(mapping),
                        original_bytes=sum(r["source_bytes"] for r in mapping),
                        stored_bytes=sum(r["archive_bytes"] for r in mapping),
                        source_files_unchanged=True, gzip_round_trip_verified=True, new_emu_executed=False,
                        files=payload)
        save(stage / "archive-manifest.json", manifest)
        (stage / "archive-manifest.sha256").write_text(sha(stage / "archive-manifest.json") + "  archive-manifest.json\n")
        for rel, digest in payload.items():
            require(sha(stage / rel) == digest, "archived payload changed")
        require(not DEST.exists(), "destination appeared")
        DEST.mkdir()
        os.replace(stage, DEST)
        print(json.dumps(dict(status=manifest["status"], files=len(mapping), destination=str(DEST),
                              manifest_sha256=sha(DEST / "archive-manifest.json"))))
        return 0
    except BaseException as exc:
        if stage.exists():
            save(stage / "INCOMPLETE.json", dict(status="INCOMPLETE", error=repr(exc)))
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--campaign", required=True, type=Path)
    p.add_argument("--results", required=True, type=Path)
    a = p.parse_args()
    raise SystemExit(main(a.work, a.campaign, a.results))
