# O2 G3 控制覆盖源码可达性复核

记录时间：2026-10-19T06:33:00+00:00

范围：**仅源码推断，不是本轮补充程序的实际覆盖结果。** 本复核没有启动补充 EMU、没有读取补充 EMU 运行结果作为证据、没有修改冻结源码、参考模型、黄金数据、驱动或原始日志，也没有生成新候选。本记录不能替代 G3 完整轨迹验收或 G4 公平性能测试。

仓库：/home/riscv/riscv-lab/zjhwork2-review-20261018/repo

当前分支：local/o2-fullcore-20261019

保存时 Git HEAD：e2d9c063ac716665f4596bc95a806bd62a56d3a7

下面的 SHA256 是保存记录时实际读取的源码字节身份；“等于 HEAD”逐文件通过 git show 与工作树字节比较获得。该 HEAD 表示本次源码复核快照，不独立证明某个正在运行的 EMU 使用此提交；实际硬件身份应查其 hardware-pins/build receipt。

| 所读文件（仓库相对路径） | SHA256 | 等于 HEAD |
| --- | --- | --- |
| team/optimizations/o2/fullcore/workloads/generate_control.py | 209fb1f5a9231f047ae72004039c09e0a6e08026f1e55bc2bad47d6b5c14909a | 是 |
| team/optimizations/o2/fullcore/workloads/control.c | 6b0f5ce7524f2a8e31d499f06aa12f66bfccafb9f0029060866500e715c5c8e8 | 是 |
| team/optimizations/o2/fullcore/analyze.py | 27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496 | 是 |
| team/optimizations/o2/fullcore/SCHEMA.md | 3f71ff3c4e4b83fc6744547a22b0f0eb450e3fbc2b8b2c12de8d493f7c3fe356 | 是 |
| src/main/scala/xiangshan/backend/exu/ExeUnit.scala | 166f70c704cc2ec477d316bc5d3ffb40498118e6f8c1c498209fc4b706070f1e | 是 |
| src/main/scala/xiangshan/backend/rob/Rob.scala | 06674f4d8ae95e0517e5bbcfef834f987b1600c528989e5bebca55e8d894d9a2 | 是 |
| src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala | 20981203b19e57658c35ee76d134a1aaee918ce4c317d0f139df97c75460491a | 是 |

## 事件安排与真实依赖

generate_control.py:20–61 生成 16 组，每组重复 16 次，共 256 个 trial。广播 burst 为 1～16，分支后的 decode_gap 为 0～3。每个 trial 的主要顺序如下：

1. 载入完整 32 个向量寄存器。
2. 标量 fdiv.s 产生 ft1，随后若干 vfmv.v.f v28,ft1。这里存在真实的浮点结果依赖；安排意图是使广播与点积争用向量写回资源。
3. 载入标量分子、除数和比较值；执行 vdivu.vv v19,v8,v9。
4. 执行分支之前的 vdot v16,v8,v9，作为始终架构执行的老请求。
5. 标量 divu 产生 t2，bne t2,t3 决定是否跳过后面八条 vdot v20…v27,v8,v9。
6. 保存完整寄存器，进入下一 trial。

真实依赖是“fdiv.s → ft1 → 广播”和“标量 load → divu → bne”（比较值 load 也影响 bne）。v19 结果不被老 vdot 或分支消费；v16 结果不被分支消费。向量 DIV 与点积之间主要是 VFEX4 资源排斥。addi t5,t5,1 结果不被点积或分支消费，因此 decode_gap 只改变前端/发射时序，不能视为延迟年轻点积的真实数据依赖。

分支结果来自确定性哈希，刻意形成不规则序列；不规则结果不等于实际误预测。源码没有保证分支预测器一定出错，也没有保证浮点广播与点积写回一定重叠。

## 四项覆盖的可达条件

| 覆盖项 | 源码安排 | 必须由实际轨迹确认 |
| --- | --- | --- |
| FULL_STALL | 浮点除法结果依赖后的广播 burst 尝试制造共享写回竞争；八条密集年轻点积尝试填满 P/R | 边沿前 occupancy=2，存在存活 R，outready=0 且存在 STALL。广播可能已结束，或 DIV 可能把点积推迟到竞争窗口之外 |
| KILL_P | 标量除法延迟分支决议，年轻点积在错误路径上被接受 | 实际父级 redirect 到达时，P 中仍有效的请求按 ROB 年龄应取消；killp=1 且身份一致的 KILL slot=P |
| KILL_R | 年轻点积已 ACCEPT、MOVE 到 R，尚未响应；写回阻塞可延长窗口 | 父级 redirect 时 killr=1 且 KILL slot=R；取消优先于响应，被取消 R 不能同时 RESPONSE |
| PARTIAL_KILL | 老 v16 与某条年轻 v20…v27 跨越分支年龄边界并存 | 边沿前 occupancy=2，并且 killp 与 killr 恰有一个为 1；单槽取消、双槽全取消均不能代替 |

