# R3 只读成本与时序提取（2026-10-24）

固定审查源码：4669c487f3024ee5fce514c37270297f99066b2a。只解析已封存 H1/O4 公共接口网表、Liberty、STA 报告；没有综合、仿真、fetch/push，也没有改生产代码或旧证据。

## 可复算产物

- extract.py：Python 标准库；读取的 82 项文件均对照原 manifest 核对压缩前后大小/SHA256。
- timing-cost-extraction.json：面积、DFF 分组、专属 own-Q hold MUX 数、原报告路径、所有五档起止点及规范实例别名。
- timing-all-profiles.csv：70 项原 STA 路径摘要。五档是独立敏感性条件，不是所有周期×负载组合。

命令（输出指向新的个人目录即可）：

~~~bash
python3 -B extract.py --repo /path/to/repo --output /path/to/new-extraction
~~~

输出状态 R3_READONLY_TIMING_EXTRACTION_PASS。它只确认资料读数/映射一致，不是新候选验证或时序收敛。输出目录必须不存在；工具拒绝Python -O/-OO。两份原manifest固定SHA绑定，actual_head记录提取时Git HEAD，analyzed_head记录审查锚点；实际硬件身份仍是历史H1/O4封存输入。最终重算位于recheck/，run.json保存命令、退出码和输出哈希，初次提取留作历史。

## 1. 现有映射成本

| 边界 | H1 面积 μm² | DFF | 标准单元 | ICG |
| --- | ---: | ---: | ---: | ---: |
| 独立完整 FU | 17298.246 | 1742 | 8894 | 0 |
| 完整 VFEX4 父级（含 VIDiv/VFDiv） | 284879.882 | 17171 | 203364 | 3 |

父级 VDot 关联 DFF 为1352位：乘积128、结果32、P/R有效位2、P/R控制18+18、P/R性能字段577+577。独立 FU 为1742位，两槽控制仍各213位。这意味着父级消费者已经裁去每槽195位控制字段，不能把独立 FU 裁剪结果当作父级净收益。

固定 Nangate45 Liberty：DFF_X1=4.522，MUX2_X1=1.862，CLKGATETST_X1=3.990 μm²。
两份性能包均各有577个DFF、577个直接 own-Q hold MUX；逐个确认 MUX 输出只接该 DFF 的 D 端且不是顶层输出。因此每份可识别局部存储成本为2609.194+1074.374=3683.568 μm²，两份7367.136 μm²，分别占独立 FU 42.5889%、完整父级2.58605%。

这只是公共接口网表中现有成本归因，绝不是承诺可省的面积上限：字段仍是观察输出，裁去会更改合同；实际全核可能已经DCE；共享控制、缓冲、输出仲裁未归因；重综合净变化不能由删单元加总得到。必须先确认真实消费者/调试配置，不能直接删577位或把其中时间戳合并。

父级两槽控制的DFF加已识别专属MUX成本总共222.376 μm²，占父级0.07806%。这是所有这些字段的局部成本而非安全删除量；ROB/pdest/异常/写使能仍必需。因可裁控制已经大幅DCE，盲目改控制包收益小且风险高。

来源：
- team/optimizations/o2/result-width/h1/H1_RESULT.md:41–50。
- 封存 files/fu-map-01/summary.json、parent-map-01/summary.json。
- 封存 files/cost-comparison-01/summary.json.gz 中 candidate.mapped_metadata、structure_register_groups。
- 本次JSON的 register_groups 对封存 mapped.json 独立逐位核对，Liberty和全部输入哈希同时保存。

## 2. 五档最差 slack（ns）

| 边界 | 1 ns/5 fF | 0.5 ns/5 fF | 2 ns/5 fF | 1 ns/1 fF | 1 ns/20 fF |
| --- | ---: | ---: | ---: | ---: | ---: |
| FU（全为 i2r） | -0.268520 | -0.768520 | +0.731480 | -0.268520 | -0.268520 |
| 完整父级（全为 r2o） | -2.335769 | -2.835769 | -1.335769 | -2.315229 | -2.411886 |

都是同一已映射网表的周期/负载扫描，没有重新映射各档。FU在2 ns条件下通过本次类别的setup检查；完整父级在2 ns下仍未闭合。到达时间包括输入延迟或clock-to-Q，不能倒数成全核Fmax。

nominal主要路径到达时间：
- FU输入乘法路径 i2r 1.190323 ns；P乘积→R结果归约 r2r 1.163404 ns。
- FU ROB取消输入→in_ready 0.636728 ns，slack +0.213272 ns；out_ready→in_ready 0.253743 ns，slack +0.596257 ns。这两类不是同一条路径。
- 父级 VDot输入→乘积寄存器 1.511395 ns；乘积→结果 1.345889 ns。
- 父级 out_ready→in_ready 0.295424 ns；20 fF升为0.413792 ns，相比B0 +89.237 ps，但该档slack仍+0.436208 ns。不能直接解释为真实执行周期退化。

