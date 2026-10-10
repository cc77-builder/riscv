# 仓库脚本实际验证（2026-10-10）

在现有 WSL Ubuntu 22.04 环境中，使用新增到本仓库的 `team/scripts` 和 `team/workloads/hello-vadd` 运行。配套依赖恢复检查、关键源码/工具版本检查和测试程序编译通过；执行真实香山 + NEMU DiffTest，3 个用例 / 24 个元素全部 PASS，GOOD TRAP，退出码 0。

本次复用阶段一已经构建的 MinimalConfig 仿真器与 NEMU 参考库，确认硬件源码、构建定义与基线无差异；没有再次执行耗时的 RTL/C++ 完整重建，也没有在全新 Ubuntu 上重复安装所有工具。GraalVM 安装脚本检查了本机已有正确版本的复用分支，固定官方归档 URL 和 SHA-256 已核对。

重新编译的测试源码位于当前仓库的 `team/workloads/hello-vadd`，运行时不生成波形，保留协同验证和公共 flash。

- `dependencies-check.log`：配套仓库与 NEMU 额外依赖固定版本检查。
- `environment-check.log`：源码及关键工具的实际版本和通过标识。
- `run-summary.log`：从本次完整运行输出提取的真实摘要，去除终端颜色控制符。
- `run.status` / `workload.status`：脚本退出码和结束时间。
- `boot-flash-disassembly.txt`：公共启动代码的实际反汇编。
- `workload.sha256` / `simulators.sha256`：本次使用的二进制校验和；文件本身保留在本机。

本次计数 `instrCnt=16505`、`cycleCnt=42727`、IPC=0.386290，宿主耗时 166.605 秒。它与昨天运行是不同记录：WSL IP 发生变化，UART 打印内容长度不同；本次也关闭了运行时波形。两次完整程序的统计不能作为 vadd 性能提升的证据。

完整运行输出位于本机 `team/out/verification-20261010/emulator-output.log`。此目录的 `SHA256SUMS` 仅校验本目录已归档的小型证据。
