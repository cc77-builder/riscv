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
    require(result["status"] == "BEFORE_AFTER_PAIRED_PERFORMANCE_PASS", "campaign is not accepted")
    before = {str(p): sha(p) for p in campaign.rglob("*") if p.is_file()}
    artifacts = json.loads((campaign / "artifact-pins.json").read_text())
    compare.verify_hashes(artifacts)
    check = compare.load_module("offline_windows", compare.ROOT / "team/workloads/unified-vdot/check.py")
    observers={
        "before":compare.load_module("offline_o1",compare.ROOT/"team/optimizations/o2/fullcore/analyze.py"),
        "after":compare.load_module("offline_o2",compare.ROOT/"team/optimizations/o2/fullcore/analyze.py")}
    gate=compare.load_module("offline_gate",compare.ROOT/"team/optimizations/o1/audit/runtime_gate.py")
    fatal=compare.load_module("offline_fatal",compare.ROOT/"team/optimizations/o2/fullcore/workloads/check.py")
    state=json.loads((campaign/"state.json").read_text())
    for saved in (campaign/"checker-snapshots").rglob("*"):
        if saved.is_file():
            relative=saved.relative_to(campaign/"checker-snapshots")
            require(compare.sha(compare.ROOT/relative)==compare.sha(saved),
                    "runtime checker snapshot changed: "+str(relative))
            if not (compare.ROOT/relative).is_relative_to(HERE):
                blob=__import__("subprocess").check_output(["git","show",state["source_commit"]+":"+relative.as_posix()],cwd=compare.ROOT)
                require(blob==saved.read_bytes(),"original committed checker changed: "+str(relative))


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
        comparison.append(dict(scenario=row["scenario"], dots=row["before"]["dots"],
                               before_custom_mean_cycles=row["before"]["custom_mean_cycles"],
                               after_custom_mean_cycles=row["after"]["custom_mean_cycles"],
                               custom_cycle_reduction=row["custom_cycle_reduction"],
                               before_over_after=row["custom_before_over_after"],
                               before_rvv_mean_cycles=row["before"]["rvv_mean_cycles"],
                               after_rvv_mean_cycles=row["after"]["rvv_mean_cycles"],
                               before_speedup=row["before"]["speedup_ratio_of_sums"],
                               after_speedup=row["after"]["speedup_ratio_of_sums"],
                               rvv_cycle_reduction=row["rvv_cycle_reduction"],
                               investigation_required=row["investigation_required"]))
    csv_rows(output / "summary.csv", flat)
    csv_rows(output / "comparison.csv", comparison)
    csv_rows(output / "samples.csv", [
        dict(sample, included_in_measured_statistics=(sample["stage"] == "performance"
             and sample["phase"] == "measured" and sample["replay"] == 0))
        for sample in samples])

    receipt = dict(status="OFFLINE_BEFORE_AFTER_PAIRED_RECHECK_PASS", finished_utc=compare.now(),
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
    lines = ["# R3 DIV取消关钟：修复前后同镜像周期结果", "",
        "before 为原H1，after 为H1加DIV关钟修复。36项实际运行已完成，并从原始日志重算。", "",
        "| 场景 | 修复前vdot cycles | 修复后vdot cycles | 修复前RVV cycles | 修复后RVV cycles | 修复后RVV/vdot |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in stats:
        a,b=row["before"],row["after"]
        lines.append(f'| {LABELS[row["scenario"]]} | {a["custom_mean_cycles"]:.3f} | {b["custom_mean_cycles"]:.3f} | {a["rvv_mean_cycles"]:.3f} | {b["rvv_mean_cycles"]:.3f} | {b["speedup_ratio_of_sums"]:.6f}x |')
    lines += ["", f'96对正式窗口；不退化={receipt["cycle_nonregression_pass"]}；完全相同={receipt["exact_measured_cycle_equality"]}；退化窗口数={len(receipt["regressions"])}。',
        "478校验窗口含first/warmup和确定性重放；192个正式窗口组成96对。重放不扩充统计样本。",
        "统计仅用DUT周期，不扣开销；不代表GEMV应用、Fmax、面积或功耗。综合/STA由独立cost结果验收。",
        "新控制器、旧检查器、硬件及镜像身份详见campaign原始记录。未推送GitHub。"]
    (output/"RESULT.md").write_text("\n".join(lines)+"\n")
    print(receipt["status"])
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.campaign, args.output))
