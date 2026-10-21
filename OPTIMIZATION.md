> 2026-10-21 本机 O2 基线：Linux LF、126个依赖、3430项输入及新全核构建通过。实际16次启动，选定14项作业；117个唯一矩阵用例/124次执行、5378条正常VDOT提交、bit100拒绝及恢复通过。严格重审为 INCOMPLETE，仅缺 PARTIAL_KILL；固定seed=1补测仍为0。原FAILED和两次INCOMPLETE均保留。该结果属于0484构建，不能用于随后H1整合源码的验收。O1/O2默认关闭，未推送，main不改；T17/人工ACK/新性能与PPA未完成。 [复验记录](team/docs/o5-current-fullcore-20261021.md)。下方为历史进展。

> 2026-10-21：[Linux LF与当前源码全核复验](team/docs/o5-current-fullcore-20261021.md)。126个依赖及显式新输入合同准备完成，3430项输入通过严格预检。真实构建遇到内存不足后改用分阶段合同，当前G3尚未验收；性能/PPA及独立T17继续另行判定。O1/O2默认关闭，本轮未推送。

> 前轮：[同步审查与O5准备](team/docs/reproduction-readiness-20261021.md)，当时70项已知输入缺失的记录保留。

> James_Hotten 整合范围（2026-10-20）：前一轮 O2/O3 已在 769b3b4b1 验证；本轮另行审查 zjhwork 9b6cf0749 的 O4 更新。O4 原测量未覆盖本地 DIV 取消时钟修复，保持历史来源绑定。O1/O2 默认关闭，main 不改；下方外部分支发布授权仅作历史记录。本轮记录：[O4 整合审查](team/docs/o4-integration-20261020.md)。

> 2026-10-20 James_Hotten：已整合并审查 O2/O3 的40项新提交，修复取消时钟、来源及验收问题；631项主机检查与新父级验证通过。见[本轮记录](team/docs/o2-o3-integration-20261020.md)。历史性能保持原版本绑定，O1/O2默认关闭，本次仅本地合并，main不改。
# 最新项目状态与本批发布（2026-10-20）

用户授权将当前项目状况保存为Markdown并发布至cc77-builder/riscv的zjhwork。本批包含已有6项O4提交、O2主线选择和状态快照，允许正常快进上传；最终成功与SHA以远端回读为准。

技术主线采用O2，O0–O4已有对应证据；下一步O5/T17及O2减代价审查，G5最终冻结待完成，T16/T18工程冻结后集中开展。源码默认开关未改，人工ACK待实际成员完成。此次仅整理与发布，不重跑已完成工程或改旧封存载荷。

当前入口：[项目当前状况](team/docs/project-status-20261020.md)。下方“未上传/不push/待做”等按历史时点阅读；原始证据保持生成状态。

# 当前主线：O2 两槽弹性 FU（2026-10-20）

按用户“推荐一版并沿用其继续优化”的要求，后续开发采用O2，O1作为冻结对照与回退。G4 batch周期少39.03%，O3应用仅少0.62%–1.50%；完整FU面积+41.41%、VFEX4父级+1.25%。这是一项开发主线选择，最终参赛采用仍须完成O5/T17及G5。

下一步固定O2复现入口、补齐独立复现，同时审查额外性能字段和控制路径成本；后续每次只实施一个有证据支持的优化。工程冻结后再集中编写T16与准备T18。默认源码开关与旧封存证据保持原状，本次只更新计划，未运行新测试或推送GitHub。

详细依据和执行顺序见[O2主线选择](team/docs/o2-mainline-decision-20261020.md)。下方保留历史状态与原始计划，不作为当前待办顺序。

# 最新优化进度：O2 G4、O3完成；本批交付zjhwork

2026-10-20用户授权发布当前O2/O3成果。见[交付说明](team/docs/o2-o3-publication-20261020.md)，实际推送以远端回读为准。密封证据保留其历史状态。

