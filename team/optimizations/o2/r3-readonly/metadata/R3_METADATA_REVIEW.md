# R3 只读审查：O2＋H1 元数据、消费者与实际映射

日期：2026-10-24。固定 HEAD：4669c487f3024ee5fce514c37270297f99066b2a。执行者：R3 元数据审查 Agent。状态：只读提取与复算通过；没有修改生产源码、旧归档，没有综合、STA、仿真、fetch 或 push。

结论：**暂不把“删掉宽元数据”作为下一项生产优化。** VPU 大字段在真实父级成本边界已被消除；perf 大字段在公共成本接口中真实存在，但目前全核的输入已经由上游生成为常零。删字段会破坏公共接口的身份复制合同，并且不能把公共 FU 的面积变化冒充全核净收益。建议先把成本边界与诊断合同说清；保留目前主线完整身份。

## 1. 证据与复算入口

- audit_metadata.py：只读审查器，输出路径必须不存在；不会写仓库。
- metadata-audit.json：按 net bit → DFF Q 驱动 → 唯一 DFF 名统计，保留逐字段 bit/cell、来源哈希、全核生成物哈希、日志统计。
- command.json、audit.stdout.log、audit.stderr.log：实际命令、UTC 开始/结束时间与退出码。
- 复算（显式输入根；输出必须是新文件）：

~~~bash
python3 -B audit_metadata.py \\
  --repo /home/riscv/riscv-lab/zjhwork2-review-20261018/repo \\
  --local-cost /home/riscv/riscv-lab/o2-h1-result32-20261021 \\
  --core /home/riscv/riscv-lab/o2-h1-fullcore-20261021 \\
  --output 新结果路径.json
~~~

- 不允许 python -O，防止跳过必要断言。两个封存 manifest 的 SHA256 已固定；全核生成物清单和 build-state 本身也须与封存载荷逐字节一致。检查器强制要求 10 份正常日志、3137 条接受记录和十个 perf 字段全部为零。
- 初次脚本保存在 audit_metadata.initial.py；增强版的重查结果、命令及退出码保存在 recheck/。本次仍只读，无硬件任务。
- 状态：R3_METADATA_READONLY_AUDIT_PASS。

两份 H1 mapped.json 均与已封存载荷解压后的字节完全一致：

| 边界 | 原始 SHA256 |
| --- | --- |
| 独立 FU，fu-map-01 | 24f54ed3d1ecc8d4f7f3231006e17ebf9c3d4244dfe96d729fd6111860ed112b |
| 完整 VFEX4，parent-map-01 | 08b5519efeadfe0cf5ebb28245c5d225a0510285a1d0adb6e215bf4d50c588dd |

当前 build/rtl 内的 VDotElastic、ExeUnit_17、ExuBlock_2、DataPath、Backend 五份 SV 均与 H1 已存 build-01/generated-artifacts.json 相符。H1 是 observe 配置，O2_TRACE=1、T13_TRACE=1，硬件源码构建提交 8b5024fcbd96986871cc40ce8c9fb71a67c495eb；不是以本次文档 HEAD 冒充构建身份。

## 2. 实际 DFF 组成

下表按唯一物理映射单元计数，所有列出的单元类型都是 DFF_X1。P/R ctrl 的 VPU 子组单列，避免重计。

| 存储类别 | 独立 FU | VFEX4 内 VDot |
| --- | ---: | ---: |
| P/R valid | 2 | 2 |
| P 槽八个 16 位乘积 | 128 | 128 |
| R 槽低32位结果 | 32 | 32 |
| P/R 必要控制，18位/槽 | 36 | 36 |
| P/R VPU，195位/槽 | 390 | 0 |
| P/R perf，577位/槽 | 1154 | 1154 |
| VDot 命名单元合计 | 1742 | 1352 |
| 整个所测边界的 DFF | 1742 | 17171 |

每槽 18 位必要控制为 ROB flag/value 共 7 位、pdest 8 位、vecWen/v0Wen 2 位、illegalInstr 1 位。其他 exception 位已消为常量，没有按异常总线名额外计算寄存器。当前 ROB=64，不能删 flag；物理寄存器索引仍需完整 8 位。

每槽 PerfDebugInfo 为一个 eliminatedMove 加九个 64 位字段，即 577 位：renameTime、dispatchTime、enqRsTime、selectTime、issueTime、writebackTime、runahead_checkpoint_id、tlbFirstReqTime、tlbRespTime。这不是“577位全都参与执行运算”。

