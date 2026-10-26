# 数学入口、完整参考消费者与 RoPE 目标阶段结果

## 结论与实际资格

本轮完成了数学/TLS 的 5 次 T17 EMU 运行、完整 scalar/RoPE-cache 双消费者的 4 个 NEMU 参考进程、完整 scalar/强 RVV/TA 三消费者的 4 个参考进程，以及 RoPE 局部边界的 4 次 T17 EMU 运行。固定模型的三位置完整状态已经有实际 RISC-V 参考执行证据；完整投影消费者尚未获得香山整核 DiffTest 或完整 token 周期资格。RoPE 的功能、应用负控和精确重放通过；后续对固定 T17 的实际 Fence/Decode/Dispatch/ROB/CSR 源码及四次原文计数器链完成复核，取得本文限定的局部计时资格。另行开发的两处真实投影目标边界见 [projection/target/RESULT.md](projection/target/RESULT.md)，其资格独立于本页的完整参考结果。

本页依据各 campaign 的原始 JSON、binary、stdout/stderr、冻结源码及迁移后原文复算。所有日期为 2026-10-27 北京时间；原回执保存 UTC 时间。源版本、artifact SHA 和恢复方法见 [交付总览](RESULT.md) 与 [README](README.md)。

共同模型为确定性、未训练的 D288/H768/L6、heads6/kv6、GS32、V32000、S256，seed 为 `0x53485041`；完整参考验证使用连续 tokens `[1,7,19]`。这些是固定 fixture 的工程正确性证据，不是训练质量或任意输入域的证明。

| 实际 campaign | 独立进程及正常工作量 | 实际回执与资格 |
|---|---|---|
| `smoke-campaign-01` | 5 个 EMU；正常、错误 golden、真实栈保护失败、恢复、重放；正常各 24 个数学输入 | `MATH_TLS_DIFFTEST_CAMPAIGN_PASS`；固定输入数学/TLS 探针资格 |
| `full-campaign-01` | 4 个参考进程；正常、bad-state、恢复、重放；正常各 3 位置 × 2 消费者，共 6 次完整 forward | `FULL_RISCV_REFERENCE_CAMPAIGN_PASS`；目标 EMU 次数为 0 |
| `projection-campaign-01` | 4 个参考进程；正常、bad-tail、恢复、重放；正常各 3 位置 × 3 消费者，共 9 次完整 forward | `FULL_PROJECTION_REFERENCE_CAMPAIGN_PASS`；目标 EMU 次数为 0 |
| `rope-campaign-01` | 4 个 EMU；负控先完成，再在 CPU 0/1/2 各启动 normal/recovery/replay；每个正常进程 4 个 ABBA 样本 | `ROPE_STAGE_DIFFTEST_CAMPAIGN_PASS`；固定 T17 的 p2 六层合并局部计时，范围见下文 |

以上“参考进程”是通过团队 adapter 执行固定原样 NEMU 共享库，不应计作香山 EMU。恢复和重放是独立进程，不能扩充为更多正式性能样本。

## 1. 数学库与单 hart TLS 闭合

普通 archive 选择得到的最小数学闭包进入了真实目标执行。十个入口为 `powf/sinf/cosf/sincosf/expf/sqrtf/roundf/round/fabsf/fabs`；24 例包括 16 个正常输入和 8 个 domain/range 输入。正常有限结果逐位核对宿主原始参考，错误 NaN 按合同检查 binary32 分类并保留原位模式，未把宿主与目标 NaN payload 强制等同。

实际 transcript 为 `MATH_PASS cases=24 errors_checked=8 guard_checks=24`。TLS errno 偏移为 0，正常例保留 sentinel 12345；domain 例返回 errno 33、NV，极点例 errno 34、DZ，溢出与下溢分别记录 OF|NX、UF|NX。目标每例先清 fcsr，检查 RNE、required/allowed flags、tp 及 TLS 两侧 guard；因此不授予其他舍入模式或非零 sticky 输入的资格。

