# C2 RTL 改法与验证合同独立评审

2026-10-25，/root/c2_rtl_contract_review。仅审查固定源码和现有验证材料；本文件不代表已完成候选编译或仿真。

## 初步结论

允许进入独立候选实现。C2 从保留基线 0f12df675378556670afd0dd2153f47fcb330610 对照，组合复用 C1 的 busy+owner 编码与 G0 的 readyless 启动谓词。C1 未被恢复采用；这两个改动组成一个新候选，须重新验证，不能继承 C1 的整体通过结论。

## 具体写法

- 在所有 clock-gate 构造之前创建 Option[WireDefault(false.B)] 前向线，至少有 divBusy、divOwnerIsFp、divOutValid；后续在定义寄存态/输出聚合处连接。切勿把较后定义的 Scala val 直接提前引用。
- 对 ownedDivGate 单独计算 start = io.in.valid && cfg.fuSel(io.in.bits) && !divBusy && !divOutValid && !elasticVDotOccupied && !io.flush.valid && !reset.asBool。
- 该 gate 的最终 clk_en = start || (divBusy && ownsDiv)。整数 ownsDiv 为 !ownerIsFp，浮点为 ownerIsFp。保持项使用旧寄存值，不得用取消后的 nextBusy，不得加 !flush、!reset 或 !cancel。
- 最好以 Scala if (ownedDivGate) 分支整体替换旧 fu.io.in.fire 驱动的门控赋值；若采用最后连接覆盖，需核对所有 Chisel when 的优先级，确保生成网表 DIV E 的组合锥确实不含 child.ready。ckAlwaysEn 原最后覆盖可保留，固定当前两 DIV 均不是 always-on。
- 实际 io.in.ready、source.valid、child.fire、divAccept、divRobIdx 捕获、busy 清除优先级、输出分配保持原代码。owner 只在实际 divAccept 时捕获，不能改为 start。

无组合环的依据：start 只读顶层输入、寄存 B、VDot p/rValid、DIV outValid 及 flush/reset；两个 DIV outValid 源于状态寄存器，非当前 start 的组合输出。ClockGate 低电平透明锁存 E，时钟高电平不透明。真实接受仍检查子 ready。此结论须再以实际生成 RTL 检查补证。

## 必要的作用范围

沿用 vdotElastic 的 VFEX4 + 非固定延迟 + 恰好三 FU 的 require；C2 不应影响 O1、旧 VDot 模式、其他执行单元或关闭门控的配置。EnableClockGate=false 时 busy/owner 仍合法，门控专用线可被优化，但不能改接收逻辑。FU 类型选择应使用与真实分派同一个 cfg.fuSel 定义，不另造 opcode 解码。

G0 仅适用于固定 DIV/SQRT 实现、有效初始化与同步接口。真实全核共享异步复位建立初始态；当前同步父级夹具先 TE=1 bootstrap。首次未初始化时 TE=0 的反例仍是环境缺项，不能靠 readyless start 自行恢复来改写合同。

## 建议的严格门禁

1. 候选来源：保存完整 baseline、候选 HEAD/补丁 SHA、生产源码与依赖 SHA。固定 ExeUnit 之外生产源应无变化；未影响 VDot 算术源码不能等同于免测新组合。
2. 源码审查：diff 只允许 gate owner/state 重编码和启动项；accept/dispatch/ROB/output 子块与 baseline 比较保持原式。
3. 结构检查：从生成 ExeUnit 两个 DIV ClockGate E 回溯组合赋值到输入/寄存器边界，拒绝路径包含 VIDiv.io.in.ready、VFDivSqrt.io.in.ready、elasticDivOccupied、allowInput 或 fu.io.in.fire。寄存器 D 的历史依赖不属于组合锥，不能据此误报。此检查只能证明本轮生成 RTL 的结构，不是物理时序。
4. 动态关系：在有效初始化后的非 reset 采样点逐拍检查 !B => RI&&RF，以及 startInt == actualIntFire、startFp == actualFpFire；检查两门控保持项 one-hot、B 时真实所有者有边沿、取消清理后空闲不多开钟。
5. 功能：VDot 22+10,000 数据完整128位；FU/真实父级的反压、取消、ROB身份、异常、元数据、输入输出计数守恒与已有负控继续保留。
6. 新覆盖：真正执行 SQRT 数值案例；浮点两 lane 不同完成时刻需读取两 lane finish/state 并计数，不能只用两个不同输入数值宣称异步完成；先完成 lane 在 POST/输出态等待，另一 lane 完成后共同释放。
7. 门控有效性：DIV/SQRT 启动、迭代、反压、取消、动态 reset 及重启阶段 TE=0（只有同步夹具首次 bootstrap 用 TE=1）。已有 DIV legacy reset 12组使用 TE=1，不能单独承担 C2 的 TE=0 reset 证明。
8. 负控至少拒绝：取消时过早断钟、无hold、把 start 简化 raw valid 导致忙时额外脉冲、破坏 owner 选择；实际 ready 与 start 等价检查需有可证明会触发的负例或独立检查器单测。

精确周期行为应相对 baseline 0f 在同一新父级刺激逐拍比较，保留旧35,075周期兼容回归。若新刺激 baseline 本身失败，应定位环境/既有缺陷，不以改变旧容限掩盖。模型、独立FU、父级、全核、面积时序是不同级别；本轮完成 FU/父级后仅称局部功能通过，PPA 与全核 NOT_TESTED。

## 关键源码定位

- C1 ExeUnit.scala 92–95：前向busy/owner线；130–148：owner hold和旧fire门控；170–195：busy/owner/ROB状态及ready聚合；309–343：实际分派；582–591：真实child valid/ROB连接。
- 当前父级 GenerateVDotElasticParent.scala 23–43：固定配置/真实FU/门控；120：真实ExeUnit实例；195–204：子握手/时钟观测；225–228：TE接线。
- 当前 parent_test.cpp 362–367：bootstrap；510–518：旧 DIV reset 用TE=1；接下来新覆盖需明确单独标识。
- C2-G0 RESULT.md：实际全核共享async reset、同步bootstrap边界、ROB身份、双lane/SQRT细状态包含及结果范围。

实际候选 diff 与生成 RTL 到达后另加审查附录，不覆盖此实现前意见。
