# Q288 已封存轨迹的离线成本观察合同 v1

标识：`r2-s3-runq-q288-fused-cost-v1`。2026-10-26，独立叶包 `R2-S3/runq-q288-fused-cost`。

本合同只解释已发布 `fused-target-v1` 的固定合成、预打包完整 Q。输入为原 ELF、manifest、recovery 原始轨迹和原 replay 字节身份；新增 EMU 为零。旧性能选择、旧合格边界和全部冻结源码保持不变。

## 输入与复用

- `evidence/target-v1/archive/payload.zip`：SHA256 `de3afffda86d1db7981d793d17f180b6af879582530d0979fe313bea00170b6c`，44,193,367 字节。
- 同目录 `archive-manifest.json`：`446a6cfb3e4f8ebc55ed2deb555bd46556a73c8c5912a5b5a8e3cfbee156c1c9`。
- 同目录 `original-audit.json`：`92483cb201c667a80da2e806fbc658ae8994eaa81f78efb8bdd086efaed1a60c`；原完整 O2 协议、DiffTest、计数器、ELF 路径已审计。当前工具验证该精确归档身份后复用原审计，不把局部诊断称为新的完整协议审计。
- 当前检出全部 98 项 `build.json.software_files` 必须与封存版本相同，分析前后复核。复用冻结的 `fused/target/run.py::paths_for_plan`、`unified-vdot/check.py`、`fullcore/analyze.py::parse_fields`；额外复用 SHA `e65e4a6056c9059af4a407445e3485256fbd976ad3778a7c24655cb08753015b` 的 `hoisted/context_prefix.py` 纯函数。
- 所有输入只读。输出目录必须不存在、位于检出外。不调用编译器、模拟器、网络或 Git 写操作。
- 稀疏观察语义另外绑定已封存 T17 `matrix-archive/files/hardware/hardware-inputs.json.gz`（stored `614c959f8bc71e11858a35c65b3f0e07eda358cdee5f8643463892e6c312773a`、raw `7c42a8130e71b39e8f5ca08d7d662a85ac58f677040c6293d38007b007ac0dcc`），确认实际构建提交 `34bae6d4acceac939f958199dae53c14bc1f6183`、EMU `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`、ExeUnit pin `166f70c704cc2ec477d316bc5d3ffb40498118e6f8c1c498209fc4b706070f1e`，并与本次硬件profile、parent identity、runtime输入及两个运行回执交叉核对。该链复用原构建/运行证明，不声称再次访问验证原外部二进制。

## 先闭合身份，再统计

全部 12 个计时窗顺序固定为 AR4、AV、AR3、FV、FR、AR4、AR4、FR、FV、AR3、AV、AR4。不得丢弃任何 AR4 锚点。首先从真实 ELF 重建各方法完整 PC/word 路径，核对原封存证书，再逐个核对所有退休记录和原样本值。

计时范围是四次 CSR 采样中间两次的 `[b,c)`，`C=c-b` 必须等于原 cycle CSR 差。marker 范围用于指令路径；instret 的 `[a,d)` 范围独立验证，不与 cycle 区间混用。

每个 AV/FV 窗必须具有 10,368 个完整、唯一、正常退休的 vdot 事务，RVV 窗为零；全阶段 COMMIT 序列恰为 103,681，分别核对 probe、functional、warm 和 timed。真实事务链为 ROB 分配世代/PC/FTQ/word → ACCEPT(seq,ROB,pdest) → RESPONSE(seq,ROB,pdest) → COMMIT(cycle,ROB,PC,FTQ) → T13 RETIRE。ACCEPT 用同拍新分配，COMMIT 用同拍旧分配，不以 seq 或 ROB 单独替代身份。边界跨越显式报告，不裁掉事务来凑数。

## 允许的指标和预定判定

1. **FU 出口背压**：目标事务的 STALL 次数、响应时延、MOVE 位置；`STALL=0` 只否证这些事务的出口背压。全部两拍响应仅证明没有额外 FU 内驻留，不证明减小固有延迟无价值。
2. **FU 供给与占用**：按接受时间排序的间隔和连续逐拍接受长度；P/R 槽占用；父接口 WAIT；同拍 RESPONSE/MOVE/ACCEPT。占用两槽不等于阻塞。`10368/C` 只称全窗接受密度。
3. **已入队但接口尚未收到请求**：对每笔目标事务的 `enqueue<t<accept`，按 cycle 并集统计。仅在该拍观测到 `vready=1, invalid=0, divoccupied=0` 且无父 flush 时归为“接口上游等待”。若实际 T17 源身份完整绑定稀疏 STATE 发射语义，静默拍可单独列为“由固定发射条件证明的空观察域”；否则标为 unknown，不填造 ready/outready。此指标不等于无效等待或可消除周期，不归因为 load miss、vset 或调度缺陷。
4. **消费者位置**：每窗 324 个动态整数 core，按已证实的机器路径位置绑定，每组 32 个 custom。输出各组事务时间包络、程序相邻 custom 的接受时间差和退休前沿位置。程序接受重排必须保留。FV/FR 可标记整数 core、gather、FP 转换/两乘一加的退休坐标；AV 标记原 leaf 出入。退休坐标不是执行起止，退休间隔不能给指令类别分配独占周期。

完整 Q 时间可以显示成“计时起点至首 ACCEPT / 首 ACCEPT 至末 RESPONSE / 末 RESPONSE 至终点”三个相加的包络，但中段包含重叠的载入、配置、FP、控制和其他执行，不称纯 vdot 周期。

## 必要验证

必须验证归档及选用成员的大小/哈希、recovery/replay 原轨迹字节身份、12 窗全部 CSR/退休/ELF 路径、全阶段与目标窗 custom 清单、事务身份唯一和时间顺序、观察到的 STATE 与事务活跃拍一致。诊断只依赖相同轨迹字节时，解析一次并核对 replay SHA 即可；不得称为新执行的重放。

小型反例至少覆盖：同拍旧 COMMIT/新 ENQUEUE、错误 pdest/ROB 的响应、压缩或缺失 custom、CSR tick/值偏移、重叠等待只计并集、活跃拍缺 STATE。反例使用内存中的小事件，不复制或破坏原始日志。真实失败输出保留，新尝试用新目录。

## 结论边界

本工具不授予新性能资格，不改变 R5 默认、RVV 对照或已有 HOLD。只据直接指标决定下一项值得验证的假设。不能将统计相关当成因果，不能把指令减少预测成周期减少；不能将 Q、MAC 数或 VFEX4 可见范围扩大为 token/全模型、全部 RVV/FP 单元、量化/pack、模型质量或 ASIC PPA。