错误 golden 必须在首例产生 `MATH_REJECT 0 result`，真实 stack protector 路径必须产生 `MATH_STACK_GUARD_REJECT`；二者以预期 BAD TRAP 失败。正常、恢复、重放的完整原始结果必须相同，并通过未修改的 DiffTest。campaign 回执记载 5 次新 EMU，终态无 active PID；运行限额为每次 100 万 guest cycles、1,200 秒，使用一个宿主 CPU。该结果闭合所需数学/TLS 入口，不自动证明完整 forward。

## 2. 完整 scalar 与 RoPE-cache 的参考执行

原 AM startup 在固定参考配置下触及未提供的 UART。诊断已定位 store access fault；因此采用团队自有 memory-only entry，保留官方链接脚本、预编译 klib/libm、NEMU 及其指令判定。入口初始化本程序的栈、FP 状态和单 hart TLS，没有模拟 UART、跳过指令或回写参考 CPU/CSR。

原始 scalar forward 与只改角度复用的 RoPE-cache 候选共享模型，分别拥有完整独立状态。每位置实际运行两者，每个状态包含全部 16 spans、3,691,424 B；正常进程导出六份状态共 22,148,544 B，并对照独立宿主原 forward 逐字节检查。每位置 120 个候选阶段事件，共 360 条，顺序也纳入验证。192 B 角度表在每次 forward 内准备；此版所有矩阵仍为 scalar，词表、KV 容量、attention、非线性和 classifier 均未缩减。

实际正常回执为 `FULL_RISCV_REFERENCE_HOST_BITS_PASS`，3 个位置、6 次完成调用，六次最终 fcsr 均为 1。参考 API 调用 817,244,797 次、退休 817,244,796 条，这些数值用于复现与运行限额，**不是香山周期**。完整权重和 embedding 的最终转储与输入相同；这证明终态字节未变，并不构成逐次 store 的动态审计。

bad-state 仅翻转首位置候选第一个 logit 的一位，要求在对应状态比较失败、halt 84；后续位置保持未执行状态。正常镜像的恢复和重放须复现全部状态、阶段事件、flags 及参考退休计数。每进程限额为 20 亿 API 调用、内部 1,800 秒、外部 1,830 秒、单输出 128 MiB。本结果建立完整参考消费者数值资格，未测香山完整应用周期。

## 3. 完整 scalar、强 RVV 与 TA 三消费者

`projection` 使用三份独立状态，运行原 scalar、`q288_fused_rvv4` 和 `q288_tail_vdot` 消费者。此版不叠加 RoPE cache，仍保留原量化公式和每行 group0…8 的 FP32 运算顺序。最终 ELF 的两个完整内核函数体由构建门禁与旧合格 ELF 逐字核对；本轮实际消费者执行为这一新包装提供证据，旧 PASS 不能替代它。

37 张 K288 矩阵真实路由为 172 次原 Q288 调用，6 张 K768 W2 保留 scalar。每个候选 forward 的实际计数为：

| 量化调用 | GS32 组 | 量化元素 | 总矩阵 | K288 路由 | scalar W2 | Q288 块调用 | 尾块 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 25 | 315 | 10,080 | 43 | 37 | 6 | 172 | 13 |

192/32 行尾部使用完整 288 行 scratch 补零权重、补 scale=1，仍调用同一完整内核，再复制有效行；每次 forward 多执行 405,504 MAC。约 91.262% 是原 int8 MAC 的 K288 覆盖率，既不是周期占比，也不是完整 forward 加速比。

正常进程的九份完整状态均与独立宿主原 forward 一致，三个最终 live state 也逐字核对。每个 routed 输出另与原 matmul 对同一真实 q/scale 的独立结果比较；同时检查量化域、向量 CSR、8 个完整 128-bit slot（共 128 B）、尾填充和 guards。packed 权重与 tail scales 由外部重建核对，原模型和 embedding 的最终字节不变。实际正常回执为 `FULL_PROJECTION_REFERENCE_HOST_BITS_PASS`，参考 API 调用 1,399,494,055 次、退休 1,399,494,054 条，仍不计性能。