| 工作包 | 当前状态 |
| --- | --- |
| O0吞吐诊断 | 主线诊断已支撑后续实现，完整矩阵的剩余解释不冒称关闭 |
| O1同拍交接 | FU/父级/全核/公平性能已完成并此前发布 |
| O2两槽弹性 | G0–G4完成，尚待G5最终采用评审 |
| O3应用评估 | 四尺寸/三数据集/两软件/两口径已完成，原始日志及双平台复算通过 |
| O4结构与时序代价 | **下一项，待开始** |
| O5/T17 | 自动回归已具备，队友干净检出完整构建运行及人工复核待完成 |
| G5、O6/T16/T18 | 取舍、冻结后再集中报告和演示；不自动执行 |

O3数据复用版endtoend中O2相对O1降低0.62%–1.50%；需要结合O4成本判断采用价值，不能把G4的39.03%等同所有应用收益。O2默认仍关闭。下方保留各历史时点。

# O3应用评估：本轮自动测量及Linux严格重审完成

2026-10-19（任务开始日期），local/o3-gemv-20261019。先读team/workloads/o3-gemv/README.md及对应证据入口。56项合格作业（46项原通过复用、10项恢复补跑，另2项中断尝试保留）、1280窗口、768正式窗口及4项确定性重放通过；Windows原生复算状态另见delivery回执。不要重跑完成campaign或改密封证据。本轮本地保存未push，不自动O4/O5/G5或切换默认模式，正式T16后置。以下为历史状态。

# 当前任务：O3中断恢复进行中（2026-10-20，本地）

原campaign-01在46项通过后中断；两项只有部分日志、无真实完成退出，不能宣称仍在跑或已完成。
当前由resume.py在campaign-02导入46项字节相同证据，仅补跑剩余10项，另2中断尝试保留。
原始campaign-01、镜像和运行源码不修改。恢复编排99f04b9，原execute源码7a642b6，恢复交付工具8aab2ed。
当前进度查/home/riscv/riscv-lab/o3-gemv-20261019/campaign-02/state.json；
恢复启动回执recovery-launch-state.json；新监督根/home/riscv/riscv-lab/o3-gemv-recovery-delivery-20261020。
finish-recovery.py负责通过后的严格复核、封存、Windows复算和本地交付。不要再启动旧launch.py/finish.py或重跑全部测试。
本轮不push，不自动O4/O5/G5/默认切换，正式T16后置。以下状态为历史记录。

# 当前任务：O3 GEMV应用测试进行中（本地）

用户2026-10-19明确授权开始O3。工作分支local/o3-gemv-20261019，基点08fc5b4；
先读team/workloads/o3-gemv/CONTRACT.md及README.md。
26新镜像已编译/ELF审计，22主机检查通过，4项真实O1/O2冒烟已通过；
campaign-01正在正式应用测量，不能提前宣称56项/768正式窗口完成。
运行源码冻结7a642b6，构建软件5fdeba3，后处理工具6df07ca。

原始工作根/home/riscv/riscv-lab/o3-gemv-20261019；
交付监督根/home/riscv/riscv-lab/o3-gemv-delivery-20261019；
Windows入口D:/yanyi/riscv大赛/doc/O3应用测试_20261019。
先查两个state.json和launch-state.json。已经启动的launch.py及finish.py负责继续测量和通过后的严格复核/封存/Windows复算/本地交付；
不要重启已经在跑或完成的campaign，不覆盖原始日志。失败先读真实stderr/退出码，不能静默剔除样本或直接重跑所有任务。

O1/O2复用G4固定硬件，四尺寸(4,8),(8,32),(16,64),(4,13)，两口径/两软件/两方法/三数据集；
不改ISA/NEMU/旧基准和旧证据。最多两个单线程EMU。成果先本地保存，不push、不自动O4/O5/G5/默认切换，正式T16后置。
下文为历史状态。

# 后续优化开发入口

