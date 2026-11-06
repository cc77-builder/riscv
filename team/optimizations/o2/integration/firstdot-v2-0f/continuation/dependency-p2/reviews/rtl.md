# P2 依赖链硬件路径：只读归因

## 结论

当前采用的硬件仍是 **0f（O2 两槽弹性 FU + H1 32 位结果保存 + DIV 取消关钟修复）**。本次没有改动 RTL、没有重跑仿真/综合/STA，也没有上传。新增工作是现有 trace 重新分析及当前源码哈希核对。

0f chain256 的 12 个正式窗口、3,072 条 vdot、3,060 条相邻依赖边显示：每条 FU ACCEPT→MOVE→RESPONSE 都是 1+1=2 拍；连续依赖 ACCEPT→ACCEPT=7 拍，余下 RESPONSE→下一 ACCEPT=5 拍。这不是 FU 自身占了七拍。事件绑定及窗口边界见 ../trace/analysis-03/summary.json。

静态源码能解释五拍后端通路，没有额外的“父级输出寄存器”，也没有 latency 元数据失配。**没有一个已经证明可无代价安全删除的周期。**下一轮建议 **P4-G0：仅针对 VDot 2→1 拍结构的只读可行性评审**，暂不改共享 WB/IQ/OG 路径，也不先为已能静态解释的五拍重建昂贵观察器。以后若优化目标转到共享后端，才需要下述最小观察合同。

## 身份和资格

- 当前 HEAD：10b71ad4bff25cd2070e775c74a4717b01602f75。
- 实测硬件源码：0f12df675378556670afd0dd2153f47fcb330610。
- 历史及当前 EMU SHA256：2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8。
- MinimalConfig，单核、单 EMU 线程；O2_ELASTIC=1、T14_FUSED_INPUT=1、O2_TRACE=1、T13_TRACE=1，O1_HANDOFF/O1_TRACE/T12_TRACE=0。
- 父任务核对的 398 个源码文件与历史输入全等，见 ../hardware-identity.json。本子任务另核对直接引用的 19 个源码文件全部相同，见 source-pins.json；完整行号及逐字摘录见 source-excerpts.txt。
- 本文复用既有真实日志和 PPA，没有形成任何新候选的功能、周期、面积或 STA PASS。

## FU 与后端逐段归因

A 是生产者 FU accept，R=A+2 是 response。前三行的握手时刻来自既有 trace；后五拍的逐段定位是**静态无冲突模型**，没有逐段 WB/IQ/OG 实测事件。

| 周期 | 机制 | 具体源码行 | 证据级别 |
| --- | --- | --- | --- |
| A | 接收向量与身份/控制；将八个 16 位乘积存入 P 槽 | VDotElastic.scala:38–46,94–101 | accept 实测，机制静态 |
| A+1 | P 槽归约，将低 32 位结果及身份转到 R 槽 | VDotElastic.scala:59–65,102–107 | move 实测，机制静态 |
| R=A+2 | R 槽输出握手，高 96 位补零；parent 输出及向量 WB 仲裁组合贯通 | VDotElastic.scala:69–74；ExeUnit.scala:696–706；WbArbiter.scala:196–224,319–325,356–379 | response 实测；同周期 WB 接受为静态推导 |
| R→R+1 | WB 按 pdest 匹配消费者 psrc，更新 IQ entry 的 src-ready 状态 | Scheduler.scala:180–188,349–365；EntryBundles.scala:178–188,285–326；OthersEntry.scala:36–57 | 静态；前提为消费者已驻留目标 IQ |
| R+1→R+2 | ready 消费者被选择，进入 deqDelay | IssueQueue.scala:758–772,800–811 | 静态；无选择/发射冲突 |
| R+2→R+3 | DataPath 接收 IQ/OG0，经 OG1 寄存 | DataPath.scala:496–503,580–615,676–678 | 静态；RF/WB 端口可用 |
| R+3→R+4 | Og2ForVector 再寄存一拍 | Og2ForVector.scala:30–50；Backend.scala:507–521 | 静态；无 flush/load cancel |
| R+4→R+5 | 组合 BypassNetwork 后的 NewPipelineConnect 保存请求，再送 VFEX4/FU | BypassNetwork.scala:133–136；Backend.scala:641–653；NewPipelineConnect.scala:40–50 | 静态；parent 可接收 |
| R+5=A+7 | 下一依赖 vdot 被 FU 接受 | O2_ACCEPT 和完整结果/输入绑定 | 总间隔 7、response 后 5 实测 |

