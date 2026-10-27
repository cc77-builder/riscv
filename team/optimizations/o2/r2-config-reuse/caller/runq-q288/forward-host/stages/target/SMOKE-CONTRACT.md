# 单 hart 数学运行时与 TLS 探针 v1

身份 `r2-s3-forward-math-smoke-v1`。静态检查已证明本机固定 libm 的十个入口只额外需要 TLS errno 和栈保护符号，本探针验证这一极小闭包。它不是通用 libc、线程运行时或完整 forward 资格。

## 固定实现与内存

复用已有固定 AM/klib 静态库及原样 loader64.ld/section.ld，不重建或修改它们。团队 assembly main 在进入 C 之前一次设置 tp，使用普通、对齐、两侧带 guard 的 64 B 独立缓冲；不以 TLS 模板本身充当线程存储。最终 ELF 必须只有一个 STT_TLS `errno`、PT_TLS 文件长度 0、内存长度不超过 64、对齐不超过 16、起址满足对齐；不接受额外 TLS、GD/TLSDESC、TLS getter、IFUNC 或任何遗留动态重定位。

按固定 RISC-V TLS_TP_OFFSET=0 的主模块 ABI，逐条确认最终 IE GOT 槽的值等于 errno 的 TLS 偏移；最终 ELF 保留反汇编与 map。检查普通缓冲、栈、堆和模拟 RAM 的地址边界。运行时核对 `&errno == tp + ELF中的偏移`、清零初值、每次调用后 tp 和两侧 guard。固定 guard 仅用于确定性探针；真实 stack protector 控制故意改变 guard，必须进入不可返回的 `__stack_chk_fail` 并失败终止。

本机GNU ld留下一个全零R_RISCV_NONE占位，三字段均0，不要求任何运行时修补。自研门禁逐字节检查这种惰性占位并单独计数；任何非零loadable重定位仍拒绝。将该记录类型改成R_RISCV_RELATIVE的真实ELF负控必须在此门禁失败。最初按section存在性拒绝两次的原失败及源快照保持，不能将它们改判为通过。

## 数值与失败边界

覆盖所有十个入口的正常输入，含原 forward 的幂底数、head_size 和常见量化舍入；另外显式覆盖8个domain/range错误输入，验证 errno 写入真实TLS存储及必要NV/DZ/OF/UF/NX位。输入由固定原始位模式给出，正常有限结果与本机宿主libm输出逐位比较，±0不合并。错误输入的NaN只要求binary32 NaN分类，原宿主/目标返回位模式都保存；这一新探针政策不修改任何旧golden，也不授予full forward等价资格。

宿主与RISC-V libm不必有相同的异常标志编码或内部运算；保存宿主fenv和目标fcsr各自原值，不把二者直接相等作为条件。24个固定输入显式给出required/allowed mask：16个有限正常例只允许NX，5个domain例要求且只允许NV，极点例为DZ，溢出为OF|NX，下溢为UF|NX。各例先清fcsr，目标FRM始终RNE；本版不声称非零sticky保留或其他FRM资格。逐指令语义由固定原样NEMU DiffTest核对，不掩码、跳过或改写其fflags判定。

同一新正常ELF的派生数据控制分别触发错误golden和真实stack guard失败，必须在对应标签拒绝；正常运行及新进程重放必须完整打印全部结果、MATH_PASS和GOOD TRAP。所有命令、原文、最终ELF/bin、派生控制镜像及输入身份留存，检查失败不靠后继文件补造旧成功。

运行前固定既有EMU/NEMU/flash/辅助文件身份、官方AM源码身份和工具链，登记运行保护；输出独立、总体CPU≤4。此轮不据该探针报告应用加速比、完整token周期、训练质量或新ASIC资格。
