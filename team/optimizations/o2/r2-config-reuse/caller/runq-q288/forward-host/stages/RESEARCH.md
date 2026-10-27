# 公开实现、严格数值边界与后续决策

本轮研究支持复用既有 Q288 内核、沿输出行扩展完整消费者的路线。固定公开实现的布局和调度值得参考，其量化格式、浮点顺序及 VLEN 条件则需要分别核对。本轮已经把 37 张 K288 矩阵接入三路完整消费者并完成四个独立参考进程；后续投入应由当前消费者的目标证据决定。[实现及原文验证](NATIVE_RESULT.md) 与 [目标边界结果](projection/target/RESULT.md) 分别记录，不能合并成完整应用性能结论。

## 1. 研究实际改变了什么

| 固定公开实现观察 | 本项目采用的判断 |
|---|---|
| llama.cpp 交错多行权重、共享输入、在完整 K 内保留累加器 [G2] | 复用本项目已有 8 行输入复用和 K288 融合函数，先减少新增机器码与证明范围；不把已有设计重复计为本轮成果。 |
| Q8 scale 存 FP16，量化用倒数乘法；dot 消费 `Ws*Xs`，部分 repack 使用 FMA [G1,G2] | 保持 FP32 scale、真除法、先 Ws 后 Xs 再 sum 的独立 binary32 舍入。相同 GS32 不代表语义相同。 |
| RVV Softmax 调用 exp helper，并使用 f64 unordered widening 累加 [G4] | 不能保证原 FP32 左折叠逐位一致。这里只核实调用点，不推断 helper 内部算法。 |
| 该 16 行路径分派要求 Zvfh/VLEN256，VLEN128 分支仍为 TODO [G3] | 它是结构参考，不能当作本机 VLEN128 的现成实现。 |

原模型每 token 的矩阵工作量如下；计数来自固定原 forward [U1]，MAC 指一次 int8 乘累加，不包含 norm、量化、RoPE、attention、激活和残差。

| 矩阵 | 次数 | M×K | 原始 MAC |
|---|---:|---:|---:|
| Q/K/V/O | 24 | 288×288 | 1,990,656 |
| W1/W3 | 12 | 768×288 | 2,654,208 |
| classifier | 1 | 32000×288 | 9,216,000 |
| W2 | 6 | 288×768 | 1,327,104 |

前 37 张矩阵的 13,860,864 MAC 占总计 15,187,968 的 **91.262%**。当前实现将它们路由为 172 个完整 Q288 调用；W1/W3 的 192 行和 classifier 的 32 行尾部使用零权重、scale=1 的 scratch 补齐，再复制有效输出。13 个尾块额外执行 405,504 MAC。这个覆盖率已经有完整参考消费者证据，但仍不是周期占比或加速比。

6 张 K768 W2 保留原 scalar。将 K 拆成 288+288+192 后相加，会改变原 group0…23 的 FP32 累加顺序；因此没有用三个既有输出直接拼接 W2。W2 仅占 8.738% 原 MAC，不能由此认定它在优化后的消费者中耗时很少。权重逻辑读取量也不能当作 DRAM 实际流量。

## 2. 已实际出现的算术差异

团队 [research_witness.c](research_witness.c) 在 `arithmetic-witness-01` 通过实际 WSL 宿主 GCC 编译与运行。使用 binary32/RNE、显式中间舍入，没有目标性能资格：

| 见证 | 原始输入与结果 | 意义 |
|---|---|---|
| 量化除法与倒数乘法 | max=`3dc6318c`，x=`3ba24cdb`，scale=`3a47c10e`；商=`40d00000`，倒数乘积=`40cfffff`；量化分别为 **7、6** | 直接替换可改变 int8 结果。 |
| 固定分母后的 SiLU 算术 | x=`3b03126f`，den=`3fffbe88`；乘倒数=`3a8333fc`，直接除法=`3a8333fd` | 差一位；这里只比较已固定分母后的算术，不宣称完整 expf/SiLU 已验证。 |

实际源码 SHA-256 为 `f38b0dd750e4e40563cbcf299780b41a2809f93d5bbba53910a80cb5a59165e0`，原文命令、二进制及 stdout 随核心证据保留。它们是具体反例，不是对全部输入的等价性证明。

