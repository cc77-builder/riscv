# R5/G5：稳定 GEMV C 源入口与回退

操作 `20261024-LiZufan001-r5-stable-1221`，合同 `r5-selected-gemv-v1`。本页固定当前四种形状的普通 C 源入口、库构建和回退方式。机器可读选择及文件身份见 [STABLE_MANIFEST.json](STABLE_MANIFEST.json)，实际 GNU 验证见 [verify-03/result.json](evidence/stable-v1/verify-03/result.json)。

资格基点为已发布的 T17 提交 `666fc80edebd50f7b3d6fb13cf0eb24d526e02d9`；其真实硬件构建源码为 `34bae6d4acceac939f958199dae53c14bc1f6183`。两者分别表示证据交付版本和硬件源码身份，不能互换。硬件、参考模型、AM、配置及依赖的完整关联继续以 [T17 结果](../repro/CLEAN_RESULT.md)、[identity-02](../repro/evidence/clean-reproduction-v1/reports/identity-02.json) 为准。

## 1. 默认选择

调用端包含 [public/selected_gemv.h](public/selected_gemv.h)，使用下表左侧名称。它们是编译期宏别名，最终仍引用原有 `r4_gemv_*` 函数；不会增加 `xs_gemv_*` ELF 导出符号、包装函数或运行时分派。因此不能用别名拼写作为 `dlsym` 或其他语言的外部链接符号。

| C 源入口 | 默认：未设置开关或设为 0 | 强制 RVV：开关设为 1 |
| --- | --- | --- |
| `xs_gemv_4x8` | `r4_gemv_4x8_reuse_vdot` | `r4_gemv_4x8_reuse_rvv` |
| `xs_gemv_8x32` | `r4_gemv_8x32_reuse_vdot` | `r4_gemv_8x32_reuse_rvv` |
| `xs_gemv_16x64` | `r4_gemv_16x64_reuse_vdot` | `r4_gemv_16x64_reuse_rvv` |
| `xs_gemv_4x13` | `r4_gemv_4x13_reuse_rvv` | `r4_gemv_4x13_reuse_rvv` |

四个显式回退名称 `xs_gemv_4x8_rvv`、`xs_gemv_8x32_rvv`、`xs_gemv_16x64_rvv`、`xs_gemv_4x13_rvv` 始终对应各自的 S1/reuse RVV，不受开关影响。

`XS_GEMV_FORCE_RVV` 必须在首次包含头文件之前设置，并最终展开为字面量 `0` 或 `1`。`0` 表示上表获选组合，K13 仍选 RVV。更改开关后需要重新编译调用这些别名的翻译单元；仅改变链接参数不会修改已编译调用者，直接写原 `r4_*` 符号的代码也不受影响。本轮只承诺 C 源接口，未扩展 C++ 链接约定。

## 2. 内存与调用合同

完整约束继承 [ENTRY_CONTRACT.md](ENTRY_CONTRACT.md)、[普通 C 验证合同](C_API_CONTRACT.md) 和原 [public/gemv.h](public/gemv.h)。稳定名称没有改变这些约束：

- 尺寸仅为表中的四种；输入为有符号 INT8、行优先的 `A[M][K]`，紧接 `x[K]`，共 `M*K+K` 字节。
- 输入与输出不重叠，并使用已验证的 16 字节对齐存储；调用者提供足够的有效空间。
- 输出每行占 **16 字节槽**，低 32 位为有符号点积结果，高 96 位清零。不能用紧密的 `int32_t y[M]` 代替这些槽。
- `a0` 为输入地址，`a1` 为输出槽地址，无标量返回值。栈及整数被调用者保存寄存器保持；调用者保存寄存器、向量寄存器和向量配置会改变。
- 调用前须在 VS 已启用、VLEN=128 的匹配平台运行。函数建立自身需要的向量状态，不要求调用者预先清零向量寄存器；返回时 `VL=8`、`vtype=0`（e8/m1/tu/mu）、`vstart=0`、`vcsr=7`。

