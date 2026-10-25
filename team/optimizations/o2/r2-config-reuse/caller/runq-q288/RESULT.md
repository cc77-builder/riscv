# runq Q288：实现与中断验证记录

状态：**INTERRUPTED_BY_USER_DISK_RECOVERY_PRIORITY / NOT_QUALIFIED_COMPLETE_EMU**。本模块是可继续审查的实验实现，尚未取得完整目标正确性或消费者性能资格。

工作单元：`20261026-LiZufan001-runq-q288-0219`；实现/实跑为 2026-10-26 02:19～03:06（UTC+08:00），原字节封存于 04:00:57。v1 实现 `1632fc66fcf8685af29ea3d1998f37fa8fc4569d`，v2 实现 `835448de73da46a8302351b93cdb399ff598fc85`；封存与文档提交不改变这两个实现身份。

## 范围与实际结果

[固定合同 v2](CONTRACT.md) 从固定版本 llama2.c 的 runq 公开消费者取得完整 288×288、GS32 的 Q 投影形状与分组浮点语义。输入是确定性合成量化数组，权重只打包一次，六种整数叶共用相同 C 包装，额外 packed 权重为 82,944 字节。公开参数、来源及许可均已落地；这里没有真实模型检查点、完整 forward、token/s 或模型精度结论。

| 层级 | 实际证据与结果 | 适用边界 |
| --- | --- | --- |
| 本机 C 数值 | `host-02/result.json` 为 `RUNQ_NATIVE_C_ORACLE_PASS`。8 次检查、7 个不同输入名称（x0→x1→x0→x2，以及 min-min、max-max、min-max、zero-weight），每次全部 288 个 binary32 输出及完整 packed 字节通过。 | 使用 scalar test stub 代替整数叶；证明本机包装/打包与独立 C oracle 一致，不是 RTL 或目标 CPU 的完成证明。 |
| 严格 FP 见证 | 严格结果 `0x00000000`，融合路径 `0xa3800000`；禁止 FMA 的固定输入确实能够区分两种语义。 | 不用浮点容差掩盖运算顺序变化。 |
| GNU / 实际 ELF | 最终 `build-04` 完成独立编译、既有六叶机器字/重定位证明、输入字节与完整 Q 地址/控制流检查。`elf-controls-04/result.json` 的 signed→unsigned、multiply→add、错误 scale 下标、错误 panel 步长四个实际 ELF 变体均被拒绝。 | 静态路径检查不模拟未知 FP/vector 算术值；目标数值仍需完整运行。 |
| v1 目标负控 | `campaign-01` 自然结束为 FAILED；注入 PC 与 DiffTest 提交组首诊断 PC 不同，未满足原合同，未进入正常运行。 | 失败原文和旧实现保留。没有降低既有故障夹具或判定条件。 |
| v2 目标负控 | `campaign-02/runs/negative/result.json` 为 `EXPECTED_VDOT_HIGHBIT_REJECTION`；真实 vd0、bit100、PC `0x80001bc4`、word `0x0388000b`，注入 PC 与 mismatch PC 相等，退出 1 为预期拒错。 | v2 加入独立 fence/vdot/fence 探针；`abort_event_pc=0x8000027c` 单独记录，不把它误当 mismatch PC。 |
| v2 正常恢复 | 02:52:37 开始；03:06:00 因用户明确优先回收磁盘，仅向核验过的本轮 PID1558 发送 SIGTERM。原始结果为退出 -15、FAILED、`ValueError('complete execution required')`。 | 人为中断，没有完整正确性 PASS；独立进程重放未启动。 |
| 性能与采用 | **没有完整、合格的消费者性能数据，没有选择结果。** | 不以局部日志、旧 8×32 窗口或静态指令数代替本计划；不把中断写作已完成的 HOLD 判决。 |

实际新 EMU 共 3 次：v1 负控、v2 负控、v2 被中断的正常恢复。v2 合同中的 17 计时窗、46 次完整 Q、15,228 次整数叶及 82,945 条已提交 vdot 是**每正常进程的计划数量**，不是本轮完成数量。

## 冻结身份

| 项目 | SHA-256 |
| --- | --- |
| build-04 ELF | `7f2c3d6de93f979cc252379a8fe2147e0d7ff121b0a38151f4604ee832884f26` |
| build-04 BIN | `51709cc0f8a147989a4992e41ae4951801356da0b3aa694ff03085f6c8f1a524` |
| T17 EMU | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 正常 NEMU | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` |
| boot-flash | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994` |
| 本机 C 测试库 | `a4db0b7a20ffb7543bc6ff65d4953f3485645d9554d1fd3f771cd3ca91857126` |

本轮没有修改官方程序、生产 RTL、固定 T17/NEMU/AM/flash 或旧负控检查器。源码硬件等价与本机最终源码绑定原文见 `hardware-source-equivalence.json`、`host-final-source-binding.json`。稳定 firstdot V2/V1、显式 RVV 回退和其他子项已有 HOLD 保持原适用范围。

## 原始证据与可接续边界

[封存说明](evidence/interrupted-20261026/README.md)、[逐文件清单](evidence/interrupted-20261026/manifest.json)和[原字节 ZIP](evidence/interrupted-20261026/raw.zip)包含 560 个文件、59,111,205 原始字节；ZIP 6,128,333 字节，SHA-256 为 `ab6596d427684c7c6f278342afed3bc32396bb7d5241d0bc1c163f210e3d93f0`。全部成员解压后 SHA 与原件一致，封存前后原件路径集/大小/mtime/inode 未变化。失败的早期构建、v1/v2 日志、命令、输入与源码快照及中断回执均在包中。

这是**中断实验的原字节快照**，不是通过冻结完整运行审计器的完成归档；字节一致不能提升结果资格。现场原件继续保留：

```text
/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/runq-q288-20261026-0219
```

本工作单元随状态交付暂停并释放认领。后续应先判断该合成 Q 投影是否值得继续投入整核时间；若确需继续，使用新 campaign 身份，重新核实冻结输入和资源保护，完成正常恢复与独立重放后才讨论性能选择。保留当前失败状态，不覆盖旧目录，不把下一轮自动续跑设为前置任务。
