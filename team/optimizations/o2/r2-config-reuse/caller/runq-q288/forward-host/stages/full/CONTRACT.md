# RISC-V 完整 forward 的纯内存参考入口 v1

身份 `r2-s3-forward-memory-v1`。本模块把固定、原样 `upstream/runq.c` 的完整 forward 和本轮通过恢复源码等式验证的 RoPE cache 候选编译为实际 RV64/lp64d ELF；在固定原样 NEMU 共享参考库上执行。它不是香山整核计时，也不证明原样 AM 可作为 standalone 参考入口。

## 边界与原样依赖

固定 NEMU 不含 UART。原样 AM startup 在进入 main 前访问 UARTLite；外部只读状态诊断已经记录第一次 store access fault。因此新程序采用团队自有的内存入口，保留固定官方链接脚本与 klib/libm 静态库；不修改或替换 AM、官方 runner、NEMU、验证器及其判定，不跳过指令，不伪造 MMIO，也不回写 NEMU CPU/CSR 状态。NEMU 自己的默认 flash 完成初始化，团队入口只初始化本程序的寄存器、FP 状态、栈和单 hart TLS。

该入口无文件、网络、UART、syscall、动态分配或动态链接依赖。正常及失败路径以原 NEMU trap 指令终止，通过 RAM 导出报告、状态和阶段事件。目标比较器、TLS/stack guard 和错误状态都是团队程序的一部分，不替代原 NEMU 指令语义。

## 固定工作

沿用确定性未训练模型 D288/H768/L6/heads6/kv6/GS32/V32000/S256、种子 `0x53485041` 和连续 tokens `[1,7,19]`。宿主 exporter 直接调用原样 fixture helper 和原 forward，导出原始权重、完整 FP32 embedding，以及每位置 16 个 RunState span 的完整字节。目标使用同一序列化布局，不截短词表、矩阵、上下文容量或 KV 状态，不把目标生成值喂回宿主参考。

两个目标 Transformer 共享只读模型，拥有独立的完整状态：原样 forward 与只增加阶段记录的 RoPE cache 候选。每位置真实执行二者，保存各 3,691,424 B 状态，并逐 span 比较；候选必须完整产生120个有序边界。192 B 角度表在每次 forward 内准备，全部矩阵、非线性、attention、classifier 均实际执行。此版仍用原 scalar matmul，不声称已接入TA/FR完整模型。

最终普通分配必须落在128MB RAM内，不重叠；TLS只有4B errno，固定ABI偏移须由最终ELF核验。每次调用清fcsr，保存完成后的原始fcsr，要求FRM=RNE、errno sentinel未改和TLS两侧guard完好。异常flag的具体值保存并在重放时比较，不把RISC-V与宿主的fenv编码直接等同。

## 验收

运行外部 adapter 必须使用实际原样 NEMU 头文件和配置计算ABI，和当前 `.so` 导出的大小一致；固定所有源码、工具、库、镜像、配置及dump plan。分别限制API调用、无退休进展、墙钟和宿主日志大小。失败、异常、限额或非零halt码均不能成为正常PASS。

正常运行必须GOOD trap、report magic/version/三位置完成标志正确；对六份完整状态，外部独立检查原样/候选逐位相等，再与对应宿主原始状态比较。跨平台差异应作为实际差异保留，不能修改golden来获得PASS。导出的权重和embedding必须和输入原样相等，阶段事件严格匹配生成器定义。错误数据控制仅将候选首位置第一个logit翻转一位，必须触发指定状态比较失败与非零trap；恢复、重放使用原正常镜像和新进程，原始状态、事件与fcsr逐项复现。

该参考执行不授予香山完整token周期、应用加速比、训练质量或ASIC资格。已有强FR及R5默认保持。以后接入矩阵内核、改变入口或扩大数值域，都需要新的身份和相应实际验证。
