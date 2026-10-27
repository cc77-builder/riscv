# T04 当前 hello/vadd 输出与调试链结果

**结论：本轮 T04 当前输出、整核运行和波形调试链已按限定合同闭合。** 同一新 BIN 在已有 T17 生产模型和本轮独立 FST 模型上分别通过普通 NEMU DiffTest；最终提取覆盖两个候选向量整数 FU、八个提交槽，核对三组实际运算与提交。最终 24 项工具检查通过。

- 操作：`20261025-LiZufan001-t04-current-0054`；执行者：`@LiZufan001 / Pro Agent`，核心代码由本轮 Pro 实现，独立 Agent 只读审查。
- 开始：2026-10-25 00:53:38（UTC+08:00）。本文形成于主要验证完成后；交付/发布实际结束见计分板与 Issue #2 的 END/DONE。
- 软件开发基点：`15e0428018b9f9bb1106b6159c522158e1403562`，本结果随源码提交，承载提交由 Git 历史定位。
- [合同](CONTRACT.md)、[机器可读汇总](acceptance.json)、[使用入口](../../docs/stage1.md)、[实际运行位置](runtime-locations.json)。

## 1. 本轮改动与选择理由

现有程序仍打印中文“我是”和无条件 `identity_status=placeholder`；阶段一波形表来自 2026-10-09，引用的旧提取脚本在本轮主机未找到。当前 T17 生产 EMU 没有编译 FST，运行时设置波形参数不能补上编译能力。因而选择补齐当前可执行证据，保留稳定硬件与软件优化基线。

1. 团队 `hello-vadd/main.c` 改为 `hello xiangshan, I am <identity>, IP address=<IPv4>`；身份由构建参数配置，地址明确标为构建宿主 IPv4。使用已核实的个人身份 `LiZufan001`，不编造团队名称。
2. 复用 `stage1.sh`，将工作负载编译到新输出目录；新增 `stage1-run.py` 保存命令、实际退出状态、输入与两路日志哈希，隔离 cwd 和运行辅助文件，处理超时并拒绝覆盖旧输出。
3. 补强团队 `summarize-run.py`：必须绑定执行 receipt 与 stderr，同时检查精确结果、顺序、DiffTest、GOOD TRAP、输入未变及正常退出。
4. 新增 `stage1-wave.py`，以 GTKWave 的成熟转换器流式读取 FST；从本轮反汇编定位目标 PC，检查真实时钟沿、操作数、完整输入/输出 tag 及延迟 DPIC 提交，生成便于复核的选通信号波形。
5. 新增有限工具反例测试；原官方 DiffTest/NEMU/验证程序、生产 RTL、稳定 GEMV 默认与既有冻结结果均保持。

这是当前 hello/vadd 工程链的补证与工具修正。没有运行官方赛事提交或宣称通过未知的官方精确字符串校验器。

## 2. 输入身份与实际运行

| 对象 | SHA-256 / 身份 |
| --- | --- |
| 固定 T17 硬件生成来源 | 源提交 `34bae6d4acceac939f958199dae53c14bc1f6183` |
| 原生产 EMU | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 本轮新 FST EMU | `1ff3f457ff582d0c3155a15dafa1fa60b8275d9356e29a0b7806c9d3915ce9f7` |
| 普通参考 NEMU | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` |
| 两次运行共同 BIN | `d81437b44473cef2b0c5777330e13fd076567d4fc1a4296be35d971e51a4dcad` |
| 两次运行共同 flash | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994` |
| 全量原始 FST | `cf8abe9104fb955c7dc4bf1efda6588a61060fce33857b9ddc6d5020421be299`，181,143,183 字节 |
| 最终选通信号 FST | `4c9f442704871010026654fd9d60854024b270a83be6354be5dee3ff25df24e1`，393,288 字节 |

新 FST 模型直接使用 T17 的 1,807 个逐文件核验输入及原版 DiffTest Makefile，未重新生成 Chisel RTL。实际 `VM_TRACE=1、VM_TRACE_FST=1`，见 [构建 receipt](trace-build-02-state.json)。构建前、构建后和最终封存都核对 T17 原件及副本，最终两份各 1,807 文件均未变化，生产 EMU 和普通参考身份保持，见 [最终输入核验](trace-inputs-final.json)。

| 新执行 | 北京时间（UTC+08:00） | 结果 | 指令数 / 周期 |
| --- | --- | --- | --- |
| 原 T17 生产 EMU | 01:09:21.574716～01:10:18.357888 | 3 组 / 24 元素、普通 DiffTest、GOOD TRAP、exit 0 | 16,621 / 43,249 |
| 新 FST EMU | 01:28:57.974329～01:31:24.009122 | 同一 BIN，3 组 / 24 元素、普通 DiffTest、GOOD TRAP、exit 0 | 16,621 / 43,249 |

两次原始串口输出及独立 stderr 分别见 [production-run](production-run/) 与 [trace-run](trace-run/)，receipt 保留完整命令和前后输入哈希。周期包含启动、UART 和校验，只证明本程序执行统计一致，不是单条 vadd 延迟、GEMV 或应用性能结论。

