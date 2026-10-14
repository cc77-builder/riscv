# T10：候选 VDOT 全核接入

2026-10-14，dev 工作区；合同仍为 `vdot-s8x8-r32-v0.1` 草案。当前主机的候选接入、真实译码与代表性全核执行已验证；本记录不代表成员签字、ISA 冻结或 T11/T12 完整验收。

## 源码与机制复核

| 环节 | 实现与复核依据 |
| --- | --- |
| 精确译码 | [VdotInstructions](../../src/main/scala/xiangshan/backend/decode/VdotInstructions.scala) 固定 mask=`0xfe00707f`、match=`0x0200000b`；[DecodeUnit](../../src/main/scala/xiangshan/backend/decode/DecodeUnit.scala) 新增独立 `FuType.vdot` 表项；vm=0 不属于 VDOT |
| 向量分类/权限 | [RiscvInst](../../src/main/scala/xiangshan/backend/decode/isa/bitfield/RiscvInst.scala) 只把精确匹配的 custom-0 纳入 `isVecArith`；现有 `FuType.vecAll` 的 VS Off 检查覆盖它 |
| 微操作 | 复用 `UopSplitType.dummy`，进入真实复杂译码路径且数量恒为1；SEW/LMUL 非法也不按 LMUL 展开目的寄存器组。禁止 ROB 压缩 |
| 源/快照 | 源槽0/1为 vs1/vs2，槽2不依赖旧目的；槽4仍是物理 VL。vtype/vstart 由实际译码快照传递，FU 再检查 e8/m1/vl8/vstart0/vill0；内部2位SEW不能独立表达ISA的第三位，保留 vset/vill 的上游约束 |
| v0 | [DecodeStage](../../src/main/scala/xiangshan/backend/decode/DecodeStage.scala) 对 v0 源启用槽3；[BypassNetwork](../../src/main/scala/xiangshan/backend/datapath/BypassNetwork.scala) 把实际 v0 数据送入槽0/1；vd=0 仅启用 v0 写使能，非0仅启用 vec 写使能 |
| 物理依赖 | [Rename](../../src/main/scala/xiangshan/backend/rename/Rename.scala) 保留 VL RAT 读取和同批 vset 目的旁路；v0 使用专用 RAT/旁路。没有用影子 `vpu.vl` 代替物理 VL |
| 执行资源 | [Parameters](../../src/main/scala/xiangshan/Parameters.scala) 仅在 VFEX1 加入 `VdotCfg`；FU延迟1，OG2使调度/写回预留为2，IQ唤醒延迟1。复用原读写口、FU/WB busy table 和碰撞断言 |
| 完整写回 | [VdotFu](../../src/main/scala/xiangshan/backend/fu/wrapper/VdotFu.scala) 直接给出128位结果，不经 Mgu；非法响应关闭 vec/v0 写使能仍保留 valid、ROB身份和非法指令异常。全核固定延迟 EXU 的输出 ready 恒真，不能把单元任意反压测试当作全核端口冲突证明 |
| 完成/退休 | [ExeUnit](../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala) 选择完整结果、标签和异常；[WbDataPath](../../src/main/scala/xiangshan/backend/datapath/WbArbiter.scala) 以输入 fire 产生送ROB的完成，不以数据写使能筛掉非法响应；dummy 进入既有 dirtyVs 分类，ROB 仅按成功提交有效位触发 VS Dirty |

这些路径复核来自源码，不能替代波形、真实 DiffTest 或故障检出。静态检查只能证明配置进入相应机制，不能单独证明同时写回、预测取消和回滚均正确。

本轮源码复核发现T06遗留的分类缺口：`VdotCfg.isVecArith` 为 false，因而其自身 `needOg2` 也为 false；共享VFEX1因其他向量FU存在仍被视为向量，原资源测试未发现这一遗漏。新增直接检查实际复现失败，再补齐 `FuConfig.isVecArith` 的VDOT分类；重新冻结源码和构建。修复前的5项通过记录保留为历史，不能作为最终源码的完整验收。

## 验证入口与边界

[vdot-decode-tests.sh](../scripts/vdot-decode-tests.sh) 通过根 Mill 工程编译真实依赖，检查全部32,768种寄存器编码、与所有既有译码项不重叠及唯一资源归属，并实例化生产 `DecodeStage` 检查别名、配置恢复、停顿和 redirect；同时保留三项 T06 FU 测试。源码/依赖在运行前后核对，检查器仅在完整通过后生成 receipt。

