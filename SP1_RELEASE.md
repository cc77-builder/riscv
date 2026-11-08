# SP1 已验收版本 — zjhwork2

本分支发布 **原 SP1 一拍算术＋两槽弹性、firstdot V2＋原 C8**，验收矩阵 **20/20**。`zjhwork` 保留在 `a0f13456e0c3180fe9c4023f5cbe7874eb5d35a9`，本次不向其写入。zjhwork2原有历史全部保留，并承接zjhwork已有的完整工程及报告记录。

## 版本与证据入口

- [最终结论](team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/RESULT.md)
- [20项验收矩阵](team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/MATRIX.md)
- [加速比、面积及五档时序](team/optimizations/o2/integration/firstdot-v2-0f/continuation/speedup-first/sp1-e-item19-final-acceptance-20261108/METRICS.md)
- [计分板](开发计分板.md)与[版本数据档案](team/docs/version-data-ledger.md)
- [发布文件清单](team/releases/sp1-20261108/PUBLICATION_MANIFEST.json)

生产源码来自已冻结功能候选，基础硬件为`0f12df675378556670afd0dd2153f47fcb330610`，原补丁SHA256为`e1842a5f52a27fda2bea30f791921d6acefd63c54b415912adb8a1e3438be682`。四处生产修改仅为ExeUnit.scala、VDotElastic.scala、VDotO2.scala、Rob.scala，全部398项源码匹配原清单。未纳入主工作树未采用的P4-R1三路Mux1H改动，也未纳入第19项诊断EMU的额外侧带观察RTL。

## 启用已验收配置

**RTL新开关仍默认关闭。** 仅检出分支后使用普通旧构建命令，并不自动启用SP1。本次保留原源码和默认值，使用显式配置选用已验收版本。

在Linux独立检出本分支并准备好固定依赖和工具后，使用以下原构建选项。首次构建使用无旧build/out的独立目录，不覆盖旧0f EMU。本次发布没有执行构建或仿真；新机器路径、工具、生成物与运行身份仍需重新核验。

```bash
git clone --branch zjhwork2 --single-branch https://github.com/cc77-builder/riscv.git riscv-sp1
cd riscv-sp1
git submodule update --init --recursive
```

固定环境包括GraalVM JDK21、firtool1.62.1及原Verilator/GNU工具。依赖提交、工具哈希及原命令见sp1-ab/dependencies-final.json、build-inputs-final.json和sp1-cd/build/FREEZE.json；仓库子模块还需核对该清单，不能任意更新到最新版。配置本机`JAVA_HOME`和`CHISEL_FIRTOOL_PATH`后，在仓库根使用：

```bash
taskset -c 4,5 env -i \
  HOME="$HOME" USER="$USER" LOGNAME="$USER" LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC \
  PATH="$JAVA_HOME/bin:/usr/local/llvm/bin:/usr/local/bin:/usr/bin:/bin" \
  JAVA_HOME="$JAVA_HOME" CHISEL_FIRTOOL_PATH="$CHISEL_FIRTOOL_PATH" \
  NOOP_HOME="$PWD" DESIGN_DIR="$PWD" MILL_WORKSPACE_ROOT="$PWD" \
  VDOT_O2_ELASTIC=1 VDOT_T14_FUSED_INPUT=1 VDOT_P4_ONE_CYCLE=1 \
  VDOT_SP1_TRACE=1 VDOT_T13_TRACE=1 VDOT_O2_TRACE=0 \
  VDOT_O1_HANDOFF=0 VDOT_O1_TRACE=0 VDOT_T12_TRACE=0 \
  make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 \
  JVM_XMX=12G JVM_XSS=16m OPT_FAST=-O3 OPT_SLOW=-O0 -j2 \
  NOOP_HOME="$PWD" DESIGN_DIR="$PWD" REMOTE=localhost PGO_WORKLOAD= \
  WITH_DRAMSIM3=0 WITH_RESETGEN=0 EMU_TRACE=0 EMU_COVERAGE=0 EMU_SNAPSHOT=0
```

原构建使用CPU4/5、MinimalConfig、单核、VLEN128、ROB48、FTQ8；机器必须具有对应CPU与资源，否则先重新绑定执行合同。已验收EMU SHA256为`e34b2eaa8deb99f83534478217aaf144e32262ba08b2c18c31c6ac7265525c1e`。EMU二进制未上传。历史build_sp1.py使用当时绝对路径，不能直接在新目录运行而写回旧工作区；搬移后需调整路径并重新冻结。

## 核心指标

| 指标 | 0f | 原SP1 |
|---|---:|---:|
| chain d0/d1/d2：RVV/VDOT周期比 | 2.929725× | 3.397658× |
| batch：RVV/VDOT周期比 | 3.067873× | 3.067873× |
| C8 reuse：RVV/VDOT周期比 | 1.095238× | 1.099265× |
| C8 basic：RVV/VDOT周期比 | 0.553010× | 0.554086× |
| FU面积（μm²） | 17298.246 | 18322.878 |
| 真实父级面积（μm²） | 284614.946 | 285241.642 |
| 名义FU Q（ns） | 1.268520 | 1.790381 |
| 名义父级Q（ns） | 3.393998 | 3.337809 |

均复用原同合同测量，没有新增测试；不能推广为应用或LLM端到端加速比。局部面积/STA基于Nangate45、Yosys0.9、ABC1.01、OpenSTA2.0.17，Q=T−worst slack，不是全核后端签核或已实现全核主频。原G0成本失败保留，采用SP0加速比优先预算。

## 历史与发布边界

归档文档中的“默认0f”“未上传”和绝对路径为当轮事实，不回写旧证据。此次仅更新zjhwork2源码与发布入口，本地旧0f二进制和zjhwork保持不变；全局JSON保留120条历史记录。

最终五角色日志、收据、冻结清单及审计随包保存；历史阶段保留摘要和合同，未全量上传数GB合成夹具、缓存、旧生成RTL、波形、EMU或依赖二进制。完整原清单可能引用仅在原机器保留的文件；发布清单标明本次归档范围，不能视为所有历史运行的可搬移闭包。M4软件仅用于反压／取消验收，不替换firstdot V2/C8应用。

末轮第一角色UTC与单调时钟存在约35.34秒差异，原记录保留；预算使用单调时钟及外部监督，UTC一致性尚未取得资格。既有LaTeX/PDF仍是0f版历史材料，尚未改写成SP1结果。
