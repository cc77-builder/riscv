# 香山 vdot：文献驱动的方案评审与并行实施建议

评审日期：2026-10-12（北京时间）。作者：ChatGPT，按 Zufan 的请求进行研究与审查。本文是建议，不代表命题方确认、三人签字或已完成的硬件验收。

## 结论先行

**保留现有精确 8 路 int8 乘法＋平衡归约树，以现有向量后端完成紧耦合集成；把主要精力从重复编写模型/长篇计划，转到全核闭环、更强 RVV 基线和有时序证据的优化。** 当前不能声称任何方案已达到最佳 PPA，也没有可报告的香山周期加速比。

这不是推倒重来。James_Hotten 分支已经有独立硬件模块、NEMU 扩展、异常 workload 和 RVV 基线；zjhwork 分支已有另一套独立数学模型。两者都值得保留和复用。真正尚未关闭的是全核译码/依赖/写回接入、真实 DiffTest、对称性能测量和综合时序。来源、版本和已完成/未完成边界见 [证据审计](01-evidence-audit.md)。

优先改进如下：

| 优先级 | 建议 | 为什么现在做 |
| --- | --- | --- |
| P0 | 处理赛题语义 Q01～Q04；把内部候选合同和官方要求分开 | “第一个元素”宽度、低 8 项、精确求和及受限合法域尚无归档官方答复；避免优化了错误目标 |
| P0 | 约定一个集成负责人，先让一条 vdot 在全核正确退休，再扩大回归 | 现有分支的单元/NEMU 通过不等于已经进入处理器；这是当前关键路径 |
| P1 | 在原 13 条 RVV 序列之外验证 B6/B7 更强基线 | 本次提出 6 条/7 条完整合法域等价候选，减少不必要配置和搬运；防止用偏慢基线夸大收益 |
| P1 | 并行做单元时序探索、全核适配、独立测试与软件微内核 | 不必等全核全部完成才研究 PPA，也不必三人串行等待 |
| P1 | 从只比单条指令，扩大到短点积、长点积及小型 GEMV/GEMM | 确认收益没有被配置切换、归约、加载和写回吞掉 |
| P2 | 仅在测得瓶颈后引入 CSA、更深流水或额外精度 | 先量化收益与代价，不为了“创新”重写成熟部件 |

## 本次最具体的技术产出

在当前 `vdot-s8x8-r32-v0.1` **受限合法域**下，提出 B6：

```asm
# 入口 VLEN=128, e8/m1, vl=8, vstart=0, VS 非 Off。
# 输入 v8/v9，输出 v10；允许破坏 v2/v3、t3/t4。
csrr       t4, vtype
vwmul.vv   v2, v9, v8
vsetivli   t3, 8, e16, m1, tu, mu
vmv.v.i    v10, 0
vwredsum.vs v10, v2, v10
vsetvl     zero, t3, t4
```

关键是：八个 16 位乘积恰好占一个 128 位寄存器；先消费输入，再把目的整寄存器清零并用它兼任零 seed；最后恢复入口策略位和 vl。完整论证、别名约束以及多一条配置但只用一个向量 scratch 的 B7 见 [实现方案](02-architecture-and-baselines.md)。**6 条不是已经证明的周期数，也不是全局最短序列定理。** B6/B7 均未在本次运行 QEMU、NEMU 或香山 RTL，必须进入现有 T09 框架验收后才能成为正式基线。

## 本次确实执行的检查

结果保存在 [candidate-check.json](evidence/candidate-check.json)，程序在 [check_candidates.py](experiments/check_candidates.py)。

- 对全部 `32³ = 32,768` 个目的/源寄存器编号组合检查 scratch 分配和同一真实寄存器快照中的别名关系；每组一个随机寄存器状态，覆盖四种策略与两种尾部处理设置。B6/B7 各完成 262,144 次手写操作级模型检查，另有各 4 组极值。
- 用 Clang 17 的 RISC-V 汇编器为每种候选分别汇编全部 32,768 个寄存器组合，确认核心区分别为 6/7 条 32 位指令。保存代码段摘要；代表性 B6 的 [反汇编](evidence/baseline6-disassembly.txt) 单独可查。
- 给出 16 位累加溢出、错误的 128 位符号扩展、策略恢复丢失、e8 下标量取数截断这四类错误的数值反例。这是反例检查，不是 RTL 故障注入。

以上检查证明候选值得进入目标平台验证，**不证明真实 CSR/异常行为、译码微操作数、目标时序、功耗或应用加速**。操作级模型不是完整 ISA 仿真器，也不是团队第三套正式 golden model。寄存器组合穷举不等于源数据位模式穷举。

复现（Python 3.10+；汇编检查另需支持 RVV 的 Clang）：

```bash
python3 team/research/2026-10-12-vdot-review/experiments/check_candidates.py \
  --assemble --output team/out/review-baseline-candidates.json
```

## 阅读顺序与交付内容

| 文件 | 用途 |
| --- | --- |
| [01-evidence-audit.md](01-evidence-audit.md) | 官方与内部要求、分支状态、现有方案优点、需要改进及尚缺证据 |
| [SOURCES.md](SOURCES.md) | 原始论文/规范/源码入口、阅读范围、可迁移方法和不能照搬之处 |
| [02-architecture-and-baselines.md](02-architecture-and-baselines.md) | RTL 方案比较、B6/B7 推导、软件展开与数据复用、选择路线的条件 |
| [03-parallel-plan.md](03-parallel-plan.md) | 三条并行工作流、可认领工作包、文件边界、依赖、验收与 Codex 任务单 |
| [04-metrics-and-verification.md](04-metrics-and-verification.md) | 正确性、延迟/吞吐/端到端、PPA、负控、实验记录与真实验收 |
| [experiments/baseline6.S](experiments/baseline6.S) | 可汇编的代表性 B6，不是可直接替代全部 harness 的生产实现 |
| [evidence/candidate-check.json](evidence/candidate-check.json) | 本次 host/汇编实测结果，含程序、输入语料和机器码摘要 |

## 审查基线与使用边界

本次审查固定以下 Git 快照，而非笼统的“最新代码”：

```text
main / zufan : c1ef31d81d50c209bf0e102af8ad7713c2da6dab
James_Hotten : a978b3b8fe731dd9422a41f80d9d53e40c775656
zjhwork      : 720dd3d668929123b8ab35e947c67f68ef595c65
XiangShan 硬件基线 : 16ae9ddcda54fc9a2fddffad73174cf793ac7814
```

赛题官网正文本次未成功重新抓取；三阶段细节和评分暂依仓库已保存的转录，不能说已再次核实全部官方条款。命题方仓库的题目与提交指南已读取，其中公有/私有作品仓库说明存在冲突，详见审计。论文结果只用于选方法，不转化为本项目已实现的指标。

本目录只新增研究材料和隔离的 host 探针；不修改既有 RTL、规格、计划、分支合并关系或正式 golden model。保存目标是个人 Fork 的 `zufan`；本次不向团队主仓库 Push，不公开私有代码，不执行正式作品提交。后续团队采纳哪些建议、A/B/C 如何对应姓名、综合工艺/时钟/资源预算，都需按实际项目情况确认。
