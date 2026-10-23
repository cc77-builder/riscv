# O2 两槽弹性 FU 工程入口

O2 的实现、接口合同和固定版本证据从这里查阅。当前基线、采用状态及下一工作包见[开发路线](../../docs/development-route-current.md)，每轮成果见[开发计分板](../../../开发计分板.md)，并行范围见[协作入口](../../docs/collaboration-current.md)。

| 内容 | 入口 |
| --- | --- |
| 两槽行为、身份、反压／取消及父级接口 | [设计合同](CONTRACT.md)、[接口审查](INTERFACE_REVIEW.md) |
| 实现与真实父级验证 | [实现说明](IMPLEMENTATION.md)、[实现审查](IMPLEMENTATION_REVIEW.md) |
| 原因分析与优化设计参考 | [轨迹分析](TRACE_ANALYSIS.md)、[原计划索引](NEXT_OPTIMIZATION_PLAN.md) |
| 固定 B0 输入和机器配置 | [R0 复现入口](repro/README.md) |
| 全核功能、控制和故障拒错 | [运行入口](fullcore/README.md)、[复现](fullcore/REPRODUCE.md)、[日志合同](fullcore/SCHEMA.md) |
| O1/O2 公平周期 | [性能入口](performance/README.md)、[测量合同](performance/CONTRACT.md) |
| H1 低 32 位保存 | [合同](result-width/h1/CONTRACT.md)、[局部成本结果](result-width/h1/H1_RESULT.md) |
| H1 全核与 B0/H1 周期 | [全核结果](result-width/h1/fullcore/H1_FULLCORE_RESULT.md)、[周期结果](result-width/h1/performance/B0_H1_RESULT.md) |
| S2 安全尾部及 S1 设计 | [候选](r2-safe-tail/README.md)、[严格筛选](r2-safe-tail/FULLCORE_VALIDATION.md)、[S1 审查](r2-safe-tail/S1_REGISTER_REVIEW.md) |
| 应用与面积／时序 | [GEMV](../../workloads/o3-gemv/README.md)、[O4](../o4/README.md) |
| 整理前逐轮状态 | [历史正文](../../docs/history/entrypoints-before-consolidation-20261023.md#original-o2-readme) |

历史证据证明其固定版本，不能自动视为当前合并版验收。运行前检查对应硬件模式、trace、NEMU、镜像和来源；设置变量不会改变旧 EMU。旧 README 中的当次授权、分支和“正在运行”说明已归档，不是新任务指令。
