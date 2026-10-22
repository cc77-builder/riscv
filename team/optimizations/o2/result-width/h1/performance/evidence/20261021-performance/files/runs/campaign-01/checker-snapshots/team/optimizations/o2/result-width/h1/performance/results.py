"""Recheck completed paired evidence and export engineering statistics; no EMU."""
import argparse
import csv
import importlib.util
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("paired_compare", HERE / "compare.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)
LABELS = {"single": "单次点积", "chain": "依赖链256", "batch": "四路独立点积128", "stream": "加载/计算/存储64"}


def csv_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def main(campaign, output):
    require, save, sha = compare.require, compare.save, compare.sha
    require(not output.exists(), "output exists")
    output.mkdir(parents=True)
    result = json.loads((campaign / "result.json").read_text())
    require(result["status"] == "B0_H1_PAIRED_PERFORMANCE_PASS", "campaign is not accepted")
    before = {str(p): sha(p) for p in campaign.rglob("*") if p.is_file()}
    artifacts = json.loads((campaign / "artifact-pins.json").read_text())
    compare.verify_hashes(artifacts)
    check = compare.load_module("offline_windows", compare.ROOT / "team/workloads/unified-vdot/check.py")
    observers={
        "b0":compare.load_module("offline_o1",compare.ROOT/"team/optimizations/o2/fullcore/analyze.py"),
        "h1":compare.load_module("offline_o2",compare.ROOT/"team/optimizations/o2/fullcore/analyze.py")}
    gate=compare.load_module("offline_gate",compare.ROOT/"team/optimizations/o1/audit/runtime_gate.py")
    fatal=compare.load_module("offline_fatal",compare.ROOT/"team/optimizations/o2/fullcore/workloads/check.py")
    state=json.loads((campaign/"state.json").read_text())
    for saved in (campaign/"checker-snapshots").rglob("*"):
        if saved.is_file():
            relative=saved.relative_to(campaign/"checker-snapshots")
            blob=__import__("subprocess").check_output(["git","show",state["source_commit"]+":"+relative.as_posix()],cwd=compare.ROOT)
            require(blob==saved.read_bytes() and compare.sha(compare.ROOT/relative)==compare.sha(saved),
                    "original committed runtime checker changed: "+str(relative))

    expected={(mode,name,0) for mode in compare.MODES for name in compare.expected_names()}
    expected|={(mode,"performance-d0-s02",replay) for mode in compare.MODES for replay in (1,2)}
    observed=[(row["mode"],row["image"],row["replay"]) for row in result["runs"]]
    require(len(observed)==36 and set(observed)==expected,"incomplete/duplicate exact run inventory")
    actual={p.parent for p in campaign.glob("*/*/*/result.json")}
    declared={campaign/row["mode"]/row["stage"]/(row["image"]+f'-r{row["replay"]}') for row in result["runs"]}
    require(actual==declared,"extra or missing raw run directories")
    rows, samples = [], []
    for record in result["runs"]:
        mode, image, replay = record["mode"], record["image"], record["replay"]
        directory = campaign / mode / record["stage"] / (image + f"-r{replay}")
        original = json.loads((directory / "result.json").read_text())
        runtime = json.loads((directory / "runtime.json").read_text())
        require(original == record, "campaign/run receipt mismatch")
        require(record["status"] == "PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS" and record["exit_code"] == 0,
                "unaccepted run")
        require((directory / "exit-code.txt").read_bytes() == b"0\n", "wrong actual exit receipt")
        require(record["command"] == runtime["command"] and record["files"] == runtime["files"],
                "launch/result identity drift")
        require(record["command"][-1] == "--seed=1" and "--max-cycles=2000000" in record["command"],
                "runtime option drift")
        stdout = (directory / "stdout.log").read_text()
        stderr = (directory / "stderr.log").read_text()
        for text in (stdout, stderr):
            fatal.reject_fatal_output(text)
            gate.validate_failure_markers(text)
        ref = next(x.split("=", 1)[1] for x in record["command"] if x.startswith("--diff="))
        compare.validate_loaded_reference(stderr + stdout, ref, gate.normalize_console)
        windows = check.verify(Path(record["build"]), directory)
        require(windows == json.loads((directory / "window-result.json").read_text()), "window reparse differs")
        analysis=observers[mode].analyze(stderr+stdout)
        canonical=json.loads(json.dumps(analysis))
        require(canonical==json.loads((directory/"observation.json").read_text()),"observer reparse differs")
        compare.observer_gate(mode,analysis,record["expected_vdot_commits"])
        require(analysis["counts"] == record["observation_counts"]
                and analysis["counts"]["COMMIT"] == record["expected_vdot_commits"], "instruction binding mismatch")
        fresh = [dict(s, mode=mode, stage=record["stage"], replay=replay, image=image,
                      image_sha256=windows["image_sha256"]) for s in windows["samples"]]
        require(fresh == record["samples"], "sample receipt differs from original evidence")
        samples.extend(fresh)
        rows.append(record)
    require(len(rows) == 36 and len(samples) == 478, "incomplete paired inventory")
    require(samples == result["samples"], "campaign sample sequence mismatch")
    compare.compare_replays(rows)
    stats = compare.summarize(samples)
    deltas = compare.paired_deltas(samples)
    require(deltas == result["paired_measured_windows"], "paired delta receipt mismatch")
    require(result["cycle_nonregression_pass"] == all(s["delta_cycles"] <= 0 for s in deltas), "verdict mismatch")
    require(result["exact_measured_cycle_equality"] == all(s["delta_cycles"] == 0 for s in deltas), "equality verdict mismatch")
    require(stats == result["rows"], "derived statistics differ")
    compare.verify_hashes(artifacts)
    require(before == {str(p): sha(p) for p in campaign.rglob("*") if p.is_file()}, "campaign evidence changed")
    flat, comparison = [], []
    for row in stats:
        for mode in compare.MODES:
            selected = [sample for sample in samples if sample["mode"] == mode
                        and sample["scenario"] == row["scenario"] and sample["stage"] == "performance"
                        and sample["phase"] == "measured" and sample["replay"] == 0]
            rvv = [sample["cycles"] for sample in selected if sample["method"] == "rvv"]
            instructions = {method: {sample["instructions"] for sample in selected if sample["method"] == method}
                            for method in ("vdot", "rvv")}
            require(all(len(values) == 1 for values in instructions.values()), "instruction count changed across equal-work samples")
            flat.append(dict(scenario=row["scenario"], mode=mode, **row[mode],
                             rvv_median_cycles=statistics.median(rvv),
                             rvv_mean_cycles_per_dot=row[mode]["rvv_mean_cycles"] / row[mode]["dots"],
                             custom_window_instructions=next(iter(instructions["vdot"])),
                             rvv_window_instructions=next(iter(instructions["rvv"]))))
        comparison.append(dict(scenario=row["scenario"], dots=row["b0"]["dots"],
                               b0_custom_mean_cycles=row["b0"]["custom_mean_cycles"],
                               h1_custom_mean_cycles=row["h1"]["custom_mean_cycles"],
                               custom_cycle_reduction=row["custom_cycle_reduction"],
                               b0_over_h1=row["custom_b0_over_h1"],
                               b0_rvv_mean_cycles=row["b0"]["rvv_mean_cycles"],
                               h1_rvv_mean_cycles=row["h1"]["rvv_mean_cycles"],
                               b0_speedup=row["b0"]["speedup_ratio_of_sums"],
                               h1_speedup=row["h1"]["speedup_ratio_of_sums"],
                               rvv_cycle_reduction=row["rvv_cycle_reduction"],
                               investigation_required=row["investigation_required"]))
    csv_rows(output / "summary.csv", flat)
    csv_rows(output / "comparison.csv", comparison)
    csv_rows(output / "samples.csv", [
        dict(sample, included_in_measured_statistics=(sample["stage"] == "performance"
             and sample["phase"] == "measured" and sample["replay"] == 0))
        for sample in samples])

    receipt = dict(status="OFFLINE_B0_H1_PAIRED_RECHECK_PASS", finished_utc=compare.now(),
                   campaign=str(campaign), campaign_result_sha256=sha(campaign / "result.json"),
                   jobs=36, windows=478, measured_windows=192, replay_jobs=4,
                   original_evidence_unchanged=True, new_emu_executed=False,
                   checker_sha256=sha(Path(__file__)), compare_sha256=sha(HERE / "compare.py"),
                   rows=stats, input_files_verified=len(artifacts))
    save(output / "verification.json", receipt)
    csv_rows(output / "paired-windows.csv", deltas)
    receipt.update(cycle_nonregression_pass=result["cycle_nonregression_pass"],
                   exact_measured_cycle_equality=result["exact_measured_cycle_equality"],
                   matched_formal_pairs=len(deltas),
                   regressions=[s for s in deltas if s["delta_cycles"] > 0])
    save(output / "verification.json", receipt)
    lines = ["# B0/H1 同镜像周期不退化检查", "",
             "36项新运行与严格原始日志重审完成；本地保存，未推送GitHub。", "",
             "B0/H1均为O2两槽配置，共同观察器、编译选项、工具链、NEMU、flash、seed及固定16镜像。"
             "源码差异为H1生产改动与独立O4测试构建入口；生成文件的Git标识、顶层注释和输入型日志模块差异已单独审查，详情见build-profile.json。",
             "每版四场景×三数据集×四轮，192个正式窗口形成96对。478个校验窗口包含first/warmup与4项代表镜像重放；重放不增加样本数。",
             "", "| 场景 | B0 vdot cycles | H1 vdot cycles | B0 RVV cycles | H1 RVV cycles | H1相对RVV |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in stats:
        a, b = row["b0"], row["h1"]
        lines.append(f'| {LABELS[row["scenario"]]} | {a["custom_mean_cycles"]:.3f} | {b["custom_mean_cycles"]:.3f} | {a["rvv_mean_cycles"]:.3f} | {b["rvv_mean_cycles"]:.3f} | {b["speedup_ratio_of_sums"]:.3f}× |')
    lines += ["", "逐正式窗口不退化：" + ("通过" if receipt["cycle_nonregression_pass"] else "未通过"),
              "逐正式窗口周期完全一致：" + ("是" if receipt["exact_measured_cycle_equality"] else "否"),
              "退化窗口数：" + str(len(receipt["regressions"])) + "（任意+1周期也保留，不使用平均值或容差掩盖）。",
              "", "加速比为各版本次实测sum(RVV)/sum(vdot)，不扣空窗、屏障或循环开销，不用宿主耗时。",
              "samples.csv保留全部原始窗口，paired-windows.csv逐键比较正式样本，summary.csv与comparison.csv提供统计。",
              "", "本轮只覆盖固定微基准；不等于GEMV应用、Fmax/时序或所有工作负载均不退化。"
              "此前H1面积节省与STA路径退化结论保持；默认开关、R0锁和旧封存证据未改，未代签人工ACK。",
              "下一步按计划评估R1取舍与R2应用候选；本轮未自动开展后续优化，正式比赛报告继续后置。"]
    (output / "B0_H1周期对比结果.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "jobs", "windows", "measured_windows",
                                            "cycle_nonregression_pass", "exact_measured_cycle_equality")}))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.campaign, args.output))
