# C2-G0：复位、取消身份与门控边沿独立审查

执行者：@cc77-builder / Agent（子任务 c2_g0_reset）；2026-10-25，UTC+08:00。只读生产 RTL；输出仅写本审查目录。没有新硬件构建、仿真、EDA、GitHub 写入。

## 结论

当前实际全核配置的复位条件能够建立父子空闲初态，**不依赖 TE=1，也不要求 DIV 门控输出额外跳一个时钟**。全核中的父 divBusy、两份保持状态、整数 DIV 控制 FSM，以及两个浮点 lane 内的 DIV/SQRT FSM 都接同一层级 reset，使用异步置位复位并清到 IDLE。正常运行时 TE 为 0。

“父级同步复位但 DIV 关钟、子状态未初始化”的反例适用于原同步父级夹具，不能据此否决当前异步全核。两种配置应作为不同证明环境保留。

对取消，已确认父子捕获同一接受事务的 ROB；忙期间不能再次接收，子 wrapper 使用保留的 ROB；取消不依赖输入端后来出现的 ROB。释放保持位前的旧保持值保证取消边沿仍到达子核。同一边沿，父 busy 清零，所有活跃子控制 FSM 收到 flush 回到 IDLE。取消与完成同拍、无关 redirect、flag 环绕及 flushItself 都须按相同谓词处理。

这些是主状态不变量证明的输入引理，不单独等于整个 C2-G0 或 RTL 形式证明通过。

## 1. 实际全核身份核验

生产 HEAD：0f12df675378556670afd0dd2153f47fcb330610。

实际 EMU：2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。

从此前冻结构建记录 /home/riscv/riscv-lab/o2-r3-div-gate-fullcore-20261024/build-01/generated-artifacts.json 核验当前 build 的 EMU 和 10 个相关生成 RTL，11/11 SHA-256 完全相同。hardware-inputs.json 记载 source_commit=0f12df6、MinimalConfig、observe profile；生产 ExeUnit.scala 哈希亦相同。没有根据当前随动 build 的名称猜测身份。

证据：[generated-identity.json](generated-identity.json)、[inputs.json](inputs.json)。32 个输入文件前后哈希相同；生产 src 的 git diff HEAD 为空。

## 2. 复位接线与 ready 来源

以下行号均相对生产仓库 /home/riscv/riscv-lab/zjhwork2-review-20261018/repo。

| 位置 | 事实 |
| --- | --- |
| src/test/scala/top/SimTop.scala:62 | SoC reset 为 reset/debug_reset 合成后转 AsyncReset |
| src/main/scala/top/Top.scala:294、309、440–448 | 顶层 ResetGen 异步输出，作为 childReset，核心复位也保持 AsyncReset 类型 |
| utility/src/main/scala/utility/ResetGen.scala:30–46 | 复位异步断言、移位同步释放；输出 AsyncReset |
| src/main/scala/xiangshan/backend/Backend.scala:868–874 | 非 MBIST 配置 cgen=false；不能泛化成任意 SoC 永久 TE=1 |
| build/rtl/Backend.sv:16160、61598–61600 | 当前 MinimalConfig TE=0；vfExuBlock 的 reset 直接透传 |
| build/rtl/ExuBlock_2.sv:880–882 | VFEX4=ExeUnit_17，父 reset 透传 |
| build/rtl/ExeUnit_17.sv:683–706 | 一个 posedge reset 块同时清两份 hold 和 divBusy |
| build/rtl/ExeUnit_17.sv:783–785、868–870 | Vfdiv/Vidiv 时钟分别经 ICG，reset 仍直接接父 reset |
| build/rtl/VIDiv.sv:305–307 | reset 透传至 VectorIdiv |
| build/rtl/VectorIdiv.sv:183–206、154 | posedge reset 把 stateReg 设为 3'h1，ready=stateReg[0] |
| build/rtl/VFDivSqrt.sv:376–378、396–398 | 两个 VectorFloatDivider lane 接相同 clock/reset |
| build/rtl/VectorFloatDivider.sv:112–142 | 每 lane 的 DIV 与 SQRT 子核均接同一 reset；lane ready 是两者 ready 的 AND |
| build/rtl/VectorFloatDividerR64.sv:743–760、1829 | posedge reset 将 fsm_q=6'h1；ready=fsm_q[0] |
| build/rtl/fpsqrt_vector_r16.sv:395–410、947 | posedge reset 将 fsm_q=4'h1；ready=fsm_q[0] |
| build/rtl/VFDivSqrt.sv:238–239 | 总 ready=两个 lane ready 的 AND，总 valid=两个 lane finish valid 的 AND |

TE 的完整连接也由脚本检查：Backend inner_cg_cgen=0 → ExuBlock_2 cg_bore_10/11/12 → VFEX4 cg_bore/1/2 → 各 ICG.TE。不是只检查一个不相关模块的常量。

### 有效初态引理

在 shared reset 有效断言并经过 RTL 事件稳定后：

- B=HI=HF=0；
- VectorIdiv 的状态为 IDLE；
- 两个 FP lane 的 DIV 和 SQRT 都为 IDLE；
- RI=RF=1，所有输出 valid=0。

