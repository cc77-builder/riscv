# B3-R5 收口：HOLD

B3-R5完成两条CSR正则的同行空白修复，checker27/27一次PASS；新增进程外超时监督，runtime10/10及12次宿主进程夹具清理一次通过。独立审计错误地把历史出处符号链接也要求为直接canonical路径，在执行0/41项对抗控前FAIL；240项冻结内容及4份别名的字节/SHA均一致。这是本轮审计新增条件导致的假阻断。按失败即停，预算0次、EMU目标0，保留全部记录，整体HOLD、SP1-E仍15/20。

开始：2026-11-06T10:19:51.632869+08:00；结束：2026-11-06T10:46:56.938495+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R5-20261106-01。

宿主差异新测 10 项：PASS_RUNTIME_HOST_TESTS；checker本轮新测 27 项：PASS_STRICT_NEGATIVE_CHECKER_HOST；旧runtime 6＋4 项仅复用、未重跑；独立实际 0 / 计划41，历史 65 项仅复用出处、未重跑：HOLD_B3_R5_INDEPENDENT_HISTORICAL_ALIAS_CHECK；预算：HOLD_B3_HOST_BUDGET。

- legacy-control：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_HOST_PREREQUISITE_FAILED_BEFORE_BUDGET；error=AssertionError: frozen file drift /home/riscv/riscv-lab/speedup-first-20261103/sp1-ab/candidate/difftest/src/test/csrc/difftest/difftest.cpp
- o2-all-pairs：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_HOST_PREREQUISITE_FAILED_BEFORE_BUDGET；error=AssertionError: frozen file drift /home/riscv/riscv-lab/speedup-first-20261103/sp1-ab/candidate/difftest/src/test/csrc/difftest/difftest.cpp

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | NOT_RUN | 0 | 0 | False |
| o2-all-pairs | NOT_RUN | 0 | 0 | False |

本轮runtime新测 10 项，状态 PASS_RUNTIME_HOST_TESTS；原6＋4项仅复用未变语义，checker本轮新测 27 项。独立新控实际 0 / 计划41，历史65仅保留出处、未重跑。独立门 HOLD_B3_R5_INDEPENDENT_HISTORICAL_ALIAS_CHECK；预算 HOLD_B3_HOST_BUDGET。实际目标数来自已完成record.process_started，启动意向单列，不把意向当完成；外部强杀缺失的角色收据单列missing_role_receipts，不能把该计数下界伪称完整启动总数。

准备期BEFORE.boot只保存历史身份；实际批次boot/PID/start_ticks/单调时钟仍严格绑定。445项生产文件、492项旧证据和历史77记录保持，原失败不删除。

生产checker改动严格为第114/115两条CSR正则中的5处空白量词：\s*、\s+改为[ \t]*、[ \t]+。原23项加4项横向空白/跨行拒绝检查在GNU timeout外部60秒保护下27/27通过；原夹具与其余语义不变。大尺寸24,558,348字节成本样本本轮仍未执行，因此不能据小测试宣称大日志预算已经通过。

进程外watchdog通过10/10方法、12个宿主夹具调用，所有清理完成；覆盖忽略SIGALRM、长C正则、另setsid子进程、短宿主截止、禁止延长整体限额、错误身份和不误杀既有无关进程。实际批次保留原目标supervisor，增加进程外绝对截止与pidfd回收；详细合同见[外部监督](EXTERNAL_SUPERVISION.md)。这属于宿主机制证明，尚不是EMU执行资格。

独立正式门只执行一次，0/41对抗控制。新audit_host.py check_pin把p.resolve()==p套到了历史候选difftest源码出处；candidate/difftest本来就是指向repo/difftest的符号链接。difftest.cpp、difftest.h、refproxy.cpp、refproxy.h原路径和内容均未漂移。240项冻件、445项生产文件及492项旧证据全部匹配。这个前提不是原合同要求，是本轮审计实现错误，不能归咎于RTL、NEMU或CSR修复。详见[失败归因](independent-review/FAILURE_ATTRIBUTION.json)。

本轮不把上述假阻断悄悄改为PASS，也不修改冻结的独立脚本后重跑。预算INPUT_FREEZE、MEASUREMENT.used及external-01均未生成；实际ADMISSION、执行freeze、授权、batch锁和目标输出均不存在。两例当前预算为null/HOLD，旧R1成本仅为历史资料。独立新增41项未执行；历史65项只保留复用出处，不能写作本轮65项重新通过。

下一轮仅删除历史证据域不必要的canonical要求，保留实际执行域规则；已记录的4个解析目标用于解释来源，不再设新的链接白名单门。只读复核还发现未执行终态wrapper把GUARD_PASS用于所有审计，下一轮应仅把它用于授予功能PASS，让失败终态也能正常留档。详细边界见[新增前提复核](independent-review/PRECONDITION_REVIEW.json)。

稳定默认仍为0f＋firstdot V2＋原C8，SP1候选尚未新增功能资格。加速比、面积、时序没有本轮新实测，按原条件保留历史数据和负slack；未改生产RTL、未构建新核、未做EDA、未上传GitHub。

SP1-E合格进度 15/20；三个暂缓项继续HOLD，默认不切换。新加速比、面积、时序全部NOT_TESTED，[历史三项指标](METRICS.md)保持原证据条件。

[下一轮指令](NEXT_STEP.md)；详细身份和最终审计见RESULT.json。
