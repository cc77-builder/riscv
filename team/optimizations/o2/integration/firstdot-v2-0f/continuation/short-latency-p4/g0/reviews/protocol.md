# P4-G0：一拍算术、两槽弹性候选的协议只读评审

评审日期：2026-10-29；执行者：Agent /root/p4_protocol。本记录只读现有源码，并在独立目录运行抽象 Python 事务模型。没有修改 RTL、构建硬件、运行目标仿真或改动 Git。模型通过不等于 RTL 通过。现行生产选择仍是 0f（O2 + H1 + DIV 取消保持修复）。

## 1. 结论与唯一候选

**协议层面有条件 GO：值得进入一次隔离的最小候选实现及局部验证；此处不授权实施、不认可新面积/时序/全核结果。** 未发现必须改 ISA、改变父级 DIV 接收协议、加入早唤醒或扩大后端结构才能达成的协议障碍。最终 G0 决定仍须合并组合路径与同约束 PPA 风险评审。

唯一候选保留现有 P/R 两个槽及 pipelineStatus 结构，R 是输出头槽，P 是等待尾槽：

- 把 P 槽的 8×16=128 位乘积保存，改为 32 位已完成点积结果；R 仍保存低 32 位。
- 接收时组合执行既有 8 个有符号乘法和 17/18/19 位平衡加法树；合法结果符号扩展到低 32 位、输出高 96 位仍清零。
- 当没有 live P、且 R 本拍可替换时，直接把**新请求的完整结果与身份**写入 R；否则新请求写入 P。
- 旧 P 总是优先于新请求进入 R。P、R 的 ctrl/perf 都随各自结果整体存取。
- 输出仅来自已经寄存的 R；禁止输入→输出组合穿透，禁止 P→输出组合旁路。
- 保留 uncertain-latency、两槽容量、实际握手和父级排他；不把 FuConfig 改成 CertainLatency(1)。

“一拍”指无前驱等待、无反压和无取消时，接收边沿 E0 写 R，最早 E1 响应。满队列或等待 R 时仍是可变延迟，不能承诺任意 accept 的固定一拍响应。长期输出 ready 时 II=1；这是现有 O2 已具备的吞吐能力，候选主要降低无排队的内部延迟。

## 2. 已核实的现行源代码

| 事实 | 当前源位置 |
| --- | --- |
| P 保存乘积/ctrl/perf；R 保存低 32 位结果与完整 ctrl/perf | src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala:38-51 |
| 每槽用自身 ROB 身份取消，reset 清除可见活动；R 可替换及 P 搬移/就绪公式 | 同文件 59-65 |
| 任意 redirect 禁止新接收；只有 live R 提供输出；高 96 位为 0 | 同文件 67-74 |
| 非法配置判定、合法目的类、异常与完整控制包 | 同文件 57-58,82-92,127-139 |
| 现行 P/R 状态更新与完整身份搬移 | 同文件 94-107 |
| 阻塞响应仅可被匹配 kill/reset 撤回 | 同文件 141-147 |
| 低 8 字节按有符号 int8 乘法；16→17→18→19 位加法树 | src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala:17-20,34-48 |
| 已有独立组合算术 top 恰好串接 Products 与 Reduce；无周期协议 | 同文件 51-68 |
| 父级占用直接读取两个原始槽位 | src/main/scala/xiangshan/backend/exu/ExeUnit.scala:85-91 |
| VDot 门控按原始占用 / 实际接收 / reset 开钟 | 同文件 146-150 |
| DIV 保留独立 busy / ROB、实际 out valid 与全部 child ready 等待 | 同文件 164-186 |
| 父级仅向被选 child 下发，握手原子、禁止 VDot 未排空即切 DIV | 同文件 300-333 |
| 父级结果选择及 out.ready 无额外寄存 | 同文件 696-706 |
| needFlush 比较 ROB 环形代际、位置及 flushItself | src/main/scala/xiangshan/backend/rob/RobBundles.scala:187-198 |

完整源 SHA-256 见 source-pins.json。上述为当前源读取得出的静态事实；不是候选硬件验证。

## 3. 精确的抽象状态合同

下式都是边沿前状态；R 比 P 先接收。fire 是原有 Decoupled 握手，acceptedPacket 是本次输入的结果、ctrl 和 perf 一体化包。

~~~
killP = pValid && pCtrl.robIdx.needFlush(flush)
killR = rValid && rCtrl.robIdx.needFlush(flush)
liveP = pValid && !killP && !reset
liveR = rValid && !killR && !reset
rReady = !liveR || out.ready
moveOldP = liveP && rReady

