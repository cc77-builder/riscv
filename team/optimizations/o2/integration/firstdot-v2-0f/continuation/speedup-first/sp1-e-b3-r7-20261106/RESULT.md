# B3-R7 收口：PASS_FUNCTIONAL

B3-R7仅把独立CSR审查共享调用的scope修正为生产API已有HOST_FIXTURE，生产runtime/checker原字节保持，27＋10项通过证据明确复用、未重跑。剩余41项独立控一次PASS；唯一外部900秒预算测量18.948秒通过，两例宿主预算664.466/527.922秒均GO。随后按原合同串行完成legacy-control→o2-all-pairs两例各五角色，共10个真实目标全部通过；完整128位、退休/CSR、身份、资源及精确重放均通过独立终态复核，新增两项功能资格，SP1-E由15/20推进到17/20。整批目标累计4708.455秒、原生外层4783.570秒、外部监督4783.682秒，未重试、未加时、未扩围；原R1至R6失败完整保留。默认0f＋firstdot V2＋原C8保持，未修改RTL、未构建新核、未做EDA、未上传GitHub。

开始：2026-11-06T11:38:31.560496+08:00；结束：2026-11-06T13:17:09.632907+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R7-20261106-01。

本轮checker新测0 / REUSED 27项：PASS_STRICT_NEGATIVE_CHECKER_HOST；runtime新测0 / REUSED 10项：PASS_RUNTIME_HOST_TESTS；原R3 6项及R4 4项仅保留更早历史出处。独立实际 41 / 计划41，历史 65项仅复用出处、未重跑：PASS_B3_EXECUTION_HOST_REVIEW；预算：GO_B3_HOST_BUDGET。

- legacy-control：GO；host_budget_seconds=664.4656078536575；预算通过，无失败
- o2-all-pairs：GO；host_budget_seconds=527.9218119536602；预算通过，无失败

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | FUNCTIONAL_PASS | 5 | 5 | True |
| o2-all-pairs | FUNCTIONAL_PASS | 5 | 5 | True |

本轮runtime新测0项、REUSED R5的10项；checker新测0项、REUSED R5的27项。更早R3六项/R4四项仅保留原未变语义出处。独立新控实际 41 / 计划41，历史65仅保留出处、未重跑。独立门 PASS_B3_EXECUTION_HOST_REVIEW；预算 GO_B3_HOST_BUDGET。实际目标数来自已完成record.process_started，启动意向单列，不把意向当完成；外部强杀缺失的角色收据单列missing_role_receipts，不能把该计数下界伪称完整启动总数。

准备期BEFORE.boot只保存历史身份；实际批次boot/PID/start_ticks/单调时钟仍严格绑定。445项生产文件、743项旧证据和历史79记录保持，原失败不删除。

独立终态审计为PASS_OFFLINE_AUDIT：8个正常角色独立核对13614次完整128位响应和13260次custom提交，两例各五角色及全部重放维度通过。详见[终态审计](independent-review/POSTRUN_RESULT.md)和[根端终态事实](ROOT_TERMINAL_FACTS.json)。

legacy-control：候选正常/重放均375701 guest cycles，0f正常/重放均376582；实际目标3538.846秒、宿主50.779秒。o2-all-pairs：候选两次均126637 cycles，0f两次均126918；实际目标1169.609秒、宿主22.801秒。这些是完整功能程序总周期，程序没有公平RVV计时窗口，不能据此新增加速比。10个角色的墙钟、退出码、线程、RSS及完整身份均保存在原始record与独立审计。

两个实际bit100拒错均通过：legacy在PC0x80000298/v0注入，诊断为同组首0x80000294；allpairs在PC0x80000364/v16注入，实际组首0x80000354，组内4个同vd写者，最终为0x80000370。按严格提交组、最终写入者及完整128位口径核对，未强制诊断PC等于注入PC，也未放宽数值覆盖。

执行时guard、batch claim、case claim及10个role绑定同一真实boot；执行结束后WSL重启，审计boot不同。既有审计正确区分两个代际，不做跨boot的PID或单调时间比较；实际运行期间的完整回执和外部清理证据通过。此为原R4/R6已明确规则的实际应用，没有新增放宽条件。

剩余o2-control、原C8普通C48、timed DIV/SQRT仍HOLD。前两项需要负载差异接入及当前两核的完整调用预算依据；timed DIV/SQRT还需闭合计时窗口与运行预算。下一步交付具体接入和有限完整校准合同，不再反复做同样的泛化只读评审；不自动启动或借用本轮预算。

本轮三项新性能/成本测量均NOT_TESTED。METRICS保留原工作负载的同镜像历史加速比及Nangate45 trace-off局部面积/五档STA；负slack与原G2 NO-GO不改写。本轮功能通过不授予新应用性能、全芯片面积/Fmax或默认采用资格。

SP1-E合格进度 17/20；三个暂缓项继续HOLD，默认不切换。新加速比、面积、时序全部NOT_TESTED，[历史三项指标](METRICS.md)保持原证据条件。

[下一轮指令](NEXT_STEP.md)；详细身份和最终审计见RESULT.json。
