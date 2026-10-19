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
    require(result["status"] == "O1_O2_PAIRED_PERFORMANCE_PASS", "campaign is not accepted")
    before = {str(p): sha(p) for p in campaign.rglob("*") if p.is_file()}
    artifacts = json.loads((campaign / "artifact-pins.json").read_text())
    compare.verify_hashes(artifacts)
    check = compare.load_module("offline_windows", compare.ROOT / "team/workloads/unified-vdot/check.py")
    observers={
        "o1":compare.load_module("offline_o1",compare.ROOT/"team/optimizations/o1/fullcore/analyze.py"),
        "o2":compare.load_module("offline_o2",HERE.parent/"fullcore/analyze.py")}
    gate=compare.load_module("offline_gate",compare.ROOT/"team/optimizations/o1/audit/runtime_gate.py")
    fatal=compare.load_module("offline_fatal",HERE.parent/"fullcore/workloads/check.py")
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
        comparison.append(dict(scenario=row["scenario"], dots=row["o1"]["dots"],
                               o1_custom_mean_cycles=row["o1"]["custom_mean_cycles"],
                               o2_custom_mean_cycles=row["o2"]["custom_mean_cycles"],
                               custom_cycle_reduction=row["custom_cycle_reduction"],
                               o1_over_o2=row["custom_o1_over_o2"],
                               o1_rvv_mean_cycles=row["o1"]["rvv_mean_cycles"],
                               o2_rvv_mean_cycles=row["o2"]["rvv_mean_cycles"],
                               o1_speedup=row["o1"]["speedup_ratio_of_sums"],
                               o2_speedup=row["o2"]["speedup_ratio_of_sums"],
                               rvv_cycle_reduction=row["rvv_cycle_reduction"],
                               investigation_required=row["investigation_required"]))
    csv_rows(output / "summary.csv", flat)
    csv_rows(output / "comparison.csv", comparison)
    csv_rows(output / "samples.csv", [
        dict(sample, included_in_measured_statistics=(sample["stage"] == "performance"
             and sample["phase"] == "measured" and sample["replay"] == 0))
        for sample in samples])

    receipt = dict(status="OFFLINE_O1_O2_PAIRED_RECHECK_PASS", finished_utc=compare.now(),
                   campaign=str(campaign), campaign_result_sha256=sha(campaign / "result.json"),
                   jobs=36, windows=478, measured_windows=192, replay_jobs=4,
                   original_evidence_unchanged=True, new_emu_executed=False,
                   checker_sha256=sha(Path(__file__)), compare_sha256=sha(HERE / "compare.py"),
                   rows=stats, input_files_verified=len(artifacts))
    save(output / "verification.json", receipt)
    lines=[
        "# O1/O2 同镜像公平周期对比：工程测量记录","",
        "本轮G4真实运行与原始日志离线重审完成，本地保存，未推送GitHub。正式T16报告继续后置。","",
        "两模式使用相同429项硬件源码和21236项依赖。O2复用G3固定EMU，O1由相同源码重建；合法的O1/O2协议观察器各自启用，共用T13全局计数，配置和实际编译参数核验通过。",
        "同一16份冻结ELF/bin、正常NEMU、flash、seed1。四场景×3数据集×4轮正式配对，first/warmup保留，不扣计时开销。",
        "共36次新EMU运行、478个校验窗口、192条正式性能样本；额外4次batch代表镜像重放仅检查确定性。每模式每场景每方法12条正式样本。","",
        "| 场景 | O1 vdot均值cycles | O2 vdot均值cycles | O2周期降低 | O1相对RVV | O2相对RVV |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in stats:
        a,b=row["o1"],row["o2"]
        lines.append(f'| {LABELS[row["scenario"]]} | {a["custom_mean_cycles"]:.3f} | {b["custom_mean_cycles"]:.3f} | {100*row["custom_cycle_reduction"]:.2f}% | {a["speedup_ratio_of_sums"]:.3f}× | {b["speedup_ratio_of_sums"]:.3f}× |')
    lines += ["","加速比使用各模式本次实测sum(RVV cycles)/sum(vdot cycles)；硬件收益使用1-sum(O2 custom)/sum(O1 custom)。","",
              "| 场景 | O1 RVV均值 | O2 RVV均值 | O1 vdot范围 | O2 vdot范围 |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for row in stats:
        a,b=row["o1"],row["o2"]
        lines.append(f'| {LABELS[row["scenario"]]} | {a["rvv_mean_cycles"]:.3f} | {b["rvv_mean_cycles"]:.3f} | {a["custom_min_cycles"]}–{a["custom_max_cycles"]} | {b["custom_min_cycles"]}–{b["custom_max_cycles"]} |')
    batch=next(row for row in stats if row["scenario"]=="batch")
    target_met=batch["o2"]["custom_sum_cycles"]*10<=batch["o1"]["custom_sum_cycles"]*9
    receipt["batch_10_percent_target_met"]=target_met
    receipt["regression_investigations"]=[row["scenario"] for row in stats if row["investigation_required"]]
    save(output/"verification.json",receipt)
    lines+=["",f'独立batch相对新测O1周期降低{100*batch["custom_cycle_reduction"]:.2f}%，预定至少10%的工程投入目标'+("达到。" if target_met else "未达到。")+"该目标不是官方计分标准。",
            "超过2%的场景均值退化调查项："+("、".join(LABELS[row["scenario"]] for row in stats if row["investigation_required"]) or "无")+"。","",
            "逐窗口整数计数、全部阶段与重放见samples.csv；各模式均值/中位数/范围、cycles/dot及退休指令见summary.csv，配对比较见comparison.csv。未剔除首次或慢样本。",
            "所有作业均要求退出0、真实DiffTest、完整状态/高位/CSR/哨兵校验、机器码/退休/CSR窗口一致及协议有限排空；严格fatal日志门禁启用。",
            "新O1构建期间固定路径辅助输出已备份、保留新身份并恢复原G3 build；旧O2 EMU保持原字节。构建、源、二进制、镜像及实际工具摘要分别记录。","",
            "single窗口包含屏障与计数器开销，cycles/dot不是FU的II；batch为同一输入的四路独立目的，不等于任意GEMV收益。",
            "本轮结果不产生Fmax/面积/功耗/PPA/官方排名或最终采用结论。O2默认关闭，人工ACK、O3应用/O4时序/O5独立复现仍待完成。"]
    (output/"性能结果与工程记录.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "jobs", "windows", "measured_windows", "original_evidence_unchanged")}))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.campaign, args.output))
