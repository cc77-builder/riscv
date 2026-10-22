# T12 全核控制回归

状态：2026-10-14 完成本机自动回归，`T12_FULLCORE_SUITE_PASS`；人工复核与共享分支发布待办。基线为 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`。本机使用独立本地分支 `local/t12-regression`，未取得或宣称共享分支推送窗口；本轮未向 main、zjhwork、zufan、James_Hotten 推送。

## 范围与完成标准

1. 原有数学模型、组合/FU/解码与全核合法/异常矩阵继续通过，保存各自验证层次。
2. 新程序四组各 512 条 vdot，覆盖 RAW/WAW/v0 别名、VL/CSR 紧邻更新、共享 VFEX4 混合操作和反复 ROB/FTQ 绕回。每组 32 个检查点，每个检查点核对全部 32×128 位向量寄存器；另核对 512 次 vcsr 读回。
3. 256 次延迟条件分支尝试，每次保存完整目的寄存器；硬件观察必须证明年轻指令真实发射并因重定向取消。源程序包含分支，不代表命中取消覆盖。
4. 观察 FU 接收/结果/反压/取消、ROB 分配/提交和共享执行单元等待。要求事务守恒、身份绑定、高 96 位为零、取消指令不提交、ROB/FTQ 多次绕回。
5. 写回反压、FU 内取消等未命中的项记为 `T12_COVERAGE_INCOMPLETE`。不得通过降低门槛或修改期望来消除缺口。
6. 完整保存真实退出码、原始日志、源版本与差异、二进制/参考库/flash/测试输入摘要。失败种子和运行保留，修复后使用新目录重跑。

本轮不涵盖委托/虚拟化、性能比较、综合、STA 或功耗；不能用于关闭 T13/PPA。

## 可观测性

生产 Scala 中的观察代码仅在生成硬件时设置 `VDOT_T12_TRACE=1` 才实例化。代码只读取真实握手、身份和重定向，不改变驱动信号、延迟或仲裁。测试采用真实 MinimalConfig/单核/48 项 ROB/8 项 FTQ，保持断言和 DiffTest。首次启用观察或仅切换环境开关时，必须使用新的硬件输出目录并保存启用参数，因为 Make 不一定把环境变量变化视为构建输入。不能把旧的无观察仿真器当成本轮覆盖证据。本轮修复计数器时先归档旧二进制、源码差异与日志，再由实际 Scala 变化触发完整 RTL 重生成和 C++ 重编，并记录新旧摘要。

硬件 printf 和 UART 使用不同输出路径。运行分别保存 `stdout.log`（UART/宿主消息）和 `stderr.log`（硬件 printf），禁止在采集时合流。`stdbuf` 无法保证加载的运行库不重置缓冲；合流尝试仍发生截断，已排除。`run.log` 仅为明确标注的派生视图，逐字节等于 stderr + stdout；归档保留并分别校验两份原始流。判定器拒绝残缺记录，并在原 stdout 顺序中核对 summary 与 GOOD TRAP。

ROB/VFEX4 的观察计数器每个全核周期递增；FU 使用现有门控时钟，空闲时不递增。依据 `ExeUnit.scala` 的组合 Dispatcher 连接，VFEX4 与选中 FU 的输入握手同拍；`uncer_en_reg` 在接收后保持时钟，直到结果握手（取消后亦不会提前关钟）。判定器将每条 FU 接收与父 VFEX4 的 vdot 接收按身份一一对应，使用事务内门控时钟增量换算全核时间，并检查其位于原 stderr 中相邻全核事件之间。缺父握手、身份错误、时间映射越界均拒绝。原始计数值不修改；不把门控计数直接当全核周期。分层 ResetGen 仍明确拒绝。合成反例只用于验证判定器，并非硬件运行证据。

## 本机运行

```bash
# 完整源码目录中，先激活团队工具环境。
source team/scripts/activate.sh
VDOT_T12_TRACE=1 make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=12G OPT_FAST=-O3 OPT_SLOW=-O0 -j2

