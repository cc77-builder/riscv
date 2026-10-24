# R3 perfDebugInfo：保留完整边界，补强真实父级验证

2026-10-25（UTC+08:00）。操作 ID：`20261025-LiZufan001-r3-perf-0001`。

**本子项完成：维持生产 577 位 PerfDebugInfo 及两槽事务身份，补齐真实 VFEX4 父级的完整元数据验证。** 固定源码中，部分返回字段确实没有活跃的最终语义消费者，或在下游被覆盖、由独立副本提供；但现有完整接口、O2 身份合同和配置相关观察约束仍然存在。本轮没有成立的直接裁剪方案，未改变生产 RTL。新增成果是更充分的正确性证据和可复核的消费者／成本判断，没有新增应用加速比、整核资格或 ASIC 成绩。

[合同](CONTRACT.md) · [封存与离线复算](evidence/r3-parent-v2/README.md) · [完整载荷清单](evidence/r3-parent-v2/manifest.json) · [运行定位](evidence/r3-parent-v2/files/runtime/locations.json)

## 1. 恢复的实际基点与修改范围

指定 Windows 来源入口保持在 `ff58e519091f273c4bc177f5e82cfbbfaf102cc5`；本轮从已发布 `zufan` 的 `5640b7fda828109a875bc4e2dfb9d9a1da0266da` 建立独立工作树和 index。未切换来源入口、未接管仍有效的 R2-S3/caller 认领。caller 的已结束 PASS 状态只用于判断同机运行资源，不用于释放其任务包或转授资格。

修改限于团队 G2 Scala 适配器、C++ scoreboard、正负／逐拍检查器和 runner，以及本目录审计工具、证据及导航。生产 `src/`、官方依赖、参考实现、模型和黄金数据保持原样。当前基点与固定 T17 源码 `34bae6d4acceac939f958199dae53c14bc1f6183` 的以下 Git 对象相同，且本轮工作区生产目录 diff 为空：

| 对象 | 两个提交共同的 Git 对象 |
| --- | --- |
| `src` tree | `17b4b38675bf8c87eeff0287dbc09e391a53d307` |
| `build.sc` blob | `ef9478063bdc65d98234b7d388006de4d68212e5` |
| `team/models/vdot/data` tree | `90843867e5464e6167aba0caae2dacf662ef356b` |

依据：[生产对象与生成物](evidence/r3-parent-v2/files/runtime/consumer-generated-v1.json)、[本轮输入身份核验](evidence/r3-parent-v2/files/runtime/run-identity-v1.json)。T17 原源码有其先前保留的未跟踪团队脚本，本轮未动它们；新源码由 Git 对象检出，未复制这些未跟踪内容。

## 2. 发现的覆盖缺口与实现

旧 G2 确实比较完整 child perf，历史 PASS 继续按原身份解释。其不足在于：

1. 旧适配器用同一个 tag 填充九个 64 位字段，随后只另设 renameTime。其余八字段始终同值；八者之间 28 种两字段互换不会改变这个激励，不能据此证明字段没有错接。
2. 旧完整 perf 比较位于 child FU 输出；真实 `ExeUnit.io.out.bits.debugInfo` 只有 issueTime、renameTime 两个命名字段被独立导出，剩余 449 位没有同样的父级全宽检查。
3. 旧 perf 期望来自 child 输入 tap，父级输入路由错误可能被接纳为期望值。

新适配器提供完整 577 位外部输入。C++ 从请求生产端保存期望，分别比较 child 输入、child 输出及真实父级输出；完整父级包也进入背压稳定性检查。普通请求用确定性 SplitMix64 产生九个互异的完整 64 位值，独立设置最高有效位；VPU 噪声 tag 保留。

保留原 12 组控制／算术场景和 22＋10000 个唯一黄金向量，新增第 13 组：577 对 walking-one／walking-zero。每对占满 P/R，执行 1～3 拍背压、拒绝第三条噪声输入并排空。最高有效位为 bit576，高于它的 padding 必须为零。新增 1154 个传输事务不计作 1154 个新算术黄金向量。

