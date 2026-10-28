# 8×32 最小 C8 软件包验收

**结果：PASS，可作为独立、显式选用的 C8 静态软件包使用。** 当前软件源码基点 c823a8786e052c6e26f6915563c42b6d730dd8e3，硬件保持 0f12df675378556670afd0dd2153f47fcb330610（O2＋H1＋DIV取消保持修复）。

本轮实现 `selected_gemv_c8.h`、完整单对象库构建、调用示例、当前身份验证器和主机测试。未切换旧四尺寸默认入口，未修改生产 RTL，未提交或上传 GitHub。执行者 @cc77-builder / Agent；本地包验收不是成员人工验收。

## 实际结果

| 验收项 | 本轮结果 |
| --- | --- |
| GNU 构建 | 固定 rv64gcv/lp64d/mno-relax，独立重建完整对象与原 C8 已验证对象全字节相同 |
| 完整对象 | 27,160 bytes；SHA256 f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3 |
| 静态库 | libxs_gemv_c8.a，仅一个完整 gemv.o；ar t/p、独立归档、确定性字节一致 |
| 符号与节 | 16 个原公共函数；单一16字节对齐.text；原对象无重定位；新增运行时别名/包装函数为0 |
| 别名与链接 | 缺省、0、1及宏展开为1共4模式；两个别名的 caller.o/linked.o 与直接调用逐字节相同 |
| 实际引用 | 每模式核对2个有序指针重定位、2个调用重定位；GNU可重定位链接后未解析符号为空 |
| 错误配置拒绝 | 17项集成负控：10种非法宏、4种错误别名、错误对象、错误库、缺失头文件 |
| 旧入口共存 | V1/V2分别与C8，两个包含顺序×旧新开关0/1，共16组，选择与版本保持 |
| 搬移 | SDK移到仓库外含空格目录；默认vdot及强制RVV示例均按文档flags编译/链接通过 |
| 主机检查 | 22项unittest通过，包括错误硬件/NEMU、混合配置、缺失数据集、伪造历史C资格及改哈希后错选择拒绝 |
| 构建门禁 | 额外3项Python优化模式负控通过：旧输出、仓库内输出、错误源码仍被拒绝 |
| 原始资格 | 当前0f身份及完整输入闭包复核；原33个矩阵进程＋3个C进程重审，48次叶函数锚点通过 |
| 新目标运行 | 0 EMU、0 NEMU；新示例运行、新最终ELF、新周期、面积/STA/功耗均为NOT_TESTED |

完整验收流水线：2026-10-27T21:36:30.342114+08:00 至 2026-10-27T21:38:56.981151+08:00，exit0；115份命令回执。新包首次集成验收即通过，原始输出与预期失败负控全部保留。

## 如何选用

使用 [构建与调用说明](README.md) 和 [完整 ABI 合同](CONTRACT.md)。头文件提供：

~~~c
#include "selected_gemv_c8.h"
xs_c8_gemv_8x32(packed_ax, slots);      /* configuration reuse vdot */
xs_c8_gemv_8x32_rvv(packed_ax, slots);  /* explicit reuse RVV */
~~~

`XS_C8_GEMV_FORCE_RVV=1` 将默认入口也选为 RVV；缺省或0为vdot。仅接受最终展开为字面量0或1，切换后重编相关翻译单元。

必须是 **VLEN恰好128**、VS已启用和已验证的RV64/lp64d平台。输入为16字节对齐的288字节有符号INT8 A[8][32]||x[32]；输出是16字节对齐的8×16字节槽，共128字节，输入输出不重叠。每槽低32位为结果、高96位清零。输出不能当作紧密的 int32_t[8]。原向量状态/CSR效果保持，详见合同。

完整库仍有16个函数及未调用vdot代码；显式RVV不等于纯RVV镜像或跨平台自动检测。旧 firstdot 包与四尺寸默认均保持。

## 性能含义与下一步

本轮证明新编译期入口在被测试的调用对象和可重定位链接中没有新增包装代码，并正确复用了已验证的同一完整对象。它不是新的性能测试，也不证明任意最终应用的布局或周期都相同。

此前第25条矩阵数据继续有效：8×32配置复用273.00 cycles，firstdot282.25，最快同场RVV299.00，加速比1.095238×；每格12正式样本。本轮没有把这些数值重新标成新实测。

最小包目标已完成。下一步若接入实际应用或产生新的最终ELF，先固定新调用布局/窗口合同，再做受影响路径的全128位正确性、差分拒错/恢复与重放；性能比较须用同路径firstdot/RVV对照。纯宏别名不需要新增wrapper。如果新增wrapper、dispatcher或CSR保护，需新的控制流检查，不能借用旧唯一jal/ret门禁。其他尺寸的4×8/16×64控制漂移仍可独立只读归因，4×13保留RVV。

## 证据与工程记录

- [机器可读记录](record.json)；[GNU与静态结果](evidence/report.json)；[当前资格绑定](evidence/qualification.json)。
- [固定输入](INPUTS.json)；[原文审计/构建工具](verify_c8_package.py)；[主机测试](test_c8_package.py)。
- [矩阵原文重审](evidence/matrix-raw-audit.json)；[C调用原文重审](evidence/c8-raw-audit.json)。
- [归档索引](evidence/archive-reference.json)；`evidence/commands/`保留115份命令及文本日志，ar提取的二进制stdout保留在完整外部归档。
- 原始输出：/home/riscv/riscv-lab/software-import-20261026/c8-package-01。
- 外部完整归档：/home/riscv/riscv-lab/software-import-20261026/reviews/c8-package-final-archive-01。
- 记录ID：C8-PACKAGE-DIVFIX0F-CLEAN02-20261027-01，统一版本档案第27条。

初版Makefile烟雾测试通过后，审查发现assert可能被Python优化模式跳过，改为显式退出并验证三项门禁；修正前后材料均保留。没有降低旧运行门禁、更新旧对象哈希或覆盖历史失败。
