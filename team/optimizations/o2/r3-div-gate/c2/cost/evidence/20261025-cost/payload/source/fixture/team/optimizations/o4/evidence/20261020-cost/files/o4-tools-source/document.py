#!/usr/bin/env python3
"""Generate the engineering record from the audited accepted set."""
import csv,json
from pathlib import Path
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("work",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    evidence=json.loads((a.work/"assessment.json").read_text());assert evidence["audit_pass"]
    results=evidence["results"];out=[]
    out+=["# O4：结构与时序代价评估","", "2026-10-20；本地分支local/o4-cost-20261020，基点676ec737。O4工程评估已完成，成果本地保存，未push；默认模式未切换。正式T16报告继续后置。","",
    "## 结论","", "O2保留了两槽吞吐优势，同时增加保存请求身份和性能字段的成本。完整FU面积增加41.41%；包含完整DIV的真实VFEX4父级面积增加1.25%。两项分母不同，均不等于整核面积增幅。",
    "", "两版乘积、归约模块在同一边界内生成文件逐字节相同；跨FU/parent边界的module主体也相同，仅全局PRINTF宏头部不同。O2没有增加乘法器。时序存在取舍：ready返回路径更短，输入到点积寄存器及最坏门控使能路径略长。当前参考库/约束下，两版均未满足1ns目标。",
    "", "本轮补齐了结构和前布局参考时序证据。建议保留O1作为对照，让O2以候选身份进入O5/T17独立复现；最终模式在G5结合应用收益、代价和人工复核决定。","",
    "## 1. 可比较边界和身份","",
    "- 完整FuncUnit生产接口；真实VFEX4 ExeUnit生产接口，包含VFDiv、VIDiv及全部3处ClockGate。O1/O2分别比较相同端口名称、方向、位宽；输入自由，输出完整可观察。",
    "- MinimalConfig单核，VLEN128、ROB48；FUSED_INPUT=1。O1 HANDOFF/ELASTIC=1/0，O2=0/1；全部T12/T13/O1/O2 trace=0。不使用旧scoreboard/tap top估面积。",
    "- 429项G4硬件文件、21,236项依赖逐项核对，唯一构建文件差异是build.sc新增vdotCost入口；生产src树及两份旧EMU哈希保持一致。本轮不重跑EMU、修改ISA/NEMU/模型或旧封存证据。",
    "- 固定工具：Yosys0.9（1979e0b）、ABC1.01、OpenSTA2.0.17；JDK21、Mill0.12.3、firtool1.62.1。工具deb独立解包，无sudo/系统包升级。",
    "- 固定[OpenROAD Nangate45 typical库](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/bf3f9b344bf7d9d999f199778a722833bccbd33c/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib)，25C/1.10V，时间ns、电容fF；SHA256 8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1。保留原头部和平台许可证。",
    "", "详细约定见[CONTRACT.md](CONTRACT.md)，重建和离线复算见[RUNBOOK.md](RUNBOOK.md)。","",
    "## 2. 结构和面积","", "面积为Liberty cell area之和，未换算为芯片面积。仅含本次边界中的映射单元。","",
    "| 边界/指标 | O1 | O2 | O2变化 |","| --- | ---: | ---: | ---: |"]
    for boundary in ["fu","parent"]:
        m1=results["o1-"+boundary]["mapping"];m2=results["o2-"+boundary]["mapping"]
        for label,key in [("单元面积和","cell_area_sum"),("标准单元数量","cell_count")]:
            v1=m1[key];v2=m2[key];out.append(f"| {boundary} {label} | {v1:.3f} | {v2:.3f} | {(v2/v1-1)*100:+.2f}% |")
        f1=m1["cell_histogram"]["DFF_X1"];f2=m2["cell_histogram"]["DFF_X1"]
        out.append(f"| {boundary} DFF位数 | {f1} | {f2} | {f2-f1:+d}（{(f2/f1-1)*100:+.2f}%） |")
    out+=["", "所有映射单元均在固定库中有定义，未知/未映射单元为0；面积按单元直方图独立求和，与Yosys stat一致。","",
    "完整FU中的寄存器分类：","",
    "| 保存内容 | O1 位 | O2 位 |","| --- | ---: | ---: |",
    "| 8路乘积 | 128 | 128 |","| 完整结果寄存器 | 128 | 128 |","| 状态/有效位 | 2 | 2 |","| 控制与身份字段 | 213 | 426 |","| perfDebugInfo字段 | 577 | 1154 |",
    "| 合计 | 1048 | 1838 |","",
    "额外790位中577位（73.04%）来自多保存一份perfDebugInfo，213位来自控制/身份字段。577位包括9个64位时间/检查点字段及1位eliminatedMove。这里保留了完整生产输出；关闭性能打印没有自动删除这些仍可观察的接口字段。位数比例不能当作功耗比例。",
    "", "算术继续使用8路有符号INT8乘积和7个归约加法节点（四个17位、两个18位、一个19位），生成IR的16位乘法输入包含原INT8的符号扩展；不能把IR的unsigned标注误读为更改了数学语义。结果仍按冻结128位合同保存，本轮没有裁剪寄存器或更改数据通路。",
    "", "真实父级裁剪了未消费的部分vpu字段：Vdot关联Q寄存器为853→1448位，父级总DFF为16675→17267位；其他父级逻辑的寄存器净减少3位，因此总增量为592位。关联子集按原映射Q线网别名定位，经实例绑定与完整连接摘要核验，不把它当作可单独相加的物理分区面积。",
    "", "两版父级均为3个CLKGATETST_X1（每个area=3.99）。原ClockGate低电平锁存TE|E、输出CK&EN；库的CK/E/SE/GCK引脚及16种布尔状态转移一致。原始门控没有短接或常开替代。该审查范围为布尔连接和状态转移，未冒称形式等价或带延迟仿真。","",
    "## 3. 参考时序","",
    "ABC组合映射目标1000ps、BUF_X1驱动、5fF输出负载。STA显式使用1ns周期、0.05ns uncertainty、输入/输出最大延迟各0.1ns、输入和时钟转换0.05ns、输出5fF。时钟理想，采用库默认5K_hvratio_1_1/top wire-load。reset/flush/ready均未加false path；父级testEnable固定为0，范围为功能模式。",
    "", "下表data arrival包含起点时序：i2*包含0.1ns输入延迟，r2*包含clock-to-Q。setup slack越大裕量越好；负值表示当前约束不满足。每项是该类最坏路径，O1/O2最坏起终点可能不同。","",
    "| 边界/路径 | O1 arrival ns | O2 arrival ns | O1 slack ns | O2 slack ns |",
    "| --- | ---: | ---: | ---: | ---: |"]
    timingrows=[]
    for boundary in ["fu","parent"]:
        for mode in ["o1","o2"]:
            for profile in results[mode+"-"+boundary]["timing"]["profiles"]:
                for kind,v in profile["paths"].items():
                    timingrows.append({"boundary":boundary,"mode":mode,"profile":profile["profile"],"path":kind,"period_ns":profile["period_ns"],"load_ff":profile["load_ff"],**v})
        t1=results["o1-"+boundary]["timing"]["profiles"][0]["paths"];t2=results["o2-"+boundary]["timing"]["profiles"][0]["paths"]
        for kind in t1:
            v1=t1[kind];v2=t2[kind];out.append(f"| {boundary}/{kind} | {v1['arrival_ns']:.6f} | {v2['arrival_ns']:.6f} | {v1['slack_ns']:.6f} | {v2['slack_ns']:.6f} |")
    out+=["", "路径含义：r2r=寄存器到寄存器；i2r=输入到寄存器；r2o/i2o=寄存器/输入到输出；ready为out_ready→in_ready。parent的vdot_*限定Vdot关联寄存器作为起点/终点；r2o仍经过完整共享仲裁逻辑，可能到DIV的fflags输出，不能称为纯点积算术延迟。gate_enable是全部3个ICG E端的最坏setup路径，未排除不利终点。",
    "", "FU输入到寄存器arrival 1.186674→1.219926ns，增加2.80%；FU归约r2r接近。真实父级Vdot输入路径1.516260→1.540559ns，增加1.60%；ready返回0.339943→0.274544ns，降低19.24%；最坏门控E路径1.785938→1.915197ns，增加7.24%。这些是固定映射下的路径取舍，不能把某一项较短直接换算为整核提频。",
    "", "父级全局最坏路径涉及完整DIV/共享输出逻辑，O2当前最坏slack较好，但两版均未在1ns、甚至2ns参考目标下实现全父级setup闭合。FU在2ns参考周期下满足本次所查setup类别。没有据此给出整核Fmax。","",
    "## 4. 敏感性与检查闭合","",
    "同一已映射网表，额外检查0.5ns、2ns周期及1fF、20fF输出负载；未对敏感性目标重新综合。","",
    "| 边界/模式 | 1ns/5fF最差slack | 0.5ns/5fF | 2ns/5fF | 1ns/1fF | 1ns/20fF |",
    "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for boundary in ["fu","parent"]:
        for mode in ["o1","o2"]:
            ts=results[mode+"-"+boundary]["timing"]["profiles"]
            values=[min(v["slack_ns"] for v in p["paths"].values()) for p in ts]
            out.append("| "+boundary+"/"+mode+" | "+" | ".join(f"{v:.6f}" for v in values)+" |")
    out+=["", "4个映射、20个正式STA profile和140份路径报告通过完整离线复核。13项主机测试包含吞掉Tcl错误、缺路径、混用两条路径的arrival/slack、动态未约束、缺失pin、面积篡改、未知单元、接口不匹配及DFF被改接等负控。",
    "", "FU每版23个无起点告警逐一对应0/1常量输出；父级每版127个，其中124个常量输出、3个为实际testEnable=0且直接相连的ICG SE测试端点。未豁免动态数据、E使能端点、reset/flush/ready或未知时钟。所有正式工具真实退出码为0，错误文本、无效对象和缺失路径会拒收。",
    "", "## 5. 与已有周期收益合并看取舍","",
    "本轮未新跑性能程序，下表引用[已发布G4/O3结果](../../docs/o2-o3-publication-20261020.md)。","",
    "| 合同/场景 | O1 cycles | O2 cycles | O2周期降低 |",
    "| --- | ---: | ---: | ---: |","| G4独立batch128 | 362.50 | 221.00 | 39.03% |",
    "| O3 reuse/endtoend，4×8 | 166.50 | 164.00 | 1.50% |","| O3 reuse/endtoend，8×32 | 323.50 | 321.50 | 0.62% |",
    "| O3 reuse/endtoend，16×64 | 856.75 | 847.75 | 1.05% |","| O3 reuse/endtoend，4×13 | 212.00 | 209.50 | 1.18% |",
    "", "实际执行时间加速 = (C_O1/C_O2) × (f_O2/f_O1)。上述四个应用点只允许约0.62%–1.50%的频率下降，之后周期优势就可能被抵消；这只是由周期算出的盈亏条件，尚未测得真实实现频率。G4的39.03%不能推广到任意应用，K=13的O2应用仍慢于该合同下较快RVV（0.907×）。",
    "", "O2具有吞吐探索价值；目前应用收益较小，额外保存字段和门控路径成本需要在最终采用前说明。若后续继续做实现优化，可先审查最终消费者是否允许裁剪额外的pPerf/rPacket性能字段，再检查合法性/取消/ready使能扇出；ROB、pdest等身份及冻结输出合同必须保持完整，任何改动都要另开单项验证。本轮未实施这些优化。","",
    "## 6. 证据、失败历史与限制","",
    "工作根：/home/riscv/riscv-lab/o4-cost-20261020。最终合格集合："]
    for k,v in evidence["selection"].items():out.append(f"- {k}：{v[0]} + {v[1]}")
    out+=["", "证据入口：[evidence/20261020-cost](evidence/20261020-cost/README.md)。manifest绑定保存文件及压缩前后SHA；精简包包含最终集合的原始网表/JSON/STA报告、生成命令、源与依赖身份、工具/库版本、许可证及复核程序。失败的大型可重建中间件保留WSL完整原件，external-artifacts.json记录位置/大小/SHA，失败日志和命令进入精简包。",
    "", "保留的失败包括Yosys不支持automatic局部变量、STA初版arrival重复行解析、内部实例名称不一致、导出换行错误、长名称/别名处理超时、OpenSTA不支持拼接赋值左值，以及过严跨边界宏头部比较。最终STA采用直接按标准单元/bit ID序列化的简洁网表，再经Yosys重读；每个单元输入的驱动来源、时钟、常量、参数和输出位拓扑摘要与原映射一致。没有删DIV、改乘法/归约或绕过坏路径。详细失败回执随证据保存。",
    "", "本轮是开源参考单元库下的同条件前布局工程比较。没有实际香山工艺库、布局布线、CTS、SPEF、OCV或活动率功耗分析。5K经验wire-load不能描述约20万单元父级的真实布线。面积和不是芯片版图面积；setup分析不是整核时序签核；寄存器/周期变化不能推算实际功耗、能效、比赛评分或排名。",
    "", "## 7. 计划位置与下一步","",
    "| 步骤 | 状态 |","| --- | --- |","| O0瓶颈/合同 | 完成 |","| O1同拍交接、真实父级及全核 | 完成 |","| O2两槽FU、G1–G4 | 完成 |","| O3应用对照 | 完成 |","| O4结构/参考时序代价 | 本轮完成 |","| O5/T17完整回归与队友干净检出复现 | 待进行 |","| G5最终模式采用、人工确认 | 待进行 |","| O6/T16正式报告、T18演示提交 | 工程冻结后集中开展 |",
    "", "下一步先冻结候选提交和构建选项，由队友在干净目录复现功能/异常/控制门禁与代表性公平性能，并保留版本、命令和真实日志；现有自动回归、拓扑复核和Windows离线复算不能代替队友T17。G5再选择O1或O2作为最终版本。本轮不自动开始O5、不代签成员ACK、不push或切换默认。",""]
    a.output.write_text("\n".join(out))
    fields=["boundary","mode","profile","path","period_ns","load_ff","exists","arrival_ns","slack_ns","startpoint","endpoint"]
    with (a.work/"timing.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(timingrows)
    print(f"O4_ENGINEERING_RECORD_WRITTEN timing_rows={len(timingrows)}")
if __name__=="__main__":main()
