"""Revalidate and reconcile all evidence before publishing a local archive.

The full preflight and WSL staging complete before any Windows output is written.
Importing this module is read-only; use its helpers for partial structural review.
"""
from pathlib import Path
import csv
import datetime
import gzip
import hashlib
import json
import shutil
import statistics
import sys
import tarfile
import tempfile

WORKSPACE = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE / "repo/team/workloads/unified-vdot"))
import check

VARIANTS = ("ours", "jade", "shishui", "redoop")
SCENARIOS = ("single", "chain", "batch", "stream")
DOTS = {"single": 1, "chain": 256, "batch": 128, "stream": 64}
LABELS = {"ours": "本项目 T14", "jade": "Jade", "shishui": "试水", "redoop": "Redoop（dot8适配）"}
OUTPUT = Path("/mnt/d/yanyi/riscv大赛/doc/四项目统一测试_20261017")


def read_json(path):
    return json.loads(Path(path).read_text())


def require_equal(actual, expected, label):
    check.require(actual == expected, label)


def preflight_variant(workspace, variant):
    """Reconstruct this suite from fresh log/ELF verification, in original order."""
    root = Path(workspace)
    suite = root / "runs" / (variant + "-suite-02")
    saved = read_json(suite / "result.json")
    require_equal(saved["status"], "UNIFIED_FULLCORE_PASS", "unaccepted suite " + variant)
    require_equal(saved["variant"], variant, "suite variant binding " + variant)
    images = read_json(root / "runs" / (variant + "-images-02/images.json"))["images"]
    require_equal(len(images), 16, "image count " + variant)
    require_equal(len({item["name"] for item in images}), 16, "duplicate images " + variant)
    require_equal([item["suite"] for item in images],
                  ["smoke"] + ["functional"] * 3 + ["performance"] * 12,
                  "image stage order " + variant)
    samples = []
    runs = []
    stages = []
    for stage in ("smoke", "functional", "performance"):
        accepted = []
        for item in images:
            if item["suite"] != stage:
                continue
            build = Path(item["path"])
            run = suite / stage / (item["name"] + "-r0")
            manifest = read_json(build / "data/manifest.json")
            require_equal(manifest["variant"], variant, "compiled image variant " + item["name"])
            require_equal(manifest["suite"], stage, "compiled image suite " + item["name"])
            verdict = check.verify(build, run)
            require_equal(verdict["status"], "PASS", "fresh image acceptance " + item["name"])
            for sample in verdict["samples"]:
                samples.append(dict(sample, variant=variant, stage=stage, run=str(run)))
            accepted.append({"name": item["name"], "samples": len(verdict["samples"])})
            runs.append({"variant": variant, "item": item, "build": build,
                         "run": run, "verdict": verdict})
        stages.append({"name": stage, "status": "PASS", "images": accepted})
    require_equal(saved["samples"], samples, "suite samples differ from fresh evidence: " + variant)
    require_equal(saved["stages"], stages, "suite stage receipts differ: " + variant)
    return {"variant": variant, "samples": samples, "runs": runs, "saved": saved}


