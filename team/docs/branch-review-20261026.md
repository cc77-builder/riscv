# zufan / James_Hotten 分支进度与复用评审

核查日期：2026-10-26（UTC+08:00）；生成时间：2026-10-26T14:27:41.207783+08:00。固定远端如下，收尾时再次回读未变。本次只读比较Git对象、关键源码、原结果JSON和部分原始证据，未执行新构建或仿真。远端对象已fetch到本地，生产检出保持0f12df675378556670afd0dd2153f47fcb330610；没有合并、推送或Issue写入。

结论：优先选择性复用zufan的T17工具、firstdot V2稳定C接口及软件优化；James主要提供值得学习的验证组织和特定场景方法。保留本地DIV取消关钟修复。已发布成果和未推送活动分开，旧硬件PASS不转授当前0f组合。

## 1. 分支实际位置

| 对象 | 固定提交／最后提交时间 | 当前实际进度 |
| --- | --- | --- |
| 本地保留版 | 0f12df675378556670afd0dd2153f47fcb330610 | O2＋H1＋DIV取消关钟修复；C1/C2/C3-HF拒绝，当前门控试验结束 |
| zufan | fcf4a11fc569cb2a8fcb4e18d96ec2764b228557；2026-10-26 12:48+08 | T17、稳定接口V1/V2、firstdot、配置复用、split及Q288融合目标验证；最新提交是融合后的周期诊断 |
| James_Hotten | a669af7801aca9ddf67db978935f2c56cfafff1a；2026-10-24 15:14+08 | G3定向覆盖补充、T17/R5共享交付导入、GNU11构建准入、first-dot负控恢复及单场景配对性能 |

两分支与本地共同祖先是c9132b8d7f284ad7e76550315214b5b2ca431f79。相对本地，zufan有41个独有提交、本地2个；James有74个、本地2个。提交数含历史整合、观察器和证据，不能用来比较性能或判定哪一版整体更好。

生产src目录逐文件Git blob比较：zufan的399个文件中398个与本地相同，唯一差异是ExeUnit.scala，正是本地新增DIV匹配取消后的hold释放。James有6个生产文件差异，包含更广的取消行为和可选观察器，不能把整分支导入视为单纯搬软件。

## 2. zufan可用成果及数据

| 成果 | 已有证据 | 对我们下一步的价值 |
| --- | --- | --- |
| T17干净复现 | 50次新EMU：47正常、3预期负控；重建EMU/NEMU/AM；384正式窗及跨构建768对应窗口一致 | 复用独立源码、依赖准备、身份记录、构建、拒错恢复、原文归档工具，省去重新设计流程 |
| R5 firstdot V2 | 四形状、八个稳定C别名，可搬移静态库与双头文件；V1/RVV回退保留 | 优先作为当前0f的新稳定软件候选；固定16字节输出槽、低32位结果和高96位清零，不能误接紧密int32数组 |
| firstdot | 首个点积直接初始化累加寄存器，省清零及第一次相加；三个整块形状已有矩阵与普通C验证 | 改动小、有完整接口，比继续改门控更适合作为下一项软件候选 |
| config-reuse | 仅删除状态已知且等价的重复向量配置，未知情况使状态记录失效；RVV同步优化 | 首先用8×32小范围验证当前0f上的净收益，合格再扩尺寸 |
| split-input | A/x分离接口省去每次288字节拷贝，六类算法一并比较 | 适用于本就分离存储的消费者；接口收益不计成RTL加速 |
| Q288融合 | 整数点积与FP32消费融合，保留FP运算次序和同样融合的强RVV | 为固定Q消费者提供更接近应用的比较；保持显式可选入口 |
| 周期诊断 | 事务按ROB分配世代、PC/FTQ/pdest关联；等待重叠取并集 | 学习先定位软件供给和消费开销，再决定是否改FU |

firstdot原批：4×8／8×32／16×64的vdot均值157.75／282.25／707 cycles，分别比同轮原S1 vdot少7.0692%／3.5043%／1.4291%。另一轮config-reuse的vdot为153／273／702.75 cycles，同轮最快RVV为185／299／773 cycles；4×13仍保留RVV。这两批各有独立合同和布局，不把百分比直接相加。

Q288融合的同ELF结果：

| 方法 | 正式窗口cycles |
| --- | --- |
| acc8 vdot | 82314、82270 |
| acc8 RVV4 | 88453、88456、88420、88396 |
| fused vdot | 62691、62692 |
| fused RVV4 | 67298、67311 |

最慢fused vdot相对最快acc8 vdot少23.797253%；同样融合后RVV也减少约23.85%。最慢fused vdot相对所有纳入RVV的最快观察少6.844186%，周期比约1.07347×。后者才是这次已发布固定Q测试中较保守的vdot/RVV对照，不能把约24%的软件融合收益全部归给vdot。

使用域仅是预量化、预打包、暖态、合成288×288/GS32的Q计算；不含pack、量化、冷启动、完整forward或token。x1/x2是功能检查，确定性重放不是新独立样本，也不是统计显著性证明。

