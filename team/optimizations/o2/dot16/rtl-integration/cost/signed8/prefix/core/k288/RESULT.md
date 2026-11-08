# Prefix core02：固定 K288 完整调用回归

日期：2026-11-08 UTC。合同 `r3-prefix-k288-eight-window-regression-v1`。

**新 prefix EMU 实际通过固定 K288 normal-0 的八窗口完整调用回归。** 本次增加这一固定例的 `target_runtime_qualified=true` 和局部 CSR 周期观察；不授予完整应用、G3、非法指令/trap 矩阵、完整退休审计或 PPA 资格。构建及原六例 smoke 的独立证据见 [core-build-02 / smoke-02](../RESULT.md)。

## 实际执行与输入身份

[status.json](status.json) 记录新 `core-build-02/cwd/build/emu` 的真实运行，终态为 `PACKED_WS_EIGHT_WINDOW_TARGET_PASS`：`process_started=true`、exit 0、输入身份未变、进程回收且进程组不存在。CPU affinity 为 `[1]`（单核）、nice5，seed1、128 MB RAM、4,000,000 guest cycle 保护；未修改 RTL 或软件算法。

状态起止为 **04:07:42.031246–04:19:42.680116 UTC**，相隔 **720.648870 秒，约12分钟**。这是包含仿真和检查的宿主耗时，不是芯片执行时间，也不是硬件加速比。

本次 runtime、目标 ELF/BIN、reference、flash 和新 EMU 由同一冻结 profile 绑定；最终审计重新核对 **457 个实际输入 pins**。关键身份为：

| 对象 | SHA-256 |
| --- | --- |
| 最终 source02 `run.py`（25,519 B） | `d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3` |
| `TARGET_CONTRACT.md` | `18f5b8b22e5be4ccd98a8cc854662376f90210e1c4dbfa55fae4402f50c07447` |
| 实际冻结 profile（93,672 B） | `ff1fede1efbd70926b6f3ddb00ba1579efcba8a059b8292e514e7888215ffc8c` |
| 新 EMU（71,489,976 B） | `6387d998c3f715a9ced1f44c4410f0f29f76780a96ec15c1830c8828ded6f887` |
| K288 ELF | `7b164fd3a6e08840f1bcc5824f48295e310e4d19544d41000740a8742fd58426` |
| normal-0 目标 BIN | `5efdb3f53786490fd2752b44e0ec48053bbfab98ce829a82ec7fcc8b5db2a756` |

最终 source02 仅为原 runner 增加新硬件身份绑定及固定 K288 合同适配；独立审查确认 `guest_check()`、`run()` 完整函数源字节未变，声明修改可反还原原 runner。初版 source01 曾把排版 `abi-layout.json` 的 SHA `6a4ec332…` 错绑到原始 `abi-run.log`；在任何 preflight 或 EMU 执行前已改为后者正确的 `5d6e133f…`。两文件解析出的1400 B ABI布局相同，字节身份不同。旧 source01 与纠正记录保留；这是准备阶段修正，不是一次已发生的预检或目标运行失败。

## 八个窗口与四组均值

实际测量顺序为 **P、N、packedP、packedN、packedN、packedP、N、P**，即 `[1,2,3,4,4,3,2,1]`。下表每行列出该方法两次出现时的全部周期样本；均值直接由这八个新样本计算，依据为 [checks.json](checks.json)。

| 方法 | 实现 | 第一次 cycles | 第二次 cycles | 平均 cycles | 每窗 instret |
| --- | --- | ---: | ---: | ---: | ---: |
| P（1） | 原 paired16 RVV | 45,669 | 45,610 | 45,639.5 | 22,173 |
| N（2） | 原 whole8/narrow custom | 27,419 | 27,288 | 27,353.5 | 13,025 |
| packedP（3） | packed-Ws RVV | 45,023 | 45,072 | 45,047.5 | 22,173 |
| packedN（4） | packed-Ws custom | 25,630 | 25,681 | 25,655.5 | 13,025 |

保留同次更快的 RVV 对照 packedP，与同次更快的 custom packedN 比较：

`45,047.5 / 25,655.5 = 1.7558613163×`；对应窗口周期下降 `1 − 25,655.5 / 45,047.5 = 43.047894%`。

这是本次固定完整调用窗口的观察倍率，`performance_qualified=false` 保持。**打包 prepare 位于计时窗口外**，不能将上述倍率称为包含打包成本的端到端收益。

四项均值与旧 f149 固定 K288 记录相同，只支持该固定例下各方法的周期保持。当前八个窗口确由新 EMU 运行，未借用旧硬件 PASS；均值相同也不证明其他输入、模型或应用周期保持。旧 f149 的 NQ/PQ 完整 forward 结论不转授给新 prefix，本次 K288 结果同样不外推为完整 forward 收益。

## 正确性覆盖与资格边界

本次包含 **8 次 warm 调用及8次测量调用，共16次完整调用、4608个输出比较**。原 guest 已检查完整活动／非活动槽、guards、CSR/FCSR 及全部 prepared bytes；八窗 flags 均为1、输出 FNV 均为 `f4481cc0f931d2d5`，窗口 instret 与固定 reference 相符。完整序列、原 DiffTest/reference/image 检查、原失败门禁及 GOOD TRAP 均按未改的 checker 判定通过。未做完整目标内存 dump。

聚合 `cycleCnt=914004`、`instrCnt=758544` 仅为运行诊断，`aggregate_is_kernel_or_application_metric=false`；它们不是某个内核或完整应用的性能指标。

`performance_qualified`、`application_performance_qualified`、`full_retirement_window_audited`、`retired_custom_count_verified`、`asic_ppa_qualified` 均保持 false。没有目标重放或本次目标负控；本次合格范围止于上述固定例的完整调用正确性及局部周期观察，不改变生产默认，也不将局部 FU 面积与这些周期拼成已测整核／应用 PPA。

## 已闭合归档

[raw.zip](raw.zip) 为 **172,225 B**，SHA-256 `709b6de063b1bc97dcaaea00d89d6a6b087c80f0503af9fcf7da772ec4b7dd57`；含 **17 个原始 payload 文件 / 3,267,086 B**，省略文件数为0。归档 manifest SHA 为 `0ab1f04c3f8cdc63ad2634fc6678beb6ee480ebd120c7d4f5920598000ff9bb2`。

[audit.json](audit.json)（972 B，SHA `243d76a612d7837a5d894b6032d37e1b31dbed9a6d5d90501ed6bf209d470286`）记录全部成员 SHA/CRC、源库存及内容未变、457 pins 实际核验，以及32168／32169两个进程组均不存在。归档阶段没有新 EMU 运行或构建；这不改变此前目标已经真实执行的事实。

审计固定的 status SHA 为 `1b20be409bbb90373900739bf2eccde4e418f5d062bc33d19d981529d6cbefd0`，checks SHA 为 `66b30e06cb5a39f57e3790210dc3b2aa741d7a01a8230857c8d556d164e7bb4d`，二者与本文引用原件一致。归档通过仅说明这批证据保存完整，不新增运行资格或独立重建能力。
