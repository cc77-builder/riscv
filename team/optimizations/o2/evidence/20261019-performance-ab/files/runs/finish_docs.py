"""Finalize engineering status only after all real G4 runs and strict replay."""
from pathlib import Path
import json,hashlib
r=Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
w=Path("/home/riscv/riscv-lab/o2-performance-20261019")
read=lambda p:json.loads(p.read_text())
launch=read(w/"launch-state.json");result=read(w/"campaign-01/result.json");audit=read(w/"results-01/verification.json")
assert launch["status"]=="ALL_COMMANDS_FINISHED" and all(x["exit_code"]==0 for x in launch["stages"])
assert result["status"]=="O1_O2_PAIRED_PERFORMANCE_PASS"
assert audit["status"]=="OFFLINE_O1_O2_PAIRED_RECHECK_PASS" and audit["original_evidence_unchanged"]
assert audit["jobs"]==36 and audit["windows"]==478 and audit["measured_windows"]==192
host=read(w/"host-check-04/verification.json");assert host["status"]=="HOST_CHECK_PASS" and host["tests"]==30
for name,digest in host["source_sha256"].items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==digest,name
profile=read(w/"campaign-01/build-profile.json");assert profile["status"]=="MATCHED_O1_O2_BUILD_PROFILE_PASS"
monitor=read(w/"build-monitor.json")
assert monitor["invocations"] and all(x["sha256"]==profile["compiler_sha256"] and "Ubuntu clang version 19.1.7" in x["version"] for x in monitor["invocations"])
pins={m:read(w/"campaign-01"/(m+"-hardware-pins.json")) for m in ("o1","o2")}
rows=audit["rows"];batch=next(x for x in rows if x["scenario"]=="batch")
labels={"single":"单次点积","chain":"依赖链256","batch":"四路独立点积128","stream":"加载/计算/存储64"}
table=["| 场景 | O1 vdot均值cycles | O2 vdot均值cycles | O2周期降低 | O2相对实测RVV |","| --- | ---: | ---: | ---: | ---: |"]
for row in rows:
    table.append(f'| {labels[row["scenario"]]} | {row["o1"]["custom_mean_cycles"]:.3f} | {row["o2"]["custom_mean_cycles"]:.3f} | {100*row["custom_cycle_reduction"]:.2f}% | {row["o2"]["speedup_ratio_of_sums"]:.3f}× |')
target=audit["batch_10_percent_target_met"]
reg=audit["regression_investigations"]
assessment=f'独立batch相对本次新测O1降低{100*batch["custom_cycle_reduction"]:.2f}%，至少10%的预定工程目标'+("达到" if target else "未达到")+"。"
assessment+="超过2%的场景均值退化调查项："+("、".join(labels[x] for x in reg) if reg else "无")+"。"
summary=dict(status="O1_O2_FAIR_MEASUREMENT_COMPLETE",finished_utc=audit["finished_utc"],rows=rows,
    jobs=36,windows=478,measured_windows=192,representative_replay_jobs=4,
    batch_10_percent_target_met=target,regression_investigations=reg,host_tests=30,
    source_commit=read(w/"campaign-01/state.json")["source_commit"],
    emus={m:dict(sha256=pins[m]["emu_sha256"],source_commit=pins[m]["source_commit"]) for m in pins},
    strict_recheck_sha256=hashlib.sha256((w/"results-01/verification.json").read_bytes()).hexdigest(),
    new_performance_runs=True,github_pushed=False,default_mode_changed=False,PPA_measured=False,final_adoption_decided=False)
