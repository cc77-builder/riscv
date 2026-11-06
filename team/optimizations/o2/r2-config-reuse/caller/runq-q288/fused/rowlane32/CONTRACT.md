# Row32 W8 输出行向量化：有界筛选合同 v1

合同 `r2-s3-runq-rowlane32-screen-v1`。对应 Issue #2 WORK 6672608444。
本阶段新增一个独立团队软件候选，只做源码、真实 GNU ELF、有限数值/地址与已有参考功能筛选；不启动新 EMU 或硬件构建，不修改稳定入口。

## 1. 问题和决策

固定完整 Q288、GS32、VLEN128。把 32 个独立输出行映射到向量 lane，比较取消横向整数归约/结果收拢的收益与宽 LMUL、符号扩展、标量 X 装载及新权重布局的代价。架构指令、解码微操作和实际周期分别记录，任何一项都不能替代另外两项。

第一版只接受 W8；W16 扩展会把权重存储翻倍，暂停。输出行 tile32 是本次可证伪的候选参数，不是已证明的最优值。不为保住参数而增加 spill 或放松合同。若实际展开、功能或成本理由不成立，保留失败证据并停止。

## 2. 入口和数据布局

新符号 `q288_rowlane32_i8` 接受原 `struct q288_context` 的前六个指针，`entry` 字段不读。相同结构仅提供相同 ABI；其 `packed` 指针必须指向本候选的新布局，不能把原 P[t,g,row,k] 缓冲直接传入。

```text
P[t,g,k,r] = W[(32*t+r)*288 + 32*g+k]
t=0..8, g=0..8, k=0..31, r=0..31
byte offset = (((t*9+g)*32+k)*32+r)
```

W8 共 82,944B，无填充或数值转换。X 仍为 288B；Ws 仍为 row-major 的 288×9 个 binary32；Xs 为 9 个 binary32。Y 为全部 288 个 binary32，slots 为末组八个完整 128 位结果。量化数据允许任意字节对齐，float 指针 4B、slots 16B 对齐，各缓冲区不重叠。需要 FS/VS enabled、FRM=RNE。

packing 是新的、显式的工作。`pack_q288` 仅供格式/fixture 转换，不是目标机计时结果。后续已装载模型的核比较必须单独披露 packing；从原格式到首 token 的比较必须包括初始化和 packing。已有基线也有 packing 时，应比较两者实际成本差，不把其中一方的成本默认为零。

## 3. 整数和浮点语义

W、X 保留完整 signed-int8 输入域，包括 −128。每行、每 group 的 32 项整数积按 k 奇偶分入两组 int32 累加器；各有 16 项，范围 [−260096,262144]，最终和范围 [−520192,524288]。所有中间结果均无 int32 溢出，最终整数也可由 binary32 精确表示。

每行仍按 g0→g8 执行：

```text
dot = exact sum of this group's 32 signed products
p0 = binary32(dot)
p1 = RN_binary32(p0 * Ws[row,g])
p2 = RN_binary32(p1 * Xs[g])
acc = RN_binary32(acc + p2)
```

初始 acc 为 +0。不使用 FMA，不预合并尺度，不改变乘法顺序，不跨 group 合并整数和。不同输出行可并行，行内浮点运算树保持。

有限模型复用原 `fused/model.py` 的整数实现 binary32 RNE 运算及独立 row-major C/Python oracle；不修改这些文件。该模型覆盖有限值及有限结果，不模拟 fflags、NaN/Inf、非 RNE、硬件异常或周期；真实目标资格必须另证。合法 FP 异常标志允许正常累积。

## 4. 寄存器与可观察状态

| 向量寄存器 | 整数阶段 | 浮点阶段 |
| --- | --- | --- |
| v0…v7 | 偶 k 的 e32/m8 累加，组末并入奇 k | 保留完整整数和；v6…v7 为最后八行 |
| v8…v15 | 奇 k 的 e32/m8 累加 | signed 转换后的 FP 乘积 |
| v16…v23 | 保留 32 行 FP 累加 | 32 行 FP 累加 |
| v24…v25 | W8 load，EEW8/EMUL2 | Ws 的 e32/m8 组的一部分 |
| v28…v31 | vsext 结果，e16/m4 | Ws 的 e32/m8 组的一部分 |

