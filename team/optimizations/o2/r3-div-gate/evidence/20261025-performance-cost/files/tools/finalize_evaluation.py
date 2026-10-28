#!/usr/bin/env python3
"""Produce source-bound R3 engineering result after both original campaigns finish."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4]
MODULE=Path(__file__).resolve().parent
LAB=ROOT.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def main():
    perf=LAB/"o2-r3-div-gate-performance-20261025"
    cost=LAB/"o2-r3-div-gate-cost-20261025"
    pr=read(perf/"campaign-01/result.json")
    pv=read(perf/"results-01/verification.json")
    cs=read(cost/"campaign-state.json")
    cr=read(cost/"results-01/summary.json")
    gd=read(cost/"generation-diff.json")
    need(pr["status"]=="BEFORE_AFTER_PAIRED_PERFORMANCE_PASS"
         and pv["status"]=="OFFLINE_BEFORE_AFTER_PAIRED_RECHECK_PASS","cycle audit incomplete")
    need(pr["cycle_nonregression_pass"] and pr["exact_measured_cycle_equality"],"measured cycles changed")
    need(cs["status"]=="passed" and cs["frozen_inputs_unchanged"]
         and cr["status"]=="R3_DIV_GATE_COST_AUDIT_PASS","cost audit incomplete")
    need(gd["status"]=="R3_COST_GENERATED_SCOPE_PASS"
         and gd["diagnostic_body_excluded_by_actual_mapping"],"generation review missing")
    identity=read(cost/"candidate-inputs.json")
    for name,digest in identity["files"].items():need(sha(Path(name))==digest,"final input drift: "+name)
    need(subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()==identity["source_commit"],
         "source HEAD drift")
    need(not subprocess.check_output(["git","diff","HEAD","--","src","build.sc","Makefile","scripts"],cwd=ROOT),
         "production worktree changed")
    f=cost/"evaluation-final-validation.json";need(not f.exists(),"final receipt exists")
    receipt=dict(status="R3_DIV_GATE_CYCLE_COST_VALIDATION_PASS",
        finished_utc=datetime.now(timezone.utc).isoformat(),source_commit=identity["source_commit"],
        actual_new_emu_jobs=36,checked_windows=478,formal_pairs=96,regressed_pairs=0,
        deterministic_replay_jobs=4,host_checks=62,new_mappings=2,new_sta_profiles=10,new_path_reports=70,
        before_ppa_reused=True,source_and_inputs_unchanged=True,github_push=False,human_ack=False,
        power_measured=False,whole_core_ppa_measured=False,
        receipts={str(p):sha(p) for p in [perf/"campaign-01/result.json",perf/"results-01/verification.json",
            cost/"campaign-state.json",cost/"results-01/summary.json",cost/"generation-diff.json"]})
    f.write_text(json.dumps(receipt,indent=2)+"\n")
    need(not (MODULE/"cost/results").exists(),"cost delivery exists")
    shutil.copytree(cost/"results-01",MODULE/"cost/results")
    lines=["# R3 DIV取消关钟修复：周期不退化、面积与STA结果","",
        "2026-10-25。**本轮36项EMU、严格原文复算、两份新映射及十组新STA均已完成。96对正式窗口周期完全相同，退化0。未推送GitHub。**",
        "这是工程验证记录，正式比赛报告后置。独立FU面积/时序与修复前一致；父级整体映射变化见下表。",
        "",
        "## 1. 受测身份与公平条件","",
        "| 对象 | 修复前 | 修复后 |","| --- | --- | --- |",
        "| 实现 | O2两槽＋H1低32位保存 | O2＋H1＋DIV取消关钟修复 |",
        "| 硬件源码 | 8b5024fcbd96986871cc40ce8c9fb71a67c495eb | 0f12df675378556670afd0dd2153f47fcb330610 |",
        "| EMU SHA256 | e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747 | 2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8 |",
        "",
        "硬件429份Git源码、21236份依赖、每版1672份生成产物、实际编译命令和七类工具版本均经核验。生产源码仅ExeUnit.scala不同。",
        "同一MinimalConfig/单核单线程/O2与T13观察配置、128MB、seed=1、正常NEMU和flash；208份冻结软件载荷不变。",
        "正常NEMU SHA256：efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4。",
        "完整生成物还包含已审查的Git标识、只读诊断日志、顶层注释及标量FDiv公共子表达式内联差异；没有声称全设计形式等价。",
        "",
        "## 2. 同镜像周期","",
        "| 场景 | 修复前vdot均值 | 修复后vdot均值 | 两版RVV均值 | 两版RVV/vdot |",
        "| --- | ---: | ---: | ---: | ---: |"]
    labels={"single":"单次点积1","chain":"依赖链256","batch":"四路独立批量128","stream":"加载/计算/存储64"}
    for row in pr["rows"]:
        a,b=row["before"],row["after"]
        lines.append(f'| {labels[row["scenario"]]} | {a["custom_mean_cycles"]:.3f} | {b["custom_mean_cycles"]:.3f} | {b["rvv_mean_cycles"]:.3f} | {b["speedup_ratio_of_sums"]:.6f}× |')
    lines+=["","单位均为DUT全局cycles。每场景三组数据×四轮，vdot和RVV分别配对；192正式窗口形成96对，每对差值均为0，退休指令与工作量相同。",
        "共478个校验窗口，保留first/warmup；四次额外batch重放完全一致，不加入正式样本。36项实际EMU均通过完整128位结果、DiffTest、GOOD TRAP、窗口计数和O2生命周期/排空检查。",
        "加速比为本轮各场景sum(RVV cycles)/sum(vdot cycles)，不扣计时开销，不用宿主时间。**本修复没有提高cycles加速比，也没有使这些固定微基准退化。**",
        "详见[逐窗差值](performance/results/paired-windows.csv)、[全部样本](performance/results/samples.csv)、[复算回执](performance/results/verification.json)。",
        "",
        "## 3. 同约束综合与面积","",
        "修复前复用已封存H1的205份完整原始生成/综合/STA载荷并逐字节核验；修复后实际重新生成、综合和STA，未拿旧值冒充新运行。",
        "两边使用相同完整生产接口、相同未修改O4脚本、Yosys0.9/ABC1.01/OpenSTA2.0.17及其动态库、Nangate45 typical 25°C/1.1V库。",
        "ABC目标1000ps、BUF_X1驱动、5fF映射负载。面积是Liberty单元面积之和，单位μm²，非芯片布局面积。",
        "",
        "| 边界 | 修复前面积 | 修复后面积 | 增量 | 增量比例 | DFF数量 | ICG数量 |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |"]
    for boundary,item in cr["results"].items():
        a,b=item["before"],item["after"]
        lines.append(f'| {boundary} | {a["area"]:.3f} | {b["area"]:.3f} | {item["area_delta"]:+.3f} | {item["area_delta_percent"]:+.6f}% | {a["dff_count"]}→{b["dff_count"]} | {a["icg_count"]}→{b["icg_count"]} |')
    lines+=["","两版VDot结果仍保存32位，公开输出128位高96位清零，算术与控制/perf寄存器分组不变；父级DIV输出不能被误当作高位常零。",
        "FU生成5份文件完全相同。父级58份生成文件仅ExeUnit.sv和LogPerfEndpoint.sv不同；后者只改变打印顺序，并被实际SYNTHESIS定义排除。",
        "",
        "## 4. STA及敏感性","",
        "同一映射的五档条件为1ns/5fF、0.5ns/5fF、2ns/5fF、1ns/1fF、1ns/20fF。理想时钟、0.05ns uncertainty与transition、0.1ns输入/输出delay、0.05ns输入transition、5K_hvratio_1_1线负载。parent testEnable=0，不额外排除ready/reset/flush路径。",
        "每版70条类别/档位路径对照，父级网表规范化经逐bit拓扑绑定；未知单元和动态未约束端点拒收。以下nominal到达时间包含对应外部输入延迟；同类最差端点可以变化，不能解释为同一物理路径。",
        "",
        "| 边界/路径 | 修复前arrival(ns) | 修复后arrival(ns) | 差值(ps) | 修复后slack(ns) |",
        "| --- | ---: | ---: | ---: | ---: |"]
    all_rows=[]
    for boundary,item in cr["results"].items():
        for profile,data in item["timing_changes"].items():
            for name,t in data["paths"].items():
                all_rows.append((boundary,profile,name,t))
                if profile=="nominal":
                    lines.append(f'| {boundary}/{name} | {t["baseline"]["arrival_ns"]:.6f} | {t["candidate"]["arrival_ns"]:.6f} | {t["arrival_delta_ns"]*1000:+.3f} | {t["candidate"]["slack_ns"]:.6f} |')
    slow=[x for x in all_rows if x[3]["arrival_delta_ns"]>0]
    fast=[x for x in all_rows if x[3]["arrival_delta_ns"]<0]
    nominal=[x for x in all_rows if x[1]=="nominal"]
    lines+=["",f'70条类别/档位比较中，到达时间变大{len(slow)}条、变小{len(fast)}条、相同{70-len(slow)-len(fast)}条。全部差值和端点见[完整时序CSV](cost/results/timing.csv)。',
        f'nominal所报路径中，修复前有{sum(x[3]["baseline"]["slack_ns"]<0 for x in nominal)}类负slack，修复后有{sum(x[3]["candidate"]["slack_ns"]<0 for x in nominal)}类。流程审计PASS不等于1ns收敛；本轮没有获得整核Fmax、布线后时序或功耗。',
        "",
        "最差端点回溯已保存path-endpoint-review.json：前后r2r均是VFDiv的fsm_q[0]到quo_m1_iter_q_f64_0[1]，i2r最差起点从vsew输入变为src输入；gate_enable最差起点从vfdivs_1切到vfdivs_0，终点仍是浮点DIV的ICG。不能因其属于DIV就忽略父级时序退化，也不能把最差路径切换解释为同一固定路径的变化。",
        "",
        "## 5. 结论与限制","",
        "本次修复解决匹配DIV取消后的无效关钟保持；前轮严格局部测试已证明48取消窗口/144个后续采样拍无多余钟脉冲。新全核回归与本轮周期检查进一步支持保留其行为正确性和固定微基准性能。",
        "这是门控正确性修复，不是新的吞吐提速。面积/时序取舍必须按父级完整映射结果判断，不能将消除时钟脉冲直接换算成功耗百分比。",
        "建议保留这项修复作为工程候选：周期未退化、空闲关钟缺陷已消除、父级面积小幅下降；但它不是时序全面改善版。冻结版本前应由队友复核nominal父级r2r约+94ps、i2r约+119ps及门控使能约+33ps的取舍。若下一项专门做时序优化，应另立候选和同约束对照，不改写本轮结果。",
        "当前本地源码仍为0f12df6；未自动切换团队默认版本、未推送、未代签人工ACK；本轮不转授GEMV、LLM、T17或其他硬件版本的资格。",
        "",
        "## 6. 复查、失败记录与交付","",
        "新增主机检查共62项：周期配对30、验收身份6、沿用成本审计20、归档拒错6，均通过。保留首次预检的验收JSON字段适配失败，以及生成范围检查首次遗漏日志模块的拒绝；二者均发生在检查工具/范围审查，不是EMU或综合功能失败，未删除原记录。",
        "原始周期根：/home/riscv/riscv-lab/o2-r3-div-gate-performance-20261025。",
        "原始综合根：/home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025。",
        "原H1完整build：/home/riscv/riscv-lab/o2-h1-build-before-r3-div-gate-20261024。",
        "原始stdout/stderr、真实退出码、命令、源/依赖/镜像/工具/库哈希及所有路径报告随归档保存；EMU/NEMU和EDA可执行文件保留在本地，用SHA绑定，不放进日常Git提交。",
        "只读复算入口为performance/recheck.py和cost/compare.py；必须传新的输出路径。归档字节核验使用package_evaluation.py --verify ARCHIVE --receipt NEW_JSON；字节检查不能冒充重新仿真或重新STA。",
        "下一步是依据本轮成本结果完成工程取舍与队友复核，用户授权后再发布zjhwork。本轮没有自动开展新的RTL优化。",""]
    (MODULE/"PERFORMANCE_COST_RESULT.md").write_text("\n".join(lines))
    print(receipt["status"])
if __name__=="__main__":main()
