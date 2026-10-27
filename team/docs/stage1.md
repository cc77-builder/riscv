# hello/vadd 运行与调试链

## 当前入口（2026-10-25）

本轮 T04 的验收约束见 [CONTRACT](../evidence/stage1-current-20261025/CONTRACT.md)，实际运行、源码身份、原始日志和波形结果见 [RESULT](../evidence/stage1-current-20261025/RESULT.md)。当前实现使用英文 `hello xiangshan, I am ...`，并如实区分已配置身份和默认占位身份；显示的是**构建宿主 IPv4**。

当前入口适用于团队 hello/vadd 三组 8-bit 用例。优先复用来源清楚的合格模型，按修改影响重建；改变构建开关不会使已有 EMU 自动拥有波形能力。该包不包含比赛报告、录屏、赛事提交，也不替代 vdot 或最终组合回归。

### 复用合格模型构建并运行软件

在 Linux 原生目录的团队源码根执行，下列路径变量由执行者配置。输出目录应位于仓库外；同一 action 及 run 输出拒绝覆盖，失败后换新目录。

```bash
export TEAM_XS_ENV_ROOT=/path/to/isolated/xs-env
export TEAM_STAGE1_EMU=/path/to/qualified/source/build/emu
export TEAM_STAGE1_REF=/path/to/qualified/riscv64-nemu-interpreter-so
export TEAM_STAGE1_RUNTIME_HOME=/path/to/qualified/source
export TEAM_ID=your_confirmed_personal_or_team_id
export STAGE1_ROOT=/path/to/new/stage1-run

TEAM_EVIDENCE_DIR="$STAGE1_ROOT/build" BUILD_JOBS=1 \
  bash team/scripts/stage1.sh workload
export TEAM_STAGE1_WORKLOAD_DIR="$STAGE1_ROOT/build/workload"
TEAM_EVIDENCE_DIR="$STAGE1_ROOT/normal" \
  bash team/scripts/stage1.sh run
```

`TEAM_STAGE1_RUNTIME_HOME/build` 需要该模型配套的 `constantin.txt` 与 `plusArgs`。运行器将二者复制进本次 `run/work/build`，在隔离 cwd 下设置 `NOOP_HOME`，并记录前后哈希。工作负载的 `identity.h`、`identity.json`、对象文件及镜像都在新输出目录，不修改团队源目录。

每次 `run/` 保存实际 command、PID、CPU affinity、起止/超时/退出码、输入身份和 stdout/stderr 哈希到 `run.json`；完整串口输出与模拟器 stderr 分开保留，`run-summary.log` 从实际日志提取。不得仅凭打印了 PASS 或 shell 管道退出成功就认定执行合格。

### 波形与复核

波形模型必须实际以 `EMU_TRACE=fst` 编译。本轮保留 T17 原始 RTL，复制其冻结输入后直接调用未修改的 DiffTest Makefile；精确复制列表、构建参数、工具版本和失败尝试见新证据目录。新 FST EMU 是独立身份，本轮用同一新 BIN 和普通参考实际重验，不能继承生产模型的其他验收。

设置新的 `TEAM_STAGE1_EMU`、匹配的 `TEAM_STAGE1_RUNTIME_HOME` 后：

```bash
TEAM_EVIDENCE_DIR="$STAGE1_ROOT/trace" DUMP_WAVE=1 \
  WAVE_BEGIN=10000 WAVE_END=44000 MAX_CYCLES=2000000 \
  bash team/scripts/stage1.sh run
python3 team/scripts/stage1-wave.py \
  --fst "$STAGE1_ROOT/trace/run/hello-vadd.fst" \
  --receipt "$STAGE1_ROOT/trace/run/run.json" \
  --disassembly "$STAGE1_ROOT/build/disassembly.txt" \
  --output "$STAGE1_ROOT/wave"
```

