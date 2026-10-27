# C2-G0 整数 DIV 控制不变量审查

2026-10-25，独立只读子 Agent。结论：**在父、整数 DIV 和全部内部状态机已获得有效初始化边沿后，固定 0f12df6 源码的整数路径支持无占用必 ready，并有源码绑定的有限状态闭包检查。初始同步复位能否穿过时钟门，必须由系统复位审查闭合；不能在这里隐含假定。**

本目录仅包含分析和 Python 检查；未修改 RTL，未启动 RTL 仿真、综合或 GitHub 写入。数学抽象不是自动 RTL 等价证明、算术证明或全核验证。主任务负责与 FP/SQRT、真实复位分发及系统 ROB 模型组合。

## 1. 固定身份和源码依据

- 主源码 HEAD：0f12df675378556670afd0dd2153f47fcb330610。
- yunsuan 子模块 HEAD：cadd3c2f43096e253d61296b33ac697be8354e29。
- 8 份源码身份在 [inputs.json](inputs.json)，6 份已存在生成 RTL 的身份在 [generated-inputs.json](generated-inputs.json)。主源码及 yunsuan 无本轮改动。
- 本模型检查前后复核 8 个输入 SHA256；生成 RTL 仅作只读交叉核查，不是本轮重新生成。

以下路径相对固定源码仓库：

| 位置 | 控制事实 |
| --- | --- |
| src/main/scala/xiangshan/backend/exu/ExeUnit.scala:126–144 | 对 DIV，旧 hold 持续开钟到 out.fire 或 divCancelled；接受当拍 fire 直接开钟；取消当拍仍使用旧 hold 供给清理边沿 |
| 同文件:166–186 | divBusy 在父级接收 DIV 时置位，在匹配 ROB 取消或任一 DIV out.fire 时清零；divReady 为整数和浮点 ready 的 AND |
| 同文件:300–333 | allowInput 必须没有 DIV occupied，无 flush、无 reset；父子 fire 相等且 one-hot；不允许完成当拍绕过旧占用直接切换 |
| 同文件:573–583 | 子 ctrl.robIdx 接自同一 source.bits.robIdx |
| src/main/scala/xiangshan/backend/fu/wrapper/VIDiv.scala:25–47 | ready 时 thisRobIdx 选输入，busy 时选 outCtrl；flush=needFlush(thisRobIdx)，ready=VectorIdiv.ready，outvalid=VectorIdiv.outvalid；内部 out_ready=外部 ready AND valid |
| src/main/scala/xiangshan/backend/fu/vector/VecNonPipedFuncUnit.scala:23 | outCtrl=DataHoldBypass(in.ctrl,in.fire) |
| utility/src/main/scala/utility/Hold.scala:65–68 | DataHoldBypass 用相同 valid 的 RegEnable，接受当拍旁路新值 |
| src/main/scala/xiangshan/backend/rob/RobBundles.scala:193–195 | needFlush 对相同 ROB 和 redirect 是相同纯布尔表达式，包含 flushItself 相等判断及 isAfter |
| yunsuan/src/main/scala/yunsuan/vector/VectorIdiv/VectorIdiv.scala:32–73 | top 状态 idle/divide/output；flush 最高显式优先回 idle；idle 接受后 divide，finish 后 output，输出 fire 后 idle；ready=idle |
| 同文件:93–107、115–138、150–177、190–221 | 8 个 I8、4 个 SRT16、2 个 SRT32、2 个 SRT64，共 16 个子单元，所有子 in_valid=top.divide，out_ready=top.output，flush 直通 |
| 同文件:241 | finish 是上述全部 16 个 outvalid 的 AND，不能依据 sew 只等选中的部分 |
| I8DivNr4.scala:29–55 | idle→pre→iter/post→output；early_finish 和 iter_finish 决定路径；output 在 out_ready 后回 idle；flush 回 idle |
| SRT16Divint.scala:65–116 | idle→pre_0→pre_1→iter/post→output；相同输出／flush 清理协议，适用于 16/32/64 位实例 |

已存在生成 RTL 明确为同步复位：VectorIdiv.sv:239–243、I8DivNr4.sv:74–78、SRT16Divint.sv:392–396 均为 posedge clock 内的 if(reset)，不是异步 reset 事件。

## 2. 为什么完成与反压不会留下子 DIV 未 ready

父级接收整数 DIV 的边沿，parent divBusy 与对应 hold 置位，VectorIdiv 从 idle 转 divide；16 个内部单元当拍仍 idle。随后所有内部单元看到 top.divide，分别按自身数据走 early 或迭代路径，先完成的在 output 等待。

top 只有在全部内部单元 output 时才进入 output。下一边沿，所有内部 output_ready 都为 1，所以它们统一回 idle：

- 若外部 ready=1，parent、top 和全部内部子在同一边沿释放，下一拍 B=0、整数 ready=1。
- 若外部 ready=0，全部内部子先回 idle，top 留在 output 保持已寄存结果。之后真正 out.fire 的边沿只需清 top／parent；内部已 idle。

因此不能把内部结果等待误写成“外部反压令所有内部单元一直占用”。实际内部清理比外部完成更早或同拍。已有结果寄存器位于 top.divide，证明不涉及算术数据的正确性。

## 3. 为什么匹配取消不会留下未 ready

