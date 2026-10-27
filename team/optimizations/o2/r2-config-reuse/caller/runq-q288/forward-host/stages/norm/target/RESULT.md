# W2＋norm 首 token：构建、参考与目标证据

日期：2026-10-27（UTC+08:00）。工作负载身份 `r2-s3-w2-norm-first-token-v1`，资源身份 `r2-s3-w2-norm-first-token-resources-v1`。基点为 `431938271dd3b9eda8595a45d2bcf4e429d25797`；本页随新增源与证据提交。

**最终 build-03 的四例原参考已通过；完整目标四例仍在运行，尚未授予目标正确性资格。** 实时进程保护以协调 Issue 和实际 `state.json`／进程为准。单冷窗口的公平性能资格始终为 false，不随运行成功而改变。

## 已完成资格

最终包装使用同一个已通过八例消费者和双状态 API 的 `consumer-w2-norm.o`，没有重编该对象。四个 GEMV 函数、norm 叶及规范化 C 函数的重定位身份均经过实际 ELF 检查；完整状态前后各16字节 guard、TLS/errno、RNE、精确 flags==1 和成功／失败 a0 trap 均在最终包装中验证。

`first-token-reference-03` 分别在四个独立原 NEMU 进程执行真实 TA 负控、FR-cache、TA-cache、TA-cache 重放，读取完整 guarded state、五模型、gold、TLS、controls 和初末寄存器／CSR。正例全部3,691,424字节状态与 host gold 一致；负控真实翻位 byte152476，精确 code94 / BAD trap。TA 与重放完整验证结构相同。

| 案例 | 整个参考程序退休指令数 | 终态 |
| --- | ---: | --- |
| TA 负控 | 10,276,596 | 预期 code94 拒绝 |
| FR-cache | 11,196,269 | GOOD trap |
| TA-cache | 13,815,497 | GOOD trap |
| TA-cache replay | 13,815,497 | GOOD trap，完整重放一致 |

这些值包含初始化及状态验证，不是香山周期。新离线入口已用最终四例原始参考数据预检，231项历史输入绑定、完整原始校验、TA/replay 相等通过；父构建和八例资格 metadata 已对应父 norm manifest。预检没有启动新 NEMU/EMU，也不等于尚未完成的目标 raw 复算。

## 实际调用窗口的参考 PC 诊断

`first-token-pc-profile-02` 于2026-10-27 22:26 +08:00完成 FR-cache、TA-cache 各一次独立原 NEMU 执行。它使用最终同一 guest ELF/BIN，只在团队宿主 adapter 副本中加入被动观察器；原 adapter、NEMU、官方头文件和目标四例输入均未改。契约见 [PROFILE.md](PROFILE.md)，生成器 SHA256 为 `be376c1b82176a8634e585bfa6d981a75419a038b5654124f62c370de2283538`。

每例15份完整 guest 二进制文件与原合格参考逐字一致，包括 image、完整状态／模型／gold／TLS，以及初末寄存器和 CSR。四个 CSR 实际寄存器值与原 report 一致，PC计数之和等于原 instret 差；FR 共1,576个不同退休PC，TA共1,664个，所有计数均落入实际 ELF 函数范围，无未归属PC。下表是**函数自身的动态退休指令数**，调用的其他函数分别记账，不能读成目标耗时份额。

| 函数／组 | FR-cache | TA-cache |
| --- | ---: | ---: |
| 完整 instret 窗口 | 7,502,872 | 10,122,100 |
| K288 GEMV（各自的 FR／TA 函数） | 6,135,240 | 8,531,544 |
| K768 GEMV（各自的 FR／TA 函数） | 567,180 | 790,092 |
| 两个矩阵函数合计占比 | 89.3314% | 92.0919% |
| `quantize` 自身 | 261,236 | 261,236 |
| `r2_rmsnorm_rvv`＋`r2_norm_output_rvv` | 20,709 | 20,709 |
| 上述两个 norm 函数合计占比 | 0.2760% | 0.2046% |

窗口计入起始 instret 指令、排除末尾 instret 指令，包含两者之间实际 fence 与 dispatch。历史源码闭包对完整原始 histogram、状态和收据重新计算通过；外层证据接线另核对348项已保存的历史输入，包括间接 norm baseline。此时这些是原生数据复算和绑定预检，正式归档恢复复算须在目标四例终结后单独完成。

首次 `first-token-pc-profile-01` 在宿主编译阶段失败：该实际 NEMU 头文件将 gpr 定义为包含 `_64` 的联合体，观察器误把联合体整体赋给整数。原生成器 `7cc63c42…d3a3467`、派生C、完整编译错误和进程回收收据均保留，实际启动 NEMU 为0。只修正字段读取后在新目录运行第二版，不改官方声明或参考语义。

该证据支持收束 norm 指令级枚举，并优先结合目标实测检查矩阵路径。向量指令每条完成的工作量、延迟和访存差异仍需目标证据；不能从上述 FR／TA 指令差推出周期快慢，也不为本批增加公平性能或全部普通指令退休审计资格。

## 冻结身份

| 实物 | SHA256 |
| --- | --- |
| 同一 consumer 完整对象 | `68ece1e0b8d7fbce6e3ea7167818058b2c74b19691f8e06ef15e917be396e037` |
| 最终首 token ELF | `a4e7da9ac8580f4aee583061a5f2dd7a666dec4c128e63b93fe45584b16e5692` |
| 最终首 token BIN | `bdf226be80859c37d90a61979581ff6e8f2f10832f9d087cc48006e29c16e99d` |
| 最终运行 profile | `4a4cffd7a2d4bfbbcbdb4f6ab9423ac82a1703f29b783cf92c46dea74a4cf428` |
| T17 EMU | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 原 NEMU reference | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` |

最终镜像77,108,464字节，heap 起始 `0x84caa000`，实际失败 trap PC `0x80001d34`、成功 trap PC `0x8000013c`，两者均为 `0x0005006b`。此前 build/reference-01、02 按原字节保留；新 run 只接受带 `exact_flags_guard=1` 的最终版本，旧参考 PASS 没有迁移。

正式输出根为 `norm-resume-20261027-2000/first-token-target-01`，操作 ID 为 `20261027-LiZufan001-first-token-2120`，实际于2026-10-27 21:23:24 +08:00启动四例。使用在执行前封存的 resource-contract-v2；此前 profile只曾预检，未启动 EMU，版本调整修复信号清理保护，未改变任何预算或工作负载。

## 证据处理与边界

每个 EMU 子进程上限40M guest cycles、28,800秒墙钟、4GiB每条输出流；随后完整 raw 审计及输入复核耗时另记，四独立进程受四核总预算约束。profile和源码在执行前冻结，原 O2/T13、UART 与 DiffTest 均保留。原始数据将由 [evidence.py](evidence.py) 封存并从真实恢复目录重新复核，完整失败也原样保留。

流式归档器与旧 `sha256-object-zip-v1` 格式的双向恢复兼容检查已通过，覆盖重复对象、空文件、Unicode路径；对合法重新编码但对象内容被篡改的 ZIP，实际 SHA 门禁拒绝。它避免一次载入数GB日志，未改变冻结目标日志策略。

本候选没有新 S256、连续 token、训练模型质量或 ASIC 资格。原 norm 性能 HOLD、原 W2 性能 HOLD、R5 默认、强 FR 对照及完整 scalar norm/W2 consumer 回退均保持。目标全部普通退休窗口未审计；最终即使正确性通过，也只适用于此固定模型和 p0/token1 的明确入口。
