# GS32 整组量化：独立候选 v1

合同 `r2-s3-gs32-quantize-v1`。当前阶段为源码与短参考原型准备，尚无候选 GNU、NEMU、EMU 或周期资格。新叶位于 `fused/gs32-rvv/quantize/`，不修改父 GS32、paired16、当前 first-forward 实验、原 upstream/runq.c 或原参考/验证程序。

## 1. 要作的决定

判断将每元素的 double fabs/round、精度转换和 flags CSR 往返改为每 GS32 组处理，是否值得进一步完整消费者验证。原完整 forward 每次有 19×288＋6×768＝10,080 个量化元素、315 组。实际冻结 GNU 的 quantize 每元素调用 fabs 和 round；正常 round 自身为13条指令，包含 frflags/fsflags，fabs为2条。因此这些 helper 另有151,200条退休指令和20,160次逐元素 flags CSR 访问，不能只看 quantize 本体的旧261,236条。

新实现仍执行315次 scale 除法和10,080个元素除法；不以倒数乘法、近似除法或数值重关联替代。正常组的转换环境管理为 frcsr→fsrmi→fscsr 三次CSR访问，总计945次，另计调用入口和向量状态管理。指令/CSR减少不是目标周期收益或上限；vector divider、LMUL拆分、配置与归约成本仍未知。若量化原周期份额为 f、实际速度比为 s，则仅在其余工作不变的因果条件下，总窗口减少为 f×(1−1/s)；当前 f、s 均未测得。

## 2. 入口与内存边界

独立符号 `r2_quantize_gs32_rvv` 使用原 QuantizedTensor 的 RV64 ABI：a0指向两个连续指针 `{int8_t *q, float *s}`，a1为float输入，a2为int长度。原 `quantize` 与 `GS` 由未修改的团队消费者对象/原upstream编译对象提供，不重新定义或补丁修改。

目标为现有 RV64G＋RVV、VLEN128、FS/VS已启用。输入float和scale各4B对齐；输入、q、scale和context互不重叠且在调用期间有效；GS和输入不被并发修改。完整消费者的 x/xb/hb、xq/hq、xs/hs 独立数组满足此边界。此原型不是可任意别名的通用量化API。

快速路径要求 GS=32、n>0且为32倍数、FRM=RNE、VSTART=0和合法VTYPE；当前实际消费者长度为288/768。其他长度、GS或合法舍入模式走原scalar全调用。快速路径只读n个float，写n个q字节和n/32个scale；未使用的scale数组尾部仍是完整state的一部分，禁止清零或扩大写入。

不分配栈或heap，不增加packing，不调用其他数学函数。保存并恢复入口VL/VTYPE；VSTART为零的快速路径返回仍为零，VCSR不改。整数及FP callee-saved、ra/sp均不改；a/t临时寄存器、ft0–ft2及v1/v8–v23可改变。与原量化的逐组FP flags和最终FRM一致；不要求caller-saved向量内容相同。

## 3. 数值与异常标志

每组清除32个binary32的sign bit，用unsigned整数最大值取得绝对最大值。任何NaN/Inf使该最大位模式达到0x7f800000；全零组或非有限组退回原scalar。有限输入的原fabs、S→D→S转换与最大值比较均不引入额外异常，整数最大值不改变其数值结果。

保留 `scale=RN_binary32(wmax/127)` 和 `z[i]=RN_binary32(x[i]/scale)` 的原RNE关系。本版把normal scale作为已证明范围，计算出的scale若小于最小normal binary32便保守退回原scalar；不以scale>0替代这个域判据。令u=2^-24，normal scale时 `abs(z) <= 127*(1+u)/(1-u) < 127.5`，故RMM转换得到[-127,127]内整数。若精确scale略低于最小normal而舍入为normal，wmax/scale小于127，也满足此界；较小输入的次正规商通过RNE单调性包含，不对下溢商直接套相对误差。随后32→16→8的整数窄化只保留所需低字节，不饱和、不改变VCSR。

原round正常域以静态RMM转换并恢复进入round时的flags。新实现必须在scale和整组vfdiv完成后保存FCSR，临时设置RMM，执行vfcvt.x.f.v，再恢复这个post-div快照；转换自身的NX被删除，原除法产生的全部flags保留，FRM同时恢复RNE。不得恢复调用入口flags替代成功路径的post-div快照。

若任意组转入fallback，恢复整个调用入口FCSR、VL/VTYPE和原参数，再尾调用原quantize处理整个输入。早先组可能已写输出，但输入不别名，原函数会安全覆盖这些输出。fallback可重复读写已处理组，但不得越界；原零/NaN/Inf/下溢行为保持，不能擅自“修复”原结果。