上述窗口针对本轮实际镜像；更换程序后应重新定位，不能假设所有程序的三次 vadd 都落在同一范围。新入口使用官方 `--dump-wave-full` 保留时钟两相。`-b/-e` 按 trap cycleCnt 筛选，不等同于 FST 时间戳。

提取依赖已安装的 GTKWave `fst2vcd` / `vcd2fst`，流式读取完整原始 FST，输出 `wave.json`、`cases.csv`、`selected.vcd` 与 `selected.fst`。后两者只保留验证所需信号，可直接在 GTKWave 中打开。原始 FST 不修改，哈希与运行 receipt 绑定。

提取器以实际时钟沿前的稳定低相值检查三组操作数、完整 ROB tag/pdest、写回值及延迟 DPIC 提交；具体层级和采样合同绑定本轮 T17 MinimalConfig。DPIC 提交有三级观察延迟，事件间隔不是执行单元固有延迟。未知值、缺帧、错误或歧义关联均拒绝；不会把非空波形文件直接判为事件通过。

### 检查器的有限反例测试

```bash
python3 team/tests/test-stage1-tools.py \
  --run "$STAGE1_ROOT/normal/run" \
  --wave "$STAGE1_ROOT/wave/wave.json" \
  --output "$STAGE1_ROOT/tool-tests"
```

该入口使用实际 PASS 的日志与事件表作为基准，构造错误/缺失信息来验证拒错，并用明确标识 MOCK 的进程检查超时、空输出和防覆盖。它不增加硬件用例数。单独重算一次执行日志时必须同时传入 receipt 与 stderr：

```bash
python3 team/scripts/summarize-run.py \
  "$STAGE1_ROOT/normal/run/emulator-output.log" \
  --receipt "$STAGE1_ROOT/normal/run/run.json" \
  --stderr "$STAGE1_ROOT/normal/run/emulator-stderr.log"
```

## 2026-10-09 历史记录（按原版本适用）

以下保留早期阶段证据、旧构建条件和当时结论；旧提取脚本没有在本轮主机找到，不将旧 CSV 或旧 PASS 当作新模型结果。需要原样复现旧合同应使用它记录的源码版本。当前使用以上入口。

2026-10-09 已完成 NEMU 参考库、香山 MinimalConfig 仿真器和 hello/vadd 裸机测试程序构建。香山 + NEMU DiffTest 运行通过：3 组用例 / 24 个元素、GOOD TRAP、退出码 0。尚未实现 vdot。

### 按顺序运行

完成 [环境准备](environment.md) 后，在团队仓库根目录执行：

```bash
export TEAM_EVIDENCE_DIR="$PWD/team/out/my-stage1"
bash team/scripts/stage1.sh nemu
bash team/scripts/stage1.sh emu
TEAM_ID=riscv-vdot-team bash team/scripts/stage1.sh workload
bash team/scripts/stage1.sh run
```

脚本按当前仓库路径定位测试源码，无需用户名为 `riscv`。`TEAM_ID` 默认为待替换的 `riscv-vdot-team`，`identity.h` 根据当前 WSL IPv4 生成且不提交 Git；这不是仿真处理器的网络地址。正式提交前必须确定并替换团队标识。

构建仿真器使用 `CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 EMU_TRACE=fst JVM_XMX=12G`，并行度默认 2。昨天 C++ 增量构建曾使用 4，但复现脚本先采用 2；Scala/RTL 与处理器参数相同。需要观察波形时运行 `DUMP_WAVE=1 bash team/scripts/stage1.sh run`。默认关闭运行时波形，避免每次重复生成约 211 MiB 的文件；这不关闭 DiffTest。

已有仿真器和 NEMU 参考库时，可跳过它们的构建，只重新编译 workload 并运行。改变硬件配置、源码或工具版本后必须重新构建，不能拿旧仿真器验证新 RTL。

各步骤保留命令、日志、产物 SHA-256 和 `*.status`（含退出码）。普通运行的完整输出为 `emulator-output.log`，精简输出为 `run-summary.log`；精简日志从真实输出提取，不伪造通过信息。

