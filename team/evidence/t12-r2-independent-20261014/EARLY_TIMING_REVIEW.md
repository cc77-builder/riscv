> 本文件是独立审查的只读展示副本。正文相对路径指向同目录审查包解压后的 `independent-review/`，原始正文保存在归档中，不代表所有源码副本直接铺在 GitHub 目录。参见 [README](README.md)。

# VDot early timing review — independent

审查对象固定为 `b8272f2e8a62557437869c936b6ea9ce5fff84fe`；团队 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3` 的相关 RTL blob 相同。逐文件 Git blob/SHA256 在 [source_manifest.json](evidence/source_manifest.json)。Draft #1 `f8e8276681e0f4cfdc4ce0d8e2a76ebb4897493e` 尚不可解析，不能替它签字。原融合 patch 是已散列的外部研究工件，不冒充该 Draft 提交。

**当前决策：候选不晋升。真实 STA、工艺库映射、布局布线、功耗与候选整核验证全部 NOT_RUN；没有 Fmax、面积、PVT 或比赛加速比结论。** 本报告首先修正一个真实时序路径判断，而不是预设融合输赢。

**重要发现 H01：原研究把 RF/旁路 mux 与融合乘法直接串联，遗漏了固定后端中真实存在的寄存级。** [Backend.scala](sources/baseline/src/main/scala/xiangshan/backend/Backend.scala) 509、521、645–652 行把 DataPath → OG2 → BypassNetwork → `NewPipelineConnect` → VFEX 连接起来；[NewPipelineConnect.scala](sources/baseline/src/main/scala/xiangshan/backend/datapath/NewPipelineConnect.scala) 40–50 行有 `RegInit(false.B)` 和 `RegEnable(left.bits,left.fire)`，`right.bits := data`，不存在组合 fall-through。VDot 配置 `srcNeedCopy=false`（FuConfig 默认 63 行），[ExeUnit.scala](sources/baseline/src/main/scala/xiangshan/backend/exu/ExeUnit.scala) 304–308 行给 VDot 直接接 `io.in.bits.src`；Dispatcher 处理 valid/ready/控制，不能凭模块名假设数据再经过一次源选择 mux。

真实数据边界应这样审查（`→ |reg|` 表示终止一个组合段）：

| 段 | 固定源码上的真实边界 | 融合的影响 |
|---|---|---|
| RF 读、源类选择 | DataPath 中 RF 输出/源数据 → OG2 `s2_toExuData`，Og2ForVector 30–50 行 | 未直接合入乘法；保持自身 STA 约束 |
| 前递/旁路 | EXU forward、`bypassDataVec`、`bypass2DataVec` 或 OG2 输出 → BypassNetwork 163–174 行两层 Mux1H，含 v0 路径 → `bypassNetwork2vfExuBlock.data` | 这里有真实寄存器切断；不能跨它相加延迟 |
| FU 接受 | `bypassNetwork2vfExuBlock.data.Q` → EXU 源连线 → 原 `src1Reg/src2Reg.D` | 融合替换为上述 Q → 八个 signed 8×8 乘法 → `productsReg.D`；仍须包含布线、负载、使能 mux、门控时钟 skew，不允许理想零输入到达时间 |
| 乘积 | 原 `src*Reg.Q` → signed 8×8 → `productsReg.D` | 原独立段被删除；没有证据说明新段优于原段 |
| 归约 | `productsReg.Q` → 四个17位、两个18位、一个19位加法 → 符号扩展/非法零选择 → `resultReg.D` | 融合 patch 不改这一段；也可能仍为瓶颈 |
| 写回 | `resultReg.Q`/身份/illegal → EXU 结果选择 → WB 仲裁/寄存器写与 ROB completion | 候选早一拍进入该竞争；必须重验停顿和取消，不等于多一个写回端口 |

**接口与局部时序。** [VDot.scala](sources/baseline/src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala) 20–101 行继承 XSModule 的 clock/reset 与 Decoupled in/out，flush 是 Valid Redirect。128 位双源只读取低64位的八个 signed8；单项范围 −16256…16384，总和 −130048…131072，正端要求19位有符号数，18位不够。`VDotDatapath.scala:34–48` 用 16→17→18→19 位扩宽树，先 sign extend 至32位，再拼96位零。负数如 −130048 的完整目的为 `000000000000000000000000fffe0400`，绝非128位符号扩展。

合法域是 VLEN128、e8/m1、实际重命名 VL=8、vstart0、vill0、vm1 和内部 op=s8x8；vta/vma/vxrm 不参与算术，vxsat/fflags 不写。VL 取输入 renamed VL 源，不可偷换成 ctrl.vl。oldVd、tail/mask merge 不参与结果。目的 vec/v0 写使能二选一，非法请求同样保留身份，数据为0且禁写，并返回 illegalInstr；“精确异常”还依赖 ROB 的有序提交，单 FU 不能独自证明。

E0 接受源/身份，E1 寄存乘积，E2 沿后 result 和 valid 出现，E3 最早 out.fire；下一请求 E4 接受，即局部 II4。融合 patch 预测 E0 乘积、E1 沿后 valid、E2 响应、E3 再接受，即 II3，**候选本次未做 RTL A/B**。响应反压保持完整结果/身份；匹配 redirect 优先撤销，idle 遇任意有效 redirect 都不接受，reset 抑制 ready/valid。数值寄存器无复位依赖，仅状态复位后清除有效性；物理 reset 极性/同步性须以实际 elaboration 为准，不能因 `RegInit` 擅断。生产顶层给 core AsyncReset（Top.scala:448），局部独立生成 top 的 reset 合同还须另核对。

**共享控制不允许只改 piped 就宣称 II1。** FuConfig 583–596 行是 non-piped/UncertainLatency，VFEX4 与 Vfdiv/Vidiv 共用（Parameters.scala:456）。ExeUnit 127–143、224–226 行 busy 寄存器在 out.fire 的沿才清；响应这一拍 input 仍被旧 busy=1 阻挡。NewPipelineConnect 的一项缓冲可能先接收下一条，但不改变 FU 的接受间隔。OG2 每拍重写 valid、失败反馈 IQ block（Og2ForVector:39–65），不是无限保留队列。WbArbiter:224 由实际仲裁给 uncertain ready；177–183 的 notWrite 让禁写异常仍能 completion；357–360 只把 fire 发给控制块。ExeUnit:321–322 要求各 FU 输出 one-hot。

**H02，源码推导、需门控 RTL 确认：取消后时钟使能可能持续为1。** ExeUnit:102–106 的 `uncer_en_reg` 仅 in.fire 置位、out.fire 清零；VDot 的 kill 不响应，busy 却在 needFlush 清零。最小轨迹：接受 A → 在 MUL/REDUCE/RESP 取消 A → 无后续输入、无 out.fire，`uncer_en_reg` 保持1。候选同样继承此行为。这是门控失效/动态功耗风险，不能称功能死锁或已测功耗。独立取消清使能建议须保留 kill 当拍门控时钟，使 FU 状态真的回 idle；不能只组合拉低 E 导致丢掉清状态的时钟沿。

控制 STA 必须覆盖：redirect/RobPtr 比较 → killed → out.valid → EXU/WB 仲裁 → out.ready/fire 与状态/busy；redirect → in.ready → fire → 输入寄存使能与 ICG E；FU select/busy/state → ready → NewPipelineConnect.left.ready → OG2 响应。RobPtr.needFlush（RobBundles:193–198）包括 flag 环绕年龄和 flushItself，不能用只有 index 的 unsigned 比较。utility 固定提交 `a8ca0c6564865ee69b564d431ecbc52074ba8060` 的 ClockGate:40–44 是低电平透明的使能锁存，E/TE 有真实 clock-gating setup/hold 检查，不能按普通组合 AND 门看待。

**H04，源码推导、需活动/物理验证：融合会失去输入寄存器提供的操作数隔离。** 目前 `products.io.vs* := src*Reg`，VDot 未接受请求时源寄存器保持；融合 patch 37–38 行改成直接 `vs1/vs2`。ExeUnit:304–308 把共享输入数据接到所有 FU，与 Dispatcher 是否选中 VDot 无关。因此 Vfdiv/Vidiv 等共享输入更新时，即使 VDot 的 gated clock 关闭，RawModule 中的乘法组合逻辑仍可翻转。不能用“少寄存器/少一拍”直接宣称节能。若增加 operand isolation，其门延迟/扇出又必须纳入 product 路径 STA；直接连接乘法也改变 EXU 输入寄存器 Q 的负载，可能影响共享源路径。这里没有给出任何功耗数值或断言最终 PPA 必差。

| 晋升前阻断项 | 原因与可用验证 |
|---|---|
| 未锁定全芯片时钟/Liberty/PVT/输入输出约束 | 不能报 Fmax/面积；单独 FU 的理想端口时序不足。须在实际共享后端同约束 A/B 报 max/min timing、unconstrained endpoints、generated/gated clock 关系 |
| input/product、reduce/result 任一路 setup 负裕量，或 ICG/身份短路径 hold 失败 | 融合缩短周期数不补偿不可闭合频率；检查时钟偏斜、reset recovery/removal、边沿门控和布线后延迟，不仅逻辑层数 |
| 高扇出/转换或电容违约、门控 enable 扇出恶化 | in.fire/state/kill 同时驱动产品/元信息寄存，单元数和声称删除的声明位数无法描述实际负载 |
| kill/reset/backpressure/ROB wrap/illegal/v0/共享 div/WB 竞争未回归 | 原独立 A/B harness 不能覆盖真实 clockgate、输入 buffer、WB/ROB；须保留 DiffTest、注入响应丢失/身份错/取消泄漏负控 |
| 只有局部 II、无公平完整程序时间 | 比较真实 `cycles × 可闭合周期`；不得以仿真主机秒或 generic gate 计数代替性能/PPA |

更简单的优先项：先修正/加强软件基线，消除冗余 scalar 往返；保留窄平衡归约；若仅降低活动，验证取消后的门控恢复；如声明冗余，先看综合裁剪（高64源、结果高96常零、符号复制可能早已消除），不能把256位输入声明直接等同256个可节省触发器。共享 busy 同拍释放会拉长 ready/仲裁控制路径、改变共享 FU 契约，不是局部一行优化。若上述软件基线消除了大部分“加速”，或同约束时序抵消少一拍，保留现状合理。

本轮 [时序推导脚本](scripts/timing_counterexamples.py) 验证18,240个有效环绕年龄/flush-self组合、同拍释放反例、取消后门控使能轨迹与 E0 接受的局部状态推导；[结果](validation/timing/results.json) 明确标记非 RTL、非 STA。原融合 patch 在固定 review 副本上 `git apply --check` exit0，未应用，未修改生产。发现本地 Yosys 与 Verilator 工具路径，但未获得适用的真实 STA 工具/工艺库/PVT/SDC；不运行 generic gate 统计替代 PPA。

最终的命令回执、额外验证和状态见 [REVIEW.json](REVIEW.json)、[FINAL.md](FINAL.md)。软件/ISA工作结果分别在 [RVV 基线审查](RVV_BASELINE_REVIEW.md)、[timeout/验收审查](TIMEOUT_REVIEW.md)。
