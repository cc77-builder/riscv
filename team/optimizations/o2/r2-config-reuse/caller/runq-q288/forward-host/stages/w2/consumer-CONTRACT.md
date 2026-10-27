# 可选完整 forward / K768 W2 接入合同 v1

身份 `r2-s3-forward-consumer-w2-v1`。从已冻结纯 consumer 机械派生，全部改动可逆回父源码原文；旧 consumer、官方 runq/AM/NEMU 和所有冻结输入不改。独立 API `r2_w2_init/reset/forward` 复用原 state/method 类型，新增借用、不可变、16 字节对齐的 `6×221184B` W2 pack。只对 K768/M288 且 tensor 指针属于原六层 W2 的调用选择匹配 FR/TA；原 K288 路由、尾块、量化缓存及 scalar 回退保留。

四个实际核函数必须与父 consumer ELF 的 Q288 FR/TA 及本轮完整 W2 ELF 的 K768 FR/TA 各自逐字相等。独立 consumer-w2.o 中不得有 counter、oracle、snapshot、report 等观察依赖。完整 ELF/BIN、静态库/TLS/errno、工具和所有源码/模型均绑定哈希。

使用原正常 NEMU 与原独立 adapter。固定自然 token 1/7/19，p0..2，五个显式方法 scalar/FR/TA/FR-cache/TA-cache 各自实际执行；全部 3,691,424B 状态逐位置等于原 host gold，最终 live state 全量相等，flags 等于新同 ELF scalar 基线，RNE/TLS/errno 维持原判据。新增 W2 pack 作为第十个实际 dump，原模型/旧 pack/tail scale/新 W2 pack 均完整回读。

应用负控在 p0 后翻转实际最后 logit 的 bit0，必须由同一完整状态比较器在 byte152476 拒绝，精确 one-bit 差异与 BAD TRAP94 均成立。两个独立路由负控分别用 FR-cache/TA-cache：同 ELF 仅把实际 W2 pack 的所有数据字节置零，不改任何原权重、gold 或参考程序，必须正常执行完成但被原完整状态比较器拒绝；实际新 pack 的回读必须精确全零，其他输入仍不变，不能把故障结果授予正确性资格。此负控证明新 pack 的真实数据依赖，与应用负控分列。

负控后正常恢复和独立重放均采用 TA-cache，验证结果与首次 TA-cache 逐字一致；只使用 CPU3、独立输出/进程组、不与本轮目标运行争用 CPU0..2。每参考进程最多2G API调用、600秒，保留全部失败、原始和清理回执。该合同仅给新组合固定模型/三个位置的参考正确性资格；不授予完整香山 forward DiffTest、应用性能或 ASIC PPA。