量化舍入还有独立的 flags 边界：现有 math/TLS 目标探针中 `round(-2.5)` 和 `round(2.5)` 返回 -3/+3、errno sentinel 保留、fcsr=0。C round 的 ties-away 值规则不要求非整数一定产生 NX；直接使用 RMM 浮点转整数，规范要求非精确转换置 NX。[C1,F1,V1] 因而只验证整数相同仍不够，完整 forward 已有的 sticky NX 会遮蔽局部差异。先加带符号 0.5 再 RTZ 也不能普遍替代：binary32 `0x3effffff` 在 RNE 加 0.5 后成为 1，而原 round 的结果为 0；这是算术推理，未作为新目标实跑记录。

原量化器没有 clamp。[U1] 全零组或 scale 下溢为零、非有限输入和 int8 不可表示值，均须明确入口定义域；不能静默改成 scale=1/q=0 或饱和转换，然后沿用原资格。当前消费者先验证其有限、正 scale、可表示域，官方原文保持原样。

## 3. 可选的非矩阵 RVV 起点

下表是改动与证明成本排序，**不是项目下一轮的固定优先级**。尚未为这些新候选编写或运行目标实现。

| 环节与真实规模 [U1] | 最小候选 | 需保留的合同 |
|---|---|---|
| RMSNorm：13×288 元素，末次 `o==x` | 先只向量化输出的两次乘法；求和、sqrtf 和倒数沿用原路径 | 先舍入 `ss*x` 再乘 weight；支持原地调用，不加入错误 restrict 假设。 |
| 量化：19×288、6×768，共 315 个 GS32 组 | 每组绝对值/max 与真除法可研究 RVV；先保留原 scalar round | 每组独立、FP32 scale/quotient、ties-away、errno/fcsr；不让临时 RMM 改变除法舍入。 |
| Attention Softmax：36 次，长度 pos+1 | 先保留 max、expf 和标量累加，只研究末尾真除法 | 不改成乘倒数，不把长度扩到无效元素，不替换 libm。 |

同宽 `vfredosum` 从真实标量种子按元素顺序加法；可将上一连续块的真实累计值带入下一块。[V1] 块内从零累加再合并、unordered reduction、FP64 累加和 FMA 都不能给出原 FP32 左折叠保证。例如平方项 `[2^24,1,1]` 在 RNE 左折叠得到 `2^24`，先合并两个 1 则得到 `2^24+2`；该例可由 RMS 输入 `[4096,1,1,…0]` 构造。这是可复核的舍入推理，不能当作已运行的新候选结果。

p0/p1/p2 的 attention Softmax 长度为 1/2/3，p255 才为 256；完整 forward 内没有 V32000 的词表 Softmax。[U1] 短长度暂留 scalar 只是控制工程成本，未测得它必然更快。将原比较扫描换成 `vfredmax` 还须处理 NaN/±0 和异常差异，不能仅根据普通有限输入推断全域等价。

## 4. 下一次决策所需证据

两个真实投影边界已完成目标运行与原文复算；后续先评估完整消费者的目标执行成本。完整参考镜像包含逐矩阵重算、完整状态比较和大转储，不能直接拿它当性能镜像。若另建精简镜像，需要用源码、最终 ELF、实际输入和原始输出重新闭合其身份；局部目标 PASS 与旧完整参考 PASS 不能自动拼接成新完整性能资格。

实际[完整验证程序](projection/main.c)每个正常进程执行3个TA forward，共516Q、5,349,888条custom，是当前有界目标正常进程207,360条的25.8倍；另有6个候选forward的222次原matmul重算，以及9份完整快照的33,222,816 B guest写入。这些工作解释了为什么不能直接迁移当前8M guest cycles、7200秒和1 GiB日志合同。现有目标解析器读取整份原文并构造事件列表，放大日志限额前还需评估解析峰值内存。参考API次数还包含验证程序的真实指令，不是香山cycle；adapter在guest停止后的内存导出则是宿主工作，应分开记录。

本轮已取得直接的容量证据：新边界每份正常stderr为408,925,813 B；06:37:27（UTC+08）的顺序审计观察点，Python进程的VmHWM已达4,635,124 kB，WSL MemTotal为16,094,260 kB。原始观察保存在交付包的`target-delivery-preparation-01/observation-0637.json`；这是该观察点的高水位，未冒充整个后续流程的最终峰值。完整消费者应先评估流式或分段审计及其等价性，不仅提高文件上限，也不把上述比例线性外推成确定的内存预测。

