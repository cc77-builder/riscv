# 配置复用：数据集与尺寸扩展

[结果](RESULT.md) · [完整记录](record.json) · [扩展合同](tools/expansion-v1/CONTRACT.md) · [源文件映射](source-snapshot.json)

本目录保存24图/33进程扩展的工具快照与精简证据。实际输入和原始日志位于记录所列WSL路径；完整trace以本地逐文件压缩归档保存，日常仓库不收构建目录或波形。

tools/expansion-v1 与 tools/adapter-v3 的相对层级保留。复跑需要完整香山源码、固定 clean identity 与其物理依赖，以及新的输出路径；快照本身不是可脱离环境执行的便携工程。root-control 与 evidence 的真实命令记录原始工作目录。

本次仅扩展数据集与尺寸，不自动切换默认入口，不上传GitHub。
