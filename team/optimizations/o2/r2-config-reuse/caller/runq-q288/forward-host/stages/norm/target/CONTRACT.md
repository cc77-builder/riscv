# W2 + RMSNorm 首 token 完整正确性入口 v1

身份：`r2-s3-w2-norm-first-token-v1`。本目录是团队新派生入口。原
`consumer/target_main.c`、`aux_build.py`、300k probe、W2 和 norm 冻结实验不改。

## 输入及派生

链接已通过本轮八个完整状态 reference 的同一 `consumer-w2-norm.o`，不重编
消费者，不改变四个 K288/K768 FR/TA kernel 或 norm 对象。固定真实模型、五个
模型缓冲区、原始 host gold，状态大小 3,691,424 字节。只有 p0、token 1，
单个冷启动调用，方法 3 FR-cache 与方法 4 TA-cache；同一预处理和 norm 策略。
它不是连续 token、seq=256 或完整应用性能合同。

`build.py` 要求旧 main SHA `15d0fd567415783fc7caf90ffb8ff6ac1ef26199354c791af8feee0060a2fd3f`
与 entry SHA `7db6047a7dfea8a4a1cd98ba95b2845c03405d4fc8aee638463e241da6290531`。
有限字符串替换须能完整反向恢复原文。新增 W2 五缓冲区接口、完整状态前后各
16 字节 guard；成功和失败 trap 都使用实际消费 a0 的 `0x0005006b`。
失败函数保持独立且不克隆，静态 gate 记录唯一失败 PC 和成功 PC。

## 测量窗口与应用验收

每个镜像只调用一次消费者。四次计数器读取顺序为 cycle、instret、instret、
cycle，每次两侧均为 `fence iorw,iorw`。窗口包含完整纯 forward 调用；初始化、
模型绑定初始化、guard 检查、完整状态比较、UART 均在窗口外。调用仍包含该
消费者内部实际执行的绑定、量化、投影及其余计算。绝不将窗口外的工作计入
此窗口结论，也不从 reference 计数推算目标周期。

CSR 原值先写入 report，再校验 TLS/errno=12345、RNE、guard、计数器边界，
随后输出唯一 COUNTERS 行，最后进行负控损坏和完整比较。因此正负控都有
完整 1 窗 / 4 读，可逐值绑定原始目标 counter 记录与 UART。最终 flags 必须
精确等于本轮组合消费者同方法 p0 的参考值。

负控：TA-cache 执行完整正确调用后翻转最后一个 logit 的首字节最低位，
状态偏移 152,476；完整比较必须拒绝，report code=94、byte=152476，实际
BAD trap halt_ret=94。其他字节和两侧 guard 必须精确保持。正控完整状态
逐字节等于独立 host gold，GOOD trap halt_ret=0。错误 trap 不得视为成功。

## 独立 reference

使用既有原版 NEMU 与已合格 adapter，顺序运行 negative、FR、TA、TA replay，
每个独立进程、初始化和镜像，只修改明确的三个控制字并禁用 UART。
最多 100,000,000 API calls、内部 600 秒、外部 630 秒、单文件 128 MiB，
单 CPU。保存完整 report、guarded state、五模型、gold、TLS、controls、
初末寄存器和 CSR；准确核对 terminal PC、所有大小、原始 byte/hash、真实
负控拒绝。TA 与 replay 的完整验证结构必须相等。旧候选 PASS 不转移。

## 目标机运行边界

目标运行另由明确的资源 profile 冻结 guest cycles、墙钟、原始日志上限、
CPU affinity、固定 EMU/reference/flash/seed/RAM、镜像和新入口摘要。profile
必须在 EMU 前写入；不得自动追加预算、截断输出、静默降低观察器或修改官方
程序。保留原 `--log-end=0` profile 的所有裸 O2/T13 日志及 UART/DiffTest。

目标 campaign 的四例均必须独立完整退出、直接子进程回收且进程组消失。
所有原始流经过现有 failure/fatal/runtime gate；只排除精确绑定预期 PC 的
唯一负控 BAD trap。cycle-limit、超时、日志上限、未闭合 ROB/FTQ、未知记录
或其他错误均失败。完整流式协议 gate、精确 ENQUEUE PC/word、退休允许 PC、
完整 4-CSR 样本链与应用 transcript 都须通过；TA/replay 的确定性架构、
counter、协议摘要须相等。具体实现和上限由资源 profile 与 runtime source
pins 共同固定。

本实验所有 `performance_qualified` 均为 false；单冷样本不替代公平多样本
性能合同。`full_retirement_window_audited` 也为 false，因为这里只闭合 custom
协议、四 CSR 和程序完整比较，没有审计全部普通指令的退休窗口。原始失败、
不完整或拒绝结果均保留，不能改名为 PASS。
