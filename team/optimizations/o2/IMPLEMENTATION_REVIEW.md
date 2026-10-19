# O2 G1/G2 实现与检查器源码审查

日期：2026-10-19。依据：[O2 设计合同](CONTRACT.md)。

状态：**源码审查完成；本记录不代表 G1/G2 仿真通过，不是团队成员签字。** 审查时 G1 构建由主任务执行，本审查没有启动硬件生成、仿真或全核任务。运行门禁必须另以实际命令、退出码、原始日志、配置和二进制身份确认。

审查工作包括新 FU 实现者的自查，以及对主任务编写的独立 FU 检查器、另一代理编写的父级接入代码的交叉阅读。自动代理之间的交叉阅读不替代两位团队成员对语义、编码或核心接口的人工 ACK。此文件没有代任何成员确认。

## 1. 审查范围与身份

工作分支为 local/o2-elastic-parent-20261019；记录时已提交源码基点为 a7d32f1d03eef251ce7845bb89a8b42cebe096ad。下列摘要固定本轮实际阅读的文件字节；文档后的提交号变化不表示重新编译或重新运行。

| 文件 | SHA-256 |
| --- | --- |
| src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala | 7a146759155840b6fbe4e6b736a3846cf2e3bb66d723c84d529d4cddee104c58 |
| src/main/scala/xiangshan/backend/fu/wrapper/VDotO2.scala | b5fbaef22612a51634f6f77c1a16a93e2df260194581fe1e2a6a22715795f21a |
| src/main/scala/xiangshan/backend/fu/FuConfig.scala | 35cb5475c78a33a613ab70c30f443045473ae1b398062ed2f3799fd2068fea18 |
| src/main/scala/xiangshan/backend/exu/ExeUnit.scala | 901e43c4ae6f17f1ac414d7bae780b457743d0a125ef1730801ccd37d085b4fc |
| team/optimizations/o2/fu/GenerateVDotElasticFu.scala | 74601b2c0097f2da5401b826518a23d910e1f9cb390536cf43215e8684678ff4 |
| team/optimizations/o2/fu/fu_test.cpp | d4dc81c7c206f1d395856023b01a32e76bf1dbef957b9023f8debc0a549bc01d |

同时查阅现有 FuncUnitInput/Output、VecFuncUnitAlias、RobPtr.needFlush、VIDiv/VFDivSqrt 包装及底层 DIV ready 的来源。已有算术单元、ISA、NEMU 与黄金数据没有在本次审查中改写。

## 2. 生产 FU 对合同的实现

| 合同要求 | 源码检查 |
| --- | --- |
| 两份独立身份 | P 保存完整 FuncUnitCtrlOutput、perfDebugInfo 和八个乘积；R 保存完整 FuncUnitOutput，不使用单在途基类的 DataHoldBypass。 |
| 正确槽间移动 | move 使用边沿前的 P；同拍新接受只写 P。R 响应、P 移动、新接受三件事可以同时发生。 |
| 合法/非法及完整结果 | 沿用当前非法配置判断，非法返回零结果和 illegalInstr，抑制 vec/v0 写使能；乘积与归约复用原模块，高 96 位清零。 |
| 逐槽取消 | P/R 各调用自身保存 ROB 的 needFlush，不能把一槽取消扩展为另一槽取消；无关 flush 不清除幸存请求。 |
| redirect/reset 优先级 | redirect 当拍阻止新接受；reset 屏蔽输入、输出、移动及有效 kill 观察，两个 RegInit valid 复位清零。 |
| 反压保持 | R 仅在 move 时写入；R 有效且不 ready 时，只有匹配取消/reset 能撤销旧响应，并有完整输出包稳定性断言。 |
| 实际占用输出 | pipelineStatus 的 pValid/rValid/occupancy 来自实际注册槽状态，不组合屏蔽本拍即将取消的槽，保证父级仍能发出清除边沿。 |
| 配置隔离 | VDOT_O2_ELASTIC 默认关闭；启用时要求 FUSED_INPUT=1、O1_HANDOFF=0，拒绝旧 T12/O1/T13 观察协议。 |
| 框架合同保持 | FuConfig 仅按新开关选择 FU，piped=false、UncertainLatency 与其余 VDot 配置保持原值；旧 VDot 和 Handoff 路径保留。 |

以上是对代码结构与赋值关系的判断。真实最早响应两拍、持续 II=1、取消无丢失以及复位传播均须由 G1/G2 实测确认。

## 3. 父级接入检查

当前接入局限于包含 VDot、VIDiv、VFDivSqrt 的不定时延 VFEX4：

- vdot 占用直接取实际 P/R 槽；DIV 使用独立 busy 与 ROB，不因一笔 vdot 结束就清除另一笔。
- DIV 忙态之外，还检查旧 DIV out.valid 和底层 ready。取消/完成当拍不能直接切换到 vdot，须等待旧输出撤销并恢复接收能力。
- O2 路径局部选择被选 FU 的 ready，子 valid 使用同一 allowInput 和选中条件。父子握手一致、至多一个 child 接受以及输出 one-hot 都有断言。
- 已查 VIDiv.div_in_ready 和 VFDiv.start_ready_o 的底层实现，它们来自注册 FSM。当前“DIV ready → allowInput → child valid”路径没有形成 valid/ready 组合环。
- vdot 时钟使能覆盖实际占用、当前 in.fire 及 reset。满槽被取消当拍仍保留处理清除的边沿；空槽且先前已关钟的 reset 也显式开钟。
- 其他 FU 的门控及非 O2 Dispatcher 路径保留原分支；是否行为回归通过仍以实际旧模式运行结果为准。