`metadata.log` 另存完整原始包：A 为接受时的外部期望及 child 输入，O 为每次可见的 child／parent 输出，E 为响应、取消或复位终结。独立 [audit.py](audit.py) 先调用严格逐拍控制重放，再按 cycle／seq 核对全部 A/O/E、完整位值、事务守恒及 walking 实际响应。它可直接读取原文或 gzip，分别记录传输字节和解压载荷哈希。合同标记 `perf_contract=2` 不代替源码身份。

## 3. 本轮真实验证结果

配置为 MinimalConfig、单核参数、ROB48、VLEN128、O2＋H1，实例化真实 VFEX4、Vdot、VIDiv、VFDiv 和 ClockGate。生产 O2/T13 trace 在本次隔离父级构建中关闭；观察来自团队适配器。Linux 原生目录实际运行 Chisel／firtool、Verilator 和 C++，CPU affinity 为 0–3，构建最多四并发，JVM 参数为 `-Xmx5G -Xss8m -XX:ActiveProcessorCount=4`。

| 检查 | 实际结果 |
| --- | --- |
| 正向父级仿真 | 37,817 拍，13 组全部完成 |
| 事务守恒 | 接受 14,669＝响应 14,191＋取消 418＋复位丢弃 60，最终无在途 |
| 每类 FU 接受 | Vdot 12,979；VIDiv 859；VFDiv 831 |
| 完整元数据 | 14,669 次接受核验，17,342 次 child／真实 parent 全宽观察，46,680 条 A/O/E 事件全部对应 |
| 普通独立字段激励 | 13,515 个请求的九个 64 位字段互异 |
| 全位扫描 | walking-one 577、walking-zero 577，全部实际响应；577 位均出现 0 和 1 |
| 原算术／控制合同 | 10,022 个唯一黄金向量；冻结流 10,021 个 II=1 间隔及全部两拍响应；三 FU 切换、反压、逐槽取消与 TE=0 复位保留 |
| 观察负控 | 原 16 项＋新增输入路由／字段交换／父级非命名字段／跨槽身份 4 项；20 项均真实退出 1，并由精确类别检查器接受 |
| 证据篡改 | 8 类全部拒收：父级 bit576、child 字段交换、输入 bit448、缺少／重复观察、错误 seq、错误 walking 标签、缺少 END |
| 检查器单测 | Linux 42 项通过；Windows 结果见交付回执 |
| 旧合同兼容 | 真实旧 H1/G2 的 34,356 拍、12 组日志通过新版控制重放，仍标识 perf 合同 1，不授予新覆盖资格 |

来源：[原始运行与退出码](evidence/r3-parent-v2/files/run-02/commands.json)、[原始控制日志](evidence/r3-parent-v2/files/run-02/result.log.gz)、[完整元数据日志](evidence/r3-parent-v2/files/run-02/metadata.log.gz)、[最终原文审计](evidence/r3-parent-v2/files/runtime/post-raw-audit.json)、[压缩原文审计](evidence/r3-parent-v2/files/runtime/post-gzip-audit.json)、[旧日志兼容与网表子集复核](evidence/r3-parent-v2/files/runtime/historical-reuse-v1.json)。

20 项负控属于 C++ **观察值**故障注入；8 类篡改检验离线证据拒收。两者都不称 RTL 硬件故障注入、形式等价或新 DiffTest 运行。控制重放不重新计算算术，算术正确性依据本次真实 C++ scoreboard 的完整结果比较。legacy DIV 取消当拍仍可能有原始可见输出，O 会核对其旧事务包，E 随后记录取消，不误计作响应。

## 4. 实际消费者：返回值与独立副本分开

