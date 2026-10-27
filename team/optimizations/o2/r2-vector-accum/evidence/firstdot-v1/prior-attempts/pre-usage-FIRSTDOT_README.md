# Firstdot：普通 C 使用、复算与回退

Firstdot 将每个行组的第一条 vdot 直接写入最终累加寄存器。它与原 S1 使用相同的点积条数和硬件；实际性能、采用范围及验证层级见 [FIRSTDOT_RESULT.md](FIRSTDOT_RESULT.md)。这里说明如何消费独立函数库，不修改 [R5 稳定默认入口](../r2-select/STABLE.md)。

## 1. 选择入口

新头文件为 [firstdot/public/gemv.h](firstdot/public/gemv.h)，源为 [firstdot/public/gemv.S](firstdot/public/gemv.S)。符号形式如下：

```c
void firstdot_gemv_8x32_reuse_vdot(const int8_t *packed_ax, void *output_slots);
```

四种形状 `4x8`、`8x32`、`16x64`、`4x13`，分别提供 `basic` / `reuse` 和 `vdot` / `rvv`，共16个函数。名称表示算法实现，不自动决定采用。选择应查看本轮完整矩阵的更快合格 RVV 和原 S1；尤其不能因为 K13 提供 vdot 符号，就把它替换为默认。

本接口没有运行时分派，也没有改写 `xs_gemv_*` 或 `r4_gemv_*`。只承诺普通 C 链接；没有增加 C++ `extern "C"` 接口合同。

## 2. 缓冲区与运行环境

| 条件 | 要求 |
| --- | --- |
| 输入 | 有符号 INT8，行优先 `A[M][K]` 后紧接 `x[K]`，共 `M*K+K` 字节 |
| 输出 | 每行一个16字节槽，低32位为有符号 INT32 点积，高96位清零，共 `M*16` 字节 |
| 内存 | 输入输出各自16字节对齐、互不重叠、具有完整有效容量；不能传紧密的 `int32_t y[M]` |
| 平台 | 本轮固定 T17 的 RV64 / lp64d / VLEN128 环境，VS 已启用；vdot 入口需要项目自定义指令 |
| 状态 | 栈和整数被调用者保存寄存器保持；调用者保存寄存器、向量寄存器及配置可改变 |
| 返回状态 | `VL=8`、`vtype=0`、`vstart=0`、`vcsr=7`；函数自行建立状态，不要求预清零向量 |

完整语义以 [FIRSTDOT_C_CONTRACT.md](FIRSTDOT_C_CONTRACT.md) 及其引用的原 C 调用合同为准。RVV 函数也只取得这里列出的平台资格；预编译对象包含全部16个函数，并非不含 vdot 的通用 RVV 库。

下面的调用端在匹配的平台中接收普通矩阵与向量，打包后调用8×32内核。输入打包和 `slots` 到 `y` 的结果提取均在 firstdot 内核调用之外；它们的代价没有包含在本轮固定内核调用窗中。

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
    firstdot_gemv_8x32_reuse_vdot(packed_ax, slots);
    for (unsigned r = 0; r < 8; ++r) y[r] = slots[r].value;
}
```

该示例是使用说明，不是新的完整应用性能测试。调用方仍负责启用 VS、有效指针、生命周期以及实际应用的启动和链接环境。

## 3. 链接已交付的静态库

预编译库及其真实 GNU 命令位于 [evidence/firstdot-v1/library](evidence/firstdot-v1/library/library.json)。`library.json` 记录完整对象、库成员、全部16函数、C consumer 链接和矩阵/C证据身份；`library-check.json` 为包装检查。库成员来自已经实际运行资格验证的普通 C 对象，不通过改写机器码获得。

```bash
REPO=/path/to/full-riscv-checkout
S1="$REPO/team/optimizations/o2/r2-vector-accum"
LIB="$S1/evidence/firstdot-v1/library"
OUT=/path/to/new-consumer-build
mkdir "$OUT"

riscv64-linux-gnu-gcc -std=c11 -march=rv64gcv -mabi=lp64d -mno-relax \
  -ffreestanding -O2 -I"$S1/firstdot/public" \
  -c app.c -o "$OUT/app.o"

riscv64-linux-gnu-ld -r --no-relax "$OUT/app.o" \
  "$LIB/libfirstdot_gemv.a" -o "$OUT/app-firstdot.o"
```

`app.c` 可采用上面的调用端。最后一行生成可重定位集成对象；最终应用还需自己的 AM/平台启动代码和链接脚本。不要再同时链接另一份定义相同 `firstdot_gemv_*` 的 `gemv.S` 或对象。

库内的 [consumer.c](evidence/firstdot-v1/library/consumer.c) 仅用于链接覆盖全部16个符号。它反复使用同一指针调用不同尺寸，不是可直接运行的通用调用示例。

若自行从源构建，使用新输出目录和同一 GNU 工具链：

```bash
riscv64-linux-gnu-gcc -march=rv64gcv -mabi=lp64d -mno-relax \
  -c "$S1/firstdot/public/gemv.S" -o "$OUT/gemv.o"
