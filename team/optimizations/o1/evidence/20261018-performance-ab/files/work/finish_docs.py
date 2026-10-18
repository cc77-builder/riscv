"""Publish local engineering status from accepted offline measurements."""
from pathlib import Path
import json

W = Path(__file__).absolute().parent
R = Path("/home/riscv/riscv-lab/zjhwork2-review-20261018/repo")
B = R / "team/optimizations/o1"
P = B / "performance"
a = json.loads((W / "results-01/verification.json").read_text())
assert a["status"] == "OFFLINE_T14_O1_PAIRED_RECHECK_PASS"
assert a["original_evidence_unchanged"] and not a["new_emu_executed"]
rows = a["rows"]
assert not any(x["investigation_required"] for x in rows)
batch = next(x for x in rows if x["scenario"] == "batch")
summary = (f'独立batch128平均周期 {batch["t14"]["custom_mean_cycles"]:.2f}→'
           f'{batch["o1"]["custom_mean_cycles"]:.2f}，降低{100*batch["custom_cycle_reduction"]:.2f}%；'
           f'O1相对实测RVV为{batch["o1"]["speedup_ratio_of_sums"]:.3f}×。')
launch = json.loads((W / "launch-01/command.json").read_text())
t14 = json.loads((W / "t14-build-final-01/hardware-inputs.json").read_text())
o1 = json.loads((W / "campaign-01/o1-hardware-pins.json").read_text())
labels = {"single":"单次点积","chain":"依赖链256","batch":"独立批量128","stream":"加载/计算/存储64"}
table = ["| 场景 | T14均值cycles | O1均值cycles | 周期降低 | O1相对RVV |",
         "| --- | ---: | ---: | ---: | ---: |"]
for x in rows:
    table.append(f'| {labels[x["scenario"]]} | {x["t14"]["custom_mean_cycles"]:.3f} | '
                 f'{x["o1"]["custom_mean_cycles"]:.3f} | {100*x["custom_cycle_reduction"]:.2f}% | '
                 f'{x["o1"]["speedup_ratio_of_sums"]:.3f}× |')
entry = ("# T14/O1 同镜像公平性能比较\n\n本轮真实运行及完整离线复核完成，成果本地保存。正式T16报告继续后置。\n\n"
         + summary + "\n\n" + "\n".join(table) + "\n\n"
         "36次主campaign运行、478个校验窗口通过，其中192个为正式性能窗口；另有1次11窗口O1校准探针不计入统计。"
         "额外4次batch128全新EMU重放逐seq周期与退休指令数一致，不作为独立统计样本。最后22项主机检查通过。\n\n"
         "[测量合同](CONTRACT.md) · [密封证据](../evidence/20261018-performance-ab/README.md) · "
         "[完整结果](../evidence/20261018-performance-ab/files/work/results-01/性能结果与工程记录.md)\n\n"
         "两模式使用完全相同的16份ELF/bin、参考库、flash和seed=1；427个硬件文件、21236个依赖文件一致，"
         "实际编译器clang19.1.7及C++/硬件生成参数一致（仅归一化输出路径）。唯一功能开关差异为VDOT_O1_HANDOFF=0/1，"
         "共同设置FUSED_INPUT=1、O1_TRACE=1、T12_TRACE=0、T13_TRACE=1，MinimalConfig/单核/VLEN128/EMU_THREADS=1。\n\n"
         "O1复用原完整回归的固定EMU，T14本次从同一组输入生成并编译；本轮工作负载全部实际重跑。"
         "T14初次外置目录构建缺少固定输出的辅助源文件，复制本次生成文件后继续编译；旧恢复脚本曾误固定宿主time.log，"
         "事前记录范围修正，并通过finalize_t14.py核验全部不可变生成输入。失败、恢复和最终回执均保留；当前恢复脚本已修正并有专项测试。\n\n"
         f'O1硬件源码18c0ce08，EMU {o1["emu_sha256"]}。\n\n'
         f'T14生成源码 {t14["source_commit"]}，继续编译源码 {t14["compile_source_commit"]}，EMU {t14["emu_sha256"]}。\n\n'
         f'正式运行器源码 {launch["source_commit"]}。后续结果导出工具独立记录身份，不改原始结果。\n\n'
         "工作根 /home/riscv/riscv-lab/o1-performance-20261018；本地分支local/o1-performance-20261018。"
         "从完整WSL仓库执行，输出路径须全新：\n\n"
         "    python3 -B team/optimizations/o1/performance/compare.py --output /absolute/new/campaign\n"
         "    python3 -B team/optimizations/o1/performance/results.py --campaign /absolute/completed/campaign --output /absolute/new/results\n\n"
         "默认入口绑定本机的固定镜像、二进制与参考库。换机需恢复原统一测试镜像tar并显式更新入口路径、重核摘要；"
         "本轮不是T17干净机器完整构建复现。\n\n"
         "窗口包含循环和屏障开销，不扣空窗；batch为同一输入的四路独立目的，不等于实际GEMV收益。"
         "本轮没有Fmax/PPA结论。O1默认关闭，未推送GitHub；团队人工ACK、O3应用/O4时序代价及O5/T17复现仍待完成。\n")
