# T04：当前 hello/vadd 输出与调试链验证合同

- 操作 ID：`20261025-LiZufan001-t04-current-0054`
- 执行者：`@LiZufan001 / Agent`，Pro 负责本轮实现；独立 Agent 只读审查。
- 软件分支基点：`15e0428018b9f9bb1106b6159c522158e1403562`。
- 范围：团队 hello/vadd 程序、运行入口、结果检查器、波形提取器；不修改官方源码、权威参考或判定器，不修改 vdot/整核 RTL。
- 本合同对已完成的生产模型运行作追溯说明，并在首次新 FST 运行前固定波形验收条件。它不是性能实验合同，也不替代 T17 最终组合合同。

## 1. 固定输入及身份

| 输入 | 本轮身份 / 约束 |
| --- | --- |
| 硬件生成来源 | T17 clean-02，源提交 `34bae6d4acceac939f958199dae53c14bc1f6183`；复用完整既有生成 RTL，不重跑 Chisel、不修改生成物 |
| 生产 EMU | SHA-256 `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 普通 NEMU 参考 | SHA-256 `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`；实际始终启用 DiffTest |
| DiffTest 源码 | `62e4540c03c03aa947bdb67f4b6bf66f1a29c5d0`，原样复制到隔离目录，调用官方已有 Makefile |
| 新 FST 模型输入 | `trace-inputs.json` 的 1,807 项逐文件哈希；manifest SHA-256 `7e702810fefa46300ad82424f047d3e584115da0ac95c5a9ca7b23d4683d1db2` |
| 软件 ELF | `ea3f538dceaecfad4b9041f13c4d8953bfa895aed03a63d90cb5c9169abcfd30` |
| 软件 BIN | `d81437b44473cef2b0c5777330e13fd076567d4fc1a4296be35d971e51a4dcad` |
| 共同启动 flash | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994`，12 字节，EMU 与普通 NEMU 读取同一输入 |
| 软件用例 | 既有 `vadd.S` 与三组输入不变；仅更正 hello 的英文输出及身份状态 |
| 身份 | `TEAM_ID=LiZufan001`（已核实的个人 GitHub 身份）；IPv4 来自本轮构建宿主，明确不是仿真核的网络地址 |

新 FST EMU 的文件身份在成功构建 receipt 中记录。开启 `EMU_TRACE=fst` 会生成另一仿真器，不能将生产 EMU 的完整验收自动转移给它；本轮只为该 FST 模型重新验证同一 hello/vadd 镜像。

软件执行输入分两次不可变快照：`workload-source-01.json` 用于工作负载构建及生产模型运行；`workload-source-02.json` 使用相同 main.c/汇编/镜像，并补充完整两相波形选项、提取与工具测试。具体脚本哈希以各 receipt 为准，不把旧脚本执行写成新脚本执行。

## 2. 正确性验收

生产模型与 FST 模型分别必须满足：

1. 正常进程退出码 0、未超时，原始 stdout/stderr 与 receipt 绑定。
2. 普通 DiffTest 明确启用；日志报告的 image/reference/flash 路径匹配本次真实命令。
3. `hello xiangshan, I am LiZufan001, IP address=<构建宿主 IPv4>`，随后输出 `identity_status=configured` 和地址用途。
4. `VLEN=128`、`SEW=8`、`LMUL=1`、`AVL=8`，每次实际返回 `VL=8`。
5. 下列三组各八个字节结果严格匹配、顺序正确、无缺失/重复，最后 `HELLO_VADD_PASS cases=3 lanes=24`，再命中 `HIT GOOD TRAP`。
6. 原始两路日志没有 FAIL/BAD TRAP/断言/差分失败标志；输入 EMU、参考库、镜像、flash 和运行辅助文件执行前后哈希一致。

| 组 | 有效输出字节（低 lane 在前） | 低 64 位 |
| --- | --- | --- |
| 0 | 9 9 9 9 9 9 9 9 | `0909090909090909` |
| 1 | 254 252 250 248 246 244 242 240 | `f0f2f4f6f8fafcfe` |
| 2 | 128 127 0 0 0 0 254 254 | `fefe000000007f80` |

程序使用模 256 的 8 位加法；不验证 tail-agnostic 的高 64 位，也不借此证明 vdot 的宽位累加语义。团队检查器增加证据一致性检查，不能取代普通 NEMU 的实际差分。

## 3. 波形采样与关联