所有组起点满足 LMUL/EMUL 对齐，扩展源与目的不重叠。integer 阶段 VL32/e16/m4；widening MAC 目的为 e32/m8，使用两条独立累加依赖。FP 阶段 VL32/e32/m8，Ws 用 stride36 读取，Xs 用原 scalar binary32。VL32 用寄存器 AVL 设置，不能误用五位立即数 `vsetivli`。

每个 32 行 tile 只存一次 Y。函数结束从 v6…v7 以 stride16 写末八槽低32，再用零向量对 offset4/8/12 三次 strided store 清高96；每个输出/slot 字节恰好写一次，不读回输出或槽。slots 不承诺中间过程值。

入口重置 vstart=0、vcsr=7；出口为 vl8/e8/m1/tu/mu、vstart0/vcsr7。所有整数/FP callee-saved、ra、sp 保留；仅 caller-saved scalar、ft0 与 vector registers 可改变。无栈分配、无外部调用、无额外内存输出。

## 5. 第一阶段证据和停止条件

1. 绑定未修改的父生成器/公共 RVV 源、FP 模型、fixture、oracle 及工具身份；真实 GNU 编译、链接和反汇编，实际 ELF 中保留旧 FR，逐字验证它没有改变。
2. 检查新指令的真实编码、组对齐和完整路径，执行实际函数的有限 ELF 模型；逐位核对全部 Y、末八槽、精确读写足迹、输入不变、ABI/CSR、无栈和正确返回。
3. 用 x0→x1→x0→x2、min×min、max×max、min×max、零权重及额外字节对齐检查；保持同一 packed 地址和前次向量状态，保留原 FMA/舍入见证。
4. 真实 ELF 负控至少覆盖短 VL、错误 X/W 步长、错误符号扩展/宽 MAC 源、组对齐、FP 乘法交换、缺失高96清零、缺失CSR重置和callee-saved破坏。不能把未知指令静默忽略。
5. 核对固定 T17 源码的实际 uop 分类、LMUL 展开和所需依赖；同时披露 scalar load、weight bytes、向量寄存器存活。静态数量只决定是否值得测量。
6. 已有 NEMU 功能检查如执行，使用现有未修改的参考库和新隔离输入/输出；不重建 NEMU，不继承历史候选的 PASS。无 NEMU 结果时明确写未验证。

最多使用已协调 CPU3 一核；新输出在既有常驻 runs 下的独立目录，当前输入锁和在途 GS32/paired16 任务保持。源和输出保留版本/哈希，实际失败保留原样。通过这些检查也不授予目标 DiffTest 或性能资格。

## 6. 后续边界

只有功能合格且成本理由仍成立，才提出同一新 ELF 中的完整 Q 公平比较；保留当时最快的合格 RVV 和合格 TA、全部锚点、事前计划及负控/恢复/重放。跨 ELF 的旧周期不能拼接成新加速比。

完整 Q 合格后才能考虑 K768 和完整消费者；本合同不修改 consumer、不处理最终 logits 以外的替代任务，不省略分类器行，不给完整 token、模型质量或 ASIC PPA 背书。

资料依据：RISC-V V1.0 的寄存器组、widening MAC、整数扩展及 strided load/store；llama.cpp 固定提交 `e14a779719652200cec7ad58dfa4820edc347182` 的 `ggml/src/ggml-cpu/arch/riscv/repack.cpp` 中 `ggml_gemv_q8_0_16x1_q8_0` 提供单向量输出-lane GEMV 先例。但其启用条件为 VLEN256/Zvfh，使用 half scale 和 FMA，不能直接迁移为本 T17/VLEN128/严格 FP 合同的性能结论。
