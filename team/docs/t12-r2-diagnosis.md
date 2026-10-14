# T12 第二轮定位与可复现实现

原 b827 的 initial、compact-1、stress-slices-1 是真实构建/运行；后两类均有 timeout 124 和不完整日志，initial 的 wrapper exit0 也不是通过。本轮不修改这些历史产物。

固定 EMU/ref/flash 与 T10/T11 验收值一致，当前生产 RTL/build.sc 与 EMU 来源一致，AM 086a238 离线 clone --no-hardlinks 到本工作区 deps。工具使用既有便携 GCC 11.4.0 / binutils 2.38，LD_LIBRARY_PATH 指向其 usr/lib/x86_64-linux-gnu；没有安装工具或写旧 AM/NEMU。

| 真实诊断/对照 | 结果 |
| --- | --- |
| 旧 000 原镜像，周期上限 50k | instrCnt=50348，PC=0x800034f0，仍在全向量观察；45.7 host 秒 |
| 旧 000 原镜像，周期上限 90k | instrCnt=101873，PC=0x80000140，位于 find 扫描；89.4 host 秒；无 GOOD TRAP |
| 原校验逻辑仅添加阶段记录，seq0/count1 | 进入/返回/校验/FNV 阶段均完成；72788 cycles、60219 instructions、GOOD TRAP、实际 exit0；77.8 host 秒 |
| 精确比较与计划扫描修复，seq0/count3 | 原80秒限制内完整通过，42482 cycles、41611 instructions、GOOD TRAP、实际 exit0；40.3 host 秒 |

这些进展显示该最小失败对照并非 CPU 停退或软件死循环。约 1k 模拟周期/host 秒的既有 EMU 下，逐字节校验/复制、FNV 字节乘法、重复 find 扫描及 UART 输出造成预算不足。不同工作负载、诊断日志会影响总周期；不拿 host 秒数声称 vdot 性能或 FU 时延改善。其余历史 timeout 仍按各自原结果保留。

另外确认 EMU 达到 `-C` 周期上限也可能 exit0。新验收必须同时满足完整计划、全部负控、唯一且有序的 summary/GOOD TRAP、DiffTest 实际启用、实际进程退出0，拒绝周期上限/信号终止/失败标记。

实现只改 team：生成器输出显式 (case-index,repeat) 顺序，避免每片扫描整表找性能入口；判定器用对齐检测加两个精确64位比较，非对齐回退逐字节，`__builtin_memcpy` 避免 alias UB。scratch 只豁免声明的最终向量，32个初始寄存器永不豁免；没有减少任何输入/输出位、CSR 或异常比较。T12 不再复制728字节 trap_record 和512字节 comparable，每次直接校验原记录。

原 FNV64 是有碰撞可能的状态摘要，且不包含全部 trap/pre-state 字段；目标代码本来还有精确 judge，但不能仅凭一个64位摘要重建独立完整状态。新日志改为计划位图，**它编码每个固定 (id,repeat) 的精确判定结果，不冒充原始寄存器转储**。位图只在全状态 judge 成功后置位，重复执行拒绝；结束时 host 逐位比较精确选择集合、count、未用高位，并逐条验证全部性能记录。目标仍比较全32×128位初态/终态（仅明示 RVV scratch 除外）、六 CSR、精确 cause/PC/tval、状态位、canary 与存储结果。失败继续输出诊断；位图没有摘要碰撞。数据字典与执行计划以构建 source/manifest/image SHA256 绑定。

intake/t12-tests.untracked.py 原字节保留。其来源门禁/进程回执设计已审查并纳入 `team/scripts/t12-tests.py`；适配 b827 后继的分片与新检查器，而没有直接覆盖新实现。修复原入口仍调用旧 verbose checker、无切片参数、cwd 输出污染等问题。每次构建/运行用新目录，保存 argv、cwd、PID、开始结束时区时间、实际退出、timeout、原日志及确定性 gzip。原始失败不被清洗。

验证：旧25项 C 判定器测试通过；新98321项 C 检查覆盖32×128位逐位破坏、8种对齐、scratch仅终态豁免、六CSR与异常PC；24项Python测试含缺项/重项/重排/位图任一位翻转/错误退出/伪完成/性能配对错误拒绝。主机合成反例不计为DUT运行。

第二阶段已在 a4fea8f69f8c2c58f986858481257d3424a903f0 完成原190项，五片为 [0,13)、[13,63)、[63,113)、[113,163)、[163,190)。每片真实 DiffTest/GOOD TRAP/exit0；独立复核直接重读 source Git blobs、工具、ELF/BIN、manifest、原日志/gzip与进程回执，并从最终ELF机器字计算计时窗口的退休指令跨度，27条实测 instret 差值全部一致。

后续独立审查补强：原故障后恢复到v10会掩盖故障瞬间的v10污染；新非法VL恢复入口在任何向量结果写入前切合法捕获配置，保存全部32×128位，再执行合法恢复。故障CSR在原trap handler中先保存，未被捕获配置覆盖。此补强只针对本T12的VS开启/vstart0/非法VL域，不更改旧通用陷阱harness。每个异常用例还对快照v10和v16分别注入高位污染，必须检测到。

长循环用a4逐轮递增并存回t12_iterations，与32/256/128/1024的确定计划比较；目标负控再翻转计数，必须拒绝。功能向量终态不再独立承担循环次数证明。性能循环的执行量单独按生成源与最终ELF双路解码，检查64位范围及精确退休跨度；代码不把这个执行量检查当作rdcycle/FU延迟校准。新计划还给输入/期望数组显式8字节对齐，确保精确双64位比较实际启用，任意非对齐API仍有逐字节回退。
