> **当前适用范围：** [当前路线](development-route-current.md)决定任务顺序。以下为 2026-10-09 阶段一记录与复现命令，“尚未实现 vdot”只描述当时。当前技术缺项见路线 T04，比赛材料由成员另行安排；只有需要补证且输入匹配时才新跑，不把旧阶段结果当最终组合验收。

# 阶段一：hello/vadd 构建、运行和证据

2026-10-09 已完成 NEMU 参考库、香山 MinimalConfig 仿真器和 hello/vadd 裸机测试程序构建。香山 + NEMU DiffTest 运行通过：3 组用例 / 24 个元素、GOOD TRAP、退出码 0。尚未实现 vdot。

## 按顺序运行

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

## 启动 flash 必须一致

固定 DiffTest 的默认启动 flash 有 3 条指令，固定 NEMU 的默认启动代码有 6 条。直接省略 `--flash` 曾在 PC=`0x10000004` 出现整数寄存器不一致，尚未运行到用户程序。

本队以 [boot-flash.S](../workloads/hello-vadd/boot-flash.S) 生成共同的 12 字节启动镜像，显式向仿真器传入 `--flash`，两端读取同一文件。运行脚本同时指定 `--ram-size=128MB` 和从固定 NEMU 源码构建的 `--diff` 参考库；不通过关闭协同验证回避问题。

## 程序覆盖和通过标准

独立汇编函数 [vadd.S](../workloads/hello-vadd/vadd.S) 实际执行 `vsetivli`、两个 `vle8.v`、`vadd.vv`、`vse8.v`。C 程序初始化向量状态，核对 VLEN=128、VL=8，再按元素与标量参考值比较。SEW=8、LMUL=1，有效 8 个元素；不要求尾部元素清零。

| 输入类别 | 预期输出（按无符号字节展示） |
| --- | --- |
| 正数 | `9 9 9 9 9 9 9 9` |
| 负数补码 | `254 252 250 248 246 244 242 240` |
| 边界与模 256 回绕 | `128 127 0 0 0 0 254 254` |

必须同时满足：`HELLO_VADD_PASS cases=3 lanes=24`、`HIT GOOD TRAP`、DiffTest 启用、运行退出码 0。vadd 的模 256 加法规则不等于未来 vdot 的宽位累加规则。

## 昨天的实际结果

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

## 归档范围

仓库保留源码、精简真实日志、配置、版本清单、反汇编和 CSV；完整 FST、完整 VCD、仿真器、参考库和测试二进制保留在原本机归档。Git 内的 `SHA256SUMS` 只覆盖本目录实际提交的历史材料，可在 `team/evidence/stage1-20261009` 执行 `sha256sum -c SHA256SUMS`。

阶段一仍需确定团队名、录制演示视频并按比赛系统要求交付；目前的材料证明环境和向量执行链路已通过，不代表 vdot 设计或比赛交付完成。
