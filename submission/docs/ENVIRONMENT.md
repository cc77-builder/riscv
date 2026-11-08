# 环境与依赖

硬件构建使用 Linux/WSL 原生文件系统。固定源码见仓库根 `.gitmodules`、`team/versions.env` 及本目录上级的 `FINAL_VERSION.json`；实际 checkout 保留十个直接 gitlink，递归依赖由这些固定提交继续锁定。

| 工具 | 原验证环境 |
| --- | --- |
| GraalVM JDK | 21.0.12 |
| Mill | 0.12.3 |
| firtool | 1.62.1 |
| Verilator | 5.052 |
| RISC-V GNU GCC | 11.4.0，riscv64-linux-gnu- 前缀 |
| Python | 3.10 及以上；原环境 3.10.12 |

从完整 Git 检出恢复固定子模块：`git submodule update --init --recursive`。设置独立的 `TEAM_XS_ENV_ROOT` 后运行 `bash team/scripts/prepare-dependencies.sh`，再配置 `JAVA_HOME`、加载 `team/scripts/activate.sh` 并执行环境检查。依赖准备可能下载固定来源；代码包不包括完整离线工具链和下载缓存。

新建 NEMU vdot reference 使用 `team/scripts/prepare-nemu-vdot.sh reference`，需要系统开发依赖和编译器；补丁、配置及来源由原检查器核对。不要以未扩展的 NEMU 替代 vdot reference。

原默认资源为 MinimalConfig、单核、单仿真线程、JVM 12 GiB、构建并行度 2。构建/运行应使用新输出目录，保留失败日志。Windows 查看副本没有 `.git` 和子模块内部文件，硬件构建应使用实际 WSL Git 仓库或以后发布的完整递归检出。
