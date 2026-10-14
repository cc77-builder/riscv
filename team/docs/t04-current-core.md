# T04：James 主机的当前源码全核基线

日期：2026-10-13（北京时间）。分支 dev，基准提交 `5389bde799f5ce1e7939e4eeed5fe9bcdc2325a3`，包含未提交的 T06 接口实现。本记录补当前主机的 hello/vadd 调试基线；T03 团队确认、真实团队标识、非作者复现和视频交付仍独立验收。

## 构建输入与环境

构建使用本仓库的源码副本，源码包包含当前已跟踪差异、非忽略的新文件及 126 个递归子模块的固定版本。Windows 源码与 Linux 副本通过 Git clean 后的规范字节比较，副本另记录物理文件 SHA256；不声称 Windows CRLF 文件与 Linux LF 文件的原始字节相同。编译输入清单包含 436 个根文件；依赖审计检查 21,236 个文件并拒绝编译目录中的未知/忽略源码。

本次实际源码包摘要为 `e8bd8d763650fc4fe8b8a389f643032db4f582aa2388915750635250bacc05d6`，Linux 副本在 `/home/amesotten/.cache/codex-rvinno/t04/source-e8bd8d763650fc4f`。共享 Git 对象存储仅用于检出和版本查询，编译源文件与输出位于 Linux 文件系统。

| 项目 | 本次配置 |
| --- | --- |
| 工具 | Ubuntu-HDL，Ubuntu Java 21.0.12.1，Mill 0.12.3，Chisel 6.6.0，firtool 1.62.1，Verilator 5.020；仿真器用 Clang 19.1.1，workload 用 RISC-V GCC 13.3.0 |
| 处理器/仿真 | MinimalConfig，单核，EMU_THREADS=1；RTL 生成单任务，C++ 编译先单任务、后双任务；FST 支持 |
| 检查 | DiffTest 与断言开启；共用显式 12 字节 flash；RAM=128MB；最多 2,000,000 周期，运行超时 20 分钟 |
| 构建资源 | WSL 约 11GiB 内存、默认 3GiB swap；驱动 JVM 1GiB、生成器 JVM 6GiB，必要时使用项目缓存中的临时 8GiB swap |
| 可选插件 | WITH_CHISELDB=0、WITH_CONSTANTIN=0、WITH_ROLLINGDB=0；不关闭 DiffTest |
| AM | 固定 `086a238062fdfb3281b745a537b361983d0154b5`；记录实际链接库摘要 |
| NEMU | 已交付的候选扩展 reference；运行入口重新核验角色、配置、源码及 DSO 摘要 |

该工具/插件组合不同于原开发机，不能替代旧环境版本检查或全队复现。没有更改全局 PATH、Java 安装、WSL 配额或 `.wslconfig`。

为解决 GCC 对生成代码的高内存占用，本轮在 Ubuntu-HDL 中安装 `clang-19=1:19.1.1-1ubuntu1~24.04.2` 及八个配套包（下载 53.8MB、磁盘约 257MB、没有升级已有包）。这是该 WSL 发行版的系统级工具，其他项目可以显式使用 `clang-19/clang++-19`；源码副本、Mill、波形提取工具及构建输出放在项目缓存，不修改 Windows 的全局编译器配置。

## 构建问题与处理

首次启动因 Mill 的 `-i` 与重复 `--no-server` 冲突失败；修正项目本地启动器后重新冻结源码包。随后根 Scala 编译通过，硬件展开给出 135 条警告；直接生成完整 RTL 时出现内存耗尽，内核记录 Java 被 OOM killer 终止。降低驱动堆并增加临时 swap 的重试也未取得完整退出记录，保留失败日志。

恢复使用本次留下的完整 `SimTop.fir`，重新检查源码绑定，记录其摘要；在独立进程运行 firtool 并关闭 MLIR 多线程。完整解析及 RTL 转换成功，输入摘要未变；实测耗时 5:54.26、最大 RSS 6,903,600KiB。随后执行与根 Makefile 相同的 SRAM 模型生成及断言处理，再恢复正式 Make emu 流程。并未修改处理器行为以规避启动或差分问题。

[拆分构建脚本](../scripts/core-baseline-split.sh) 提供正常 FIR-only → firtool → Make emu 路径，以及必须显式选择、核验摘要/成功记录的恢复入口。本次采用恢复入口；正常 FIR-only 入口是否已完整复现，以后续实际验证记录为准。