export T12_RUN_ROOT=/绝对路径/新的回归输出目录
bash team/scripts/t12-regression.sh build-workload
export T12_NEMU_ROOT=/绝对路径/已验证的vdot-reference检出
bash team/scripts/t12-regression.sh run
```

脚本拒绝覆盖已有构建/运行证据。退出码 2 表示覆盖缺口时，查看 result.json 的具体未命中项。构建/参考来源失败或程序结果错误则不产生通过结论。原 T05/T11 黄金数据保持原字节；T12 使用独立生成器和输出目录。

## 本轮实测结果

最终运行目录为 `/home/riscv/riscv-lab/t12-regression-20261013/runs/suite-final-v4`。2026-10-14 17:48:59 开始，18:42:41 汇总完成（UTC+08:00）。11 项全部满足各自预期；驱动程序真实退出码为 0。证据见 [归档入口](../evidence/t12-regression-20261014/README.md)。

| 验证层次 | 结果与范围 |
| --- | --- |
| 主机检查 | 108 项单元测试通过；含判定器反例、输入独立重放及归档检查。另有原数学模型 35 项及 5 文件一致性通过；xTVAL 策略检查 1,114,256 次。 |
| 组合 RTL | 22 定向 + 10,000 随机，完整 128 位对照通过，含低位/最高位错误注入拒绝。 |
| 独立 FU | 6 类场景、71,258 周期通过；11,245 接收 = 10,960 响应 + 271 取消 + 14 复位丢弃；90 非法配置、25,700 反压周期。 |
| 解码 RTL | 131,109 次事务通过。 |
| 全核控制程序 | 四组各 512 条主序列；128 个全寄存器检查点共核对 65,536 字节，另有 512 次 vcsr 检查和 256 次分支尝试。实际提交 2,157 条 vdot = 2,048 主序列 + 109 条应提交的分支序列；summary failures=0、DiffTest、GOOD TRAP、exit0 全部成立。 |
| 原 T11 功能矩阵 | 8 分片全部通过，117 个唯一用例（80 合法、37 精确异常），实际 124 条记录，重复仅为 D00 对照；56 个自检、24 个 harness 预期拒错。黄金数据不变。 |
| hello/vadd | `HELLO_VADD_PASS`、开启 DiffTest、GOOD TRAP、exit0。 |
| DiffTest 负控 | v10 bit100 注入在 PC `0x80001bdc`、机器字 `0x0294050b` 被准确拒绝，exit1 为预期结果；相同镜像使用正常参考库的完整 shard-0 通过。两者是独立并行进程的配对对照，不是进程内切换参考库。 |

控制回归的硬件事件来自实际接收/响应/重定向，严格核对身份和事务守恒：

| 覆盖项 | 实测 |
| --- | ---: |
| FU 接收 / 响应 / FU 内取消 | 2,250 / 2,248 / 2 |
| 已被 FU 接收后被重定向取消的年轻 vdot | 93（包括上述 2 条 FU 内取消） |
| 正常提交 / 取消后错误提交 | 2,157 / 0 |
| vdot 写回反压事件 | 20 |
| 共享 VFEX4 等待事件 | 6,552 |
| VFEX4 接收：vdot / 其他共享 FU 类型 | 2,250 / 940 |
| ROB / FTQ 绕回 | 214 / 315 |
| ROB 重定向事件 | 318 |

这些计数是本固定程序和配置下的观察覆盖，不是 IPC、吞吐率、加速比或穷尽证明。ROB/FTQ 计数按判定器定义统计；不能以宿主运行分钟数估计处理器性能。

同一压力镜像在 standalone NEMU 上以 exit0/GOOD TRAP 结束；该模式未输出程序 UART summary，仅记为独立执行检查。失败与中断历史见归档的 `historical-attempts.json`，均不计入最终通过次数。

## 固定来源与复核边界

| 对象 | 固定值 |
| --- | --- |
| 开发起点 | `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3` |
| 实际 EMU 硬件源码 | `117ecbf40e107872e046311f556cc4fdf3f733d7` |
| 最终套件及判定软件 | `29949d03fbde84444403593367c174715ba3c25a` |
| EMU SHA-256 | `e879356c4f3ad027a708de3adbabb7285ab6e36196426854040460d1e394b4de` |
| 正常 reference SHA-256 | `efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4` |
| flash SHA-256 | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994` |
| 控制镜像 SHA-256 | `2cbdcc7a7b4b857e6f9a2c63984b1fc5a2a4ec1dce841bad0a703df4892c742f` |
| 正常/负控共用 shard-0 SHA-256 | `b8b7e1a7032070bdfdfc2a747ab6453011ea9959ebd5ac52ca21b439d4d113b3` |

