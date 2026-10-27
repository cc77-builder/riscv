# 纯 forward、组合验证与有界目标成本结果

工程轮次：`20261027-LiZufan001-forward-consumer-0900`。基点 `7b358d98c95dacf1897fe9169b1f16d6f0ae76d9`；实际起点 2026-10-27 09:00:51 UTC+08，交付时间见本次计分板及发布回执。认领 [Issue #2 / WORK 6431143260](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6431143260)。

**本轮交付固定模型的纯计算消费者，完成强 FR/TA 与 RoPE-cache 的组合参考验证，并把真实 O2 日志审计改为有界内存。完整香山 forward 和应用性能仍未合格。** 本轮无 RTL、官方程序、原参考或判定标准修改。

## 1. 实际工程变化

前序阶段镜像含逐矩阵重算、快照及比较，不适合作为完整应用计时入口。本轮提取独立 `consumer.o`，包含原 scalar、FR、TA、FR+cache、TA+cache 五条完整前向路径。四份派生函数的路由与 cache 转换均可机械反向恢复到原 forward 文本；完整原样 `runq.c` SHA256 为 `ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548`。

核心对象没有 CSR/计时、oracle、阶段标记、快照、比较或应用负例接口。验证与目标包装直接链接同一核心对象，强 FR 的 592 B、TA 的 764 B 完整函数字节仍与前序合格 ELF 相同。37 张 K288 矩阵经 172 个 Q 调用及 13 个尾块进入这些内核；六张 K768 W2 保留原 FP32 scalar 左折叠。每次调用内准备并复用 24 对 RoPE 角度，逻辑表容量 192 B。

固定输入为未训练 D288/H768/L6/HQ6/HKV6/V32000/S256/GS32 fixture；权重预打包在调用前完成，完整 forward 的绑定、cache 准备、量化、所有投影与余下 Transformer 数学在函数内部。冷模型加载、离线 packing 及其摊销没有计入本次调用资格。

| 最终实物 | SHA256 |
|---|---|
| `consumer.c` | `f1d944367614fda5df4317355315b456afc8ff3ff53779ff021fb87d04940d4c` |
| build-02 `consumer.o` | `a1c036656a8f305183c0aa4bd2d1fd30fba2014b26465429ffb2ab77ef2a3193` |
| build-02 ELF | `cf35f16ad7b7ec0e3fb7ab3b36b7acdf8a9cb2b7cf7a55acce89e2a21c86ef74` |
| build-02 BIN | `7f41e6c5b12fbd98e031147e5bbd2c865d517ed0872f7082d0c3c293bcb91828` |
| target-build-02 ELF | `7648697e99e1058e981708395fc16b82275461a17a0d918bdcbf76ea860fe073` |
| target-build-02 BIN（控制字改变前） | `a005fd797a6f76cdab22533eb036018817581f3381eb0034dfbba26306fd48f8` |
| 增量 O2 核心 | `3f72629ea0ccc30779883f9e696e21c4d92d33aa2406b67df02ab2212d9382cf` |
| 原 O2 checker（保持原样） | `27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496` |

build-01 与 build-02 的 BIN 完全相同；路径/调试身份使 ELF 和对象 SHA 不同。新参考批次仍重新绑定到最终 build-02，未把旧 PASS 直接转授新候选。

## 2. 完整参考、负例与接口验证

| 层级与实际运行 | 结果及范围 |
|---|---|
| `reference-01`、最终 `reference-02` | 每批八个独立实际参考进程：负例、五方法、恢复、重放。五方法均自然执行 `[1,7,19]`、p0..2，每次全部 3,691,424 B 状态逐字节等于独立原 host gold，包括 32,000 logits、完整 KV 和 scratch。模型、packed、tail scales 全字节保持。 |
| 真实应用负例 | p0 后翻转实际最后一个 logit 的 bit0；正常完整状态比较器精确拒绝 byte152476，返回 code94，未执行的快照仍全零。恢复和独立重放恢复全部原值/flags。 |
| `process-controls-01` | 真实 SIGKILL 启动器时，独立会话子进程仍存活；新运行器保留 cleanup-unknown。控制测试随后清理并 reap 自己的全部子进程。 |
| `api-reference-01` | 同一只读模型下，A=TA+cache 与 B=FR+cache 顺序交错，单独 reset B；六对完整快照及全部 guard 正确。十个 forward 拒绝、两次失败 init 清绑定和三次成功 init 均完成。 |
| `target-reference-01` | 同一核心对象的目标包装执行负例→FR+cache→TA+cache→独立 TA 重放；完整状态与模型正确，实际词比较器拒绝同一个最后 logit 位翻转。 |

普通参考 BIN 为 94,241,416 B；目标包装 BIN 为 75,779,320 B。API 双状态镜像为 120,072,080 B。大小、链接地址、TLS、原 AM/klib/libm、完整内核字节和所有数据控制位置均在实际 ELF 上核验。

目标包装的独立参考观察到 FR+cache/TA+cache 调用窗口分别退休 17,356,358 / 19,752,662 条指令。这些数字仅作为原 NEMU 的运行观察和预算输入；**它们不是香山周期，也不能据此选择较快硬件路径。**

## 3. 真实目标成本探测

`target-probe-01` 使用原 T17 EMU `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`、原正常 NEMU `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` 和原 flash。TA+cache、p0/token1、无预热，单 CPU0、seed1、128 MB RAM，预定 300,000 guest cycles / 1,200 s / 每日志 128 MiB 上限。

实际记录明确出现原 DiffTest enabled；`--log-end=0` 的源码检查和实际日志共同证明它没有抑制裸 O2/T13，也未关闭 DiffTest/UART。程序在预定 cycle limit 停止：

| 观察 | 实际值 |
|---|---:|
| `cycleCnt` | 300,000 |
| `instrCnt` | 164,815 |
| EMU 报告 guest cycles | 300,004 |
| 包装器单调时钟耗时 | 222.343692 s |
| EMU 自报 host time | 230,792 ms |
| stderr 原始字节 | 56,601,062 |
| stdout 原始字节 | 1,236 |
| 子进程峰值 RSS | 366,756 KiB |

两种主机耗时来自不同观察边界，分别保存。程序没有 `CONSUMER_PASS` 或 GOOD TRAP。`probe-audit-01` 实际复核 29,344 笔完整 custom transaction，末尾另有 5 个未完成 ROB 分配；所有旧 partial 摘要和规范 transaction SHA 一致，原 complete checker 明确拒绝 `unfinished ROB allocations`。两条起始 CSR 的实际 ELF/入队/采样/退休链一致，结束读数尚未出现，完整窗口数为 0。前缀速率不外推完整耗时或 token/s，也不视为功能失败。

**路线决定：本轮不直接展开多次完整长时目标重放。** 该前缀已经显示完整链路的仿真和日志成本较高，而赛题既有应用指标与本模块完整 LLM 性能资格是不同层级。先交付可调用的纯消费者和可复查证据，降低日志审计成本；下一次完整目标实验应有明确的问题、完整计数器/状态验收、强 FR 同缓存政策与足够运行预算。局部历史收益不迁移或串乘。

## 4. 增量日志审计资格

原 checker 保持原字节。新工具复用其严格字段解析、ROB 年龄关系、full128 算术 oracle 和覆盖计算；逐周期执行同一套协议状态判断，保存最多 96 个 ROB 键及待按序输出的事务。完整日志字节不删减；新记录增加 transaction 数量与规范 JSON SHA、实际存储高水位。

最终 `check_stream.py` 完成原 29 项定向测试、45 次接受和 55 次拒绝的结果对照、30 个分片输入案例、跨文件换行、UART 插入及非 ASCII 残留。另覆盖同 ROB 键取消后复用、较老 R 停顿时四笔有序积压、最终 redirect 截断与中途漏拍拒绝。保存结果 JSON 检查器通过 11 个合法边界输入和 12 个损坏/重复/截断拒绝。

最终 `recheck_stream.py` 为 `13503f8132dd84ceed347fd22c3cc06e81e06020546ce60e6fbd81ddcbbcc56f`。实际重新读取旧冻结正/负例原日志，逐笔比较保存的原 transaction，比较全部旧摘要、每个有序提交 PC、T13 counter 链和应用 `TILE_` transcript，并核对原 receipt 内全部被复用的旧辅助代码/ELF 身份：

| 原日志 | transaction/提交数 | 最终复查耗时 | 峰值 RSS |
|---|---:|---:|---:|
| 正例 `normal` | 207,360 | 35.542063 s | 36,176 KiB（35.33 MiB） |
| 真实应用负例 `bad-tail` | 41,472 | 7.502150 s | 36,000 KiB（35.16 MiB） |

上述为本次审计工具成本，不是硬件性能。正例 stderr 为 408,925,813 B。全部原始字节 SHA 与旧运行回执一致；旧 `protocol.json` 本身没有历史单独 SHA，因此这里证明的是本次读取的保存结果与原始日志重新计算完全等价，不额外声称那份 JSON 的历史字节身份。完整 UART 残留并无旧单独产物；逐项等同的是应用 transcript。

资源限制写在 [STREAM-CONTRACT](STREAM-CONTRACT.md)：单物理行、单周期事件数、残留文本、T13 条数及完成积压均显式有界，超限拒绝。未来完整 forward 日志尚未通过这些上限资格；`full_retirement_window_audited` 仍为 false。

## 5. 证据、恢复及失败保留

详见 [evidence/index.json](evidence/index.json)。核心包使用既有内容寻址 ZIP 去重，保留两轮完整构建/参考、API/目标包装、实际成本探测和失败输入：1,267 个文件、5,760,274,336 B 原始内容、415 个唯一对象，ZIP 为 488,128,872 B，SHA256 `e86c992ccca51724425261400dc25b7845dc81b31ec587be45a1afc620a79ce5`。全部文件已实际完整恢复。审计包保留定向控制、各版源快照、真实日志等价复查、partial 审计和恢复复算。发布的每个大 ZIP 分片保持原字节，每个恢复对象按原大小和 SHA 复核。

恢复流程：按索引 SHA 使用上级 `restore.py` 重组各包，再用 `archive.py verify --expected-sha256 ... --output ...` 复原。核心恢复后执行：

```bash
python3 -B "$module/../restore.py" --archive "$module/evidence/core-v1" \
  --output "$work/core-zip"
python3 -B "$module/../archive.py" verify --archive "$work/core-zip/payload.zip" \
  --expected-sha256 e86c992ccca51724425261400dc25b7845dc81b31ec587be45a1afc620a79ce5 \
  --output "$work/core"
python3 -B "$module/recheck.py" --root "$work/core" \
  --manifest "$module/evidence/core-v1/manifest.json" \
  --expected-manifest-sha256 f3942416575266db0d2de69b1df4683a46664d4b5f77784453b55b4f692537e7 \
  --output "$work/core-recheck"
```

脚本使用各真实 campaign 捕获的原验证器，对全部 21 个原参考案例重新计算；实际独立进程 `core-recheck-02` 已通过，每个案例的全部原判定相等。只有辅助验证器读取合格参考结果的目录在内存中做经 SHA 绑定的数据位置映射，不修改任何原回执、镜像或输入。恢复与复查的实际回执、文件数和哈希见索引，不要求新克隆或新 EMU；物理运行环境不在离线复算中重新资格化。

失败原件保留：第一次 UART 目标链接因未包含原 `klib.h` 而缺 `printf` 符号；修正团队包装并使用新的 target-build-02，未修改 AM。首次恢复复算在同进程包装器内调用，因预先导入当前工作树的辅助模块而被严格快照闭包检查拒绝；改用文档中的独立 Python 进程入口后通过，检查器未放宽。早期运行器、早期审计辅助版本及其已完成记录保留各自源字节。所有新证据均在原冻结输入之外；既有原始/失败证据和仍被借用的 Git 对象供体不清理。

## 6. 采用与接续边界

本模块作为固定模型的显式工程入口交付，R5 稳定默认不变。TA+cache 可按相同缓存政策回退 FR+cache；异常状态从 reset 后 p0 重放。初始化只验证结构前提，不能替代输入数据与量化域校验；独立状态交错不代表多线程资格。

尚未验证：本新消费者的连续 256 位置、完整香山 forward DiffTest、完整首 token 周期与公平重复样本、steady-state token/s、任意 checkpoint/tokenizer、训练模型质量、通用异常量化域、多线程、冷加载/packing 摊销，以及新 RTL/ASIC 面积时序。未改 RTL，因此没有启动无关综合或重复旧硬件回归。