Verilator 转换完成后，早期 C++ 单个编译任务的内存为数百 MiB。确认本次副本的顶层 Make 后受控终止单任务构建，保留日志/143退出记录，使用 [编译恢复脚本](../scripts/core-baseline-compile.sh) 以双任务继续。随后 `VSimTop___024root__DepSet_hd5918264__173.cpp` 的 GCC `-O3` 优化耗尽约 11GiB 内存和约 11GiB 总 swap；终止该优化步骤，保留失败记录及旧驱动源码，将 248 个对象/缓存文件移入独立备份，再统一以 `OPT_FAST=-O1 / OPT_SLOW=-O0` 重编。没有混用先前 O3 对象。

GCC O1 对同一文件仍占用大量内存，因此保留该次失败和驱动源码，将 274 个对象/缓存文件另行备份，切换 Clang 19.1.1 全量重编，保持 `OPT_FAST=-O1 / OPT_SLOW=-O0`。先前卡住的文件在 Clang 下已生成对象；没有将两种编译器的旧对象混入本次产物。

恢复入口先检查源码绑定及全部准备好的 RTL 摘要；构建后再次核对 RTL，避免 Make 意外重新生成后沿用旧来源。正常拆分入口现也调用该编译脚本，默认 Clang/双任务/O1；缓存 profile 绑定编译器二进制、优化级别、源码包、RTL 清单及生成的 DiffTest 文件，profile 改变或缓存缺少来源时拒绝继续，须移走旧对象后完整重编。降低的是宿主仿真程序的编译优化，不能据此声称处理器频率或 vdot 性能改变。临时 swap 的清理记录与最终构建结果一并归档，未加入永久配置。

## 复现入口

在 Windows 仓库根目录用 Python 生成新的包，避免 WSL Git 对 Windows CRLF 检出产生无关差异：

```powershell
python team/scripts/prepare-core-baseline.py pack --source . --pack team/out/my-core-source
```

再在 WSL 中 materialize 到一个不存在的 Linux 缓存目录；脚本从本地固定 Git 对象检出依赖，不升级子模块。工具和 NEMU/AM 路径按本机已核验位置设置：

```bash
python3 /mnt/c/Code/RVInno/riscv/team/scripts/prepare-core-baseline.py materialize \
  --source /mnt/c/Code/RVInno/riscv \
  --pack /mnt/c/Code/RVInno/riscv/team/out/my-core-source \
  --cache /home/amesotten/.cache/codex-rvinno/t04
task_root=$(cat /mnt/c/Code/RVInno/riscv/team/out/my-core-source/build-copy.txt)
cd "$task_root"
export CORE_SOURCE_PACK=/mnt/c/Code/RVInno/riscv/team/out/my-core-source
export TEAM_EVIDENCE_DIR=/mnt/c/Code/RVInno/riscv/team/out/my-core-run
export CORE_MILL=/home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3
export CORE_FIRTOOL=/home/amesotten/.cache/llvm-firtool/1.62.1/bin/firtool
export NEMU_HOME=/home/amesotten/.cache/codex-rvinno/t08/delivered/reference
export AM_HOME=/home/amesotten/.cache/codex-t05/nexus-am-086a238
export JAVA_OPTS='-Xmx1g -XX:ActiveProcessorCount=2'
python3 team/scripts/audit-core-dependencies.py --target "$task_root" --evidence "$TEAM_EVIDENCE_DIR"
bash team/scripts/core-baseline-split.sh
bash team/scripts/core-baseline.sh workload
DUMP_WAVE=1 bash team/scripts/core-baseline.sh run
python3 team/scripts/check-core-baseline.py --source /mnt/c/Code/RVInno/riscv \
  --pack "$CORE_SOURCE_PACK" --target "$task_root" --evidence "$TEAM_EVIDENCE_DIR" --nemu "$NEMU_HOME"
```

临时交换文件只用于资源不足的构建阶段；本脚本不自动修改机器的永久交换配置。正常复现不设置 `CORE_REUSE_FIR` 或 `CORE_REUSE_LOWERED`。

验收入口先删除旧 `check.json`，检查构建/程序/运行退出记录、绑定源码及依赖、仿真器/程序/flash/参考库摘要、真实运行参数、24 个明确结果及 GOOD TRAP，再生成新验收记录。失效日志或旧 PASS 不能单独满足入口。

## 当前执行路径