源码快照按实际使用身份分别保存到 [execution-snapshots.tar.gz](execution-snapshots.tar.gz)，对应 `workload-source-01` 至 `05` 清单。01 构建并运行生产模型；02 使用 full 波形运行；03/04 增补测试和修正提取范围；05 仅删除 main.c/stage1.sh 文件末尾各一个空行，全部最终 Python 工具与 04 逐字节相同。05 重新 GNU 编译的 BIN/flash 与已实际执行输入逐字节相同，见 [发布源码等价证明](published-workload-equivalence.json)。两个 ELF 文件字节不同，本轮实际执行以 BIN 为输入；不混写 ELF 身份，原始 ELF 与新 ELF 均归档。

## 3. 最终波形结果

采集参数为 `--dump-wave-full -b 10000 -e 44000`，程序在达到上限前正常结束。最终选择 **127 个信号、两个 VialuFix、八个提交槽**，检查 33,249 个完整上升沿，得到三次输入、三次写回、三次目标提交共九条事件。结果见 [wave.json](wave/wave.json)、[事件表](wave/cases.csv)、[选通信号 FST](wave/selected.fst) 和 [压缩 VCD](wave/selected.vcd.gz)。

| 组 | FU 输入 timer | FU 输出 timer | DPIC 观测 timer | ROB flag/value/pdest | 实际输出低 64 位 |
| --- | ---: | ---: | ---: | --- | --- |
| 0 | 19525 | 19526 | 19531 | 1 / 13 / 51 | `0909090909090909` |
| 1 | 25526 | 25527 | 25532 | 0 / 21 / 57 | `f0f2f4f6f8fafcfe` |
| 2 | 33193 | 33194 | 33199 | 1 / 25 / 63 | `fefe000000007f80` |

三个运算均在 `exus_2.VialuFix` 实际发生；同时检查了无数字后缀的 `exus.VialuFix`。三次目标提交均为 PC `0x80000138`、机器码 `0x021101d7`、`vecwen=1、wdest=3`。低 lane 在前的八字节输出分别为 `9×8`、`254 252 250 248 246 244 242 240`、`128 127 0 0 0 0 254 254`。

本表 timer 是实际时钟沿前低相采样的 ROB trap timer；原始 FST 时戳另列在 JSON/CSV。固定源码 [Rob.scala](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/rob/Rob.scala) 对 InstrCommit 设置 `delay=3`，DPIC 的 robIdx 只含 value。因而 DPIC 观测时间不是原始 ROB retire 时间；接口事件的间隔也不能直接定义 FU 固有延迟或吞吐率。

验收所需时钟、控制及有效事件字段出现未知值会拒绝。未生效 FU 的无效 payload 不作为有效数据检查；tail-agnostic 的高 64 位不参与三组结果判定。

## 4. 拒错、修订与保留证据

最终 [24 项工具检查](tool-tests/final-24.json) 全部通过，包括实际选通 VCD 重放同样九条事件，以及日志变更、错 lane、缺 DiffTest、截断 trap、重复用例、非零退出、超时、输入/辅助文件变更、stderr 失败、空输出、缺波形、禁止覆盖、超时清理、缺 FU、缺半周期、有效操作数未知、缺提交、错写回/目的寄存器/ROB/操作数/输入 tag。

封存数据在另一新目录的离线重放见 [交付复核](delivery-replay.json)。这些测试使用真实通过的日志/事件作为基准，生命周期测试使用明确标识 MOCK 的进程；**不增加硬件用例数**。最终原始测试夹具保存在 [tool-tests-final.tar.gz](tool-tests-final.tar.gz)。此前以生产日志运行的 14 项及修订中间的 23 项摘要保留，最终资格以 24 项及对应脚本哈希为准。

本轮两项实际问题均保留了原证据：

- 首次 FST 构建因非登录环境 PATH 没有已安装的固定 Verilator 而失败；未修改官方源码，显式设置 PATH/VERILATOR_ROOT 后构建成功。失败 [state](trace-build-state.json) 与 [原始日志](logs/trace-build.log.gz) 保留。
- 首版提取正则遗漏没有数字后缀的 `exus.VialuFix`。首版程序虽返回 PASS，但只覆盖一个 FU，**不满足本合同**，因此标为 `INCOMPLETE_SCOPE`，见 [修正记录](wave-scope-correction.json)、[实际层级检查](fst-hierarchy-inspection.json) 与 [首版原件](superseded-wave-01/)。修正选择器、强制要求两个 FU 并增加缺 FU 反例后，从同一未变 FST 重新提取；无需重复硬件仿真。

发布准备时的文件末尾空行由格式检查发现并清理，使用新快照进行 BIN 等价验证；不覆盖先前运行输入。所有原始构建、执行、失败/中间结果与完整 FST 继续保留在 runtime-locations 指定目录。

## 5. 使用与离线复核

正常构建、运行和波形提取的完整入口见 [stage1.md](../../docs/stage1.md)。每次输出使用新目录；工作负载、运行、提取分别有独立身份，不修改已完成目录。

在仓库根的 Linux 环境可离线检查本目录与重放最终工具验证；该过程不启动真实 EMU/NEMU：