[干净复现结果](https://github.com/cc77-builder/riscv/blob/fcf4a11fc569cb2a8fcb4e18d96ec2764b228557/team/optimizations/o2/repro/CLEAN_RESULT.md) · [V2使用与回退](https://github.com/cc77-builder/riscv/blob/fcf4a11fc569cb2a8fcb4e18d96ec2764b228557/team/optimizations/o2/r2-select/FIRSTDOT_STABLE.md) · [firstdot结果](https://github.com/cc77-builder/riscv/blob/fcf4a11fc569cb2a8fcb4e18d96ec2764b228557/team/optimizations/o2/r2-vector-accum/FIRSTDOT_RESULT.md) · [配置复用结果](https://github.com/cc77-builder/riscv/blob/fcf4a11fc569cb2a8fcb4e18d96ec2764b228557/team/optimizations/o2/r2-config-reuse/RUNTIME_RESULT.md) · [融合Q结果](https://github.com/cc77-builder/riscv/blob/fcf4a11fc569cb2a8fcb4e18d96ec2764b228557/team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/RESULT.md) · [供给诊断](https://github.com/cc77-builder/riscv/blob/fcf4a11fc569cb2a8fcb4e18d96ec2764b228557/team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target/COST.md)。

## 3. James值得学习的部分

James最新first-dot试验在8×32/dataset0/endtoend/reuse下，原S1 vdot 278.25→268.5 cycles，少3.504%；相对两镜像中最快RVV289 cycles少7.093%。有5次真实EMU（1精确负控＋4正常/重放）、32正式窗、48重放核对；basic vdot仍为634，对basic RVV342没有优势。

这是单场景资格，不是完整矩阵或当前0f成绩。硬件源码bc9e5ae4／EMU e66a8900，与zufan T17和本地均不同。最终运行脚本还有运行后的隔离修复，不能称最终工作源码已经执行过全部旧EMU。值得学的是实际目标寄存器bit64精确拒错、同镜像恢复、双方重放、强RVV对照和准入条件。

T17/R5公共入口由zufan导入，关键稳定头、Makefile、verify_stable.py、clean_prepare.py与zufan相同；first_dot_probe.py原型本地也已有。优先从zufan取更完整的firstdot/V2交付，James作为验证方法补充，避免把共享成果重复计为两份独立成绩。

James用延迟和依赖链构造同FU部分取消窗口的方法可用于未来补覆盖。但本地0f已经有PARTIAL_KILL=1及六类O2覆盖，fullcore/analyze.py的195位vpu/577位perf检查与James相同，当前不需为重复导入而重跑。

[James最新提交](https://github.com/cc77-builder/riscv/commit/a669af7801aca9ddf67db978935f2c56cfafff1a) · [firstdot结果JSON](https://github.com/cc77-builder/riscv/blob/a669af7801aca9ddf67db978935f2c56cfafff1a/team/evidence/firstdot-runtime-20261024/result.json)。

## 4. 复用时必须保留的本地能力

1. 保留0f的DIV取消释放逻辑及已通过的新严格关钟检查。两分支都不能整文件覆盖本地parent/check_trace.py和check_negative.py：那会丢失本地28组DIV ROB定向、48取消窗口／144立即空闲采样及零额外时钟复算。
2. zufan新增577位独立perf输入、walking-one/zero及真实父级输出检查有补强价值；如引入，应与本地严格取消门禁组合验证，不能用新perf覆盖替代原关钟覆盖。
3. James的ExeUnit对legacy/T14/O1也扩大取消释放，另有接受与flush同拍处理，不属于本次只读软件复用。若以后需要这类RTL变化，先说明范围再单独验证。
4. zufan T17/firstdot运行绑定硬件34bae6d4acceac939f958199dae53c14bc1f6183、EMU ff840528…e30f、NEMU 8af118e5…87c9；本地为0f／EMU2d1db77c…26e8。可复用工具/用例/来源证据，但要为当前组合建立真实新身份，不能改旧manifest中的SHA冒充旧结果。
5. T17是同主机、保留工具/下载缓存、独立源码与产物的Agent复现；不是全新机器安装或成员人工验收。R5打包本轮EMU0，真实运行资格来自此前合格批次。

## 5. 已发布与未推送活动

收尾远端仍为表中两个SHA。Issue #2截至评论6409643976（2026-10-26 14:23+08）：

- phased在远端fcf4a11只有静态资格。14:17协作记录称本地d103df8已完成负控/恢复/重放及归档，保守比FV少3.7948849%、比具名FR少10.3370386%，等待统一发布。本轮未读取该未发布提交的原始证据，按“协作记录报告”处理，暂不列为可直接导入成果。
- tail-agnostic两处vta位候选已在本地a9583d1冻结并准备目标运行保护，尚无TA目标性能结论。不要同时重复这一活动。
- hoisted/fixed-weight旧HOLD_CONTEXT_VARIATION仍保留；forward-host有宿主输入捕获与数值接续，不表示完整模型已替换成vdot或获得token收益。

[phased本地进度](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6409565128) · [TA运行准备](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6409643976)。

## 6. 建议接续顺序

1. 先按文件/提交范围选择T17工具、firstdot V2最新清单校验器、接口和必要来源，保留0f硬件与现有严格门禁。暂不整体合并任一分支。
2. 形成“0f＋选中软件”的统一候选，完成R4/O5：普通C ABI、完整128位、CSR/边界、负控恢复及受影响的组合验证；公平周期首先从8×32开始。
3. 对通过的组合用复用的T17流程做干净目录实际构建与运行复算，再完成本地R5/G5稳定入口。现有相容结果可复用，硬件未改的检查不无理由重复。
4. 后续软件优化按firstdot→config-reuse→匹配实际调用者的split/Q融合逐项取舍。保留同步优化的RVV和K13回退，不拼接不同合同的百分比。
5. 本轮R3门控试验保持关闭。Q288直接观察到接受后固定2拍、FU出口无STALL、上游有供给间隔，当前更值得检验软件排程；这并不证明vset是唯一瓶颈或更短FU延迟永远无收益。

本次形成复用建议，未实施导入或替换本地默认入口；统一版本数据档案仍21条，不添加虚构的新硬件实测。独立评审与比较原件在 /home/riscv/riscv-lab/branch-review-20261026。