强制 RVV 只改变调用目标，不表示已取得任意 VLEN 或任意标准 RVV 平台的运行资格。库中仍包含全部 16 个合格函数，因而也不能把强制 RVV 描述为“整个镜像不含 vdot”。

最小调用示例（在匹配的 RV64 运行环境中调用）：

```c
#include "selected_gemv.h"

static int8_t packed_ax[4 * 8 + 8] __attribute__((aligned(16)));
static unsigned char output_slots[4][16] __attribute__((aligned(16)));

void run_4x8(void) {
    /* 先填写 A 的 32 字节及其后 x 的 8 字节，确保 VS 已启用。 */
    xs_gemv_4x8(packed_ax, output_slots);
}
```

## 3. 构建库并接入调用端

在 Linux/WSL 原生目录中的项目检出运行，使用 GNU RISC-V 工具链。`RESULT_ROOT` 使用仓库外的新输出目录；下列 shell 变量由使用者按环境设置，公共文件不依赖个人路径。

```bash
REPO=/path/to/riscv-checkout
RESULT_ROOT=/path/to/new-gemv-build

make -C "$REPO/team/optimizations/o2/r2-select/public" \
  OUT="$RESULT_ROOT/library" CROSS_COMPILE=riscv64-linux-gnu- -j1 all

riscv64-linux-gnu-gcc -march=rv64gcv -mabi=lp64d -mno-relax \
  -ffreestanding -O2 -I"$REPO/team/optimizations/o2/r2-select/public" \
  -c app.c -o "$RESULT_ROOT/app.o"

riscv64-linux-gnu-ld -r --no-relax "$RESULT_ROOT/app.o" \
  "$RESULT_ROOT/library/libxs_gemv.a" -o "$RESULT_ROOT/app-gemv.o"
```

`app.c` 是使用上面接口的调用端。最后一步生成可重定位的集成对象，完整应用仍须使用其启动代码、AM/平台链接脚本及运行合同。不要同时把原 `gemv.S` 和 `libxs_gemv.a` 作为两套定义重复链接。当前库构建固定 `rv64gcv/lp64d/-mno-relax`；这些设置不会自动传播到其他应用的编译和最终链接。

需要整个调用端使用 RVV 时，在编译 `app.c` 时增加 `-DXS_GEMV_FORCE_RVV=1`，或在首次包含头文件之前定义该宏。只回退一处时，直接使用对应 `xs_gemv_<shape>_rvv`。

## 4. 真实运行、复现和性能依据

硬件/依赖准备、实际构建、整核拒错恢复、普通 C 运行和串行性能矩阵均使用 [T17 干净复现入口](../repro/CLEAN_REPRODUCE.md)。历史 [ENTRY_README.md](ENTRY_README.md) 保留 R4 固定批次的生成与实验入口；其中的旧硬件身份不应替代 T17 新构建身份。

当前选择依据为 [T17 最终矩阵原文审计](../repro/evidence/clean-reproduction-v1/reports/matrix-archive-audit-03.json) 中每候选 12 个正式完整调用窗；比较包括同一调用路径的全部合格 RVV，最快者均为 S1/reuse：

| 形状 | S1/reuse vdot 平均周期 | 最快合格 RVV 平均周期 | 当前默认 |
| --- | ---: | ---: | --- |
| 4×8 | 169.75 | 187.50 | vdot，周期少 9.4667% |
| 8×32 | 292.50 | 300.75 | vdot，周期少 2.7431% |
| 16×64 | 717.25 | 779.50 | vdot，周期少 7.9859% |
| 4×13 | 219.75 | 187.00 | RVV |

这里的周期范围是固定 GEMV `endtoend-with-c-abi-call` 窗口，不是完整应用或 LLM 的性能。R5 没有新计时结果。任意新应用、调用计划、链接布局或硬件变化都需按影响验证；特别是 8×32 仅有 8.25 周期余量，应先与走同一新路径的最快合格 RVV 配对。

