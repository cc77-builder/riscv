# llama2.c 量化 Q 投影调用适配器

当前新增的普通 C 调用与回退从 [完整 Q 融合入口](fused/README.md) 进入。固定目标计划已经完成完整运行、独立重放与原文审计；性能选择和范围见 [融合目标结果](fused/target/RESULT.md)。R5 稳定默认不会自动切换。

| 独立阶段 | 已完成结果 | 资格边界 |
|---|---|---|
| [原 v1/v2 实验](RESULT.md) | 实现、主机/GNU与目标负控；原正常批中断，证据保留 | 保持旧中断状态，不继承新候选 PASS |
| [acc8 第一阶段](acc8/RESULT.md) / [目标第二阶段](acc8/target/RESULT.md) | 八累加器驻留，真实目标负控/恢复/重放及新源复算闭合 | 诊断合同没有共同预热/性能锚点，不授予公平加速 |
| [完整 Q 融合](fused/target/RESULT.md) | 五路同 ELF、两个反序块、全部四锚点通过；本计划显式选择 fused-vdot | 相对最快纳入 RVV 保守少 6.844186% 周期；仅预打包、一次同方法 selfwarm 后的完整 Q |
| [完整上游 forward 观察](forward-host/RESULT.md) | 6 次宿主完整 forward、72 位置/矩阵捕获、两融合 ELF 模型数值接续 | 确定性未训练权重；未把候选替换进完整模型，未测 token 性能 |
| [融合剩余成本](fused/target/COST.md) | 原归档12窗与41,472笔计时custom事务身份、11项控制及新进程复算闭合 | 两FV窗无FU额外驻留/出口背压；接口上游间隔不可直接归因vset，无新性能资格 |
| [phased 排程](fused/phased/RESULT.md) | 一版实际 GNU/有限模型和新源静态复现 | 当前仍静态资格；新成本证据支持一次独立目标对照，尚无新的目标结果 |

研究依据与条件探索见 [RESEARCH.md](RESEARCH.md)。新的完整 Q 使用 288×288、GS32 的原严格分组 FP32 语义，量化输入和尺度由消费者提供；固定上游、来源和许可保持。

## 原包装的兼容调用

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

调用前由执行环境启用FS/VS并设FRM=RNE。保持 `-ffp-contract=off -fno-fast-math`；目标是RV64/lp64d、VLEN128。六个可选叶列于复用的 `split.h`。`q288.h`说明布局、对齐、完整槽和向量状态约定。示例显式使用原强RVV候选；原 v2 保持未闭合资格；新的获选融合入口见上方独立结果，不能只更换这里的叶就转移性能。

## 原 v2 实验的构建与复现

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
