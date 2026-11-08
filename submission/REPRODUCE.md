# 复现说明

以下命令均在仓库根目录执行。`submission/reproduce.sh` 是统一入口，内部调用原有的构建和检查脚本。

## 交付文件与宿主检查

```bash
bash submission/reproduce.sh check
bash submission/reproduce.sh logs-check
```

`check` 校验交付文件清单、参考模型、确定性测试向量、指令编码和静态接入；`logs-check` 逐项校验全部归档日志及其元数据。两者只需要 Python 3.10+，几秒内完成。

## 构建软件库

输出目录须为仓库外的新绝对路径：

```bash
bash submission/reproduce.sh firstdot /absolute/new/firstdot-sdk
bash submission/reproduce.sh c8 /absolute/new/c8-sdk
```

firstdot 提供四种尺寸的软件接口；C8 是 8×32 GEMV 静态库，默认入口和 RVV 回退语义保持不变。C8 的 Makefile 会核对源文件和生成对象的固定哈希。

## 硬件与 NEMU

先按[环境说明](docs/ENVIRONMENT.md)准备固定版本的工具和子模块，然后：

```bash
export TEAM_XS_ENV_ROOT=/absolute/xs-env
bash team/scripts/prepare-dependencies.sh
source team/scripts/activate.sh
bash submission/reproduce.sh environment

# 构建最终 EMU（O2 两槽 + T14 融合输入，O1 关闭）
bash submission/reproduce.sh build-emu --output /absolute/new/emu-record --profile observe --firtool-dir /absolute/firtool/bin

# 构建带 vdot 扩展的 NEMU reference，并让后续命令使用它
export TEAM_NEMU_VDOT_ROOT=/absolute/new/nemu-vdot
export TEAM_EVIDENCE_DIR=/absolute/new/nemu-build-record
bash team/scripts/prepare-nemu-vdot.sh reference
export NEMU_HOME="$TEAM_NEMU_VDOT_ROOT/reference"
export VDOT_NEMU_REF="$NEMU_HOME/build/riscv64-nemu-interpreter-so"
export VDOT_EMU_BIN=/absolute/path/to/final/emu
```

`activate.sh` 默认把 `NEMU_HOME` 指向 xs-env 中未扩展的 NEMU；`prepare-nemu-vdot.sh` 把带 vdot 扩展的参考版建在 `$TEAM_NEMU_VDOT_ROOT/reference`，且在子进程中运行，不会修改当前 shell，所以构建完 reference 后要按上面显式导出 `NEMU_HOME` 和 `VDOT_NEMU_REF`。构建器拒绝覆盖已有的 `build/` 和输出记录。

## 按阶段执行

| 目标 | 入口 |
| --- | --- |
| hello/vadd 工作负载与运行 | `team/scripts/stage1.sh workload`、`team/scripts/stage1.sh run` |
| 乘积与归约算术 RTL（最终硬件共用） | `team/scripts/check-vdot-datapath.sh` |
| 译码接入 | `team/scripts/check-vdot-decode.sh` |
| 基础单槽 VDot FU | `team/scripts/check-vdot-fu.sh` |
| 最终两槽 FU 与 VFEX4 父级 | `bash submission/reproduce.sh o2-fu`、`o2-parent`（即 `team/scripts/check-vdot-o2.sh fu`、`parent`）：生成 RTL、Verilator 编译、10022 组向量与全部故障注入；运行日志见 `verification/o2-check-20261108/` |
| vdot 测试程序与整核差分 | `team/scripts/vdot-tests.sh host`、`build-xs full`、`run-rtl full` |
| RVV 等价基线 | `team/scripts/baseline-tests.sh` 与 `team/workloads/rvv-baseline/` |
| 微基准与 C8 数据复算 | `cd 提交/测试数据与运行结果证明材料 && python3 tools/prepare_data.py`：从原始 O2 运行日志重算表 3-3、3-4 |
| 微基准硬件重测 | 原测量程序：提交 `a0f13456e` 的 `team/optimizations/o2/r3-div-gate/performance/` |

整核运行前，`VDOT_EMU_BIN`、`VDOT_NEMU_REF`、数据目录、镜像和 `TEAM_EVIDENCE_DIR` 都要指向本次准备的输入和新的输出目录。`artifact_guard.py` 会核对 NEMU、镜像和输入的来源身份。

报告中各项数据对应的原始日志可用 `python3 -B submission/logs/read_log.py list --contains <关键字>` 查找，用 `show <路径>` 阅读。
