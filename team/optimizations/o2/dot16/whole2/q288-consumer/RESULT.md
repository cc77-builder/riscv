# whole2：同镜像完整 Q288 整核筛选结果

**状态：PASS（固定 Q288 整核调用）；选择 whole2 进入完整 first-forward。** 本轮接续既有候选源码，实际完成新 GNU 镜像、静态核验、preflight 和唯一一次目标运行。相对同镜像 plain dot16，whole2 两个窗口平均少 **15.7665% 周期（1.18718×）**；两种执行顺序均改善。相对同镜像 P，平均少 **35.2684% 周期（1.54484×）**。这些是本次固定 Q288 观察，完整应用、正式性能、退休窗口和 ASIC PPA 资格仍为 false。

合同：[CONTRACT.md](CONTRACT.md)，`r3-dot16-whole2-q288-v1`；完整身份与判断：[REFERENCE.json](REFERENCE.json)；原始证据：[evidence-v1/raw.zip](evidence-v1/raw.zip)。合同开头的 UNBUILT/暂停文字是冻结前状态，本页记录 2026-11-07 实际恢复后的结果，不改写原合同和输入。

## 做了什么，以及为什么有效

沿用已通过主机模型筛选的完整 `q288_dot16_whole2`：在 VLEN128 下，每组把 18 次 16B 供数改为 9 次 32B whole-register load，相关地址加法由 17 条减为 8 条，总读字节、严格 FP 次序和 `X += 32` 后缀保持。完整函数由 plain D 的 484B 变为 412B。这里优化的是既有 dot16 硬件上的软件供数方式；本轮没有改变 RTL、时钟、复位、FU 接口、流水时延、吞吐保证或官方程序。

以原 plain D 的实际 source/ELF 为基底，新镜像保留 P、D、FR 完整函数的逐字节身份，仅替换 slot1 为 W。沿用原构建命令与现有运行框架。新 [run.py](run.py) 通过 [run-derivation.json](run-derivation.json) 记录 12 项精确可逆替换，调整合同、镜像身份、臂调用数和满幅归属；进程控制、清理及行首协议解析逻辑保持。

## 实测结果

固定 M=K=288、GS32、VLEN128、lp64d；相同 ELF、数据、硬件、参考模型、CPU1、seed1。计时顺序为 FR/P/W/D/FR，随后 FR/D/W/P/FR，每窗前均保留同臂 warmup。保留全部窗口，不补入其他镜像的样本。

| 方法 | 两个窗口周期 | 窗口指令数 | 平均周期 |
| --- | --- | --- | ---: |
| P：paired16 RVV | 44,244 / 42,953 | 22,149 / 22,149 | 43,598.5 |
| W：whole2 dot16 | 28,374 / 28,070 | 21,101 / 21,101 | 28,222.0 |
| D：plain dot16 | 33,534 / 33,475 | 26,933 / 26,933 | 33,504.5 |

四个 FR 锚周期为 67,846 / 62,737 / 62,744 / 62,734，窗口指令数均 35,681。未丢弃较慢的首个锚。

- W 对 D 两种顺序分别减少 **15.3874% / 16.1464%** 周期，最高 W 28,374 仍低于最低 D 33,475；平均周期减少 **15.7665%**，指令数减少 **21.6537%**。
- W 对 P 的平均周期减少 **35.2684%**，对应 P/W **1.54484×**；指令数减少 **4.7316%**。
- 两窗是有限路线筛选，不构成大量重复或频率、功耗、统计稳定性证明。W/D 是同硬件软件优化收益；P/W 是当前候选硬件上 RVV 与 dot16 调用路径的组合比较，不能单独归因成纯硬件收益。

## 真实验证与运行闭合

2026-11-07 UTC，@LiZufan001 / Agent：

| 环节 | 实际结果 |
| --- | --- |
| GNU 构建 | 8 个子进程 exit0，已回收且进程组不存在；新 ELF/BIN 及四函数身份核验通过 |
| preflight | 81 项实际输入冻结；6M guest-cycle、7,200s 内层、两路日志各 64MiB，128MB RAM |
| 唯一目标 | 宿主 09:07:09.621318Z–09:28:15.938207Z，exit0、cleanup_complete=true，未超时／取消 |
| 功能与协议 | 29 次完整 Q、8,352 个输出、10 个计时窗；W 满幅 all−128、最终 slots、5 项判错控制和完整协议通过 |
| 整核 | 实际 DiffTest、指定 feature1 NEMU、GOOD TRAP，`DOT16_WHOLE2_Q288_FULLCORE_PASS` |
| 清理与身份 | EMU385 exit0、direct child reaped、process group absent；81 pins 未变，同 boot 读回 PID 已不存在 |

