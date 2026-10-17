# Redoop 公共 RVV 基线周期差异审计

记录时间：2026-10-17T17:00:28.095812+08:00。本次仅只读检查既有 ELF、硬件退役日志和封存源码，没有重新运行仿真、构建或改动原数据。

## 已核实事实

核对范围：dataset 0 的 single（performance-d0-s00）与 batch4×32（performance-d0-s02），四个项目各 6 轮。所有对应 check.json 均为 PASS。

- 四项目 RVV 完整函数 `t13_kernel_1` 的地址、长度及 ELF 机器码字节完全相同。
- 四项目从硬件 `T13_RETIRE` 记录提取的实际 `(PC, instruction word, count)` 序列逐项完全相同，包括所有六轮、START/STOP 标记和循环路径。未只依赖源码、静态指令计数或软件打印。
- single 的 instret 窗口计数全部为 16；START 至 STOP 共 21 条退役记录。
- batch 的 instret 窗口计数全部为 552；START 至 STOP 共 557 条退役记录。
- 因此这两项分母差异不能归因于公共 RVV 基线少执行/多执行了指令、换了机器码或走了不同的已退役路径。

## 原始 RVV 各轮 cycles

第 0 轮为 first，第 1 轮为 warmup，第 2–5 轮为正式 measured；不应选取最低轮替换统一统计。

| 场景 | 项目 | first | warmup | measured 2 | measured 3 | measured 4 | measured 5 | measured 均值 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| single | ours | 86 | 85 | 85 | 85 | 86 | 85 | 85.25 |
| single | jade | 86 | 85 | 85 | 85 | 86 | 85 | 85.25 |
| single | shishui | 86 | 85 | 85 | 85 | 86 | 85 | 85.25 |
| single | redoop | 85 | 85 | 86 | 86 | 86 | 86 | 86.0 |
| batch | ours | 712 | 695 | 678 | 678 | 678 | 678 | 678.0 |
| batch | jade | 712 | 695 | 678 | 678 | 678 | 678 | 678.0 |
| batch | shishui | 712 | 696 | 678 | 678 | 678 | 678 | 678.0 |
| batch | redoop | 713 | 741 | 695 | 700 | 695 | 678 | 692.0 |

single：Redoop 86 vs 其余 85.25，差异约 +0.880%；batch：692 vs 678，差异约 +2.065%。Redoop batch 的最后一轮也测得 678，不能由本组证据断言其公共 RVV 有固定的 14 周期额外延迟。

## 字节与退役序列证据

| 场景 | RVV 函数地址 | 字节数 | ELF 函数 SHA256 |
|---|---|---:|---|
| single | `0x80002000` | 732 | `0c691f834e4217e57fa05ed1f9f8cc1e5aba0743d004f7136d1eea65f2f045d8` |
| batch | `0x80002000` | 768 | `74bdeec3b1e577dbd2c9767c0cb9326b9b1c842cc211873deeb753e2a8f7b901` |

实际退役序列 SHA256 对 `(pc,word,count)` 数值列表执行默认 Python `json.dumps` 后求 SHA256；完整 hash、每轮计数、原始证据路径和文件 hash 见同目录 `redoop-rvv-cycle-audit.json`。证据输入均为 `runs/<variant>-images-02/performance-d0-s00或s02/vdot-perf.elf` 及 `runs/<variant>-suite-02/performance/performance-d0-s00或s02-r0/{stderr.log,check.json}`。

## 源码核对

Redoop 的接口增量是新增 VdotCfg/FuType 并挂入 VFEX0，复用现有三个向量源读口、V0/VL 读口及向量写回口；VdotCfg 为 CertainLatency(2)、piped=true。移植没有更改原 VimacCfg 的延迟或读写口，也没有改现有 RVV 指令的解码条目。VIMacU.scala、VIMac64b.scala、ExeUnit.scala、ExeUnitParams.scala 与统一上游字节相同。Parameters.scala 的增量仅是 VFEX0 增加该 FU，未引入公开补丁文件中的无关缓存/处理器配置差异。

没有发现“为了移植而给公共 RVV 路径增加固定流水级、降低端口数或改指令序列”的代码证据。新增 FU 的集成确实改变了硬件实例组成，但当前证据不足以把这约 2% 差异归因为某个 FU 仲裁或唤醒变化。

## 未确定的根因与报告限制

根因尚未确定。以下仅为可能性，不能作为已证实解释：交替运行不同长度/不同分支位置的 custom 内核后，分支预测、前端、资源分配等微架构状态可能不同；统一 fence 保证计时窗口顺序，但并不清空分支预测器和缓存，也不把全部微架构状态重置成同一状态。不同 custom 路径、不同 FU 组成及其状态影响仍需独立实验才能分离。

实际退役日志可见 Redoop 某些 batch 轮的退役间隔不同，但现有观察点不能把间隔归因到某个确定的取指、预测或发射事件。不能把它笼统说成“主机负载波动”：这里报告的是模拟处理器 cycles，而非主机用时。

报告应保留各变体配对实测的原始 RVV 分母，分别列出 custom cycles、RVV cycles、加速比及分母偏差。不得把 Redoop 的分母人工换成其他项目的 678；也不应将未解释的小幅差异包装成已验证的硬件优势或缺陷。
