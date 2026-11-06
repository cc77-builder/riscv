# dot16 生产解码双态验证结果

2026-11-06 的两次实际运行均通过。本记录只给出生产解码器及新增只读运算类型观察的动态资格；FU 与父级结果分别见上级 [FU 结果](../VALIDATION_RESULT.md) 和 [父级结果](../parent/RESULT.md)。

## 来源与真实运行

固定 HEAD 为 `c981529dc6e493fb7deee8429b9ce05fd197497b`，叠加生产补丁 `5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416`。新运行器 SHA256 为 `0214e9a220b905156c9818342832a9226e3b7bfcce2a8f5340f0b659f7c68b7c`，合同为 `92b12eefa986c0b309d91cb72295746a10d538adba11da14ca77cff671f5a62d`；完整来源与回执在 [result.json](result.json)。

| 状态 | 仓外运行目录末级 | 实际外层 UTC 区间 | 实际耗时 | 结果 |
|---|---|---|---:|---|
| 关闭 | decode-flag0-02 | 02:35:47.949–02:36:58.323 | 70.317 秒 | exit=0；cleanup=true |
| 开启 | decode-flag1-01 | 02:38:41.265–02:39:52.185 | 70.865 秒 | exit=0；cleanup=true |

共同运行根目录为 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-production-20261106-0014-pro2`。两态均使用 CPU1/jobs=1、4 GiB JVM、内部累计 900 秒预算与外层 1000 秒保护；没有超时或取消。除回执中的 cleanup 外，还分别独立核验最后受控进程组已不存在。

两态均实际完成：官方核心 classpath 导出、独立小模块 Scala 编译与 Chisel elaboration、生成 RTL lint、Verilator 构建、正例以及两个观察负控。正例命令 exit=0；负控预期并实际 exit=1，日志原因与指定注入一致。终态中的 `last_process_returncode=1` 对应最后一个预期失败的负控，不表示整轮失败。

## 动态覆盖与结论

原 `GenerateVDotDecode.scala` 和 `decode_test.cpp` 保持字节原样。新 probe 继承原 harness，只引出实际 simple/complex `fuOpType`；C++ 通过 11 处受控变换生成，两态均逆变换逐字节重建原测试。

| 实际观察 | 关闭态 | 开启态 |
|---|---:|---:|
| 原 dot8 完成事务 | 131109 | 131109 |
| 新 dot16 完成事务 | 0 | 131109 |
| 新编码组合分类拒绝 | 131072 | 不适用 |
| simple op0 比较 | 131109 | 131109 |
| complex op0 比较 | 131373 | 131373 |
| simple op1 比较 | 0 | 131109 |
| complex op1 比较 | 0 | 131373 |
| 新编码 MASK 邻位回归 | 不适用 | 17 |
| 指定观察负控 | 2 项按预期拒错 | 2 项按预期拒错 |

每套 131109 次完成事务保留原 4 种 ta/ma × 32³ 寄存器组合、SEW/LMUL、vill、VS-off、vstart、v0 以及 redirect 后恢复。complex 比较比事务数多 264 次，来自 33 个停顿场景各 8 次额外观察。原寄存器字段、异常、写使能、无 old-vd 依赖、单 uop/写回边界、旧邻位及 vadd 回归继续执行。

开启态的新编码受阻时，输入已切换为旧 dot8 编码并扰动 vtype/vstart；在途复杂解码结果仍保持 op1 和原快照。新旧编码的实际 op 分别为 1 和 0，已经经过运行比较。关闭态的 131072 项只是组合分类拒绝，不计入完成事务。

两项负控只在 C++ 读取后翻转一次实际 simple/complex op：关闭态在旧首例 case=0 拒绝；开启态先完成全部旧事务，再在新首例 case=131109 拒绝，分别出现 `simple operation mismatch` 和 `complex operation mismatch`。这些结果证明新增观察比较链能拒错，不是 RTL 故障覆盖率。

## 输入与生成物身份

两态共用 435 项硬件构建输入、126 个固定递归依赖、14 项直接输入和 4 项 probe 工作区输入。435 是 `compiler-inputs.json` 的口径，不能与父级包含额外测试源码的 437 项 source 清单混用。运行器完成前后身份比较，采证时又核验了直接输入、probe 输入、生成 RTL 和二进制的实际字节。

导出 classpath 保留全部 135 项及顺序：92 个文件、20 个目录（内含 10165 个文件）与 23 个明确允许缺失的资源目录。两态 classpath 内容清单 SHA 相同，为 `ab6aaa12cb8b9508d1a1bf994d63561a08f2112ea6d9d48b30ac7916fc1dfdde`；缺失目录没有被创建或从清单过滤，身份前后保持一致。

| 关键证据 | 关闭态 SHA256 | 开启态 SHA256 |
|---|---|---|
| status.json | `80f6db20a701ccb9ab802612e703b9934e9a9353c33442742b334d8eeac80341` | `0f2fada77b37ccbce9852aaf7b10bcf4305a5673ec3698890bce78cc1cd69c4a` |
| result.log | `1ff0ce51229c6bee942e0dff9785b23988adb0099a753d1a0f5a178428adc914` | `f893dc34c340c9925e0afba857ccdf092cb218cfce33e731e3658928cf493587` |
| 生成 VDot16DecodeProbe.sv | `bf2bd8c5ab858f760d426ae131e8fa167c3bd5cc27874049d3a6049c5d47db1d` | `641c1be092a5ccd317de09e7ad94018c0d91219d2e9c7988188ab889ec5f1a91` |
| Verilator 二进制 | `6e5087fd0a443bb7e6c4d5c587f720ae454c97650bb66325c8075b256217c336` | `50cf43c7737f1d346022a085317fa5c524efd9af79783bf118410dee70154d9e` |

所有命令、原始 stdout/stderr、完整 classpath 内容清单、生成物及源码快照均在对应运行目录保留。机器结果记录它们的路径、大小、SHA256、外层操作身份及退出码，不用本说明替代原始记录。

## 首轮失败与适用边界

`decode-flag0-01` 于 02:26:56.691–02:27:11.589Z 实际 exit=1、cleanup=true，耗时 14.865 秒；核心 classpath 任务 exit=0，尚未进入 probe 编译。原因是新增运行器错误地要求所有 PathRef 路径存在，而 Mill 正常导出了 23 个缺失的可选资源目录。原运行器 `31ea96df…`、原合同 `6d62f33d…` 和失败证据保留在该次源码快照及机器结果中。

后续仅修正新团队运行器与合同，逐项限定这些资源路径、记录缺失身份并在结束前复核；未知缺失项、缺失 JAR/classes 和悬空链接仍拒绝。此修正没有改变生产解码器、官方构建、原测试或矩阵规模。

本 harness 没有 VL 输入，也没有 Rename、RF、ROB 或整核提交。这里观察的是分类与解码，不证明关闭态整核 illegal-instruction trap，也不代替 VL=8/16 的执行检查。运行时长用于可复现性与资源记录，不作为应用性能、综合时序或功耗结论。
