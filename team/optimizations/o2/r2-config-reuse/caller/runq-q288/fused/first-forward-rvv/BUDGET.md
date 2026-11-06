# 首次完整 forward 三臂资源边界

资源身份：`r2-s3-first-forward-rvv-resources-v1`，工作负载合同 `r2-s3-first-forward-rvv-v1`。全部CPU任务遵守团队总共四核预算。

## 短资格

主端协调CPU0单核GNU和五个参考进程，最多一个参考进程并发。沿用原first-token参考上限100,000,000 API步、内部600秒/外部630秒及128MiB单文件上限；外层短阶段另记录实际预算和清理回执。复用已有AM/libm与reference adapter，不重建官方程序。新失败使用独立输出并保留；不静默延长或重放。

## 三正常目标

新目标队列仅 `fr/gs32/paired16`，每个独立fresh进程一次p0/token1调用。计划CPU0/2/3三槽并行，每槽一个EMU；只有主端审查冻结输入并核实资源后启动。不能因为参考资格有五例而启动五个EMU。

每臂沿用原成熟边界：40,000,000 guest cycles，28,800秒EMU外部超时，stdout/stderr每个原始流4GiB文件上限；seed1、128MB RAM，OMP/EMU threads均1，原DiffTest/UART及 `--log-end=0`。冻结profile记录精确命令、环境、输入SHA、三份仅方法word不同的目标镜像身份、分配CPU和操作ID。保留原进程组owner/清理逻辑；未知清理不得PASS，不自动追加运行或扩预算。

## 规划依据与口径

旧 `norm/evidence/first-token` 的原三正常案例，EMU自报host time为6.078–6.176小时，UTC起止跨度6.181–6.584小时，wrapper monotonic为5.844–6.247小时。这三种时钟不相减作审计成本；现有回执没有实际进程树user+sys CPU秒。旧FR原回执SHA `159571b8b1e90423e0009086f0569a1652790b32828ae51676fe8e80e63eb4d7`，stdout SHA `473ca12fab2c7fa42934a6000d5e432dff13a933ff4b536db368ed3842666754`，两者已与原发布manifest相符。FR仅约2.32MB stderr仍需约6.18小时，不能因三臂纯RVV而承诺一两小时。

每臂按6–8小时单核槽位占用规划；三臂共18–24槽位小时，三个可用槽位并行运行窗口6–8小时，两个槽位两批12–16小时，单槽18–24小时。此为排期锚点，不是新候选性能预测或保证完成时间；构建、短参考、冻结、审计和最终汇总另计。8小时EMU超时不是整个工程闭环的8小时承诺。

宿主并行的墙钟争用不作为软件性能指标；三臂仅比较相同模拟配置下的guest窗口CSR差分。资源争用造成超时或输入状态不明确时按真实失败/未完成报告，不转成周期结论。