```bash
EVID=team/evidence/stage1-current-20261025
(cd "$EVID" && sha256sum -c SHA256SUMS)
REPLAY=$(mktemp -d /tmp/hello-vadd-replay.XXXXXX)
mkdir "$REPLAY/run" "$REPLAY/wave"
cp "$EVID/trace-run/run.json" "$EVID/trace-run/emulator-output.log" "$REPLAY/run/"
gzip -cd "$EVID/trace-run/emulator-stderr.log.gz" > "$REPLAY/run/emulator-stderr.log"
cp "$EVID/wave/wave.json" "$REPLAY/wave/"
gzip -cd "$EVID/wave/selected.vcd.gz" > "$REPLAY/wave/selected.vcd"
python3 team/tests/test-stage1-tools.py \
  --run "$REPLAY/run" --wave "$REPLAY/wave/wave.json" --output "$REPLAY/tests"
```

离线检查验证封存证据与工具，不等于重新运行硬件、独立机器安装或人工验收。`selected.fst` 可直接由 GTKWave 打开；完整 FST 的位置/哈希在 runtime-locations 中。

### 从已核实 T17 生成物重新构建 FST 模型

需要与本轮一致的 T17 生成物和固定工具。设置 `T17_SOURCE` 为其 source 根、`TRACE_ROOT` 为全新 Linux 原生目录，复制并校验 manifest 内输入：

```bash
export T17_SOURCE=/path/to/t17-clean/source
export TRACE_ROOT=/path/to/new/t04-trace
export T04_EVIDENCE="$PWD/team/evidence/stage1-current-20261025"
python3 - <<'COPY'
import os, json, hashlib, shutil
from pathlib import Path
source, target = Path(os.environ['T17_SOURCE']), Path(os.environ['TRACE_ROOT'])
manifest = json.loads((Path(os.environ['T04_EVIDENCE']) / 'trace-inputs.json').read_text())
target.mkdir(parents=True, exist_ok=False)
for rel, expected in manifest['copied_inputs'].items():
    part = Path(rel)
    assert not part.is_absolute() and '..' not in part.parts
    src, dst = source / part, target / part
    assert hashlib.sha256(src.read_bytes()).hexdigest() == expected, rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    assert hashlib.sha256(dst.read_bytes()).hexdigest() == expected, rel
COPY
export VERILATOR_PREFIX=/path/to/pinned/verilator-5.052
export PATH="$VERILATOR_PREFIX/bin:$PATH"
export VERILATOR_ROOT="$VERILATOR_PREFIX/share/verilator"
taskset -c 0-2 make -C "$TRACE_ROOT/difftest" emu \
  DESIGN_DIR="$TRACE_ROOT" NOOP_HOME="$TRACE_ROOT" SIM_TOP=SimTop \
  NUM_CORES=1 RTL_SUFFIX=sv EMU_THREADS=1 EMU_TRACE=fst \
  OPT_FAST=-O3 OPT_SLOW=-O0 NO_DIFF=0 WITH_CHISELDB=1 WITH_CONSTANTIN=1 \
  WITH_DRAMSIM3=0 EMU_COVERAGE=0 EMU_SNAPSHOT=0 RELEASE=0 -j3
```

精确实际命令、版本及输入哈希以构建 receipt、[工具版本](tool-versions.json) 和 manifest 为准。改目录会影响二进制内的构建路径等身份，必须记录新的 EMU SHA，再按当前运行入口重验；不能仅拿同名 `emu` 视作本轮二进制。没有原生成物时先按 T17 自身的干净构建说明恢复，不能拼接其他历史 RTL。

## 6. 范围、回退与接续

新增真实整核执行为两次，每个模型各三组/24元素；新 FST 构建成功一次，失败尝试独立保留。实际四核预算内，构建 CPU0–2/-j3，功能运行及提取单核隔离。没有新 vdot RTL、完整应用性能、ASIC PPA、T17全套回归、新机器安装或人工 ACK 结论。

本 T04 子项输入不变时无需重跑。后续更换 hello 程序、模型、FU 接口、层级或调试合同才按影响补验。原生产 EMU 与现有稳定 GEMV/RVV 回退保持可用；需要回退本轮团队工具时，在独立分支对本成果提交执行正常 Git revert，再遵守 Issue 短集成窗口，不覆盖原始归档。

当前没有由本轮遗留的构建或仿真。R2-S3/caller 的有效认领仍属原执行者；其后台进程结束不代表认领释放。本轮不接管该包，也不因局部事件间隔就新开 RTL 性能改动。

工程工具反馈：本次 ChatPC 的完整 git_status 调用超时；同一 Windows 工作树原生 Git status 约 0.8 秒完成，随后继续使用原生 Git。长 WSL 构建若把 PowerShell cwd 放在 Git 工作树，会持有过宽的 Git common-dir 资源锁；本轮后续任务从独立非 Git 宿主目录执行，使用不可变 Linux 输入和隔离输出，恢复并行而没有改权限或绕过安全拒绝。无需改项目工具配置，也不把这两次不同实现的耗时当成严格性能基准。
