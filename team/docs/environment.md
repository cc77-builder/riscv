# 已验证的环境与安装方法

2026-10-09 在个人电脑完成验证：Windows + WSL2，Ubuntu 22.04.5 x86_64，Ryzen 7 7840H（8 核 / 16 线程），物理内存约 27.7 GiB。WSL 内存上限 20 GB、swap 16 GB。本记录描述实际已验证环境，不代表所有电脑必须使用相同内存或用户名。

## WSL 内存

在 Windows 的 `%UserProfile%\.wslconfig` 中设置：

```ini
[wsl2]
memory=20GB
swap=16GB
```

保存正在进行的 WSL 工作后，在 PowerShell 执行 `wsl --shutdown`，重新进入 Ubuntu，用 `free -h` 核对。原机器 swap 文件放在 `D:\WSL\wsl-swap.vhdx`，新成员无需照搬该路径。较小内存的机器相应降低 JVM 堆和构建并行度，不能同时把 JVM 堆和构建进程占满可用内存。

## 固定源码

| 组件 | 已验证提交 |
| --- | --- |
| xs-env | `b0b506481e839a5df8a580e76f5aa246dc60fe7c` |
| 香山硬件基线 | `16ae9ddcda54fc9a2fddffad73174cf793ac7814` |
| NEMU | `a48a11f208ff81ad765591d83271d1b339fb3861` |
| nexus-am | `086a238062fdfb3281b745a537b361983d0154b5` |
| DRAMsim3 | `1d2a9bf6da8e050d975ef2669c42faa93943f489` |
| DiffTest | `62e4540c03c03aa947bdb67f4b6bf66f1a29c5d0` |
| yunsuan | `cadd3c2f43096e253d61296b33ac697be8354e29` |

在团队仓库运行 `bash team/scripts/prepare-dependencies.sh`：固定检出 xs-env，仅初始化配套 NEMU、nexus-am、DRAMsim3 及其递归子模块，然后锁定 NEMU 额外依赖。团队仓库自己的香山子模块通过 `git clone --recurse-submodules` 获取。脚本遇到已有依赖版本不同或已跟踪文件修改会停止，不丢弃队友修改。

NEMU 额外依赖的实际提交见 [锁定脚本](../scripts/lock-nemu-extra-deps.sh)。SimPoint 是 NEMU 已记录的子模块，通过递归初始化固定；其他额外下载仓库不能依赖当天默认分支，构建前必须执行锁定脚本。

## 已验证工具

| 工具 | 版本 |
| --- | --- |
| Oracle GraalVM JDK / javac | 21.0.12 |
| LLVM / Clang | 19.1.7 |
| Mill 项目版本 | 0.12.3 |
| Scala / Chisel | 2.13.15 / 6.6.0，由项目解析 |
| firtool | 1.62.1，由本次项目依赖解析 |
| Verilator | 5.052，提交 `ea338be98e1e838d3518809ce8899f85a009963c` |
| RISC-V GCC | 11.4.0，`riscv64-linux-gnu-` 前缀 |
| GNU binutils | 2.38 |
| 宿主 GCC / G++ | 11.4.0 |
| Make / CMake / Ninja | 4.3 / 3.22.1 / 1.10.1 |
| Python / GTKWave | 3.10.12 / 3.3.104 |

完整工具输出见 [tool-versions.txt](../evidence/stage1-20261009/tool-versions.txt)。Ubuntu 软件包版本清单提供历史来源信息，不建议无差别恢复整台主机的软件包。

## 新机器安装

先完成配套源码检出，然后加载路径。在团队仓库根目录执行：

```bash
source team/scripts/activate.sh
sudo bash "$TEAM_XS_ENV_ROOT/setup-tools.sh" --target base
sudo bash "$TEAM_XS_ENV_ROOT/setup-tools.sh" --target llvm
sudo bash "$TEAM_XS_ENV_ROOT/setup-tools.sh" --target mill
sudo apt-get install -y cmake ninja-build gtkwave
```

以上安装入口来自固定 xs-env 的 [setup-tools.sh](https://github.com/OpenXiangShan/xs-env/blob/b0b506481e839a5df8a580e76f5aa246dc60fe7c/setup-tools.sh)。软件源提供的补丁版本可能变化，因此安装后必须运行团队环境检查。

JDK 原安装脚本使用 Oracle `21/latest` URL；它会随时间变化，不能据此保证重装仍是 21.0.12。本队提供 [固定 GraalVM 安装脚本](../scripts/install-graalvm.sh)，使用已核对可下载的官方 21.0.12 Linux x64 归档和官方 SHA-256，安装到用户目录，不需要 sudo：

```bash
export JAVA_HOME="$HOME/.local/share/graalvm-jdk-21.0.12"
bash team/scripts/install-graalvm.sh
source team/scripts/activate.sh
```

新终端中继续导出相同的 `JAVA_HOME`；已安装原本机 `/opt/graalvm-jdk-21` 的成员可使用默认路径，无需重装。脚本遇到已有 JDK 版本不同会停止，不能覆盖现有安装。新版本需要单独验证后更新团队记录。安装方法参考 [Oracle GraalVM 安装说明](https://docs.oracle.com/en/graalvm/jdk/21/docs/getting-started/installation-linux/)；固定归档为 [21.0.12 Linux x64](https://download.oracle.com/graalvm/21/archive/graalvm-jdk-21.0.12_linux-x64_bin.tar.gz)，校验来源为 [官方 SHA-256](https://download.oracle.com/graalvm/21/archive/graalvm-jdk-21.0.12_linux-x64_bin.tar.gz.sha256)。

Verilator 在用户目录源码编译，避免官方脚本默认 `-j$(nproc)` 导致个人电脑资源不足。先安装依赖，再使用已安装的 Clang：

```bash
sudo apt-get install -y help2man perl autoconf flex bison libgoogle-perftools-dev \
  libjemalloc-dev numactl perl-doc zlib1g-dev liblz4-dev libfl2 libfl-dev
mkdir -p "$HOME/riscv-tools"
git clone https://github.com/verilator/verilator.git "$HOME/riscv-tools/verilator"
cd "$HOME/riscv-tools/verilator"
git checkout ea338be98e1e838d3518809ce8899f85a009963c
unset VERILATOR_ROOT
autoconf
./configure CC=/usr/local/llvm/bin/clang CXX=/usr/local/llvm/bin/clang++ LINK=/usr/local/llvm/bin/clang++
make -j2
sudo make install
```

回到团队仓库根目录：

```bash
source team/scripts/activate.sh
bash team/scripts/check-environment.sh
```

此检查核对配套源码提交、香山递归子模块与关键工具版本；香山 `HEAD` 可以包含本队新增文档提交，但必须保留硬件基线祖先。检查通过不等于新硬件改动已通过仿真。不要手动升级全局 Scala；项目 Mill 会读取仓库 `.mill-version`，启动器来源版本不等于项目版本。

## 使用现有环境

现有主机只需从 `/home/riscv/riscv-lab/xs-env/XiangShan` 运行脚本。`activate.sh` 会设置当前团队仓库为 `NOOP_HOME`，按 `TEAM_XS_ENV_ROOT` 指定 NEMU 和 AM，设置 `LINUX_GNU_TOOLCHAIN=1`。AM 默认不会自动启用向量 ISA，因此构建 workload 仍需显式设置 `MARCH=rv64gcv`。
