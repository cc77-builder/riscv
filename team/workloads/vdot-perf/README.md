# T13：精简 RVV / vdot 等价验证与周期测量

来源分支已将 T13 交付至 zjhwork@3b337a5；2026-10-16 本地 James 并入并加强验收门禁，未推送本次修改。阅读 [整合复核](../../docs/james-t13-integration-20261016.md)、[来源结果报告](../../docs/t13-performance.md)、[测量约定](../../spec/measurement.md) 和 [历史证据包](../../evidence/t13-performance-20261015/README.md)。

| 文件 | 用途 |
|---|---|
| `generate.py` | 固定数据与配对计划、5/7/14 条 RVV 基线、显式汇编、全宽黄金结果 |
| `main.c` | 完整 32 寄存器、CSR、循环次数、内存结果和 canary 判定 |
| `campaign.py` | 独立 AM 构建、单核 EMU 批量运行、命令/版本/原始流回执 |
| `check.py` | 源生成一致性、ELF 常量、逐指令退休及计数器采样核对 |
| `reference.py` | 固定 NEMU 的 10,022 输入精简基线检查，仅参考层 |
| `host_judge.py` | 编译真实 C 判定器，原生与 UBSan 错误位翻转 |
| `test_check.py`、`test_validation_gates.py`、`audit_negatives.py` | 检查器边界、回执缺失/矛盾、优化模式、来源变化与实际工件临时损坏测试 |
| `analyze.py` | 先验收全部计划，再计算配对周期比和确定性重放 |
| `archive.py`、`verify_archive.py` | 原始字节无损归档、可搬迁离线复算 |
| `report.py`、`plot.py` | 从已验收数据生成报告和图，拒绝未验收数据 |

Python 验收工具只用标准库（3.10+）；C 主机检查需要 GCC。绘图单独使用 Matplotlib 及图形检查工具，不是离线数据验收的依赖。

从仓库根目录复核：

```bash
python3 -B -m unittest discover -s team/workloads/vdot-perf -p 'test_*.py' -v
python3 -B team/workloads/vdot-perf/verify_archive.py \
  --archive team/evidence/t13-performance-20261015 \
  --output /tmp/t13-review-new
```

重新仿真见 measurement.md。完整矩阵原始布局构建用 `campaign.py build`；正式访存修正版另加 `--stream-only`，以共享 64 字节对齐输入。最终 `analyze.py` 同时指定这两组镜像和运行目录，并按预先确定的规则排除原访存数据。所有输出目录要求不存在，不覆盖历史记录。

构建前提交源码并保持工作区干净；AM 必须是固定的 `086a238062fdfb3281b745a537b361983d0154b5`。每个镜像保留 `source/` 快照、生成输入及 bin/ELF/manifest 摘要，构建前后核对源码与 AM。运行前后核对 EMU、参考库、flash、镜像及构建回执；变化会留下失败回执并拒绝成功汇总。验收要求明确 DiffTest、128MB、单核/单线程、`--seed=1`、完整原始流摘要，Python `-O`/`-OO` 不会关闭这些门禁。旧校准回执缺失元数据仅对七项固定原始文件摘要保留兼容，新回执不能靠删字段进入例外。

注意：`rdcycle` 本身没有被假定为序列化指令；这版香山的 fence 隔离经过事件校准。换核/换配置需重新确认，不能直接照搬本轮周期结论。确定性三次重放不是统计显著性。任何脚本均不推送 GitHub。