来源：team/optimizations/o2/result-width/h1/timing-comparison.csv；本次CSV对原 summary 和70份路径报告读取绑定。

## 3. 最差路径的真实归属：避免误优化

原始规范实例通过 parent-sta-01/instance-binding.json.gz → parent-map-01/mapped.json.gz 的引脚/别名反查：

| 类别 | 规范实例和真实起止点 | 判断 |
| --- | --- | --- |
| 父级全局 r2r / i2r | c201794 = Vfdiv.vfdivs_1.u_vector_float_divider_r64.fsm_q[0]；c201979 = 同模块 quo_m1_iter_q_f64_0[1] | VFDiv迭代/共享控制，非纯点积归约 |
| 父级 vdot_i2r | src_1[57] → c198612 = Vdot.pProducts_7[15] | 点积输入/乘积路径 |
| 父级 vdot_r2r | c198712 = Vdot.pProducts_0[1] → c201174 = Vdot.rPacket_res_data[18] | 点积归约到结果路径 |
| 父级 vdot_r2o | c198727 = Vdot.rValid → fflags[1]，2.832115 ns | VDot存活状态影响共享仲裁/DIV输出；非点积数据延迟 |
| 全父级最坏 gate_enable | c201794（VFDiv FSM）→ c203361 = dut.ClockGate.impl/E，1.855397 ns | **门控终点是 VFDiv，不是 VDot** |

3个ICG映射：c203361=ClockGate→VFDiv；c203362=ClockGate_1→VIDiv；c203363=ClockGate_2→VDot。最坏门控路径包含18个BUF_X1和1个BUF_X2以及逻辑门，这也提示公共父级flatten+经验wire-load下的扇出/缓冲对结果影响很大，不是布局布线后物理路径。

重要限制：已有 gate_enable.rpt 仅报告全部3个ICG中最差一条，并没有保存每个ICG的单独最差路径。不能用1.855397 ns给VDot门控标价，不能保证修改VDot门控会改善全父级最差STA。门控并行审查已确认O2 VDot占用门控正确，实际候选是共享DIV取消保持位 uncer_en_reg 清理（详见gating报告）；当前H1在36组取消、108拍采样内有72个多余门控脉冲，James历史green版本为0，但该修复与当前组合尚未验证。即使减少多余脉冲，也不能保证改善VFDiv最差门控setup路径，无新面积、时序、活动率测量时没有PPA数字收益。

以上路径名在封存 files/parent-sta-01/nominal/*.rpt 的第1–2行；具体c实例→别名完整保存于本次JSON的parent.path_binding。FU取消路径为 files/fu-sta-01/nominal/i2o.rpt:1，起点flush.robIdx[2]。

## 4. 面向后续候选的排序

1. 先做真实消费者与调试构建配置核查。性能字段在公共接口harness占比大，但只有证明实际全核仍保留且无必要消费者时才值得引入明确配置；若已被DCE，当前生产版再改包结构几乎没有硬件收益。
2. 共享DIV取消保持位清理（详见gating报告）优先作为功能健壮性/无用活动修复；O2 VDot自身占用门控已核查正确。验收须覆盖DIV取消后真正关钟、存活请求继续排空、再接收/复位以及VDot/VIDiv/VFDiv切换，并对当前H1组合重新验证。其价值不能冒充消除了VFDiv最差门控setup延迟，也不能直接写成PPA收益。
3. ready/取消逻辑先保守。已有正slack，20 fF回退应保留；引入registered-ready或额外skid会改变两槽接收合同和II/取消交叠，当前没有可证明周期收益，性价比不高。
4. 如要继续纯时序创新，应单列点积乘法/归约而不是全父级fflags：真实点积相关1.511395/1.345889 ns，虽然值得观察，但增加流水会改变延迟与队列合同且不能解决DIV最差路径。当前评奖目标偏正确性/应用周期，先完成已有组合复现，优先级低于低风险门控修复。
5. 不推荐立即19位结果存储或改P槽乘积宽度。H1已去96位，进一步32→19仅13个DFF理论局部DFF成本58.786 μm²（FU0.340%、父级0.0206%，还未算组合重映射），P槽16位乘积已为INT8×INT8所需宽度；是否值得需先证明不是削弱未来参数扩展。

没有全核面积、真实P&R/CTS/SPEF、功耗/活动率或新cycles测量。只读审查不宣布R3候选实现完成。
