# T13 离线搬迁复核回执

2026-10-15：WSL Python 3.10 与原生 Windows Python 3.13 分别完成全包离线复算，均为 `T13_OFFLINE_REPLAY_PASS`，完整结果逐项一致。两平台各 18 项单元测试通过。命令和完整验收方法见 [主证据包](../t13-performance-20261015/README.md)。

- [WSL 结果](wsl-receipt.json) 与 [执行输出](wsl-replay.log)。
- [Windows 结果](windows-receipt.json)。Windows 命令使用 `python -X utf8 -B`；输出写入独立 Windows 目录。
- [交付检查](delivery-check.json)：校验器源码摘要、平台、最终清单摘要及 Git 字节一致性。

首次原生 Windows 复算在源码再生成摘要检查中拒绝了平台自动产生的 CRLF。现只对临时再生成的两份文本转为 LF 再核对，归档源码、日志、ELF 和性能数据均不改写。此修复后的完整复算已在两平台通过。

归档添加局部 `.gitattributes`，防止上层 `team/** text` 将压缩日志、ELF 或原始 CSV 自动转换换行。1473 个最终归档文件逐字节与 Git 暂存对象一致；核心 archive-files 包含 1456 条原始记录，其余为清单、说明、图形 QA 与补充诊断。

这些回执说明已归档运行可独立复算；没有再次运行硬件，不构成人工评审签字。本轮没有向 GitHub 推送。