def calculate_rows(variant, rows):
    """Independent recomputation of analyze.py's four rows for one variant."""
    require_equal(len(rows), 96, "measured sample count " + variant)
    check.require(all(s["variant"] == variant and s["stage"] == "performance"
                      and s["phase"] == "measured" for s in rows), "measured sample binding")
    require_equal({s["scenario"] for s in rows}, set(SCENARIOS), "scenario set")
    wanted_keys = {(dataset, repeat) for dataset in range(3) for repeat in range(2, 6)}
    records = []
    for scenario in SCENARIOS:
        selected = [s for s in rows if s["scenario"] == scenario]
        require_equal(len(selected), 24, "scenario sample count " + scenario)
        methods = {}
        for method in ("vdot", "rvv"):
            method_rows = [s for s in selected if s["method"] == method]
            require_equal(len(method_rows), 12, "method sample count " + scenario + "/" + method)
            methods[method] = {(s["dataset"], s["repeat"]): s for s in method_rows}
            require_equal(set(methods[method]), wanted_keys, "dataset/repeat set " + scenario + "/" + method)
        require_equal({s["dots"] for s in selected}, {DOTS[scenario]}, "dot count " + scenario)
        check.require(all(type(s["cycles"]) is int and 0 < s["cycles"] < (1 << 32)
                          for s in selected), "invalid cycle count")
        dots = DOTS[scenario]
        custom = [s["cycles"] for s in methods["vdot"].values()]
        baseline = [s["cycles"] for s in methods["rvv"].values()]
        paired = [methods["rvv"][key]["cycles"] / value["cycles"]
                  for key, value in methods["vdot"].items()]
        records.append(dict(
            variant=variant, scenario=scenario, dots=dots, samples_per_method=12,
            custom_mean_cycles=statistics.mean(custom), custom_median_cycles=statistics.median(custom),
            custom_min_cycles=min(custom), custom_max_cycles=max(custom),
            custom_mean_cycles_per_dot=statistics.mean(custom) / dots,
            rvv_mean_cycles=statistics.mean(baseline), rvv_median_cycles=statistics.median(baseline),
            rvv_min_cycles=min(baseline), rvv_max_cycles=max(baseline),
            speedup_ratio_of_sums=sum(baseline) / sum(custom),
            paired_speedup_median=statistics.median(paired),
            paired_speedup_min=min(paired), paired_speedup_max=max(paired)))
    return records


def verify_csv(path, records):
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        require_equal(reader.fieldnames, list(records[0]), "CSV columns " + str(path))
        actual = list(reader)
    expected = [{key: str(value) for key, value in row.items()} for row in records]
    require_equal(actual, expected, "CSV statistics/samples differ " + str(path))


def preflight_summary(workspace, suites):
    root = Path(workspace)
    result = read_json(root / "results-01/result.json")
    require_equal(result["status"], "UNIFIED_FOUR_PROJECT_COMPARISON_PASS", "summary acceptance")
    rows = []
    samples = []
    for variant in VARIANTS:
        selected = [sample for sample in suites[variant]["samples"]
                    if sample["stage"] == "performance" and sample["phase"] == "measured"]
        rows.extend(calculate_rows(variant, selected))
        samples.extend(selected)
    require_equal(len(rows), 16, "summary row count")
    require_equal(len(samples), 384, "summary measured sample count")
    require_equal(result["samples"], samples, "final summary samples differ from fresh evidence")
    require_equal(result["rows"], rows, "final 16 statistics rows differ from independent recomputation")
    verify_csv(root / "results-01/summary.csv", rows)
    verify_csv(root / "results-01/samples.csv", samples)
    # Bind all displayed numeric rows while allowing explanatory prose to evolve.
    expected_lines = []
    for scenario in SCENARIOS:
        for row in rows:
            if row["scenario"] == scenario:
                expected_lines.append(
                    f"| {LABELS[row['variant']]} | {row['custom_mean_cycles']:.3f} | "
                    f"{row['custom_mean_cycles_per_dot']:.3f} | {row['rvv_mean_cycles']:.3f} | "
                    f"{row['speedup_ratio_of_sums']:.3f}× | {row['custom_min_cycles']}–{row['custom_max_cycles']} |")
    table_prefixes = tuple("| " + label + " |" for label in LABELS.values())
    actual_lines = [line for line in (root / "results-01/统一测试结果.md").read_text().splitlines()
                    if line.startswith(table_prefixes)]
    require_equal(actual_lines, expected_lines, "Markdown statistics differ from independent recomputation")
    summary_hashes = {name: check.sha(root / "results-01" / name) for name in
                      ("result.json", "summary.csv", "samples.csv", "统一测试结果.md")}
    return {"rows": rows, "samples": samples, "files": summary_hashes}


