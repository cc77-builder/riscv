# GS32 K288 消费者：独立入口参考正确性通过

2026-11-06 UTC。合同：[r2-s3-forward-consumer-gs32-v1](CONTRACT.md)。关联 WORK：Issue #2 `6671408286`，操作 `20261106-LiZufan001-gs32-rvv-pro3`。

## 结论

新增 `r2_w2_gs32_forward(state, token, position)` 已完成真实 GNU 构建、实际 ELF 路由核对及三个独立参考进程验证。固定合成模型 D288/H768/L6/HQ6/HKV6/V32000/S256/GS32，tokens 1、7、19，位置 0、1、2：每步完整 3,691,424 字节状态与独立 host golden 相同，fflags 与原 scalar 的 `[1,1,1]` 完全一致；模型输入保持不变，正常恢复与重放结果完全一致。

资格仅为这个独立入口的三步参考正确性。未运行新的目标 EMU，未授予全 256 步、其他模型、训练模型质量、双状态隔离、完整应用周期或加速比资格。旧方法 0–4、方法 5 非法、稳定默认入口均保持。

## 实现与实际路由

从已验证 norm/W2 父消费者的实际编译源码派生，只复制 FR-cache 模板并替换七处 K288 路由。原四个 C 消费者保留；去掉新增代码后，三个派生 C 输入必须逐字节恢复为父源码。量化、打包、尺度、FP32 乘加次序、norm、RoPE cache、attention、SwiGLU 和状态写回沿用原实现。

| 路径 | 新入口实际选择 | 每 token 的 full-Q288 panel 调用 |
|---|---|---:|
| 六层 Q/K/V/Wo | GS32 K288 | 24 |
| 六层 W1/W3，输出 768 行 | GS32 K288；每矩阵三个 panel | 36 |
| classifier，输出 32000 行 | GS32 K288；112 个 panel | 112 |
| 六层 W2，输入 K768 | 原 FR，选择器落到 `q768_fr` | 不在 K288 合计内 |

合计 37 个 K288 矩阵、172 次完整 288×288 panel 调用。13 个有填充的尾 panel 仍执行完整 Q288 内核；172 不是内核内部的 8 行 tile 数，后者为 6,192。

实际 ELF 有八处 `route_matmul` 调用，七处传入 `q288_gs32_rvv=0x80001300`，唯一 W2 调用传入原 FR 指针 `0x80000a40`。原选择器在合法 W2 域中选择 `q768_fr=0x80000180`；K288 的完整和尾 panel 两处间接调用均使用传入指针。旧公开入口的 unsigned `4 < method` 分支仍使方法 5 返回 NULL。证据为 [实际机器码路由记录](evidence/reference-v1/routing-review.json)；[review_routes.py](review_routes.py) 可重做这份固定 ELF 的地址和机器字审查。

构建同时核对旧四个汇编函数、GS32 完整 420 字节函数体及原 norm 对象的链接身份。GS32 函数体 SHA256 为 `2d95481faa1c79f7a8a06ef65fc02154e30cf731e6ba5c990a7209c2e90c32ab`，与已经筛选和目标验证的 v2 相同。

## 真实验证

GNU 构建实际于 00:53:01.662–00:53:08.615Z 完成。参考 campaign 于 01:14:34.379–01:14:48.310Z 完成，CPU0 单核、串行三进程。外层操作 16.359 秒，exit 0、cleanup complete；三个独立 PID/进程组均已回收。随后重新核验 308 个冻结运行输入，零漂移。

| 用例 | 实际行为与结果 | 退出码 | 完成位置 | fflags |
|---|---|---:|---:|---|
| negative | 新入口运行后翻转末 logit 的一个比特；原比较器在 byte 152476 拒绝，BAD94 | 2 | 1 | `[1]` |
| recovery | 每步完整状态、最终 live state、全部模型输入和未用区检查通过 | 0 | 3 | `[1,1,1]` |
| replay | 新进程完整复现 recovery 的状态、flags、参考退休量和计数样本 | 0 | 3 | `[1,1,1]` |

实际 guest 还运行了未初始化、空状态、token/position 越界和旧方法 5 的拒绝检查，并检查被拒绝调用前后的状态为空。正常结果的 snapshots SHA256 为 `be5e938c1405d866bb1c2f776805b4dca95a53fa6a02808f7a93f1b4ece8bb85`，live-state 为 `1c2b3ff1c04fda9deb3a2a02aee820c4bbfe46a8f187186c6f7945ff8d8d0674`。恢复和重放 validation 文件 SHA256 同为 `e624f86aaeb663d30ccf3e97928e4b7f78bc61ac787f2e74250280d0e9060690`。

原始结构化报告：[results.json](evidence/reference-v1/results.json)、[state.json](evidence/reference-v1/state.json)。这些是实际文件的逐字节副本，包括 64 位整数，没有经过浮点 JSON 数值重写。

## 指令归因诊断，非目标性能

复用已执行的旧 norm/W2 和新 GS32 参考结果，读取每个完整 forward 窗口的 `instret_after - instret_before`。原记录顺序是 `[cycle_before, instret_before, instret_after, cycle_after]`；不能把外层 cycle envelope 当作该退休指令窗口。

