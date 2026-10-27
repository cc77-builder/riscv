# C3-G0 协议与最小候选独立审查

2026-10-25，Agent 只读审查。**建议仅保留一次有界 C3-HF 试验机会：从 0f 出发，只改变浮点 DIV/SQRT 的保持寄存器置位来源；整数、门控输出式、共用 busy/ROB、实际握手全部保持原样。** 本轮没有生产 RTL 改动、EDA、EMU、Git 写入；C3 的 RTL 功能、面积、STA、全核及周期全部 NOT_TESTED。

这不是从 C2 恢复采用。0f 双 hold 的状态结构保留，C1/C2 的 owner 替换不继承。成本成功与否仍未知，任何新映射都可能重排全父级。

## 1. 候选的准确边界

记 F 为浮点子单元的实际 in.fire，H 为原浮点 uncer_en_reg，C 为原 out.fire OR elasticDivCancelled。只针对 O2/VFEX4 的 vfdiv 配置提出：

~~~text
P_F = parent.inputValid AND selectedFloatingDIV/SQRT
      AND NOT divBusy AND NOT anyDIVoutValid
      AND NOT VDotOccupied AND NOT flushValid AND NOT reset

原保持：H_next = reset ? 0 : F OR (H AND NOT C)
C3-HF：H_next = reset ? 0 : P_F OR (H AND NOT C)

时钟不变：E_F = F OR H
~~~

伪方程表达候选，不是生成的 RTL 补丁。实现时仍须保留 Scala when 的原接受优先级以及 RegInit 的复位优先级；不要把 P 用作实际事务接受、ROB 捕获、child.valid、parent.ready，或取消/完成判定。前向访问 divBusy/outValid 可用预先建立的只读 Wire，禁止重复保存新状态、重复独立 ROB 或改变实际协议。

更大的 FP gate+hold 候选把 E_F 也换为 P_F OR H。它在同一有效域也有控制等价依据，但新增第二处消费点，且改变真正 ICG E 逻辑锥，因此不作为本轮首选。双 DIV gate+hold 又扩大整数范围，没有当前必须改变整数 hold 的实测依据。仅改 gate 不改 hold 则直接目标仍在 hold 更新链，优先级更低。

## 2. 为什么它有具体结构依据

旧 nominal 原文记录：FP hold.D 最差 1.930584 ns，INT hold.D 为 1.506153 ns，divBusy.D 为 0.870094 ns。原门槛 1.737526 ns 只被 FP hold 超过。保存的 ROB Q、flush ROB 输入、flush level 到 FP hold.D 分别 0.505119、0.610073、0.269579 ns；这些是既有来源限定报告，不是新 C3 数据。

旧 FP hold.D 最差报告经过同时馈入 ICG.E 的共享组合/缓冲网络。mapped.json 的 net 103659 同时连接 OR2 输出、NAND2 输入和 dut.ClockGate.impl.E，直接连接证据见 old-hold-shared-net.json。原报告可见 18 个 BUF，总 BUF 弧 1.344565 ns。没有把该网络描述为穿过 ICG E→GCK 数据弧，也没有据此推算新 Fmax 或可消除的固定延迟。

旧 D=F OR(H AND NOT C)，E=F OR H，在布尔表达式中允许 D 与 E 因子复用。新 D 的 P 不含 ready，而实际 F 仍含 ready，二者仅在已证明的可达域等价，完整布尔空间不等价；这使慢 fire/ready 网络不再是 hold 置位函数的必要输入，是一项新的、可解释的结构假设。

这不意味着 ABC 一定拆除旧共享缓冲。P 与原逻辑仍共享 busy、outValid、VDot、flush 等来源，可能产生新的扇出或被重组；release 输入也仍可能成为最坏项。C2 已证实局部缩短不保证整父级通过。因此建议只有一次固定候选筛选，不更改约束、阈值、false path 或随机改写表达式寻优。

## 3. 协议等价与边界

复用已封存 C2-G0 的真实实现不变量：有效初始化后的非复位稳定采样点，NOT divBusy 推出 INT ready AND FP ready。它使用独立的 divBusy，不把含 NOT ready 的 elasticDivOccupied 定义当证明。

原 dispatch 在没有 busy、输出、VDot 占用、flush、reset 时，实际 FP fire 等于 P_F AND RI AND RF。因此在不变量域 P_F=F。H 初值相同，每拍 reset、release、F/P 相同，归纳得到 H 全程相同。C3-HF 的 E 原式完全不动，故清理时钟与旧版相同，子 FSM、实际接收、输出、ROB 身份的相等保持。这里没有假定新 RTL 自动实现了该方程。

需要保持的边界：

- **共享异步复位**：旧真实全核父子共享异步 reset 已由 G0 的冻结生成物核实；不能把同步成本夹具直接当全核复位合同。
- **同步夹具**：需要初次有效 bootstrap。已有效初始化后，TE=0 动态复位仍由旧 hold 保留活跃子的清理边沿。本轮也检查了 reset 与 valid 同时有效，实际握手仍被原 reset 掩蔽。
- **取消**：保留原匹配 ROB 的 cancellation；不能将任意 flush 当 kill，不能把 kill/flush 直接屏蔽 E。取消拍使用旧 H，下一空闲拍才关钟。
- **响应反压**：原 H 等待真实子 out.fire；不能以 out.valid 释放。父级继续等待实际物理输出撤销。
- **双 lane**：两 lane ready 和输出各按 AND 汇合；一 lane 提前完成不能释放忙态。SQRT 与 DIV 共享 cfg.fuType==vfdiv，P 的 selection 必须包含二者，不能只匹配浮点 DIV opcode。
- **ROB 与同步域**：父 divRobIdx 与 wrapper outCtrl 仍只在同一真实接受边沿捕获；P 只写 ungated parent hold，不新增跨域反馈。物理门控毛刺、复位恢复/移除不是抽象证明范围。
- **不合法初始化**：保留 B=0 但 integer RUN 的反例。此时 P_F 可为真而真实 fire 被 all-ready 阻止；不能删除有效初始化前提，不能用模拟器默认 0 当证明。
- **单事务及 flush 禁接收**：实际 dispatch 不改，release 与新接受的潜在优先级冲突仍由原协议排除。

