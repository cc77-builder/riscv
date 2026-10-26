# 活动 forward 与 FP32→QKV 消费者

本模块把既有 TA/FR 完整 Q 内核接入实际状态推进，分两层提供工程证据：

| 入口 | 做什么 | 结果范围 |
| --- | --- | --- |
| `check.py` | 原样参考与两个独立候选状态，候选使用实际 RISC-V ELF 的有限执行模型 | 3 位置完整 logits/KV 逐位接续，以及消费前 K/V 污染、漏写负控 |
| `target/run.py` | 实际 FP32 激活、一次量化、顺序 Q/K/V 三次投影 | 同一最终 ELF 的整核 DiffTest 与固定计时边界 |
| `target/boundary.h` / `boundary.S` | 可复用的 RV64 普通 C 边界 | 固定 D288、GS32、VLEN128；显式选择 TA 或 FR |

完整 forward 的资格见 [活动状态结果](RESULT.md)，目标边界的选择与限制见 [QKV 结果](target/RESULT.md)。普通投影、pack 与去重汇编继续复用[现有 C 入口](../../fused/phased/README.md)。最终链接布局或调用方式变化后，原镜像周期不自动适用；R5 稳定默认沿用现有版本。

## 复验活动 forward

仓库外指定全新的输出目录，默认从已发布的 TA 证据包提取固定 ELF。也可用 `--elf /path/to/qualified-tail.elf` 显式提供，SHA-256 必须完全匹配。

```bash
repo=$(git rev-parse --show-toplevel)
module="$repo/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/active"
out=/absolute/path/to/new-active-forward-output
python3 -B "$module/check.py" --repo "$repo" --output "$out"
```

需要 Linux、Python 3.10 或更新版本、宿主 GCC 和 libm；本批实际验证环境为 Python 3.10.12/glibc 2.35，其他环境仍须实际复验。命令将自身及子进程限制到单 CPU。它重新编译宿主消费者，逐一运行正常、K 污染、V 污染、漏写四个新进程，保留失败回执和全部原始状态。宿主动态库、编译器与源码身份随结果保存。确定性权重用于工程接续，不表示训练模型质量，也不产生目标 token 周期。

已封存输入可独立启动复验：从 `evidence/active-v1/archive/raw.zip` 提取 `auditor/archive.py` 与同目录的 `auditor/check.py`，保持二者相邻，然后运行：

```bash
python3 -B /absolute/path/to/auditor/archive.py --action replay \
  --archive /absolute/path/to/evidence/active-v1/archive \
  --output /absolute/path/to/new-archived-forward-replay
```

启动器先逐项检查封存清单，再把源码和固定 ELF 提取到新的临时目录；子进程重新构建宿主库并运行全部四项验证。完整 logits/KV、真实输入捕获、机器回调日志和证书均逐字节对比。系统 GCC/libm/Python 仍是明确的外部运行依赖；这项复验不是操作系统安全沙箱或跨平台逐位一致承诺。

## 复验冻结目标与输入来源

目标命令需要已合格的 T17 EMU、正常 NEMU、AM、flash、RISC-V 交叉工具链及父身份记录。默认身份为 `team/optimizations/o2/repro/evidence/clean-reproduction-v1/reports/identity-02.json`；命令复用这些实物，不负责安装工具或重建整核环境。运行前按项目协作约定确认输入、资源和认领。

复验本批目标时直接使用仓库中的冻结 `target/evidence/input-v1/fixture.zip`，在新目录构建和执行完整负控→恢复→重放序列：

```bash
python3 -B "$module/target/run.py" --repo "$repo" --action build \
  --output /absolute/path/to/new-qkv-build
python3 -B "$module/target/run.py" --repo "$repo" --action elf \
  --build /absolute/path/to/new-qkv-build \
  --output /absolute/path/to/new-qkv-elf-controls
python3 -B "$module/target/run.py" --repo "$repo" --action run \
  --build /absolute/path/to/new-qkv-build \
  --operation-id unique-new-operation-id \
  --output /absolute/path/to/new-qkv-campaign
```

参数、计时计划和选择门槛见[目标合同](target/CONTRACT.md)。原始轨迹可通过已封存归档做独立源码复算，不新增 EMU：

```bash
python3 -B "$module/target/archive.py" --action audit-snapshot \
  --archive /absolute/path/to/published-target-archive \
  --output /absolute/path/to/new-target-source-audit
```

目标归档携带132项冻结运行源、5项归档审计器/支持工具，以及19个历史 Git 原对象；启动器仍需本检出中对应版本的补充审计器。它与前面的活动 forward 两文件启动器具有不同依赖范围。子进程的路径依赖探针及原文复算不能替代新环境的实物重建，也不是操作系统沙箱。

如需重新核对输入来源，可另从通过的活动 forward 结果执行：

```bash
python3 -B "$module/target/prepare.py" --repo "$repo" \
  --capture /absolute/path/to/accepted-active-output \
  --output /absolute/path/to/new-input-preparation
```

这一步重新生成输入、原量化器对照与证明材料；回执包含运行路径和耗时，新 ZIP 身份不保证等于发布包。它不是复验冻结目标的前置，也不会被上述 build 自动采用或覆盖旧 fixture。新输入实验须以可区分的身份和相应合同开展。

## 普通 C 的 FP32→QKV 调用

