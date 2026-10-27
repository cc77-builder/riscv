# DIV 门控只读语义归因与 C2 可测假设

2026-10-25。静态审查与历史轨迹复算；没有修改生产 RTL，没有重新生成硬件、运行仿真、综合或 STA，也没有推送或发布 Issue。

**结论：有足够证据开启一个边界清晰的 C2“证明／合同”步骤，尚不足以直接进入 RTL。** 值得核查的假设是“固定 DIV 实现的空闲就绪不变量”，利用它将门控启动路径与高扇出 DIV ready 网络分离。保留当前修复版 0f12df6；C1 未通过筛选的事实不变。若不能证明新不变量，不实施此写法，也不以允许额外时钟的方式放宽严格门禁。

## 1. 版本与源码定位

- 现行修复版：0f12df675378556670afd0dd2153f47fcb330610。
- 独立 C1：3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66。
- 本地输入精确路径、SHA256、命令及返回码见 predicate-audit.json、audit-command.json。
- 仅新建本目录内 audit_predicate.py、审计输出和本文。脚本在读取前后核验 15 个输入文件哈希相同。

| 证据 | 位置／含义 |
| --- | --- |
| 修复版 ExeUnit.scala | 126–144：两个保持位按实际 child fire 置位，完成／匹配取消清零，门控为 fire OR hold |
| 修复版 ExeUnit.scala | 166–186：divBusy、ROB、取消、完成、accept；occupied 还包含两个 raw output valid 及任一个 DIV 未 ready |
| 修复版 ExeUnit.scala | 300–333：分派、allowInput、selected-ready、父子同拍接收及互斥断言 |
| C1 ExeUnit.scala | 130–148：保持项改成 busy AND owner，启动项仍是 child fire |
| C1 ExeUnit.scala | 170–195：busy／owner、ROB 和 occupied |
| C1 生成 ExeUnit.sv | 198–227：child fire、occupied、allowInput、child valid 的实际生成方程 |
| C1 生成 ExeUnit.sv | 310–334：父级 busy／owner／ROB 寄存器更新 |
| C1 生成 ExeUnit.sv | 606–626：三个 ClockGate 实例绑定 |
| utility/ClockGate.scala | 34–45：低电平锁存 TE OR E，输出 CK AND EN |
| C1 parent-map-01/map.ys | synth -flatten -noabc 后统一 ABC 映射；普通 Chisel wire 别名或仅抽取模块不自动隔离共享逻辑 |

本表源码路径相对于对应 repo；生成文件位于对应成本输出 parent-cost-01/rtl。精确绝对路径可在 JSON 中查到。未对旧材料覆盖或补造资格。

## 2. 为什么整数门控路径会从浮点 ready 起步

定义 B=divBusy，T=ownerIsFp，RI/RF 为整数／浮点 ready，OI/OF 为 raw out.valid，V 为 VDot 两槽占用，F=flush.valid，R=reset。合法 FU 类型只有整数、浮点、VDot，分别用 SI、SF、SV 表示互斥译码。

生成 SV 明确给出：

~~~text
divOccupied = B | OI | OF | !(RF & RI)
allowInput = !divOccupied & (SV | !V) & !F & !R
childValid_j = parentValid & allowInput & S_j
fireI = RI & childValid_I
fireF = RF & childValid_F
E_I(C1) = fireI | (B & !T)
E_F(C1) = fireF | (B & T)
E_VDot = V | fireVDot | R
~~~

因此整数启动也需要 RF，浮点启动也需要 RI。这是父级互斥／排空策略引入的真实依赖，不是 STA 把无关模块误当成时序起点。C1 的状态编码删除两份 hold，**没有删除这一接收依赖**；不能声称只改 owner 就应该解除它。

在合法 DIV 译码下可展开为：

~~~text
P_j = parentValid & S_j & !B & !OI & !OF & !V & !F & !R
fire_j = P_j & RI & RF
~~~

单独将门控 fire 写成 fu.io.in.valid，在现有分派中虽与实际 fire 相等（allowInput 已包含 RI&RF），但仍沿用整个 ready 网络，不能达成路径隔离。把相同表达式复制成另一根 Wire 也会被 flatten／ABC 重新共享，不能把源码多写一份当成实现了独立缓冲树。