“同周期 WB”指响应握手与仲裁产生 toVfPreg.wen 可在同一计数周期成立，**不等于已实测物理寄存器阵列写边沿**。DataPath.scala:357–359 的 vfRfWaddr/vfRfWdata/vfRfWen 还会寄存，这是并行的数据写入路径，不能额外加到上面的五拍串行链中。

O2 的 pReady/rReady/move 允许合法的接收、搬移和响应重叠；无冲突依赖链的固定 2+5 不能外推到 DIV 占用、输出反压或取消场景。

## 父级没有额外输出寄存器

- ExeUnit.scala:641–647 只为 extraLatencyVal 插附加输出级；VDot 没有该配置。
- ExeUnit.scala:696–706 直接组合 valid/data/robIdx/pdest，697 行将 parent ready 直接传给 child。
- ExuBlock.scala:38–49 为直接连接，Backend.scala:666–668 直连 WbDataPath。
- RealWBArbiter 的优先级与 ready/grant 为组合逻辑（RFWBConflictChecker.scala:114–130）。
- WbArbiter.scala:214–216 的附加 RegNext 只属于 vector 单元写 integer RF 的分支，当前 vdot 写 Vec/V0 不经过它。

不能建议“删父级输出寄存器”来减拍。真正存在的是父级**输入前**的 bypassNetwork2vfExuBlock 寄存级，涉及整个向量通路的时序、取消与流控。

## latency、唤醒与旁路一致性

| 项目 | 当前源码 | 判断 |
| --- | --- | --- |
| FU 协议 | FuConfig.scala:583–598：piped=false、UncertainLatency | 与反压、取消、两项在途匹配 |
| 共享位置 | Parameters.scala:456–457：VFEX4 共享 VDot/Vfdiv/Vidiv；Vec/V0 WB 端口 3、priority 1 | 不是独占定长管线 |
| 定长表 | ExeUnitParams.scala:152–181：无 latencyCertain/uncertainLatencyVal，map 为空 | 不是漏填“2”，不能只改成“1” |
| IQ early wakeup | Parameters.scala:508–519 只有 ALU/LDU/FEX 组，无 VFEX；源码无其它 iqWakeUpParams 定义覆盖 | 当前 VFEX4 非 source，也非 sink |
| 约束 | ExeUnitParams.scala:323–327 禁止普通 uncertain FU 成为 IQ wakeup source | 单独增加配置不合法 |
| WB 唤醒 | Scheduler.scala:180–188,349–365；EntryBundles.scala:178–188,326 | 当前路径使用真实 WB 更新 ready |
| 同拍 bypass | EntryBundles.scala:250–253 只对 IQ 预测唤醒；BypassNetwork.scala:152–167 受 IQ sink 资格控制 | 不支持把当前 WB ready 直接当同拍 select/forward |
| vconfig/maskWakeUp | FuConfig.scala:594–595 | 源类型支持，不等于提前预测 VDot 完成 |

当前没有“数据两拍但调度错误宣告一拍”的证据。未来若迁入定长路径，必须同时处理数据可用、唤醒、端口预约、取消及仲裁。

## 观察器定义与缺口

| 事件 | 定义位置 | 正确解释 |
| --- | --- | --- |
| O2_ACCEPT | ExeUnit.scala:523–524 | 子 FU in.fire，不是 IQ select |
| O2_MOVE | 526–527 | 产品槽→结果槽，不是写回 |
| O2_RESPONSE | 538–539 | 子 FU out.fire；当前没有独立 WB/wakeup 事件 |
| O2_STATE/O2_STALL | 511、535–536 | pre-edge 槽/握手状态、输出阻塞 |
| O2_VFEX4_ACCEPT | 513–514；断言 320 | 父级接受与子级身份绑定 |
| O2_ENQUEUE | Rob.scala:1552–1555 | **ROB 分配，不是 IQ 入队** |
| O2_COMMIT | Rob.scala:1558–1561 | **退休，不是 WB** |
| selectTime/issueTime | IssueQueue.scala:795–797 | 设计元数据，现 trace 未输出，不能当已采样阶段事件 |

