# W2＋norm 首 token：构建、参考与目标证据

更新：2026-10-28（UTC+08:00）。本轮接续基点 `ffd668bf1bc80850d382f514d13bb00316c85582`，操作ID `20261028-LiZufan001-first-token-close-1127`。工作负载身份 `r2-s3-w2-norm-first-token-v1`，资源身份 `r2-s3-w2-norm-first-token-resources-v1`。基点为 `431938271dd3b9eda8595a45d2bcf4e429d25797`；本页随新增源与证据提交。

**最终build-03四例原参考、四例完整目标、归档实际恢复及冻结原文复算全部闭合。** 资格限本页固定首token场景；单冷窗口的公平性能资格始终为false。当前资源与发布事实以协调Issue和实际收据为准。

## 已完成资格

最终包装使用同一个已通过八例消费者和双状态 API 的 `consumer-w2-norm.o`，没有重编该对象。四个 GEMV 函数、norm 叶及规范化 C 函数的重定位身份均经过实际 ELF 检查；完整状态前后各16字节 guard、TLS/errno、RNE、精确 flags==1 和成功／失败 a0 trap 均在最终包装中验证。

`first-token-reference-03` 分别在四个独立原 NEMU 进程执行真实 TA 负控、FR-cache、TA-cache、TA-cache 重放，读取完整 guarded state、五模型、gold、TLS、controls 和初末寄存器／CSR。正例全部3,691,424字节状态与 host gold 一致；负控真实翻位 byte152476，精确 code94 / BAD trap。TA 与重放完整验证结构相同。

| 案例 | 整个参考程序退休指令数 | 终态 |
| --- | ---: | --- |
| TA 负控 | 10,276,596 | 预期 code94 拒绝 |
| FR-cache | 11,196,269 | GOOD trap |
| TA-cache | 13,815,497 | GOOD trap |
| TA-cache replay | 13,815,497 | GOOD trap，完整重放一致 |

这些值包含初始化及状态验证，不是香山周期。新离线入口已用最终四例原始参考数据预检，231项历史输入绑定、完整原始校验、TA/replay 相等通过；父构建和八例资格 metadata 已对应父 norm manifest。该预检没有启动新NEMU/EMU；后续目标终态和正式归档复算见下节。

## 完整目标与原字节复算

原四例目标 campaign 于2026-10-28 03:58:40（UTC+08:00）完成，原宿主执行收据为 exit0、cleanup_complete；本轮没有重新启动 NEMU 或 EMU。FR-cache、TA-cache 和独立 TA replay 均完成全部3,691,424字节状态比较、双侧guards、TLS errno、RNE与精确flags=1、原DiffTest终态；TA负控完成forward后在状态byte152476按预期code94拒绝，实际BAD trap消耗a0。

| 案例 | 调用窗口 cycles | 调用窗口 instret | 整个程序 guest_cycles | 终态 |
| --- | ---: | ---: | ---: | --- |
| TA负控 | 19,772,704 | 10,122,100 | 20,072,530 | 预期code94／BAD trap |
| FR-cache | 20,258,039 | 7,502,872 | 26,842,481 | GOOD trap |
| TA-cache | 19,774,245 | 10,122,100 | 26,359,987 | GOOD trap |
| TA-cache replay | 19,774,245 | 10,122,100 | 26,359,987 | GOOD trap，完整validation相等 |

四次CSR的原值、实际sample与retire数据以及差值逐例一致，详见[原件算术交叉核对](../evidence/first-token/analysis/target-summary.json)。TA与replay相等的是完整验证结果结构；stdout长度、PID和宿主时间不同，不声称所有运行文件逐字相同。负控在窗口外提前终止状态比较，整体guest_cycles较少不构成forward收益；窗口外差值6,285,916周期未按验证阶段进一步归因。

