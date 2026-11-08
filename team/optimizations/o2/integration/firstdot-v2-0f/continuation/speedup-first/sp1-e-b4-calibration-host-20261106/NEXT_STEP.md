# 下一轮：两例完整调用有界校准

开始 SP1-E B4 两例完整调用有界校准：按 NEXT_STEP 使用最终 runtime-r1/calibration_guard.py，先核查已有进程、宿主准入、两份 cases-r1 冻结输入及未消费锁。接受本轮新校准预算后，仅按 o2-control→original-c8-c48 串行，每例 bit100 拒错300秒/10万guest→候选完整2400秒/150万guest→0f完整2400秒/150万guest；每例最多3目标、目标累计5100秒、宿主900秒、外层6000秒，整批最多6目标、目标10200秒、外层12000秒，不借时。保持CPU4、整组4线程、RSS12GiB、每例日志2GiB和原seed/RAM/reset，保留o2-control的16组/256trial/1208custom及C48全部48调用/1008custom/384完整128位输出、CSR/ABI、当前提交组bit100与物理运行身份。失败或超限立即停止整批，不重试、不加时、不跳过继续。只收集完整调用正确性、周期、吞吐、进度和资源，重新判断原五角色6300/7200秒预算，不自动进入正式验收或timed DIV/SQRT。校准不增加17/20资格。不改RTL、不构建新核、不做EDA、不切默认、不上传GitHub；完成后更新计分板及三项指标状态，给出结论和下一轮指令。

## 当前已完成与执行边界

B4宿主GO；o2-control/C48差异接入、真实输入写读、共享运行器及经验900秒宿主预算均已闭合。最终运行器是`runtime-r1`，用例冻结在`cases-r1`；旧`runtime`与`cases`留作首次JSON写读FAIL证据，不用于下一批。`watchdog.py`的旧CLI不是本轮入口。

本轮尚无RUN_AUTHORIZATION、BATCH.used或真实target输出。下一条明确执行指令接受新预算后，才创建绑定当前ADMISSION、CALIBRATION_CONTRACT、runtime-r1/SOURCE_VERSION及两份cases-r1/EXECUTION_FREEZE的授权，并使用最终guard运行。不得直接调用内层runner绕过进程外监督。授权结构见[runtime交接](runtime-tests/host-r1/HANDOFF.md)。

本轮及完整调用校准均不冒充五角色验收；17/20需两例正式验收后才能19/20，timed DIV/SQRT再通过才20/20。目标时间尚未实测，12000秒是整批停止上限而非预期耗时。若正常完整调用超过旧1500秒门槛，应如实HOLD旧正式合同，不能静默加时。

[本轮结论](RESULT.md) · [完整校准合同](CALIBRATION_CONTRACT.md) · [宿主预算](BUDGET_REVIEW.md) · [timed DIV/SQRT缺项](timed-div-sqrt/GAPS.md)
