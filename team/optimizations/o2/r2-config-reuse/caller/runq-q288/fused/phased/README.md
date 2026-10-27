# Q288 phased 与两位 TA：普通 C 入口

这里提供固定 `288×288 / GS32 / VLEN128` 的完整 Q 投影入口，复用既有 packed 权重布局、尺度和 `q288_context`。调用方显式选择函数；R5 firstdot V2 的稳定默认及官方程序保持原样。

## 入口与资格

| 入口 | 实现 | 对应证据 |
| --- | --- | --- |
| `q288_phased_vdot` | 两阶段整数排程 + 行间向量 FP | [phased 完整目标结果](target/RESULT.md) |
| `q288_tail_vdot` | phased 的两条内部 e8 配置将 vta 置 1 | [TA 完整目标结果与选择](tail/target/RESULT.md) |
| `q288_fused_vdot` | 原 fused vdot | [原 fused 结果](../target/RESULT.md) |
| `q288_fused_rvv4` | 同边界的 RVV4 回退 | 各批次与候选同 ELF、同固定计划比较 |

phased 已通过自身固定目标计划的选择门槛。TA 是否应采用，以其独立目标结果的预定选择器为准。`export.py --variant tail` 只增加导出 TV 符号，不隐含采用 TV。

性能资格仅覆盖各批冻结的合成、预打包完整 Q 工作负载。实验在每个计时调用前执行一次同方法完整 Q selfwarm；这不等于所有缓存全热或任意新应用具有相同缓存状态。没有计入 pack、量化、token 或模型质量，也没有新增 ASIC 面积、时序、功耗结果。

## 布局、缓冲区与执行环境

| 对象 | 大小/布局 | 约束 |
| --- | --- | --- |
| 原始量化权重 W | `int8_t[288][288]`，82,944 B | 仅 pack 使用；原始与 packed 区间分离 |
| `packed` | 82,944 B | `P[t,g,r,k] = W[8*t+r][32*g+k]`；`t=0..35,g=0..8,r=0..7,k=0..31` |
| `x` | `int8_t[288]`，288 B | 已量化；字节指针可任意字节对齐 |
| `weight_scale` | `float[288][9]`，10,368 B | 保持原 row-major；4 B 对齐 |
| `input_scale` | `float[9]`，36 B | 4 B 对齐 |
| `y` | `float[288]`，1,152 B | 全部覆写；4 B 对齐 |
| `slots` | `struct caller_slot[8]`，128 B | 必须 16 B 对齐；类型自身只具有自然对齐 |
| `context` | RV64 下 56 B，七个指针 | 自然对齐，与全部缓冲区分离 |

投影入口接收前六个指针并忽略 `entry`；可以设置 `entry=0`。所有区间与 context 互不重叠。内核只在末尾写最后一个 tile/group 的八个完整 128 位 slots，高 96 位为零；slots 不保存所有中间组结果。

权重不变时可复用 packed W；权重字节变化后重新 pack。该生命周期约定不保证 packed W 常驻硬件缓存。投影不执行量化、不分配内存，也不进行隐藏 dispatch。并发调用由调用方提供各自的可写 Y、slots 和 context。

调用投影前启用 FS/VS，采用 RV64/lp64d、VLEN128、FRM=RNE。PV/FV/TV 要求处理器实现本项目当前受测的自定义 vdot 编码及语义（内部原型合同）；`-march=rv64gv` 只说明工具链的基础 ISA，不代表运行目标具备该扩展。FR 使用标准 RVV，仍须满足上述向量、浮点及缓冲条件。

普通标量和浮点 ABI 的被调用者保存寄存器及 sp 保持；全部向量寄存器可破坏。返回 `vl=8,vtype=0,vstart=0,vcsr=7`，FRM 保持，浮点异常标志允许正常累积。TV 的 TA 策略仅在内部使用，返回仍是 TU。上述投影状态约定不套用于普通 C 的 `q288_pack`。

每行按组 0→8 严格执行 `((float)dot * Ws) * Xs` 再累加；禁止 fast math、FMA 收缩、预合并尺度或跨组改变整数/FP 顺序。现有数值模型资格覆盖 RNE、有限输入尺度及有限结果；NaN/Inf、溢出到无穷、非 RNE 和异常标志的完整行为没有由该模型授予资格，详见[原数值合同](../CONTRACT.md)。

## 最小调用示意

以下缓冲区应由实际消费者填入合法数据。FS/VS 与 FRM 由应用启动和调用环境负责设置。