复杂译码的输出有效位受到 rename 就绪数量约束，停顿期间无效的输出载荷不具有保持语义；测试在停顿中改变后续输入，恢复时检查原已缓冲微操作。局部测试关闭性能打印、补齐日志/性能配置，不建立全局日志端点以避开 chiseltest6 对 Probe 端口的限制；生产模块内的 XSError 断言保留。测试使用单翻译单元编译绕过 chiseltest6 强制头文件与 Verilator5.020/GCC 预编译头的冲突，不改生产RTL。

[vdot-integration](../workloads/vdot-integration/main.c) 和 [vdot-core-smoke.sh](../scripts/vdot-core-smoke.sh) 从现有 T05 独立数据选10项合法与10项非法输入，复用实际陷阱观测、执行前32寄存器快照与全32寄存器检查器。合法覆盖负数、边界、v0源/目的/别名、v31、尾部清零、Initial/Clean置脏；非法覆盖m2/mf2、VL0/7、非零vstart、vill、VS Off、vm0及v0目的无部分写回。另按固定 AM 源码、实际库、镜像和参考库摘要绑定运行。

该小程序只用于接入冒烟；T11/T12仍使用完整 `vdot-exceptions` 矩阵、完整日志检查与故障注入。NEMU standalone 的通过仅说明程序/判定器可运行，不能作为RTL通过。冒烟复用的通用判定器允许非法非Off初态出现架构许可的保守置脏，因此不得仅凭它宣称异常严格保持VS；具体实现是否发出 dirty_vs 需另核对退休/异常波形。

本次独立源码包为 `team/out/t10-source-pack-20261014-v5`，SHA256=`b657e0896a10d6c9fadda54500a77b9c1819f1ca03c9d93dea47cd4884643901`，440项根输入与126个子模块。开发迭代副本有明确 DEVELOPMENT_ONLY 标记；正式全核副本另从源码包物化，使用T04的低内存分阶段构建和Clang19，不复用旧仿真器作为新接入证明。

早期版本真实 DecodeStage/FU 共5项测试与实际RTL lint通过，源码清单7125项前后一致；该版本完整冷构建通过（尚不含后续mtval修复）。首次20项全核程序的10项合法全部通过，但第一项非法配置发生真实DiffTest不一致，退出1且不生成通过记录。旧T04仿真器的普通vadd/ebreak自测复现同类失败。波形明确给出DUT正确的异常PC、指令及cause；源码定位参考端Smrnmi已启用而NMIE_INIT=0，普通陷阱被抑制并返回PC=0，与RTL的NMIE复位1不一致。

已在独立NEMU检出中把reference配置设为NMIE_INIT=y，ISA补丁和基线提交保持原值；[构建脚本](../scripts/prepare-nemu-vdot.sh)与[运行来源门禁](../scripts/artifact_guard.py)补齐目标复位配置核对。新增[参考API测试](../tests/nemu_reference_traps.cpp)使用实际DUT生成的状态结构并由difftest_init_v2核对ABI，旧参考库被复位检查拒绝，新参考库的单步ebreak、非法配置VDOT精确cause/PC/mtval与全寄存器保持、合法VDOT完整结果/VS Dirty均通过。此次参考复位修复未改硬件或陷阱时序；参考配置与运行验证源码单独捕获，不冒充原编译输入包的字节。该阶段随后进入兼容配置下全核重跑；最终结果见下节。

参考复位修复后的首次全核重跑：10项合法与X02-m2通过，X02-mf2晚发现异常发生mtval不一致（DUT零、参考指令字）。依据异常测试合同，保留此失败并补齐[CSR包装器](../../src/main/scala/xiangshan/backend/fu/wrapper/CSR.scala)的VDOT原始指令路径：[VdotTrapInstruction](../../src/main/scala/xiangshan/backend/fu/wrapper/VdotTrapInstruction.scala)仅在精确VDOT、真实非中断EX_II陷阱时优先使用精确ROB队首的原始指令，其他情形保留原TrapInstMod行为。ROB已有的原始指令寄存器始终存在，也已用于架构异常PC/指令输出，未引入按Debug开关消失的数据源。

[晚发现异常选择测试](../../src/test/scala/xiangshan/backend/fu/vector/VdotTrapInstructionSpec.scala)共65,586项，覆盖全部32,768种原始寄存器编码、空/旧缓冲优先级、陷阱/中断/异常条件以及17位固定编码扰动；6项真实单元测试及lint通过，7,127项源码清单前后一致。其后重新冻结v5；完整冷构建与20项实际DiffTest结果见下节。旧基线普通ebreak在兼容参考配置下完成精确陷阱记录，但诊断整次运行在10分钟限制处退出124，只作因果定位，不记为7项入口自测全部通过。


