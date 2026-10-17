# T15 跨平台复核与历史修复

2026-10-17，正式 unit-02 的原始 Linux 重算、压缩归档 Linux 重算、Windows 离线重算均通过 T15_OFFLINE_RECHECK_PASS，最终 Linux/Windows 回执解析后相同。正式源码 65f6159e305adc10b4f8bd67812f3a6460ccf360。

初版 unit-01 的硬件/模型及 Linux 核验通过，但 Windows manifest 重生成失败。history 保留错误日志、旧生成器/清单及初版 Linux 回执；修复将来源路径改为 POSIX 格式，四份数值输入及预期结果文件完全不变。正式两配置硬件验收在修复后重新执行，不能用旧回执替代新版本。

windows-command.json 保存实际 Python 版本、运行命令和退出码；verification-provenance.json 固定最终归档及两个回执摘要。Windows 第一次外层日志捕获还遇到终端编码问题，后续以原始字节保存日志，并显式使用 UTF-8 子进程，保留了真实的路径分隔符失败原因。

离线核验只复算记录，没有重新运行硬件；模型复核不是成员人工 ACK。回归/图表/物理时序等范围以 T15 报告为准，本轮没有新 ISA 或全核 int16 支持。