完整 VFEX4 的 VDot VPU 字段没有保留寄存器网络；源码 ExeUnit.scala:688–707 选择输出时只复制执行结果及必要控制，输出 ExuOutput 不转发 VDot 的整个 VPU 包。CommonFuCostTop 将整个 FU IO 暴露为公共端口，所以独立 FU 的 VPU 被保留；CommonParentCostTop 暴露的是父级公共 IO，所以它消失。见 team/optimizations/o4/GenerateVDotCost.scala:15–43。

**390 个 VPU DFF 的“删除机会”已经在父级映射兑现，不能再次当成未来父级面积可节省量。** 同理，1154 个 perf DFF 是此公开接口下的现存成本，不是可以承诺的净节省，更不是整核面积比例或功耗数。

## 3. 架构必要与诊断必要的消费者

| 内容 | 消费者与依据 | 结论 |
| --- | --- | --- |
| P/R valid 与 ROB | VDotElastic.scala:58–68，needFlush、liveP/liveR、move、ready | 取消、身份和容量必要，不可压缩为无身份忙标志 |
| pdest、vecWen/v0Wen、illegal | VDotElastic.scala:84–91；ExeUnit.scala:688–707；寄存器写回与 ROB 异常 | 必须逐槽绑定，非法指令关写使能，不能从同拍新输入重建 |
| VPU 整包 | VDotElastic.scala:90；O2 全核观察器 ExeUnit.scala:514、526、529；父级身份测试 GenerateVDotElasticParent.scala:210–219、parent_test.cpp:234–252 | 在独立公共 FU/验证合同中必要；关闭观察器的真实父级功能输出已不消费整包 |
| rename/dispatch/enq/select/issue 时间 | ExeUnit.scala:727 → WbArbiter.scala:376–379 → Backend.scala:262 → CtrlBlock.scala:124–131、746–747 → Rob.scala:531–534、1374–1400、1429–1436 | ROB 延迟统计、数据库诊断需要；不能将“非 ISA 架构状态”等同“随便清零” |
| 输入 writebackTime | CtrlBlock.scala:130 在送 ROB 前重新写 GTimer | 后续 ROB 不需要 FU 携带的旧 writebackTime；但 FU 公共接口与完整身份观察器仍要求复制它 |
| tlbFirstReqTime/tlbRespTime | Rob.scala:1437，数据库 tlbLatency | vdot 不是访存指令，语义上可定义无效；公共输入当前允许任意值，修改需明确诊断合同和配置范围 |
| eliminatedMove / runahead_checkpoint_id | 本次后端消费者搜索未发现其在 VDot 响应后直接控制 ISA 行为；ROB eliminatedMove 使用 enq 独立位（Rob.scala:1571–1598），不是 FU perf 位；JumpUnit 中 runahead 赋值已注释 | 存在“诊断字段只在有效配置保存”的设计方向；不能据此直接删除完整字段或宣布所有配置均无消费者 |
| 整个 perf 包 | ExeUnit.scala:514/526/529 完整打印；parent_test.cpp:252 比较整包；heldResponse 断言比较完整输出 | 当前测试有意覆盖任意非零身份；任何压缩都必须先建立明确的新观测合同并保留强身份负控 |

源头定义：src/main/scala/xiangshan/Bundle.scala:237–250；FuncUnit.scala:39–52、73–85；VPU 定义 backend/Bundles.scala:407–459。

这里“可以条件压缩”仅表示新的、明示的诊断配置有研究空间，不是当前公共接口可合法变更。改变全局 PerfDebugInfo 宽度会影响其他 FU、ROB、数据库及观察器，不宜作为 vdot 单项优化。

## 4. 关键边界：实际全核的 perf 输入已经为零

不能仅由日志全零推断硬件常量；此次同时追了结构：

1. IssueQueue.scala:795–797 确实尝试给 issue bundle 填 perfDebugInfo 和 select/issue 时间。
2. backend/Bundles.scala:651–686 的 ExuInput.fromIssueBundle 复制了执行控制、VPU 等字段，**没有复制 perfDebugInfo**。
3. DataPath.scala:502 构建 s1_toExuData 寄存器，611 调用上述转换，678 输出整包。
4. 当前已封存 H1 DataPath.sv:19173–19182 对 VFEX4 路径 io_toVecExu_2_0_bits_perfDebugInfo 的全部十字段明确 assign 0。
5. BypassNetwork.scala:134 复制公共端口；Backend.scala:509、644–652 经 OG2/旁路/流水寄存器连接 VFEX4；ExeUnit.scala:589 将 perf 送 FU。生成 ExuBlock_2.sv:935–955、ExeUnit_17.sv:997–1016 可核对接线。

