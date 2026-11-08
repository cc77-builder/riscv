# B3-R6 收口：HOLD

B3-R6已修正历史出处检查：准备与正式验证使用同一原路径/字节数/SHA逻辑，304项冻结内容及4份历史别名通过；运行器和checker保持R5原字节，27＋10项证据明确复用、未重跑。独立审查唯一正式尝试在首个CSR正控API调用时报explicit scope/run id：审查脚本误传HOST_FIXTURE_NOT_TARGET，生产既有合法值为HOST_FIXTURE。首个正控调用1次、完成0/41；这是Agent编写的审查脚本参数错误，不是RTL、CSR结果或预算超限。按失败即停，预算0次、EMU目标0，保留原FAIL，整体HOLD，SP1-E仍15/20。

开始：2026-11-06T11:14:20.923904+08:00；结束：2026-11-06T11:33:14.118243+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R6-20261106-01。

本轮checker新测0 / REUSED 27项：PASS_STRICT_NEGATIVE_CHECKER_HOST；runtime新测0 / REUSED 10项：PASS_RUNTIME_HOST_TESTS；原R3 6项及R4 4项仅保留更早历史出处。独立实际 0 / 计划41，历史 65项仅复用出处、未重跑：HOLD_B3_R6_INDEPENDENT_CONTROL_SCOPE_ERROR；预算：HOLD_B3_HOST_BUDGET。

- legacy-control：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_CSR_CONTROL_CALLER_SCOPE_BEFORE_BUDGET；error=ValueError: explicit scope/run id
- o2-all-pairs：HOLD；host_budget_seconds=None；failure_stage=INDEPENDENT_CSR_CONTROL_CALLER_SCOPE_BEFORE_BUDGET；error=ValueError: explicit scope/run id

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | NOT_RUN | 0 | 0 | False |
| o2-all-pairs | NOT_RUN | 0 | 0 | False |

本轮runtime新测0项、REUSED R5的10项；checker新测0项、REUSED R5的27项。更早R3六项/R4四项仅保留原未变语义出处。独立新控实际 0 / 计划41，历史65仅保留出处、未重跑。独立门 HOLD_B3_R6_INDEPENDENT_CONTROL_SCOPE_ERROR；预算 HOLD_B3_HOST_BUDGET。实际目标数来自已完成record.process_started，启动意向单列，不把意向当完成；外部强杀缺失的角色收据单列missing_role_receipts，不能把该计数下界伪称完整启动总数。

准备期BEFORE.boot只保存历史身份；实际批次boot/PID/start_ticks/单调时钟仍严格绑定。445项生产文件、642项旧证据和历史78记录保持，原失败不删除。

本轮只删除历史出处必须为直接canonical路径这一无关条件；实际执行路径、boot/PID/start_ticks、完整128位、CSR和重放合同保持。没有新增别名白名单或准备期boot不变要求。

失败后的两份交叉只读复核确认：确定的接口错误只有CSR共享调用处的scope字面量；旧R5_INDEPENDENT_CSR作为非空run_id仍合法，不另设轮次名称门。其他41项的参数、夹具接口和返回字段静态相符，但未运行的动态结果仍不能写PASS。见[失败归因](independent-review/FAILURE_ATTRIBUTION.json)和[接口复核](READ_ONLY_INTERFACE_REVIEW.md)。

VT/FF/NEL负例会由既有console入口拒绝，不能全部称为CSR正则层独立证据；原27项中已有LF/CRLF的CSR行特定拒绝覆盖。该说明只修正证据适用范围，不增测试条件。

预算脚本接口只读复核使用合法HOST_FIXTURE，没有同类确定误参；成本测量未运行，两个host_budget_seconds均null，新N等代价NOT_MEASURED。原R1预算值只作历史，不能冒充本轮GO。见[预算终态](budget-review/RESULT.md)。

本轮新加速比、面积、时序全部NOT_TESTED；历史数值按原负载/trace-off局部成本合同复用。默认0f＋firstdot V2＋原C8保持，候选未采用。

SP1-E合格进度 15/20；三个暂缓项继续HOLD，默认不切换。新加速比、面积、时序全部NOT_TESTED，[历史三项指标](METRICS.md)保持原证据条件。

[下一轮指令](NEXT_STEP.md)；详细身份和最终审计见RESULT.json。