正常TA及replay各有1,949,184次ACCEPT／MOVE／RESPONSE／ENQUEUE／COMMIT，未出现WAIT、FULL_STALL、KILL或收尾未完成事务；1,949,182次响应握手为2拍，2次为3拍，同时记录2次输出STALL。该结果符合原两槽弹性接口允许反压延长握手时延的合同，不承诺所有请求固定2拍。观察到1,192,754对相邻事务以1拍间隔被接受；这不是整窗口平均吞吐率，也未逐项归因两次3拍事务的具体PC。

逐PC核算得到K288的32个站点各55,728次，K768的32个站点各5,184次；与固定几何 `(172×36×9 + 6×36×24)×32 = 1,949,184` 精确相符。这是结果分析补充，原校验器的 `exact_dynamic_count_claimed=false` 字段保持原值。

本轮在2026-10-28 13:12:18（UTC+08:00）完成实际归档恢复后的[完整原文复算](../evidence/first-token/audit/result.json)：原reference、target和PC profile分别调用封存的历史校验器；四个target case在至多四核内并行，每例五项派生产物与原件逐字相等，TA/replay完整门禁及全部恢复文件前后inventory通过。新调度只改变离线执行安排，原官方参考、目标日志、冻结输入和判据均未改。

归档为1,646个普通文件、15,071,206,214原始字节、481个去重对象；ZIP为1,028,780,967字节，按50个至多20MiB原字节分片发布。实际重组与已恢复ZIP完全同SHA，未重复展开第二份恢复树。ZIP SHA256为 `5dd9c61601ed204ba6d0475da2fb5319b36a164129257ea6eeea23f85bdfc28e`，manifest为 `df00872b6b493d9a89c37ca72c226d96bf7d5ed2882afc232186e765d68475ef`；完整[发布索引](../evidence/index.json)和[重组收据](../evidence/first-token/transport-receipt.json)提供逐文件身份。父norm包仍独立引用，本包不冒称重做父raw审计。旧失败构建、参考包装、PC诊断首版、机制检查及诊断原件均保留。

**本合同只授予固定未训练模型、冷启动p0/token1的正确性资格。`performance_qualified=false` 与 `full_retirement_window_audited=false` 始终保留。** FR与TA窗口相差483,794周期仅为本次原始观测，没有多样本公平比较、全部普通指令退休窗口或应用加速资格；不改R5默认，不迁移旧S256、模型质量或ASIC资格。

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

窗口计入起始 instret 指令、排除末尾 instret 指令，包含两者之间实际 fence 与 dispatch。历史源码闭包对完整原始 histogram、状态和收据重新计算通过；外层证据接线另核对348项已保存的历史输入，包括间接 norm baseline。当时这些是原生数据复算和绑定预检；本轮已将该诊断纳入同一首token归档，并由历史profile校验器完成恢复后的原文复算。

首次 `first-token-pc-profile-01` 在宿主编译阶段失败：该实际 NEMU 头文件将 gpr 定义为包含 `_64` 的联合体，观察器误把联合体整体赋给整数。原生成器 `7cc63c42…d3a3467`、派生C、完整编译错误和进程回收收据均保留，实际启动 NEMU 为0。只修正字段读取后在新目录运行第二版，不改官方声明或参考语义。

该证据支持收束 norm 指令级枚举，并优先结合目标实测检查矩阵路径。向量指令每条完成的工作量、延迟和访存差异仍需目标证据；不能从上述 FR／TA 指令差推出周期快慢，也不为本批增加公平性能或全部普通指令退休审计资格。

## 矩阵退休差的汇编闭合与后续候选

对最终冻结的 `fused.S`、`w2.S` 按真实循环界限展开，并逐函数、逐助记符对照已复算的参考 PC 统计，四个矩阵函数的全部动态计数一致。TA 窗口相对 FR 多出的2,619,228条指令由矩阵内核的2,619,216条及 `route_matmul` 的12条精确闭合。

每个内组处理八个输出行、每行32个K元素；`addi ..., 0` 按实际反汇编别名记作 `mv`：