in.ready = (!liveP || rReady) && !flush.valid && !reset
out.valid = liveR
out.bits = R 的保存值（data = zero96 || savedLow32）

directNewR = in.fire && !liveP && rReady
enqueueNewP = in.fire && !directNewR

pValidNext = (liveP && !moveOldP) || enqueueNewP
rValidNext = (liveR && !out.fire) || moveOldP || directNewR

写 P：仅 enqueueNewP 时，保存 acceptedPacket
写 R：moveOldP 时保存旧 P 包；否则 directNewR 时保存 acceptedPacket
~~~

moveOldP 与 directNewR 互斥。旧 R 的输出、旧 P 的搬移、这拍新输入都使用边沿前身份，不能用新输入的 ROB/pdest/vpu/perf 覆盖仍在响应的旧请求。原来的 in.ready 公式可以原样保留。

| 边沿前 live 槽与事件 | 边沿后的槽 | 核查要点 |
| --- | --- | --- |
| 空，accept X | R=X，P 空 | X 只会在下一周期成为响应 |
| R=A，ready，accept X | 本拍响应 A；R=X | 同拍弹出/接收，不能把 X 身份给 A |
| R=A，blocked，accept X | R=A，P=X | R 全包稳定，第二槽真实容纳 X |
| R=A/P=B，blocked | 原样保持；in.ready=0 | 不可接受第三个请求 |
| R=A/P=B，ready，accept X | 响应 A，R=B，P=X | 响应/旧 P 搬移/新接收三者重叠 |
| R=A/P=B，ready，无新输入 | 响应 A，R=B，P 空 | 两槽顺序保持 |
| 仅 P=B 存活（例如本拍 kill R） | 这拍不输出 B；边沿将 B 移至 R | 禁止 P 组合穿透；flush 当拍不接收 |
| 仅 kill P，R blocked | R 保留，P 清空 | R 身份和数据不得变化 |
| kill R 且 P 存活 | 撤回旧 R，旧 P 移 R | 不能假设杀头必杀尾，接收先后不等同 ROB 年龄 |
| 同时 kill P/R | 两槽清空 | 原始占用仍为 clearing edge 供钟 |
| 无关 flush，R ready | 可响应 R、可搬移旧 P；不接收新请求 | 禁止把所有 flush 当成清空队列 |
| reset，任意槽/ready/valid | 两槽清空；无输入/输出 fire | reset 开钟清空与禁止握手共同生效 |

包内未初始化的无效槽数据没有语义；valid 决定可见性。禁止把“data 只存 32 位”扩展为删减 ctrl/perf、把两个槽共用一个 ROB 身份或一个异常标志。

## 4. 取消、异常、身份与 DIV 共用不变项

1. 非法条件保留：vill、非 e8、非 m1、vm=0、vstart 非零、vl 非 8、非 s8x8 操作。异常结果为 0；vecWen/v0Wen 同时关闭。非法请求仍是正常占槽事务，不能静默丢弃。
2. 外部结果永远完整 128 位；高 96 位清零。负和仅在低 32 位采用补码，不是对 128 位整体符号扩展。
3. ROB 的 flag/value、pdest、目标类、vpu 整包、perf 整包、exception 保持请求绑定。允许输入口持续变化而旧 R 反压不变。
4. 匹配 kill 优先于可见输出。任意 flush 禁止新接收；无关 flush 不撤回未命中的旧响应。
5. 继续向父级输出原始 P/R valid；不能改成 kill 掩码后的 live 状态。否则全 kill 周期可能丢掉清空边沿，且 DIV 排他边界发生变化。
6. VDot→DIV 继续等待前一拍原始槽位排空，不能因为最后一个 response 当拍会 fire 就允许 DIV 同拍接收。DIV→VDot 继续等待 divBusy、child out.valid 和真实 child ready 全部满足原条件。
7. DIV 的浮点双 lane、整数除法、SQRT、取消保持与实际接收路径全部保留。短 VDot 只缩短其自身持有时间；不能顺带拿掉 ready 依赖或合并之前未采用的 C1/C2/C3 逻辑。
8. piped=false / uncertain latency 继续有效，且本轮不新增早唤醒或绕过仲裁。父级外部接口保持不变。

## 5. 观察器是后续实现的必要配套改动

