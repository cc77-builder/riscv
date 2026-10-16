# T13 周期测量约定 v1

适用对象：固定 MinimalConfig、单核、VL=8、SEW=8、LMUL=1、VLEN=128，`vdot-s8x8-r32-v0.1`。本文规定测量方法，实际完成状态以 T13 报告和运行回执为准。

## 1. 两条路径必须计算同一结果

低 8 个 signed int8 元素分别相乘，在足够宽的有符号整数中求和；目的向量低 32 位存二补码结果，高 96 位清零。检查完整 128 位，不用截断标量或摘要替代。`vdot` 不修改其他向量寄存器；RVV 只允许破坏事先声明的 scratch。

复用来源为 `zufan@f090665130107282be0990a7664aebf26e491b87`。原文件与 SHA-256 位于 `team/references/zufan-t13/`，本轮重新构建和运行，不继承对方的 PASS 为本轮验收结果。

| RVV 路径 | 点积主体指令数 | 向量 scratch | 入口与出口 |
|---|---:|---|---|
| 已知配置单次 | 5 | v2、v3 | e8/m1/VL8、tu/mu；退出恢复相同配置 |
| 通用配置单次 | 7 | v2、v3，另用 t3/t4 保存 CSR | 保留原 VL/vtype，测试四种 tail/mask policy |
| 独立四路批处理 | 14 / 4 个点积 | v16–v23 | e8/m1/VL8、tu/mu；退出恢复相同配置 |

已知配置序列：`vwmul.vv` → 设置 e16/m1/VL8 → `vmv.v.i vd,0` → `vwredsum.vs` → 恢复 e8/m1/VL8。e16 下 8 个元素正好清零整个目的寄存器；宽化归约使用 tu，保留已经清零的高位。必须先乘后清目的寄存器，以支持源/目的别名。通用序列增加 `csrr vl/vtype`，末尾用 `vsetvl` 恢复。四路批处理共享两次 vtype 设置，不人为放大基线开销。

每次调用保存并比较全部 32 个向量寄存器，按声明排除 RVV scratch；检查 VL、vtype、vstart、vxrm、vxsat、vcsr、实际循环次数以及缓冲区前后 canary。访存组逐个比较全部 128 位输出，并检查未使用输出空间。C 判定器使用真实源文件进行原生及 UBSan 位翻转测试。

## 2. 为什么不能直接使用一对 rdcycle

`DecodeUnit.scala` 的普通 CSR 表带 waitForward/blockBackward；但 `Rename.scala` 282–299 行会解除大部分只读 CSR 的这些限制。本轮初始观测确实看到 cycle/instret 在 ROB 未清空时进入，标志为零。因此不能由解码表单独推导 rdcycle 串行化，更不能把旧无校准窗口当作指令延迟。

本轮在**软件测量边界**加入 `fence rw,rw`，不改变生产核执行规则。该固定版本的 fence 使用等待旧指令、阻止后续分派和 flush 的实现，作用必须通过实际日志确认。这是针对固定香山实现的实验方法，不是声称 RISC-V ISA 的普通内存 fence 在任意处理器上都能序列化计算和 CSR。

窗口结构如下（所有实验分支相同）：

```text
fence; START; fence
read instret_begin; fence
read cycle_begin; fence
执行显式汇编主体（含循环控制）
fence; read cycle_end; fence
read instret_end; fence
STOP; fence
保存结果；完整状态检查；打印
```

观察器以编译开关 `VDOT_T13_TRACE=1` 启用，仅打印 CSR 实际采样、计数器入 ROB 和窗口内退休信息。与 T12 观察器一起构建，不改数据通路、频率、复位、忙闲接口或 NEMU 计时。硬件源码提交为 `4460300e9557ad20ac152fa67b1827c5d62802dd`；工作负载另列实际构建提交，不能用后来的文档提交冒充重新构建。

每个窗口必须同时满足：

1. 精确匹配四条计数器指令的 PC、机器码、ROB 身份与顺序。
2. CSR 读值与对应退休写回数据相等，采样位于入队和退休之间。
3. 每条计数器的前一 fence 已退休，后一 fence 在计数器退休后才退休。
4. cycle 差值等于硬件全核采样 tick 差值。
5. instret 差值等于真实退休计数，也等于从 ELF 机器码展开有限循环得到的指令数。
6. 完整窗口及 UART 记录数量、顺序与 manifest 一致；真实 exit0、DiffTest 启用、完整成功 summary 后 GOOD TRAP。

绝对计数器可能大于 2^53，所有解析与差值计算使用 Python 整数。禁止经过 JavaScript Number 或浮点再保存绝对值。FU 自身时钟存在门控，使用已验收 T12 的 parent VFEX4 accept 逐事务归一化，不能直接拿 FU 局部 tick 减 ROB tick。

