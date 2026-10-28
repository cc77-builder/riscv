# R3 DIV 取消门控候选源码复审

结果：STATIC_RTL_REVIEW_PASS。未发现阻止该最小候选进入 FU／真实父级验证的问题。

候选路径：candidate-source/ExeUnit.scala；固定基线 4669c487f3024ee5fce514c37270297f99066b2a。候选 SHA256：fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa；补丁 SHA256：37a2763eae0166cd20231b1b5aba5baa5b1bd888c575d1adcf045fc18ecf79f8。结构检查及原始基线 SHA 见 candidate-review.json。

本复审只读候选副本，没有修改生产源码或测试，也没有额外执行硬件任务。

## 范围与旧模式

- 第93行仅 O2 创建 elasticDivCancelled Wire。其他模式为 None。
- 第126–131行采用 Scala 构建期条件：仅 vdotElastic 且 FuType 为 vidiv/vfdiv 时，把 cancel 加入 releaseUncertain。其他 FU／legacy 的清除表达式仍严格是 fu.io.out.fire。
- 第146–150行 VDot 的 P/R occupancy、accept、reset 门控未变。没有移植 James 的 legacy 接受即取消规则，也没有引入其 O1 观察器。
- 对候选反向应用四个预期替换后，字节级恢复完整基线 ExeUnit.scala；候选补丁也与固定基线和候选的完整差异精确相同。没有隐藏的其他生产修改。

## 时序、取消与优先级

- 第174行取消条件只读取已保存的 divBusy、divRobIdx 以及当前 flush；复用现有 RobPtr.needFlush，保留 flush-self、环绕 flag 和无关 redirect 判断。
- 第130行取消影响 uncer_en_reg 的下一状态。第142行门控仍读取保持寄存器当前值，没有把 cancel 组合接到当前 clk_en。
- 因此在合法在途 DIV 上，取消当拍旧保持位仍为1，真实子 FSM 接收清理上升沿；父寄存器同时清0，后续 CK 低相位门控锁存器更新，下一次空闲上升沿被屏蔽。
- 第132–135行仍为“接受先设1，否则完成／取消清0”，原接受优先级不变。O2 的 allowInput 对任何 flush/reset 都拒绝新请求，取消与新接受本来互斥。
- divBusy 的原取消＞完成＞接受优先级不变；第186行物理占用公式 divBusy || divOutValid || !divReady 未变。修复不会允许同拍 DIV→VDot、VDot→DIV 或跨 DIV 接收。
- 新信号的唯一额外依赖是注册的 divBusy/divRobIdx → needFlush → 保持位 next-D；反馈通过保持寄存器及子状态寄存器打断。源码中未引入组合环。综合／elaboration 的无环检查仍以真实构建结果为准。
- 未选中的另一个 DIV 保持位也能在该取消沿清0；在 O2 单 DIV 排他的前提下它不可能持有合法请求，所以不会取消别的合法在途结果。

## 仍需执行证据支持的结论

1. 旧 RTL＋新严格门禁出现预期 RED，候选＋同门禁 GREEN。
2. 取消沿必须有子钟；下一拍无输入无存活请求即关钟，不能以延后采样绕过。
3. 同 ROB 无 self、无关 redirect 与环绕关系不能误关存活 DIV；后续新请求仍能醒钟完成。
4. 算术、完整128位返回、身份、反压、异常、VDot双槽和真实父级排他保持；离线 raw-clock 重算及负例拒错独立成立。
5. 本轮不能据此宣称当前组合全核/NEMU、周期、面积、时序或功耗已验证。DIV reset 仍沿用原 TE 约定，不能借 VDot TE=0 覆盖扩大结论。

此结论适用于上述精确候选 SHA；后续若改候选，应重新核对实际差异与适用范围。
