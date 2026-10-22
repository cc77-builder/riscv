# R2 当前入口（2026-10-21）

所有后续写入仅限 `cc77-builder/riscv:zjhwork2`；`zjhwork` 保持对照，不强推、不改历史。

## 最新：ELF / B0-H1 验证入口已提交，真实运行被环境预检阻断

基点 `24cb8b2e`。新增原 GNU+nexus-am 构建、S0/S2 严格 ELF/BIN 校验、B0/H1 冒烟与周期筛选入口。29 项主机测试及 24 组链接测试样本通过。**这些是检查器测试，不是正式 benchmark 验收。**

实际环境预检与完整流程尝试均退出 2：缺少原 GNU 工具链、nexus-am 库、B0/H1 构建产物及 NEMU/flash。正式 benchmark ELF=0，新 EMU=0，新周期数据=0；未生成虚假通过回执。

[本轮状态、实际边界及执行命令](team/optimizations/o2/r2-safe-tail/FULLCORE_VALIDATION.md)

预定流程：26 份 ELF；4 次冒烟全部通过后，48 次正式运行加 8 次重放。任何失败停止。S2 仍为显式候选，默认实现不变；R2 尚未完成。

## 前序成果

- `a89648d7`：[原内核反汇编审查](team/optimizations/o2/r2-kernel-audit/README.md)。
- `24cb8b2e`：[S2 安全尾部及主机验证](team/optimizations/o2/r2-safe-tail/README.md)。117→83 是静态指令数，不是周期成绩。
- [S1 寄存器分配与 RVV 对等方案](team/optimizations/o2/r2-safe-tail/S1_REGISTER_REVIEW.md)：仅设计审查，未实施 S1 内核或实测。

生产 RTL、ISA/NEMU、原 O3 内核、默认模式和旧封存证据未改。没有 R4/R5 完成或人工 ACK；旧入口的 zjhwork 发布指示按历史任务阅读。