analyze.py:326 的 FULL_STALL 定义为 occupancy==2 且确实有 STALL。其 occupancy 是边沿前状态；同周期若只取消 P、R 存活并受阻，仍可计入 FULL_STALL，不应额外加入“必须没有任何取消”的条件。

analyze.py:340–342 分别定义 PARTIAL_KILL、R_KILL_P_SURVIVES 与 P_KILL_R_SURVIVES。它们根据父级真实 flush 和逐槽完整 ROB 年龄重算，不凭源代码顺序或 ACCEPT 顺序判定年龄。

## 部分取消的结构性风险

源码确实有老请求 v16，因此不能说“程序完全没有老幸存者”。风险在于没有依赖强制 v16 留在 FU 中等待分支判定：它可能远早于标量除法完成，或在 redirect 到达前正常 RESPONSE。此后 P/R 若全是年轻请求，取消丰富也不能形成部分取消。

最自然的目标窗口为：

    R = 分支之前的 vdot v16，ROB 年龄应幸存
    P = 分支之后的一条 vdot v20…v27，ROB 年龄应取消
    父级 redirect → P_KILL_R_SURVIVES

若 R 的老 v16 已响应，即便后续两槽满，也可能只得到 BOTH_KILL。若仅剩一个年轻请求，只能得到单槽 KILL；这两种情况均不满足 PARTIAL_KILL。

反方向 R_KILL_P_SURVIVES 需要更年轻请求先进入 R、较老请求随后进入 P 等接受次序。当前源程序未刻意构造能保证这种次序的数据依赖，不能承诺覆盖。共享写回反压可能扩大老请求的存活窗口，但必须由实际轨迹验证，不能从 burst 长度推定。

## 覆盖缺失时先检查的轨迹字段

1. 先确认实际误预测/redirect：结合静态分支位置、vdot 的 ENQUEUE.pc/word、REDIRECT 与 VFEX4_REDIRECT。ROB redirect 与 VFEX4 实际 flush 相隔一个全局周期，需查看两个边界，不能提前一拍判 FU 取消。O2 ENQUEUE 仅记录 vdot，不直接给出所有分支 PC；需要完整程序反汇编/现有 ROB 信息辅助定位，不能虚构分支 ENQUEUE。
2. 用 seq、完整 rob 和 ENQUEUE.pc/word 关联老 v16 的 ACCEPT → MOVE → RESPONSE/KILL，检查它在父级 redirect 前是否已正常结束。pdest 是物理目的寄存器，不能直接把它当 v16/v20 的架构编号；架构目的寄存器应由 word/反汇编识别。
3. 查看 STATE.pvalid/rvalid/occupancy，确定是否曾同时两槽有效。若没有，先结合 VFEX4_WAIT、divoccupied、divactive、busy 和接受间隔分析派发/资源时序，不能先归因于取消逻辑。
4. 查看 rseq/rrob/outvalid/outready、STALL 与两槽有效窗口是否重合。仅 occupancy=1 时受阻无法补足 FULL_STALL。
5. 依据包含环回 flag 的 ROB 顺序及 redirect.self 重算每槽取消。不能只比较 ROB value，下标绕回也不能解释为年龄反转。
6. 对部分取消同时检查幸存者最终归宿。幸存 R 在 redirect 同周期即可正常 RESPONSE；幸存 P 在 R 被杀的同周期即可 MOVE，再正常响应。必须维护每个 seq 的单次终结与请求守恒。
7. 区分“FU 内取消”与“响应之后 ROB 撤销”：ACCEPTED_YOUNGER_SQUASHED 可能包含已 RESPONSE、随后被 ROB 清除的请求，不能用它替代 KILL_P/KILL_R。

O2 轨迹中的 outready=0 和 STALL 可以直接证明反压；当前这些事件不直接给出写回仲裁赢家。因此，没有额外已有写回信号时，把每次反压归因于 F2v 广播仍只是推断。

## 架构正确性与覆盖的边界

control.c:14–22 对每组 16×32×16=8192 字节进行完整寄存器比对；16 组共 131072 字节。其后检查 vl=8、vtype=0、vstart=0、vcsr=7、fflags=0。generate_control.py:69–74 的 manifest 预期 vdot 提交总数为 1208，覆盖声明明确为 pending actual O2 full-core observations。

这些检查能约束错误路径操作不得改变最终架构结果，但不能单独证明部分取消、双槽反压或逐槽取消覆盖。具体覆盖结论应以本轮真实日志、严格 analyze 重算及硬件/输入身份绑定为准。本文没有报告任何补充 EMU 的 PASS、覆盖计数、周期值或加速比。
