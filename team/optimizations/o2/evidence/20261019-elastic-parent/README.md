# O2 G1/G2 正式验收证据（2026-10-19）

本目录归档真实 RTL 构建、运行与离线复核材料。最终入口为 [工程记录](../../IMPLEMENTATION.md) 与 [机器结果](verification.json)。

- 正式 G1：g1-attempt-01，源码 a7d32f1。
- 正式 G2：g2-attempt-02，源码 3e4280d；完整逐拍日志为 result.log.gz。
- 最终离线复核：postcheck-02；源 SHA、命令、退出码及 41 项 host tests 均保留。
- 兼容性：compatibility-01 是默认/T14/O1 三模式 FU；parent-compatibility-01 是 T14/O1 真实父级。
- g2-attempt-01 虽运行通过，构建期间两处 C++ 观察负控代码曾短暂变动后恢复，只保留为探索记录；正式验收使用重新冻结后全新目录的第二轮。
- postcheck-01 是初版离线检查。独立复核发现其对 DIV 反压撤销 valid、切换场景精确集合检查不足，已修检查器、补反例，并在 postcheck-02 只读重审原始日志。未因此新增 RTL 样本。

[archive-manifest.json](archive-manifest.json) 记录每份原始文件与归档字节 SHA-256；大日志采用 gzip，解压后必须匹配 raw_sha256。精简不代表删除失败或探索记录。source-g2 固定正式 G2 输入源码，source-postcheck 固定最终离线工具；全源码和递归依赖模块身份另见各次 source/dependencies 清单。构建目录、可执行文件与生成 RTL 留在外部工作目录；其 SHA 和生成文件清单在本目录。

这里没有全核 EMU、NEMU DiffTest、应用性能或 PPA 结论。观察负控只验证检查器拒错能力，不等同于真实 RTL 故障注入。两项辅助计数 idle_clock_samples、cancel_idle_clock_on 由 live scoreboard 验收，没有再由独立离线工具重算。

本证据目录通过窄范围 .gitattributes 关闭文本换行转换和空白规范化；原始命令尾空格、源码快照原有空白及 gzip 字节均保留。归档验收会直接比较 Git blob 与原始 SHA，防止 Windows/WSL 换行转换破坏压缩日志。
