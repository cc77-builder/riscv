# P3 宿主数值门禁计划

仅验证当前固定 GNU 产物的宿主数值、控制、地址与 ABI 合同；不运行 EMU/NEMU。
源闭包与根合同冻结前只读审查，不执行候选验证。

1. 独立 binary32 oracle：用有理数实现 RNE 的除法、乘法、加法，RMM 整数转换；拒绝零组、NaN、Inf、scale=0、转换越界。
2. 两个 288 FP32 活动输入与独立语义夹具逐元素验证全部 q 字节、9 个 scale 的 binary32 位。
3. 将数学语义绑定到当前 GNU 量化器实际机器字和显式 rm；RNE 除法与 RMM 转换必须拒绝被篡改的 op。
4. 对两输入、TA/FR、三 Q/K/V 共全部 864 输出逐位检查，检查 3 组最后完整 128 位 slots。
5. 审查当前 ELF 的 CSR 返回合同、callee-saved/栈对齐/还原、只读输入、guards、context 和共享 x/xs 地址；negative controls 需作用于实际 ELF 或验证器观察的实际数据，不继承供体 PASS。
6. 分开记录 HOST_MODEL_PASS、GNU_STATIC_PASS 与 TARGET_NOT_TESTED。宿主地址模型不视为原生执行 FP 指令，fflags 不能冒称目标已测。

执行固定 CPU6，所有原始命令、输入哈希、stdout/stderr、状态与失败保存在本目录对应证据及外部 W/numeric；不覆盖先前失败。
