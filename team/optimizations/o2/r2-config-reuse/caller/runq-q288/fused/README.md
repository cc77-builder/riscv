# 完整 Q 的融合调用入口

本模块提供两个普通 C ABI 函数：`q288_fused_vdot` 和 `q288_fused_rvv4`，均完成预量化、预打包的 288×288、GS32 投影。两者使用相同的接口、内存布局和严格逐组 FP32 消费顺序。源码与静态证据见 [RESULT.md](RESULT.md)，真实目标执行与本次比较结论见 [target/RESULT.md](target/RESULT.md)。性能选择以该目标结果的资格范围为准。

## 接口与回退

包含 `fused.h`，继续使用原 `struct q288_context`。量化输入与尺度由消费者提供；模型加载时调用原 `q288_pack` 一次，后续输入复用该 packed W。融合函数只读取 context 前六个指针，`entry` 字段保留但不参与选择，可以设为零。

下面是可单独编译的 C 示例。环境负责在调用前启用 FS/VS、设 FRM=RNE；所有传入数组与内部 packed/slots 均不重叠。

```c
#include <stdalign.h>
#include "fused.h"

alignas(16) static int8_t packed[Q288_WEIGHTS];
alignas(16) static struct caller_slot slots[8];

void consumer_load_weights(const int8_t *weight) {
    struct q288_pack_context pack = {weight, packed};
    q288_pack(&pack);
}

void consumer_project(const int8_t *input, const float *weight_scale,
                      const float *input_scale, float *output) {
    struct q288_context q = {
        .packed = packed, .x = input,
        .weight_scale = weight_scale, .input_scale = input_scale,
        .y = output, .slots = slots, .entry = 0
    };
    q288_fused_rvv4(&q);
}
```

示例显式调用 RVV4 入口；需要自定义指令版本时将这一行替换为 `q288_fused_vdot(&q)`，并在支持既定 vdot 编码的环境执行。两条入口之间的回退不需要重新打包或转换尺度。原 `q288_full`／acc8 包装及六个整数叶仍是另一层可选回退；其 `entry` 字段需要有效叶函数，不能照搬上述零值。R5 firstdot V2 的稳定选择和既有 API 不由本模块自动替换。

内存尺寸：packed W 82,944 字节，X 288 字节，Ws 为 row-major `[288][9]` 共10,368字节，Xs九个float共36字节，Y 288个float共1,152字节，slots八个完整128位值共128字节。float指针按4字节对齐，slots按16字节对齐；量化字节允许非对齐。函数覆盖全部Y和最后一组slots，保持context及全部输入只读。调用者自行安排持久权重和临时缓冲的生命周期。

## 生成与编译

在仓库根使用已有 RISC-V GNU 工具链。输出目录必须是仓库外的新目录，`FUSED_OUT` 不能已存在：

```sh
QMODULE=team/optimizations/o2/r2-config-reuse/caller/runq-q288
python3 "$QMODULE/fused/generate.py" --repo "$PWD" --output "$FUSED_OUT"
riscv64-linux-gnu-gcc -march=rv64gv -mabi=lp64d -mno-relax \
  -c "$FUSED_OUT/fused.S" -o "$FUSED_OUT/fused.o"
```

将 `fused.o` 与调用端链接。头文件搜索路径包含 `$QMODULE/fused`、`$QMODULE/../split` 和 `$QMODULE/..`。调用端使用 GNU C11、RV64/lp64d；关闭 fast math、FP contraction和LTO。若使用示例中的 `q288_pack`，还需链接现有 Q 包装对象；目标构建的 `objects/q288.o` 同时包含该函数。融合对象本身没有对六个旧整数叶的外部引用。

这两个入口复用同一固定团队源生成整数核心，完整Q对象内含两种实现。可以直接链接现成目标构建中的 `objects/fused.o`，但新的最终ELF、应用布局和调用计划仍需按影响验证；当前固定镜像的周期不能自动迁移到新程序。原始生成、独立编译和最终目标ELF身份均由本模块证据记录。

## 验证入口

静态及有限数值检查不启动EMU：

```sh
python3 "$QMODULE/fused/screen.py" --repo "$PWD" --output "$OUT/screen"
```

实际目标构建、七项ELF负例和串行运行：

```sh
python3 "$QMODULE/fused/target/run.py" --repo "$PWD" --action build --output "$OUT/build"
python3 "$QMODULE/fused/target/run.py" --repo "$PWD" --action elf \
  --build "$OUT/build" --output "$OUT/elf-controls"
python3 "$QMODULE/fused/target/run.py" --repo "$PWD" --action run \
  --build "$OUT/build" --output "$OUT/campaign" --operation-id "$OPERATION_ID"
```

`OUT`为新的仓库外父目录，`OPERATION_ID`为本次唯一ID。启动前遵守协调Issue的运行保护与总四核预算；运行器执行固定负控、恢复和独立重放，不把重放增加为统计样本。原文封存与新源审计命令见目标结果。

本模块验证的是有限值、RNE、严格两乘一加和原逐组顺序。没有完整模型检查点、量化质量、attention/KV cache、完整forward/token或实际ASIC功耗结论。[phased](phased/RESULT.md) 是另一版静态排程候选，不属于这里已冻结的目标镜像。