## 最终本机结果与复现

最终源码经完整冷Scala编译、FIR-only生成、独立firtool转换及Clang19全量构建通过；未借用旧仿真器。仿真器SHA256=`cc5a926b0c95777af5c4feb51a2164229d9d6e7eadef65d8d208e39609cf455b`，参考库SHA256=`a6b3ac4e250d5cd53012f787cee3b69f67d65cb439173a2b50f5a2cb44d8609e`。构建峰值9,591,800KiB，使用既有WSL约11GiB内存/3GiB swap；本轮未安装新环境或修改永久配额。

- 真正全核DiffTest：10合法+10非法全部通过，每项执行前pre32、执行后all32、守卫及陷阱现场判定通过；GOOD TRAP，退出0，运行前后源码、程序/参考/仿真器摘要一致。见[全核记录](../evidence/t10-integration-20261014/smoke/check.json)。
- 现有指令回归：同一新仿真器及兼容参考库的hello/vadd三组24项通过，真实DiffTest、GOOD TRAP、退出0。见[回归记录](../evidence/t10-integration-20261014/regression/check.json)。
- 局部实际路径：波形区间140000～190000，合法输入147671、输出147672、VDOT提交147677；输入/输出ROB标签32与物理目的124一致，物理VL=8，128位结果为低32位-8、高96位零。mf2非法输入177596、输出177597，ROB标签89与物理目的153一致，vec/v0写使能均为零；177614的异常事件记录cause=2、PC=`0x8000182c`、原始指令与mtval=`0x0294050b`。见[波形核对](../evidence/t10-integration-20261014/wave/wave-summary.json)。ROB提交观察来自DiffTest延迟器输入，本片段没有独立追踪提交ROB标签，不声称完成全核依赖/取消证明。
- 失败门禁：编译退出17后旧PASS消失；程序镜像单字节损坏在启动仿真器前被摘要门禁拒绝，旧PASS消失，之后恢复原镜像。后续hello/vadd程序构建在VDOT运行与负控结束后进行，未在VDOT检查前后改变共享AM库。

材料保留两次真实差分失败、测试夹具初次错误和超时诊断，未以最终PASS替换失败历史。完整证据见[归档说明](../evidence/t10-integration-20261014/README.md)；大文件仅保留本机路径与摘要，不入Git。源码包中编译输入和当前运行脚本分别绑定：最终冒烟入口增加波形起止参数后同步到正式副本，再构建程序并捕获运行源码清单；该入口不在440项硬件编译输入内。

在匹配源码包的正式Linux副本中，按[T04构建流程](t04-current-core.md)准备源绑定与126个子模块，设置CORE_MILL/CORE_FIRTOOL及证据目录后运行`core-baseline-split.sh`；设置CORE_SOURCE_PACK、CORE_BUILD_EVIDENCE、NEMU_HOME、AM_HOME、TEAM_EVIDENCE_DIR后依次运行`vdot-core-smoke.sh build`与`run`。局部验证用`vdot-decode-tests.sh`；参考库须经更新后的`prepare-nemu-vdot.sh`构建，Smrnmi reference要求NMIE_INIT=y。各最终命令、配置、来源和实际产物摘要均在归档内。

下一步T11：先完成高位/非结果位和一项向量CSR的独立DiffTest故障检出，再补配置依赖/恢复、连续请求/别名、全核取消代表例及现有乘法/归约回归，随后按实际运行成本推进完整异常/随机矩阵。T10本机通过不关闭G3完整验收、T11/T12、成员复现或ISA签字；311458个整程序周期仅是运行结束信息，不用作vdot延迟、baseline配对或加速比。

## 后续验收门禁修复（2026-10-14）

[当前审查](current-tasks-audit-20261014.md)发现的优化模式绕过与运行输入绑定问题已修复，检查集中到 [vdot_core_checks.py](../scripts/vdot_core_checks.py)。实际产物路径、摘要及运行前后来源均显式验证；唯一RTL选择也不再依赖Python assert。33个Python测试方法通过，缺失结果、变更副本镜像、编译失败三个入口反例均拒绝且删除旧PASS。

复用本节已绑定的硬件构建，以最终运行检查器在 `PYTHONOPTIMIZE=1`、相对 `NEMU_HOME` 下重新运行20项真实全核DiffTest，全部通过；本轮未改硬件实现或重跑旧单元/波形/vadd项目。见[修复复审](current-tasks-fixes-20261014.md)与[最终记录](../evidence/current-tasks-fixes-20261014/core-smoke/check.json)。T11、成员复现与规格冻结仍未关闭。
