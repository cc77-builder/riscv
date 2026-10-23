# O2 原技术计划与当前执行入口

当前工程工作包、默认顺序、前置条件、实验决策和组合验证统一维护于[当前开发路线](../../docs/development-route-current.md)。本文件仅保留旧链接的兼容入口，不再维护另一套“下一步”。

2026-10-20 原计划及其后追加的历史进度完整保存在[整理前正文](../../docs/history/entrypoints-before-consolidation-20261023.md#original-o2-plan)。其中数学位宽分析、公平硬件／软件矩阵、验证阶梯和停止依据可作为设计参考；原三人分工、排期、zjhwork 发布目标及已完成 R0/R1 的“下一步”不再指导当前执行。

| 当前技术任务 | 应读合同／入口 |
| --- | --- |
| 输入来源与新机器预检 | [R0](repro/README.md) |
| H1 语义与成本取舍 | [H1 合同](result-width/h1/CONTRACT.md)、[结果](result-width/h1/H1_RESULT.md) |
| S2 真实构建／筛选 | [S2 运行合同](r2-safe-tail/FULLCORE_VALIDATION.md) |
| S1 累加及对等 RVV | [寄存器审查](r2-safe-tail/S1_REGISTER_REVIEW.md) |
| 完整应用选择 | [O3 合同](../../workloads/o3-gemv/CONTRACT.md) |
| R3 两槽／观测边界及成本 | [O2 合同](CONTRACT.md)、[O4](../o4/README.md) |
| 每轮结果和路线调整记录 | [开发计分板](../../../开发计分板.md) |

不因归档而放宽旧实验合同或重写结果；新候选使用明确的新身份和相应验证。原计划中的百分比、输入锁和固定硬件只适用于各自实验，不作为所有新实验的统一门槛。
