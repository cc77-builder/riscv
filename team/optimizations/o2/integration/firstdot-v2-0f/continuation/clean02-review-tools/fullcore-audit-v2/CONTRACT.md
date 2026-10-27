# clean-02 全核资源审计 v2（源码冻结，等待 root 复核及实际 raw audit）

本合同仅适用于 clean-02/fullcore-run-01 的原 14 次完成运行。原冻结控制器、源码、结果、时间戳以及 v1 失败回执保持不变。此工具不启动 EMU。

原 UTC 区间扫描的峰值为 4，超过 jobs=3，因此严格墙钟资源判据继续记为 **FAIL**。唯一异常是 o2-control-diagnostic 的 05:05:46.666837+00:00 开始，早于 functional-7 的 05:05:46.746956+00:00 结束 80,119 微秒。其原因未证实；没有单调时钟或线程身份实测记录。

新的通过范围是冻结控制器保证的最大 3 个阻塞 worker 执行槽：hello 同步结束后才启用 ThreadPoolExecutor(max_workers=3)；negative/recovery 在同一任务内顺序执行；每个 worker 唯一启动点在 proc.wait() 返回之后才继续检查、退出并释放槽。该结论有精确源 SHA、14 组 spawn/result、父命令、完成日志和身份绑定支持，**不是 OS 时间轴实测峰值**。

新合同为 zjh-current-clean-fullcore-archive-v2-wall-clock-limited。physical、pack、bytes 和 live audit 的状态均带 WALL_CLOCK_LIMITED。功能、全 128 位 DiffTest、异常、负例恢复、O2 行为和覆盖率仍由原 fc.audit 全量复算，未放宽任何目标语义。宿主时间不用于目标周期性能结论。

## 允许变化

- 从冻结 current_clean_archive.py 复制外部审计器，保留原实现路径不动。
- 在私有 receipt 模块中，仅替换该精确 campaign 的资源证明；其余 receipt/raw/exit/身份/归档判据不变。
- 新 capacity-evidence 角色封存精确 case 的全部小证据，包括原 v1 失败链。新审计源码和 case 进入 auditor-source。
- bytes 验证只证明归档字节闭包，不声称重新执行 raw 语义检查；live audit 仍要求全部物理原件并重跑原 raw 检查。
- 每次输出采用新目录，所有失败保留，不设通用时间容差，不更改原 UTC 值。

## 运行闭包

runtime-closure.json 在源码完成和测试后生成，列出外部运行所需的固定文件绝对路径与 SHA。测试报告、实际审计结果不会加入运行闭包。原 35 项工具测试用于未变化能力回归；新测试覆盖固定异常拒绝、误称测量/原因、身份与失败证据闭包。真实 raw 审计须经 root 复核后启动。
