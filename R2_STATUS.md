# R2 应用内核开发入口

当前待办与采用状态统一见[开发路线中的 R2 工作包](team/docs/development-route-current.md)。完成或暂停工作后更新[开发计分板](开发计分板.md)，并按[协作约定](team/docs/collaboration-current.md)结束本轮操作记录。

| 已有材料 | 内容与边界 |
| --- | --- |
| [原内核审查](team/optimizations/o2/r2-kernel-audit/README.md) | 既有复用、交错、展开及搬运／累加分析，避免重复已有优化 |
| [S2 安全尾部](team/optimizations/o2/r2-safe-tail/README.md) | 已入库候选及历史主机检查；117→83 是静态指令数，不是周期提升 |
| [S2 构建／全核筛选](team/optimizations/o2/r2-safe-tail/FULLCORE_VALIDATION.md) | 26 ELF、4 冒烟＋48 正式＋8 重放；2026-10-21 记录停在环境预检，不是新机器现状 |
| [S2 合并版实测](team/optimizations/o2/r2-safe-tail/MERGED_RESULT.md) | 新单硬件合同：26 ELF、31 次真实运行和384正式窗口通过；4×13 reuse/endtoend 周期少10.621%，basic退化；限定reuse进入R2-SELECT，原B0/H1仍BLOCKED |
| [S1 寄存器与 RVV 对等方案](team/optimizations/o2/r2-safe-tail/S1_REGISTER_REVIEW.md) | 设计审查，实施与实测按当前工作包推进 |

团队集成目标为 zufan。原任务中的 zjhwork2 写入限制已结束其适用范围，不应据此切换当前工作或推送；固定旧构建、输入与测量合同仍按原身份保存。当前筛选必须核对真实环境，不能以主机测试代替 ELF/DiffTest/周期结果。详细历史状态保留在各结果文件，本入口不累积逐日进度。