| 位置 | 旧 FR-cache 参考退休指令 | 新 GS32 参考退休指令 | 净减少 |
|---|---:|---:|---:|
| 0 | 7,502,872 | 4,828,781 | 2,674,091 |
| 1 | 7,532,699 | 4,858,608 | 2,674,091 |
| 2 | 7,561,908 | 4,887,817 | 2,674,091 |

父级同一 full-Q288 目标计划中，FR 与 GS32 的退休差为 `35,681 - 20,134 = 15,547`。`172 × 15,547 = 2,674,084`，与完整调用窗口的净减少只差 7 条。这个吻合支持实际消费者覆盖和主要指令差值归因；另外 7 条是尚未逐 PC 定位的调用窗口净差额，不能直接归给入口，也不能据此证明其他路径逐 PC 相同。详见 [参考指令诊断](evidence/reference-v1/reference-instructions.json)。

两个消费者是不同 ELF；这里没有公平的香山完整应用周期比较。新正确性 harness 在测量窗口外多做两次完整状态逐字节扫描，因此新全进程 retired `47,916,198` 不能直接与旧 `26,406,695` 比较。扫描还会改变真实硬件的 cache 状态，未来性能验证应另用相同准备流程的公共 harness。既有 full-Q288 中 GS32 相对较快 TA 的保守周期改善约 1.37%，也不能把本节约 35% 的参考指令减少解释为应用周期收益。

## 身份、复现与失败保留

所有外部运行位于常驻 `runs/gs32-rvv-20261106-0640/`，完整绝对路径、控制器身份、操作回执和失败位置见 [provenance.json](evidence/reference-v1/provenance.json)。主要身份如下。

| 产物 | SHA256 |
|---|---|
| 实际父 `consumer-build-02/result.json` | `8ad05a4aa3bee2bd23d14f698c43ebfa445703aa19e2f2951d079b655d76482d` |
| 新 `consumer-build-01/forward-consumer-gs32.elf` | `20fa1bc02dcc195833cd4b7f47d484bc57b22f56e5729f50280c74a47d25ed0b` |
| 新 BIN | `3c02ecbf6650b29d1bcefe18b7ec1b593ecd8de87251029abddc0a730cabbdcc` |
| 新构建 result | `01a9c1131f64bec666f6baea21f8d59d76a2b3228ed875ada7eabe11d6757cff` |
| 参考 results | `88a120c2b208cad6554ceef35bb96679b12b359dea19ba66e423a2f75300ad2b` |
| 参考 state | `a83fc8c5b4e4c8cfd83800c9b74ee9a2c934eec0a42b7d5e526e71eb73c37c58` |
| 运行输入清单 | `d73645d370b724ef92cb4843ec43aeae1b7cdaabbc5e2ab703c91db63377a0b8` |
| 完整支持快照清单 | `359d35f5242c8091992ac1b81955473d6dc7ff942c322de528142569366c43a0` |

已有 scalar 大 raw 已正式封存，第一次构建预检在旧路径找不到它们。`restore_scalar.py` 使用原归档工具校验 ZIP、清单和对象，只还原 scalar 原字节到 `scalar-audit-01`。重新审查生成的验证报告与原 SHA 完全一致；没有从 golden 重造输出，也没有补跑旧方法。

第一次参考预检发现旧 `runtime-source` 只保存模块，缺少身份门禁另行读取的源码。补齐时，当前生成器、检查器及 migration 文件与历史固定版本的差异被原条件拒绝；改为读取精确 Git blob/固定提交。初版收集器又因只遍历 build 可达模块而漏掉运行侧入口，该次 `consumer-support-01` 的文件集合标签不代表运行合格。最终 `snapshot_support.py` 完整复制原 manifest 的 75 个源码文件，并补齐 20 个按原 SHA/blob 核验的依赖，得到 95 文件、895,124 字节的 `consumer-support-02`。

构建仍使用冻结 `consumer-controller-02`；参考运行使用新冻结 `consumer-controller-07`。所有旧控制器、六次预检失败回执、第一次不完整支持目录、原构建及原父结果继续保留。未重写原身份门禁或原构建清单，未创建新检出，未修改官方代码。原 `git show BASE:path` 仅在身份校验期间通过真实既有 Git metadata 只读取对象，之后恢复进程环境。

复核这份已构建 ELF 时，用 `review_routes.py --build <consumer-build-01> --controller <consumer-controller-07> --output <新的路由记录>`；参考复现用 `run.py` 的 `--build`、`--adapter`、`--identity`、`--routing-review`、`--support-snapshot` 和全新 `--output`。具体已执行输入在上述 provenance 与运行清单中。必须先协调 CPU 预算，不能覆盖已有输出。新 ELF 的 PC、机器字和身份须重新审查，不能只换 SHA 后沿用本次路由记录。

## 采用与回退

保留该入口作为已验证的 GS32 K288 消费者候选，供后续更大收益方案在相同语义下组合或比较；当前不替换稳定默认，不单独为约 1.37% 的局部优势启动长整应用性能 campaign。回退直接继续使用原命名入口和旧方法枚举，无需迁移状态结构或重写模型。

CPU0 的三个参考进程和后续输入核对均已结束；已向主 Pro 释放给 NEMU 构建。提交、共享计分板及 `zufan` 发布由主 Pro 协调，本记录本身不代表已提交或已推送。