整数活跃时 top 不在 idle，所以 VIDiv 使用已保持 outCtrl.robIdx。它和父 divRobIdx 在同一次接受、从同一 ROB 输入捕获；接受边沿的子时钟由 in.fire 本身保证。活动期间不允许第二次输入，双方 ROB 不变。因此，无论 ROB flag 回绕、flushItself、自身或更年轻比较，双方 needFlush 的输入完全相同。

parent 的 divCancelled 是 B AND 相同 needFlush。整数 active 时旧 hold=1；取消当拍不遮断 hold，故子收到清理边沿。父清 B，top 和全部 16 内部子 flush 回 idle，同时 hold 清零。无关 redirect 则不清任何活跃整数状态。完成和取消同时发生时也回同一 idle 状态。这里采用的是相同表达式和捕获关系的论证，不是把“所有 flush 都会取消”当成前提。

模型的 1536 个 ROB 捕获等式组合仅用于检查实现的等式逻辑；位宽无关结论来自上述源代码等式。完整 RobPtr 空间与 FP 绑定由主模型审查，不把 3 位诊断枚举冒充全 ROB 穷举。

## 4. 有效初始化之后的机器检查

[prove_int.py](prove_int.py)手工转写上述控制转移，在每一个可达状态遍历 1152 组输入，直到状态集合不再增加。这是有限状态抽象的闭包检查，覆盖任意长执行序列，不是只跑有限拍日志。

输入包括 reset、TE、选择单位、无／无关／匹配 redirect、early_finish、iter_finish、其他子完成、外部反压及另一 DIV 的完成。early/iteration 完成允许任意等待和任意发生，不假定完成期限或公平性。这放宽了真实数据条件，因而安全性 PASS 不依赖特定除数、零、溢出等数据。

每次仅抽取**任意一个**内部子单元，保留精确控制状态；其余 15 个用一个非确定 all-other-finished 表示。top.finish 仍必须要求当前代表子 output。这是源代码 AND 的必要条件，不是假定待证明结论。对每一实例都能使用同样局部归纳，因此覆盖 8×I8、4×SRT16、2×SRT32、2×SRT64。SRT 位宽只影响被放宽的算术完成条件，不影响控制拓扑。

模型里的子状态统一编号为 idle=0、pre/pre_0=1、pre_1=2、iter=3、post=4、output=5；I8 没有状态 2。编号是抽象标签，不是声称实际 one-hot 寄存器使用同一编码。

| 模型 | 可达状态 | 检查转移 | 结果 |
| --- | ---: | ---: | --- |
| 任意 I8 代表子 | 9 | 10,368 | PASS |
| 任意 SRT16/32/64 代表子 | 10 | 11,520 | PASS |

检查组合不变量包括：

- parent 无任何 DIV 占用 ⇒ top idle（即整数 ready）。
- 当前 owner 不是整数 ⇒ top idle；整数 hold 与整数活跃相符。
- top idle ⇒ 代表内部子 idle。
- top output ⇒ 代表内部子为 output 或 idle。

有效初始化提供基例；可达集合闭包逐步保持这些关系。9 类场景都有最短机器轨迹保存在 [proof.json](proof.json)：TE=0 活动中复位，divide 取消，output 反压取消，完成/取消重叠，output 反压时内部先清理，同拍父子释放，任意迭代等待，无关 redirect，以及另一 DIV 占用。

该模型也证明：**已经有效初始化后**，TE=0 的正常动态 reset 不会凭空制造 busy/ready 脱节。活动整数旧 hold=1 会把 reset 送入；闲置整数已经 idle。这个结论不等于上电 bootstrap 自动有效。

## 5. 故障注入与初始化边界

5 个故障模型均被检查器拒绝，原始反例保存在 proof.json：

| 人为破坏 | 最短失败步数 | 原因 |
| --- | ---: | --- |
| 子单元不处理 flush | 2 | 父取消清 B，但 top 留忙 |
| 取消当拍遮断时钟 | 2 | 子收不到必要清理边沿 |
| 全部子 finish 就过早清父 B | 6 | top 尚未完成外部输出 |
| 子不处理同步 reset | 2 | 活动 reset 清父 B，top 留忙 |
| top 不再等待代表子 outvalid | 2 | 破坏全部子 drain 关系 |

另明确保留无效 bootstrap 的示意反例：parent B=0、hold=0，而子 top=divide。若 reset=1 但 TE=0 且门关，parent reset 不会让同步复位的子获得边沿，撤销 reset 后 B=0 而 ready=0。它不是本模型有效初始化后的合法轨迹；它说明不能省略真实系统复位合同。报告未依据仿真器默认初值把该边界隐藏。

## 6. 结论范围

整数控制路径没有发现**有效初始化后的合法**无占用但未 ready 反例。其正常完成、反压、匹配取消及已初始化后的 TE=0 动态 reset 均有具体源码论证和机检支撑。

本报告仍不能单独批准 C2 RTL：真实启动复位是否到达，FP 双 lane／SQRT、所有父子身份以及候选改写的逐拍门控等价，必须由总 G0 审查闭合。源码哈希匹配只保证输入身份，不会把手工抽象变成工具自动证明的 RTL 等价关系。只证明安全性，不证明算术、除法终止、周期／面积／时序收益。
