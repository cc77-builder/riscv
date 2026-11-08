# SP1-E B4：宿主接入完成，等待两例完整调用校准

**结论：o2-control与原C8普通C48的宿主准入均GO；timed DIV/SQRT仍HOLD。SP1-E正式验收仍为17/20。** 本轮没有运行EMU/NEMU，没有修改RTL、构建新核、运行EDA、切换默认或上传GitHub。

## 本轮完成内容

| 工作 | 当前结果 | 证据边界 |
| --- | --- | --- |
| o2-control | 原27项覆盖通过；新增精确前缀15项通过 | 完整16组、256trial、1208custom、131072寄存器检查字节；不新增FULL_STALL或双方向partial要求 |
| 原C8普通C48 | 原27项覆盖通过；新增精确PC6项通过 | 保留48调用、1008custom、384完整128位结果、CSR/ABI及尾部/哨兵；普通CSR/内存依冻结目标判据和未来实际DiffTest |
| 共享运行器 | 10项联合检查通过 | 两种adapter访问顺序、normal/bit100、完整源码、无授权拒绝、失败即停；合成不算目标证据 |
| 最终JSON冻结 | 独立修订5项通过；两份各338项写读验证通过 | 最小三行修订，原10项仅按未变语义复用；旧首份冻结FAIL原位保留 |
| 宿主预算 | o2-control235.713秒；C48 213.416秒，均<900秒 | 当前CPU4完整解析/哈希/收据测量＋明确经验余量，不是目标完成保证 |
| timed DIV/SQRT | 原137份文件SHA一致，旧41项测试及已有GNU产物复用 | 尚缺共享执行接入、当前完整调用预算及54窗/432算术指令的实际目标验证 |

初始o2夹具标签误触旧观察器规则，C48夹具发生同名模块冲突，最后冻结检查出现tuple/list序列化误判。这些都是宿主代码问题，本轮分别修好并补受影响验证；原FAIL、旧锁和原PASS全部保留，不要求用户再开一轮来处理这些问题。

## 最终入口及版本

默认稳定组合仍是 **0f＋firstdot V2＋原C8**。本轮只增加宿主接入和记录，不改变候选硬件。完整HEAD为 `347b1ae7eafb0f30c3b2cc1f8da8d9c8cdd3f98e`，本地分支`local/zjhwork-integration-20261024`。核对445份生产源码与1599份历史证据不变。

- 最终执行入口：`runtime-r1/calibration_guard.py`；源码版本SHA `b8726ede70ef14e45071ecd5051041d25b800b3eab95bda011f8b349f83fc797`。
- 两例输入：`cases-r1/o2-control/EXECUTION_FREEZE.json`与`cases-r1/original-c8-c48/EXECUTION_FREEZE.json`，均未消费。
- o2当前adapter：`o2-control/host-r2/adapter.py`；C48当前adapter：`c48/adapter-r1/adapter.py`。
- `ADMISSION.json`只表示宿主GO；当前不存在真实`RUN_AUTHORIZATION.json`、batch.used或target输出。
- 旧`runtime`、旧`cases`、o2顶层初版RESULT和SHARED_API早期描述仅供历史追踪；当前以本文件、最终合同和R1交接为准。

## 下一批只做什么

按o2-control→original-c8-c48串行，每例bit100→候选完整→0f完整，最多6目标。每例300＋2400＋2400秒，目标累计5100秒、宿主900秒、外层6000秒；整批目标10200秒、外层12000秒（3小时20分停止上限）。负控10万guest、正常150万guest；CPU4、整组4线程、RSS12GiB、每例日志2GiB及原seed/RAM/reset保持。

这些新预算等待用户下一条明确执行指令。任何失败/超限停整批，不重试、不加时、不借预算、不跳过继续，不自动进入正式验收或timed DIV/SQRT。校准只用于取得当前完整调用数据，未含同核精确重放；不能据此把进度写成19/20。原5角色1500秒/正常角色和6300/7200秒合同未改。两项以后正式验收通过可19/20，timed保护再通过才20/20。

## 三项主要指标

| 指标 | 本轮新测 | 处理 |
| --- | --- | --- |
| 加速比 | NOT_TESTED | 保留既有同镜像、分工作负载成绩；宿主解析时间不算加速比 |
| 面积 | NOT_TESTED | 保留Nangate45 trace-off局部FU/真实父级历史面积 |
| 时序 | NOT_TESTED | 保留原五档STA、负slack及原严格G2 NO-GO，不冒充整核Fmax |

完整历史数值及来源见[METRICS.json](METRICS.json)，本轮没有新的性能或成本提升结论。

## 证据与接续

[校准合同](CALIBRATION_CONTRACT.md) · [宿主预算](BUDGET_REVIEW.md) · [下一轮完整指令](NEXT_STEP.md) · [o2最终结果](o2-control/host-r2/README.md) · [C48结果](c48/RESULT.md) · [最终运行器交接](runtime-tests/host-r1/HANDOFF.md) · [最终独立审查](independent-review/runtime-r1-RESULT.md) · [timed缺项](timed-div-sqrt/GAPS.md) · [结构化总结果](RESULT.json)。
