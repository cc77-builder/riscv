# B3-R4 收口：HOLD

B3-R4已修正准备期启动身份范围：旧boot只作历史，真实批次仍绑定boot/PID/start_ticks/单调时钟；4项新差异与65项独立检查一次通过，原6项运行器和23项checker按身份复用。唯一宿主预算进程超过900秒仍未返回，核实身份后在观测1012.62秒时发送SIGTERM，超限112.62秒已如实留档；两例预算均HOLD/null，EMU目标0，不重试，SP1-E仍15/20。

开始：2026-11-06T00:00:02.772841+08:00；结束：2026-11-06T00:46:59.722251+08:00（两者均显式包含 UTC offset）。操作人：@cc77-builder / Agent；operation id：SP1-E-B3-R4-20261105-01。

宿主差异新测 4 项：PASS_RUNTIME_HOST_TESTS；旧 runtime 6 项及 checker 23 项仅复用、未重跑；独立 65 项：PASS_B3_EXECUTION_HOST_REVIEW；预算：HOLD_B3_HOST_BUDGET。

- legacy-control：HOLD；host_budget_seconds=None；failure_stage=None；error=None
- o2-all-pairs：HOLD；host_budget_seconds=None；failure_stage=None；error=None

| 用例 | 目标结果 | 实际目标数 | 启动意向数 | 合格功能证据 |
|---|---|---:|---:|---|
| legacy-control | NOT_RUN | 0 | 0 | False |
| o2-all-pairs | NOT_RUN | 0 | 0 | False |

本轮runtime新测 4 项，状态 PASS_RUNTIME_HOST_TESTS；原6项仅复用未变语义，checker23项REUSED，未重新执行。独立门 PASS_B3_EXECUTION_HOST_REVIEW；预算 HOLD_B3_HOST_BUDGET。实际目标数来自record.process_started，启动意向单列，不把意向当完成。

准备期BEFORE.boot只保存历史身份；实际批次boot/PID/start_ticks/单调时钟仍严格绑定。445项生产文件、399项旧证据和历史76记录保持，原失败不删除。

本轮实际放宽的是准备期不变条件：BEFORE历史boot与独立门实际观察boot不同仍可通过。新批次执行时才绑定实时boot；已经通过且未变的验证没有重跑。源码差异仅新独立包内的Python运行器及宿主辅助材料，生产RTL与默认配置不变。

预算失败必须单独保留：原脚本用进程内SIGALRM设900秒，但未及时终止；1012.62秒是按/proc出生时刻与uptime观察的发SIGTERM时刻耗时，不是脚本报告的完成时间。原程序stdout/stderr均为空，没有生成原生RESULT或traceback。当前预算RESULT明确是外部监督收口回执，不能伪装成原测量输出或900秒内停止。两例当前H/I/N及合格预算均不可取得；旧R1的468.345/331.801秒仅作历史成本，不作本轮GO。

静态只读归因指向checker第114/115行CSR正则：re.M下的行首\s*能够跨换行，尾部连续空白会产生重复回溯；内部\s+也允许跨行拼接字段。legacy原解析文本53,864B、allpairs宿主合成文本8,926B，分别补空白到24,558,348B。实际旧日志中的CSR字段各自处于单行，因此限定横向空白是具体的最小修订方向。但本轮没有抓到运行栈，不能宣称已精确确认卡在某个case或某一行。详见[复杂度只读复核](independent-review/BUDGET_COMPLEXITY_REVIEW.json)。

900秒门未可靠生效暴露了我们宿主工具的监督缺口。下一轮外部监督属于落实原预算，不能通过缩小24MB夹具、提高900秒或删除实际身份/完整结果检查来放行；同样需要核查实际批次宿主解析使用进程内信号的路径。无必要扩大到RTL或新全核构建。

[独立终态复核](independent-review/FINAL_READONLY_RESULT.json)确认预算PID已不存在、231项预算冻件/184项独立冻件/445项生产文件/399项旧证据无漂移；无ADMISSION、最终执行freeze、实际授权、batch消费锁或目标输出。legacy-control和o2-all-pairs均未执行，不能从宿主PASS新增功能资格。

本轮没有加速比、面积或时序新实测。历史同镜像性能和Nangate45局部成本在METRICS.md/json中按原口径保留，包括负slack与旧严格G2未通过结论。稳定默认继续0f＋firstdot V2＋原C8；未上传GitHub。

SP1-E合格进度 15/20；三个暂缓项继续HOLD，默认不切换。新加速比、面积、时序全部NOT_TESTED，[历史三项指标](METRICS.md)保持原证据条件。

[下一轮指令](NEXT_STEP.md)；详细身份和最终审计见RESULT.json。