这更接近现有上游诊断连接缺口，**不能当作已设计好的“轻量性能模式”**。本次只报告，不顺手修正全局通路；修正会改变所有相关 FU 的诊断数据、构建结果和对照条件，应另立验证任务。已有 mcycle 公平性能窗口仍独立于这些时间标签，不能因此否定既有 cycles 数据，也不能把标签全零说成完成了全核非零身份验证。

证据检查：

- 10 份已封存正常日志：8 个 functional shard、dense-batch128、control；逐份核对压缩载荷及 raw SHA。
- 共 3137 条 O2_ACCEPT，577 位 perf 输入均为零。这个统计是样本事实，常量结论来自上面的生成 SV 赋值。
- 当前 VDotElastic.sv 仍声明 P/R 各 577 位 perf reg；同一 EMU 的 C++ header 仍保留对应 20 个字段。它们不是一份全核综合后的单元计数，不能宣称已经 DCE 为零 DFF，也不能宣称全核必然占1154 DFF。
- observe 模式保留 VPU P/R 各 192 位 reg；另外三位由 ExeUnit.scala:586–588 强制零。关闭 trace 的父级成本映射消掉所有 VPU，两个边界用途不同。
- VDotElastic.sv SHA256：f15adc6d2bda414b8d6eba2f8a9e25d29e34e80b72599f873c90a9202c7204eb。
- 实际 H1 EMU SHA256：e37b3c267cae29036bda0b6952a17db2523ca0b3a573d45281341d4207df8747。

## 5. 候选取舍

| 候选 | 现有证据 | 建议 |
| --- | --- | --- |
| 删除/缩小 VPU 整包 | 独立 FU 有390 DFF，但真实父级已全部消除；身份验证会受损 | 不列为生产收益候选 |
| 全删 perfDebugInfo | 公共边界有1154 DFF，实际整核输入常零，但公共接口/非零身份测试/诊断消费者存在 | 不直接做，不能用削弱接口制造面积成绩 |
| 仅保存有消费者的诊断字段，例如去旧 writebackTime | ROB 会重写该时间；理论上可缩小诊断包，但当前合同不同；整核常零路径可能无净收益 | 若未来确需硬件发布配置，先定义 trace/DB/perf 功能矩阵与观测等价边界，再重新映射；当前优先级低 |
| 时间戳截短 | 涉及64位差值、长时间停顿、回绕和统计完整性；当前没有界限证明 | 暂缓 |
| 精简 ROB/pdest/写使能/异常 | 必要位已只有18/槽，异常无效位已经裁掉 | 保持 |
| 诊断连接审查/补齐 | 有明确丢失链，能提升非零身份验证可信度 | 可作为单独的验证基础设施问题，先隔离范围与对照，不与低功耗/面积候选混做 |

后续如果尝试任何字段重建，最低门槛应包括：所有受影响配置的消费者列表、非零随机元数据、P/R 双槽不同身份、同时出/移/入、反压稳定、P/R 独立取消与 partial kill、DIV 切换、完整128位结果及 bit100 负控、父级同接口成本、全核 trace 与周期不退化。不能只跑已有 perf 恒零的全核镜像就声称身份重建通过。

## 6. 关键源码身份

详细 14 份文件 SHA256 与 Git blob ID 在 metadata-audit.json。重要三份：

- VDotElastic.scala SHA256：93812d4776bdf390d60d4cd47f6fbc80debfff82d8a5e9d1a5676987365658db；Git blob：72d23e224bbfea13245865cc5a506ac87aed877b。
- backend/Bundles.scala SHA256：5455eb58abaa45aebeb400e1b1dcd744ad41fc1b15620f5120b54b1217490280；Git blob：eae7563c7294bca172ce2f61b053737b0de2567a。
- DataPath.scala SHA256：838eefec28b52827de0f0f0be6dbf33726e9e69518711138054cdf670aacac8f；Git blob：b7cb67ee20cdff03ec1313337ae5c9c5af83aee4。