3,060 个消费者在 producer response 前已分配 ROB，因此可排除“尚未进入 ROB”的供给解释；**不能单凭此事件证明目标 IQ residency 或完全没有 dispatch 堵塞**。后五拍表保留静态模型及前提。

## P4-G0：只读评审的唯一候选

候选目标：输入组合逻辑完成八路乘法和归约，保存“已完成结果 + 原身份/控制”，最早在 accept 下一拍 response；仍保留两项弹性在途容量、完整 128 位输出、反压稳定、取消/复位、同拍出入和 DIV 切换。这里只规定待评审目标，不代表已有可用实现。

不能删掉一个槽位冒充等价。原 P 槽保存乘积，候选可能改存结果；头尾、迁移与 flush 必须重新立合同。减拍必须来自真实算术完成，不能改 observer/schema 或 latency 元数据伪造。

| 既有 PPA：Nangate45、布局前、nominal 1 ns | arrival/ns | slack/ns |
| --- | ---: | ---: |
| FU input→register | 1.190323 | -0.268520 |
| FU register→register | 1.163404 | -0.240117 |
| parent vdot input→register | 1.474949 | -0.549064 |
| parent vdot register→output | 2.776701 | -1.926701 |
| parent vdot register→register | 1.356106 | -0.433760 |

既有 FU 面积 17,298.246 μm²，parent 面积 284,614.946 μm²。源为 team/optimizations/o2/r3-div-gate/cost/results/RESULT.md:5–30。不是本轮重测，不是整核面积/频率/功耗。

两个算术分段目前都为负 slack，组合融合风险很高。不能简单相加 1.190323 与 1.163404 声称候选新 STA；起止点、mux、负载、映射和寄存器开销都会变化。更不能将布局前局部结果换算成全核 Fmax。

G0 先明确同频要求、面积及最差路径允许退化门槛，检查已有单拍算术证据和两项存储协议可行性。若明显不划算即 NO-GO，保留 0f；若产生可检验 GO，再提前告知用户具体 RTL 改法，进入隔离 FU/真实父级验证与同约束 PPA，通过后才考虑全核。现有端点观察足以支撑这个小范围 G0，不需要先重建观察器。

## 条件收益模型：不得记作实测

每个现有 chain256 窗：

1857 = 37（首 accept 前）+ 255×7（相邻间隔）+ 2（最后 FU）+ 33（尾部）

| 条件假设 | 模型 cycles | 减少 cycles | 当前版/候选模型比例 |
| --- | ---: | ---: | ---: |
| 仅 FU 2→1，其余保持：37+255×6+1+33 | 1601 | 256（13.786%） | 1.15990× |
| 仅后端 5→4，FU 保持：37+255×6+2+33 | 1602 | 255（13.732%） | 1.15918× |

是**条件性理想估计**，候选尚未存在，不能填入版本实测加速比列，也不能外推为 8×32 应用收益。实际前后开销、调度、分支或端口冲突可能改变。

## 后续共享后端候选才需要的最小观察合同

现在不额外构建 EMU。若以后选择修改 WB/IQ/OG 某段，需补：

1. WB/grant：cycle、EXU/port、ROB flag/value、pdest、Vec/V0 wen、完整结果或可核验摘要；绑定 O2_RESPONSE 和 toVfPreg.wen。
2. 依赖 IQ：实际 IQ enqueue、消费者 ROB、psrc/srcType/srcState、WB 命中、其它源 ready、blocked/issued/canIssue；直接证明 residency。
3. 选择/发射：deqBeforeDly、deqDelay 的 valid/ready/ROB、取消及 RF/WB 端口阻塞原因。
4. OG 边界：OG0→OG1、OG1→OG2、OG2→最终 input register 的 valid/ready/fire/ROB/dataSource，末端复用现 O2_ACCEPT。
5. 同一 GTimer、pre-edge 定义，处理 ROB 环绕、重新发射、kill、pdest 重用、DIV 交错和 flush；观测不得反馈功能输入。

一个正式 chain 窗加短控制探针即可用于定位，不自动触发整套 campaign。即使完全吻合五拍，也只证明路径成立，不能据此认定哪一拍可删除。
