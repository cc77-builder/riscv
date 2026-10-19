# O2 接口可行性审查

审查日期：2026-10-18。源码基点：`cd866d52`；工作分支：`local/o2-feasibility-20261018`。本文件是源码只读审查与设计建议，不是 O2 RTL 已实现、仿真通过或性能提升的证据。本次只新增本文件，未构建、提交或推送。

结论：优先评估方案 A——在 VFEX4 保留不确定时延对外合同，VDOT 内部改为最多两个在途请求的弹性 P/R 两级流水，VDOT 与 DIV 互斥并排空后切换。方案 B——迁往固定时延向量执行路径——可以研究，但涉及发射、写回预约和资源竞争，当前不宜作为第一版 O2。两者的性能收益仍须由真实运行决定。

## 1. 已由源码确认的约束

### 1.1 当前 VDOT、VFEX4 与时延分类

- [VDot.scala:21–27](../../../src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala#L21) 继承 VecNonPipedFuncUnit，要求 `!cfg.piped`、无 certain latency、128 位向量/V0 写回及 illegalInstr 异常。[FuConfig.scala:583–596](../../../src/main/scala/xiangshan/backend/fu/FuConfig.scala#L583) 配置 `piped=false, UncertainLatency()`；五类输入为 vs1、vs2、oldVd、V0、VL。
- [Parameters.scala:444–457](../../../src/main/scala/xiangshan/Parameters.scala#L444) 将 VDOT 与 VFDiv、VIDiv 共同放在 VFEX4 的一个 IssueBlock 中，Vf/V0 写口均为 port 3、priority 1，共用该 EXU 的寄存器读取配置。VDOT 当前不是独立执行端口。
- [ExeUnitParams.scala:149–181](../../../src/main/scala/xiangshan/backend/exu/ExeUnitParams.scala#L149) 的 `latencyCertain` 要求该 EXU **所有** FU 均有确定时延。只把 VDOT 改为 CertainLatency，仍不能使含两类 DIV 的 VFEX4 变为确定时延 EXU。
- [FuConfig.scala:93](../../../src/main/scala/xiangshan/backend/fu/FuConfig.scala#L93) 要求 `piped=true` 必须有 certain latency。对本次 `src/main/scala` 的 `.piped` 使用检索仅找到 VDOT 的要求；发射与写回所使用的分类来自 latency 及其派生映射。因此 **物理上做弹性流水，不等于必须把此配置标志改为 true**。A 可保留 false/UncertainLatency，但应明确记录“配置表示不确定时延接口，内部可有多请求”，并移除对单在途基类的依赖。
- [ExeUnit.scala:343–356](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L343) 对 certain latency 建立每拍推进、没有 ready 停顿的父级控制流水；[386–416](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L386) 将 ctrlPipe/validPipe/dataPipe 接到该类 FU。故不能在 VFEX4 内仅改 latency 字段后继续使用弹性停顿数据通路。

### 1.2 父级忙状态与 Dispatcher

- [ExeUnit.scala:131–159](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L131) 只有一位 busy 和一个最近接受的 robIdx。O1 的 [241–262](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L241) 只允许旧 VDOT 输出握手与新 VDOT 输入握手同拍；没有第二个同时保留的请求。直接放开 ready 会使 busy/robIdx 与真实在途集合不一致。
- [Dispatcher:537–547](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L537) 的子输出 valid 为 selected AND parent valid，而父输入 ready 是 **所有** 子 FU ready 的 AND。若未选中 FU 不 ready，所选子 FU 仍可能握手而父级没有 fire。因此 A 必须使用 VFEX4 局部的派发规则，保证 `parent.fire == selectedChild.fire`；不能仅把 parent.ready 改为 selected ready 后保留不一致的 valid 条件，也不应为本任务修改所有 EXU 的通用 Dispatcher。
- [ExeUnit.scala:436–437](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L436) 要求 FU 输出 one-hot；[481–497](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L481) 对结果/身份使用 Mux1H，并把同一个 out.ready 广播到全部 FU，没有多结果排队仲裁。**VDOT 与 DIV 互斥**是 A 降低改动范围的关键，而非已有支持并行的证据。

### 1.3 时钟门控不是多请求占用计数

[ExeUnit.scala:75–125](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L75) 的 uncertain 门控位在 in.fire 时置位，否则 out.fire 时清零。对单在途/O1 同拍交接成立；若 O2 的 R 输出，而 P 仍有效且此拍没有新输入，该位会清零，下一拍可能关闭仍需工作的 VDOT 时钟。该风险直接来自现有逻辑，是 A 必须修改的部分。

建议 VDOT 专用门控由**边沿前的非空占用、当拍接受、需要处理的 reset/redirect**维持；最后一项被取消的边沿同样必须有时钟。不能仅按“下一拍占用为零”组合关钟。DIV 的既有门控路径保持其独立合同；父级所有权不能由门控位推断。reset 的具体传播还应在真实门控开启的仿真中验证。

### 1.4 身份、写使能和异常必须逐槽绑定

- [VecNonPipedFuncUnit.scala:23–24,55](../../../src/main/scala/xiangshan/backend/fu/vector/VecNonPipedFuncUnit.scala#L23) 的 DataHoldBypass 以及 [FuncUnit.scala:109–121](../../../src/main/scala/xiangshan/backend/fu/FuncUnit.scala#L109) 的单份 RegEnable 身份会被每次输入覆盖。不能用于同时容纳两请求的输出身份。
- [VDot.scala:121–134](../../../src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala#L121) 已为 O1 避免新请求 write-enable 穿透作专门处理；O2 需要把 robIdx、pdest、vecWen/v0Wen、vpu 控制、perfDebugInfo、illegal 标记与乘积/结果作为同一请求逐级移动。合法性只在接受当拍由对应 VL/vtype/op 等决定。
- [VDot.scala:48–52](../../../src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala#L48) 当前 kill 仅针对单个输出控制里的 robIdx。O2 必须对 P、R 各自 robIdx 调用 needFlush。**接受顺序不代表 ROB 年龄顺序**，不能仅保留“最新 robIdx”或只检查队首，也不能因为一个槽取消就无条件清空另一个仍存活的槽。
- [VDot.scala:133–158](../../../src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala#L133) 的完整 128 位结果、高位清零、非法结果无 vec/V0 写使能以及反压稳定性要求继续成立；被对应 redirect 取消的响应允许撤回。reset 清空所有槽，不产生陈旧响应。

### 1.5 发射、写回与唤醒

- [IssueQueue.scala:100–129](../../../src/main/scala/xiangshan/backend/issue/IssueQueue.scala#L100) 按 ExeUnitParams 的 latency 映射建立 FU 和 Vf/V0 写口忙表；不是根据 VDOT 算术级数自动得到预约能力。
- [WbArbiter.scala:219–242](../../../src/main/scala/xiangshan/backend/datapath/WbArbiter.scala#L219) 对不确定时延 EXU 返回实际仲裁 ready；对确定时延 EXU 直接 ready=true，并断言输出不得仲裁失败。B 必须证明每拍写回不会与共享 FU/端口冲突，不能把弹性背压假设带过去。
- [Parameters.scala:508–519](../../../src/main/scala/xiangshan/Parameters.scala#L508) 这里的显式 IQ 快速唤醒连接包含 ALU/LDU 和 **FEX**，没有 VFEX4 或其他 VFEX；不要把 FEX4 当作 VFEX4。[ExeUnitParams.scala:323–340](../../../src/main/scala/xiangshan/backend/exu/ExeUnitParams.scala#L323) 还禁止非 load 的不确定时延 EXU 成为这种 IQ 快速唤醒源。A 保留现有机制；B 迁到 certain 路径也不意味着自动获得新的快速唤醒连接。
- 本次审查确认的是上述默认参数与派生规则；没有重新 elaboration 验证全部配置，也没有证明依赖链等待全部来自唤醒。因此不能承诺 O2 改善 chain256。

## 2. 两个候选方案的范围与成本

| 项目 | A：VFEX4 内弹性两级、DIV 互斥排空 | B：迁往固定时延向量执行路径 |
|---|---|---|
| 对外时延 | 保持 UncertainLatency；无阻塞最早 2 拍、目标 II=1 | 明确 CertainLatency(2) 等合同；不可随意延迟输出 |
| FU 包装 | 自有 P/R 两槽完整身份，复用乘法/归约算术；不能复用单份 non-piped 身份 | 对接 VecPipedFuncUnit/HasPipelineReg 的控制与数据时序，逐级处理合法性 |
| EXU 父级 | VFEX4 局部派发、所有权/占用、门控改造，DIV 排空后切换 | 从 VFEX4 移出并加入 VFEX0/2 等候选或新增 EXU；配置变化触及发射队列/寄存器与写回资源 |
| 输出冲突 | 互斥保证已有 Mux1H one-hot，继续接受背压 | 依赖已声明时延的预约与仲裁；必须验证不同 FU latency 碰撞及 writeV0 异常路径 |
| 唤醒 | 保留现有路径，不承诺 chain 收益 | 审核新的执行路径/旁路/预约；快速 IQ 唤醒是另一个明确的配置改动 |
| 隔离与复核 | 可由编译开关限定 VDOT/VFEX4；需新 FU、真实父级和全核回归 | 即使 VDOT 算术不变，也扩大到其他向量算术、队列与写口共享负载回归 |
| 当前判断 | 改动边界较小，但不是“只加两个寄存器”；适合第一个实现候选 | 范围更大，可能有吞吐/调度优势，也可能争抢原向量资源；先保留备选 |

B 的固定流水并不是可直接照搬的通用弹性模板：[VecPipedFuncUnit.scala:58–60,93](../../../src/main/scala/xiangshan/backend/fu/vector/VecPipedFuncUnit.scala#L58) 依赖 HasPipelineReg；[FuncUnit.scala:165–237](../../../src/main/scala/xiangshan/backend/fu/FuncUnit.scala#L165) 联合外部 ctrlPipe/validPipe 工作。不能只继承该类就宣称多在途、任意背压、取消语义已自动解决。B 是否值得选择取决于固定时延资源预约审查和真实吞吐证据，当前没有开发工期或 Fmax 的实测依据。

## 3. A 的最低可行设计合同（建议，尚未实现）

1. **两槽上限与时序**：P 存 8 个有符号乘积和请求元数据；R 存完整 128 位结果和对应元数据。单请求 E0 接受、E1 转入 R、E2 最早输出握手；在连续有效输入、无取消、输出 ready 时，每拍可接受，稳态每拍输出。不新增组合输入直达输出旁路。
2. **弹性流动**：R 有空位或本拍已输出才允许 P 前移；P 有空位或本拍前移才允许接受。输出堵塞时允许填满空 P，满后反压。R 不被取消且 valid&&!ready 时，全输出包稳定。
3. **优先级**：reset 清空所有状态；redirect 对每个有效槽独立 needFlush；本拍不接受任何新输入；存活项再按有效槽和下游容量推进。若旧 R 存活、P 取消，不影响 R；若 R 取消、P 存活，可以在设计定义的边沿转入 R，但该边沿前不得伪造 P 的即时响应。需明确测试同拍取消/输出/前移组合。
4. **身份原子性**：数据、legal/illegal、目的寄存器、目的类别、ROB/调试信息使用同一 enable 移动；输出只读 R 的身份。非法项仍作为一项正常占用流动，响应 illegalInstr，无寄存器写使能。
5. **父级局部派发**：单次输入仅选择一个 FU；以局部选择和 ownership 形成 ready/valid，断言父 fire 与选中子 fire 完全一致，其他子 fire=0；不更改通用 Dispatcher。若采用保守的 all-ready gate，必须保证子 valid 也被一致限制，且证明没有 ready-valid 组合环；建议首选清晰的 selected-ready 局部分流。
6. **DIV 互斥**：VDOT 非空时不接受任一 DIV，DIV 在途时不接受 VDOT；无跨 FU 同拍交接。最后一个响应/取消处理后，至少在下一拍确认原 FU 已静默才切换所有权。不能仅以某个取消事件就假定 DIV 输出已立即撤回；要求输出有效性/ready 与已有 DIV 合同一致，再进入新域。
7. **占用与门控**：P/R valid 为占用的真实来源；父级不得继续只用最新 robIdx 清 busy。VDOT clock enable 必须覆盖有效占用、输入接受以及状态清除边沿。禁止照搬 uncertain 单位门控位的出队即清零逻辑。
8. **兼容性**：采用独立编译期开关，原基础/T14/O1 行为保留；不要叠加两个相互矛盾的父级 handoff/流水分支。ISA、编码、合法性、NEMU、测试向量和性能镜像保持原合同。
9. **新观察器**：现有 O1 观察器只存一份 active seq/身份（[ExeUnit.scala:282–339](../../../src/main/scala/xiangshan/backend/exu/ExeUnit.scala#L282)），需升级到两项可独立取消的事务身份；不能沿用一个 seq 标记所有在途事件。

## 4. 决策和验证门槛

O1 batch 周期下降 20.02% 已证明独立请求吞吐优化有效，但 II=2→1 不等于全核性能翻倍。实现前先区分有效输入等待、上游供数/依赖和输出背压；既有观察器若只看到 EXU 入口等待，只能给该边界的事实，不能反推所有 issue queue 阻塞。

如果归因与资源检查支持 A，则先做独立两槽 FU 和真实 VFEX4 联调，再决定是否支付全核构建成本。最少需要：

- 原有 22 定向和 10,000 随机完整 128 位结果，并覆盖满流水 II=1、反压填满/排空、不同 pdest/ROB 的相邻请求和合法/非法交错；
- P/R 分别取消、同时取消、ROB 年龄与接受顺序不一致、ROB 回绕、flushItself 两值、reset 于各占用组合；
- 门控开启时，R 出队但 P 仍有效且无新输入这一最关键反例；全部取消后静默，再接受能正确唤醒；
- 真实父级中 VIDiv 与 VFDiv 的双向切换、取消和反压；父/子 fire 对等、输出 one-hot 和无丢失/重复；
- 通过后执行全核功能/异常/控制回归，再复用固定镜像做 O1/O2 公平 A/B，分别报告 batch、single、chain、stream 和真实应用收益；
- 时序/面积需单独测量。出现周期下降不能视为频率或 PPA 已改善。

这些是拟实施合同与验收项，不是本文件已完成的测试。源码审查没有证明 A 必然达到应用目标，也没有给 B 的收益作保证。