官方 DiffTest `single_cycle()` 在 `clock=1; eval()` 后、`clock=0; eval()` 后分别保存 full 模式高/低相。时间戳为 `H(n)=2R+2n`、`L(n)=2R+2n+1`，其中 R 是复位周期数，n 是宿主循环计数。`-b/-e` 按 trap cycleCnt 筛选，是闭区间；它们不是 FST 的半周期时间戳。

必须使用 `--dump-wave-full`。以相邻前一个低相快照的有效、ready、数据和 tag 作为下个上升沿的采样值；同时检查实际 FU 门控时钟和提交端口时钟的 0→1。窗口首帧没有前一个低相时跳过该沿。所取连续窗口要求相邻时间戳 +1 且 TOP 时钟交替；未知信号或不完整片段不能获得 PASS。

- PC 与机器码由本轮 ELF 反汇编定位。当前实际 `vadd.vv v3,v1,v2` 为 `0x80000138 / 0x021101d7`。
- 从两个可能的 `VialuFix` 实例与 8 个 DPIC 提交槽收集事件，要求恰好三次 FU 输入、三次 FU 输出、三次目标提交。
- FU 输入要求 `fuop=64, vsew=0, vm=1, vuopIdx=0`，实际低八个 lane 输入匹配三组测试向量。
- 当前 `VIAluFix` 的输入控制/数据由父 ExeUnit 的组合 Dispatcher 传递；本拍 tag 在父入口，`ctrlPipe_1` 已延迟，不能冒充本拍 tag。采样时同时验证父 ExeUnit 接收握手，提取其 ROB flag/value/pdest；输入到输出要求这三项完整一致，再检查实际数据和 vecWen/vxsat。
- 输出到延迟提交要求时间顺序、ROB value、物理目的寄存器 pdest 一致，且目标 PC/机器码、vecwen=1、wdest=3。任何多候选或重复使用都拒绝。
- 固定 T17 的 ROB 对 InstrCommit 使用 `delay=3`。DPIC 的 robIdx 是 ROB value 的零扩展，不含 flag；保留 FU flag，但不声称提交端可观察它。结果称“DPIC 提交观测周期”，不把它当作原始 ROB 退休周期。
- 同时保存原始 FST 时戳、前/后沿 ROB trap timer 与选通信号 FST/VCD。波形事件检查单独记录，生成了一个非空 FST 本身不算事件 PASS。

以上定义来自本轮实际检查的固定 RTL/官方源码。若以后更换硬件、层级、提交延迟、用例数量或 FU 接口，应重新建立适用合同；不要为了通过提取而放宽匹配条件。

## 4. 资源、隔离与异常

- 总预算四核：FST 构建 CPU 0–2 / `-j3`；独立软件构建、单线程生产模型和轻量检查在 CPU 3。性能比较不在此并发环境中执行。
- 构建与运行在 Linux 原生目录；Windows 工作树仅用于源码核验、提交和发布，使用 Windows Git。
- 新执行目录必须不存在；重复 action/output 路径会拒绝覆盖。failed attempt、stdout、stderr、状态与超时处理证据保留。
- FST 构建首次因非登录 PATH 缺少已安装 Verilator 失败。保留原始失败日志，第二次显式设置固定工具 PATH/VERILATOR_ROOT；不修改官方构建程序。
- `constantin.txt` 和 `plusArgs` 复制到每次运行自己的 work/build，并通过 NOOP_HOME 指向隔离目录；不依赖隐式旧工作目录。
- T17 生产输入只读，其他 Agent 的 R2-S3/caller 认领仍受保护，进程结束不视为认领释放。

## 5. 工具验证与结论边界

使用实际通过日志和 receipt 做有限反例：错误字节、缺失 DiffTest、截断 trap、重复用例、非零退出、超时、输入/辅助文件变化、stderr 失败等必须被拒绝。用明确标识 MOCK 的临时进程检查空输出、无波形、禁止覆盖和超时清理。这些仅计为工具检查，不增加硬件通过用例数。

波形使用真实事件表做错目的寄存器、错 ROB/tag、错数据、错操作数和缺提交的反例。原始 FST 及提取失败证据保持不变。

本轮不产生新完整应用性能、ASIC 面积/时序、最终组合全套回归、独立成员人工复现或赛事验收结论。它补齐当前 hello/vadd 的可运行入口与可复核调试链。详细结果见同目录 RESULT.md；大体积模型、全量波形和中间构建在运行记录定位，不放进 Git。
