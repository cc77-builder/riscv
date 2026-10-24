# R4：GEMV 普通调用入口实测与交付

> 本轮普通调用入口的性能、功能及原始证据复算通过；按尺寸保留较快实现。完整组合资格、T17及默认入口仍分别验收。

操作：`20261024-LiZufan001-r4-entry-0442`，执行身份：`@LiZufan001 / Agent`。软件开发基点为 `ac2f4082a6a4710dca6a739f66d6fa77c49552b8`；实际新增源码以构建快照、运行输入和归档哈希为准，基点 SHA 不冒充含未提交新文件的完整源码身份。

## 1. 本次解决的问题

原 R2-SELECT 能查询和导出已合格的完整基准镜像，但这些镜像还不是可供 C 程序直接调用的 GEMV 函数。本次保留原计算 body，新增按形状命名的 RV64 C ABI 叶函数、公共汇编/头文件、普通 C 功能程序及独立验证入口。原镜像工具、既有合同和官方程序保持原样。

采用结论按新调用路径的完整比较产生：4×8、8×32、16×64 保留 S1 reuse vdot；4×13 选更快的 S1 reuse RVV。全部 S0/S1、basic/reuse、vdot/RVV 候选及 S0 回退同时保留。默认工程入口的切换仍按 R4 组合资格和 T17 的条件处理。

接口及复现命令见 [ENTRY_README.md](ENTRY_README.md)，性能合同见 [ENTRY_CONTRACT.md](ENTRY_CONTRACT.md)，普通 C 功能合同见 [C_API_CONTRACT.md](C_API_CONTRACT.md)。公共源码为 [gemv.S](public/gemv.S) 和 [gemv.h](public/gemv.h)。

## 2. 同一新入口下的实际性能

每个候选格包含 3 个数据集 × 4 个正式 repeat，共 12 个样本。下表单位为平均周期；first/warmup 和重放不重复计入均值。最快 RVV 从同一新入口下的 S0/S1 × basic/reuse 四种 RVV 中选择，本次四个尺寸均为 S1 reuse RVV。

| 形状 | S0 reuse vdot 回退 | S1 reuse vdot | 最快合格 RVV | S1 vdot 相对 RVV 的周期变化 | 采用函数 |
| --- | ---: | ---: | ---: | ---: | --- |
| 4×8 | 178.50 | 169.75 | 187.50 | 少 9.4667% | `r4_gemv_4x8_reuse_vdot` |
| 8×32 | 335.50 | 292.50 | 300.75 | 少 2.7431% | `r4_gemv_8x32_reuse_vdot` |
| 16×64 | 860.00 | 717.25 | 779.50 | 少 7.9859% | `r4_gemv_16x64_reuse_vdot` |
| 4×13 | 219.25 | 219.75 | 187.00 | 多 17.5134% | `r4_gemv_4x13_reuse_rvv` |

### 全部 32 个候选格

| 版本／软件／指令 | 4×8 | 8×32 | 16×64 | 4×13 |
| --- | ---: | ---: | ---: | ---: |
| S0 basic vdot | 216.50 | 658.75 | 2226.25 | 250.50 |
| S0 basic RVV | 328.25 | 489.25 | 1460.50 | 332.75 |
| S0 reuse vdot | 178.50 | 335.50 | 860.00 | 219.25 |
| S0 reuse RVV | 204.00 | 344.00 | 909.75 | 204.00 |
| S1 basic vdot | 206.75 | 648.50 | 2216.50 | 254.00 |
| S1 basic RVV | 225.25 | 356.00 | 991.75 | 230.00 |
| S1 reuse vdot | 169.75 | 292.50 | 717.25 | 219.75 |
| S1 reuse RVV | 187.50 | 300.75 | 779.50 | 187.00 |

测量窗包括参数传递、真实 `jal ra`、完整叶函数、`ret` 和观测指针恢复。函数内部完成向量状态建立、全部输入读取、累加及全部输出写回。夹具自身的寄存器快照和栈帧建立在窗外，双方一致；固定布局的 S0/S1 在四个 8 KiB 计算槽外逐字节相同，公共入口 PC 也配对相同。