原始 guest 汇总为 instrCnt=991,760、cycleCnt=1,554,727；另一 guest-cycle-spent 字段为 1,554,731，保留各自口径。它们不是 Q288 性能表的分母。计划执行 W7+D6、每次 5,184 条 dot16 加一次 dot8 probe；本轮不将计划数量写成已核验退休计数。

目标操作：`49cbde030e5643f0cccfca5cec8a79c1.b04499267ed1ddca9f9fd554a06d5ee8`。资源保护已在 [RUN END 6705216516](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6705216516) 闭合，原 WORK 继续；完整 first-forward 的运行状态以其独立入口为准。

## 与当前报告指标的关系

本轮只读核对 `team/submission/latex-v1/sections/stage3.tex`（SHA `6b2bfc3d343b2b41639b9b3cee7db095bdc92d964205f551354a1546aae51dc3`）。报告区分加速比 `S=C_old/C_new` 与周期降低率 `R=(C_old-C_new)/C_old`。本页 1.54484× 和 35.2684% 来自同一组 Q288 P、W 样本，分别按上述公式计算；前者分母为 W，后者分母为 P，不能混称。

| 现有报告范围 | 已有数字 | 与本次结果的关系 |
| --- | --- | --- |
| batch128 点积微基准 | 3.0679× | 工作量与统计窗不同，不能用本次 1.54484× 替换或判断高低 |
| C8 普通调用，8×32 整数 GEMV | RVV 299 / C8 273 周期，1.095238× | Q288 是完整 FP32 输出调用，不能使用 299 作分母或相乘阶段收益 |
| 同 ELF FR/G/P 完整 forward | 22,244,288 / 19,996,570 / 17,382,632 周期 | 保留较快合格 P 路径；新四臂必须同新 ELF 重新测量，旧周期不能作 D/DQ 分母 |
| 实际 8 项 FU／父级综合、STA | 现有生产硬件成本 | 本次没有新 dot16 FU／父级成本，不能据 Q 周期推导频率或 ASIC PPA |

当前报告 dot16 段仍主要记录功能进展，本工程结果供人工后续取用，正式报告文件未修改。达到人工“10%以上改善”的筛选条件不等于官方评分资格或得分推算。

## 身份、原始证据与复现边界

- 新 ELF：`9f7978f3d4be2b8793d979c2e6b84636476fc3547bd7da17441e2076ca9ffde0`。
- 新 BIN：`ec900613377b8a023435a4eb88b9d3134e0da011675fc0dc4a45aae57d3149eb`。
- 完整 W 函数：`b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6`。
- profile：`c279366b5bb6f9a153714452209da7a7affdc29d3154a55b82bc6c3983032769`。
- 原始状态：`d43ef6de938a992bf349c2bf34c208b2a209fe9ebf213e43c1a473a72d3084ff`；checks：`8d095edf27981ae1a17d020cd31ddd07da875c9af74ec8cb9c138b59ab21b5e4`。

[evidence-v1/manifest.json](evidence-v1/manifest.json) 列出 70 份完整原运行文件，另含宿主回执和内嵌清单，共 72 个 ZIP 成员；原文件总计 9,180,763B，ZIP 3,768,978B，SHA `7f2d3f732c98a394318c1dd0eacf4f10e344bda1f10e97f44421121e09694d65`。归档逐成员 CRC/SHA、原件前后和 Windows 副本字节均核验通过，没有重跑 guest。EMU/NEMU/flash 等外部大依赖保留路径和 SHA 绑定，不能把这个证据 ZIP 当作已经完成干净机器独立复现。

## 决策与回退

W 正确且两种顺序均取得清楚优势，选择既有 whole2 完整函数进入 [P/PQ/D/DQ first-forward](../../first-forward/RESULT.md)，检验局部收益在包含量化与完整状态比较的应用中的实际传递。比较使用新共同镜像的较快合格 RVV 臂，软件、dot16 路径和组合收益分别报告。这里不再追加微优化或为填充样本重复此案。

旧 plain D、RVV、所有冻结／失败证据保持，可回退为不选择新独立镜像；稳定默认入口未切换，无部署。发布状态以 Git 与协调 Issue 为准。
