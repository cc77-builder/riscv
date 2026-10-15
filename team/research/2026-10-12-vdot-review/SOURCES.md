# 文献与资料索引：读到了什么，拿来解决什么

访问/核对日期：2026-10-12。仅以命题方、规范发布者、作者论文和实际源码为技术依据；不把博客转述当规范。本文件不转载论文全文，数值指标必须回到原平台解释。硬件建议和 B6/B7 是本次针对当前合同的推导，不是下列论文已经证明的本项目结果。

## S01｜命题方材料与团队转录

- [XiangShanLab 应用赛道入口](https://github.com/OpenXiangShan/XiangShanLab/blob/master/2026-CIE-RISC-V-Contest-Application-Track/README.md)：本次读取，确认题目和昆明湖 V2 平台。
- [作品提交指南](https://github.com/OpenXiangShan/XiangShanLab/blob/master/2026-CIE-RISC-V-Contest-Application-Track/SUBMISSION_GUIDE.md)：本次读取前 95 行，文件 blob `2de8454bf41a17ab0a77f4baff935be9700e66ab`。第 2 步公有仓库要求与后续私有 URL 模板不一致，须咨询；不据此擅自公开现有私有 Fork。
- [赛题官网](https://rv.cie.org.cn/direction?id=8)：本次无法取得有效正文。三阶段细节、评分和日期暂依 [团队执行计划](https://github.com/LiZufan001/riscv/blob/c1ef31d81d50c209bf0e102af8ad7713c2da6dab/team/香山vdot赛题_执行计划.md) 的既有转录；新验收前需归档官方当前原文/截图。

用途：定义“做对题”的边界，而不是用论文自行替换赛题 ISA。证据冲突及 Q01～Q07 见 [审计](01-evidence-audit.md)。

## S02｜RISC-V V 1.0 规范：B6/B7 的语义依据

[官方版本化规范页面](https://docs.riscv.org/reference/isa/v20260120/unpriv/v-st-ext.html)。本次重点读取 widening multiply、integer widening reduction、scalar move、尾部策略、LMUL/EMUL 和配置部分。

关键约束：`vwmul` 产生双宽乘积；归约的 seed/result 是向量寄存器中的标量，可与输入重叠；尾部策略影响目的其余元素；`vmv.x.s` 按当前 SEW 取数。因此 e8 不能直接读出完整 int32 结果。B6/B7 将源乘积重新解释为 e16/m1，并在归约前清零目的，推导完整结果与恢复条件。

不能照搬之处：RVV 标准不定义本项目 custom-0 指令的合法域或“高 96 位必须零”。标准规则只能约束软件基线和既有向量路径，不能替命题方认可自定义合同。

落地：候选汇编→独立模型→NEMU/QEMU→全核；全部非 scratch 寄存器和真实入口/出口 CSR 逐项比较。

## S03｜Chen 等，Nanhu-vdot，2024

[论文元数据](https://arxiv.org/abs/2409.00661)；[作者 PDF](https://arxiv.org/pdf/2409.00661)。本次读取正文，并查看 PDF 第 5、7、8 页的结构/结果图表。

最直接相关的是其在香山南湖中增加点积单元、通过软件调用并做系统验证的路径。八路乘法和平衡求和可以作为结构参照；但该实现使用通用寄存器和 64 位接口，不是本题 128 位 RVV 寄存器/低 32 位结果合同。其 FPGA、标量对照和 GPT-2 结果不能变成本项目的预计加速比或 ASIC 面积。

还发现正文 §5.4.2 对两种实现耗时的排列，与紧随的加速结论方向不一致。因此不使用这两个耗时为本项目设目标，也不自行把疑似笔误改成确定事实。

采用：紧耦合实现、短归约树、从单指令到 kernel 的验证链。
不采用：照搬编码/寄存器语义、将其标量基线代替优化 RVV、把 FPGA 资源增量套到昆明湖 V2。未核验到可直接复用的配套实现提交，本轮不宣称复现了该论文。

## S04｜Perotti 等，Ara2，2023/2024

[Ara2 论文元数据](https://arxiv.org/abs/2311.07493)；[PDF](https://arxiv.org/pdf/2311.07493)；DOI `10.1109/TC.2024.3388896`。本次重点阅读性能驱动因素、物理实现、比较方法，并查看 PDF 第 9 页图 8～10。

论文有价值的不是把另一个核的频率搬过来，而是将短向量性能拆解为发射、设置、存储和向量结构限制，并用对照实验定位瓶颈。理想 dispatcher/cache 结果属于性能上界，不是已经实现的系统。其优化基线讨论也说明，拿朴素标量程序比较会误导结论。

采用：长度扫描、展开扫描、发射/存储/写回停顿分解及控制变量实验。
不采用：把 CVA6 发射限制、Ara2 lane 数、频率或浮点能效当成香山参数；为处理 8 项点积直接搬来多核向量体系。

落地：在同一香山快照测试 U=1/2/4/8，分别记录核心计算和完整 kernel，解释为何增加运算资源可能无收益。

## S05｜Garofalo 等，XpulpNN，DATE 2020

[会议原始 PDF](https://past.date-conference.com/proceedings-archive/2020/pdf/0650.pdf)：《XpulpNN: Accelerating Quantized Neural Networks on RISC-V Processors Through ISA Extensions》。本次重点阅读指令、乘加单元、kernel 与 PPA 方法，并查看 PDF 第 3 页图 3。

该工作说明低位宽数据布局、打包开销和软件复用与运算单元同样重要；文中为避免选择/分配逻辑拉长关键路径，并非一概共享不同精度的乘法资源。这支持“复用成熟控制，但数据通路是否共享由时序决定”的策略。

采用：先量化数据搬运，再做短点积内核；以相同工艺约束比较面积/时序。
不采用：RI5CY 的 4/2 位指令、旧目的累加和整套工具链扩展不直接进入本题主线；其 22nm 实现不是本项目综合结果。

相关但不同的后续期刊工作 [arXiv:2011.14325](https://arxiv.org/abs/2011.14325) 本次仅检查摘要层信息，不把其融合指令或集群数字与 DATE 论文混成同一次实验。

## S06｜RISC-V dot-product 扩展提案

[提案仓库](https://github.com/riscv/riscv-dot-product)；[intro.adoc](https://github.com/riscv/riscv-dot-product/blob/main/intro.adoc)。本次直接读取的 intro blob 为 `fc74f8a388f4811951f0179b55ab248dc45619d9`，文字仍将其描述为 proposed。

它讨论的是每组四个 int8 向 32 位组结果累加，包含旧目的累加含义；与本题当前“低八项、零初值、一个结果”不同。它可以帮助论证将来扩展方向，但不能凭同名 dot 就宣称兼容，也不能把此页当作本项目指令已获标准批准的证明。

落地：把分组累加、更多符号组合列入后续 ISA 选项；只有基础三阶段及应用证据完成、且允许修改范围时再做。

## S07｜Xiao 等，SmoothQuant，ICML 2023

[PMLR 正式论文页面](https://proceedings.mlr.press/v202/xiao23c.html)。本次阅读正式摘要与元数据，未完成全文复现。

此处只取一个边界判断：W8A8 推理还需要解决量化和激活范围问题，整数点积 bit-exact 不等于模型推理精度已验证。不要把论文特定平台的加速数字移植到 RISC-V。

落地：第一轮先交付准确的 int8 算子；若扩展到真实 LLM，另报告量化配置、比例因子、校准数据和精度指标，不把随机矩阵称为完整 LLM 验证。

## S08｜Jacob 等，整数推理论文，CVPR 2018

[作者 PDF，arXiv:1712.05877](https://arxiv.org/pdf/1712.05877)。本次重点读取 §2.1～2.4：仿射量化、矩阵乘、零点修正和 int32 累加。

采用的要点是区分 `sum(a*b)` 和带零点/比例因子的真正量化算子。零点项可以在 kernel 外预处理一部分，但其成本与有效范围必须记入实验；输入补零时应按量化的“实数零”处理。不能为省指令把可能越界的 `q-z` 静默塞回 int8。

落地：先以对称 signed-int8 算子验证本题，再单独扩展非零零点校正；分别检验整数精确性与模型精度。论文的 uint8 例子不是本题 signed-int8 合同。

## S09｜固定版本的香山源码，比 latest 页面更重要

- [VIMacU.scala](https://github.com/LiZufan001/riscv/blob/c1ef31d81d50c209bf0e102af8ad7713c2da6dab/src/main/scala/xiangshan/backend/fu/wrapper/VIMacU.scala)：本次读取；两个 64 位模块、宽化输入组织、旧目的、Mgu 与写回。
- [FuConfig.scala](https://github.com/LiZufan001/riscv/blob/c1ef31d81d50c209bf0e102af8ad7713c2da6dab/src/main/scala/xiangshan/backend/fu/FuConfig.scala)：本次抽查配置结构、确定延迟/流水要求和特殊源索引。
- [VdotExec.scala](https://github.com/LiZufan001/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/src/main/scala/xiangshan/backend/fu/vector/VdotExec.scala)：本次完整读取独立实现。
- [RTL 接口合同](https://github.com/LiZufan001/riscv/blob/a978b3b8fe731dd9422a41f80d9d53e40c775656/team/spec/rtl-interface.md)：本次读取关键路径、配置与写回部分。

本次访问的 [latest vector 文档入口](https://docs.xiangshan.cc/projects/user-guide/en/latest/vector/) 指向 V3 内容。V2 实现决策必须以上述固定源码核对，不能因页面来自官方就忽略版本差异。

## 取舍摘要

文献给出的成熟组合是：**短精确算术路径＋复用既有后端控制＋高质量软件基线＋数据复用＋端到端/物理约束实测**。本轮不引入全新预测器、旁路状态机、完整编译器后端、独立总线加速器、多精度矩阵引擎或完整 LLM 移植作为关键依赖。将来若证据显示它们值得做，再以单独假设、验收和成本预算推进。

引用论文不等于获得源码许可。若后续直接引入第三方实现，需记录实际仓库、commit、许可证和修改范围；本目录未复制论文全文或第三方 RTL。
