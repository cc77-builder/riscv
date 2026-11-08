# 微基准性能重测

在新构建的最终 EMU 上重新测量第三阶段表 3-3 的四类微基准：单次点积（single）、256 次依赖链（chain）、128 次四路独立批量（batch）、64 次加载-计算-存储流（stream）。程序重新生成测试数据、编译镜像并运行 EMU，同一镜像内对比 VDot 与等价 RVV。

入口：`bash submission/reproduce.sh perf <build|run|analyze> ...`，即 `python3 -B team/workloads/unified-vdot/retest.py`。

## 准备

- Linux 或 WSL 原生文件系统，Python 3.10+。
- 固定版本的 nexus-am 和 RISC-V GCC（[复现操作步骤](../提交/复现操作步骤.md)第 3 部分）。
- 用 `bash submission/reproduce.sh build-emu --profile observe ...` 构建的最终 EMU 及其记录目录。observe 配置会输出计数窗口事件，`cost` 配置不输出，不能用于重测。
- 带 vdot 扩展的 NEMU reference（复现操作步骤第 5 部分）。

```bash
export OUT=$HOME/vdot-retest-01           # 新目录
export AM_HOME=/absolute/xs-env/nexus-am
export EMU=/absolute/path/to/emu
export REF=/absolute/nemu-vdot/reference/build/riscv64-nemu-interpreter-so
mkdir -p "$OUT"
```

## 第一步：smoke

只构建并运行 1 个镜像，确认工具链、DiffTest、结果比对、退休指令数和计数窗口都正常，单个镜像在常见主机上约 1～2 分钟。

```bash
bash submission/reproduce.sh perf build --am "$AM_HOME" --mode smoke --output "$OUT/smoke-images"
bash submission/reproduce.sh perf run --images "$OUT/smoke-images" --emu "$EMU" --reference "$REF" \
  --timeout 240 --output "$OUT/smoke-run"
```

通过时输出 `SMOKE_RETEST_PASS`。smoke 不传 `--emu-record`，结果里不记录硬件身份。

## 第二步：完整重测

```bash
bash submission/reproduce.sh perf build --am "$AM_HOME" --mode full --output "$OUT/images"
bash submission/reproduce.sh perf run --images "$OUT/images" --emu "$EMU" --reference "$REF" \
  --emu-record /absolute/new/emu-record --jobs 2 --timeout 1200 --output "$OUT/runs"
```

- 共 16 个镜像：1 个 smoke、3 个功能检查、12 个性能镜像，前一阶段全部通过后才进入下一阶段。
- 每个场景、每种实现 3 个数据集 × 4 个正式窗口；first 和 warmup 窗口不计入。加速比为 RVV 周期之和除以 VDot 周期之和，窗口数相同，等于平均周期之比。
- `--emu-record` 指向 `build-emu` 的记录目录（含 `hardware-inputs.json`、`build-state.json`），程序核对构建回执、EMU 二进制与发布源码的对应关系，并把硬件身份写入结果。
- 每个镜像默认超时 1200 秒，`--jobs` 可取 1 或 2。

通过时输出 `PERFORMANCE_RETEST_PASS`，结果在 `$OUT/runs/analysis/`：

| 文件 | 内容 |
| --- | --- |
| `summary.csv` | 四个场景的均值、范围和加速比，对应表 3-3 |
| `samples.csv` | 全部逐窗口数据，含 first/warmup |
| `result.json` | 检查范围、硬件身份、输入与原始日志的哈希 |

每个镜像单独保存 stdout、stderr、实际命令、退出码和检查结果，输出目录已存在时拒绝运行。

## 检查内容

- NEMU reference 由 `team/scripts/artifact_guard.py` 核对来源。
- 每个窗口由 `team/workloads/unified-vdot/check.py` 核对：源码快照、ELF、DiffTest、完整 128 位结果、退休 PC 与机器字、fence，以及 CSR 周期与全局周期一致。
- 解析的是最终两槽硬件输出的 O2 事件。

## 重新分析已有运行

镜像、EMU、NEMU 和记录目录保持原路径时，可以只读日志、不启动 EMU，重新执行全部窗口检查：

```bash
bash submission/reproduce.sh perf analyze --images "$OUT/images" --runs "$OUT/runs" --output "$OUT/reanalysis"
```

## 本分支上的验证

2026-11-08：重测程序 10 项单元测试通过；16 个镜像在 Linux 上构建成功；smoke 镜像在本机 EMU 上运行两次，均为 `SMOKE_RETEST_PASS`，日志离线重新分析结果相同。记录在 [verification/performance-retest-20261108/](verification/performance-retest-20261108/)。