def preflight(workspace, output):
    root = Path(workspace)
    identity = read_json(root / "audit/image-identity.json")
    require_equal(identity["status"], "UNIFIED_INPUT_AND_BASELINE_IDENTITY_PASS", "image identity acceptance")
    suites = {variant: preflight_variant(root, variant) for variant in VARIANTS}
    summary = preflight_summary(root, suites)
    manifest = read_json(root / "audit/hardware-source-manifest.json")
    for variant, data in manifest.items():
        for sub, repo in data["repositories"].items():
            for file, digest in repo["files"].items():
                require_equal(check.sha(Path(data["root"]) / sub / file), digest,
                              "hardware source changed " + variant + "/" + sub + "/" + file)
    # Check all later packaging prerequisites before touching the output directory.
    required = [root / name for name in
                ("build-remaining-v2.py", "run-public-v2.py", "run-public-v3.py", "WORK_STATE.json", "archive-results.py")]
    for variant in VARIANTS:
        required.extend(root / "runs" / (variant + "-suite-02") / name for name in ("state.json", "result.json"))
        ref = root / "runs" / (variant + "-reference-01/result.json")
        require_equal(read_json(ref)["status"], "PASS_REFERENCE_ONLY", "reference acceptance " + variant)
        required.append(ref)
        if variant != "ours":
            required.extend(root / "runs" / (variant + "-build") / name for name in ("build.json", "build.log"))
        for entry in suites[variant]["runs"]:
            required.extend(entry["run"] / name for name in ("runtime.json", "result.json", "stdout.log", "stderr.log"))
            required.extend(entry["build"] / name for name in
                            ("vdot-perf.bin", "vdot-perf.elf", "build.json", "build.log", "data", "source"))
    check.require(all(path.exists() for path in required), "missing packaging prerequisite")
    for name in ("结果", "验证证据", "测试镜像与构建快照.tar.gz", "验收记录.json", "文件校验.json"):
        check.require(not (Path(output) / name).exists(), "refusing to replace an existing archive: " + name)
    return {"suites": suites, "summary": summary}


