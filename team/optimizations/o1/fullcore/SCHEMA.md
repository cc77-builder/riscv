# O1 观察协议 v1

当前默认选择：`VDOT_O1_TRACE=1 VDOT_O1_TRACE_PROFILE=events`（profile省略时为events）。frames显式选择另一套[原子帧协议](../TRACE.md)，两者互斥。新构建回执必须记录profile，历史缺字段回执只在其冻结检查器下解释。

自刷新`self=1`且目标为已观察存活VDot时，检查FTQ flag/index与分配身份一致。此协议没有FTQ offset，不宣称frames扩展的完整offset/CSR身份覆盖；非self重放不要求相同FTQ来源。

本协议用于真实全核验证，默认关闭。`VDOT_O1_TRACE=1` 要求 T14 fused input、共同仿真复位、`VDOT_T12_TRACE=0`；支持 handoff=0/1。O1 handoff 模式只有启用本协议后才允许同时保留原 `VDOT_T13_TRACE=1` 的全局 ROB/CSR 记录。旧 T12、T13、O0 检查器及历史证据不改写。

## 时钟、序号与旧/新身份

全部 `O1_* cycle` 来自未门控的 ExeUnit 或 ROB 本地 GTimer，共同复位；不再把门控 FU tick 当作 CPU cycle。VDot 的握手、输出控制、结果均读取真实 child I/O，`state/killed/illegalInput/vl` 通过只读 tap 暴露。输出身份取 `io.out.bits.ctrl`，不使用同拍输入会直通的 DataHoldBypass `outCtrl`。

`seq` 为父 VFEX4 每次接受请求后递增的 64 位观察序号，从 0 开始，包含 DIV；VDot 子事件必须与其父记录一一对应，故 VDot 子序号可以有间隔。ACCEPT 使用下一序号，RESPONSE/KILL/STALL 使用接受时保存的旧序号。没有观察信号反馈到功能输入。

解析器按全局 cycle 分组，不依赖跨模块 printf 顺序。同拍先处理旧请求终结，再登记新请求；只有旧 vdot RESPONSE＋新 vdot ACCEPT 能交接，必须有精确匹配的 HANDOFF 和父握手记录。STALL、KILL 不能与新接受组成交接。所有旧/新身份、pdest、写使能、非法标志与完整数据须独立绑定。

## 精确字段顺序

以下前缀均为 `O1_`，空白允许 Chisel 的十进制补位；未知、缺失、重复或截断字段必须拒绝。rob/ftq/redirect 为 flag:value，fu/data/exception/pc/word 为 0x 十六进制，其余数值字段为十进制。

| 事件 | 字段 |
| --- | --- |
| SCHEMA | version=1 clock=global latency=2 rob_size=48 ftq_size=8 vlen=128 handoff=0或1 |
| VFEX4_ACCEPT | cycle seq rob fu pdest |
| VFEX4_WAIT | cycle rob fu busy |
| VFEX4_REDIRECT | cycle rob self |
| ACCEPT | cycle seq rob pdest vl illegal vecwen v0wen |
| RESPONSE / STALL | cycle seq rob pdest illegal data vecwen v0wen exception |
| KILL | cycle seq rob pdest redirect self state |
| HANDOFF | cycle oldseq newseq oldrob newrob oldpdest newpdest busy |
| ENQUEUE | cycle rob pc ftq word |
| COMMIT | cycle rob pc ftq |
| REDIRECT | cycle rob ftq self |

SCHEMA 在父级复位释放后只打印一次，参数读取真实配置。ROB REDIRECT 来自 s1_s3，VFEX4_REDIRECT 是真实 s2_s4 flush；当前固定 CtrlBlock 将后者延迟一拍，解析器分别匹配两个边界。不能因同拍出现 ROB REDIRECT 就拒绝尚未收到 flush 的父级接受；禁止接受/交接的是真实父级 flush 当拍。取消自身由 self 表示，年龄计算保留 flag 绕回。

## 验收层次

一般轨迹检查验证结构、父/子绑定、旧/新身份、响应/反压时序、事务守恒、ROB 生命周期和真实重定向对应。正常完整运行不接受悬空事务；bit100 故障注入导致的主动终止只允许显式 partial 审计，不能标作完整轨迹通过。

控制回归继续要求原 T12 的每项覆盖：年轻请求取消、FU 在途取消、共享 VFEX4、写回反压以及重复 ROB/FTQ 绕回；另要求实际 O1 同拍交接证据。数值与精确异常由冻结程序和正常 NEMU DiffTest 判定，bit100 负控必须匹配故障 PC、目的寄存器和位差，再用正常库运行同一镜像恢复。

T13 全局记录可以继续由原窗口检查器验证；旧 `fu_statistics` 和 O0/T12 mapper 不能解析本协议。本轮的稠密点积运行用于交接压力与窗口/程序一致性，不代替之后同镜像 T14/O1 性能 A/B 或物理时序验证。
