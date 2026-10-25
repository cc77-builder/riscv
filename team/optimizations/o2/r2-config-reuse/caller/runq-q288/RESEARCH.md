# Q288 消费者研究：先消除真实共同开销，再决定融合和硬件投入

研究日期：2026-10-26（UTC+08:00）。包：`R2-S3/runq-q288-consumer`；执行者：@LiZufan001 / Pro 主 Agent，软件、微架构与独立反证由只读子 Agent 并行审查，主 Agent 核对原始证据、设计实现并完成实际验证。

## 1. 当前决定

**第一步采用八个标量 FP32 累加器跨整数叶调用驻留的有界软件候选；已完成主机数值和真实 GNU/ELF 静态筛选，尚未取得目标周期资格。** 六种整数叶完全保持，各完整 Q 路径少 19,354 条架构指令，其中 vdot 为 20.9859%、RVV4 为 25.6766%；不能将这些百分比称为加速。源码、负控、完整数字与原始证据见 [acc8 结果](acc8/RESULT.md)。

接下来优先用新的有界合同取得这项修改的完整目标正确性与周期证据。如果它没有稳定目标收益，应接受否证；不自动增加展开宽度、重跑旧 HOLD 矩阵或升级 RTL。完整 K 融合、严格行间 SIMD、真实 batch 与新量化布局是不同条件下的后续方向，不是必须全部执行的队列。稳定 firstdot V2 及 V1 回退保持原资格。

本研究从固定入口 `3182e945df59dd5183b22e06103556496c6b1695` 与消费者检查点 `ff873a0e043fcebea0617d08b452d92c64804650` 恢复事实；完整旧 Q288 正常运行中断、独立重放未执行，见 [原结果](RESULT.md)。早先 split 的 8×32 PASS、fixed-weight 的 HOLD、旧 FU/STA 数据均不自动转移到新消费者。

## 2. 为什么先做这一小步