```c
#include "phased.h"

static int8_t weights[Q288_WEIGHTS], packed[Q288_WEIGHTS], x[Q288_DIM];
static float ws[Q288_DIM * Q288_GROUPS], xs[Q288_GROUPS], y[Q288_DIM];
static _Alignas(16) struct caller_slot slots[8];

void prepare_fixed_weights(void) {
    struct q288_pack_context p = { .weight = weights, .packed = packed };
    q288_pack(&p);
}

void project_current_input(void) {
    struct q288_context q = {
        .packed = packed, .x = x, .weight_scale = ws, .input_scale = xs,
        .y = y, .slots = slots, .entry = 0
    };
    q288_phased_vdot(&q);
}
```

若采用 TA，包含 `tail/tail.h` 并显式调用 `q288_tail_vdot(&q)`。切换为 FV 或 FR 只需更换直接调用函数，四个完整融合入口可复用同一 context、packed W 和尺度。旧 `q288_full` / acc8 包装会使用 `entry`，不能沿用这里的空叶函数指针。

## 导出与构建

`export.py` 复用已冻结目标生成器，只导出一个去重后的汇编源。`phased` 导出 FV/FR/PV，`tail` 导出 FV/FR/PV/TV。只链接该汇编对象一次；不要同时叠加旧 `fused.o` 或静态筛选用的 `phased.o` / `tail.o`。

下面在仓库外创建独立输出。`example.c` 是实际核验的普通 C 包装函数及 16 B 对齐 slots 示例；应用可以使用自己的消费者替代它。

```bash
repo=$(git rev-parse --show-toplevel)
caller="$repo/team/optimizations/o2/r2-config-reuse/caller"
q288="$caller/runq-q288"
module="$q288/fused/phased"
out=$(mktemp -d /tmp/q288-c-api.XXXXXXXX)
python3 -B "$module/export.py" --repo "$repo" --variant tail --output "$out/export"

base=(-march=rv64gv -mabi=lp64d -mcmodel=medany -mno-relax -fno-pic -fno-pie -fno-lto)
cflags=(-std=c11 -O2 -ffreestanding -fno-builtin -fno-tree-vectorize
        -fno-tree-slp-vectorize -fno-fast-math -ffp-contract=off
        -I"$module" -I"$caller" -I"$caller/split")
riscv64-linux-gnu-gcc "${base[@]}" "${cflags[@]}" -DQ288_INCLUDE_TAIL=1 \
    -c "$module/example.c" -o "$out/consumer.o"
riscv64-linux-gnu-gcc "${base[@]}" "${cflags[@]}" \
    -c "$q288/q288.c" -o "$out/pack.o"
riscv64-linux-gnu-gcc "${base[@]}" \
    -c "$out/export/q288-kernels.S" -o "$out/kernels.o"
```

将这三个对象接入应用自己的启动代码、链接脚本与执行环境。若只导出 `phased`，去掉示例 C 编译的 `-DQ288_INCLUDE_TAIL=1`。`example.c` 中全局 slots 仅演示对齐；多并发消费者应提供独立工作区。

## 普通 C 最终链接核验

`c_api_check.py` 用实际 GNU 编译/链接结果检查：每个导出恰有一个定义、无未解决符号、全部普通 C 包装保留、实际 AUIPC/JALR 或 JAL 调用目标正确，以及最终 ELF 中每个完整内核函数与指定目标 ELF 逐字节相同。slots 的 16 B 对齐与 128 B 大小也从最终 ELF 检查。调用解码器保留五个独立机器字反例/正例，包括 AUIPC 写 x0 的边界。

```bash
python3 -B "$module/c_api_check.py" --repo "$repo" --variant tail \
    --build /absolute/path/to/qualified-tail-build \
    --output /absolute/path/to/new-api-check-output
```

`--build` 指向已封存的对应 build；输出必须是输入和仓库之外的全新目录。也支持 `--variant phased`，使用原 phased build，并仅对原证书 `mode_phases` 字段内四个 tuple 应用已封存的 JSON 表示适配，完整结果严格比较不变。实际本轮检查见 [C API 核验摘要](evidence/ordinary-c-v1/summary.json) 与同目录原始证据包。

生成的 `consumer.elf` 是链接核验产物，没有由此新增应用运行或性能资格。函数体相同不保证新 ELF 的地址、调用上下文、缓存状态或周期相同。运行和性能结论继续由各自负控→恢复→回放及原文封存/隔离源码复算给出。
