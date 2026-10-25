# R5/G5 V2：firstdot 稳定 GEMV 源入口

V2 将已合格的 firstdot 普通 C 函数提供为四形状 `xs_gemv_*` 编译期入口，
并一次构建可独立搬移的静态库和头文件。三个整块形状默认使用 firstdot
vdot，4×13 保留 RVV；全部形状均可显式回退到 RVV。
原 [V1 入口](STABLE.md)的汇编、头文件、库构建、清单和验证器保持原字节，
现有 V1 调用者不会因为仓库新增 V2 自动改变。

合同：[FIRSTDOT_STABLE_CONTRACT.md](FIRSTDOT_STABLE_CONTRACT.md)。
机器可读选择与身份：[FIRSTDOT_STABLE_MANIFEST.json](FIRSTDOT_STABLE_MANIFEST.json)。
本轮构建与原文复核结果：[结果入口](evidence/stable-firstdot-v2/README.md)。

## 1. 选用或回退

新包中的 `include/selected_gemv.h` 定义 `XS_GEMV_STABLE_API_VERSION=2`。
这些名称是 C 宏别名，最终引用原有 `firstdot_gemv_*` 符号；没有额外
包装函数、`xs_gemv_*` ELF 导出符号或运行时分派。

| C 源入口 | 默认或 `XS_GEMV_FORCE_RVV=0` | `XS_GEMV_FORCE_RVV=1` |
| --- | --- | --- |
| `xs_gemv_4x8` | `firstdot_gemv_4x8_reuse_vdot` | `firstdot_gemv_4x8_reuse_rvv` |
| `xs_gemv_8x32` | `firstdot_gemv_8x32_reuse_vdot` | `firstdot_gemv_8x32_reuse_rvv` |
| `xs_gemv_16x64` | `firstdot_gemv_16x64_reuse_vdot` | `firstdot_gemv_16x64_reuse_rvv` |
| `xs_gemv_4x13` | `firstdot_gemv_4x13_reuse_rvv` | `firstdot_gemv_4x13_reuse_rvv` |

四个 `xs_gemv_<shape>_rvv` 名称始终映射本表对应的 firstdot/reuse/RVV，
不受开关影响。开关须在首次 include 前设置，最终展开为字面量0或1。
更改开关或V1/V2版本后，需要重新编译调用这些别名的全部翻译单元；
仅更换链接参数不会改变已有调用者，直接写 `r4_*` 或 `firstdot_*` 的
代码也不受开关影响。

| 迁移目的 | include 根与库 |
| --- | --- |
| 使用 V2 | 本页构建产物的 `package/include` 与 `libxs_gemv_firstdot.a` |
| V2 调用全部回退 RVV | 编译调用端时加 `-DXS_GEMV_FORCE_RVV=1`，库保持 V2 |
| V2 单处回退 RVV | 改用对应 `xs_gemv_<shape>_rvv` 并重新编译 |
| 恢复 V1 | 按 [原稳定使用说明](STABLE.md)选择旧 `public` include 根和 `libxs_gemv.a`，完整重编译调用端 |

一个应用应统一选择其需要的版本，避免意外混用头和库。若同一翻译单元
先包含V1再包含V2，V2会明确报错；先包含V2再包含冻结V1时，共同guard
跳过旧头、保持V2。后者是防止降级，并非“双向混用均拒绝”。这个机制
不能发现跨翻译单元的混搭，建议在调用端保留下面的版本静态断言。

## 2. 构建可独立搬移的包

在 Linux/WSL 原生检出中，使用已验证的 GNU RISC-V 工具链：

```bash
REPO=/path/to/riscv-checkout
OUT=/path/to/new-gemv-v2

make -C "$REPO/team/optimizations/o2/r2-select/public/firstdot" \
  OUT="$OUT/package" CROSS_COMPILE=riscv64-linux-gnu- -j1 all

riscv64-linux-gnu-gcc -std=c11 -march=rv64gcv -mabi=lp64d -mno-relax \
  -ffreestanding -O2 -I"$OUT/package/include" \
  -c app.c -o "$OUT/app.o"

riscv64-linux-gnu-ld -r --no-relax "$OUT/app.o" \
  "$OUT/package/libxs_gemv_firstdot.a" -o "$OUT/app-gemv.o"
riscv64-linux-gnu-nm -u "$OUT/app-gemv.o"
```

`app.c` 是自己的调用端。最后一步生成可重定位集成对象；完整应用仍须
自己的启动代码、平台链接脚本和实际运行验证。`ld -r`即使存在未解析
符号也可能退出0，因此还需检查未解析符号是否全部符合应用预期。

对外搬移只需要以下三件产物，可直接复制整个 `package/include` 和 `.a`：

- `libxs_gemv_firstdot.a`
- `include/selected_gemv.h`
- `include/firstdot_gemv.h`

生成包的头文件相互使用本地相对名称，不依赖仓库的目录结构。
**调用端应包含构建产物的 `package/include`，不能直接把新增的源码
`public/firstdot` 目录当作完整SDK include根。** 后者的第二个头由Make
从已冻结的firstdot公共头逐字节复制到产物目录。

库内恰好一个 `gemv.o`，包含全部16个firstdot函数。完整对象应为27,416
字节，SHA256：