这里的消费者来自固定版本 [llama2.c runq.c](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/runq.c#L317-L341)，形状为 288×288、GS32，当前使用合成但可复现的量化输入，未下载模型或实现完整 token 推理。其每行数值图是：

`sum = +0.0f; for g=0..8: sum += (float(dot32) * Ws[row,g]) * Xs[g]`

两次乘法、每次舍入、组顺序和 signed 转换均属于当前合同。FMA、`dot*(Ws*Xs)`、跨组整数累加后统一缩放不满足此数值图。不同输出行之间可交错，因而八行显式展开有明确的等价基础。[原合同](CONTRACT.md)、[候选合同](acc8/CONTRACT.md)固定这些边界。

原真实 GNU 11.4 / `-O2` 的 `q288_full` 是 408 B 代码、192 B 窗内额外栈深度，八行数组在 group 间反复落栈；该判断来自完整 ELF，不是根据 C 数组语法猜测。lp64d 的 `fs0`–`fs11` 可以保存不超过 ABI_FLEN 的值，八个 FP32 累加器具备合法的跨调用驻留空间；标准向量调用约定则不保留任何向量寄存器。[psABI 固定原文](https://github.com/riscv-non-isa/riscv-elf-psabi-doc/blob/3095deae52ae3feecc54b5e185d14eb177e05d04/riscv-cc.adoc#L77-L110)

候选实际使用 `fs0`…`fs7`，FP 栈访问由 5,474 次变为全调用入口/出口的 16 次，代码增至 576 B。公共叶、pack、布局、ABI、输入、整数与 FP 算术次数不变，这使一次最小干预可归因。它比同时融合调用、重排尺度、改 RVV/RTL 更适合作为第一步。

### 完整 Q 的工作量

下表来自当前生成物、固定叶机器码及实际完整路径检查；不是缓存或周期模型。

| 项目 | 每个完整 Q | 含义 |
| --- | ---: | --- |
| 行 tile / group / 整数叶调用 | 36 / 9 / 324 | 8 行×32 列叶 |
| signed INT8 乘积 | 82,944 | 全部 288×288 权重 |
| vdot 指令 / 整数 vadd | 10,368 / 7,776 | 当前 vdot 叶路径 |
| vsetivli / csrwi | 4,212 / 648 | 当前 vdot 叶路径；acc8 未删除 |
| signed INT32→FP32 / FP32 乘 / FP32 加 | 2,592 / 5,184 / 2,592 | 原与 acc8 均相同 |
| 完整结果槽写 / low32 读 | 41,472 B / 10,368 B | 合计 51,840 B 逻辑访存，未声称 DRAM 流量 |
| W / Ws / X / Xs / Y | 82,944 / 10,368 / 288 / 36 / 1,152 B | 命名数据；另有 128 B 复用结果槽 |
| 叶架构指令 vdot / RVV4 | 164 / 112 | 每叶；少指令不保证少周期 |

权重已在生命周期开始打包一次。继续宣称“永久 pack”收益会重复计算既有成果。上游 Q/K/V 本来就共用一次量化后的输入，W1/W3 亦然；后续跨投影融合必须找到新的装载、调用或调度成本，不能计入不存在的重复量化。[上游调用序列](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/runq.c#L363-L370)

## 3. 一级资料给出的启发和边界

以下是本轮实际检索与阅读的作者论文、官方规范和项目源码。外部性能数字不充当本项目成绩；固定代码身份用于避免随上游更新漂移。

| 来源 | 可采用的思想 | 本项目的限制与决定 |
| --- | --- | --- |
| [BLIS 作者稿](https://www.cs.utexas.edu/users/flame/pubs/BLISTOMSrev2.pdf)，§4.3–4.4；[正式 DOI](https://doi.org/10.1145/2764454) | GEMV 可通过 DOTXF/AXPYF 在寄存器层融合，融合因子受寄存器和数据类型限制 | 现整数叶已经跨 8 行复用 X；新的机会是组间 FP 累加与叶外接口。支持 acc8 的机制，不提供其周期预测 |
| [Goto/van de Geijn 作者修订稿](https://www.cs.utexas.edu/~flame/pubs/GotoTOMS_revision.pdf)，§4.2、§7.3；[DOI](https://doi.org/10.1145/1356052.1356053) | 按供数与计算能力选择块；小 n 时 packing 摊销不足 | 单向量 n=1 不能继承 GEMM 的跨右端权重复用；不照搬论文块形状或速度 |
| [gemmlowp kernel.md](https://github.com/google/gemmlowp/blob/16e8662c34917be0065110bfcd9cc27d30f52fdf/doc/kernel.md) | 内核寄存器分配和 pack 格式共同设计，先画完整生命期 | NEON 的 12×4、无符号扩展和整数 MAC 不适用于现 signed W8/GS32；只借方法 |
| [Roofline 原技术报告](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/Archive/EECS-2008-134.pdf)，§3 | 区分计算能力、持续带宽和运算强度 | 原定义用缓存过滤后的 DRAM 字节；本报告的指令访存字节不能直接放入 DRAM Roofline，混合 INT/FP 也不能套一个浮点峰值 |
| [llama2.c 固定 runq](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/runq.c) | 真实消费者的 GS32 数值图、量化输入生命周期 | 本模块仍是可复现 Q 投影工程夹具，没有真实模型质量、完整 token 或服务吞吐资格 |
| [llama.cpp RISC-V quants.c](https://github.com/ggml-org/llama.cpp/blob/6050b467c07a95c7b87debd4ddac2f8ba8d9b807/ggml/src/ggml-cpu/arch/riscv/quants.c#L435-L480) | i8m2 一次读取32元素、i16m4 widening multiply、i32 widening reduction，可研究更强 RVV | FP16 scale 和缩放表达式不同，不能直接替换严格 FP32；在新融合接口下应重新比较 RVV，旧 RVV4 不代表全局最优 |
| [llama.cpp RISC-V repack](https://github.com/ggml-org/llama.cpp/blob/6050b467c07a95c7b87debd4ddac2f8ba8d9b807/ggml/src/ggml-cpu/arch/riscv/repack.cpp#L447-L495)及[实际分派](https://github.com/ggml-org/llama.cpp/blob/6050b467c07a95c7b87debd4ddac2f8ba8d9b807/ggml/src/ggml-cpu/repack.cpp#L5110-L5131) | 完整 K 内保留跨行结果；多输入复用权重 | 该 Q8 16行路径要求 Zvfh/VLEN256，VLEN128 分支为 TODO，且使用 FMA；这里只借结构，不声称可即用移植 |
| [RISC-V Vector 固定 v1.0 历史稿](https://github.com/riscvarchive/riscv-v-spec/blob/3570f998903f00352552b670f1f7b7334f0a144a/v-spec.adoc)与[psABI](https://github.com/riscv-non-isa/riscv-elf-psabi-doc/blob/3095deae52ae3feecc54b5e185d14eb177e05d04/riscv-cc.adoc) | 32向量寄存器、VLMAX=LMUL×VLEN/SEW；标量保留寄存器与向量 clobber 的差别 | VLEN128 的8个FP32行需两个m1或一个m2；现8个结果分散在不同寄存器低32位，收拢、vset与依赖均须计费。历史tag是冻结公开审阅稿，不称其为当前规范版本 |
| [SmoothQuant，ICML 2023](https://proceedings.mlr.press/v202/xiao23c.html)与[作者量化代码](https://github.com/mit-han-lab/smoothquant/blob/c61476d728e42ae0d8a35e7e78494edcac3237b5/smoothquant/fake_quant.py#L183-L205) | 离线平滑与外维尺度可使完整 K 先做整数累加 | 是新量化合同，须校准和留出质量验证；不是现 GS32 的逐位等价优化，GPU收益不能转借 |
| [T-MAC，EuroSys 2025](https://arxiv.org/abs/2407.00088v2) | 面向低位宽权重的查表计算，工作随权重位宽变化 | 当前精确 W8A8/dot8 缺少相同优势证据，不优先转向 W4/LUT；若改精度须另有质量合同 |
| [Nanhu-vdot，2024](https://arxiv.org/abs/2409.00661v1) | 软硬件协同到模型层评估，而非只报告独立点积 | 论文基于南湖、标量对照及 GPT-2；其局部4倍和约30%模型结果不适用于当前昆明湖/RVV128/GS32对照 |

文献启发不替代项目反证。历史 O2 的独立 batch 指标明显改善，但完整 GEMV 只改善 0.62%～1.50%；此前 CSA 的真实完整 FU 筛选也未达到事前时序/面积条件。这些结果支持先调查当前消费者成本，而不是机械追加 FU 方案。[项目路线证据](../../../../../docs/development-route-current.md)

## 4. 冻结 T17 的实际机器，而非公开典型配置

本轮从原生成日志、hardware-inputs 及相关源码逐字节核对配置；29份源码的身份和精确定位收于 [research-source-index.json](research-source-index.json)。原日志与硬件清单已在既有 T17 原始归档中，无需复制一套新的硬件输入。

| 项目 | 当前冻结 T17 |
| --- | --- |
| 配置、DUT核数、EMU线程 | MinimalConfig、1、1 |
| L1I / L1D | 16 KiB / 32 KiB |
| L2 / L3 | 128 KiB（64 KiB×2 bank、inclusive TL–TL）/512 KiB（1 bank、non-inclusive） |
| 取指 / 译码 / 重命名 / 提交 | 8 / 6 / 6 / 8 |
| ROB / RAB / FTQ / IBuf | 48 / 96 / 8 / 24 |
| INT / FP / VF物理寄存器 | 64 / 192 / 160 |
| 标量加乘 | FEX0/2/4 各含 falu/fmac |
| INT32→FP32 | i2f 仅在 BJU2；FEX4 与 BJU2 共用 FP写回port2 |

EMU SHA-256：`ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`。原硬件源为 `34bae6d4acceac939f958199dae53c14bc1f6183`；原 hardware-inputs SHA 为 `7c42a8130e71b39e8f5ca08d7d662a85ac58f677040c6293d38007b007ac0dcc`，生成日志 SHA 为 `7a735de54bbc652378a23bd46789d17d12b19a0ed1aeb02b2963cb2187deb253`。

源码旧注释“L2 not included”与实际参数和生成日志冲突，采用实际生成事实。Q288 命名数据连结果槽共94,916 B，大于32 KiB L1D、小于128 KiB L2总容量；这只证明容量关系，不证明每次L2命中，更不证明DRAM受限。falu/fmac/i2f内部参数1/3/2也不是完整架构依赖延迟，不能相乘预测Q周期。共享FP端口是潜在约束，不是已测停顿。

### whole-register load＋slide 为何暂缓

最初的架构计数提示整叶可由164降到146条，但固定实现显示：LMUL1 `vle8.v`、NF0 `vl1re8.v`、LMUL1 `vslidedown.vi`都展开成2个uop。前两者为i2v＋vldu，后者为i2v＋vppu。36次load改成18次whole-load＋18次slide后，相关复杂指令仍36、i2v仍36、相关uop和向量目的定义请求仍72；只省18条标量addi，同时引入18次VPPU工作。整叶复杂指令仍113，复杂译码每周期只接受第一条复杂指令，因此不能用少18条addi推导少18拍。[源码及行号索引](research-source-index.json)

公共 A/X 允许任意字节对齐，只有slots要求16B对齐。同一连续16B载荷在固定VSplit中：起址mod16=0时两次8B→一次16B为2→1 flow；mod16=8时为2→2；其它余数为3→2。整叶A/X均余8时，36→36 flows完全不减少，却新增slide。当前测试镜像恰好16B对齐，不能据此收紧公共接口。[公共接口](../split/README.md)、[当前q288.h](q288.h)

VPPU保留旧目的依赖，原tu/vl8也不触发whole-load自动消依赖；i2v仅在BJU2，向量端口亦有共享。这些都是更改优先级的源码反证，**不是实测负优化或正式 STOP_SCREEN**。只有目标数据指向load-flow/merge等待且对齐收益明确，才值得重开该候选。

## 5. 有条件的后续研究方案

### A. 下一步：acc8 的完整目标正确性和有限周期判别

新合同先固定身份、工作量、资源、停止门槛，再执行；不直接把父生成器里保留的旧46次Q计划当成新候选默认任务。

1. 使用同一新ELF同时放原包装与acc8，复用当前六个完整整数叶、输入和严格oracle；先保留vdot与原强RVV4的最小功能对照。候选变动不修改官方参考、判定程序或固定EMU。
2. 建议首批正常过程只做10次完整Q：两种旧包装各x0一次，新包装两种叶各执行x0→x1→x0→x2；独立负控→正常恢复→独立重放。逐位比较全部288输出、完整128位结果/架构DiffTest、guard、输入只读、CSR/ABI，实际失败立即停。这个小批仅取得功能与成本定位，不能选最快RVV或宣称正式性能资格。
3. 记录完整Q周期、退休指令、共同锚点与可用的既有观测；首先验证静态少掉的栈/循环工作是否出现在实际退休序列、是否缩短完成时间。只读分析已有轨迹，不为得到一个新统计而先改生产RTL。
4. 若继续正式比较，原/新包装都包括六叶，使用同一硬件、ELF、输入生命周期、状态准备和预定顺序，pack单列；在开始前明确完整样本、锚点与上下文门槛，保留较快合格RVV。两个正式顺序须同向且稳定；建议以完整Q至少5%收益作为这一软件候选的继续投入门槛，系拟议研发标准而非官方评分。旧合同1%锚点规则如沿用，应明确写入新合同，不在结果出来后放宽。
5. 功能失败先定位；静态减少但目标收益不足则关闭acc8性能采用或只保留研究候选；共同锚点不稳则HOLD。不得靠追加样本挑选有利窗口，也不以“测试做完”代替性能价值。

资源仍为同机总CPU≤4、一个常驻原生开发检出和仓库外独立输出；目标EMU默认单个运行，其他重任务按Issue及实际占用协调。没有必要新增完整源码检出或硬件构建。实际用时与保留日志量先由小批估计，避免未经测量又启动大矩阵。

### B. 若剩余接口/FP成本显著：严格完整K融合

以8×288私有内核为单位，保持g0→g8、两乘一加及同一量化输入，消除324次边界中的一部分调用、完整槽物化、配置和地址准备。八行结果跨组驻留；Ws可保持原布局，或只做可逆的字节重排 `Ws[t,g,r]`。公共dot8语义不变，删除软件中间槽也不删除高96位架构结果义务。

先画寄存器生命期，再决定两个m1/一个m2 FP32行向量是否划算。每组FP编码次数理论上可由32条标量操作变成8条四路向量操作，但结果收拢、vtype切换、实际uop和spill必须全部计入；不能称为4倍加速。vdot与RVV同步融合，另研究上游启发的GS32/LMUL2完整归约，允许RVV成为赢家。

先在当前单一形状做主机逐位与真实GNU静态否证。若新增收拢、切换和spill抵消收益就停止。只有acc8后的真实目标数据仍显示这些可改变成本显著，才进入新的有界EMU；不把完整融合预先写成下一轮必须实现。

扩大行块的回报有限：8→16行仅使显式X读取10,368→5,184 B，W+X读字节93,312→88,128 B，减少5.56%；这也不是周期上限。普通GEMV每个权重只供一个右端向量，不能直接继承GEMM的双向复用。

### C. 若真实消费者有多个同时就绪输入：batch4/prefill

四个独立右端可以共享权重载入，才有机会显著改变供数成本；这不同于现fixed-weight N4的四次串行调用。四次理想单量逻辑数据379,152 B，对一次共享W/Ws的batch4为99,216 B，比值3.82；MAC数未减少，缓存复用会缩小差距，不能将此比值当吞吐预测。

先确认实际生产者是prefill或独立序列，不能假设未来自回归token已知；主机四核授权也不等于DUT四核。两边都允许相同batch与持久pack，报告batch总延迟、吞吐和单量回退。若没有真实批输入，直接不立项。

### D. 若模型质量允许：外维尺度W8A8

per-row权重尺度与per-token激活尺度允许完整K先INT32累加再去量化。对K288，signed8极值绝对和不超过4,718,592；转换可由2,592→288，乘法5,184→576。该潜力来自改变尺度布局与重新量化，**不是现GS32的等价重排**。[SmoothQuant作者实现](https://github.com/mit-han-lab/smoothquant/blob/c61476d728e42ae0d8a35e7e78494edcac3237b5/smoothquant/smooth.py#L49-L71)

条件是取得有明确许可和哈希的原浮点检查点、代表性校准与独立留出数据，先对FP32/GS32/新量化做主机质量比较并预注册可接受NLL差异。只有质量和实现成本均通过，才讨论目标加速；保持现oracle、正式ISA和稳定入口。当前没有下载或运行模型，没有质量结论。

### E. 何时重开FU/RTL

只有新的完整消费者轨迹显示FU接受、占用、写回等待或实际关键路径阻塞，且它们是可改变的主导成本，才重开R3。旧固定窗口的2拍响应、无写回stall或某个ACCEPT间隔不能证明所有新消费者相同；也不能用dot数量推导FU已饱和。任何硬件候选仍分别完成FU、父级/整核、强RVV公平周期和同条件PPA，不从软件静态筛选跳到硬件收益结论。

## 6. 可交付边界

本轮交付了可运行的第一步实现、严格oracle/真实ELF负控、六叶公平静态比较、原始字节归档，以及有可证伪条件的后续方案。新增acc8 EMU为0，当前没有新完整应用周期、模型质量、ASIC PPA或人工验收资格。论文、已有PASS和本次静态收益各有适用身份；任何正式采用均等目标数据闭合后再决定。