`qkv_context` 在 RV64 下有 7 个指针、共 56 B。三个 `q288_context` 必须共享 `x` 和 `input_scale`，分别指向自己的 packed 权重、权重尺度、输出及 slots。边界只量化一次，再按 Q、K、V 顺序调用同一个显式函数。调用前确认输入合法域；函数内部不分配、不打包、不检查数据域。

```c
#include "boundary.h"

static float fp[288], xs[9], y[3][288], ws[3][288 * 9];
static int8_t x[288], packed[3][288 * 288];
static _Alignas(16) struct caller_slot slots[3][8];

void project_qkv(void) {
    struct q288_context projection[3];
    for (unsigned i = 0; i < 3; ++i) {
        projection[i] = (struct q288_context){
            .packed = packed[i], .x = x,
            .weight_scale = ws[i], .input_scale = xs,
            .y = y[i], .slots = slots[i], .entry = 0
        };
    }
    struct qkv_context qkv = {
        .fp = fp, .x = x, .xs = xs,
        .projection = { &projection[0], &projection[1], &projection[2] },
        .kernel = q288_tail_vdot
    };
    qkv_boundary(&qkv);
}
```

例中的权重、尺度、packed 权重和激活应由消费者填入合法值；静态零初始化不是有效测试输入。回退时显式把 `kernel` 改为 `q288_fused_rvv4`。不支持把原 `q288_full` 当作这些无叶指针的融合入口使用。

| 缓冲与环境 | 要求 |
| --- | --- |
| `fp` | 288 个 FP32、1,152 B、4 B 对齐；只读 |
| `x` / `xs` | 288 B / 36 B，可写；尺度 4 B 对齐 |
| 三个投影 | 各自 82,944 B packed、10,368 B 权重尺度、1,152 B 输出、128 B slots；权重尺度与输出至少 4 B 对齐 |
| slots | 每份至少 16 B 对齐，互不重叠 |
| context 与别名 | 各 context 自然对齐、彼此及与全部数据区间分离；x、xs、三个 y/slots 的可写区间彼此不重叠，且与 fp、packed 权重和权重尺度等只读区间分离；三个 projection 共享同一 x/xs 指针，量化完成后将其只读使用 |
| 输入域 | 每 32 元素全部有限、最大绝对值非零，binary32(max/127) 是有限正数，binary32(x/scale) 有限且 ties-away 后属于 [-128,127] |
| 数值 | FP32 除法 RNE，整数转换 RMM；组内、组间顺序及两次尺度相乘保持原语义 |
| 投影有限域 | 沿用既有完整 Q 资格：权重尺度有限，每组 FP 中间值与最终结果有限；量化输入合法不自动保证投影合法 |
| 执行环境 | RV64/lp64d、VLEN128，FS/VS 已启用、FRM=RNE；TA 另要求当前项目 vdot 实现 |
| 返回状态 | 普通 ABI 的 callee-saved 寄存器和 sp 保持；向量寄存器可破坏，vl=8、vtype=0、vstart=0、vcsr=7，FRM 保持 |
| 浮点标志 | 正常累积；输入域允许部分次正规数及 NX/UF，不能将非零 fflags 一律判失败 |

单独调用 `qkv_quantize(fp,x,xs)` 只做量化，不执行投影，也不设置上述投影返回向量状态。零组、NaN/Inf、scale 下溢为零及舍入超 int8 范围均不支持，域外不承诺与原 C 转换行为等价；原参考程序保持原样。

每个并发消费者须提供自己的可写 x、xs、三个 y/slots 和 context；不可并发复用上述示例的静态工作区。固定 packed 权重及尺度可只读共享。

## 连接已有导出

使用现有 `fused/phased/export.py --variant tail` 导出一次去重的 `q288-kernels.S`。把本目录的 `target/boundary.S` 另编译成一个对象，与该导出对象、调用方及需要的 `q288_pack` 链接。不要同时链接重复的 phased/tail 静态筛选汇编。

```bash
caller="$repo/team/optimizations/o2/r2-config-reuse/caller"
q288="$caller/runq-q288"
python3 -B "$q288/fused/phased/export.py" --repo "$repo" --variant tail \
  --output /absolute/path/to/new-kernel-export
riscv64-linux-gnu-gcc -march=rv64gv -mabi=lp64d -mcmodel=medany \
  -mno-relax -fno-pic -fno-pie -fno-lto \
  -c "$module/target/boundary.S" -o /absolute/path/to/boundary.o
```

C 调用方还需 `-I"$module/target" -I"$q288" -I"$caller" -I"$caller/split"`，并沿用严格浮点和禁向量化编译条件。现有[普通 C 构建说明](../../fused/phased/README.md#导出与构建)给出完整基础参数。新目标 `main.c` 是实际编译运行的 C 消费者。

本 README 的唯一 C 代码块另有[两变体实际 GNU 链接证明](evidence/ordinary-c-v1/result.json)：FR 只替换一次显式 kernel 选择；验证真实重定位、最终指针地址及调用前 `context.kernel` 写入，检查调用目标、384 B/16 B 对齐 slots、无未解符号与重复导出，并逐字节核对四个投影和两个新边界函数。完整命令、源码和 ELF 保存在同目录归档。这个链接产物没有完整应用启动与有效示例输入，不授予新的运行或性能资格。
