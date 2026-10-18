# 后续优化开发入口

## 当前任务：O1 观察器已接入，全核回归进行中

新观察器使用全局周期，并分别记录旧响应、新接受和真实重定向身份。固定源码 `18c0ce08` 的全新 MinimalConfig 单核 EMU 构建通过；十二项实际回归正在运行，最终覆盖与完整通过状态尚待全部作业及离线复核完成。见 [工程入口](team/optimizations/o1/fullcore/README.md) 和 [协议](team/optimizations/o1/fullcore/SCHEMA.md)。

本轮先完成 O1 全核功能、异常、控制压力和密集窗口校验。密集程序的周期记录不能替代 T14/O1 同镜像性能 A/B；尚无新的加速比。默认 O1 关闭，成果本地保存，正式 T16 报告继续后置。下文已完成的父级联调是历史阶段记录。

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
