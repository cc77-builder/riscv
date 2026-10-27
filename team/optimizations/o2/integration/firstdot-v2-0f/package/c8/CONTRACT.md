# C8 8×32 软件包合同

合同版本：`current-c8-package-v1`。本包显式选用配置复用 8×32 入口，不改变已有 firstdot 入口或工程默认。别名是预处理宏；库保留原始完整对象。没有运行时分派、参数检查、CSR 保护或 CPU 探测。

## 入口与选择

| 入口 | 目标 |
| --- | --- |
| `xs_c8_gemv_8x32`，开关缺省或 0 | `config_reuse_gemv_8x32_reuse_vdot` |
| `xs_c8_gemv_8x32`，`XS_C8_GEMV_FORCE_RVV=1` | `config_reuse_gemv_8x32_reuse_rvv` |
| `xs_c8_gemv_8x32_rvv` | 始终 `config_reuse_gemv_8x32_reuse_rvv` |

`XS_C8_GEMV_FORCE_RVV` 最终展开只能是字面量 0 或 1；空值、表达式和未知标识不受支持，编译时拒绝。独立 guard 为 `XS_C8_SELECTED_GEMV_H`，API 版本 `XS_C8_GEMV_API_VERSION=1`。`XS_C8_GEMV_PROFILE` 是静态合同标签，不能检测 CPU 能力或不同翻译单元的旧对象。改变宏或版本后，完整重编所有相关翻译单元。

旧 `XS_GEMV_FORCE_RVV` 和 `xs_gemv_*` 不参与本包选择。包内不重新定义旧 guard、版本、别名。应用按所选版本使用匹配的旧库；C8 库不能代替 firstdot 库。

## 普通 C ABI

函数原型为 `void entry(const int8_t *packed_ax, void *output_slots)`。已验证运行环境为当前香山昆明湖 V2/Nexus-AM 裸机 RV64、lp64d，**VLEN 恰好 128（vlenb=16）**，VS 已启用。默认路径要求该硬件实现项目的自定义 vdot 编码。编译器支持 RVV、misa.V 或本包标签均不足以证明自定义指令存在。无 Linux 用户态运行资格。

- 输入：有符号 INT8 行优先 `A[8][32]`，紧接 `x[32]`，共 288 字节。
- 输出：8 个 16 字节槽，共 128 字节。每槽低 32 位为 INT32 点积结果，高 96 位清零。不得改为紧密 `int32_t[8]`。
- 两块缓冲区各自 16 字节对齐、有效且不重叠；输入不会被修改。调用者负责生命周期、数据打包及平台初始化。
- 沿用原 RV64 C ABI：栈及被调用者保存寄存器约束不变；向量寄存器和允许的调用者保存状态会改变。
- 返回状态为 `vl=8`、`vtype=0`（e8/m1/tu/mu）、`vstart=0`、`vcsr=7`，不保留原向量配置。

底层 `vs1r.v` 存整个向量寄存器，而输出行步长固定为 16。VLEN 256 会越过槽边界；不能把该包当作 VLEN≥128 通用实现。强制 RVV 只改变调用目标，完整库仍包含未使用的 vdot 函数，也不授予任意 RVV 平台运行资格。

## 构建与资格边界

独立 GNU 汇编参数固定为 `-march=rv64gcv -mabi=lp64d -mno-relax -c`。完整 `gemv.o` 为 27,160 字节，SHA256 为 `f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3`。确定性 `libxs_gemv_c8.a` 只含一个 `gemv.o`，保留 16 个函数、原节和重定位；`config_reuse_gemv.h` 从合格 `gemv.h` 原字节复制，仅改产物文件名。

当前资格链绑定软件源基点 `c823a8786e052c6e26f6915563c42b6d730dd8e3`、选中 RTL `0f12df675378556670afd0dd2153f47fcb330610` 和 clean-02 配套身份。完整输入、工具身份及验收结果以 `INPUTS.json`、验证器输出和版本数据档案记录为准。构建成功本身不代表资格链通过。

静态验收覆盖完整对象、单库成员、缺省/0/1 两别名的 GNU 调用对象和可重定位链接等价、实际符号解析、错误配置拒绝及 SDK 搬移。它不产生新的最终 ELF、目标运行、周期、面积或 STA 数据；`example.c` 仅为编译/链接示例。只有上述完整等价及身份检查通过，才可明确复用原矩阵和 C8 普通调用证据，不能改写旧记录或当成新应用验证。

新增 wrapper、分派、CSR 保存、裁剪/混合对象、编译参数或最终布局变化，以及新实际应用，需要按影响补独立目标运行和必要的公平性能比较。叶函数字节相等不能单独授予新最终映像的功能或周期资格。

## 回退

本包内设 `XS_C8_GEMV_FORCE_RVV=1` 或显式调用 `xs_c8_gemv_8x32_rvv` 后完整重编。撤销 C8 选用时，恢复原 firstdot 头和匹配库并完整重编。其余尺寸未提供 C8 稳定别名；不要将本包的 8×32 结论推广到其他形状。