必须使用真实 ClockGate 验证低电平锁存、清除边沿、空槽复位后重新唤醒及 DIV 切换；逻辑公式和 Scala 阅读不能证明这些物理时钟事件已经发生。旧 DIV 在取消当拍仍可能输出 valid，本实现按既有合同等待其撤销，不应将该旧行为记作 O2 的幽灵响应。

## 4. 独立 FU 检查器与适配器

fu_test.cpp 的预测状态是 C++ 接受队列与每笔响应可见时刻 due。预测只使用外部 valid/ready、flush/reset、当前周期和已接受请求，不使用 DUT 的 pValid/rValid/occupancy 来更新预期。DUT 状态端口作为被比较的对象。

检查过的关键边界：

1. 周期 t 接受新请求时设置 due=t+2，故首拍 P、下一拍转移、再下一拍 R 才可响应。
2. 第二笔受旧 R 阻塞时，在旧 R 响应或取消的周期，将幸存第二笔 due 调整为 max(oldDue,t+1)。P 只能在该边沿转入 R，不能同拍绕过到输出。
3. 取消先于响应记账；reset 使用边沿前队列长度计算丢弃并清空，避免同笔取消和 reset 重复计数。
4. 任意步检查 accepted=responses+cancelled+reset_dropped+pending，并约束容量与最终排空。
5. ready/valid、R/P 是否应存在、完整 128 位结果、异常、ROB/pdest、写使能与控制身份均与软件预期比较。

已阅读的场景代码包含原 22+10000 向量连续供给、合法/非法交错、满槽反压、接受年龄顺序颠倒、ROB flag 环绕、flushItself 两种取值、部分/全部取消、四种占用形态的 reset/flush 组合及固定种子随机控制。

GenerateVDotElasticFu.scala 的源寄存器顺序、renamed VL 与故意不同的 ctrl VL、27 位控制字段拼接、异常向量和两项 perf 标签映射已逐项核对。ROB 软件取消依据采用 48 项 MinimalConfig 的半环窗口，并拒绝年龄相差恰好半环的歧义测试输入。

## 5. 必须由实际证据补齐的项目

- **完整元数据覆盖：** 独立 FU 适配器只导出 vpu 的 27 位子集和 issueTime/renameTime 两项 perf。父级测试需要实际变化并逐位比较完整 vpu/perf 包，不能将该子集检查看作全部字段验证。
- **负控覆盖：** 当前 FU 检查器提供 identity、wen、high、cancel 四项 C++ 观测值破坏。它们是检查器负控，未修改真实硬件；不能称为生产 RTL 故障注入，也不能单独代表合同列出的全部反例。
- **剩余负控：** 槽身份互换、漏取消、误杀幸存槽、重复/丢失响应、反压改包、父子握手不一致、双 FU 输出、有请求误关钟须由后续测试明确覆盖并区分故障注入层级。
- **真实门控与 DIV：** G2 需覆盖真正 ExeUnit、VIDiv、VFDivSqrt 和 ClockGate，检查两槽满时切换等待、取消与切换重合、最终排空及 reset 后唤醒。
- **运行可追溯性：** 正常运行与每项负控均需保存退出码、预期故障标记、完整结束标记及源码/工具/二进制身份；编译成功不等于测试通过。
- **阶段边界：** 本轮源码审查没有 G3 新 EMU、DiffTest、G4 公平性能、应用加速、Fmax/PPA 或 T17 干净检出结论。
- **人工复核：** 另外两位团队成员对核心接口的人工 ACK 尚待完成，自动审查不签署该项。

## 6. 运行后追加复核清单

后续若实际运行完成，可在相邻工程记录或本节新增带日期的结果链接，保留上述源码审查时点状态：

- 将真实编译源码和上述摘要逐项对照；若有修复，明确哪些文件变化及重新运行范围。
- 核对 G1 的 10022 个原向量、II=1、两拍最早响应、终结守恒、完整排空与每项负控检出。
- 核对 G2 的完整 vpu/perf、所有 FU 切换、真实门控、取消、复位与旧模式对照结果。
- 明确失败的原始运行、修复和新运行目录，保留旧日志。
- 将源码审查通过、真实运行通过、全核未做和人工 ACK 未完成分别列出。

审查结论：当前已阅读源码中未发现需要阻断首轮 G1/G2 构建的功能问题；该结论允许继续实际验证，不提前批准 O2 为最终采用模式。

## 7. 运行后证据（2026-10-19 追加）

上述审查的四份生产源码 SHA 均与正式 G1/G2 输入一致，运行结果已在 [工程记录](IMPLEMENTATION.md) 和 [证据](evidence/20261019-elastic-parent/README.md) 落盘。完整 VPU/perf、16 项父级观察负控、真实门控和旧模式回归已补齐。独立离线复核发现两处检查器缺口并修复，最终 41 项主机测试通过。G3/G4/PPA/人工 ACK 仍未完成；本段没有代替成员签字。