> 当前整合（2026-10-19）：以最新 zjhwork `cd866d52d` 为基准，并保留 James_Hotten `724fbb12f` 的时钟取消与验收修复。当前状态见[整合与审查记录](team/docs/o1-latest-integration-20261019.md)。以下全核及性能数字保留原受测版本绑定，不代表合并后源码的新运行；O1默认关闭。
## 当前进度：O1/O2 公平性能测量完成

2026-10-19。独立batch128平均cycles 362.500→221.000，降低39.03%；O2相对自身实测RVV为3.068×。独立batch相对本次新测O1降低39.03%，至少10%的预定工程目标达到。超过2%的场景均值退化调查项：无。

36项新EMU运行、478校验窗口、192正式样本与原始日志严格离线重审通过，见 [G4工程入口](team/optimizations/o2/performance/README.md)。本轮本地保存，未推送；O2默认关闭，无PPA或最终采用结论。下一步G5结合应用、时序/结构和独立复现，正式T16报告后置。

## 前一轮：O2 G3 完成时的进度

2026-10-19，新O2全核EMU的原十二项与两项补充验证已满足预期；117唯一矩阵、bit100差分拒错/正常恢复、原F2v七项、dense十二窗口及六项两槽覆盖均通过，正常程序共5378条vdot提交。95项主机检查及原始日志严格离线重审通过。见 [全核工程入口](team/optimizations/o2/fullcore/README.md) 与 [封存证据](team/optimizations/o2/evidence/20261019-fullcore-validation/README.md)。

本轮仅本地保存，未推送；O2默认关闭。下一步G4公平O1/O2性能对比，本轮没有新增加速比/PPA/最终采用或人工ACK结论，T16报告继续后置。

## 前一轮：O2 G1/G2 完成时的进度

2026-10-19，两槽弹性 FU、局部原子派发及真实占用门控已实现，隔离 FU 与真实 VFEX4/DIV/ClockGate 自动验收通过。连续流 II=1、无阻塞响应 2 拍；父级 13,515 条接受全部终结，16 项观察负控、旧模式回归与独立离线复核通过。见 [实现与复现](team/optimizations/o2/IMPLEMENTATION.md)、[正式证据](team/optimizations/o2/evidence/20261019-elastic-parent/README.md)。

下一步按合同做 O2 两槽全核观察器与 G3 回归，通过后才做 G4 同镜像公平性能对比。尚无 O2 整核加速比、PPA 或最终采用结论；O3/O4/O5、人工 ACK 和 T16 后置安排不变。本轮本地保存，不推送，O2 默认关闭。

## 前一轮：O2可行性评估与设计合同完成

2026-10-19，本轮已完成源码审查、24个旧性能作业/96个正式custom窗口的离线分析及O2合同；[当前判断与下一步](team/optimizations/o2/README.md)。推荐保留VFEX4的不定时延接口，先做两槽弹性FU和真实父级原型；没有O2 RTL或实测提速。O1保留，O3应用/O4时序/O5独立复现仍待推进，T16报告后置。本轮本地保存，不推送。

## 当前发布：O1 成果交付 zjhwork

已获用户授权，交付范围包括真实父级联调、全核回归与同镜像公平性能结果，见 [发布说明](team/docs/o1-publication-20261018.md)。下方未上传状态按历史时点阅读；实际发布以远端回读为准。O1默认关闭，后续优化及验证待新任务推进。

## 当前任务：O1公平周期对比完成

独立batch128平均周期 453.25→362.50，降低20.02%；O1相对实测RVV为1.870×。36次主运行及完整离线复算通过，其他场景数据见 [工程入口](team/optimizations/o1/performance/README.md)。

O1默认关闭，成果本地保存，未推送。O2按收益/成本另行决定，O3应用/O4时序与O5/T17复现仍待推进；正式T16报告后置，尚无PPA或人工ACK结论。

## 前一轮：O1 全核功能与控制回归通过，下一步为公平性能 A/B