现有 ExeUnit.scala:479-482 把每个 accept 的 seq 写 P，只有 MOVE 才把 Pseq 写 R；507 固定打印 latency=2。候选 directNewR 路径不产生 P 搬移，因此**原观察器不能直接验证一拍候选**。

后续实施必须冻结旧 schema 和旧 checker，另开明确版本的观察合同：

- directNewR 时将新 seq 与 R 包同步，enqueueNewP 时才更新 Pseq；moveOldP 时 Rseq 取旧 Pseq。
- 每个 accept 明确记入目标槽/直接写 R 事件；响应 seq、ROB/pdest、完整 128 位结果、异常、vpu/perf 对齐。
- MOVE 表示真实 P→R 搬移，不再要求每个请求都存在 MOVE，也不能伪造 MOVE=accept。
- state 仍记录原始 valid、live/kill、ready、direct、move、占用和 DIV 状态。schema 明确 minimum_latency=1、slots=2、uncertain=true。
- checker 必须拒绝重复响应、丢失、乱序、旧身份给新结果、flush 周期 accept、未经真实 parent accept 的 child accept、全 kill 后残留占用。
- 严格区分新 observer 回归和已有 O2 历史 PASS。功能性父级 dispatch/gating 不需要因此修改，观察器改动不准反馈功能逻辑。

## 6. 抽象主机模型的本轮结果与边界

abstract_model.py 对四种物理 P/R 占用、reset、ready、incoming valid、incoming illegal，以及无 flush / 四种独立 kill 掩码，共 **320 组单步组合**审查状态方程。独立参考为“过滤已取消旧包 → 仅弹出原有物理 R → 在尾部追加实际 accepted 包”，比较完整不透明包及顺序。

结果 ABSTRACT_TRANSITION_AUDIT_PASS；另审查连续 8 笔无反压请求均一拍响应、每拍接收，以及阻塞时接受序列 [true,true,false,false]、满槽同拍响应/搬移/新接收。完整结果和脚本 SHA 见 abstract-model-result.json。

边界：此模型没有 Chisel、Verilog、真实 ROB 比较器、ClockGate、真实 DIV、算术向量或 STA。独立 kill 掩码只抽象每槽已计算的 kill，不证明 ROB 代际计算。**只支持方案层面的顺序/容量/取消状态可行性，不能替代 RTL/真实父级验证。**

## 7. 进入局部候选验证的协议门禁

| 门禁 | 必须满足 |
| --- | --- |
| 算术 | 原 22 组定向与 10,000 组随机数据，逐项核查完整 128 位；非法结果 0、禁写回 |
| 单槽无阻塞 | accept→首个可用 response=1，禁止同周期透传；连续输入 II=1 |
| 弹性 | 满两槽、持续反压、全包稳定、pop/move/push 重叠、输入不停变化、无丢失/重复/乱序 |
| 取消/reset | 两槽分别与同时取消、头取消尾存活、无关 flush、匹配/非匹配 self、ROB 环绕、反压时取消、reset during blocked |
| 身份 | 交错 pdest、vec/v0、vpu/perf、合法/非法事务；输入更新不污染旧输出 |
| 真父级 | 原子握手及输出 one-hot；VDot↔VIDiv/VFDiv/SQRT，两槽未排空禁止切换，cancel clearing edge 和实际 child ready 边界 |
| 模式隔离 | 原 O2/旧 T14/O1 路径及失败配置拒绝按合同检查，新候选只在显式构建开关启用 |
| 观察器 | 新 schema 独立；故障注入能识别身份错绑、kill 后输出、flush 接收、非法写回、缺响应 |
| 最终资格 | 上述局部协议门禁和同约束 PPA 筛选都通过后，才可申请后续全核/NEMU/同镜像周期验证 |

NO-GO 条件：任何一项依赖“满槽强接收、输出穿透、取消时忽略身份、共用单身份、放松 DIV 排他、改 CertainLatency、静默复用旧观察器”才能工作；或局部验证无法维持已冻结协议。通过该评审也不等于生产采用；面积和时序可能使最终候选否决。

## 8. 存储与组合路径的协议相关取舍

仅数源级结果/乘积保存：现行 P=128、R=32，共 160 位；候选 P=32、R=32，共 64 位，少 96 个逻辑保存位。ctrl/perf 和 valid 数量不变。该数字**不是综合面积下降保证**：输入至 P/R 同时含乘法、三层归约及合法性/写入选择，R 又有旧 P/新输入选择，映射缓冲/门控/时序修复可能抵消寄存器减少。真实面积、时序、功耗均仍为 NOT_TESTED。
