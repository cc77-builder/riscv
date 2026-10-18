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
    require(result["status"] == "T14_O1_PAIRED_PERFORMANCE_PASS", "campaign is not accepted")
    before = {str(p): sha(p) for p in campaign.rglob("*") if p.is_file()}
    artifacts = json.loads((campaign / "artifact-pins.json").read_text())
    compare.verify_hashes(artifacts)
    check = compare.load_module("offline_windows", compare.ROOT / "team/workloads/unified-vdot/check.py")
    observer = compare.load_module("offline_observer", HERE.parent / "fullcore/analyze.py")
    gate = compare.load_module("offline_gate", HERE.parent / "audit/runtime_gate.py")
    rows, samples = [], []
    for record in result["runs"]:
        mode, image, replay = record["mode"], record["image"], record["replay"]
        directory = campaign / mode / record["stage"] / (image + f"-r{replay}")
        original = json.loads((directory / "result.json").read_text())
        runtime = json.loads((directory / "runtime.json").read_text())
        require(original == record, "campaign/run receipt mismatch")
        require(record["status"] == "PAIRED_IMAGE_DIFFTEST_AND_WINDOWS_PASS" and record["exit_code"] == 0,
                "unaccepted run")
        require((directory / "exit-code.txt").read_text().strip() == "0", "wrong actual exit receipt")
        require(record["command"] == runtime["command"] and record["files"] == runtime["files"],
                "launch/result identity drift")
        require(record["command"][-1] == "--seed=1" and "--max-cycles=2000000" in record["command"],
                "runtime option drift")
        stdout = (directory / "stdout.log").read_text()
        stderr = (directory / "stderr.log").read_text()
        for text in (stdout, stderr):
            gate.validate_failure_markers(text)
        ref = next(x.split("=", 1)[1] for x in record["command"] if x.startswith("--diff="))
        compare.validate_loaded_reference(stderr + stdout, ref, gate.normalize_console)
        windows = check.verify(Path(record["build"]), directory)
        require(windows == json.loads((directory / "window-result.json").read_text()), "window reparse differs")
        analysis = observer.analyze(stderr + stdout)
        require(analysis == json.loads((directory / "observation.json").read_text()), "observer reparse differs")
        require(analysis["status"] == "O1_TRACE_PASS" and analysis["schema"]["handoff"] == (mode == "o1"),
                "wrong observer mode/status")
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
        comparison.append(dict(scenario=row["scenario"], dots=row["t14"]["dots"],
                               t14_custom_mean_cycles=row["t14"]["custom_mean_cycles"],
                               o1_custom_mean_cycles=row["o1"]["custom_mean_cycles"],
                               custom_cycle_reduction=row["custom_cycle_reduction"],
                               t14_over_o1=row["custom_t14_over_o1"],
                               t14_rvv_mean_cycles=row["t14"]["rvv_mean_cycles"],
                               o1_rvv_mean_cycles=row["o1"]["rvv_mean_cycles"],
                               t14_speedup=row["t14"]["speedup_ratio_of_sums"],
                               o1_speedup=row["o1"]["speedup_ratio_of_sums"],
                               rvv_cycle_reduction=row["rvv_cycle_reduction"],
                               investigation_required=row["investigation_required"]))
    csv_rows(output / "summary.csv", flat)
    csv_rows(output / "comparison.csv", comparison)
    csv_rows(output / "samples.csv", [
        dict(sample, included_in_measured_statistics=(sample["stage"] == "performance"
             and sample["phase"] == "measured" and sample["replay"] == 0))
        for sample in samples])

    receipt = dict(status="OFFLINE_T14_O1_PAIRED_RECHECK_PASS", finished_utc=compare.now(),
                   campaign=str(campaign), campaign_result_sha256=sha(campaign / "result.json"),
                   jobs=36, windows=478, measured_windows=192, replay_jobs=4,
                   original_evidence_unchanged=True, new_emu_executed=False,
                   checker_sha256=sha(Path(__file__)), compare_sha256=sha(HERE / "compare.py"),
                   rows=stats, input_files_verified=len(artifacts))
    save(output / "verification.json", receipt)
    lines = [
        "# T14/O1 同镜像公平周期对比：工程测量记录", "",
        "本页记录工程测试结果，正式 T16 报告继续后置。本轮没有上传 GitHub。", "",
        "两模式采用相同硬件源码与依赖、MinimalConfig、单核、VLEN128、同一编译工具和选项，仅 VDOT_O1_HANDOFF 为0/1。",
        "O1复用上一轮已通过全核回归的固定EMU；T14从相同硬件输入生成。本轮测试程序均实际重新运行，不继承旧性能数字。", "",
        "两模式共享16个冻结ELF/bin、参考库、flash和seed=1。四场景各3数据集、每组4轮正式配对；保留first/warmup，不扣计时开销。",
        "主campaign共36次全核运行、478个校验窗口，其中192个正式性能窗口。另有1次O1校准探针（11窗口），不计入本表统计。",
        "每个模式每个场景每种方法有12个正式样本。加速比=sum(RVV cycles)/sum(vdot cycles)，周期降低=1-O1/T14。", "",
        "| 场景 | T14 vdot均值 | O1 vdot均值 | 周期降低 | T14相对RVV | O1相对RVV |", 
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in stats:
        t, o = row["t14"], row["o1"]
        lines.append(f'| {LABELS[row["scenario"]]} | {t["custom_mean_cycles"]:.3f} | {o["custom_mean_cycles"]:.3f} | '
                     f'{100*row["custom_cycle_reduction"]:.2f}% | {t["speedup_ratio_of_sums"]:.3f}× | {o["speedup_ratio_of_sums"]:.3f}× |')
    lines += ["", "每项RVV分母均为该模式本次实测值：", "",
              "| 场景 | T14 RVV均值 | O1 RVV均值 | T14 vdot范围 | O1 vdot范围 |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for row in stats:
        t, o = row["t14"], row["o1"]
        lines.append(f'| {LABELS[row["scenario"]]} | {t["rvv_mean_cycles"]:.3f} | {o["rvv_mean_cycles"]:.3f} | '
                     f'{t["custom_min_cycles"]}–{t["custom_max_cycles"]} | {o["custom_min_cycles"]}–{o["custom_max_cycles"]} |')
    batch = next(r for r in stats if r["scenario"] == "batch")
    lines += ["", f'独立batch本次周期降低为{100*batch["custom_cycle_reduction"]:.2f}%，'
              f'预定20%目标{"达到" if batch["custom_cycle_reduction"] >= 0.2 else "尚未达到"}。'
              "该目标是工程投入参考，不是官方计分门槛。", "",
              "超过2%的预定退化调查项：" + ("、".join(LABELS[r["scenario"]] for r in stats if r["investigation_required"]) or "无"), "",
              "原始整数计数器、所有阶段及重放样本保存在samples.csv；逐模式均值、中位数、范围与指令数见summary.csv，配对差异见comparison.csv。",
              "batch128的额外四个重放作业逐seq周期/指令数一致，只证明代表镜像的确定性，不作为独立统计样本或全部镜像重放证明。", "",
              "窗口包含循环与屏障开销；single窗口不是FU固有延迟，cycles/dot不是硬件II。batch4对同一输入产生四个独立结果，不能直接宣传为任意GEMV收益。",
              "本轮不推导最高频率、面积、功耗、PPA或官方排名。O1默认仍关闭；最终采用结合周期收益、接口成本、应用实例与独立复现决定。", "",
              "构建首次因辅助C++固定输出路径停止，修正外置目录配套文件后继续同一份新生成RTL的编译；保留全部失败与恢复回执。",
              "恢复包装脚本曾将可变宿主time.log误列为生成输入；事前记录范围修正，以独立最终检查核验全部不可变生成文件。原日志未改、未重跑硬件来掩盖记录。", ""]
    (output / "性能结果与工程记录.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "jobs", "windows", "measured_windows", "original_evidence_unchanged")}))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.campaign, args.output))