## 3. 不能采用的捷径

### 无条件 valid 提前开钟

E_j=hold_j OR (parentValid AND S_j) 在当前轨迹复算中，有 **5,321 拍**使本不该开的 DIV 门控额外打开。一个直接例子是 cycle 11447：VDot 两槽尚未排空，输入正在等待切换到整数 DIV；父级没有接受 DIV，原 DIV 时钟也关闭，raw valid 写法会额外唤醒整数 DIV。

这里统计的是原日志的组合表达式投影，**不是已经修改 RTL 后得到的仿真结果**。它足以否定“与现有逐拍门禁精确一致”，不用于推断芯片功耗。

### 取消信号直接掩码 hold

取消当拍必须由旧 B／hold 保持子单元边沿。E=oldE AND !cancel 会让 DIV 状态机吃不到 flush，父级却已经清 busy，可能导致下一事务无法正确恢复。这违反原状态合同，不是优化选择。

### 先寄存门控启动或 ready，再使用下一拍结果

这会改变首拍接受与子单元实际时钟的对应关系，除非同时改变整个接收协议。当前题目的候选是保持协议与周期不变，因此不属于这次 C2 的范围。

### 放宽旧合同来容许额外脉冲

C1 原抽象合同允许“父级取消后，子单元暂留输出或未 ready”的保守状态。在这个合同下 P_j 不等于 fire_j：例如 B=0、OI=OF=V=F=R=0、parentValid=SI=1，但 RI=RF=0，则 P_I=1、fireI=0。

audit_predicate.py 检查 6,144 个 Boolean／合法类型组合，发现 12 个不受新不变量约束的门控差异。因此**不能直接引用 C1 状态模型 PASS 为删掉 ready 背书**。

## 4. 唯一建议继续核查的 C2 假设

只改变 DIV ICG 的启动项为 P_j；保留实际 dispatch、child.valid、parent.ready、accept、ROB 更新、完成／取消优先级不变，hold 沿用 busy／owner。不新增状态寄存器，不把 P_j 当作接受信号：

~~~text
E_I_candidate = (B & !T) | P_I
E_F_candidate = (B & T)  | P_F
~~~

它真正从 ICG 的启动锥中去掉 RI/RF，但必须先证明：

~~~text
在本机固定 DIV 实现、有效初始化与父级协议下：
!reset && !divBusy  =>  RI && RF
~~~

若此不变量成立，P_j 必然等于旧 fire_j，两个候选 E 与原 E 逐拍相等：没有提前接受、没有新增空闲脉冲，也保留取消边沿。无需把它包装成容许多开钟的“提前唤醒”。

**这是假设及证明义务，不是已有 RTL 等价证明。** 也可以使用更弱的 P_j=>RI&&RF；推荐先检验上述较易追溯的空闲不变量。证明时应绑定当前固定的 DIV 子单元实现，不能无条件推广到可替换 FU。

静态支持：

- VIDiv.scala 25–43：忙时使用已保存 ROB 产生匹配 flush；46–47 将 ready/out 直接接到 VectorIdiv。
- VectorIdiv.scala 38–73：复位 idle；flush 同拍边沿回 idle；output handshake 回 idle；ready 就是 idle 状态位。
- VFDivSqrt.scala 51–61：同样从保存 ROB 生成 flush；86–87：输入 ready 为两个 lane 的 AND，输出 valid 为两个 lane 的 AND。
- VectorFloatDivider.scala 33–59：每个 lane 内仅选 DIV 或 SQRT 接受，ready 是两者 ready 的 AND。
- VectorFloatDivider.scala 175、193–224：DIV 状态复位 PRE_0；flush 回 PRE_0；输出 handshake 回 PRE_0；start_ready 为 PRE_0 位。
- fpsqrt_vector_r16.scala 78、569–571、1479–1492：SQRT 也有对应的 PRE_0／flush／完成恢复关系。

