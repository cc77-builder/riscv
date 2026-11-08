# Pgroup 局部实验控制器独立静态审查

## 结论与范围

最终审查对象为 `controller/pgroup.py` 的 SHA-256 `794544ddfb3455b05deaffe8588d3c9715d02446ac04c50fe2710c6caaaafc0e`，45,126 B。**未发现阻止按现有合同继续冻结、运行本次局部实验的剩余静态缺口。** 初版末端中断检查窗口已用一个独立、可逆的小改动闭合，具体见下文。

此结论仅来自云端现有文件的静态阅读、JSON 字段核对、AST 提取与逐字节比较。没有访问 PC、Pro 或网络，没有导入或执行被审控制器及其 helper，没有启动编译、结构证明、FU、EDA、整核或应用运行。没有将静态审查记作新候选的正确性或 PPA PASS。

审查任务是核实新 Pgroup 控制器相对于已运行 prefix 基线的输入闭包、证据适用范围、路径、资源回收和结果状态。未扩大到全 FU 时序形式化证明、整核验证或新的覆盖范围；这些不作为此次局部准备的新增门槛。

审查开始：2026-11-08 02:20:15 UTC。最终文件回读与补改核对完成：2026-11-08 02:27:49 UTC。

## 已核身份

| 对象 | 字节数 | SHA-256 |
| --- | ---: | --- |
| 最终 `controller/pgroup.py` | 45,126 | `794544ddfb3455b05deaffe8588d3c9715d02446ac04c50fe2710c6caaaafc0e` |
| 最终 `controller/PGROUP_CONTRACT.md` | 7,702 | `295dcec00ba74f3805b8ec4ff24624308136e7602ad607bb76a4a7a8ce3989a5` |
| 最终 `controller/controller-derivation.json` | 20,821 | `dd6046d7001f264e9704030718f8d337870389afbe2095cf8b857d3826686ea7` |
| 控制器直接基线 `base/controller/prefix.py` | 43,201 | `8f33f550c9b7e74e8190cb5f5a2cfdcc693a783d86ae905ec3e60c7ad10d148c` |
| 新 `source/VDotDatapath.scala` | 9,850 | `1f9a4c807b30b8aa769e65595ce6b54619b190a5f2b5af1d531413de9970b90c` |
| datapath 直接基线 | 8,780 | `1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb` |
| `source/VDotElastic.scala`，与直接基线逐字节相同 | 8,999 | `912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92` |
| `source/source-derivation.json` | 8,340 | `b757bddd341c5dae1188b6a45a1a88ba32ed7b856864e4fbc6e503283b13a630` |
| 未修改的 `controller/verify_csa.py` | 14,051 | `e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de` |
| 已闭合 prefix 基线 `source-review/prefix-candidate-v1/actual-result.json` | 205,865 | `a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0` |

最后一项是独立回读的历史实际结果，不是本次新运行结果。该记录的四个 consumer 为 feature 0/1 × cost/FU；两项 R miter 分别是 19 位、2 行与 20 位、4 行，均记录 `PASS`、无约束输入、solver proved、退出码 0；cost 结果顺序确为 `[0,1]`，与新控制器计算差值的索引一致。

## 1. 新输入与快照闭包

静态检查入口 `run()` 的固定输入、派生关系与快照阶段，以及末端核验，未见本次新增加输入的遗漏或必然路径冲突。