bad-tail 翻转首个候选 classifier 尾块最后有效输出的一位，必须通过真实复制进入 live state，并在行 31,999 拒绝、halt 94。后续消费者和位置不得伪装完成。恢复、重放要求原始状态、counts、flags、内存摘要及退休计数一致。该镜像包含逐矩阵重算和大规模转储等验证开销；未获得完整消费者香山 DiffTest 或性能资格。W1/classifier 尾边界另有新合同和独立目标结果；不能由其局部结果替代这里完整消费者的整核资格。

## 4. RoPE 实际 EMU 范围与原始样本

输入合同从完整原 forward 的真实边界捕获六个指定位置；本轮 EMU **只执行 p2**。每次完整处理六层各 288 个 Q/K、共 13,824 B，缓存每次准备 24 对 FP32 角度。六层旋转紧密串联，不等同于完整 forward 中与 GEMV、attention 等交错的缓存环境。

每个正式样本先执行同方法完整 selfwarm，再恢复输入；计数窗口包含完整方法和缓存准备，输入恢复、全字节比较、guard、摘要、UART 位于窗口外。实际 ABBA 原始数据如下，保留旧 wrapper 成本，不扣估值：

| 样本 | 方法 | raw cycles | raw instret | fcsr |
|---:|---|---:|---:|---:|
| 0 | 原角度计算 | 140,157 | 175,270 | 1 |
| 1 | 角度缓存 | 19,045 | 31,327 | 1 |
| 2 | 角度缓存 | 19,010 | 31,327 | 1 |
| 3 | 原角度计算 | 140,045 | 175,270 | 1 |

每个正常进程报告 `ROPE_PASS samples=4 full_comparisons=8 bytes=13824`，摘要均为 `fc0e4ddf78da5b5c`；摘要用于外部核对，逐字节正确性来自目标端八次完整比较。normal/recovery/replay 的全部样本、counter、fcsr 和摘要须精确相同。

bad-output 在首个缓存正式样本完成后翻转输出首字节，按指定 `ROPE_REJECT 1 result 0` 拒绝，EMU 退出码 1。随后三个正常进程各自退出 0，四份回执均记录进程组已消失。这是应用输出比较负控，不能称为新增官方 DiffTest 架构差异注入。运行限额为每次 600 万 guest cycles、7,200 秒、单输出 128 MiB。

后续 `rope-counter-recheck-01` 对四份完整原文执行独立 counter 审计：正常每次 4 个窗口、16 条 CSR，负控 2 个窗口、8 条 CSR；逐条把最终 ELF 的 PC/指令字、enqueue、sample、retire 绑定。CSR 只读、ROB 身份、采样与退休值、emptyROB 和时间顺序均通过；对已经打印的样本核对 UART cycle/instret 差分，负控第二窗口没有 UART 样本，只保留完整 counter 链。每个窗口 cycle 的模 2^64 差分还与独立全局周期区间一致。三次正常的完整链与样本完全相同。实际 counter enqueue 的 wait/block 为 0/0，未冒充 1/1；也没有追踪窗口内每一条中间退休指令，`full_retirement_window_audited=false` 保留。

旧 ELF 使用 `fence rw,rw`。固定 T17 源码中，Fence 单元并不按 pred/succ 掩码区分行为，统一等待 store buffer 清空后结束；FENCE 解码为 noSpec/blockBack/flushPipe。结合真实 counter 链，这支持**此固定 T17、此 ELF、p2 同方法自预热六层合并边界**的周期与指令计数。源码全文及 SHA 保存在 `timer-hardware-01`，实际核源 HEAD 为 `34bae6d4acceac939f958199dae53c14bc1f6183`，捕获时 tracked status 干净。这是实现特定的复核，不能把 RW 围栏泛化成所有 RISC-V 实现的计数器排序保证；新投影合同单独使用 IORW 围栏。

