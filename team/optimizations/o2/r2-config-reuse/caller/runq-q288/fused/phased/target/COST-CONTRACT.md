# Q288 phased 消费者周期坐标分析合同 v1

合同 ID：`r2-s3-runq-q288-phased-cost-v1`。

本合同在 phased target 的 recovery/replay 尚未闭合时制定。它只复算随后封存的同一批原始证据，不启动 EMU，不变更 target 的选择门槛，不把 replay 当成额外样本。

## 输入身份与复算

输入限 `r2-s3-runq-q288-phased-target-v1`，冻结提交 `34092ebcf579a5de76e70cadfb6a5333173891ae`、build-03、106 项软件源闭包、原 T17 硬件和同一 NEMU。实际 ELF SHA256 为 `bcbe7088f3548813d8ea24fd3a71ce5cb268e7074e7573bb74680d641e5a33b4`；BIN 为 `73bc3a0e8b6d172cb427b09c2f6ff5ca2e0b56c0e0c1617b426cdc20bf84342d`。

先完成原始归档和隔离新进程源闭包审计，再生成只含这些已完成产物身份的 seal.json；调用方显式提供 seal 的 SHA256。seal 的归档三件套、fresh-source result 和固定提交均须匹配。生成 seal 不调整本合同的指标。分析器复核 ZIP 清单、所读原始成员、全部 106 源文件、固定辅助分析器、实际 ELF 路径、8 个 CSR 窗口、124417 条全阶段 custom PC 序列以及 recovery/replay 原始字节一致性。对性能的解释沿用原 target 的 selection。

窗口顺序固定为 `FR,FV,PV,FR | FR,PV,FV,FR`。全部 8 窗口保留；4 个 vdot 窗口各有 10368 条完整事务。其他 4 个 FR 窗口作为实际对照保留。输出写到输入及检出树外的新目录，并保存命令、输入身份、分析器身份、控制结果、失败或成功结果和压缩的逐条坐标。

## 指标定义

1. 沿用已发布 cost.py 的 ROB 代次、seq、pdest、PC 绑定，计算分配 E、FU 接受 A、响应 R、提交 C；复用 source-bound P/R 域观测，不把缺少 STATE 解释成 outready 或整核空闲。
2. 每个 vdot 窗口保留 10367 个程序相邻对：10044 个核内、288 个相邻量化组、35 个 tile 边界。若后项接受时间 N 早于前项 P，保留负差。非负时，以 `clamp(E_next,P,N)` 分成下一条分配前后两段。两段加和等于该对的非负差；不同程序对的时间区间可以重叠，也可以包含其他指令的接受，不能相加成为 bubble 或完整程序周期预算。
3. 从精确动态整数核解码两个实际 load 源、最近一次 vset、逻辑行和 chunk。每次读取必须来自该架构寄存器的最新 writer；遇到中间 dot/add 写入，不能跳过它回找旧 load。先读取两个源再更新目的，支持源目的别名。FV 和 PV 各自按真实指令顺序绑定，不按第 k 条强行视作相同数学项。
4. `expanded_frontier.tick` 是窗口相对值，先加 sample start 恢复全局 cycle。ROB 压缩记录里的多条退休指令共用原观测 cycle，不构造子周期、未知 ROB 身份或实际 issue 时间。
5. 定义 `M=max(E, 两个 load 的退休 cycle, 最近 vset 的退休 cycle)`。统计严格位于 M 与 A 之间的整数周期并集，且必须为 E 与 A 之间等待并集的子集。M>=A 合法，产生空区间并保留有符号差。该指标仅表示这些特定生产者已经退休的保守时间界，不能证明更早的操作数何时就绪，不能归因于 IQ、RF 端口、cache 或 vset。
6. 对上述 M 区间分别报告直接 STATE 的 ready/no-request 观测和独立的 source-bound 空域沉默。缺失 STATE 不进入直接 ready 计数。
7. 记录每组首分配/接受、末响应/提交、整数核退休、浮点转换和累加退休坐标。退休跨度不是该类指令独占执行周期；无 FU 响应阻塞也不排除上游供给限制。

## 控制与接受

保留已发布 helper 的身份反例，并新增：旧分配时间钳位、10/20/12 乱序邻接、最新 writer 拒绝、压缩退休同周期、重叠并集、全局时间平移、M>=A 空区间、缺失 STATE 不构成直接 ready。对实际结果的解释必须同时覆盖 FV 和 PV 两个顺序块；不按结果删窗或改阈值。

结论仍限固定合成预打包 Q。未包含 pack、量化、token、模型质量或 ASIC。R5 默认不变，RTL 不变。