## 4. 本轮控制抽象检查

control_variants.py 以 SHA 固定导入已审查 G0 的参考状态机，独立计算候选的 P、hold 下一状态及可选 gate；枚举所有后继到集合闭合，没有以目标性质过滤状态。参考模型的 RUN 非确定等待/完成，保留整数、双 lane 的 DIV/SQRT I/R/O 和独立 ROB 历史，未假定固定除法延迟。

| 假设候选 | 复位合同 | 可达状态 | 状态/输入组合 | 后继检查 | 结果 |
| --- | --- | ---: | ---: | ---: | --- |
| 只 FP hold | 共享异步 | 48 | 38,400 | 48,960 | PASS |
| 只 FP hold | 有效 bootstrap 后同步、TE 任意 | 48 | 38,400 | 48,960 | PASS |
| FP gate+hold | 共享异步 | 48 | 38,400 | 48,960 | PASS |
| FP gate+hold | 有效 bootstrap 后同步、TE 任意 | 48 | 38,400 | 48,960 | PASS |

每组从八种 ROB 初始历史出发，检查 P_F=F、全部后继集合一致、实际 clock-edge 集合一致；覆盖 SQRT、DIV lane 偏斜、输出反压、匹配/无关取消、完成取消、复位取消、TE0 活跃复位、VDot 阻塞、reset+valid。各组重复域不能加总成 RTL 覆盖率。

六个控制模型负控均被拒绝：遗漏 flush、遗漏 VDot、遗漏 busy、遗漏 reset、遗漏 SQRT、取消拍掩蔽时钟。前五个属于 P 定义检查，最后一个验证不能提前断钟。尤其“遗漏 reset”在 hold-only 模式由寄存器 reset 优先级屏蔽了状态变化，触发的是 P=F 合同失配，**不是声称已经发现 hold-only RTL 的复位功能故障**。外部无效初始化反例独立保留。

这套检查是新候选方程的源码绑定控制抽象复核；不是新 RTL 的自动形式等价、数值测试、全部真实时钟时序验证或 C3 局部验收。没有重新跑整套旧 G0。

## 5. 源码与复用审计

- 0f ExeUnit：fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa。
- C1 ExeUnit：ac73f507ee2eaebf5c7c4f515a136e4eb256ac1aab4e2224895965c497513be0。
- C2 ExeUnit：febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6。
- G0 system_model.py：8ae8349a08ff5e234215ebc68607f58784492d17b53dea9dfb01657db9968018。
- 完整固定来源见 input-identities.json；三个 ExeUnit 以 git show 只读提取为 .scala.txt，没有候选补丁。

准确源码锚点（相对生产仓）：

| 文件 | 行号 | 依据 |
| --- | --- | --- |
| src/main/scala/xiangshan/backend/exu/ExeUnit.scala | 126–136 | 原 release 和双 hold 更新 |
| 同上 | 138–159 | 原 gate 输出式、VDot 覆盖和 ClockGate |
| 同上 | 166–186 | 原独立 busy/ROB、ready/outValid、取消优先级 |
| 同上 | 300–334 | selected-ready、flush/reset 抑制、父子同接受断言 |
| src/main/scala/xiangshan/backend/fu/wrapper/VIDiv.scala | 25–47 | ready 时取输入ROB，否则保存ROB，flush/ready/out |
| src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala | 51–87 | 保存ROB、两lane start/finish、SQRT opcode、AND汇合 |

旧 G0 final-audit 的65项现场复核有64项当前完全相同；AGENTS.md 后续增补了档案规则，因此初次全匹配报告为 FAIL 并保留。旧AGENTS哈希0eec...由既有 historical-document-snapshots/AGENTS.md 完整恢复；resolved 审计明确将其作为历史说明文件，不把任意源码变更豁免。生产源码、实际模型与依赖绑定未变化。

## 6. 后续合同和停止条件建议

1. 用户另行授权实施后，先通知准确 RTL 改法；独立候选只做 C3-HF。不得顺手改 gate、INT、状态编码、ready、输出、ROB 或算术。
2. 新源码须审查实际 P 构造、reset/flush 优先级与 legacy/O1 不变；检验生成 RTL 的 FP hold 置位来源确实去掉 ready/fire，而实际 ICG E 保留原协议。保留所有源/生成物身份。
3. 跑真实 FU、真实父级及 SQRT/lane/TE0 reset 补充；所有完整128位结果、身份、异常、反压、取消严格门禁及观察负控照旧。旧 C2 PASS 不能移植到 C3。
4. 成功后做原同约束父级综合、五档45项与全部 DIV 状态D筛选：最差状态D≤1.737526ns、各路径≤baseline101%、旧正slack门控非负、面积≤284899.560946µm²、未知单元0。
5. 只要功能或任何冻结成本门禁失败，归档失败、保留0f并关闭当前门控试验；不自动升级到 gate+hold 或重新调表达式。只有全部通过，才进入新全核/NEMU和同镜像周期比较，另记身份与结果。

**结论：C3-HF 是有具体路径证据、协议前提且比 C2 更小的独立假设，值得至多一次试验；目前只有“可以提出并控制范围”的资格，没有“已优化成功”的资格。**
