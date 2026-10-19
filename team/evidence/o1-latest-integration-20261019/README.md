# 最新O1整合验证

范围与限制见[整合报告](../../docs/o1-latest-integration-20261019.md)。

606项主机检查、35组实际编译Scala配置、三模式frames父级/4负控、最新两模式父级/7负控及事件开启父级通过。没有新全核运行。

`events-parent-01`保留本机Verilator位宽告警导致的失败；第二次按固定依赖表达式应用精确行级豁免，先lint后构建。`host`保留初次测试工具/fixture失败与最终回执。

`source-snapshot.json`和tar保存整合源码及最终门禁工具；`build-binding`保存受测源码包身份及补丁。父级构建中的源码快照先于部分工具门禁收紧，`compiled-hardware-identity.json`确认受测Scala/build.sc与最终源码一致；不把工具变动冒充重新仿真。

`review`保存导入归档完整性及36次历史观察日志/统计复算；这些属于原受测版本。`file-map.json`绑定保存日志的原始和压缩字节，`old-evidence.json`确认5套James旧证据未变；`files.json`封存本目录除自身外的文件。生成RTL、二进制和构建缓存留本机，未纳入Git。
