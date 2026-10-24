# R3 交付复核

本目录是封存之后的交付回执，不纳入自身验证的 manifest。

- [cross-environment.json](cross-environment.json)：Linux／Windows 最终审计除原生路径外全部语义字段相等，输入保存字节及原始载荷身份相等。
- [archive-byte-linux.json](archive-byte-linux.json)、[archive-byte-windows.log](archive-byte-windows.log)：177 份载荷完整字节核验；复用现有 format-1 verifier，不代表新增 H1 资格。
- [metadata-windows.json](metadata-windows.json)、[原始输出](metadata-windows.log)：Windows 原生 Python 对 gzip 原文作完整控制／payload 重放与 8 类拒错。
- [tests-windows.log](tests-windows.log)：42 项检查器单测。
- Git 暂存字节的最后核验由同目录 `git-index.json` 记录；它不把自身的哈希循环写入自身。实际承载提交及推送结果由 Git 历史与 Issue #2 定位。

这些是本轮隔离父级证据的交付核对；没有新增 EMU、性能窗口或综合／STA 运行。
