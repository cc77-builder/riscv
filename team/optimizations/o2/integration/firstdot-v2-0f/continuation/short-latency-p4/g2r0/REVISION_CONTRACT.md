# P4-G2R1 唯一最小修订合同（尚未实施）

父合同 `p4-short-latency-g0-v1` 不变。R0 只读结论为“值得一次试验”，不会重新开放 G2 失败版本的全核资格。

## 修改范围

唯一拟修改生产文件：`src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala`，仅已有 `if (oneCycle)` 中 R 的 ctrl/perf 写入表达。改前再次告知用户文件、信号与行为；默认关闭开关和既有 VDotO2.scala 不改。

拟将完整 ctrl、perf 各自改成三路 one-hot 选择，明确包含旧 R 保持：

    holdR = !(move || directR)
    rPacket.ctrl_next = Mux1H(holdR -> rPacket.ctrl,
                             move -> pCtrl,
                             directR -> acceptedCtrl)
    rPacket.perf_next = Mux1H(holdR -> rPacket.perf,
                             move -> pPerf,
                             directR -> io.in.perf)

以上是设计伪代码，不是已编译 Scala，也不是指定技术单元实例。实际字段名沿用原 perfDebugInfo；使用 Chisel 类型安全的 Bundle 选择，完整保留所有位。不添加新模式、寄存器、技术单元实例、dont_touch 或新的综合约束。

保持原 rPacket.res.data32 的 when(move)/elsewhen(directR) 写入；它与元数据取同一沿前事务。P 捕获、pResult、乘法/加法树、valid、raw 占用、kill、flush、reset、ready、接受及输出协议全保持。ExeUnit、DIV/SQRT、ICG、共享后端均不改。VDotO2.scala 默认关与拒错原样。

## 必须成立的行为

1. move 和 directR 由原逻辑保证互斥，hold/move/directR 恰一；不能靠测试假设跳过实际断言。
2. flush 当拍禁止新接受，但未被命中的旧 P 仍可搬入 R；不要把写使能整体与 !flush 相与。
3. reset 时禁止接受/响应、valid 清零，旧载荷保持；不得新增载荷复位或改变默认关逻辑。
4. 旧 R 弹出、旧 P 搬入和新请求进 P 同沿时，R 必须取沿前 P；新请求不能越序。
5. 反压时完整输出稳定；匹配取消/reset 例外沿用原合同。R/P 独立 ROB 代际匹配不变。
6. 非法输入仍占槽，data32=0，illegalInstr=1，vecWen/v0Wen 关；身份与完整 ctrl/perf 同事务绑定。
7. 输出始终完整128位，高96为零；不增加 P/输入到输出的组合旁路。
8. P/R raw valid 的父级占用以及 DIV 接收/取消/关钟协议不变，不能顺带“优化”它们。

## 下轮分层验证

**R1 局部轮**：固定新补丁/源码 SHA，与 G1 原补丁并存；静态检查修改范围、状态和默认关差异；完整22定向＋10000随机128位；新源 FU 的两槽/反压/取消/身份/非法/II1；新源真实 VFEX4 DIV、浮点双lane、SQRT、复位与取消关钟；默认关回归/生成逻辑、开关拒错、严格负控。原G1测试及负控不得只换 latency 常数放行。原失败保存。

**后续 R1 成本轮，另行启动**：上述全部通过才按 G2 原工具/库/端口/负载/路径覆盖做 FU 综合＋五档 STA；FU 任何门槛失败，停止，不继续父级。FU 通过再做真实父级综合＋五档 STA。旧0f证据只在完整输入/工具/约束与校准资格可复用时复用，否则重建同口径对照，不改门槛。记录新修订与0f的47项判定，同时保留旧P4成本作为归因参考。

冻结门槛：
- FU ≤18163.158300 μm²；父级 ≤287461.095460 μm²。
- FU/父级 Q：nominal、period050、period200、load001 ≤3.563697900 ns；load020 ≤3.583858950 ns。
- 原35项保护路径不变：FU i2o/r2o/ready；父级 gate_enable/ready/r2o/vdot_r2o，各五档 arrival 增量 ≤max(旧值5%,0.050ns)。
- 父级 ready 上限 nominal/period050/period200=0.297821、load001=0.288594、load020=0.358999 ns。
- 原14组×5、额外全局/P/R/输入直写路径全部保留；无空候选路径、未知单元、漏约束或新增false/multicycle。
- 不采用手工 cell 数替代综合，不改变 Liberty/ABC/STA 约束，不删除缓冲。成本变小不能豁免时序。

**本次只尝试上述一个逻辑候选。** 功能错误可在同一合同内纠正并保留失败；若最终成本仍失败，不自动做第二种逻辑/门控/状态结构搜索。停止该次P4修订，保持0f；以后重新打开方向需新的证据和用户启动。只有全部47项及完整性通过，才可另行提议G3，不自动全核/NEMU/性能/采用/上传。