(P/"README.md").write_text(entry,encoding="utf-8")
perf = dict(status="O1_PAIRED_CYCLE_PERFORMANCE_PASS", performance_measured=True, new_emu_jobs=36,
            extra_calibration_probe_jobs=1, validated_windows=478, measured_windows=192,
            deterministic_replay_jobs=4, final_host_tests=22, default_o1_enabled=False,
            new_github_push=False, ppa_measured=False, t17_complete=False, human_ack_complete=False,
            execution_source_commit=launch["source_commit"], t14_emu_sha256=t14["emu_sha256"],
            o1_emu_sha256=o1["emu_sha256"], receipt="../evidence/20261018-performance-ab/README.md", rows=rows)
(P/"verification.json").write_text(json.dumps(perf,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
p=R/"AGENTS.md"; text=p.read_text(); marker="## 前一轮：O1 全核功能与控制回归、严格离线复核通过"
assert marker in text
header=("# 团队 Agent 入口\n\n## 当前任务：T14/O1 同镜像公平性能比较完成，本地保存\n\n"
        +summary+"36次主运行、478窗口、192正式样本、4次额外确定性重放及完整原始日志离线复算通过；最后22项主机检查通过。\n\n"
        "见 [工程入口](team/optimizations/o1/performance/README.md)、[合同](team/optimizations/o1/performance/CONTRACT.md) 和 "
        "[证据](team/optimizations/o1/evidence/20261018-performance-ab/README.md)。实际执行检查器、受测硬件源码、二进制和后续导出工具身份分别记录。"
        "不要重启已经完成的campaign或覆盖原始/密封证据。\n\n"
        "分支local/o1-performance-20261018，工作根/home/riscv/riscv-lab/o1-performance-20261018。"
        "成果本地保存，未推送GitHub，O1默认关闭；O2按收益/接口成本另行决定，O3应用、O4时序代价、O5/T17独立复现及人工ACK仍未完成，正式T16报告继续后置。\n\n")
p.write_text(header+text[text.index(marker):],encoding="utf-8")
p=R/"OPTIMIZATION.md";text=p.read_text().replace("## 当前任务：","## 前一轮：",1)
text=text.replace("# 后续优化开发入口\n\n","# 后续优化开发入口\n\n## 当前任务：O1公平周期对比完成\n\n"
                  +summary+"36次主运行及完整离线复算通过，其他场景数据见 [工程入口](team/optimizations/o1/performance/README.md)。\n\n"
                  "O1默认关闭，成果本地保存，未推送。O2按收益/成本另行决定，O3应用/O4时序与O5/T17复现仍待推进；正式T16报告后置，尚无PPA或人工ACK结论。\n\n",1)
p.write_text(text,encoding="utf-8")
p=R/"team/README.md";text=p.read_text()
text=text.replace("# 三人团队：项目计划与开发入口\n\n","# 三人团队：项目计划与开发入口\n\n"
                  "> **T14/O1 同镜像公平性能比较完成，本地保存。** "+summary+
                  "36次主运行、478窗口及完整离线复算通过。见 [性能入口](optimizations/o1/performance/README.md) · "
                  "[证据](optimizations/o1/evidence/20261018-performance-ab/README.md)。O1默认关闭，未推送；PPA/T17/人工ACK仍待完成，正式T16报告后置，下方按历史时点阅读。\n\n",1)
text=text.replace("| 内容 | 入口 |\n| --- | --- |\n","| 内容 | 入口 |\n| --- | --- |\n"
                  "| T14/O1 同镜像公平性能比较 | [结果与复现](optimizations/o1/performance/README.md) · [证据](optimizations/o1/evidence/20261018-performance-ab/README.md) |\n",1)
p.write_text(text,encoding="utf-8")
p=B/"README.md";text=p.read_text().replace("当前任务：","前一轮：",1)
text=text.replace("# O1：受控 vdot→vdot 同拍交接候选\n\n","# O1：受控 vdot→vdot 同拍交接候选\n\n"
                  "**当前任务：T14/O1 同镜像公平周期比较完成。** "+summary+
                  "见 [性能入口](performance/README.md) 与 [证据](evidence/20261018-performance-ab/README.md)。"
                  "默认O1关闭，本轮本地保存；正式T16报告后置，PPA/T17和人工ACK未完成。下方是各层历史结果。\n\n",1)
p.write_text(text,encoding="utf-8")
p=B/"verification.json";d=json.loads(p.read_text())
d.update(status="O1_FULLCORE_AND_PAIRED_PERFORMANCE_PASS",performance_measured=True,
         fullcore_receipt=d["receipt"],receipt="evidence/20261018-performance-ab/README.md",
         performance_receipt="performance/verification.json",performance_validation_pass=True,
         performance_new_emu_jobs=36,performance_validated_windows=478,performance_measured_windows=192,
         deterministic_replay_jobs=4,performance_final_host_tests=22,performance_rows=rows,
         hardware_validation_scope="Pinned MinimalConfig single-core function/exception/control and four-scenario paired cycle measurements; no Fmax/PPA, T17 or human ACK acceptance.",
         next_step="Review O1 adoption/O2 cost; O3 application, O4 timing/PPA and O5/T17 reproduction remain")
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
state=json.loads((W/"WORK_STATE.json").read_text())
state.update(status="PAIRED_PERFORMANCE_VERIFIED_PENDING_ARCHIVE",paired_performance_pass=True,offline_recheck_pass=True,
             main_jobs=36,validated_windows=478,measured_windows=192)
(W/"WORK_STATE.json").write_text(json.dumps(state,indent=2)+"\n")
print("Engineering entries updated from strict accepted measurements.")
