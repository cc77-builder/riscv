# llama2.c 量化 Q 投影调用适配器

**实验状态：完整整核验证未完成。** 本机 C、GNU/ELF 与目标负控已有结果；正常恢复因用户磁盘清理优先级中断，独立重放未启动。使用和资格边界先见 [RESULT.md](RESULT.md)，本模块尚不提供合格性能选择。

新增[研究方案](RESEARCH.md)与[acc8八累加器候选结果](acc8/RESULT.md)：六种完整Q路径的真实GNU静态筛选通过，目标周期未测；新候选的合同、源码、复现命令及原始证据从结果页进入。

这里把已有8×32整数叶接到公开消费者的完整288×288量化投影，提供一次权重打包、严格分组浮点消费、五种RVV对照、独立oracle和真实整核验证入口。数值及测量范围见 [CONTRACT.md](CONTRACT.md)。当前源码不是完整LLM推理实现；性能结论以实际完成的本模块结果为准。

## 在消费者中调用

原始权重是row-major `int8_t W[288][288]`，权重尺度是 `float Ws[288][9]`。每次投影接收预先量化的 `int8_t X[288]` 和 `float Xs[9]`，输出 `float Y[288]`。所有数组互不重叠。

```c
#include <stdalign.h>
#include "q288.h"

alignas(16) static int8_t packed[Q288_WEIGHTS];
alignas(16) static struct caller_slot slots[8];

/* 权重加载后执行一次。 */
struct q288_pack_context pack = {weight_q, packed};
q288_pack(&pack);

/* 同一份权重供后续输入复用；entry显式选择，没有隐藏分派。 */
struct q288_context q = {
    .packed = packed, .x = input_q,
    .weight_scale = weight_scale, .input_scale = input_scale,
    .y = output, .slots = slots,
    .entry = split_gemv_8x32_rvv4
};
q288_full(&q);
```

调用前由执行环境启用FS/VS并设FRM=RNE。保持 `-ffp-contract=off -fno-fast-math`；目标是RV64/lp64d、VLEN128。六个可选叶列于复用的 `split.h`。`q288.h`说明布局、对齐、完整槽和向量状态约定。示例显式使用原强RVV候选；本消费者是否可以选择vdot，须查看本合同的实测选择门槛。

## 构建与复现

使用已有工程依赖，在原生Linux工作区运行，所有输出使用仓库外的新目录：

```sh
MODULE=team/optimizations/o2/r2-config-reuse/caller/runq-q288
python3 "$MODULE/check.py" --action host --output "$OUT/host"
python3 "$MODULE/run.py" --repo "$PWD" --action build --output "$OUT/build"
python3 "$MODULE/check.py" --action elf --build "$OUT/build" --output "$OUT/elf-controls"
python3 "$MODULE/run.py" --repo "$PWD" --action run --build "$OUT/build" \
  --operation-id "$OPERATION_ID" --output "$OUT/campaign"
```

`OUT`须是新建的输出父目录，`OPERATION_ID`为当次唯一运行ID。固定T17身份默认取现有仓库记录，可用 `--identity`显式指定同一受检身份。运行前按协调Issue核实资源和冻结输入。

build输出的 `source/q288.c`、`source/q288.h`、`source/caller.h`、`source/split.h`、`source/kernels.S`可以组成实际消费者调用模块；`oracle.c`、`main.c`、`data.h`与定时器用于工程验收。复用叶体逐机器字对照原资格对象，实际消费者只链接所需模块，无需把未使用的旧完整库强行保留在ELF。

固定输入为合成数据；公开源、派生形状与GS的依据、FP规则、全量次数及选择限制均在合同中。它解决的是可复现消费者工程输入与调用语义，未新增真实检查点、完整token性能或人工验收资格。