新全局周期及身份观察器已在固定硬件 `18c0ce08` 的 MinimalConfig 单核 EMU 上完成十二项真实运行，全部符合预期；原检查器 `518c0567` 保持冻结，严格门禁集成提交 `d1100020` 对应的离线全套重审也已通过，原日志未改、未新增 EMU 运行。正常程序共提交 3,012 条 vdot，功能矩阵覆盖 117 个唯一用例（80 合法、37 异常），八分片执行 124 次；bit100 差分负控及同镜像正常恢复通过。控制程序自身满足八项覆盖，303 次同拍交接、62 拍 vdot 写回反压、3 次在途取消；密集程序 12 个窗口通过，另有 725 次交接及 2 次取消。见 [工程入口](team/optimizations/o1/fullcore/README.md)、[协议](team/optimizations/o1/fullcore/SCHEMA.md) 和 [完整证据](team/optimizations/o1/evidence/20261018-fullcore-validation/README.md)。

本轮完成固定配置下的功能、异常和控制验证；全核共享 FU 仅覆盖 vdot/VIDiv，未覆盖 VFDiv，vdot 取消仅观察到 reduce 阶段。下一步按计划开展 T14/O1 同镜像公平周期性能 A/B，现有密集窗口数据不构成新的加速比或 PPA 结论。O1 默认关闭，成果本地保存，不推送 GitHub；正式 T16 报告继续后置，T17 及团队人工 ACK 未完成。下文父级/FU 等状态按各自历史时点阅读。

## 前一轮：O1 真实 VFEX4 父级联调通过，本地保存

2026-10-18，固定源码 `99d5f6c` 的真实 ExeUnit＋VDot/VIDiv/VFDivSqrt＋三个 ClockGate 两模式通过。10022 组 vdot、真实 DIV、全部九种 FU 切换、432 组 redirect、27 组 reset、20000 拍随机控制及七项负控均有原始证据。O1 同拍交接 10343 次，连续 vdot 接受间隔从 T14 的 3 拍变为 2 拍；这是父级指标。

[父级工程记录](team/optimizations/o1/parent/README.md) 与 [证据](team/optimizations/o1/evidence/20261018-parent-validation/README.md) 记录两次前期失败、实际源码/工具/依赖和边界。T14 对照在 reset/redirect 主动抑制 valid，O1 不抑制；两模式总周期不能作为公平加速比。现有 DIV 的取消当拍旧响应及取消后门控行为留待全核验证，不隐去或改变其黄金预期。

本轮未改生产 RTL，成果本地提交，尚未推送 GitHub。`parent_validation_pass=true`，O1 全核回归、观察器适配和性能 A/B 尚未完成。下一步补 O1 观察器并跑全核功能/异常/控制压力，通过后再测同镜像性能。默认 O1 关闭，正式 T16 报告继续后置。


## 前一轮：三模式 FU 本地验证通过（历史）

2026-10-18，按用户要求复用 `zjhwork2@75dce60` 的 O0/O1，在本地修复并验证后准备普通快进上传 `cc77-builder/riscv:zjhwork`。实际构建源码为 `db0408aa42afc13e3ff93e865f26a2d5bfb02c93`；下方 zjhwork2 目标和未验证状态均为历史记录。

本轮将环境激活移到工具检查之前，并用严格负控校验拒绝 `fault escaped`、无关错误和重复标记；首次真实编译又修复 `ExeUnit.scala` 两处 `FuType.vdot` 硬件比较，右侧改为 `FuType.vdot.U`。`fu-01` 的编译失败保留，修复后的 `fu-02` 三模式 Chisel/Verilator 验证通过。原基础版、T14 和 O1 的真实 FU 响应延迟/最小接受间隔分别为 **3/4、2/3、2/2 拍**。