```text
b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af
```

不要同时把定义相同firstdot符号的原汇编/对象和该库作为两套定义链接。
强制RVV不会删除库中未使用的vdot函数，也不使这个包自动获得任意标准
RVV平台的运行资格。

## 3. 调用合同

本版本继承 [firstdot普通C合同](../r2-vector-accum/FIRSTDOT_C_CONTRACT.md)
及原C ABI。仅提供四形状、普通C链接；不增加C++链接约定。

| 项目 | 要求 |
| --- | --- |
| 输入 | 有符号INT8，行优先矩阵 `A[M][K]`，紧接 `x[K]`，共 `M*K+K` 字节 |
| 输出 | 每行16字节槽，低32位为有符号点积结果，高96位清零，共 `M*16` 字节 |
| 内存 | 输入输出各16字节对齐、互不重叠，容量完整有效；不能用紧密 `int32_t y[M]` 代替输出槽 |
| 参数 | `a0`为输入地址，`a1`为输出槽地址，无标量返回值 |
| 平台 | 固定T17的RV64/lp64d/VLEN128平台，VS已启用；vdot入口需要项目自定义指令 |
| 状态 | 栈及整数被调用者保存寄存器保持；调用者保存寄存器、向量寄存器和向量配置会改变 |
| 返回CSR | `VL=8`、`vtype=0`、`vstart=0`、`vcsr=7` |

最小调用如下，[完整可编译示例](public/firstdot/example.c)已由本轮GNU
构建验证；它自身没有新增整核运行或性能测量。

```c
#include <stdint.h>
#include "selected_gemv.h"
_Static_assert(XS_GEMV_STABLE_API_VERSION == 2, "GEMV V2 required");

struct slot { int32_t value; uint32_t high[3]; };
_Static_assert(sizeof(struct slot) == 16, "16-byte output slot");
static _Alignas(16) int8_t packed_ax[8 * 32 + 32];
static _Alignas(16) struct slot output_slots[8];

void run_8x32(void) {
    /* 先填写A和x，确保运行平台VS已启用。 */
    xs_gemv_8x32(packed_ax, output_slots);
}
```

没有隐藏打包、量化、分配或结果重排。调用方负责缓冲区内容、生命周期
和实际业务的准备/整理成本。

## 4. 为什么选择firstdot

采用依据来自已完成的 [firstdot完整矩阵与普通C实跑](../r2-vector-accum/FIRSTDOT_RESULT.md)。
每格是三数据集×四正式repeat，共12样本；这些数值属于原固定
`endtoend-with-c-abi-call`窗口，本轮只重新审计原文，没有新增计时。

| 形状 | V1 S1/reuse vdot | V2选用函数的历史均值 | 同轮最快合格RVV | V2包内RVV回退 | 选择 |
| --- | ---: | ---: | ---: | ---: | --- |
| 4×8 | 169.75 | 157.75 | 187.50 | 187.75 | firstdot vdot |
| 8×32 | 292.50 | 282.25 | 300.75 | 300.75 | firstdot vdot |
| 16×64 | 717.25 | 707.00 | 778.75 | 778.75 | firstdot vdot |
| 4×13 | 219.75 | 187.00 | 187.00 | 187.00 | firstdot RVV；V1默认也为RVV187.00 |

三个整块firstdot/vdot相对同轮S1分别少7.0692%、3.5043%、1.4291%周期；
相对同轮最快合格RVV分别少15.8667%、6.1513%、9.2135%。4×8公平分母
保留187.50，不能用包内较慢的187.75夸大收益。K13两侧RVV聚合并列，
不代表每个窗口相同。本轮选择单一firstdot对象，保留整个V1作为回退。

这些是软件在固定T17硬件上的历史调用窗结果。新应用、最终链接布局、
调用序列、数据打包与完整LLM流程仍须按实际影响验证，不保证任意调用者
迁移后的百分比。没有新RTL、芯片频率、功耗或ASIC面积/时序结论。

## 5. 重建与验收

在含冻结历史Git对象及原证据的完整检出中运行：

```bash
python3 -B "$REPO/team/optimizations/o2/r2-select/verify_firstdot_stable.py" \
  --repo "$REPO" --output /path/to/new-v2-verification
```

输出必须是源码外尚不存在的新目录；失败目录原样保留。验证器最多使用
四个可用CPU，GNU配置检查最多两个worker，各库构建为 `-j1`。
完整原文审计复用冻结firstdot判定，同一次C审计内部的矩阵结果仅通过
私有适配器旁路记录，不更改任何原判定或冻结源码，也不重复运行矩阵。

验收包括：从原始证据推导四形状选择、完整对象与库成员等价、三种宏模式
下8别名的完整caller/link对象相等、非法设置与真实头顺序检查、重哈希后
的错选择/错别名/错对象拒绝、错库未解析检测，以及独立搬移SDK后的实际
编译链接。原V1验证器也在新目录实跑，以确认回退仍成立。

底层函数运行资格引用firstdot的33次性能进程及3次普通C进程；本轮新增
EMU/NEMU均为0。V2交付的是源入口、可重建包和明确回退，不把可重定位
链接相等扩大为新的最终ELF运行、任意应用性能或成员人工验收。
