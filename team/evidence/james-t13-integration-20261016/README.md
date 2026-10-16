# T13 本地整合复核证据（2026-10-16）

代码来源 `46b6715da`（完整新验证）及 `e967f207f`（固定 seed 修复后复验）。本次新增全核运行为 **0**。详细发现和判断见 [整合报告](../../docs/james-t13-integration-20261016.md)。未推送远端，main 未改动。

- `runs.json` / `final-runs.json`：实际命令、退出码、预期退出码和耗时。前者记录157主机测试、35模型测试、T13三模式测试、真实C判定器、9镜像交叉编译/ELF核对及Scala编译；后者记录最终seed修复后的三模式各23项测试及归档复算。
- `*.log.gz` / `raw-logs.json`：无损原始执行日志、解压摘要和长度。
- `source-binding.json` / `final-source-binding.json`：测试时源码SHA-256与提交；`modules.json` 固定126项依赖。最终504项代码与Git字节一致，工具README后续仅更新说明。
- `integration-audit.json`：两侧历史证据不变、生产源码相同、main和测试源码核对。两侧证据有重叠，2109与2299不可相加成唯一文件数。
- `t13-host-judge.tar.gz`：四组原生/UBSan共8次真实C判定器输出、源文件和可执行文件。
- `t13-fresh-stream.tar.gz`：9个新编译镜像，包含source、data、bin、ELF、构建回执和日志；省略objects。镜像仅编译检查，没有启动EMU。
- `t13-final-replay.tar.gz`：加强校验器对来源归档的全量复算输出；13校准窗口、126有效运行、108功能调用、1404性能窗口，结果与历史一致，`hardware_rerun=false`。
- `bundle-files.json`：三个压缩包内每个文件的原始摘要和长度；`file-manifest.json` 固定本目录全部其他文件。
- `validate-native.py` / `validate-final.py` / `package-evidence.py`：本机实际使用的执行/归档脚本，包含固定绝对路径；用于记录流程，不是可移植安装器。

在任意具有 Python 3.10+ 的检出中验证本包（不执行包内程序、不启动硬件）：

```bash
python3 -B team/evidence/james-t13-integration-20261016/verify.py
```

重新核对当前T13逻辑与来源证据，使用未存在的输出目录：

```bash
PYTHONOPTIMIZE=2 python3 -B -m unittest discover -s team/workloads/vdot-perf -p 'test_*.py'
PYTHONOPTIMIZE=2 python3 -B team/workloads/vdot-perf/verify_archive.py \
  --archive team/evidence/t13-performance-20261015 --output /tmp/t13-new-review
```

原始全核数据仍位于 `t13-performance-20261015`，没有改写。本包完整性清单不代替其来源真实性、团队人工复核或新硬件执行。复用已有WSL和工具链，本次没有安装新系统依赖。