这组结构使不变量有合理的归纳路线：bootstrap reset 后所有子 FSM ready；接受只改变 owner；busy 期间 owner 时钟持续；完成或匹配取消时父子同一边沿回空闲；未选中的模块保持空闲。**还必须证明父子 flush 的 ROB 身份相同、浮点所有 lane 的完成握手一致、复位边沿确实送达，不能只看状态枚举就跳过。**

## 5. 本轮只读复算结果

基于 C1 已冻结的父级日志 SHA256 a38e8d806dc84c46b16af6f3c17323ee5f404ba3eb221d94fa15e127bf22ee6d：

| 项目 | 结果 |
| --- | ---: |
| 读取历史拍数 | 35,075 |
| 非 reset、B=0 的拍数 | 17,666 |
| 这些拍中任一 DIV 不 ready | 0 |
| P_j 识别出的 DIV 启动 | 1,744 |
| P_j 与实际 child fire 不同 | 0 |
| hold OR P_j 与实际 DIV 门控不同（含 TE） | 0 |
| raw valid 写法多开 DIV 门控拍数 | 5,321 |

Boolean 表在新不变量允许的 4,992 个组合中没有 E 差异；**这只证明“若不变量成立，则公式相等”的组合引理**，不证明 RTL 总能保持不变量。轨迹观察也不能替代未出现输入的证明。

C1 现有动态刺激为 DIV，没有新增 SQRT 动态资格。本轮没有新全核／NEMU／周期／面积／时序数据。

## 6. 进入 C2 RTL 前的门槛与停止条件

1. 用实际父子状态机证明空闲不变量，或给出保守、可机检的归纳抽象；明确有效 reset／TE 合同。验证 SQRT、各浮点 lane 不同完成时刻、输出反压、取消与完成重叠、ROB 回绕、无关 redirect、取消后保留 valid、持续等待的另一个类型请求。
2. 若任何允许状态出现 P_j=1 且 RI&RF=0，则不能用“只多一个无害时钟”豁免；停止这个候选。
3. 若证明通过，用户获知具体 RTL 文件与改法之后，才可建立单独 C2 候选，保留修复版和 C1。重新执行完整状态／FU／真实父级门禁，不能继承 C1 的功能 PASS。
4. 仍先同约束成本筛选，再决定全核。除目标整数 ICG 外，必须同时保住 VDot r2r、ready、所有 ICG 和既定面积上限；C1 还有两类退化不会因 P_j 自动消失。
5. 合成后还需检查 ICG 锥中实际不再出现 DIV ready 起点。仅 RTL 方程改变却又被映射为共享长路径时，假设没有达到结构目的，不能以一次偶然采样或改约束择优。
6. 不声称缩短 ICG.E 等于整核 Fmax、周期或功耗改善。若证明成本过高，或结构变化仍不能通过整体筛选，就结束门控硬件探索，转入现有软件应用优化。

## 7. 复算入口

本目录 audit_predicate.py 仅读取已固定输入和历史日志。它拒绝覆盖 predicate-audit.json；移机运行应先复制脚本到新的输出目录，并提供同路径或相应经过审核的定位调整。audit-command.json 保存本次命令和 exit 0，audit.log 保存输出。

本报告不替代主归因的网表扇出／路径数据，只给出 RTL 语义及下一假设的边界。最终是否投入 C2，应结合主审查的映射成本与其他退化路径一起判断。


## 8. C2-G0 必须单独审查的三个边界

### 8.1 TE=0 时的父子复位不能从历史结果外推

本轮成本生成物 ExeUnit.sv 的 338、423、502 行把同一个 reset 端口送到三个 FU，但它们的 clock 是各自门控输出。ClockGate 仅锁存 TE OR E，没有“reset 自动旁路”。因此“复位接线相同”不等于“子单元一定采到复位边沿”。

现有 parent_test.cpp 509–518 行明确在 DIV 动态复位时使用 TE=1；533 行随机复位遇到在途 DIV 同样置 TE=1。TE=0 复位组 496–508 行主要为 VDot 两槽；不能把这些日志写成 DIV TE=0 资格。

