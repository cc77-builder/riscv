# Config-reuse：普通 C 使用、复算与回退

Config-reuse 在 firstdot 的直线 GEMV 函数中删除已证明不改变状态的重复 `vsetivli x0`。vdot 与 RVV采用同一规则；指令减少与实际周期收益分开验收。采用范围和真实资格见 [RUNTIME_RESULT.md](RUNTIME_RESULT.md)，接口合同见 [C_CONTRACT.md](C_CONTRACT.md)。本说明随通过资格的独立候选交付，稳定 R5 入口仍可用于回退。

## 1. 公共函数与缓冲区

头文件为 [public/gemv.h](public/gemv.h)，汇编为 [public/gemv.S](public/gemv.S)。函数名包含形状、软件算法和指令实现：

```c
void config_reuse_gemv_8x32_reuse_vdot(const int8_t *packed_ax, void *output_slots);
```

`4x8`、`8x32`、`16x64`、`4x13` 各有 `basic`/`reuse` × `vdot`/`rvv`，共16个独立符号。函数名不自动决定采用；按结果页选择相应形状中更快且合格的实现。

| 条件 | 要求 |
| --- | --- |
| 输入 | 有符号INT8，行优先 `A[M][K]` 后紧接 `x[K]`，共 `M*K+K` 字节 |
| 输出 | 每行16字节槽，低32位为有符号INT32结果，高96位清零，共 `M*16` 字节 |
| 内存 | 输入输出各自16字节对齐、完整有效、互不重叠；紧密 `int32_t y[M]` 不能直接作为输出槽 |
| 平台 | 固定T17的RV64/lp64d/VLEN128环境，VS已启用；vdot入口需要项目自定义指令 |
| 状态 | 标准被调用者保存整数寄存器和栈保持；向量和调用者保存寄存器可改变 |
| 返回 | `VL=8`、`vtype=0`、`vstart=0`、`vcsr=7`；函数自行建立向量状态 |

下面展示实际应用如何打包和提取结果。打包及提取均在本轮固定内核调用窗之外，其成本没有包含在报告的内核周期中。

```c
#include <stdint.h>
#include "gemv.h"

struct result_slot { int32_t value; uint32_t high[3]; };
_Static_assert(sizeof(struct result_slot) == 16, "16-byte output slot");

void gemv8(const int8_t a[8][32], const int8_t x[32], int32_t y[8]) {
    _Alignas(16) int8_t packed_ax[8 * 32 + 32];
    _Alignas(16) struct result_slot slots[8];
    for (unsigned r = 0; r < 8; ++r)
        for (unsigned k = 0; k < 32; ++k)
            packed_ax[r * 32 + k] = a[r][k];
    for (unsigned k = 0; k < 32; ++k)
        packed_ax[8 * 32 + k] = x[k];
    config_reuse_gemv_8x32_reuse_vdot(packed_ax, slots);
    for (unsigned r = 0; r < 8; ++r) y[r] = slots[r].value;
}
```

调用方负责VS、指针生命周期、启动和最终链接环境。本接口承诺普通C ABI；C++调用方需自行匹配C链接声明。库包含全部16函数，包括自定义指令，并不是通用硬件上的纯RVV库。

## 2. 链接与从源构建

预编译库为 `evidence/runtime-v1/library/libconfig_reuse_gemv.a`，其 [library.json](evidence/runtime-v1/library/library.json) 记录合格完整对象、唯一库成员、16函数、真实consumer以及矩阵/C证据身份。

```bash
REPO=/path/to/full-riscv-checkout
S3="$REPO/team/optimizations/o2/r2-config-reuse"
LIB="$S3/evidence/runtime-v1/library"
OUT=/path/to/new-consumer-build
mkdir "$OUT"

riscv64-linux-gnu-gcc -std=c11 -march=rv64gcv -mabi=lp64d -mno-relax \
  -ffreestanding -O2 -I"$S3/public" -c app.c -o "$OUT/app.o"
riscv64-linux-gnu-ld -r --no-relax "$OUT/app.o" \
  "$LIB/libconfig_reuse_gemv.a" -o "$OUT/app-config-reuse.o"
```

`app.c` 可采用上面的完整示例。最后生成的是可重定位集成对象，最终应用还需要自己的平台启动代码和链接脚本。避免同时链接另一份定义相同 `config_reuse_gemv_*` 的汇编或对象。

库的 [consumer.c](evidence/runtime-v1/library/consumer.c) 用于覆盖16符号的链接，反复使用同一指针调用不同尺寸，不能直接作为运行示例。上述 `gemv8` 的真实GNU构建、链接及公共源完整对象重建见 [usage-check/report.json](evidence/runtime-v1/usage-check/report.json)；该检查不执行示例，也不测量完整应用。

从源构建时，使用匹配工具链与新的输出：

```bash
riscv64-linux-gnu-gcc -march=rv64gcv -mabi=lp64d -mno-relax \
  -c "$S3/public/gemv.S" -o "$OUT/gemv.o"
riscv64-linux-gnu-ar rcsD "$OUT/libconfig_reuse_gemv.a" "$OUT/gemv.o"
sha256sum "$OUT/gemv.o"
```