- 控制器要求新 datapath、wrapper、完整 source derivation、未修改的结构 verifier、原 resident 源码、classpath 配置、生成配置、成熟 helper、FU C++/vectors、映射模板和工具等与各自来源一致。新控制器的 derivation 同时绑定基线 SHA、候选 SHA 和全文件可逆关系。
- 我独立逆序应用最终 **23 项**控制器文字变换，每一项的目标片段均恰好出现一次；恢复后的完整字节与实际 `base/controller/prefix.py` 相同。新 source 的 **1 项**完整对象替换也可恢复完整 datapath 基线，且整个 wrapper 与基线字节相同。这证明了本次文字改动范围，没有代替新 RTL 的算术验证。
- 直接 prefix 结果固定 SHA 和长度，读取其终态、资格字段、源快照、四套生成物、每套精确五个 SV 文件、filelist/resource manifest、两套 R proof 的 RTL/gold/gate/script/log。相关输入先 pin 后复制，复制物再比对记录 SHA。不能只换一个旧结果 JSON 而继续使用其他来源的 proof 或生成物。
- 新 overlay 的编译产物递归纳入 class pins，并置于原 classpath 前方。没有沿用一个只枚举旧固定 class 集合的约束，因此本次 `HeapBit` 等新内部编译类不会天然遗漏。原完整 classpath 和原本缺席的可选资源在运行前后都核对。
- 新生成的四套 consumer、结构报告、实际 FU binary 及实验相关输入建立生成 pins，最后与原输入、快照、overlay 类一起核验。最终输出目录必须不存在，且与 repository、原 cost/FU、当前源与控制器以及四组历史 baseline 互不包含；编译、临时文件、生成物和日志在本次独立输出下。

这里核实的是控制器的消费和记录闭包；没有声称本机路径、内存、文件权限或全部工具实际可用。这些仍应由正常启动前检查和本次实际回执说明。

## 2. 新 P 的证明没有借用旧 P PASS

新资格入口是**对本次新生成的实际 CSA SV 调用固定原样 `verify_csa.py`**。四个 consumer 的 CSA 全字节相同后，控制器要求结构报告同时满足：完整解析、全输入等价、verifier SHA、实际 RTL SHA、477 个 FA、17 个 HA，并要求无丢弃 carry、row0 的第 18 位恒 1、row1 的第 18 位恒 0。报告记为本次新证明，`arithmetic_structure_proof_reused` 为 false。

原 verifier 的完整解析、部分积与符号修正、FA/HA 真值、层级和权重、唯一消费及输出行检查仍保留；它允许来自更早合法层的项，未把原 P 的具体分组顺序硬编码成新 P 必须满足的结构。新分组必须实际通过这些检查，控制器没有用旧结构报告替代它。

固定行符号与无丢弃 carry 条件对 feature 1 有实际作用：结构证明给出带固定修正的整数 heap 等式，row0 的符号解释恰好消去 `2^19` 修正；随后把两条 19 位行分别符号扩展到 20 位才可保持相同的有符号和。控制器没有把“仅模 `2^19` 等价”直接提升成此处更强的结论。

新 `independent_miter` 明确是 `NOT_RUN`、`solver_equivalence_proved=False`；旧乘法 solver 的 `UNKNOWN_EXTERNAL_TIMEOUT` 移到 `historical_multiplication_miter` 并保留旧输入来源。未发现把旧 UNKNOWN 写成本次运行，或把旧乘法结论转授新 P 的路径。

## 3. 旧 R SAT 的复用边界适当

控制器先核实历史两项 miter 的特征、宽度、行数、无约束输入、退出码、solver 结论和未重试状态，并固定实际 RTL、gold、gate、证明脚本和原始日志。历史日志还须有单个成功标记且没有失败或 ERROR。原 prefix 控制器源码显示该 miter 对实际组合 R 与直接模加法作等价证明，输入没有依赖旧 P 的取值约束。

新生成阶段另外要求：

- 两个 feature 的 cost/FU 新 R 模块分别与对应历史实际 `VDotPrefixFinish19/20.sv` 全字节相同。
- 每个新 wrapper 与相应旧 prefix wrapper 全字节相同；成熟 `wrapper_binding` 继续核对 P 的输入分半、19 位行、feature 1 的符号扩展、R 接口及结果连接、非数据时序赋值和异常输出行为。
- 新 `prefix_miters` 显式记录复用来源和依据，并再次核对新实际 finish SHA 与原证明的 actual RTL SHA。

因此复用的是相同 R 组合函数在全部输入上的证明，不是新 P 的证明。新 P、R 精确字节与 wrapper 连接约束共同组成这里的算术依据。未发现旧 PASS 无条件传递给新 P 的状态路径。

## 4. FU、映射与时序保持原验证用途

