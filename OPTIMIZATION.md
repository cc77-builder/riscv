# zjhwork2：后续优化开发入口

用户已明确要求从现有进度建立 `zjhwork2` 并开始优化。2026-10-17 本轮开始时，GitHub 中该分支已存在，且与 `zjhwork` 一样指向 `3d051f0d870945215724bcc579496403e8884aee`，因此直接续做，不重建、不重置分支。

本轮唯一写入目标为 **cc77-builder/riscv:zjhwork2**。不推送 zjhwork/main/zufan/James_Hotten，不覆盖成员成果、不强推。旧 AGENTS/README 中的发布分支是历史约定；本页记录本次用户的新指示，不表示其他成员已 ACK。

## 第一批代码：O0 诊断入口

- [O0 使用与边界](team/optimizations/o0/README.md)
- [轨迹分析器](team/optimizations/o0/analyze.py)：复用固定 T12 解析和时钟映射，生成事务时间线、接受间隔、响应延迟、反压与父级 busy 等待统计。
- [主机测试](team/optimizations/o0/test_analyze.py)：合成轨迹正反例，不是硬件仿真证据。
- [本批验证记录](team/optimizations/o0/host-check.json)：绑定实际测试代码摘要、环境与未运行项。
- [O1 接口变更约定草案](team/optimizations/o1/CONTRACT.md)：规定下一批硬件/父级/检查器必须共同改变的行为，尚不是实现。

**状态：O0 工具已实现并通过主机测试；真实基准轨迹诊断、O1 RTL、父级联调与新全核回归仍待运行/实现。未获得新的加速比。** 本批不改 src/、NEMU、ISA、T05 数据、原 T12 检查器、build.sc 或任何旧封存证据。

按[后续优化方案](team/香山vdot_后续优化方案_20261017.md)推进 O0 → O1；只有收益/接口成本明确后才决定 O2。T14 构建基准需显式设置 `VDOT_T14_FUSED_INPUT=1`，默认仍为基础模式。T15 INT16 仅为独立单元实验。正式 T16 报告继续后置，开发证据持续保存。