空窗口、8 条整数指令、32 条依赖除法用于校准。**不从测量结果直接减掉空窗口开销**；小样本的屏障、取指和循环开销占比必须说明。

## 3. 工作负载矩阵

| 场景 | n | 点积数 | 含义 |
|---|---|---:|---|
| single | 1 | 1 | 已知配置完整调用窗口 |
| chain | 16、64、256 | n | 目的向量作为下一次源，观察依赖限制 |
| batch | 1、8、32 | 4n | 每轮四个独立目的，比较共享配置的 RVV 批处理 |
| stream | 1、16、64 | n | 两个 128 位加载、点积、128 位存储以及指针更新 |
| generic | 1、16、64 | n | 原 vtype=192 的 CSR 保留对照 |

链式实验的反馈值是上一结果的完整向量表示，后续数值可能收敛到零。它用于固定依赖关系的微基准，不代表真实模型的数值分布。批处理四个目的独立且共享输入，用于消除人为增加的配置开销；不将其宣传为任意矩阵乘法性能。

三组输入包括正极值、负极值和混合符号；高半区设置非零哨兵，访存组加入固定种子的随机数据。功能矩阵使用原始 22 组定向和前 32 组随机数据，轮换七种别名与四种 policy；这 54 对不是全部笛卡尔积。另用固定 NEMU 对全部 10,022 组数据重新检查精简基线，明确与全核执行层分开计数。

每个配置同一镜像内运行 6 轮配对：首次样本、预热、4 轮正式样本；顺序按 AB/BA 交替。首次不是人为清空缓存后的“冷缓存”；预热也不保证全部微架构状态完全相同。每种配置单独分片，两个实现的入口均 64 字节对齐；代码长度、地址和寄存器压力的自然差异保留并记录。

每个性能镜像以固定 seed=1 在全新 EMU 中运行三次。重放比较同一镜像、同一 seq 的周期和退休指令数；用于确定性复核，不作为独立统计样本，不给 p 值或统计显著性。宿主允许 8 个进程并行；每个 DUT 仍是同一个单核、EMU_THREADS=1 配置。宿主秒数仅用于安排任务，不参与加速比。

## 4. 汇总与结论边界

保留全部首次、预热、正式窗口。逐配置、逐数据集报告原始周期、周期/点积、指令数、正式样本 min/median/max；配对加速比为 `RVV cycles / vdot cycles`，减少比例为 `1 - vdot / RVV`。不以最优个例冒充总体，不在不同场景、不同 n 或不同数据集之间错配。若 vdot 变慢，照实记录。

报告层次区分：局部 FU accept→response；完整序列的窗口；独立批处理的点积吞吐；包含加载/存储的循环。FU 局部 E3/II4 不是全核指令周期。端到端窗口含相同的隔离与循环开销，不等同于纯算术单元延迟。

本轮不推断 Fmax、面积、功耗、PPA、实际 LLM 加速或官方比赛得分。没有 STA/综合结果，不把周期减少转换成频率提升。正式规范及队友人工复核仍按团队流程处理。

## 5. 可复现入口

```bash
# 完整香山仓库中，使用现有 Ubuntu/WSL 工具链
python3 -B -m unittest discover -s team/workloads/vdot-perf -p 'test_*.py' -v
python3 -B team/workloads/vdot-perf/host_judge.py --output /新目录/host
python3 -B team/workloads/vdot-perf/reference.py --reference /固定NEMU.so --output /新目录/reference
python3 -B team/workloads/vdot-perf/campaign.py build --am /独立nexus-am --output /新目录/images
python3 -B team/workloads/vdot-perf/campaign.py run --images /新目录/images --emu /固定emu --reference /固定NEMU.so --flash /固定flash --output /新目录/runs --jobs 8
python3 -B team/workloads/vdot-perf/check.py --build /具体image目录 --run /具体run目录 --output /新文件/check.json
```

所有重跑使用新目录；不覆盖旧失败证据，不改黄金输入，不用 `--no-diff`。原始 stdout/stderr 分开保存并计算摘要。来源 T13 已交付至 zjhwork@3b337a5；2026-10-16 的 James 合并与修复仅在本地，未推送远端。当前构建、完整回执和来源门禁见 [工具说明](../workloads/vdot-perf/README.md)。

## T09 历史基线与当前 T13 的关系

原 T09 使用13条完整序列和4个scratch，完整合同保存在[历史快照](../docs/history/measurement-james-before-t13-20261016.md)。其独立模型/状态检查继续有效，但本T13比较采用上文5/7/14条精简序列及各自显式scratch；不能混用指令数、排除寄存器或时序结果。原有全128位、非scratch保持、CSR恢复、异常另验要求继续适用。