静态 AST 源片段比较确认 `command`、`interrupt`、`check`、`wrapper_binding` 与直接基线逐字节相同。完整 FU `for feature in (0,1)` 循环也逐字节相同；此次提取范围为 1,508 B，SHA-256 `64206a08f5440d9a05840ea5b840d7c363955515f17dca2819acc8f9625ead62`。

每个 feature 仍须重新 lint/build、执行完整正向 FU vectors，并依次执行 identity、wen、high、cancel 四个实际注入及原 negative checker；总计八个负控。旧 FU PASS 没有直接用作新 FU 的完成状态。

映射/STA 继续使用固定库、原 common 边界、原 abc 约束和同模板；只替换本次输出路径及实际模块读取块，再逆变换核对原模板完整字节。新模块读入包含 CSA、相应宽度的 PrefixFinish、VDotElastic 和 CommonFuCostTop。结果仍区分实际面积、五类时序路径、DFF 记录和不同历史基线差值。DFF 数相等、面积门槛和 nominal setup 是否满足是记录，未被混作 FU 功能资格。

此次 local 完成状态不会把 `parent_qualified`、整核、应用或 core cost 字段设为真。结构深度估计不是 STA 测量，也不构成实际性能提升。新映射和时序结果未产生前，不能据本审查宣称优化成功。

## 5. 资源、命令范围与回收

固定 CPU 已从基线 1 改为 **2**，CLI 和运行内校验一致；单 worker、nice 5、Java 单处理器、j1、线程环境及独立临时目录保留。完整成功路径为 32 个子命令：compile 1、generate 4、新结构 checker 1、FU 22、map/STA 4；总预算固定 1,200 秒，子命令预算受剩余总预算约束，未增加隐式重试或自动延时。

新命令仍以独立进程组执行，等待期间检查信号和时间；正常返回前要求进程组消失，异常路径仍经原有限停止/回收逻辑，并记录日志和终态。所有命令成功返回后，最终 `all_children_reaped` 由每条命令的实际记录计算。这里未发现本次派生引入的资源回收回归。CPU2 与其他正在使用的核分离、启动时实际资源占用及内存余量，应由主端按合同核实，不由云端静态阅读代替。

## 6. 发现的一处问题及最小闭合

初审版控制器 45,009 B / SHA-256 `038c07162603cdb0e5a4c825e9d460df55578d94ec80914ec4910902cebd818b` 在末端 `check()` 后执行全量 pin/classpath 核验和 manifest 保存；期间若收到 TERM/INT，signal handler 仅设置 pending 标志，原代码可能在未重查 pending 的情况下写成功状态。原末端虽再次检查总 deadline，却未覆盖这个 pending 窗口。

已向主端提出最低修复：保留成熟函数与 FU 段，在最后 manifest 保存之后、成功状态更新之前，再调用一次 `check()` 并检查 deadline。最终版本的实际顺序已经是：

1. 核验全部固定输入、快照、class、生成物的 SHA。
2. 核验原完整 classpath 和缺席资源，检查总 deadline。
3. 保存最终 artifact pins manifest。
4. 再调用 `check()`，再检查总 deadline。
5. 更新本次 local 成功状态。

该补改作为独立文字 edit 纳入最终 23 项可逆 derivation；合同同步说明了这一顺序。我独立回读最终源码及 derivation，确认它们相互一致。**此具体窗口已静态闭合**；没有因此改写成熟 command/helper，或增加新的覆盖验收条件。此判断针对最终成功决策前已有的待处理信号，不声称建立任何操作系统级原子信号/文件提交机制。

## 仍需本次实际结果回答的问题

目前只有“可以继续准备这一有界局部实验”的静态结论。实际新 CSA 是否满足结构及 signed-row 条件、两套新 FU 与八个负控是否通过、映射和 STA 是否得到更好的合格结果，以及实际输入保持和进程回收是否完成，都尚未由本审查执行。应按原合同保留真实成功或失败输出，以这些结果决定保留、调整或放弃新 Pgroup。没有必要为本次准备追加旧 monolithic multiplication SAT 重跑、整核或应用运行。