riscv64-linux-gnu-ar rcsD "$OUT/libfirstdot_gemv.a" "$OUT/gemv.o"
sha256sum "$OUT/gemv.o"
```

与交付 `library.json` 中 `qualified_object_sha256` 比较完整对象；不同对象、工具链、caller 或最终布局不能自动继承同一机器码身份和周期。无需为重新打包相同对象重跑 EMU，但新应用的正确性与性能仍须按其实际影响验证。

## 4. 离线复算与重新实跑

必须使用完整 Git 检出及冻结历史对象；仅复制新脚本或解压 `tools` 不够。严格原文重算在 Linux/WSL 原生目录执行，输出到新的仓库外目录。它不启动 EMU，也不重新验证未分发的硬件/工具链实体。

```bash
MATRIX="$S1/evidence/firstdot-v1/matrix-archive"
C_ARCHIVE="$S1/evidence/firstdot-v1/c-archive"
IDENTITY="$REPO/team/optimizations/o2/repro/evidence/clean-reproduction-v1/reports/identity-02.json"

# 可选：仅需独立性能矩阵报告时执行；下一条 C 审计已包含矩阵重算。
python3 -B "$S1/firstdot_evidence.py" --repo "$REPO" --action audit \
  --archive "$MATRIX" --output "$OUT/matrix-audit.json"

python3 -B "$S1/firstdot_c_evidence.py" --repo "$REPO" --action audit \
  --identity "$IDENTITY" --matrix "$MATRIX" --archive "$C_ARCHIVE" \
  --output "$OUT/c-audit.json"

python3 -B "$S1/firstdot_library.py" --repo "$REPO" --action bytes \
  --output "$LIB"
```

第一项只重算性能矩阵；第二项连带重算完整矩阵与普通 C 原始日志，因此需要完整资格审计时可直接执行第二项，避免重复。最后一项只复查现有库包装字节，不代替原文审计。归档根只允许原清单文件和三个固定元数据文件，不能把新报告写进去。

重新实跑遵循 [性能合同](FIRSTDOT_CONTRACT.md) 和 [C/库合同](FIRSTDOT_C_CONTRACT.md)：先核实原 T17 物理身份、Issue 活动和四核总预算，再创建新输出。实际机器路径、构建/运行/宿主回执及全部尝试在 [运行定位](evidence/firstdot-v1/runtime/locations.json)。当前脚本绑定原 T17 身份；新机器或新硬件需通过其来源流程形成新身份与合同，不能直接替换哈希或把旧 PASS 转移过去。

在 C 合同的 `build → run → export` 均完成后，先比较导出公共源与当前检出的发布源，再为本次新运行封存 C 证据。以下路径的含义与合同一致，`$OUT/c-build`、`$OUT/c-run` 是刚完成的构建和三进程运行，`$MATRIX` 是通过完整审计的24图矩阵归档；新输出必须尚不存在：

```bash
cmp "$OUT/qualified-public-source/gemv.S" "$S1/firstdot/public/gemv.S"
cmp "$OUT/qualified-public-source/gemv.h" "$S1/firstdot/public/gemv.h"

python3 -B "$S1/firstdot_c_evidence.py" --repo "$REPO" --action pack \
  --identity "$IDENTITY" --matrix "$MATRIX" --build "$OUT/c-build" \
  --run "$OUT/c-run" --archive "$OUT/c-archive"

python3 -B "$S1/firstdot_c_evidence.py" --repo "$REPO" --action audit \
  --identity "$IDENTITY" --matrix "$MATRIX" --archive "$OUT/c-archive" \
  --output "$OUT/new-c-audit.json"

python3 -B "$S1/firstdot_library.py" --repo "$REPO" --action build \
  --identity "$IDENTITY" --matrix "$MATRIX" --c-archive "$OUT/c-archive" \
  --build "$OUT/c-build" --run "$OUT/c-run" --output "$OUT/qualified-library"
```

若公共源不相等，停止沿用该发布身份并检查原因；不能通过覆盖原冻结源或回填旧 PASS 让归档通过。

## 5. 回退与接续

| 目的 | 具体做法 |
| --- | --- |
| 恢复稳定默认 | 使用 [selected_gemv.h](../r2-select/public/selected_gemv.h) 的 `xs_gemv_<shape>` 并重新编译调用端，链接原 `libxs_gemv.a` |
| 使用稳定 RVV | 使用原显式 `xs_gemv_<shape>_rvv`，或首次包含稳定头文件前设置 `XS_GEMV_FORCE_RVV=1` 后重新编译 |
| 对照本轮某个函数 | 直接选相应 `firstdot_gemv_<shape>_<basic/reuse>_<vdot/rvv>`，同时遵守本轮输入和窗口边界 |
| 恢复完整旧版本 | 在独立工作区检出 `137b44befb041439a018a1079577cc000df1ee03`；保留共享分支历史与本轮证据 |

`XS_GEMV_FORCE_RVV` 不控制显式 `firstdot_gemv_*` 调用，修改该宏不会让已编译的 firstdot 调用自动回退。两个库使用不同公开符号；实际混合应用仍需检查其链接和使用影响。

后续优先级和具体待续条件见结果页与[开发路线](../../../docs/development-route-current.md)。本轮没有修改 RTL 或官方程序；完整应用、LLM、ASIC PPA、新机器安装与人工 ACK 均不由这些固定调用窗和库检查代替。