普通 `vadd.vv v3,v1,v2` 经 [VecDecoder](../../src/main/scala/xiangshan/backend/decode/VecDecoder.scala) 映射到 `FuType.vialuF / VialuFixType.vadd_vv`。重命名分配向量目的与实际 VL 依赖；向量调度等待源数据/VL，就绪后经读端口进入 [VIAluFix](../../src/main/scala/xiangshan/backend/fu/wrapper/VIAluFix.scala)。其结果经过普通向量尾部/掩码处理和现有向量写回端口，ROB 按程序顺序提交，DiffTest 对照 NEMU 的架构状态；随后 `vse8.v` 将有效元素写入内存，C 程序用标量模 256 加法逐项核对。

普通 vadd 的 tail-agnostic 行为不能替代 vdot 的高 96 位清零合同。当前 [执行资源](../../src/main/scala/xiangshan/Parameters.scala) 仍未配置 `VdotCfg`；新增 FU 定义及适配层通过单元测试，不表示 custom-0 已可在全核执行。

## 本机实际结果与边界

Clang 全量编译成功，耗时 13:13.84，最大 RSS 2,969,272KiB，退出码 0。仿真器 SHA256 为 `e75b1506abcc77025da776a222abaa684bdc389cebbc7bc4340a6468d40fb944`。FIR、准备好的 RTL、生成的 DiffTest 文件和缓存 profile 在编译后保持一致；所有旧 GCC 对象已单独移走。

实际全核运行：`Difftest enabled`，正数、负数、边界三组共24项正确，`HELLO_VADD_PASS`，`HIT GOOD TRAP`，退出码0。统计为 `instrCnt=16518 / cycleCnt=42415`，宿主约235.919秒；包含启动、UART和校验，不能当作单条指令延迟或加速比。参考端和 DUT 显式使用同一12字节 flash；向量寄存器/向量CSR比较由生成的 `diffstate.h` 配置开启。

FST 为236,538,469字节，SHA256 `55fa40b08b8d104466167cde9550f72f0b9a4da122ed6023589ae732099ab0aa`。实际反汇编确认 `vadd.vv` 的 PC=`0x80000138`、机器字=`0x021101d7`。波形中的执行实例为 `inner_vfExuBlock.exus_2.VialuFix`，fuOpType=64、vsew=0；三个输入/输出握手及提交完整，vecwen=1、逻辑目的v3。

| 用例 | FU输入周期 | FU输出周期 | ROB提交观测周期 | 结果低64位 |
| --- | --- | --- | --- | --- |
| 正数 | 19719 | 19720 | 19722 | `0x0909090909090909` |
| 负数补码 | 25366 | 25367 | 25369 | `0xf0f2f4f6f8fafcfe` |
| 边界/回绕 | 32698 | 32699 | 32701 | `0xfefe000000007f80` |

本次提交观测取 `rob.difftest_delayer*.i_*`，即ROB侧、DiffTest内部三周期延迟之前；[Rob.scala](../../src/main/scala/xiangshan/backend/rob/Rob.scala) 直接用 `commitValid && isCommit` 产生该有效信号。FST默认时间戳为 `DiffTrapEvent.cycleCnt`，在上升沿eval后采样。旧历史记录使用DPIC侧，不能混合采样位置比较延迟；事件间隔也不独立定义FU固有延迟。完整128位结果在CSV中保留，高64位为普通vadd的agnostic填充值，不能冒充vdot高96位清零的证明。

验证工具在初次检查中出现两类问题并修正：资源子模块误按根文件归档；波形总线名含位宽后缀且当前提交信号不在历史DPIC层级。保留失败日志，重新按锁定子模块检查资源、保留原始FST名称/数据并按本次层级采样。最终来源/产物门禁通过；真实失败退出码使旧receipt消失、忽略路径中的资源头文件被拒绝并恢复、不同优化profile缓存被拒绝且原仿真器摘要不变，均有实际负控记录。

归档见 [本轮证据](../evidence/t04-current-core-20261013/README.md)。原历史证据保持。正常FIR-only冷构建入口尚未在第二个干净副本完整复现，本次成功路径明确为已绑定FIR恢复→独立转换→Clang全量编译→真实运行；不以这一结果关闭非作者/全队复现或环境完全等价验收。真实团队标识、成员复核和视频仍待完成。

下一阶段推进T10的准确译码、VS Off、VL/v0物理依赖、执行资源、写回与成功退休置脏，随后T11运行真正的vdot guest DiffTest。当前不报告vdot全核通过或性能优化完成。
