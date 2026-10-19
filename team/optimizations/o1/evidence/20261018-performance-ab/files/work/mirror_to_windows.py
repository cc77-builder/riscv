"""Mirror finalized engineering results and sealed evidence to Windows."""
from pathlib import Path
import csv,gzip,hashlib,json,shutil,subprocess,datetime

WORK = Path(__file__).absolute().parent
ROOT = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
SOURCE = ROOT / "team/optimizations/o1/evidence/20261018-performance-ab"
RESULTS = WORK / "results-01"
DEST = Path("/mnt/d/yanyi/riscv大赛/doc/O1公平性能对比_20261018")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not DEST.exists(), "refuse overwrite"
manifest = json.loads((SOURCE / "archive-manifest.json").read_text())
assert manifest["status"] == "PERFORMANCE_EVIDENCE_ARCHIVE_COMPLETE"
assert sha(SOURCE / "archive-manifest.json") == (SOURCE / "archive-manifest.sha256").read_text().split()[0]
DEST.mkdir()
MIRROR = DEST / "evidence/20261018-performance-ab"
MIRROR.parent.mkdir()
shutil.copytree(SOURCE, MIRROR)
copied = {}
for p in SOURCE.rglob("*"):
    if p.is_file():
        q = MIRROR / p.relative_to(SOURCE)
        assert sha(p) == sha(q)
        copied[q.relative_to(DEST).as_posix()] = sha(q)
for row in json.loads((SOURCE / "file-map.json").read_text()):
    p = MIRROR / row["archive"]
    body = gzip.decompress(p.read_bytes()) if row["storage"] == "gzip" else p.read_bytes()
    assert hashlib.sha256(body).hexdigest() == row["source_sha256"]
    assert len(body) == row["source_bytes"]
for name in ("性能结果与工程记录.md", "summary.csv", "comparison.csv", "samples.csv", "verification.json"):
    q = DEST / name
    shutil.copyfile(RESULTS / name, q)
    assert sha(RESULTS / name) == sha(q)
    copied[name] = sha(q)
rows = list(csv.DictReader((DEST / "samples.csv").open(encoding="utf-8")))
assert len(rows) == 478 and sum(r["included_in_measured_statistics"] == "True" for r in rows) == 192
performance_source = ROOT / "team/optimizations/o1/performance"
performance_dest = DEST / "performance"
performance_dest.mkdir()
for p in performance_source.iterdir():
    if p.is_file() and p.suffix in (".py", ".md", ".json"):
        q = performance_dest / p.name
        shutil.copyfile(p, q)
        assert sha(p) == sha(q)
        copied[q.relative_to(DEST).as_posix()] = sha(q)
q = DEST / "测量合同.md"
shutil.copyfile(performance_source / "CONTRACT.md", q)
assert sha(performance_source / "CONTRACT.md") == sha(q)
copied[q.name] = sha(q)
(DEST / "README.md").write_text(
    "# T14/O1 公平性能对比\n\n"
    "[性能结果与工程记录](性能结果与工程记录.md) · [测量合同](测量合同.md) · "
    "[CSV汇总](comparison.csv) · [全部样本](samples.csv)\n\n"
    "[源码与复现入口](performance/README.md) · "
    "[原始证据](evidence/20261018-performance-ab/README.md) · [交付核验](交付核验.json)\n\n"
    "这里保存查看副本，运行命令应在完整WSL仓库执行。Windows核验只检查复制字节与解压摘要，"
    "不代表新机器硬件构建或新EMU运行。本轮未推送GitHub。\n", encoding="utf-8")
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
receipt = dict(status="T14_O1_PERFORMANCE_WINDOWS_MIRROR_PASS",
               completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               local_delivery_commit=head, branch="local/o1-performance-20261018",
               archive_manifest_sha256=sha(MIRROR / "archive-manifest.json"),
               copied_file_sha256=copied, stored_bytes_verified=True, original_gzip_payloads_verified=True,
               rows=478, measured_rows=192, new_emu_executed=False, fresh_machine_hardware_build=False,
               new_github_push=False)
(DEST / "交付核验.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(status=receipt["status"], files=len(copied), commit=head), ensure_ascii=False))
