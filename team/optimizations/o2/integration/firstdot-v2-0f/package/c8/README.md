# 独立 C8 8×32 最小软件包

C8 提供两个编译期别名和一个完整对象静态库，用于显式选用已验证的配置复用 8×32 实现。使用前阅读 [调用合同](CONTRACT.md)。总体方案见 [设计评审](../C8_DESIGN.md)，实际验收结果由本目录验证工具生成；本 README 不把构建成功当作新目标运行通过。

## 构建

从仓库根设置下面三个路径；`SOURCE_DIR` 仅接受已限定 SHA 的公共 `gemv.S/h`。`OUT` 必须是源码、仓库之外的全新目录，存在时拒绝，失败目录也保留。

```bash
C8="$PWD/team/optimizations/o2/integration/firstdot-v2-0f/package/c8"
SOURCE_DIR="$PWD/team/optimizations/o2/integration/firstdot-v2-0f/continuation/config-reuse-c8-v2/public"
OUT="/absolute/path/outside-repository/c8-sdk-new"
make -f "$C8/public/Makefile" SOURCE_DIR="$SOURCE_DIR" OUT="$OUT"   CROSS_COMPILE=/usr/bin/riscv64-linux-gnu- -j1
```

固定汇编 flags 为 `-march=rv64gcv -mabi=lp64d -mno-relax -c`，不能通过 CFLAGS 改变它们。工具链必须与本次验证身份一致；若完整对象不同，构建停止，不更新旧哈希迁就新工具。Makefile 接口使用常规无空格 GNU Make 输入路径；生成的 SDK 可搬到含空格路径后通过下面的带引号命令使用。

产物为 `gemv.o`、`libxs_gemv_c8.a`、`include/selected_gemv_c8.h`、`include/config_reuse_gemv.h`、`CONTRACT.md` 和 `example.c`。验证器另外记录包 manifest、输入身份及检查结果。日常提交保存源与必要证据，构建产物留在外部输出目录。

## 编译与可重定位链接示例

完整 SDK 可整体复制至脱离仓库的新目录。下面的 `SDK` 指向该目录；可从任意工作目录调用，不需要仓库 include 路径。

```bash
SDK="/absolute/path/moved-c8-sdk"
BUILD="/absolute/path/fresh-example-output"
mkdir "$BUILD"
riscv64-linux-gnu-gcc -std=c11 -O2 -ffreestanding -fno-builtin   -fno-pic -fno-pie -fno-stack-protector -march=rv64gcv -mabi=lp64d   -mno-relax -I"$SDK/include" -c "$SDK/example.c" -o "$BUILD/example.o"
riscv64-linux-gnu-ld -r --no-relax "$BUILD/example.o"   "$SDK/libxs_gemv_c8.a" -o "$BUILD/example-linked.o"
riscv64-linux-gnu-nm -u "$BUILD/example-linked.o"
```

`nm -u` 应为空。`ld -r` 仅生成可重定位对象，不是可启动镜像；编译成功和没有未解析符号也不能代替完整验证器。示例不执行，不测周期；平台启动、VS 启用和最终链接由真实应用负责。

## 显式选用与回退

```c
#include "selected_gemv_c8.h"
/* packed_ax: 16-byte aligned 288-byte A||x.
 * slots: 16-byte aligned 128-byte output, disjoint from input. */
xs_c8_gemv_8x32(packed_ax, slots);     /* default: reuse vdot */
xs_c8_gemv_8x32_rvv(packed_ax, slots); /* explicit reuse RVV */
```

在第一次 include 前定义 `XS_C8_GEMV_FORCE_RVV 1`，或编译时传 `-DXS_C8_GEMV_FORCE_RVV=1`，使默认别名也使用 RVV。缺省与 0 使用 vdot；其他值编译失败。切换后完整重编相关翻译单元。旧 firstdot 宏、头及工程默认不改变；若同程序调用旧入口，还需链接匹配的旧库。

## 验证

`verify_c8_package.py` 接收显式当前身份与冻结矩阵/C8 证据输入，在新输出目录完成 GNU、负控和搬移检查。调用参数与验收结果见该工具 `--help` 及本轮 RESULT/evidence；`test_c8_package.py` 提供检查器主机测试。新示例、最终 ELF、性能及 PPA 均不因静态检查自动获得资格。