O0 113 项、O1 26 项主机检查通过。O1 接受 13626、响应 13212、取消 388、复位丢弃 26；同拍交接 12237 次、反压 26659 拍。原 10022 算术向量完整结果及控制用例通过，候选与旧模式控制矩阵并非完全相同。四项 C++ 观测值破坏均被严格检出。见 [O1 工程入口](team/optimizations/o1/README.md) 和 [本轮证据](team/optimizations/o1/evidence/20261018-fu-validation/README.md)。

当前 `parent_exu_elaborated=false`、`fullcore_difftest=false`、`performance_measured=false`，O1 默认关闭。下一步是真实 VFEX4 父级（含 DIV）联调，再补观察器、全核回归及公平性能 A/B。本轮没有新的全核加速比；正式 T16 报告仍待工程完成后集中编写。

## 历史：zjhwork2 的 O1 候选实现，尚未运行 RTL 验证

基点 `9e7cce9c9dc090e5280f1a7f8791551612777cc6`；唯一提交目标仍为 `cc77-builder/riscv:zjhwork2`。本批已修改生产 `VDot.scala` 和 `ExeUnit.scala`，新增 elaboration-only 开关 `VDOT_O1_HANDOFF=1`（必须同时设置 `VDOT_T14_FUSED_INPUT=1`）。默认开关为 0，原基础版/T14 分支保留。

候选包括 FU 响应拍接收下一请求、旧写使能寄存、父级只允许 vdot→vdot 交接，以及同拍完成/接受后保持 busy。ISA、乘法/归约、NEMU、原始数据、旧检查器及历史归档没有修改。旧 T12/T13 观察协议不适用于同拍交接，候选暂时拒绝启用这些旧 trace 开关，不能复用其通过记录。

新增真实 FU C++ 测试及三模式运行脚本。17 项主机合同/源码检查通过，C++ 仅用端口声明桩做语法检查通过，shell 语法通过；真实 RTL 脚本因缺少 Mill 明确退出 2。**没有 Chisel elaboration、Verilator、真实父级联调、新整核 DiffTest 或性能结果；不能声称 II=2 已在硬件验证。** 详见 [O1 候选入口](team/optimizations/o1/README.md) 及该目录的 verification.json。

下一步先在匹配环境运行三模式 FU 回归，再补真实 VFEX4 父级测试、O1 观察/时钟映射、完整控制回归与冻结基准 A/B。O0 其他场景仍是待办；本 pilot 的结果足以启动受控候选开发，不等于全部诊断结束。正式 T16 报告继续后置。

## 上一批：性能 batch128 逐拍诊断（历史）

从 `91b94073` 继续，仅写 `zjhwork2`。此次 176,256 字节上传文件与原性能 pilot 完全一致，原严格 trace 入口实际通过。768 次接受—响应—提交、48 条 CSR 采样已关联；发现 **738 次旧响应当拍的 busy 等待，且同一等待请求全部在下一拍被接受**。0 次写回反压；每个正式 128 点积窗口有 125 次上述匹配。

见 [性能轨迹诊断](team/optimizations/o0/PERFORMANCE_TRACE.md) 和 [实际回执](team/optimizations/o0/evidence/20261017-performance-trace/execution.json)。新增逐窗口/动态 ROB 分析器和 16 项离线测试，旧 functional 18 项也重跑通过。此次不再存在性能文件传输阻塞。

**此 pilot 已完成，为 O1 同拍交接原型提供依据；完整 O0 矩阵、O1 RTL/父级验证和新性能 A/B 尚未完成。738 不是可直接节省的周期数。** 本批不改生产 RTL、ISA、NEMU、原检查器和旧封存证据，不产生新加速比。后续优先联合处理 FU/父级 busy/新旧身份，不直接改写回优先级；正式报告仍后置。

## 上一批：上传功能日志重放（历史）

本批基点 `a877e0575ea91392edc7816637e51ae8d1689b36`，唯一发布目标仍是 `cc77-builder/riscv:zjhwork2`。

