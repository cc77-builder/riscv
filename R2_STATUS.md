# R2 当前入口（2026-10-21）

用户当前指定：所有后续改动只提交 `cc77-builder/riscv:zjhwork2`，保留 `zjhwork`，不强推、不改写历史。

R2 原内核审查已在 a89648d7。现在 S2 安全 4×13 尾部已实施，并通过主机/交叉汇编/指令级模型/原渲染器集成检查；真实 B0/H1 EMU + NEMU DiffTest 和周期筛选未运行。117→83 是 reuse/endtoend 的静态主体指令数，不是周期成绩。

- [S2 实现、实际验证与剩余门禁](team/optimizations/o2/r2-safe-tail/README.md)
- [S1 寄存器分配及 RVV 对等方案](team/optimizations/o2/r2-safe-tail/S1_REGISTER_REVIEW.md)
- [本批验证摘要](team/optimizations/o2/r2-safe-tail/evidence/validation.json)

原 O3 源码、ISA/NEMU、生产 RTL、默认模式和历史证据未改。S1 仅完成设计审查，不自动混入 S2；不宣称 R2/R4/R5 完成。旧入口里的 zjhwork 发布指示和阶段进度按历史时点阅读。