复位释放不改变这些 FSM 状态；ready 直接组合读取 idle 位，所以不需要先给某个 DIV 子时钟。未复位的数据/ROB 寄存器此时不参与 busy 身份，后续 fire 再共同捕获。这里讨论的是数字 RTL 语义；不声称证明物理复位恢复/移除时间、模拟亚稳态或任意未声明的芯片 reset 序列。

### 同步夹具的不同边界

旧 parent-cost-01/rtl/VectorIdiv.sv:239 只有 posedge clock，没有 posedge reset。ClockGate.sv 的 EN 仅在低相位采样 TE|E；它没有 reset bypass。对一个尚未初始化、状态编码为 000 的同步子 FSM，若父 hold=0、TE=0、没有输入，则即使父经历 reset 时钟，子钟也不跳，RI 可持续为 0。

[reset-edge-probes.json](reset-edge-probes.json) 保存这一事件负控，以及真实异步模式无子时钟也清空的示例。它们是源语义驱动的二态事件例子，不是新 RTL 仿真。未来同步父级夹具若采用 G0 不变量，必须将“有效 reset 子边沿”写进合同；不能以真实全核异步复位证明代替夹具初始化。

## 3. 父子 ROB 一致性与取消边沿

### 接受时建立身份

- ExeUnit.scala:169–170：divAccept=parent fire 且非 VDot，divRobIdx=RegEnable(input ROB, divAccept)。
- ExeUnit.scala:300–333：allowInput 受整个 DIV 占用门禁约束；只选择一个子 FU；父/子 fire 一致性已有断言。
- ExeUnit.scala:582：分发子 ctrl.robIdx 直接来自对应 source.robIdx。
- VecNonPipedFuncUnit.scala:23 与 utility/Hold.scala:65–67：子 outCtrl=DataHoldBypass(input ctrl, child fire)，底层是同 fire 使能的 RegEnable。
- fire 自身开启 ICG，因而同一个合法接受边沿父 divRobIdx 和选中子 outCtrl 均捕获相同值。

### 忙期间保持身份

父 B=1 时 elasticDivOccupied=1，allowInput=0，因此不能有另一个子 fire 覆盖身份。

VIDiv.scala:25–30 与 VFDivSqrt.scala:51–55 在 in.ready=0 时选 outCtrl.robIdx；其结果通过相同 RobPtr.needFlush 下发给子内核。对于实际仍占用的整数状态或浮点 lane 任一未回 idle，总 ready=0，选择的就是被捕获身份。未占用子即使以输入 ROB 计算出 flush，也只在原本 idle 中保持 idle，不会创建新事务。

### 取消/完成边沿先后

父 divCancelled=B && storedROB.needFlush(redirect)。原修复 ExeUnit.scala:126–140 中 releaseUncertain=out.fire||divCancelled，并以“有 fire 优先设 hold，否则 release 清 hold”的方式更新。

合法取消到来前，活动子 hold=1。当前 E=fire||旧 hold 仍为 1；低相位 ICG 采样后，取消边沿到达子状态机。父与子在这一上升沿共同清忙/回 IDLE；之后 hold=0，下一空闲周期关钟。不能把更新后的 hold 错用来判断同一释放边沿已经关掉。

取消与完成同拍时，二者都要求回 IDLE，结果相同；cancel 时 parent flush.valid 阻止新接受，不存在取消旧事务同时覆盖 ROB 的路径。无关 redirect 则两个身份谓词同时为假，不应释放 hold 或 busy。

这一论证依赖常规同步接口约束：redirect/控制在采样边沿稳定，ICG 以低相位采样 E。它不是模拟门控毛刺或 STA 证明。

## 4. 独立可复现检查

运行：

~~~bash
python3 -B /home/riscv/riscv-lab/o2-c2-g0-20261025/review-reset/audit_reset_identity.py
~~~

结果：

- 32 个输入文件读取前后哈希不变；11 个冻结构建产物身份一致。
- 从真实生成 RTL 核对各级 reset、异步块、ready 常量来源、TE 精确层级连接；另检查同步夹具确实不同。
- 对 MinimalConfig 全部 128 个 ROB 编码 × 128 redirect 编码 × valid × flushItself，**65,536** 项独立谓词比较全部一致；含 16,512 kill、128 同指针 self-flush、8,320 flag 不同的 kill。
- 故意把子 ROB 换成旧身份，枚举能检出父/子 kill 分歧，避免“任意取消都算一致”的空检查。
- 保持位 16 行真值表检查中，所有合法“旧 hold=1、release=1、无新 fire”均保留当前清除边沿并关闭下一拍。

原始结果：[rob-exhaustive.json](rob-exhaustive.json)、[hold-edge-check.json](hold-edge-check.json)、[audit-command.json](audit-command.json)、[audit.log](audit.log)、[summary.json](summary.json)。

## 5. 交给总体模型的条件

主模型可以把真实 reset 建模为优先的**共享异步事件**，无条件把父 hold/B 和全部 ready-producing 控制 FSM 置 idle；不需要 TE=1 前提。同步夹具应采用另一初始化契约，并保留 TE=0 且没有有效子边沿的负控。

主模型仍须证明各控制转移（包含独立 lane 进度、浮点 DIV/SQRT 互斥、输出共同握手、取消优先级）保持：B=0 ⇒ RI&&RF。不要以本文件 ROB 谓词枚举或复位检查代替该可达状态证明；也不要把未来门控改写的安全性、综合收益或全核验收归入本次只读结果。