| 每内组项目 | FR | TA | TA−FR |
| --- | ---: | ---: | ---: |
| 点积主体 | 16次vwmul＋16次vwredsum，共32 | 32次dot8 | 0 |
| `vle8.v` | 18 | 36 | +18 |
| `addi` | 21 | 39 | +18 |
| `mv` | 2 | 1 | −1 |
| `vadd.vv` | 0 | 24 | +24 |
| `vsetivli` | 13 | 5 | −8 |
| `vmv.v.i` | 8 | 0 | −8 |
| 其他共同指令 | 15 | 15 | 0 |
| 合计 | **109** | **152** | **+43** |

两条路径均有 `172×36×9 + 6×36×24 = 60,912` 个内组，故矩阵差额为 `43×60,912 = 2,619,216`。这些 `vle8.v` 的显式元素读取量每组都是288B（FR为18×16，TA为36×8）；这不包含其他加载，也不代表缓存或总线事务。TA的24次部分和合并存在真实数据依赖，不能为了降低计数直接删除。

复算器 `analysis/reference-loop-cost.py` 固定输入SHA并拒绝不匹配来源；原报告、逐助记符计数、输入绑定和运行收据位于本轮输出根的 `analysis/`。该诊断没有新增NEMU/EMU，没有更改冻结目标输入，也不授予新内核资格。

当前保留三个有界假设，均尚未实现或取得新参考／目标资格：

- **尾部补齐行裁剪**：原K288路径多算1,408行，即176个tile。对应现有循环体为FR 174,240条、TA 242,352条，分别占原窗口2.3223%和2.3943%；新增控制与分派成本未扣除。
- **零偏移地址复制清理**：FR/TA分别有121,824/60,912条，占窗口1.6237%/0.6018%。这与尾部预算重叠，不能直接相加；公平实验应同时处理两条路径。
- **相邻8B加载合并**：在固定VLEN128、e8/m1、VL8合同下，可研究18次16B `vl1re8.v` 加18次 `vslidedown.vi 8`，替换36次8B加载，并省18次地址形成。激活必须提取到另一寄存器以保留后四行所需低半；权重可在低半消费完后原地滑动。静态数据流允许保留32次dot8、24次整数合并及FP顺序，不新增向量寄存器。内组计数预算为152→134，总计1,096,416条，约原TA窗口10.8319%。但每组置换由6次增至24次，还增加load→slide→dot依赖，实际可能变慢；访存故障的指令边界也不同。

加载合并的语义核对依据现有[vdot合同](https://github.com/cc77-builder/riscv/blob/ffd668bf1bc80850d382f514d13bb00316c85582/team/spec/vdot.md)及[RISC-V向量规范](https://docs.riscv.org/reference/isa/v20260120/unpriv/v-st-ext.html)中的whole-register load和vslidedown条款；静态可行性不代替固定工具链、原参考及实际目标机上的新验证。

这些只是当前指令预算和设计可行性。它们不是净收益、周期收益或其上限，不支持此时扩大ISA/RTL，也不改变当前norm性能HOLD、强FR对照或原四例目标合同。具体下一步以当前目标终态及必要的新候选验证为依据。

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

每个 EMU 子进程上限40M guest cycles、28,800秒墙钟、4GiB每条输出流；随后完整 raw 审计及输入复核耗时另记，四独立进程受四核总预算约束。profile和源码在执行前冻结，原 O2/T13、UART 与 DiffTest 均保留。原始数据已由 [evidence.py](evidence.py) 封存并从真实恢复目录重新复核，历史失败按原样保留；完整发布位置见上节。

流式归档器与旧 `sha256-object-zip-v1` 格式的双向恢复兼容检查已通过，覆盖重复对象、空文件、Unicode路径；对合法重新编码但对象内容被篡改的 ZIP，实际 SHA 门禁拒绝。它避免一次载入数GB日志，未改变冻结目标日志策略。

本候选没有新 S256、连续 token、训练模型质量或 ASIC 资格。原 norm 性能 HOLD、原 W2 性能 HOLD、R5 默认、强 FR 对照及完整 scalar norm/W2 consumer 回退均保持。目标全部普通退休窗口未审计；最终即使正确性通过，也只适用于此固定模型和 p0/token1 的明确入口。