这证明固定 GEMV 调用窗中的取舍。普通 C 程序另作功能验证，没有以其总周期计算加速比；这里也没有完整应用或 LLM 端到端收益结论。旧直线内核窗口没有作为本次比较分母。新路径比原 body 多出的退休指令可以精确核对，但旧、新链接布局没有构成独立的纯调用延迟实验，因此不把跨合同周期差称作纯 ABI 开销。

## 3. 验证记录

性能原始档案取得 `R4_ENTRY_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS`，普通C档案取得 `R4_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS`。三份档案的Git完整索引检查均通过。

| 验证层级 | 实际结果 | 可定位证据 |
| --- | --- | --- |
| 性能矩阵 | 24正式＋8重放＋1负控，33个EMU；384正式窗口、192全窗口重放比较 | [矩阵原文复算](evidence/entry-v1-audit-linux.json) |
| 普通C实际调用 | 1负控＋2正常，3个EMU；16函数、48不同case、96正常case执行；每个正常进程1008条vdot提交 | [C原文复算](evidence/c-api-v1-audit-linux.json) |
| 主机测试 | 11＋8＋6，共25项通过 | [测试与命令回执](evidence/entry-runtime-v1/native-commands) |
| 完整Git索引 | 矩阵1381、探针204、C档案110文件，合计1695；均为唯一stage0、100644，清单和blob字节一致 | [矩阵](evidence/entry-runtime-v1/entry-v1-index.json)／[探针](evidence/entry-runtime-v1/entry-probe-v1-index.json)／[C](evidence/entry-runtime-v1/c-api-v1-index.json) |

性能批次先执行最小 8×32/dataset0 probe，再依据仍胜最快 RVV 的结果扩大。完整矩阵使用 24 个 GNU/AM ELF、12 对完整布局，实际完成 24 次正式正常运行、8 次 dataset0 重放和 1 次真实 bit100 负控，共 33 个 EMU 进程。384 个正式窗口与 192 个全窗口重放比较分别统计。

`run-extension-01` 自身不含负控，也不含已经在 probe 完成的 8×32/dataset0 重放，因此实际局部状态保持 `R4_CALLABLE_ENTRY_PARTIAL_PASS`。聚合审计从原始记录验证 probe 与 extension 合计恰好覆盖完整矩阵、没有重复样本、重放发生在对应正式运行之后且不存在性能 EMU 并发。

另在`/home/lizufan/riscv-lab/r4-entry-review-20261024-0623`进行[跨目录原文复算](evidence/entry-runtime-v1/cross-workspace/independent-matrix-audit.json)，报告与原报告逐字段相同，复制的工具源文件未改变，见[比较回执](evidence/entry-runtime-v1/cross-workspace/comparison.json)。该步骤由主Agent `/root` 实际执行，使用部分文件检出和共享Git对象；审查Agent负责源码及报告只读审阅。它没有新增EMU或重新构建外部硬件，不能计作另一执行者的完整T17。

主机测试实际通过 25 项：11 项调用路径/ELF/模型测试、8 项C链接与日志协议测试、6 项探针档案语义拒绝测试；涉及产物的测试使用本轮真实构建和封存文件。主机测试项数与整核执行次数分别统计。普通 C 的独立汇编对象与最终 ELF 的 16 个叶函数逐字节一致，静态模型为每函数 9 组试验；这些静态结果不代替下述实际 C 执行。

普通 C 镜像采用未修改的 AM 默认启动和链接方式，依次调用 16 个公共函数的 48 个形状/方法/数据集组合。判定包括独立标量 C 计算的全部 128 位结果、输入不变、未用区、保护区、CSR 和 5 种软件破坏自检；真实负控后同 BIN 新进程恢复，再重放正常功能。两个正常进程均实际记录1008条vdot提交，全部输出和协议检查通过，96次正常case执行不加入性能窗口。负控在`vd20 / PC 0x800003e0 / word 0x03880a0b`注入bit100，唯一拒错的事件PC为`0x80000404`；同BIN恢复于22:28:12 UTC完成，重放于22:40:32 UTC完成，控制器最终于22:40:34 UTC写出`R4_C_APPLICATION_CALLS_PASS`。

## 4. 固定输入与证据位置

