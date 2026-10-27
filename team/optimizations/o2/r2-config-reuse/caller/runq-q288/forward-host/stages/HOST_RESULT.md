# 完整 forward 阶段边界与 RoPE 复用：宿主结果

合同：`r2-s3-runq-forward-stages-v1`；基点：`b1d3f136dafae81cf76d2c1f35079cb1465ce7af`。本节依据 2026-10-27（北京时间；原回执 UTC 日期为 10-26）的实际宿主源码快照、命令回执、原始输出、状态文件及封存清单，限定为宿主工程证据，不包含后续 native、NEMU 或 EMU 结果。

**宿主完整功能与阶段接口通过。** `check-02` 完成连续 256 位置的四路完整 forward；`check-04` 完成最终运行器接口的三位置正常、破坏控制、独立重放及 ASan/UBSan/float-cast-overflow 检查。泄漏检测没有取得 PASS。原始失败与未知旧回执保留，后续成功不改变其状态。

下文 `check-01/...` 至 `check-04/...`、`runner-controls-01/...`、`runner-controls-02/...`、`signal-audit-*/...`、`archive-review-*/...` 均是 [`evidence/host-v1`](evidence/host-v1/manifest.json) 的 `payload.zip` 恢复根内的相对路径。封存包的 `manifest.json` 和 `verification.json` 与 ZIP 同组保存；恢复目录名不构成验证身份。

## 1. 验证对象与实现边界

模型为既有确定性未训练 fixture：D288/H768/L6/heads6/kvheads6/V32000/seq256/GS32、种子 `0x53485041`。位置从 0 连续推进，前三 token 为 `[1,7,19]`，之后为 `(pos*7919+17)%32000`；p255 的 token 为 3362。没有下载训练 checkpoint，也没有模型质量结论。

四个方法分别是原样 `forward`、带阶段标记的原算法、带阶段标记的 RoPE 缓存候选、无标记的同一候选。它们共享只读权重，各有独立 RunState。每位置比较全部 16 类状态 span；每份导出状态为 **3,691,424 B**。检查当前 KV 行及所有历史、未来行，检查权重和 embedding 不变，并对验证构建的生成路径执行量化定义域检查。原样 forward 及旧观察器源码未改。

候选唯一算法变化是：每次完整调用内先计算 24 对 FP32 RoPE 角度，逻辑表大小 **192 B**，在本次六层、六头间复用。准备属于完整调用，表不跨位置缓存。矩阵仍为原 scalar matmul；没有混入 TA/FR 有限模型、目标 vdot/RVV 或其计时。

生成器对完整正文执行去标记、恢复函数名和量化调用的源码等式检查；对候选再删除表声明与准备、恢复原角度式。每个被标记调用有 **120 个边界、119 个半开区间**；独立读取 CSV 检查阶段/层标签、相邻端点和首末跨度闭合。证据：各目录 `generation.json`、`forward.inc`、源码快照，及 `check-02/result.json`、`check-04/result.json`。

## 2. 各次运行的实际范围

| 证据目录 | 实际覆盖 | 可采用的结论与限制 |
|---|---|---|
| `check-01` | 普通三位置、连续 256 位置、五项破坏、宿主 timing 和三位置 replay 已有对应输出；sanitized 子进程退出 1 | 顶层 `failure.json` 为 FAIL。LSan 环境错误和未闭合编译回执均保留，不能将整次流程改判 PASS。 |
| `check-02` | 连续 256 位置；三位置 normal/timing/replay/sanitized；五项破坏 | 顶层 `HOST_FORWARD_STAGES_AND_ROPE_CANDIDATE_PASS`；完整 256 位置功能结果的主要证据。sanitized 仅三位置，关闭 LSan。 |
| `check-03` | 各正常项均为三位置，包含名为 `extended` 的项 | 中间报告写 PASS，但 `replay.command.json` 磁盘回执仍为 started；不得作为回执已完全闭合的最终流程。保留实际输出与不一致记录。 |
| `check-04` | 各正常项均为三位置，五项破坏、timing/replay/sanitized | 最终接口 PASS；17 个命令磁盘回执均为 exited，且与实际执行记录一致。不是又一次 256 位置运行。 |

`check-02/extended` 的关键数字：

- 连续位置 **256**，四路完整 forward **1,024 次**。
- 三个生成方法对原方法的完整状态比较为 **12,288 个 span**（256×3×16）。
- 有阶段标记的完整调用 **512 次**，原始半开区间 **60,928 段**（512×119）。
- 每位置在 C 中检查全部状态；完整原始状态文件只保存 p0、p1、p2、p255，而非导出所有 256 位置。外部重新读取所保存的每个位置四份文件逐字节比较。
- p255 四份状态文件各 3,691,424 B，实际 SHA-256 均为 `dc615c2399b14109bcb3540895edf5e431c398e8701f7665ca5ed88a6209bc26`。

