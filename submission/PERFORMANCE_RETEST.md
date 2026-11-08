# 最终 O2 微基准重测

入口：`python3 -B team/workloads/unified-vdot/retest.py`，或 `bash submission/reproduce.sh perf`。
从发布仓库根目录在 Linux / WSL 原生文件系统运行。Python 3.10+；需要已准备的固定版 nexus-am、RISC-V GCC、最终 observe-profile EMU 和带 vdot 扩展的 NEMU reference。

本程序重新生成、编译并执行测试镜像，不读取报告中的周期作为结果。覆盖报告表 3-3 的 single、chain、batch、stream 四类微基准；不包含 C8 GEMV、O2 队列专项验收或综合时序。

## 先快速检查

```bash
export OUT=$HOME/vdot-retest-01    # 使用新的目录，不覆盖已有测量
export AM_HOME=/absolute/xs-env/nexus-am
export EMU=/absolute/path/to/emu
export REF=/absolute/nemu-vdot/reference/build/riscv64-nemu-interpreter-so
mkdir -p "$OUT"
python3 -B team/workloads/unified-vdot/retest.py build \
  --am "$AM_HOME" --mode smoke --output "$OUT/smoke-images"
python3 -B team/workloads/unified-vdot/retest.py run \
  --images "$OUT/smoke-images" --emu "$EMU" --reference "$REF" \
  --timeout 240 --output "$OUT/smoke-run"
```

快速检查只有一个镜像，检查真实 DiffTest、结果、退休指令和计数窗口。未传 `--emu-record` 时只用于检查工具链，结果中的 `hardware_identity` 为 null，不能据此宣称最终硬件性能通过。超时或缺少 T13 trace 均失败，原始日志保留；不能将超时视为 PASS。实际耗时取决于仿真器和主机。

## 正式重测

EMU 必须使用 `build_fullcore.py --profile observe` 构建。`--emu-record` 指向它产生的记录目录，内有 `hardware-inputs.json` 和 `build-state.json`。支持新的构建提交和新的 EMU 哈希：验证回执、二进制和发布源码的对应关系，不要求旧实验二进制。不要使用 `cost` profile，它不输出计数窗口 trace。

```bash
python3 -B team/workloads/unified-vdot/retest.py build \
  --am "$AM_HOME" --mode full --output "$OUT/images"
python3 -B team/workloads/unified-vdot/retest.py run \
  --images "$OUT/images" --emu "$EMU" --reference "$REF" \
  --emu-record /absolute/new/emu-record \
  --jobs 2 --timeout 1200 --output "$OUT/runs"
```

总共 16 个镜像：1 个 smoke、3 个功能检查、12 个性能镜像，按阶段通过后再进入下一阶段。每个场景每种方法有 3 个数据集 × 4 个正式窗口，同镜像比较 VDot 与 RVV。first/warmup 不计入平均值，加速比为 RVV 周期总和 / VDot 周期总和。默认每镜像最多 1200 秒，`--jobs` 仅控制并行进程数，不能保证整个测试在半小时内完成。

通过后输出 `PERFORMANCE_RETEST_PASS`，结果在 `$OUT/runs/analysis/`：

- `summary.csv`：四场景均值、范围和加速比。
- `samples.csv`：所有逐窗口数据，包括 first/warmup。
- `result.json`：检查范围、硬件身份、输入及原始日志哈希。

每个镜像独立保存 stdout、stderr、实际命令、退出码和检查结果。拒绝覆盖已有输出。NEMU 按既有 `artifact_guard.py` 检查来源，性能窗口按既有 `unified-vdot/check.py` 验证来源快照、ELF、DiffTest、完整结果、退休 PC/机器字、fence 与 CSR/global cycle 一致性；不使用旧 T12 单槽分析器。

## 对本次运行重新分析

输入镜像、EMU、NEMU 和回执保留在原路径时，可离线重新执行全部窗口检查：

```bash
python3 -B team/workloads/unified-vdot/retest.py analyze \
  --images "$OUT/images" --runs "$OUT/runs" --output "$OUT/reanalysis"
```

该步骤读取本次运行的原始 stdout/stderr，不会启动新 EMU。旧报告数字不作为验收断言；不同新构建的结果应保留并如实解释。