现有完整入口没有计时窗口和`TILE_*`协议，目标运行器又固定两case/40Q/8样本，不能只换BIN或放宽限额。较小的下一实现是单独抽出纯消费者包装，复用原上游正文、量化/数学函数、完整TA/FR函数、矩阵布局、172次路由及尾复制：先对同一消费者函数完成完整状态验证，再将oracle、快照和导出放到计时外。当前`checked_matmul`内部直接调用原matmul重算，在`projection_forward`外套计数器仍会计入该开销。新包装会改变ELF与调用上下文，需新身份和资格，不能声称整个旧机器路径不变。

取得实际目标成本后，再在 K768 W2、量化、norm、非线性之间选择投入。若完整运行成本暂不可接受，选择能改变决策的具名完整边界继续测量，并明确剩余缺口。完整LLM token/s不是当前赛题的新增硬门槛，这项工作按长期工程价值安排。RMSNorm 可作为非矩阵低改动起点，全 RVV round 和近似 exp 不应在缺乏瓶颈证据时先行复杂化。

另需保留组合边界：`full` 的 scalar+RoPE-cache 与 `projection` 的 scalar/FR/TA 是两份分别验证的消费者；当前 projection 未叠加 RoPE cache。两组成功不能写成 TA+RoPE-cache 完整模型已通过。

## 固定一级来源

下列 llama.cpp 文件统一固定 commit `63b4b303bd87456adc2f09d56c7e1f74e9e26673`；SHA-256 对应实际完整 UTF-8 原文件，不把公开项目版本当作本轮新消费者版本。

| ID | 来源与位置 | 完整文件身份 |
|---|---|---|
| U1 | [karpathy/llama2.c runq.c](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/runq.c)，量化145–170，norm/softmax282–315，forward344–480 | Git blob SHA-1 `42360ae97c724d28e11ac4545e30f57b7a9c9a8e`；本仓原文件 SHA-256 `ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548` |
| G1 | [RISC-V quants.c](https://github.com/ggml-org/llama.cpp/blob/63b4b303bd87456adc2f09d56c7e1f74e9e26673/ggml/src/ggml-cpu/arch/riscv/quants.c)，32–65、435–480 | `acf089ff8b39c1eeb7cb8f67df8ab49055a5b82a530b9c4871ea7ab732cf390f` |
| G2 | [RISC-V repack.cpp](https://github.com/ggml-org/llama.cpp/blob/63b4b303bd87456adc2f09d56c7e1f74e9e26673/ggml/src/ggml-cpu/arch/riscv/repack.cpp)，447–495 | `57b1362562ec0dfe8475e49a639783468da3ddbf7a5f009adcd01a7e4ed61fbf` |
| G3 | [repack.cpp 分派](https://github.com/ggml-org/llama.cpp/blob/63b4b303bd87456adc2f09d56c7e1f74e9e26673/ggml/src/ggml-cpu/repack.cpp)，5110–5131 | `159d4e6e863ca3d39e0ba0ab4fa3b10be7d0c778f6d59f2baea07dcab00c744a` |
| G4 | [vec.cpp](https://github.com/ggml-org/llama.cpp/blob/63b4b303bd87456adc2f09d56c7e1f74e9e26673/ggml/src/ggml-cpu/vec.cpp)，625–698 | `ed6690d3246f420c37d1441469a3631e365c24425f9722ca2f46651c88c1e292` |
| V1 | [Vector v1.0 历史源](https://github.com/riscvarchive/riscv-v-spec/blob/3570f998903f00352552b670f1f7b7334f0a144a/v-spec.adoc)，3738–3758、3930–4027 | `bfe42bd33dc6abeef5362f475605dda3d229e722257a613b0691cee760f04a19`；固定历史版本 |
| F1 | [官方 F 2.2](https://docs.riscv.org/reference/isa/unpriv/f-st-ext.html) 的 Conversion and Move Instructions；[非特权 ISA PDF](https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf) §20.7；[当前 V 1.0 页](https://docs.riscv.org/reference/isa/unpriv/v-st-ext) 的转换和同宽归约 | 2026-10-27 访问的官方当前页，未伪称固定发布标签；规范事实与实际 T17 支持验证分别对待 |
| C1 | [WG14 N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)，§7.12.9.6、F.10.6.6、§6.3.1.4 | 2011-04-12 委员会草案；不代替本项目固定 libm 的实际 flags |

本轮原始工程证据从 [RESULT.md](RESULT.md) 进入；上述建议不变更官方代码、验证标准或 R5 默认版本。