设计见证：`[127,0.5,0…]`应得到q=1、flags=0，能区分RNE错误和裸RMM多NX；`[1,0…]`的scale除法产生NX，能检出错误恢复入口flags。令η=2^-149，`[254,η,−η,0…]`的scale=2精确正常，但小输入除法产生UF|NX=0x03，二者均须保留。`[190η,0…]`的scale舍入为η、quotient为190，说明normal-scale的[-127,127]界不能直接外推；v1因此保留保守回退。原scalar最终sb与非饱和窄化仍可能留下同一低字节，不据此断言所有扩域实现必错。后续坏组发生在已处理正常组之后也须覆盖。

规范依据：[RVV转换、归约与整数窄化](https://docs.riscv.org/reference/isa/v20260120/unpriv/v-st-ext.html)、[FCSR/舍入/异常标志](https://docs.riscv.org/reference/isa/v20260120/unpriv/f-st-ext.html)。具体原round/fabs语义以实际链接的固定机器码为准，不凭通用C库约定推断。

## 4. 最小验证和停止条件

先固定独立GNU对象/ELF以及未改原quantize、fabs、round的来源，检查真实指令和fallback目标。复用既有原NEMU共享库与成熟reference-adapter；不修改、重建官方参考，不另造CPU/浮点模拟器。独立新输出保留命令、源码/ELF/库身份、原始dump、退出码和清理事实。

同一guest依次调用原scalar与新入口，比较完整q、全部scale存储（含未用尾部）、guard、输入原字节、FCSR、VL/VTYPE/VSTART/VCSR以及ABI。正常组、正负边界、±0、半整数相邻值、极小/极大有限值、NaN/Inf、后组fallback、合法非RNE模式、n非整组和GS非32按不同义务覆盖。除最终汇总外保留每例输入/输出/flags原始记录。

至少三个独立候选负控：RMM改RNE、漏post-div FCSR恢复、错误恢复入口FCSR；必须由上述指定见证分别检出。原scalar和判据不改。原型通过只说明该实际ELF和有限样本；不继承完整consumer、目标DiffTest或性能资格。

2026-11-06 05:01Z 已收到 CPU1 释放及主协调的短构建/NEMU授权；CPU0/2/3留给既有三臂forward。本叶仅使用CPU1、GNU `-j1`，不启动EMU，也不把候选混入冻结FR/G/P。原first-forward运行根有写锁，读取该根的首次预检被拒且未执行；改用已关闭的 `norm-resume-20261027-2000/consumer-build-02` 原对象，不绕过锁。父对象SHA为 `6d50d5b613f6bdb7011f4fd148e668ca44e23bb59b11e2b9e6fcbaa69a7207bb`，同一 `libm.a` SHA为 `fab30dd1171318d09d987f7f84a9542e2b0504b27bca4170ddc22454c6b8041b`。该父ELF与实际first-forward缓存的quantize/round/fabs指令，仅外部目标重定位immediate不同；已实际读取分母127.0和round阈值2^53。新链接继续检查原函数全部非重定位机器码、调用目标及常量。

独立guest含30个固定案例，每例保留输入原件与两次调用后的完整输入、完整q和全部scale存储、context与guard、入口/出口CSR和24个callee-saved寄存器检查。一个ELF包含正常候选及三种单点错误变体；四个独立参考进程仅修改显式模式字，正常应GOOD，三个负控应BAD且由指定见证检出。只记录参考instret，不记录或声称香山周期；每进程上限20M API调用/120秒。固定参考运行器和原共享库不修改、不重建，官方AM前后目录/字节核验，构建与原始dump放于独立runs目录。

若依赖封装连续失败，优先复用更小的既有参考入口，不能用反复包装替代技术判别。只有短参考语义和成本理由仍成立，才提出独立G与G＋quantize完整消费者比较；不因已投入工作强行推进。

首次 `attempt-01` 的 GNU 链接与原函数身份核对成功，但参考进程只执行88次API调用，在AM设备初始化 `__am_init_uartlite` 写地址0x4060000c时发生store access fault，尚未进入任何量化用例；不把它记为候选数值失败。原始输出保留。后续隔离尝试采用团队自研无设备启动入口和链接脚本，入口0x80000000、自有64KiB对齐栈，初始化FS/VS/FCSR/vstart后进入同一测试函数；不链接AM设备运行时。原consumer对象、libm、参考共享库、参考运行器和boot不改，原函数机器码与常量继续核对。测试镜像的独立启动不取得实际应用启动或目标运行资格。