(w/"final-summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
body=f"""# O1/O2 同镜像公平周期对比

**G4公平测量及Linux原始日志严格重审完成，本地保存，未推送GitHub。** 完成时间：{audit["finished_utc"]}。正式T16报告继续后置。

{chr(10).join(table)}

{assessment}

## 本次实测范围

两模式使用原16份冻结镜像，实际新跑36项（32次首次镜像运行＋4次代表batch镜像重放），478个校验窗口，192条正式性能窗口。每场景每模式每方法为3数据集×4measured＝12条样本；first/warmup和重放完整保留，重放不增加独立样本数。

周期降低按1-sum(O2 custom)/sum(O1 custom)，加速比按该模式本次实测sum(RVV)/sum(custom)。每组逐dataset/repeat/seq/镜像配对，机器码、工作量及退休指令一致；未扣循环/屏障或空窗开销。历史362.50/678没有作为本次统计输入。single不是FU固有延迟，batch四路同输入独立目的不代表任意GEMV收益。

每个作业通过真实DiffTest、约定输出/128位高位/非scratch寄存器/CSR/哨兵、计数器与全局周期窗口核验，以及各自O1/O2完整协议和有限排空门禁；致命错误文本显式拒绝。冻结manifest明确允许各内核的scratch寄存器范围，scratch_control也须通过；不把允许破坏的scratch当成全部32寄存器逐位相同。额外4次batch重放逐seq周期与退休数一致。30项主机测试通过；全部原始stdout/stderr、真实退出码、版本、输入和检查器摘要保留。

## 可复算材料

[测量合同](CONTRACT.md) · [封存证据](../evidence/20261019-performance-ab/README.md)

原始工作根：/home/riscv/riscv-lab/o2-performance-20261019。results-01下有逐窗口samples.csv、各模式summary.csv、配对comparison.csv和性能结果与工程记录.md；verification.json为严格原流重审。Windows交付目录为D:/yanyi/riscv大赛/doc/O1_O2同镜像性能对比_20261019。

## 硬件与工具身份

| 项目 | O1 | O2 |
| --- | --- | --- |
| 实测EMU SHA-256 | {pins["o1"]["emu_sha256"]} | {pins["o2"]["emu_sha256"]} |
| 构建源码提交 | {pins["o1"]["source_commit"]} | {pins["o2"]["source_commit"]} |
| 来源 | 本轮从相同硬件输入重建 | 复用G3已验收固定EMU |
| O1_HANDOFF/O2_ELASTIC | 1/0 | 0/1 |
| O1_TRACE/O2_TRACE | 1/0 | 0/1 |

429项硬件源码与21236项依赖逐字节相同，MinimalConfig/单核/VLEN128/单线程EMU；共同FUSED_INPUT1、T12_TRACE0、T13_TRACE1。各自合法协议观察器只提供只读观察，共同T13提供全局周期/退休计数。

路径归一化后的实际Verilator/C++命令、七类工具版本日志一致；实际LLVM19.1.7编译器由构建过程/proc记录并核对。j2、12G JVM、O3/O0；最多两个单线程EMU。新O1采用外置产品目录，原G3的1687份非对象生成文件已恢复并验证原始SHA，旧O2 EMU不覆盖。硬件构建身份、运行工具身份与后续文档/封存提交分别记录，不以文档提交冒称重构建。

## 复跑

在完整checkout中使用全新输出目录：

    python3 -B team/optimizations/o2/performance/build_o1.py --output /absolute/new/o1-build
    python3 -B team/optimizations/o2/performance/compare.py --o1-pins /absolute/completed/o1-build/hardware-inputs.json --output /absolute/new/campaign
    python3 -B team/optimizations/o2/performance/results.py --campaign /absolute/completed/campaign --output /absolute/new/results

默认路径绑定本机固定参考库、flash和冻结镜像。不要重启已完成campaign或覆盖封存输出。本轮不是T17新机器完整构建复现。

## 取舍边界

本次确认同镜像的RTL周期收益；没有Fmax/面积/功耗/PPA、官方计分或最终采用结论。O2默认关闭。后续按G5结合O3应用、O4时序/结构与O5/T17独立复现、成员人工ACK决定是否采用，再集中编写T16/T18材料。本任务未自动执行这些后续工作。
"""
(r/"team/optimizations/o2/performance/README.md").write_text(body,encoding="utf-8")
p=r/"OPTIMIZATION.md";s=p.read_text()
lead=f"""## 当前进度：O1/O2 公平性能测量完成

2026-10-19。独立batch128平均cycles {batch["o1"]["custom_mean_cycles"]:.3f}→{batch["o2"]["custom_mean_cycles"]:.3f}，降低{100*batch["custom_cycle_reduction"]:.2f}%；O2相对自身实测RVV为{batch["o2"]["speedup_ratio_of_sums"]:.3f}×。{assessment}

36项新EMU运行、478校验窗口、192正式样本与原始日志严格离线重审通过，见 [G4工程入口](team/optimizations/o2/performance/README.md)。本轮本地保存，未推送；O2默认关闭，无PPA或最终采用结论。下一步G5结合应用、时序/结构和独立复现，正式T16报告后置。

"""
s=s.replace("# 后续优化开发入口\n\n","# 后续优化开发入口\n\n"+lead,1).replace("## 当前进度：O2 G3 全核自动验收通过，下一步 G4","## 前一轮：O2 G3 完成时的进度",1);p.write_text(s)
p=r/"AGENTS.md";s=p.read_text()
s=s.replace("# 团队 Agent 入口\n\n","# 团队 Agent 入口\n\n## 当前状态：O1/O2 G4公平测量完成，本地保存\n\n2026-10-19，local/o2-performance-20261019。先读team/optimizations/o2/performance/README.md及evidence/20261019-performance-ab/README.md。36项真实新运行、478窗口、192正式样本、30主机检查与严格离线重审通过。结果见results-01及final-summary.json；不要重跑完成的campaign或改密封证据。不自动推送/切换默认/G5或代签ACK，正式T16后置。下文保留历史状态。\n\n",1);p.write_text(s)
p=r/"team/optimizations/o2/README.md";s=p.read_text()
new=f'**2026-10-19：G4同镜像公平测量完成。** 独立batch128 {batch["o1"]["custom_mean_cycles"]:.3f}→{batch["o2"]["custom_mean_cycles"]:.3f} cycles，降低{100*batch["custom_cycle_reduction"]:.2f}%，O2相对自身实测RVV {batch["o2"]["speedup_ratio_of_sums"]:.3f}×。全部四场景与取舍见 [G4工程入口](performance/README.md)。本地保存未推送，默认关闭，G5/PPA/最终采用未完成；T16报告后置。以下为G3及早期历史。\n\n'
s=s.replace("# O2 开发入口\n\n","# O2 开发入口\n\n"+new,1);p.write_text(s)
p=w/"CURRENT_TASK.md";p.write_text("# Historical execution/recovery note\n\nThe G4 run and strict Linux recheck are now complete. Read final-summary.json and results-01. The text below is the preserved execution checkpoint, not a new instruction to rerun work.\n\n"+p.read_text(),encoding="utf-8")
print(json.dumps(dict(status=summary["status"],assessment=assessment,rows=rows),ensure_ascii=False))