## 5. 本轮 GNU 验证与验收范围

可在已取得本提交文件的 Linux/WSL 检出中复现：

```bash
python3 -B "$REPO/team/optimizations/o2/r2-select/verify_stable.py" \
  --repo "$REPO" --output /path/to/new-stable-verification
```

输出目录必须不存在并位于源码目录外，路径不含空白；输出原样保留命令、退出码、stdout/stderr、实际 caller、库和链接对象。验证器最多使用四个已有可用 CPU，两个模式构建并发，库构建为 `-j1`。它可以核验完整检出或清单覆盖的逐文件哈希快照；不会凭快照路径推断 Git HEAD。当前验收使用 GNU GCC 11.4.0、Binutils 2.38、Make 4.3。

最终 [verify-03](evidence/stable-v1/verify-03/result.json) 为 `R5_STABLE_SOURCE_ALIAS_BUILD_PASS`：

1. 清单固定原汇编/头文件、新入口与构建文件，以及 T17 identity、最终矩阵/C 审计和 C02 manifest；从性能报告重新推导默认选择，不只相信新清单里的目标名。
2. 新 `gemv.o` 的全部 28,152 字节与 C02 已验证的 `gemv-reference.o` 相同，SHA256 均为 `ecb24b6cde147c5b36f0caf8e5ec2b17451d293de14e2b4e223b14141d3e1aa7`。该比较覆盖节成员、重定位、符号和 ELF 属性；静态库实际成员也与此对象一致。
3. 未设置开关、显式 0、显式 1 三种模式各覆盖全部八个别名。每种模式的别名 caller 与对应显式原符号 caller，其完整 `caller.o` 和完整 `ld -r` 产物逐字节相同；链接无未解析符号。默认/0 为七个唯一目标，强制 RVV 为四个。
4. `2`、`-1`、未定义的 `true`、`0+1`、`true && true`、`0||1`、`00` 七种非法设置均被真实编译拒绝。若已有宏（如 `<stdbool.h>` 的 `true`）最终展开为字面量 1，则属于合法输入。

新增 EMU/NEMU 执行均为 **0**。这里证明入口映射、库构建和目标对象等价；底层函数的实际运行资格引用 T17，不声称 T17 当时使用了这个后来新增的头文件。先前验证版本及审查修正见 [证据说明](evidence/stable-v1/README.md)，实际路径与宿主回执见 [运行定位](evidence/stable-v1/runtime-locations.json)。

## 6. 回退与后续接续

| 目的 | 操作入口 | 边界 |
| --- | --- | --- |
| 当前 C 调用退回 RVV | 首次 include 前设 `XS_GEMV_FORCE_RVV=1` 并重新编译；或使用四个显式 RVV 别名 | 库与硬件平台合同保持，开关不改变已经编译的调用者 |
| 恢复 S0 实验候选 | 使用 [R4 冻结生成入口](ENTRY_README.md) 按形状生成 S0，使用新的独立构建身份 | S0/S1 导出同名函数，只选一套链接；当前整套 S1 普通 C 库的资格不能转给 S0 替代库 |
| 恢复 R2 原始实验镜像 | 使用 [原镜像 export/verify/resolve](README.md) | 导出完整原 ELF/BIN，保持原运行计划；不是 ordinary C 的单函数替换 |
| 回到本入口加入前的版本 | 在独立工作区检出资格基点 `666fc80edebd50f7b3d6fb13cf0eb24d526e02d9` | 保留当前分支历史及证据，不覆盖共享工作树 |

R5/G5 在本页所述四形状、同硬件配置和 C 源使用范围内闭合。它没有改变 RTL、官方权威程序或冻结实验合同，也没有新增 ASIC PPA、全赛题验收、新机器安装或人工 ACK。后续优化以这个可用入口为保底；只有明确的新瓶颈假设才开展下一试验，完整应用收益仍需真实应用测量。
