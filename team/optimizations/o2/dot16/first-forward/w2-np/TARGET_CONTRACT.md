# W2 N/P 完整 forward 目标入口合同 v1

本入口复用已运行的 dot16 四臂 TRACE0 准备器与原进程 owner，只把 workload、resource profile 和阶段状态身份更新为新的 W2NP 实验。当前阶段仅准备目标控制器；不构建或启动 EMU，不替换原四路在途实验。

## 身份与来源

工作合同为 `r3-dot16-first-forward-w2np-v1`，profile 合同为 `r3-dot16-first-forward-w2np-resources-v1`。两份入口源码仅对原源码做 `source-derivation.json` 中列出的三类字面替换；逆向替换须逐字节恢复原文件。原 `prepare_target.py` SHA256 为 `20c97884a44209f416a10e02b6085203f5b6070da3cc5ea9245cd164277b164c`，原 `launch_target.py` 为 `ceef0e0107196b052b63c6f24190c2dfa96f0c44341b6f0de4f82bed0a49fdc6`。原参考检查、目标检查、93项支持源码、TERM/KILL/reap控制流与原owner保持既有约束；这里不修改官方程序。

新实验使用已经实际通过GNU与五例参考验证的同一完整镜像：ELF SHA256 `62a73b9d16cea43ad03eec3ec09b27edfab7da90ce895d33baa72bf9d84723c4`，BIN `fcc05cf2d1ccd2cc80c74e259d007da86b7758a626f58b7cb63dc6793c698365`、77125408字节。参考控制器 binding 为 `e4ccd6e74c31a8b30e9b89088067a5e7364a67f0a2d3e2530ab2eed9bbc687a9`。`dot16`／`dot16_quantize` 标签在本合同中表示 N／NQ：K288和K768都使用whole8 narrow。paired16两臂的K288和K768均使用合格的paired16 RVV；P/N使用原量化，PQ/NQ使用同一Q helper。

## 四臂与资源

候选集合仍为 P、PQ、N、NQ，保持原方法字和负例方法字。主要比较本次合格 `min(P,PQ)/min(N,NQ)`，不把原W实验或旧LaTeX周期作为本实验分母。可分别报告相同量化的P/N、PQ/NQ和各自量化增量，不能叠加百分比。原W/P实验继续有独立价值，其输入和输出不得覆盖或改写。

目标准备复用原有限上限：每臂40,000,000 guest cycles、43,200秒、16MiB原始日志文件；4 slots时为1 wave。这些是保留的资源上限，不是预计耗时或成绩。真实CPU slots、operation ID、完整输入、原五例重新审计和四份method-only镜像仍须由原profile阶段实际冻结；不能仅因本准备器成功就认为有可执行profile或新运行授权。不得扩大用户四核总预算，不自动重试、扩预算或重复启动。

## 验证与启动边界

准备器继续验证原固定P/PQ target源、参考controller全部输入与生成物、7/3/40支持源码适配、原源码逆向证明和Python语法。它不执行真实target检查、不生成目标性能结论。后续launch须核对实际源SHA、profile SHA、全部输入与CPU占用；同一原owner保留work/grace/hard/external的层级关系和实际清理审计。

只有真实目标终态、完整DiffTest/UART/GOOD TRAP、原完整应用状态尾检、输入不变与资源回收均成立，才授予该新镜像的目标正确性。四CSR来自UART与静态位置，不声称TRACE0未采集的退休关联或custom动态计数。面积、时序与目标应用周期分别报告。
