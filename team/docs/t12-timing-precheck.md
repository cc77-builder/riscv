# T12 前期时序审查（生产实现不变）

本轮基于生产源码与实际已验收 EMU 的一致性开展静态审查；`src/` 与 `build.sc` 仍等于 `fcb16a8764d342339670df0bbf1bc67ef2028b86`。无新综合/STA、无 Liberty/PVT/输入输出时延/时钟不确定度约束，不能声称时序闭合、Fmax、面积或功耗改善。没有自定目标频率或修改时钟、复位、128 位接口、单 uop 语义、共享 EXU busy/ready。

独立审查指出并经本任务重读确认：`Backend.scala:645` 的 `NewPipelineConnect` 在 `NewPipelineConnect.scala:43` 使用 `RegEnable(left.bits,left.fire)` 保存数据。因此实际数据路径需按寄存器分段；原 Windows 硬件审查中把 RF/旁路一路串接到融合乘法输入的描述过于保守且跨越了真实数据寄存器。`FuConfig.srcNeedCopy` 默认 false，VDot 沿用该值；不能把 Dispatcher 的 valid/ready 选择错误地算成 VDot 操作数复制 mux。**数据被寄存不代表反向 ready 控制也被寄存**：`left.ready := right.ready || !valid` 仍需单独分析。

| 路径 | setup 风险与需要的报告 | hold/fanout 风险 |
| --- | --- | --- |
| RF/OG2/旁路 → `bypassNetwork2vfExuBlock.data` | RF 到达、V0 替换与旁路 mux、扇出、实际输入捕获使能；在此数据寄存器切断 | 短旁路支路、不同 mux 分支最小延时、数据/使能相对时钟偏斜 |
| 上述寄存器 → VDot `src1Reg/src2Reg` 及控制快照 | 正常输入路径、VL/config 合法判定、`in.fire`；不跨越前级寄存器 | 极短直连与宽寄存器 enable 扇出；真实门控时钟关系需 propagated clock 与 gating check |
| `srcReg` → `productsReg` | 8 路 signed 8×8，保留 16 位乘积；布局与乘法映射决定最长路径 | 低位快速路径、各乘积位最小延时和使能偏斜 |
| `productsReg` → 17/18/19 位平衡树 → 32 位符号扩展 → `resultReg` | 三层扩位加法及 illegal 选择；进位链、符号扇出、布线 | 常零高位和短位路径；高 96 位可被常量优化，不能按声明宽度估算实际触发器 |
| ROB/flush → `needFlush` → out.valid/state/ready | 环形年龄、取消优先级、输出屏蔽；高扇出 redirect 与 backpressure 反馈 | 短控制路径及 reconvergence；取消当拍不可产生幽灵响应 |
| 共享 VFEX4 busy/dispatcher → FU ready → 反向管线 ready | 不定延迟 busy 在 out.fire 后寄存清除；可能存在反向组合关键路径 | 清 busy、valid 与数据在同拍的相对稳定性；不能靠局部 ready 优化改变通用协议 |
| result/control → ExeUnit one-hot mux → 共享 WB → RF/ROB | 128 位结果、身份及异常同时写回；真实 WB 仲裁和 notWrite ready | 控制高扇出、短异常通路、共享端口不同来源的最小延时 |

当前 FU 无反压时：E0 接收源/身份，E1 保存乘积，E2 保存结果并在沿后 valid，E3 最早响应握手，E4 最早接收下一请求，即 II4。历史单元级实测与本轮源码相符；这些不是本轮全核指令周期。共享 EXU busy、OG2 重试、门控、VL/RAW 依赖与 WB 竞争会改变全核窗口。

输入级融合的正确候选路径起点是 `bypassNetwork2vfExuBlock.data` 寄存器，到乘积寄存器途中新增乘法逻辑；不能按模块边界当作寄存边界。II3 仅是改变内部状态机后的推导，尚无本轮候选 RTL/全核/STA 证据。其理论接受率提升与真实执行时间 `C_candidate * T_candidate` 的改善不是同一指标。未晋升此候选。

另外两项独立审查发现已重读确认，仍属源码推导风险。`ExeUnit.scala:102–106` 的 `uncer_en_reg` 由 in.fire 置位、out.fire 清零；VDot 被取消后无响应，因而该使能可能持续为1。这需要真实门控EXU验证，不能称功能死锁或已测功耗问题；取消清使能还必须保留让FU回idle所需的时钟沿。融合同时取消 `srcReg` 的操作数隔离：`ExeUnit.scala:304–308` 向所有FU连接共享源，共享其他FU活动可能使未选中VDot的组合乘法器翻转。任何新增隔离门及共享输入Q负载，都必须进入setup/hold/fanout与活动分析，不能按减少寄存器直接推断节能。

算术边界仍为 `[-130048,131072]`；18 位正端点不足，最少 signed 19 位。树宽 16→17→18→19 正确，符号只扩展到低 32 位，高 96 位零。不存在饱和或舍入，禁止用窄归约当等价基线。

后续时序签字需要同一工艺/PVT、完整时钟/复位/门控约束、真实上游寄存起点与 WB 终点、最大/最小时延和扇出报告，并复测取消、反压、身份与共享 EXU 场景。当前成果是有源代码依据的前期风险审查；不把未观测的年轻指令已发射取消、ROB/FTQ 实际绕回或写回碰撞记成已覆盖。
