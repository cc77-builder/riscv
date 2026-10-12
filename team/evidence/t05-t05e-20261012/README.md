# T05/T05-E 本地验证证据

归档日期：2026-10-12（北京时间）。代码分支 `James_Hotten`，基准 Git 提交 `e27db6158c6a0e583342dbab0ec78bceff138d69`；实现文件当时未提交，以源文件摘要和工作区记录识别实际版本。原始日志均来自本次实际执行，没有使用单元测试的合成日志替代运行证据。

| 证据 | 实际结果 |
| --- | --- |
| [Python 检查](host/model-tests.txt) | 13 个测试方法通过；含完整随机 oracle、编码/状态、数据复现和严格日志判定 |
| [C 判定器检查](host/judge-tests.txt) | 18 项检查通过 |
| [QEMU 自测日志](qemu-selftest/run.log) / [退出码](qemu-selftest/exit-code.txt) | H00～H04 均通过，两项负控检出；退出 0；只证明 harness 自测 |
| [未扩展模式日志](qemu-unextended/run.log) / [退出码](qemu-unextended/exit-code.txt) | 合法 D00 被拒绝，程序退出 3；这份日志记录预期失败，不算 vdot 通过 |
| [香山目标编译](xs-build/build.txt) / [AM 提交](xs-build/am.sha) | 固定 nexus-am 构建 full ELF/bin 成功；未运行香山或 NEMU |
| [数据清单](data/manifest.json) / [异常子例](data/exceptions.json) | 48 定向 + 10,000 随机；裸机 80 合法/算术 + 35 异常子例 |
| [静态编码检查](encoding-review/review.json) | 717 个命名表项解析；10 个邻近字无已检查模式冲突，不替代真实译码运行 |

各运行目录保留源码、输入及二进制 SHA256，QEMU/编译器版本和当时工作区记录；SHA 文件中的绝对路径为原运行位置。二进制留在 `team/out/`，未作为源码产物纳入仓库。`archive.sha256` 使用归档相对路径，可在本目录检查归档完整性。本目录的 `.gitattributes` 保留原始证据字节，包括换行格式和工具输出的结尾空行，避免跨平台检出改变摘要。

本次执行入口（仓库根，Linux/WSL）：

```bash
bash team/scripts/vdot-tests.sh host
bash team/scripts/vdot-tests.sh virt-selftest
bash team/scripts/vdot-tests.sh virt-full-negative
AM_HOME=/home/amesotten/.cache/codex-t05/nexus-am-086a238 bash team/scripts/vdot-tests.sh build-xs full
```

AM_HOME 是此次固定提交的 Linux 缓存检出路径，其他成员换成自己的固定 nexus-am 检出。初评和检查边界见 [T05/T05-E 评审](../../docs/t05-t05e-review.md)。

尚未取得的证据：真正 vdot 的 standalone NEMU、RTL 全核 DiffTest、取消/配置依赖压力、故障注入与旧指令回归。不能因 QEMU harness 自测、模型正确或目标编译成功，就宣称这些验收通过。
