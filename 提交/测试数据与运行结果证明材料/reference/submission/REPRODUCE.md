# 最终版复现入口

从仓库根目录运行。`submission/reproduce.sh` 只调用保留的原构建/检查实现，提供统一入口，不修改生产代码逻辑。

## 材料与主机检查

```bash
bash submission/reproduce.sh check
bash submission/reproduce.sh logs-check
```

第一条检查当前交付文件、参考模型、确定性向量、编码和静态接入；第二条逐项校验全部归档日志及其元数据。两者均不启动 RTL/全核仿真。

## 构建软件库

输出必须是仓库外的新绝对路径，工具链须与固定身份匹配：

```bash
bash submission/reproduce.sh firstdot /absolute/new/firstdot-sdk
bash submission/reproduce.sh c8 /absolute/new/c8-sdk
```

firstdot 提供四尺寸的软件接口；C8 是独立显式选用的 8×32 静态库，默认入口和 RVV 回退语义保持原样。C8 原 Makefile 会核对源文件和生成对象的固定哈希。构建成功只证明软件构建，不证明新应用实际运行或周期收益。

## 硬件与 NEMU

先按[环境说明](docs/ENVIRONMENT.md)准备固定工具、子模块和外部依赖，然后：

```bash
bash submission/reproduce.sh environment
bash submission/reproduce.sh build-emu --output /absolute/new/emu-record --profile observe --firtool-dir /absolute/firtool/bin
export TEAM_NEMU_VDOT_ROOT=/absolute/new/nemu-vdot
export TEAM_EVIDENCE_DIR=/absolute/new/nemu-build-record
bash team/scripts/prepare-nemu-vdot.sh reference
```

最终硬件使用原 O2/H1/DIV 修复源码，构建器显式启用 O2/T14 并关闭 O1。不要用不带该配置的其他构建结果代替最终 EMU。原构建器拒绝覆盖已有 `build/` 和已有输出记录。

## 按阶段执行

| 目标 | 原入口 |
| --- | --- |
| hello/vadd 工作负载与运行 | `team/scripts/stage1.sh workload`、`team/scripts/stage1.sh run` |
| 算术 RTL | `team/scripts/check-vdot-datapath.sh` |
| FU / 译码检查 | `team/scripts/check-vdot-fu.sh`、`team/scripts/check-vdot-decode.sh`；使用对应配置与范围 |
| vdot 测试数据、程序与全核运行 | `team/scripts/vdot-tests.sh`，按其 `host / build-xs / run-rtl` 模式 |
| RVV 等价基线 | `team/scripts/baseline-tests.sh` 与 `team/workloads/rvv-baseline/` |
| 控制与性能工作负载 | `team/workloads/vdot-regression/`、`team/workloads/unified-vdot/` 及对应原检查器 |

`VDOT_EMU_BIN`、`VDOT_NEMU_REF`、数据目录、镜像及 `TEAM_EVIDENCE_DIR` 要指向本次明确准备的输入和新输出目录，不能依靠原机器的默认绝对路径。运行前按原 `artifact_guard.py` 检查来源；迁移生成的新镜像须记录新身份，不改旧哈希伪造通过。

本轮进行了材料、主机检查和软件库重建。完整硬件构建/全核运行未因目录整理而重跑；正式交付前建议从干净检出按上述入口复核，并保留新的命令、退出码、源码/依赖/配置/镜像身份及完整日志。
