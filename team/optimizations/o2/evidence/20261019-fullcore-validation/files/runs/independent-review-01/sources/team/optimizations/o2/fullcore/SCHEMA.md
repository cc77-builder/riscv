# O2 全核观察协议 v1

本协议用于 O2 两槽弹性 FU 的 G3 全核验证，默认关闭。启用组合为 VDOT_T14_FUSED_INPUT=1、VDOT_O1_HANDOFF=0、VDOT_O2_ELASTIC=1、VDOT_O2_TRACE=1，且 VDOT_T12_TRACE=0、VDOT_O1_TRACE=0。VDOT_T13_TRACE=1 可同时启用原有全局 ROB/CSR 测量记录；旧 T13 文本格式和代码保持不变。共同仿真复位为前提，ResetGen 必须关闭。非法组合在 elaboration 阶段拒绝。

## 时间、序号与真实状态

全部 O2 时间戳、P/R 序号及 DIV 生命周期观察寄存器位于未门控的真实 ExeUnit 父时钟域。ROB 使用相同复位、相同全局时钟的 GTimer。VDot 子模块的输入、输出和功能占用端口直接读取；P 控制、P perf、逐槽 kill、move、输入合法性通过只读 tap 读取。观察寄存器和 tap 均不驱动功能输入。

seq 是 VFEX4 每次真实父级接受时递增的 64 位观察序号，从 0 开始，包括整数 DIV 和浮点 DIV。P 在真实 VDot in.fire 保存下一序号，R 在真实 move 保存旧 P 序号；同拍新接受不能覆盖旧 P→R 的身份。DIV 使用独立观察序号，保持到下一次 DIV 接受。序号在一次共同复位释放后的仿真 epoch 内唯一。

STATE 是边沿前的真实 P/R 有效位、身份及握手状态。它在 P/R 有效、DIV 物理占用、输入 valid、flush、上一拍任一活动成立时打印；复位释放首次也打印。最后一项活动之后因此至少有一个空 STATE。两个连续活动拍之间缺少 STATE 应当报错；无活动空闲区间可以省略。

解析器须按 cycle 分组，不能依赖跨模块 printf 顺序。按旧状态分别判定 killP/killR、旧 R 响应、旧 P 转移，然后登记新 P 接受。P/R 的响应、取消和在途总数必须守恒，不能只通过累加事件判断成功。

## 精确事件字段

下表前缀均为 O2_，字段顺序固定。十进制数允许 Chisel 补位空白。rob/ftq/redirect 为 flag:value；fu、data、exception、vpu、perf、vs1、vs2、pc、word 为带 0x 前缀的十六进制。slot 是 P 或 R，其余除 clock=global 外为十进制。未知、重复、缺失、截断字段或未知 O2 事件均应拒绝。

| 事件 | 精确字段顺序 |
| --- | --- |
| SCHEMA | version=1 clock=global latency=2 slots=2 rob_size ftq_size vlen=128 vpu_width perf_width |
| STATE | cycle pvalid pseq prob ppdest rvalid rseq rrob rpdest occupancy invalid inready vready outvalid outready move killp killr divactive divseq divoccupied busy |
| VFEX4_ACCEPT | cycle seq rob fu pdest |
| VFEX4_WAIT | cycle rob fu busy |
| VFEX4_REDIRECT | cycle rob self |
| ACCEPT | cycle seq rob pdest vl illegal vecwen v0wen vpu perf vs1 vs2 |
| MOVE | cycle seq rob pdest illegal vecwen v0wen exception vpu perf |
| RESPONSE / STALL | cycle seq rob pdest illegal data vecwen v0wen exception vpu perf |
| KILL | cycle seq slot rob pdest redirect self |
| DIV_ACCEPT | cycle seq rob fu pdest |
| DIV_KILL | cycle seq rob fu pdest redirect self |
| DIV_OUTPUT | cycle seq rob fu pdest ready cancelled |
| ENQUEUE | cycle rob pc ftq word |
| COMMIT | cycle rob pc ftq |
| REDIRECT | cycle rob ftq self |
| RESET | cycle pvalid pseq rvalid rseq divactive divseq |

