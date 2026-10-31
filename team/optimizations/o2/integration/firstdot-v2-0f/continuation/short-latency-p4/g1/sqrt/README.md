# P4-G1 真实父级 SQRT／双 lane 补充验证

本目录只迁入C2已存在的测试内容，使用本轮独立P4父级scoreboard；不导入C2生产RTL，不转授历史PASS。当前候选RTL执行状态由根Agent的新运行报告决定。

## 文件与接口

- sqrt_parent_test.cpp：定义P4_SQRT_AUX_ENABLED后包含 ../parent/parent_test.cpp（main重命名），复用新P4 directR/P状态机；新main只运行本补充。
- sqrt_vectors.hpp：由verify_sqrt_oracle.py从sqrt-oracle.json生成并逐字检查，C++实际expected数据与独立数值常量绑定。
- instrument_parent.py：对新生成测试top加只读laneReady/laneFinish/divBusy端口；仅VDotElasticParentTestTop.sv可变化，其余生产生成物前后SHA一致。
- check_sqrt_parent.py：过滤独立aux流后使用指定路径P4 schema2 replay，require_campaign=False仅关闭原完整campaign覆盖要求；状态/身份/守恒/ready/时钟检查保留，再检查SQRT补充覆盖。
- negative_sqrt_parent.py：真实正日志上执行7项离线观察变异并要求全拒绝。
- test_sqrt_oracle.py：7项主机oracle检查；不是RTL测试。

宏观察钩子在P4父级C++中，关闭宏时不引用补充端口。每拍都打印P4_SQRT_AUX schema1，包括bootstrap/reset；P4_PARENT schema2逐拍与其严格一一对应。

## 固定覆盖

| 场景 | 数量 |
| --- | ---: |
| 5种SQRT向量×0/1/7拍反压 | 15 |
| 两方向真实lane偏斜×计算/单lane完成/全输出/反压×ready×三后继FU的取消 | 48 |
| SQRT ROB同龄/年龄/flag及完整环绕×计算/反压 | 14 |
| intDIV/FPDIV/SQRT三阶段×取消重叠，以及空闲TE0动态reset | 20 |
| SQRT与VDot/intDIV/FPDIV双向切换×0/1/7反压 | 18 |

合计115个场景标签，另有有效TE1 bootstrap；不是115条总事务。取消后3个真空闲边沿必须立即全关钟，共54个取消窗口、162样本，无grace。

两物理lane偏斜采用FP64的最小正subnormal 2^-1074与9，两方向交换；精确结果2^-537和3。必须观察laneFinish=1和2，偏斜取消必须实际落在该阶段。FP32普通/非规格化向量另测，不当作真实偏斜证据。有限结果用Fraction验证12个精确平方关系，4个特殊值检查canonical NaN、负零、正零、正无穷及聚合NV。常量不使用host sqrt或DUT自证。

## 根Agent执行顺序

先对新生成真实父级进行instrument_parent.py；保存instrument receipt、原top和全部生成SHA。用sqrt_parent_test.cpp及该生成物构建独立Verilator二进制，再执行：

    <new-sqrt-binary> <vectors.tsv> --sqrt
    python3 -B <this-dir>/check_sqrt_parent.py --log <new-log> --parent-dir <g1/parent> --output <new-replay.json>
    python3 -B <this-dir>/negative_sqrt_parent.py --log <new-log> --parent-dir <g1/parent> --output <new-negative.json>
    python3 -B <this-dir>/verify_sqrt_oracle.py --output <new-oracle-result.json>

程序最终输出P4_PARENT_PASS schema2，aux须经本补充checker剥离后才送普通P4 replay。不能直接用旧O2/C2 checker。本目录没有另起重型runner；根Agent统一串行运行并锁定实际源码/配置/生成物/命令。

## 本子任务已做与未做

已做：Python AST检查、精确oracle检查、7项主机单测；对旧0f生成物的3文件独立副本做只读观测插入smoke，原文件SHA不变。没有编译C++、运行RTL或构建任何硬件；所有新硬件资格仍NOT_TESTED，根Agent后续实际运行才能更新。

主机证据位于本地 p4-g1-short-latency-20261029-01/sqrt-agent。旧C2材料源SHA保留在source-pins-before.json；本目录源码摘要见DELIVERY.json。
