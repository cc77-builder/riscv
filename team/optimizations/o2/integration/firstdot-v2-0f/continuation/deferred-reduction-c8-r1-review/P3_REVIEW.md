# P3 FP32→QKV：只读准入评审

**GO：值得进入一个独立的最小迁入与宿主门禁工作包；本轮不实施迁入。目标EMU运行、默认采用和新性能资格仍为NOT_READY。** 这是关闭C8分段归约具体候选后的路线选择，不重开P4或重复8×32同类探针。

固定供体：ffd668bf1bc80850d382f514d13bb00316c85582。只读了7份源/工程文档，内容的Git blob全部重新计算相符，清单见[p3-reference/manifest.json](p3-reference/manifest.json)。供体是历史固定快照，不读取或改写队友正在运行的tailrows工作区；Issue #2最新保护事件6511950608仍有效，不推断其空闲。

## 1. 为什么值得有限投入

供体提供真实FP32输入→一次共同量化→三个Q/K/V完整投影的普通C接口，覆盖应用中的输入量化和浮点尺度处理，作用边界比273周期的C8叶调用更接近实际消费者。它提供TA和具名强FR两个完整分支、回退入口与输入合法域，不需要更改生产dot8 ISA。源中boundary只调用一次qkv_quantize，再依次对三个context调用同一个kernel；量化共享是已有行为，不能重复登记为新优化。