硬件构建于 17:37:31 完成；后续提交只调整采集、判定和文档，生产 RTL 文件摘要在运行前后再次一致。硬件记录中旧 `observation_revision` 文本仍提到 stdbuf，它是构建时的原始元数据；最终采集方式以各项运行回执 `separate-streams-v1` 及两份原始流为准，详见 [时钟与输出问题分析](../evidence/t12-regression-20261014/clock-and-streams.md)。不能把硬件源码 SHA 与最终软件 SHA 混称为一次新的硬件构建。

本轮实际使用 MinimalConfig、1 个核、EMU_THREADS=1、ROB=48、FTQ=8、`VDOT_T12_TRACE=1`。NEMU 基于 `a48a11f208ff81ad765591d83271d1b339fb3861`，团队补丁 1.1.0，显式 NMIE=1/MDT=0 与 invalid-VL xTVAL=0 策略。依赖 SHA、1,209 项依赖文件摘要、生成 RTL 摘要、配置、工具与命令均已保存。日常 Git 只保存可复现源码与压缩证据，EMU/波形/构建缓存仍留在本机输出目录。

离线复核发现 UART 的 CRLF 与在线 `Path.read_text()` 换行处理不一致；修复仅统一文本读取，先核对原始字节摘要，再使用与在线相同的 UTF-8/通用换行读取。新增三个正反例后，主机检查从 105 项增至 108 项。全核二进制、测试输入、原始日志和覆盖门槛均未改变；无需重复硬件执行。离线判定器修复源码为 `73a86544c5175c0eb297df979c92c123cbe39164`。

人工复核尚待其他成员完成，涉及核心文件的观察代码也需按团队约定审阅；本报告不代替真人接口确认。T13 公平 RVV 基线和周期比较、虚拟化、综合/STA/功耗均未完成。下一步先复核本轮提交，再在新的独立工作包中进行固定输入、同镜像、同测量范围的 RVV/vdot 性能对照。

## 全套运行入口与来源

`team/scripts/run-t12-suite.py` 接收已经完成构建的 EMU、reference、控制镜像及 8 个功能分片，逐项检查来源并运行。使用 `--help` 查看全部路径参数；每次 `--output` 必须是不存在的新目录。该入口不代替构建，不覆盖旧日志，默认同时运行两个仿真进程，也支持 `--jobs 4` / `--jobs 8`。本机 WSL 实测约 20 GiB 内存、16 个可用逻辑 CPU，每个仿真实例约 74 MiB RSS；最终运行使用八个独立进程；这仅改变宿主调度，不改变被测单核配置。

固定硬件输入记录包含顶层源码和实际使用的子模块文件摘要、MinimalConfig/单核/48 项 ROB/8 项 FTQ、`VDOT_T12_TRACE=1`、工具版本及构建参数。运行前后均核对 EMU、正常 reference、flash 和测试镜像摘要；正常参考库另经 `artifact_guard.py nemu-runtime` 验证补丁 1.1.0、NMIE/MDT/xTVAL 平台配置与编译来源。

8 个分片使用 T11 原生成器与原数据：`VDOT_LOG_COMPACT=1`、`VDOT_COVERAGE_PROFILE=legacy`、`VDOT_RANDOM_COUNT=32`、`VDOT_SMOKE_RANDOM_COUNT=32`、`VDOT_SHARD_COUNT=8` 和 `VDOT_SHARD_INDEX=0..7`，逐片采用新的绝对路径 `VDOT_DATA` / `TEAM_EVIDENCE_DIR` 执行 `bash team/scripts/vdot-tests.sh build-xs full`。AM 库构建有序进行；仿真可分片并行。新入口严格比较每个分片与原始母用例，确保 117 唯一项、124 实际项，额外 7 项仅为重复 D00 对照。

负控使用仓库既有 `team/evidence/t10-t11-fullcore-20261013/matrix/negative-fixture.c`，链接本轮验证过的正常 reference。它只在返回给 DiffTest 的状态副本翻转 bit100；验收要求对应 vdot 的 PC、目的寄存器、机器字和差分位完全匹配，配对的独立进程使用同一 shard-0 镜像及正常 reference，必须完整通过；最终套件允许两者并行。

离线入口 `team/scripts/check-t12-archive.py` 用于重新核对归档字节、退出码、运行记录、完整 UART/事件日志、负控与恢复、分片并集。调用时显式传入已审阅的源码及 EMU/reference/flash 摘要。离线复核不是重新执行处理器，也不是密码学签名或人工评审。