固定 [Bundle 定义](https://github.com/cc77-builder/riscv/blob/5640b7fda828109a875bc4e2dfb9d9a1da0266da/src/main/scala/xiangshan/Bundle.scala#L237) 为九个 64 位字段加一位。以下位号按当前 `asUInt` 从低到高，结论限于所审 VDot→ExeUnit→WB→CtrlBlock→ROB 路径：

| 字段 | 位号 | 已确认的下游关系 |
| --- | --- | --- |
| tlbRespTime | 0–63 | WB 的表面使用位于 InstTable；固定 utility 条件关闭该 writer。ROB enqueue 另有本地初始化。 |
| tlbFirstReqTime | 64–127 | 同上；不能把字段名引用当成活跃消费者。 |
| runahead_checkpoint_id | 128–191 | 本路径未发现活跃的最终语义消费者；上游构造或注释不等于返回值消费。 |
| writebackTime | 192–255 | CtrlBlock 在送 ROB 前覆盖为 GTimer；ROB 统计使用覆盖后的值。 |
| issueTime | 256–319 | WB 更新 ROB debug_microOp，参与条件延迟统计。 |
| selectTime | 320–383 | WB 更新 ROB debug_microOp，参与条件延迟统计。 |
| enqRsTime | 384–447 | WB 更新 ROB debug_microOp，参与条件延迟统计。 |
| dispatchTime | 448–511 | ROB enqueue 时使用本地 timer，WB 更新列表不替换该值。 |
| renameTime | 512–575 | ROB enqueue 已保存独立副本，WB 更新列表不替换该值。 |
| eliminatedMove | 576 | DiffTest 判定使用顶层 DynInst.eliminatedMove 的 ROB enqueue 副本，不能归因于 perf 返回位。 |

[CtrlBlock](https://github.com/cc77-builder/riscv/blob/5640b7fda828109a875bc4e2dfb9d9a1da0266da/src/main/scala/xiangshan/backend/CtrlBlock.scala#L124) 的覆盖以及 [ROB](https://github.com/cc77-builder/riscv/blob/5640b7fda828109a875bc4e2dfb9d9a1da0266da/src/main/scala/xiangshan/backend/rob/Rob.scala#L408) 的保存、WB 更新、统计和 DiffTest 副本已按实际源核对。性能计数器是否形成消费者还受 `EnablePerfDebug`、FPGA 和 PerfLevel 条件控制；本轮不把源码中的全部表达式视为所有配置下都有效。

这里有一个影响判断的固定依赖条件：utility 精确 pin 为 `a8ca0c6564865ee69b564d431ecbc52074ba8060`。[ChiselDB.createTable](https://github.com/OpenXiangShan/Utility/blob/a8ca0c6564865ee69b564d431ecbc52074ba8060/src/main/scala/utility/ChiselDB.scala#L234) 默认 `basicDB=false`，而 Rob 的 InstTable 调用未覆盖它；当前实现向 Table 传入 `!(basicDB & enable)`，Table.log 仅在该参数为 false 时实例化 writer。因此不能因 Rob.scala 中存在 TLB/dispatch/rename 表达式就认定该日志消费者活跃，也不能将此结论推广到其他 utility 版本。

另一方面，完整边界仍被明确保留：

- VDotElastic 的 P、R 各保存整包，在同一事务转移边沿搬运；ExeUnit 以 FU one-hot 选择整包到最终 debugInfo。
- BackendParams.debugEn 来自 EnableDifftest；WbArbiter 在该条件下对完整 WB bundle 施加 dontTouch。这是配置相关的结构观察约束，不等于 DiffTest 对这些位逐位作架构比较。
- O2 trace 启用时观察完整接受／P／输出 perf，现有 O2 合同也要求元数据与 ROB、pdest 等身份一起保持。

固定源码摘录与 SHA 见[消费者源码快照](evidence/r3-parent-v2/files/runtime/consumer-source-v1.json)。本轮据此关闭“在当前合同下直接删 perf 字段”的假设；保留完整接口，同时补足能发现错接的测试。

## 5. 生成 RTL 与成本边界

本轮实际检查 T17 的 VDotElastic、ExeUnit_17、WbDataPath、CtrlBlock、Rob 五个生成文件，并逐一匹配 T17 原构建 `generated-artifacts.json`。该构建是 **observe profile**：O2_TRACE=1、T13_TRACE=1。VDotElastic 生成物明确保留 P 的 577 位和 R 的 577 位，ExeUnit 最终出口含全部十字段。此观察不能外推为关闭所有观察器后的整核实现。

另外对已封存 H1 映射 JSON 进行原始／压缩哈希、单元直方图和 Q 驱动核对，得到：

| 历史映射边界 | 全部 DFF Q 位 | P perf | R perf | 原单元面积和 |
| --- | ---: | ---: | ---: | ---: |
| H1 完整 FU | 1,742 | 577 | 577 | 17,298.246 |
| H1 完整 VFEX4 | 17,171 | 577 | 577 | 284,879.882 |

两份 perf 的所列位均由映射 DFF 的 Q 驱动。面积沿原 Nangate45 单元面积口径；它们是[历史 H1 同条件测量](../../o2/result-width/h1/H1_RESULT.md)，本轮只复核所引用子集，没有重跑综合或 STA。

原 O4 全接口和本轮测试出口都要求完整可观察；T17 又有 trace 条件。577 是包宽，1154 是上述两个历史映射边界中保存它的位数，二者都不是当前可以删除的面积／功耗。若将来研究不同观察配置或不同综合顶层，必须先明确新合同并重新测量实际存活逻辑与公平性能，不能把这张表当预估节省。

依据：[T17 实物绑定](evidence/r3-parent-v2/files/runtime/t17-binding-v1.json)、[历史映射子集复核](evidence/r3-parent-v2/files/runtime/historical-reuse-v1.json)。

## 6. 身份、失败与交付

成功 run-02 核对 434 份源码、126 个固定依赖和 57 份生成文件；58 条已记录命令全部符合期望退出码。运行前后枚举的源码内容及依赖相同；这与第 1 节的生产基点相等检查是两个独立事实。

- 黄金 TSV：`901a7be30e62b81bcd3df55b20538a5ba9c879ba9c7c34f28b8c0421d8e6a327`。
- 实际 Verilator 二进制：`18fcfd26f525b53812451ac1ca89110f26aeb46e33148487a8db0b1c2a27b2bc`。
- 运行审计器快照：`78dee0de95dbe8416784011b3d7e2639f3c340761729b65bd4c3438ac06b065c`。
- 最终发布审计器：`780f8daa1801fa378d3fa097029e2ddc393d9e906cf4f8a64e27023854326abe`。运行后仅增加 gzip 读取与双层哈希、收紧合同标记措辞；控制和 payload 重放算法未变，最终版本已对原文和 gzip 分别重算及拒错。两份源码都保留，没有回填运行源清单。

run-01 停在 Python 直接执行本机 Mill polyglot 启动文件的 `Exec format error`，未进入 Scala/RTL。确认其 Bash 调用能报告 Mill 0.12.3 后，在本轮私有 bin 中使用 Bash 包装，run-02 完成；未改动全局工具。原失败日志、命令、wrapper 内容与两个 SHA 都在证据中。

原始源码／产物位于 `/home/lizufan/riscv-lab/r3-perf-20261025-0001`，Windows 独立工作树为 `working-r3-perf-20261025-0001`。完整证据包包含 177 份载荷，保存字节 4,381,568，最大 blob 1,643,435 字节；manifest SHA 为 `6a12ae4bb166d16f871375b606a165673a0aa71e49c329138fde9e742c8e49d6`。运行缓存和可执行文件留在隔离目录，以清单标识；未复制或修改受保护的旧实验。

Linux 与 Windows 原生封存核验、最终 Python 原文复算及 Git 暂存字节检查分别见[交付回执](evidence/delivery/)。Git 发布与任务释放由同一操作 ID 的 Issue #2 事件定位。

## 7. 路线决定与接续

R3/perfDebugInfo 子项已达到有界终点：保留生产实现，补强当前父级正确性覆盖和复现入口。既有 O2＋H1、稳定 C 入口及 RVV 回退继续有效，本轮没有选择新的性能实现。

后续只有取得真实瓶颈证据或明确定义不同观察／综合合同，才重新研究字段成本；门控／ready 优化也须有属于 VDot 的实际路径与收益依据。R2-S3/caller 仍由原认领者处理，本轮不从“进程已结束”推断可以接管。已完成的旧 EMU、T17 和 PPA 不为延长工作轮次重复运行。