将完整对象哈希与 `library.json` 的 `qualified_object_sha256` 对照。不同对象、工具链、caller或最终布局需要按影响重新验证；相同对象的重新打包不需要再启动EMU。

## 3. 离线复算

使用完整Git检出和历史对象，在Linux/WSL原生目录执行，报告放到新的仓库外路径。严格复算不依赖原物理build目录，不启动EMU，也不把外部哈希当作重新取得的硬件实体。

```bash
IDENTITY="$REPO/team/optimizations/o2/repro/evidence/clean-reproduction-v1/reports/identity-02.json"
MATRIX="$S3/evidence/runtime-v1/matrix-archive"
C_ARCHIVE="$S3/evidence/runtime-v1/c-archive"

# C审计已经包含完整性能矩阵重算。
python3 -B "$S3/c_evidence.py" --repo "$REPO" --action audit \
  --identity "$IDENTITY" --matrix "$MATRIX" --archive "$C_ARCHIVE" \
  --output "$OUT/c-audit.json"

# 仅需性能报告时，可单独运行这一条。
python3 -B "$S3/runtime_evidence.py" --repo "$REPO" --action audit \
  --archive "$MATRIX" --output "$OUT/matrix-audit.json"

# 只复查已交付库的对象、成员和consumer字节。
python3 -B "$S3/library.py" --repo "$REPO" --action bytes --output "$LIB"
```

完整资格审计可直接选第一条，避免重复相同矩阵复算。第三条仅验证包装自洽，不替代真实运行证据。归档目录只接收其原清单载荷和固定元数据，不能把新报告写入归档。

## 4. 重新构建与实跑

先检查Issue活动、物理T17来源与四核总预算。脚本绑定固定身份；新机器或硬件不能通过改哈希冒充当前资格。新候选先按 [RUNTIME_CONTRACT.md](RUNTIME_CONTRACT.md) 做有界探针；下面是同一已选定版本完整矩阵的独立复现入口：

```bash
python3 -B "$S3/runtime_experiment.py" --repo "$REPO" --action build \
  --identity "$IDENTITY" --shards 1 3 5 7 --datasets 0 1 2 --jobs 4 \
  --output "$OUT/build-matrix"

taskset -c 0-3 python3 -B "$S3/runtime_experiment.py" --repo "$REPO" --action run \
  --identity "$IDENTITY" --build "$OUT/build-matrix" --negative --replay \
  --operation-id unique-operation-id --output "$OUT/run-matrix"

python3 -B "$S3/runtime_evidence.py" --repo "$REPO" --action pack \
  --identity "$IDENTITY" --run "$OUT/run-matrix" --scope matrix \
  --archive "$OUT/matrix-archive"
```

构建可最多4任务，性能进程串行。不要对既有运行目录重复启动；失败先读state、原文和真实进程。本轮实际采用“探针两图＋剩余22图”的分批执行，既有探针窗口和重放在聚合审计中只计一次，精确命令及路径见 [运行定位](evidence/runtime-v1/runtime/locations.json)。

普通C的 `build → run → export` 与库命令见 [C合同](C_CONTRACT.md)。取得新公共源后，先比较其与当前发布源，再封存C证据：

```bash
cmp "$OUT/qualified-public-source/gemv.S" "$S3/public/gemv.S"
cmp "$OUT/qualified-public-source/gemv.h" "$S3/public/gemv.h"
python3 -B "$S3/c_evidence.py" --repo "$REPO" --action pack \
  --identity "$IDENTITY" --matrix "$OUT/matrix-archive" \
  --build "$OUT/c-build" --run "$OUT/c-run" --archive "$OUT/c-archive"
```

公共源不同则停止沿用当前身份并定位原因；不能覆盖冻结源或回填旧PASS。

## 5. 回退

| 目的 | 做法 |
| --- | --- |
| 使用此前firstdot | 按 [FIRSTDOT_README.md](../r2-vector-accum/FIRSTDOT_README.md) 改用 `firstdot_gemv_*` 和原 `libfirstdot_gemv.a`，重新编译调用端 |
| 使用稳定默认 | 按 [STABLE.md](../r2-select/STABLE.md) 使用 `xs_gemv_<shape>` 和原 `libxs_gemv.a` |
| 使用稳定RVV | 采用稳定头的显式 `_rvv` 入口，或首次包含头前设置 `XS_GEMV_FORCE_RVV=1` 并重新编译 |
| 恢复本轮前源码 | 在独立工作区检出 `43e562d5e174763d9469b6c1c2124df0d60dc576`，保留共享历史和本轮证据 |

稳定头的宏不控制显式 `config_reuse_gemv_*` 调用，也不改变已经编译的代码。三个库使用不同公开符号；混合应用仍需检查其最终链接与实际执行影响。

当前工程范围是固定GEMV调用窗、普通C资格与可回退的独立库。完整应用、LLM、ASIC PPA、新机器安装和人工ACK的状态分别见结果页，不能从删指令数或本库的局部周期代推。