用户上传的 gzip 经完整摘要比对识别为 **functional-d0-s06-r0**，不是原性能 pilot 的 performance-d0-s06-r0。本批实际解析硬件原始流，关联 12 次功能调用、48 条 CSR 采样、6 条 FU 接受—响应—提交；每条响应 2 拍、提交观测差 4 拍，未观察到 busy 等待/写回反压。18 项离线回归与拒错检查通过。

详见 [本次真实轨迹与边界](team/optimizations/o0/FUNCTIONAL_TRACE.md)。新入口为 `replay_functional_trace.py`；旧性能 pins 和原检查器不变。该运行只有孤立功能调用，不能证明吞吐瓶颈或新加速比。**O0 密集性能诊断未关闭，O1 生产 RTL 未修改。** 下方是此前批次的历史状态，不将本次功能重放当成性能 pilot 已完成。

## 上一批：O0 归档来源核验（历史）

本批在 `492db2d9e2a5041db5e0a7d1dec16555a7e1b205` 上续做，唯一目标仍为 `cc77-builder/riscv:zjhwork2`。

新增 [归档重放入口与边界](team/optimizations/o0/ARCHIVE_REPLAY.md)、[来源校验脚本](team/optimizations/o0/replay_archive.py) 和 [固定 pilot](team/optimizations/o0/pilot-t14-batch128.json)。已实际核对一个 T14 batch128 原始程序流的 12 个窗口及归档身份；新增 52 项主机测试通过，包含真实 O0/T12 解析器的合成轨迹联测。证据见 [本批实际回执](team/optimizations/o0/evidence/20261017-archive-gate/verification.json)。

**真实硬件 stderr 的完整搬运/逐拍重放仍待完成，O0 未关闭；O1 RTL 和新加速比尚未产生。** 默认严格模式缺日志就退出，不用程序 PASS 或已保存的 FU 汇总代替真实轨迹。旧 T14 的 `[465,464,464,464]` 周期样本不与新统一基准的 453.25 直接比较。本批不改生产 RTL、NEMU、ISA、旧检查器、黄金数据和旧封存记录。

## 第一批代码：O0 诊断入口（历史）

用户已明确要求从现有进度建立 `zjhwork2` 并开始优化。2026-10-17 本轮开始时，GitHub 中该分支已存在，且与 `zjhwork` 一样指向 `3d051f0d870945215724bcc579496403e8884aee`，因此直接续做，不重建、不重置分支。

本轮唯一写入目标为 **cc77-builder/riscv:zjhwork2**。不推送 zjhwork/main/zufan/James_Hotten，不覆盖成员成果、不强推。旧 AGENTS/README 中的发布分支是历史约定；本页记录本次用户的新指示，不表示其他成员已 ACK。

- [O0 使用与边界](team/optimizations/o0/README.md)
- [轨迹分析器](team/optimizations/o0/analyze.py)：复用固定 T12 解析和时钟映射，生成事务时间线、接受间隔、响应延迟、反压与父级 busy 等待统计。
- [主机测试](team/optimizations/o0/test_analyze.py)：合成轨迹正反例，不是硬件仿真证据。
- [首批验证记录](team/optimizations/o0/host-check.json)：绑定当时实际测试代码摘要、环境与未运行项。
- [O1 接口变更约定草案](team/optimizations/o1/CONTRACT.md)：规定下一批硬件/父级/检查器必须共同改变的行为，尚不是实现。

首批状态：O0 工具已实现并通过 27 项主机测试；真实基准轨迹诊断、O1 RTL、父级联调与新全核回归仍待运行/实现。未获得新的加速比。首批未改 src/、NEMU、ISA、T05 数据、原 T12 检查器、build.sc 或任何旧封存证据。

按[后续优化方案](team/香山vdot_后续优化方案_20261017.md)推进 O0 → O1；只有收益/接口成本明确后才决定 O2。T14 构建基准需显式设置 `VDOT_T14_FUSED_INPUT=1`，默认仍为基础模式。T15 INT16 仅为独立单元实验。正式 T16 报告继续后置，开发证据持续保存。
