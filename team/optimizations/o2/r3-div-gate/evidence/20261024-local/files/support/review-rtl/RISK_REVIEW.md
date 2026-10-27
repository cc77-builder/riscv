# R3 DIV 取消门控修复：独立 RTL 风险审查

本记录是静态读审；没有修改仓库、没有执行新 RTL 仿真。输入身份见 inputs.json。审查针对当前 O2＋H1 与 James b806ce9c 差异，本轮实现由根 Agent 负责。

## 结论与最小修改边界

方案可行：以 O2 父级已经保存的 divBusy 与 divRobIdx 形成 cancelElasticDivClock = divBusy && divRobIdx.needFlush(io.flush)，仅在 O2 的 VIDiv/VFDiv 门控保持寄存器清除分支加入此取消条件。无需新增 ROB 寄存器，不改变 DIV 数据/结果路径或 VDot 两槽内容。

James 完整改动还修改 legacy 接受及取消路径，并携带 O1 观察器；不应整段移植。本轮保留 legacy 源码分支、接受优先级、VDot occupancy gate，以及原输入排他和输出仲裁逻辑。若使用共享 Wire，必须通过 Scala 构建期条件只接入 O2 DIV 两项；其他 FU 的生成表达式应保持原样。

## 同拍与时钟边沿

1. 当前 ExeUnit.scala 124–127：uncer_en_reg 是父级未门控时钟域寄存器；接受设1，完成清0。取消后无 out.fire，保持位原来就无法清除。
2. 当前 134、149：门控 E 使用旧 uncer_en_reg；不应把 cancel 直接与当前 E 组合相与，否则取消清理边沿会消失。
3. ClockGate.scala 40–44 的 EN 在 CK 低电平时透明。取消所在上升沿，旧保持位仍为1，真实 DIV 状态机可看到 flush；同一父级沿将保持位清0。下一次低电平让 EN 变0，下一上升沿应不再到达空闲 DIV。
4. O2 ExeUnit.scala 297–305 对任何 flush.valid 或 reset 都阻止新接受。因此 cancel 与新 DIV 接受互斥，取消当拍不需引入新“接受即被杀”规则。
5. divBusy/outValid/!divReady 原有聚合保持，确保取消和完成都不能导致同拍跨 FU 接收。允许清除门控保持位不等于删除此排他聚合。
6. 保留接受优先于 out.fire 的现有顺序；现有 O2 DIV 不支持接受/完成同拍，不能借门控修复扩展该行为。
7. VDot 的 E = pValid || rValid || in.fire || reset 必须原样保留。部分取消仍有幸存槽，不能用任何共享 busy/redirect 替代。

## 身份、ROB 与取消覆盖

RobBundles.scala 193–195 的 needFlush 同时检查 valid、flush-self 相等及带 flag 的 isAfter。直接复用它，不能简化为 flush.valid、value 大小比较或 incoming ROB 身份。共享 DIV 父级仅允许一个在途，因此无需每个 DIV 新增 ROB 影子状态。

VIDiv.scala 25–43 和 VFDivSqrt.scala 51–61 在 busy 时使用保存的 outCtrl.robIdx，实际子模块 flush 应与父级已接受 divRobIdx 指向同一请求。VectorIdiv.scala 46–48 在 flush 沿回 idle；VectorFloatDivider.scala 193–195 回 FSM_PRE_0，输出/ready 是状态寄存器的组合结果。浮点 sqrt 同样从 wrapper 接收 flush，实际父级覆盖应保留共享 VFDiv 行为。

严格测试应覆盖：
- 计算中、结果可见、结果反压时取消；ready=0/1；后续 VDot/VIDiv/VFDiv 三种切换。
- 同 ROB+self 取消；同 ROB 无 self 保留；旧请求遇较新 redirect 保留；较新请求取消；ROB flag 环绕两方向。
- 取消当拍必须出现真实子时钟上升沿；紧接下一拍且无新输入/无存活请求时，该 DIV 时钟必须为0，不能设置宽限拍数。
- 保留请求时每个所需子钟不能缺失，最终数据/fflags/ROB/pdest/完整 VDot 128位结果不变。
- 取消之后正常新请求能够重新开钟并完成；接受优先和排他无变化。

## Reset 与边界

保持 RegInit(false) 和现有 reset 行为。本轮不顺带改 DIV reset 门控：当前父级 harness 的 DIV reset 使用 TE=1（parent_test.cpp 470–476），VDot 空槽/满槽 reset 才有 TE=0 严格覆盖。不得把后者扩称为“所有 DIV TE=0 reset 已验证”。若将来需要 DIV 冷态 TE=0 reset，应单列协议与更改。

取消与 reset 同拍时 reset 优先是现有寄存器和 scoreboard 合同；无需为此次修复改变。取消时可能还有原始 DIV out.valid，既有验证允许当拍看到但不会算正常响应；修复必须使状态下一拍清除，不应借此重新定义输出语义。

## 门禁与证据要求

原 parent_test.cpp 452 只累计 cancelIdleClockOn，并没有失败断言；原 check_trace.py 279、304 明确跳过此侧计数重算。严格版本必须同时有在线零额外脉冲门禁与独立原始帧重算。至少需要：
- 旧 RTL＋新门禁出现预期 RED；不能只改最终摘要为0。
- 新 RTL＋新门禁 GREEN，原负例仍拒错，新增漏钟/多钟/计数篡改对照被拒绝。
- 周期级非时钟字段与固定输入旧版一致性比较（如场景扩展导致序号不同，用同一新版 harness 双跑比较），保留原始日志和输入 hash。
- FU 算术和身份/异常验证通过不能代替父级门控验证；本轮父级通过不能代替新组合全核/NEMU 差分、周期、面积、时序或功耗测量。

## 评审状态

设计静态读审：可实施，以上边界应保持。
当前候选 diff：待根 Agent 完成后复审。
新候选 FU/父级执行结果：未在本记录产生。