每个三位置正常项分别包含 **12 次完整 forward、144 个 span 比较、6 个带标记调用、714 段区间**。`check-04` 的 normal、timing、replay、sanitized 保存状态逐位相同。证据：`check-02/extended.stdout.log`、`check-02/extended.command.json`、`check-02/extended/stages.csv`、`check-02/extended/state-m*-p255.bin`；`check-04/result.json` 及其相应日志、回执和状态文件。

`check-02`、`check-03`、`check-04` 的 `driver.c`、生成器、生成正文以及 validate/timing 二进制身份相同；运行器 `check.py` 有不同版本。故本记录分别采用“同一消费者二进制的 256 位置功能证据”和“最终运行器的三位置接口证据”，不声称最终运行器另做了 256 位置全量重跑。

## 3. 实际拒错与运行器控制

五项消费者破坏均实际执行并以 exit 2 在指定检查拒绝：

| 破坏 | 拒绝理由 | 相对证据 |
|---|---|---|
| 丢失阶段 | `exact boundary count` | `check-04/drop-stage.*` |
| 错误层号 | `exact stage and layer sequence` | `check-04/wrong-layer.*` |
| 错误角度 | `complete state equality` | `check-04/bad-angle.*` |
| 改写历史 KV | `all other KV rows unchanged` | `check-04/historical-kv.*` |
| 状态别名 | `independent state spans` | `check-04/aliased-state.*` |

这里的 `.*` 指同名前缀的 command JSON、stdout/stderr 原文及保留下来的部分运行输出。拒错由对应理由判定，不以任意崩溃替代。

`runner-controls-02/result.json` 为 **RUNNER_FAILURE_CONTROLS_PASS**，覆盖八项：超时、直接子进程退出后仍有进程组残留、中断、已有输出目录、被改坏的参考临时副本、原始阶段路由破坏、真实 UBSan 整数溢出、真实 ASan 堆越界。超时和中断回执记录进程组终止、直接子进程回收；残留控制即使直接子进程 exit 0，仍以 `residual_process_group` 拒绝。ASan/UBSan 负控保留了具体诊断，不能因正常 sanitizer 日志为空就推断检查器有效。控制源码身份与最终 `check-04` 运行器一致。

第一组 `runner-controls-01` 的超时和残留控制有终态记录，但中断控制没有取得终态磁盘回执，`failure-review.json` 明确为 FAIL。其原始 `interrupted.command.json` 保持 started；后来的第二组成功不替换这份记录。

## 4. Sanitizer 与未知回执的处理

`check-01/sanitized-run.stderr.log` 原文包含：

    Can't open /proc/45/task for reading.
    LeakSanitizer has encountered a fatal error.
    LeakSanitizer does not work under ptrace (strace, gdb, etc)

对应子进程 exit 1，顶层流程失败，sanitized stdout 为空。这是实际记录的 LSan 执行环境失败；不能写成泄漏检查通过，也不能仅据这段原文断言程序存在内存泄漏。产生的部分文件同样不能代替成功终态。

后续正常模式显式使用 `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1`、`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`，编译启用 `-fsanitize=address,undefined,float-cast-overflow -fno-sanitize-recover=all`。`check-04/sanitized-run` 实际三位置退出 0、stderr 为空，完整状态与 normal 一致，因此取得该范围的地址、未定义行为和 float-cast-overflow 检查通过；**LeakSanitizer 为 NOT_TESTED**，且不能把三位置 sanitizer 覆盖扩大为 256 位置。

以下三份旧回执的实际终态仍未知或未闭合，必须保留：

- `check-01/compile-timing.command.json`：只有 started，无退出码或结束时间。存在后续 timing 运行产物，不足以补造该编译的原始终态；原因未确定。
- `check-03/replay.command.json`：磁盘文件为 started，而同目录 `result.json` 的内存汇总记录为 exited/0；这是实际不一致，不选择性抹去其中一份。
- `runner-controls-01/interrupted.command.json`：未取得终态回执；不能补造进程清理成功。

`signal-audit-final/audit.json`、`signal-audit-frozen/audit.json` 是后续独立诊断，记录受控中断下 `escaped=false`、进程组已不存在及终态回执；它们不能解释或改判上述旧事件。最终 `check-04` 增加对全部落盘命令回执的存在性、终态和与执行记录相等的检查，实际 17 份回执闭合。遗留的 `.tmp` 文件不作为终态回执使用。

另，`check-01/review.json` 记录其源码快照是在失败后从当时仍保持相同 SHA 的路径补存，全部字节匹配原 `source-pins.json`。应称为按原始哈希恢复的快照，不冒充启动前已经封存。

## 5. 宿主时间只证明接口与阶段闭合

运行环境记录为 Linux x86_64、glibc 2.39、GCC 13.3.0、Python 3.12.14，CPU affinity `[0]`。计时单位是 `CLOCK_PROCESS_CPUTIME_ID` 的进程 CPU 纳秒。验证构建含量化定义域检查，不用于性能；独立 timing 构建取消这些检查，实际日志的 `checked_quantizers` 为 0。

为避免把“约 0.2%”误读成目标份额，下面只列原始 CSV 的宿主描述性汇总：每行合计 p0/p1/p2，包含三个准备区间和十八个 RoPE 层区间。

