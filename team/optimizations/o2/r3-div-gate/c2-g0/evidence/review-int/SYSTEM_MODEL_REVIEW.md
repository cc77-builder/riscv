# 对主 C2-G0 系统模型的独立审查

审查对象：主模块 system_model.py 与本轮 system-proof-02.json（同时保留并检查首版 system-proof-01.json）；本次没有重跑主闭包，只读代码、结果及反例。输入 SHA256 见 system-review-audit.json。

## 审查结论

**未发现以待证明不变量筛选后继状态的循环假设。** 模型显式计算 parent busy、两份 hold 和各子状态，errors 只检查、不修复状态。接受条件使用原 RTL 的 occupied 与 ready，这是当前设计的真实协议约束，不是将目标 !B=>ready 当成前提。prelaunch 独立去掉 ready 项，再逐状态检查其是否等于实际 fire。

这属于手工绑定源码的控制抽象闭包，不是自动 RTL 形式等价。生产 async 与 fixture 同步 reset 的身份必须分别由真实生成 RTL／复位分发证据支撑。本整数审查看到的旧 parent-cost 输入是同步 reset，不能用它替代生产 async 证据。

## 逐项复核

1. **整数 I/R/O 映射。** 主 integer=IDLE/RUN/OUT 直接对应 VectorIdiv.scala:33 的 idle/divide/output，ready 与 outvalid 对应 :72–73。实际 divide→output 必须满足 :241 全 16 子的 AND；主 RUN 可任意自环或到 OUT，包含真实转移并允许更早完成。不存在用“将来一定完成”删状态的公平性假设。独立整数模型保留任意内部 I8/SRT 子的详细 FSM，证明真实 top.output 的内层清理成立；主模型不需要用完成期限替代它。
2. **父 busy 与 hold 独立。** next_busy 在 reset、parent kill、任一输出 fire 时清除；hi/hf 按各自接受／输出 fire／共享 parent kill 更新，未直接令 hold=busy。clock_i/f 使用旧 hold，正确包含清理边沿。busy/hold 对应是检查结果，不是状态初始化之后强行赋值的关系。
3. **两种 ROB 颜色。** 初始 8 组 parent/int/fp 历史颜色并不要求相等；活跃绑定来自接受时分别更新。每个周期任意 needFlush 真值表包含所有“同 ROB 得同结论”的情况，甚至允许真实环形顺序不可能的表，因此不会用固定顺序去排除取消反例。可达状态至多一个 DIV 事务活跃，忙 child 使用其已保存 ROB，闲 child 使用当前输入 ROB；对取消决策最多只有活跃事务和输入这两个相关身份，其他历史 ROB 在 idle 时不可见、下次接受会覆盖。两颜色因此足以表示这部分控制关系，而非声称把整个真实 ROB 队列缩小成两个槽位。
4. **FP 两 lane／两操作组合。** observation 使用每 lane 的 DIV OR SQRT output，再对两 lane AND；ready 要四个引擎均 IDLE。四个 unit_next 独立枚举 RUN 完成时刻，实际可见 RUN/OUT 与 OUT/RUN 偏斜均存在；两 lane 一起接受相同 DIV 或 SQRT，未通过初始之外的状态筛选假定“必定同时完成”。具体 FP 内部状态到 I/R/O 的包含关系由 FP 子审查负责。
5. **同步环境限制公开。** sync-qualified 仅排除 reset=1 且 TE=0，必须在结果标题明确它是 fixture 合同；不能据此声称证明任意同步无 TE bootstrap。reset_establishes 明确保留无 bootstrap 的同步 TE=0 反例。异步模型在无时钟边沿时也 reset 子，这是合理的异步复位语义，但使用资格依赖生产输入证据。
6. **reset 输入简化。** reset 时请求事件固定 none，没有漏掉接受，因为真实 allowInput 已含 !reset；这时 request 对状态无影响。reset 时 redirect、outputReady、VDot、TE 仍遍历，能够检查 reset/取消／完成重合。
7. **非确定 VDot 占用。** vdot_occupied 允许忙 DIV 时同时为 1，属于比合法生产状态更宽的抑制条件，不会额外制造 DIV 接受；最弱目标是无 DIV 占用时各 DIV ready，不依赖 VDot 是否实际空闲。

## 负控制是否击穿目标

直接复核 system-proof-01.json 和 system-proof-02.json：五种负控制最终 violation 都包含 idle_implies_all_ready，未借助 hold/ROB 辅助断言提前退出：

- cancel_edge_removed：整数接受后取消，没有子清理时钟，父 idle 而整数仍 RUN。
- fp_cancel_not_delivered：FP 接受后匹配取消，父清 B，两 lane 留 RUN。
- fp_rob_wrong：FP 接受时保存错误颜色，随后表只取消 parent；两 lane 留 RUN。
- fp_join_or：一 lane OUT、另一 RUN，被错误 OR 提前当作完成，父清 B，另一 lane 留 RUN。
- lane1_reset_missing：FP 两 lane 活跃时 reset，父与 lane0 清除，lane1 仍 RUN。

前四种和初始化以外的动态 reset 反例均从合法种子产生。它们证明检查器能观察目标受破坏；不代表对真实 RTL 已做故障注入。

## 合并意见

可将主模型计为“源码绑定的控制抽象闭包 PASS”，将整数代表子模型计为独立细化支撑；生产异步复位资格与 FP 细化需引用对应只读审查。最终用户结论应保留这些身份边界，不能提升为现成候选 RTL 已通过正式验证。

## 冻结第二版补充

已只读比较 system_model-v1.py 与最终主模型：变化限于增加 sync-valid-bootstrap 路径的实际调用／结果，以及删除从未使用的 witness 参数分支，状态转换函数未改。

- 生产异步：48 状态、33,600 转移。
- 有效初始化后的同步任意 TE 动态复位：48 状态、33,600 转移。
- 原同步夹具 TE=1 复位合同：48 状态、31,680 转移。

新增同步模式没有排除 TE=0 reset，成功闭合了“有效 bootstrap 后可在任意 TE 动态复位”的控制性质，和整数独立模型一致。无有效 bootstrap 反例仍保留，不能互相替代。

另阅读 review-reset/REPORT.md：其已按原冻结构建身份核验 11 个实际全核产物，表明真实 MinimalConfig 的 VFEX4 和所有 ready-producing FSM 使用 shared async reset；本整数审查所读 parent-cost 为 sync 夹具。因此最终主模型 production_async 命名已有另一份输入证据支撑，原提醒是身份边界而非未解决的冲突。此处复核的是审查文档与输入界限，没有重复执行该子审查的生成 RTL 核验。

已核对最终 system_model.py SHA256 为 8ae8349a08ff5e234215ebc68607f58784492d17b53dea9dfb01657db9968018。另只读复核 check_composition.py 和 composition-check.json：比较实际主 unit_next，而非另写一个同名抽象函数；FP 640 组输入／660 条边、整数 top 384 组输入均作具体后继集合包含于主抽象后继集合的检查，方向正确。源码级真实到手工细模型的对应仍依赖各子报告，该脚本不会自动完成 RTL 提取或等价证明。