| 对象 | 本次身份／位置 |
| --- | --- |
| 硬件源码 | `6d2abe403b07c297b8830a7d4f06e370b0a8e070`，O2 两槽弹性 FU＋H1 32 位保存 |
| EMU SHA256 | `1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63` |
| 正常 NEMU SHA256 | `efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4` |
| AM 源码 | `086a238062fdfb3281b745a537b361983d0154b5`，构建时只读复用固定 AM/klib 库 |
| 性能档案 | [evidence/entry-v1](evidence/entry-v1) |
| 最小探针档案 | [evidence/entry-probe-v1](evidence/entry-probe-v1)，供无需EMU的语义拒绝测试复核；样本不重复计数 |
| 普通 C 档案 | [evidence/c-api-v1](evidence/c-api-v1)，以性能档案 manifest SHA256 锚定共同来源 |

实际输出父目录为 `/home/lizufan/riscv-lab/r4-entry-20261024-0442`。构建目录为 `build-probe-01`、`build-rest-shapes-01`、`build-rest-datasets-01`；运行目录为 `run-probe-01`、`run-extension-01`；普通C为`build-c-api-01`与`run-c-api-01`。本轮独立 Windows 工作区为 `D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\working-r4-entry-20261024-0442`，原指定入口工作区未改动。

运行前后核对 429 个硬件源文件、21236 个依赖文件、1672 个生成文件及构建/NEMU 来源。档案保存命令回执、原始日志、ELF/BIN、独立汇编对象、源码快照、配置、状态及哈希；大体积外部 EMU/正常 NEMU/flash、工具链和 AM 库以实跑时核验的身份封存。离线审计不宣称重新验证未随档案带走的物理外部文件。

## 5. 失败、修正与保留

准备阶段的一次 WSL shell 路径展开错误在测试启动前退出；随后使用绝对路径的新操作实际执行测试。扩展构建首次外层作业被取消，保留其回执，并实际确认预定输出不存在、没有相关 WSL 构建/EMU 残留后才以新操作启动。没有把取消、未启动或历史 PASS 记为本次成功。

新 C 日志判定使用冻结的严格 observer 解析器保留 UART 字符顺序，并在移除合法观测记录前后均检查失败标记。针对插入记录及被打断失败标记的测试验证该边界；它不声称能还原分散在两条独立 stdout/stderr 流之间的全局字节时序。

两次交给审查Agent的`powershell_propose`长时间未返回，分别在约581.7秒和357.9秒后中断等待；均未调用execute，提案交付状态未知且未盲重提。之后主Agent的跨目录审计启动遇到工具catalog更新拒绝，原回执仍为prepared、没有执行；确认该状态并刷新能力后才以新的短命令启动。上述准备/工具问题不计作EMU运行，实际失败与成功回执见[宿主记录](evidence/entry-runtime-v1/host-command-receipts.json)。

运行器的一个已知状态显示限制：普通C运行期间顶层`status`仍为`PREFLIGHT`，真实阶段以`active_pid`、`active_result`和逐次回执为准，最终收束状态不受影响。为保护已经构建和运行的源码身份，本轮未在途中修改该核心文件；未来如需改善显示，应作为新源码身份做针对性验证。

## 6. 路线影响与接续

本轮闭合的是新 GEMV 调用路径及普通 C 使用范围。硬件 RTL、接口、时钟、复位、时延、吞吐及 ASIC 面积/时序均未改变；没有新增 PPA 结论。完整 MERGE-REG 的功能/异常/控制/DIV/取消资格仍由其有效认领持有者交付，不由本次 GEMV 用例替代。T17 完整干净构建/运行和 R5/G5 默认入口尚须分别完成。

下一步把该明确候选入口与当前固定硬件的相容 MERGE-REG 证据合并审查，再由另一 Agent 或成员在干净目录按完整依赖实际构建、运行、复算。只复用当前固定 EMU 重建软件时，应标为软件复现，不能冒充完整硬件 T17。全部输入与回退命令已列在使用说明，后续不必重新从旧聊天寻找路径。

8×32 在新入口下仅剩 8.25 周期优势，继续加入调度器、布局变更或软件初始化优化时，应先在这个尺寸与同入口最快 RVV 配对检验；不能据旧直线窗口的余量或指令减少量扩大采用。4×13 已有明确较快 RVV，当前没有理由为了统一使用 vdot 而接受退化。