参数 rob_size、ftq_size、vpu_width、perf_width 从真实配置读取。当前 MinimalConfig 的 ROB=48、FTQ=8。数据始终检查完整 128 位；vpu、perf 按 SCHEMA 宽度逐位绑定。无效槽的序号、ROB、pdest 是未定义/过期寄存器内容，不得当作活跃请求。

STATE 的 invalid/inready 是父级 io.in.valid/io.in.ready；vready 是 VDot 子级 io.in.ready；outvalid/outready 是 VDot 子级 io.out.valid/io.out.ready。occupancy 是真实两槽有效位的和；divoccupied 是功能派发实际使用的 DIV 占用（含输出残留及未 ready），divactive 是独立观察器中尚未完成/取消的 DIV。busy 是真实父级功能 busy。DIV physical 占用可以在逻辑结束后保守多一拍。

ACCEPT 的 vecwen/v0wen 是原请求的写意图。MOVE/RESPONSE/STALL 是实际保存的输出控制：非法指令时两者都为 0、exception=4、data=0；合法时保持原写意图、exception=0。vpu/perf 为整个真实 bundle 的 asUInt，vs1/vs2 为整个真实输入向量，支持在日志端独立复算 signed int8×8 的完整低 32 位与高 96 位。

DIV_OUTPUT 每个实际 DIV 输出 valid 的拍打印，身份来自实际 child 输出，fu 来自该真实 FU 配置。ready=1 且 cancelled=0 表示一次逻辑正常完成。DIV_KILL 表示逻辑取消；若同拍或随后仍有物理输出，DIV_OUTPUT 保留旧 seq 且 cancelled=1，不得第二次终结该请求，也不得算作正常完成。ready=0、cancelled=0 仅表示 DIV 输出受阻。新 DIV 不能覆盖旧物理输出，VDot/DIV 不能交叠占用。

## 取消边界与 ROB 生命周期

O2_REDIRECT 来自 ROB 的 s1_s3；O2_VFEX4_REDIRECT 来自实际 s2_s4 flush。当前固定 CtrlBlock 将后者延迟一拍。分别匹配这两个边界，不能使用 ROB 提前一拍的事件替代真实 FU flush。

ENQUEUE 与 COMMIT 保留完整 ROB、PC、FTQ 绑定，支持重复绕回。ENQUEUE 只记录真正可入 ROB 且没有 ROB redirect 的请求。每项已接收 VDot 应能绑定到相应动态 ROB 分配；已响应但后来被 ROB redirect 清除的请求可以不提交，不能因为未提交就反向虚构 FU kill。两个 P/R 请求独立按 ROB 年龄取消，不能以接受顺序推断年龄。

STATE、MOVE、KILL、STALL、RESPONSE 与父 ACCEPT/WAIT 必须互相印证。无 flush/reset 且下游持续 ready 时，E0 接受、E1 转移、E2 响应，最小延迟为 2 拍，连续接受间隔可为 1。实际整核延迟和吞吐可能受到派发、操作数依赖、写回和软件输入影响。

## 复位与验收边界

初始系统复位没有 RESET 事件；复位释放后只打印一次 SCHEMA。若运行期再次复位，首边沿打印旧 epoch 的 RESET，清除序号和 GTimer，随后从新 SCHEMA/新 cycle=0 开始。当前 G3 完整运行检查器只接受单 epoch，遇到 RESET 或重复 SCHEMA 必须拒绝，不能把多次复位混成一条连续生命周期。运行期复位功能覆盖保留在已完成的 G1/G2 证据中，G3 不增加该项全核覆盖主张。

完整运行要求所有 FU 请求有正常响应或真实取消，ROB 生命周期有提交或实际 redirect 归宿；DiffTest、软件 PASS 标记和精确异常程序独立通过。故障注入导致提前停止的日志只可显式 partial 审计，不得算作完整轨迹通过。仅日志负控不等于真实 RTL 故障注入。

本轮稠密程序用于两槽压力和协议一致性。G3 不产生公平 O1/O2 性能比较结论；应用加速比需后续 G4 使用同镜像、相同窗口、相同参考库和冻结观察协议执行。