可作为待证明归纳步骤的情况是：**已经正确初始化**且旧 B=1 时，旧 owner hold 在 reset 当拍仍为 1，ICG 低电平锁存后送出复位边沿，随后 B 与子 FSM 同时清零。旧 B=0 时所有子 FSM 已 ready 是归纳前提，不能把它循环地当作初始化证据。还必须明确：
- 初始 reset 至少一次实际送达每个 DIV；现合同可用有效 TE=1 的 bootstrap reset。
- TE 与 reset 的时序满足低电平锁存和边沿采样合同；不支持上电未知状态或任意截断时钟脉冲。
- 新生成的全核 reset／ResetGen 配置与证明的父子边沿关系相符；当前观察器要求共用仿真 reset，不能自动替代其他 reset 分发配置。

如果允许父级已清 B、子 FSM 因关钟未复位且不 ready 的起始状态，P_j 会多开钟，旧 fire 不会；新不变量无从成立。C2-G0 应拒绝该无约束环境，或明确它本就不属于经过验证的启动合同；不能静默忽略。

### 8.2 取消：父级 ROB 与真正子事务 ROB 必须绑定

C1 ExeUnit.scala 180 行在 parent divAccept 保存 ROB；591 行把同一 source.robIdx 送给子单元。VecNonPipedFuncUnit.scala 23 行在真实 child fire 保存 outCtrl。父子 fire 等价加“不重叠接受”才使两个寄存器表示同一事务。

VIDiv.scala 25–43、VFDivSqrt.scala 51–61 的 thisRobIdx 选择规则是：
- 当前整体 io.in.ready=1：使用正在输入的 ROB；
- 否则：使用保存的 outCtrl.robIdx。

要证明 busy 清零后所有 ready，不能仅假设 parent cancel 就等于全部 child flush。必须证明在 B=1 的正常在途 DIV 上，所需的孩子在取消边沿前还使用已保存的相同 ROB；并检验“ready 已变回 1 但父级 B 还未清”的可能状态。若这种状态存在，输入 ROB 可能变化，从而两个 needFlush 结果不同。

已有结构提供的路线是：子 ready 只在 idle；owner 完成释放与 parent divOutFire 是同一事件；父级不允许完成当拍重接收。所以父子 busy／idle 的采样可以建立同步关系。ROB flag/value、flushSelf、回绕次序仍需纳入证明，不以具体日志中的 ROB 数值代替。

### 8.3 VFDiv、SQRT、特殊值与两 lane 汇合

VFDivSqrt 的两个 64-bit lane 收到相同 start-valid、flush 和 finish-ready，但完成延迟可能不同。整体 out.valid 是两个 lane finish-valid 的 AND，送回每个 lane 的 finish-ready 又是 parentOutReady AND 整体 out.valid（VFDivSqrt.scala 60、86–87）。因此先结束的 lane 需要在 POST 保持，直到另一个完成。C2-G0 必须包含这个等待状态；不能把“某个 lane 完成”等同于父级 complete。

每 lane 的 VectorFloatDivider 又有 DIV 和 SQRT 两个子 FSM（33–59 行），只向被选中的一个发 start-valid，ready 取两者 AND。检查：
- DIV 特殊值、非正规数路径的不同 POST 阶段与 io.is_vec_i；不能假定统一固定延迟。
- SQRT early_finish 可从 PRE_0 快速进入 POST_0；正常迭代、特殊值和不同格式同样要证明 finish 握手／flush 后回 PRE_0。
- 同时取消与结束时 flush 优先，旧门控 edge 仍到达；无关 redirect 不清 parent B。
- 所有组成 ready 的 FSM 都回到 PRE_0／idle，才可推出整体 RF=1。只证明一个 64-bit DIV lane 不够。
- 常态合法 one-hot 状态及 reset 入口属于证明域；任意状态位故障或替换子单元后的行为不在现结论内。

建议将这些控制状态以非确定完成延迟、特殊值分支、各 lane 独立进度建模，而不是重写浮点算术。该模型若有充分的源码映射及机检归纳证明，可以作为 C2-G0 结果；现有 C1 数据只提供复核样本，绝非该证明。后续新候选仍需真实 SQRT／多 lane 刺激及完整原门禁。

**当前建议准确表述为“开启 C2-G0 的固定子 FSM 不变量证明与合同评估”，不是“已可全域删掉 DIV ready”。** 正式生产 RTL 仍未修改。