本窗口平均周期从 140,101 降至 19,027.5，约 7.36 倍；该比值只描述表中两个 ABBA 方法的局部原始均值。准备已计入，固定 no-builtin 编译政策与 wrapper 开销保留；它不表示最佳通用非缓存实现，也不能换算为完整 token 收益。输入、编译政策、timer 或边界改变后必须建立新身份重新验证。

## 5. 失败、复现与证据索引

原生证据根目录为：

`/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/forward-stages-20261027-0300`

以下均相对此根目录。以下成功、失败与中间版本均保留原回执；归档只证明原字节，不改变运行状态。

| 路径 | 用途 |
|---|---|
| `smoke-campaign-01/` | `state.json/results.json/runtime-inputs.json`；`runs/{normal,bad-golden,bad-guard,recovery,replay}/` 的 result、validation、stdout/stderr |
| `full-campaign-01/` | 正常/bad-state/恢复/重放的完整 report、snapshots、events、模型转储、reference-result、ABI 与寄存器/CSR |
| `projection-campaign-01/` | 正常/bad-tail/恢复/重放的九状态快照、live states、counts、packed/scales、模型、参考回执 |
| `rope-campaign-01/` | `runs/{bad-output,normal,recovery,replay}/` 原始日志、进程记录、validation；独立保留其冻结 build 与 runtime 输入 |
| `native-core-meta-01/{summary,post-run-inputs}.json` | 三个 core campaign 汇总；运行后分别核对 104、90、140 个输入文件仍相同 |
| `smoke-build-01/`、`smoke-build-02/`、`smoke-build-03/` | 前两次错误地按 section 存在性拒绝全零 R_RISCV_NONE；03 修正为逐字节惰性占位检查，01/02 的原失败继续留存 |
| `reference-smoke-01/`、`reference-diagnostic-02/` | 原 runner 180 秒超时和完整 PMA 原文；诊断在第 88 次 API 调用、87 条退休后定位 UART store，mcause=7、mtval=`0x4060000c`、mepc=`0x8000141c` |
| `reference-adapter-03/`、`reference-adapter-04/` | 03 为中间产物；04 封存实际编译回执、argv、源码/依赖/配置与最终 adapter binary 身份 |
| `full-build-01/`…`full-build-06/` | 01–05 的失败/中间输入和回执不覆盖；06 为本次完整 scalar/cache 最终构建 |
| `projection-build-01/`…`projection-build-04/` | 01 曾因 TLS 地址比较优化丢失主体；02/03 中间版本保留；04 为本次三消费者最终构建 |
| `rope-build-01/`…`rope-build-05/` | 前四版失败/中间输入保留；05 为实际 campaign 的冻结构建 |

不能把修复后的成功回填为旧失败成功，也不能因 raw 日志较大而删去失败证据。核心证据归档 `native-core-evidence-01` 的实际记录为 1,341 个文件、581 个独有对象、payload 208,708,000 B，已完成全量恢复核验；**该核心归档不含 RoPE**，后者与新投影目标证据另行封存，见 [交付总览](RESULT.md)。数学/完整双消费者/三路投影已从搬迁后的恢复目录，用 campaign 冻结验证器重新判定全部负控与正常结果，且完整正常/恢复/重放值相等；此复算没有启动新 EMU/参考进程，也没有重新检查原机物理硬件身份。

本轮可继续采用的成果是已实际执行的数学/TLS 入口、固定三位置完整参考消费者，以及上述限定范围内的 RoPE 功能与局部计时结果。若要取得完整投影消费者的应用性能资格，还需完整调用链的香山执行与公平计时；是否立即投入应依据验证成本及可解决的问题决定。所有已冻结输入、原始回执和失败证据保持原身份。