def build_package(workspace, staging, accepted):
    root, out = Path(workspace), Path(staging)
    source = root / "repo/team/workloads/unified-vdot"
    for p in source.iterdir():
        if p.is_file():
            for dest in (out / "测试程序", out / "team/workloads/unified-vdot"):
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest / p.name)
    data = out / "team/models/vdot/data"
    data.mkdir(parents=True, exist_ok=True)
    for p in (root / "repo/team/models/vdot/data").iterdir():
        if p.is_file():
            shutil.copy2(p, data / p.name)
    shutil.copytree(root / "results-01", out / "结果")
    audit = out / "版本与适配审计"
    audit.mkdir()
    for p in (root / "audit").iterdir():
        if p.is_file():
            shutil.copy2(p, audit / p.name)
    for name in ("build-remaining-v2.py", "run-public-v2.py", "run-public-v3.py", "WORK_STATE.json", "archive-results.py"):
        shutil.copy2(root / name, audit / name)
    evidence = out / "验证证据"
    evidence.mkdir()
    verified = []
    with tarfile.open(out / "测试镜像与构建快照.tar.gz", "w:gz", compresslevel=6) as archive:
        for variant in VARIANTS:
            for entry in accepted["suites"][variant]["runs"]:
                item, build, run, verdict = (entry[key] for key in ("item", "build", "run", "verdict"))
                dest = evidence / variant / item["name"]
                dest.mkdir(parents=True)
                (dest / "check.json").write_text(json.dumps(verdict, indent=2) + "\n")
                for name in ("result.json", "runtime.json"):
                    shutil.copy2(run / name, dest / name)
                for name in ("stdout.log", "stderr.log"):
                    raw = (run / name).read_bytes()
                    require_equal(hashlib.sha256(raw).hexdigest(), verdict["raw_sha256"][name], "transcript changed during staging")
                    (dest / (name + ".gz")).write_bytes(gzip.compress(raw, compresslevel=6, mtime=0))
                for name in ("vdot-perf.bin", "vdot-perf.elf", "build.json", "build.log", "data", "source"):
                    archive.add(build / name, arcname=variant + "/" + item["name"] + "/" + name)
                verified.append({"variant": variant, "image": item["name"], "samples": len(verdict["samples"])})
            for name in ("state.json", "result.json"):
                shutil.copy2(root / "runs" / (variant + "-suite-02") / name, evidence / variant / name)
            shutil.copy2(root / "runs" / (variant + "-reference-01/result.json"), evidence / variant / "reference-only-result.json")
            if variant != "ours":
                build = root / "runs" / (variant + "-build")
                shutil.copy2(build / "build.json", evidence / variant / "hardware-build.json")
                (evidence / variant / "hardware-build.log.gz").write_bytes(gzip.compress((build / "build.log").read_bytes(), compresslevel=6, mtime=0))
    # Detect any summary/cache mutation after preflight before publishing Windows files.
    for variant in VARIANTS:
        require_equal(read_json(evidence / variant / "result.json")["samples"],
                      accepted["suites"][variant]["samples"], "suite changed during staging")
    for name, digest in accepted["summary"]["files"].items():
        require_equal(check.sha(out / "结果" / name), digest, "summary file changed during staging: " + name)
    copied_result = read_json(out / "结果/result.json")
    require_equal(copied_result["samples"], accepted["summary"]["samples"], "summary samples changed during staging")
    require_equal(copied_result["rows"], accepted["summary"]["rows"], "summary statistics changed during staging")
    verify_csv(out / "结果/summary.csv", accepted["summary"]["rows"])
    verify_csv(out / "结果/samples.csv", accepted["summary"]["samples"])
    receipt = {"status": "ARCHIVED_VERIFIED", "time": datetime.datetime.now().astimezone().isoformat(),
               "images": verified, "total_images": len(verified), "total_windows": sum(row["samples"] for row in verified),
               "measured_samples": len(accepted["summary"]["samples"]), "statistics_rows": len(accepted["summary"]["rows"]),
               "fresh_suite_sample_closure": "PASS", "summary_sample_closure": "PASS", "independent_statistics_check": "PASS",
               "source_immutability": "PASS", "source_workspace": str(root), "no_github_push": True}
    (out / "验收记录.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    (out / "当前进度.md").write_text("# 统一测试已完成\n\n四个项目均通过统一全核验证。请查看 [正式结果](结果/统一测试结果.md) 和 [测试说明](team/workloads/unified-vdot/README.md)。\n\n归档前已从原始日志重新验证全部窗口，逐项核对 suite、384 条测量样本和16条统计。本次成果仅保存在本地，未上传 GitHub。\n")
    (out / "复核说明.md").write_text("# 归档复核范围\n\n验收记录包含原始日志→每窗口样本→suite汇总→最终统计的严格一致性检查。测试镜像、ELF、构建源码快照、压缩日志及版本补丁均已归档，文件校验.json给出归档文件SHA256。\n\nEMU、NEMU和flash二进制保留在原WSL工作区，归档记录其绝对路径与SHA256，未复制这些大文件。直接使用check.py命令行重验仍需原工作区；移动归档后的证据核对需解包镜像，并通过check.verify的external参数显式提供原执行依赖哈希。仅提供哈希可核对记录绑定，不能替代重新运行这些二进制。\n")
    files = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(out.rglob("*")) if p.is_file() and p.name != "文件校验.json"}
    (out / "文件校验.json").write_text(json.dumps({"algorithm": "sha256", "files": files}, ensure_ascii=False, indent=2) + "\n")
    return receipt


def main():
    accepted = preflight(WORKSPACE, OUTPUT)
    # A staging failure cannot leave a partially accepted Windows result package.
    with tempfile.TemporaryDirectory(prefix="archive-verified-", dir=WORKSPACE) as temp:
        staging = Path(temp)
        receipt = build_package(WORKSPACE, staging, accepted)
        shutil.copytree(staging, OUTPUT, dirs_exist_ok=True)
        hashes = read_json(OUTPUT / "文件校验.json")["files"]
        for name, digest in hashes.items():
            require_equal(check.sha(OUTPUT / name), digest, "copied archive file mismatch " + name)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
