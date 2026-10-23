# 香山 vdot 团队工程入口

本目录保存自定义向量点积的实现配套、测试、优化实验和交付证据。团队集成目标为 cc77-builder/riscv:zufan；各成员独立工作区并行开发，运行与发布按当前协作约定执行。

## 从这里开始

| 要了解什么 | 入口 |
| --- | --- |
| Agent 开发规则、验证及收尾要求 | [AGENTS.md](../AGENTS.md) |
| 当前基线、工程达标与持续优化的全部工作包、下一决策 | [当前开发路线](docs/development-route-current.md) |
| 谁在做什么、保护哪些运行、如何集成 | [协作约定与真实 Issue 状态](docs/collaboration-current.md) |
| 开发时间、GitHub 身份、成果和路线历史 | [开发计分板](../开发计分板.md) |
| 工具与依赖、可复现输入 | [环境](docs/environment.md)、[版本清单](versions.env)、[O2 复现入口](optimizations/o2/repro/README.md) |

## 按任务阅读

| 内容 | 工程／证据入口 |
| --- | --- |
| 指令语义、编码与未确认问题 | [vdot 规格](spec/vdot.md) |
| 模型、数据通路、FU 与接口 | [数学模型](models/vdot/README.md)、[算术 RTL](rtl/vdot/README.md)、[FU](rtl/vdot/FU.md)、[接口](spec/rtl-interface.md) |
| O2／H1 与固定对照 | [O2 导航](optimizations/o2/README.md)、[O1](optimizations/o1/README.md) |
| S2 筛选与 S1 设计 | [R2 导航](../R2_STATUS.md) |
| 全核、性能与成本 | [O2 全核](optimizations/o2/fullcore/README.md)、[公平周期](optimizations/o2/performance/README.md)、[GEMV](workloads/o3-gemv/README.md)、[O4](optimizations/o4/README.md) |
| 参数扩展与边界 | [参数合同](spec/t15-parameters.md)、[T15 结果](docs/t15-parameter-extension.md) |
| 阶段一、环境和脚本 | [阶段一记录](docs/stage1.md)、[脚本目录](scripts/) |
| 历史功能与性能结果 | [T10/T11](docs/t10-t11-acceptance-20261013.md)、[T12](docs/t12-regression.md)、[T13](docs/t13-performance.md)、[T14](docs/t14-optimization.md)、[统一比较](docs/unified-vdot-comparison-20261017.md) |
| 历史汇总和发布 | [2026-10-20 状态快照](docs/project-status-20261020.md)、[H1 发布记录](docs/o2-h1-publication-20261021.md)、[原入口归档](docs/history/entrypoints-before-consolidation-20261023.md) |

新机器先按实际任务选择基线和配置、恢复依赖并预检，不默认重跑旧阶段或复用来源不匹配的 EMU。代码进入仓库、单元通过、整核通过、独立成员复现和比赛提交是不同结果。这里只维护导航，新增进度写计分板，路线改变写当前路线，不再向本文件叠加“最新进度”。