### 启动 flash 必须一致

固定 DiffTest 的默认启动 flash 有 3 条指令，固定 NEMU 的默认启动代码有 6 条。直接省略 `--flash` 曾在 PC=`0x10000004` 出现整数寄存器不一致，尚未运行到用户程序。

本队以 [boot-flash.S](../workloads/hello-vadd/boot-flash.S) 生成共同的 12 字节启动镜像，显式向仿真器传入 `--flash`，两端读取同一文件。运行脚本同时指定 `--ram-size=128MB` 和从固定 NEMU 源码构建的 `--diff` 参考库；不通过关闭协同验证回避问题。

### 程序覆盖和通过标准

独立汇编函数 [vadd.S](../workloads/hello-vadd/vadd.S) 实际执行 `vsetivli`、两个 `vle8.v`、`vadd.vv`、`vse8.v`。C 程序初始化向量状态，核对 VLEN=128、VL=8，再按元素与标量参考值比较。SEW=8、LMUL=1，有效 8 个元素；不要求尾部元素清零。

| 输入类别 | 预期输出（按无符号字节展示） |
| --- | --- |
| 正数 | `9 9 9 9 9 9 9 9` |
| 负数补码 | `254 252 250 248 246 244 242 240` |
| 边界与模 256 回绕 | `128 127 0 0 0 0 254 254` |

必须同时满足：`HELLO_VADD_PASS cases=3 lanes=24`、`HIT GOOD TRAP`、DiffTest 启用、运行退出码 0。vadd 的模 256 加法规则不等于未来 vdot 的宽位累加规则。

### 昨天的实际结果

成功运行时间为 2026-10-09 20:55:26—21:00:28（北京时间）。原始 [通过摘要](../evidence/stage1-20261009/hello-vadd-summary.log) 包含团队占位标识与当时 WSL IP，作为历史记录保留；新机器输出不同 IP 是正常现象。

原记录：`instrCnt=16557`、`cycleCnt=42962`、IPC=0.385387、宿主耗时约 300.823 秒、退出码 0。这些统计含启动、UART 输出和校验，不能当作单条向量指令的延迟。

来自昨天完整 FST 波形的采样结果：

| 用例 | 输入握手周期 | 输出握手周期 | vadd 提交周期 | 写回低 64 位 |
| --- | --- | --- | --- | --- |
| 正数 | 19625 | 19626 | 19631 | `0x0909090909090909` |
| 负数补码 | 25460 | 25461 | 25466 | `0xf0f2f4f6f8fafcfe` |
| 边界 | 33009 | 33010 | 33015 | `0xfefe000000007f80` |

提交 PC=`0x80000138`，机器码=`0x021101d7`，`vecwen=1`，`wdest=3`。源代码或链接选项改变后 PC 可能改变，观察新波形时应重新反汇编定位。

事件原表：[提交 CSV](../evidence/stage1-20261009/vadd-commit-events.csv)、[运算单元 CSV](../evidence/stage1-20261009/vector-fix-alu-events.csv)。这些周期差是接口采样事件间隔，不直接定义执行单元固有延迟。源码分析路线为取指/解码 → 重命名与调度 → 向量加载 → 整数向量运算及写回 → ROB 提交 → DiffTest 比较架构状态。

### 归档范围

仓库保留源码、精简真实日志、配置、版本清单、反汇编和 CSV；完整 FST、完整 VCD、仿真器、参考库和测试二进制保留在原本机归档。Git 内的 `SHA256SUMS` 只覆盖本目录实际提交的历史材料，可在 `team/evidence/stage1-20261009` 执行 `sha256sum -c SHA256SUMS`。

阶段一仍需确定团队名、录制演示视频并按比赛系统要求交付；目前的材料证明环境和向量执行链路已通过，不代表 vdot 设计或比赛交付完成。