供体报告的最慢TA245820、最快FR254665 cycles，保守周期减少3.4731903%；四FR锚点跨度0.2261795%，恢复/重放一致。这只是选择研究对象的历史证据，本轮没有复算完整目标归档，更没有在本项目0f上新测。[供体结果](https://github.com/cc77-builder/riscv/blob/ffd668bf1bc80850d382f514d13bb00316c85582/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/active/target/RESULT.md)

本方向的潜在收益是建立当前硬件上可使用、可回退的完整应用入口，以及同一FP32→QKV边界的公平数据。**不能预告新版本比原C8再快3.47%，也不能把273cycles与约25万cycles横比。** 两者尺寸、计算量和窗口完全不同。

## 2. 最小功能与数据合同

| 项目 | 已读源中的明确约束 |
| --- | --- |
| 尺寸 | D=288、GS=32；Q/K/V各288×288权重；VLEN128 |
| 输入 | 288个FP32，1152B，只读；固定层0、位置0计时，位置1功能；确定性未训练权重 |
| 量化 | 每组32元素求最大绝对值；binary32/RNE除法；RMM整数转换对应中点远离零；不换成倒数乘法 |
| 共享输出 | 288B int8和9个FP32尺度，共324B；一次量化供三个投影共用 |
| 每投影 | packed82944B、权重尺度10368B、输出1152B、slots128B；slots16B对齐 |
| 普通ABI | RV64/lp64d；qkv_context为7指针/56B；边界额外栈16B；callee-saved与sp保持 |
| 方法 | TA=q288_tail_vdot；FR=q288_fused_rvv4；同量化器、同数据、同Q/K/V调用边界 |
| 返回状态 | vl=8、vtype=0、vstart=0、vcsr=7；FRM保持；向量寄存器可破坏 |
| 浮点状态 | 输入合法域允许NX/UF，拒绝NV/DZ/OF；不能把非零fflags一概判错 |
| 窗外内容 | 权重pack、RMSNorm、RoPE、attention、KV写入、FFN、classifier、完整token均不在窗口内 |
| 非目标结论 | 不包含训练模型质量、完整LLM吞吐、最优RVV量化或新ASIC资格 |

必须拒绝全零组、NaN、Inf、scale下溢为零、有限正scale但商舍入超int8。量化合法不自动保证后续投影有限；需保持FP32计算顺序、两次尺度相乘及别名/读写范围要求。三个projection必须共享同一x/xs，所有可写缓冲与只读输入及其他可写区间分离。[固定合同](https://github.com/cc77-builder/riscv/blob/ffd668bf1bc80850d382f514d13bb00316c85582/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/active/target/CONTRACT.md)、[普通C接口](https://github.com/cc77-builder/riscv/blob/ffd668bf1bc80850d382f514d13bb00316c85582/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/active/README.md)

## 3. 已确认与尚缺项

| 检查 | 本轮状态 | 下一轮动作 |
| --- | --- | --- |
| 固定来源、合同和普通C边界 | PASS：7份原文及Git blob一致 | 作为来源，不改写原资格 |
| boundary.h / boundary.S | 已读：一次量化、三次显式kernel调用、16B栈 | 固定完整对象与ABI，验证实际GNU产物 |
| export.py入口 | 已读：variant=tail固定generator SHA256为8369f553aaf642cb2de84ca40506e04f67b5458c6c3992f4d540dc5af7c1c9b5 | 展开tail/target/generate.py的全部传递依赖，不直接执行未知闭包 |
| 全部源与原对象闭包 | NOT_YET_VERIFIED；供体目标记录132源和19历史Git对象 | 分清运行包、生成器、宿主模型、审计器依赖，冻结清单；不整树覆盖 |
| 冻结fixture | 已知SHA256为4b926d3c459e52ad3e9c8ec78c2dd22f090498b06a1b11b5188d7f1e75353913；本轮未下载/解包核验 | 核实输入与原量化/独立Q golden；不重新造输入冒充旧fixture |
| 与当前0f/NEMU兼容 | 标准RV64浮点/RVV加既有dot8具备可评审路径；尚无当前组合执行资格 | 逐项核对编码、状态、ABI、当前工具/物理EMU身份 |
| 新GNU对象/最终链接 | NOT_TESTED | 独立目录构建，对实际机器字、符号/调用、数组、路由和完整路径审计 |
| 新宿主值/负控 | NOT_TESTED | 量化域、FP边界、完整输出/高位、CSR/ABI/guard、路由污染与错误配置 |
| 当前0f目标性能 | NOT_TESTED | 仅在宿主及预算门禁通过后冻结新的有界探针；本轮不跑 |

export会生成多个去重符号，必须只链接一次完整Q内核，不能同时链接旧fused.o和phased/tail筛选对象。下一轮可只把TA、FR、共同量化边界和必要数据/检查闭合为独立消费者；主项目正式C8接口保持。[导出工具](https://github.com/cc77-builder/riscv/blob/ffd668bf1bc80850d382f514d13bb00316c85582/team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/export.py)

## 4. 不可直接继承的条件

1. 供体EMU SHA256为ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f，本项目物理0f EMU为acf672eb39f836da4000b253849e3214089e9c8e5198060a57d2cc6bbd393da9。二进制不同，不凭“T17”标签互相转授PASS。
2. 供体正式顺序FR,TA,FR | FR,TA,FR，选择阈值是0.5%。本项目后续新合同应保持1%锚点与3%收益原则，不默认继承较低门槛；还须冻结对称预热、执行顺序、控制窗口、重放和停止规则。
3. 供体3.473%距3%只有约0.473个百分点，留给新环境/布局差异的余量有限，不能保证迁入后合格。
4. 供体正常恢复和重放各约53分钟，主包原始载荷约840MB；这不是本机时长预测。供体18M guest cycles、7200s也不自动成为本轮授权预算。必须先审计目标自检/完整调用开销、日志和内存，再另轮冻结预算，禁止自动续跑。
5. 本轮只读核验7份来源，没有重放132源/19对象或复算完整归档。供体历史成功和失败均作为来源边界保留。
6. 当前队友的tailrows/forward保护继续有效。本项目只评审固定旧QKV，不接管其活动任务，也不借本轮建立共享发布窗口。

## 5. 下一轮进入与停止条件

建议只授权“最小迁入与宿主门禁”，先补齐传递源闭包和实际数据，冻结版本/完整浮点语义/输入生命周期/公平窗口，再做GNU构建、机器码/链接、完整数值、CSR/寄存器/边界及宿主负控。尽量让校验器自身的大量变异在宿主完成，目标仅保留必要功能验证、真正的负控/恢复和完整输出；不得重复C8旧轮的开销问题。

闭包缺失、源对象不符、数值/异常合同不兼容、需要改RTL或测试预算不合理时停止；不偷偷扩为整个forward。全部宿主门禁通过后，交付可以审阅的0f目标探针合同，列明总进程数、逐进程上限、正常/故障参考、锚点和收益、逐窗控制与重放、失败即停。通过合同不等于已授权开始目标运行。

如果当前0f新QKV没有合格收益，应保留FR回退或关闭该性能候选；应用功能资格与性能采用资格分开。旧R5/C8稳定版始终可以继续使用，不以完成P3编号为理由强行换默认。