| 来源与方法 | 六层 RoPE 区间合计/ns | 准备区间合计/ns | 首末阶段跨度合计/ns |
|---|---:|---:|---:|
| `check-02/host-timing` 带标记原算法 | 55,301 | 502 | 29,383,708 |
| 同目录带标记缓存候选 | 8,011 | 5,539 | 28,026,395 |
| `check-04/host-timing` 带标记原算法 | 62,475 | 482 | 36,367,115 |
| 同目录带标记缓存候选 | 7,701 | 46,319 | 29,127,599 |

原算法 RoPE 区间分别约占这两次宿主阶段跨度的 0.19% 和 0.17%。这不是香山占比，也不是正式加速比；缓存准备必须与旋转一起看，不能只挑候选较短的旋转区间。这里没有建立目标公平性能比较、统计稳定性或净因果隔离；阶段标记和计时开销未估算扣除。原始 outer 时间和阶段跨度均保留，不能把它们与别的 BIN、目标 Q 窗或 FU 周期拼接。证据：对应 `host-timing.stdout.log`、`host-timing/stages.csv` 和 `host-timing.command.json`。

这组宿主结果文件明确保留 `target_emu_runs=0`、`target_runtime_ready=false`、`performance_qualified=false`、`trained_model_quality_qualified=false`。这些字段描述本组宿主证据的适用范围，不用于判断其他独立后续实验的状态。

## 6. 核心身份与封存

以下 SHA-256 可直接定位并核对本组结果；完整依赖、命令和库身份仍以每目录 JSON 清单为准。

| 对象 | SHA-256 |
|---|---|
| 原样 `upstream/runq.c` | `ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548` |
| 生成 `forward.inc`，四次一致 | `7c694bcf012871c75330d3a7c32e9b44618286d1daf808d25df8e7728e0400a3` |
| `check-02` 至 `check-04` 的 validate | `fc8ce378d049c9635291e431cf8b05b50b7f0665d78bf856639b7fb68da73236` |
| 同组三次的 timing | `fba95dd133a2b44c7fc8bb071d3f0a20c39fc6d27b3674e8ea6ccea2bb65d6e1` |
| `check-02/result.json` | `efebac807e440e6f719fe458e63436ea19054a820660866a296189c8f1d6c29c` |
| `check-04/result.json` | `111d6b841bff0227732bf7b41036ef27d2d58f6a0b79d19685d0a05623dee8ea` |
| 最终宿主运行器 `check.py` | `0c81b6620b2c417ef73a251899bbe3af0ec4749832dd76ad2631b3e6fbd1386f` |

证据包格式为 `sha256-object-zip-v1`：**696 个文件、原逻辑字节 1,049,692,671 B、248 个唯一对象、唯一对象原字节 30,342,350 B**。ZIP 为 **6,409,832 B**。包括四次宿主检查、两组运行器控制、两份 signal audit，以及修复前后 archive 审查材料；失败、部分产物和未知回执同样封存。

- `payload.zip` SHA-256：`cad1baa7860ff11ee8c80bfb83c15fcc0bf60c8d77ffd204bef7446b3ebc9a9d`。
- `manifest.json` SHA-256：`9863e68d52df57ddac73af2816d3d272b79ffc512e6bc26cdf38b9769db884ed`。
- 封存器 SHA-256：`76c0ebc50b4e288883cf565bdf014dfdf9f344066992de3c6380c044a3df73c7`。

`verification.json` 为 `ARCHIVE_BYTES_PASS`，且明确 `restored=false`、`performance_qualified=false`：该回执证明封存字节检查，不单独证明在某个目标文件系统已经恢复，也不授予被打包运行的工程资格。

收尾复核旧恢复目录时发现两个清单外临时文件，其来源未确定；696个清单内文件仍全部匹配。原目录和两个额外文件保留，随后从相同发布SHA重新解包到新的恢复目录，实际确认696个文件的完整集合与每份字节均相等。新 `host-restore-review-01/restore-verification.json` 为 `restored=true`、`exact_file_set=true`；旧目录观察及额外文件的原字节随交付审计包保存，不回写最初的归档回执。

`archive-review-final/result.json` 记录该封存器的 **20 项小型控制全部按预期结束：17 项拒绝、3 项正控**。覆盖 Windows drive/ADS/保留名/大小写与祖先冲突、相对路径逃逸、对象字节破坏、聚合数量与发布 SHA 错误；正控包含 Unicode/二进制恢复、重复及空文件封存恢复、独立 CLI。测试只对这些具体样例给出证据，不声称穷尽所有文件系统行为。恢复文件仍须按 manifest 的 size/SHA 检查；归档成功不能把 FAIL、started 或中间文件转为 PASS。

本成果建立了可复现的宿主完整状态接续、阶段闭合和 RoPE 复用候选入口。强 RVV、R5 默认、旧合同及所有历史失败保持；目标正确性、真实目标性能和完整应用收益须由独立的最终输入与实际验证另行取得。
