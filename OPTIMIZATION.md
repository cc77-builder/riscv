# zjhwork2：后续优化开发入口

## 当前进展：性能 batch128 逐拍诊断完成

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
