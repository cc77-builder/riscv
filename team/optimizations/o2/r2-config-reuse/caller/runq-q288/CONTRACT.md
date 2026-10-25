# R2-S3：公开 runq 的完整量化 Q 投影边界 v1

合同 ID：`r2-s3-runq-q288-v1`。这是新消费者合同；不修改或继承旧调用窗的性能结论。

## 1. 公开消费者与范围

固定消费者是 [karpathy/llama2.c，350e04fe35433e6d2941dce5a1f53308f87058eb](https://github.com/karpathy/llama2.c/tree/350e04fe35433e6d2941dce5a1f53308f87058eb)。
[runq.c 的 matmul/forward](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/runq.c) 使用分组 INT8 dot、权重/输入尺度和逐组 float 累加，Q 投影尺寸为 dim×dim。
[README](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/README.md) 的原始 15M 配置 dim=288；[export.py](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/export.py) 默认 GS=64，不能整除时减半，因此此配置 GS=32。

本输入是由固定公式生成的确定性量化数组，沿用真实消费者的完整尺寸、权重生命周期、尺度布局、调用边界和运算顺序。没有下载模型检查点，也没有测量 tokenizer、quantize、KV cache、注意力、完整 forward、token/s、模型精度或整应用收益。288×288 投影的观察不能扩大成完整 LLM 结论。公开调用参数已经可由工程实现提供，不再以人工补参数为前置条件。

`oracle.c` 从该版本原始 row-major matmul 保持循环和表达式顺序，仅固定维度及拆开结构体字段；保留 MIT 许可 `LICENSE.llama2-c`。独立 Python golden 对每次乘法、加法明确舍入 binary32，实际本机 C oracle 与候选比较，目标 CPU 又实际执行一次原始 row-major oracle。

## 2. 接口、生命周期及精度

- M=K=288，GS=32，36 个 8 行 tile，每 tile 9 个 group。
- 一次性打包 `P[t,g,r,k] = W[(8*t+r)*288 + 32*g+k]`；额外持久权重空间 82,944 字节。原始权重仍保存用于独立检查，实际消费者可自行安排其生命周期。
- Ws 保持原始 `[288][9]` row-major 布局，共 10,368 字节；每输入 Xq=288 字节、Xs=36 字节；输出 Y=1,152 字节；8 个完整 128 位槽共128字节。
- `q288_full` 每次调用完成全部288输出，包括324次8×32整数叶调用、2,592次有符号 int32→float、5,184次float乘法和2,592次float加法。每行严格依次执行 `((float)dot * Ws) * Xs`，再累加，group顺序0…8。
- GNU C 单独编译，RV64/lp64d、VLEN128、`-ffp-contract=off -fno-fast-math`，禁止LTO、向量化及跨过程特化。运行前启用 FS、VS，FRM=RNE。正常 inexact flags 不视为错误；返回FRM必须仍为RNE。
- 32项signed-int8 dot绝对值不超过524,288，int32不会溢出，转float精确。主输入量化字节范围[-127,127]；本机额外测试[-128]边界。
- 所有输入/输出/槽/context互不重叠；float指针4字节对齐、槽16字节对齐。叶返回vl=8,vtype=0,vstart=0,vcsr=7。包装不得隐藏分配、重打包、量化或分派。
- row0前两组包含定向见证：严格运算输出 `0x00000000`，最后一步融合乘加输出 `0xa3800000`。不得通过容差掩盖语义改变。

## 3. 候选与公平比较

复用 split 合同的六个完整机器码叶体及逐字的允许重定位证书：vdot、S0 basic RVV、S0 reuse RVV、config-reuse basic RVV、firstdot reuse RVV、config-reuse reuse RVV（编号0…5）。每种方法共用完全相同的C包装、数据、打包权重、输出提取和浮点消费；重新选择本消费者中最快的合格RVV，不能沿用旧winner。没有RTL修改或新硬件收益资格。

主指标是完整Q调用的cycle差，包含全部整数叶、函数调用、浮点尺度处理和输出写入。一次性pack单独报告，不与Q窗混为一项；多个输入复用时可报告明确的 `pack + N×Q` 成本，不能假称测过完整模型。

## 4. 固定运行计划

单一BIN、同一固定T17 EMU/正常NEMU/AM/flash、相同seed。EMU串行；正式测量期间不运行其他重型构建、清理、压缩或EMU。总CPU上限四核。

1. 一次未计时8×32 vdot早期探针，使用从W取出的首panel。用于让负控尽早到达真实首vdot；不属于应用成本。
2. 一次实际完整pack计时窗（83KB全部覆盖），之后验证全部字节；目标上执行一次row-major FP oracle。
3. vdot独立遍历324组，检查所有2,592个完整槽（低32位及高96位）。
4. vdot与RVV4分别执行x0→x1→x0→x2，共8次完整投影；每次逐位检查全部288输出、末组完整槽、guards、context、向量状态与FRM。六个破坏/恢复控制覆盖输出位、槽低位、槽高位、guard、context输入指针和packed字节。
5. 六种方法各做一次未计时预热并检查输出。
6. 正式块0：RVV4锚点、方法0/1/2/3/4/5、RVV4锚点；块1：RVV4锚点、方法5/4/3/2/1/0、RVV4锚点。
7. 每个正式窗之前统一执行一次完整RVV4 conditioning，再统一poison输出/槽并重置向量和浮点状态。所有判定和UART在计时窗外，正式窗之间不做十进制转换或UART输出。

总计17计时窗（1 pack、12方法、4锚点），46完整Q调用、15,229整数叶调用，每个正常进程82,976条已提交vdot。first/warmup和恢复重放都不增加正式统计样本。

完整packed字节在pack后、功能段后、全部计时后检查；路径检查限制全部store只能落到允许stack/槽/Y（pack窗只写P），因此不为每窗额外扫描83KB。实际ELF常量数组必须与固定输入全部字节相同。原始W/Ws/X/Xs在路径中只读。

## 5. 验收与选择

先要求真实本机C oracle、全部输入生成/ELF/BIN/独立编译/叶体证书/地址控制流检查、目标输出和完整DiffTest均通过。路径检查器不计算FP或vector数值，明确要求未知算术值不能决定地址/分支；实际逐条退休PC/word、CSR采样、fence、ROB压缩和完整O2协议必须闭合。

实际ELF拒错控制覆盖signed→unsigned转换、乘法→加法、scale地址偏移和panel步长错误。FMA编码一律不在允许集合中。本机FMA见证确认该数据能暴露融合。

每个正式周期必须为正，选择采用整数比较：

- 四正式锚点：`100*max <= 101*min`；不满足则 HOLD。
- 每块vdot对该块五种RVV最快者：`200*vdot <= 199*fastest_rvv`。
- 保守全局门槛：`200*max(two_vdot) <= 199*min(ten_rvv)`。

仅所有正确性/上下文和分离门槛满足才标记 `VDOT_PREFERRED_IN_FIXED_PLAN`，否则保留显式RVV或HOLD。两种固定顺序只是有界观察，不给出统计显著性/稳定分布结论，也不修改已有稳定默认。

沿用团队冻结运行引擎的负控→正常恢复→独立进程重放；负控必须命中实际首vdot的vd0第100位差异，恢复与重放同BIN且完整结果一致。保留原始日志、失败、命令、源码快照、输入身份和process/state，禁止把历史PASS移到新候选。官方程序不修改。

## 6. 运行入口

在已准备依赖的原生Linux工作区，用本目录 `check.py --action host --output <新目录>` 运行本机C验收；`run.py --repo <仓库> --action build --output <新目录>` 生成并真实编译；随后 `check.py --action elf --build <build目录> --output <新目录>` 做ELF拒错；最后 `run.py --repo <仓库> --action run --build <build目录> --operation-id <唯一ID> --output <新目录>` 进行实际campaign。`--identity`默认使用仓库固定T17 identity-02.json。

输出必须位于仓库和冻结依赖之外。新增每次尝试使用新输出身份，不重写旧失败目录。执行前按Issue #2核实工作包、运行输入和资源保护。
