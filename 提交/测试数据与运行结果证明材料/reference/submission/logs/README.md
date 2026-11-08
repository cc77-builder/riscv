# 运行日志

原先索引的 **5,356 个日志文件全部保留**；另外补入 1,199 份文本/状态日志，共 6,555 个日志文件，并保留 3,124 份命令、配置、身份、结果或校验记录。

它们按原字节放入 7 个独立 ZIP 文件。每卷可直接打开，成员仍使用原路径；不包含历史源码快照、旧程序发布包或开发计分板。日志里的版本标识用于解释当时的运行条件，不表示这些旧代码版本仍在交付目录中。

- [完整索引](index.tsv)：类别、原路径、ZIP 文件、字节数和 SHA-256。
- [机器可读清单](manifest.json)：同时保留来源 Git blob 和固定来源提交。
- [阶段一常用记录](stage1/)：hello/vadd 摘要、工具版本、配置和事件 CSV，可直接打开。
- [最终组合原结果记录](final-result/record.json)：原运行资格；不作为本轮重新仿真结果。

从仓库根目录运行：

```bash
python3 -B submission/logs/read_log.py list --contains stage1
python3 -B submission/logs/read_log.py show team/evidence/model-20261012/check.log --head 40
python3 -B submission/logs/read_log.py verify
python3 -B submission/logs/read_log.py restore --to /absolute/new/log-view
```

`show` 自动解开 gzip 供阅读；校验针对原始存储字节。恢复建议使用仓库外的新目录，避免把旧日志目录重新展开到清爽的提交树中；已有不同文件不会被覆盖。

通过、失败、取消、中断的日志全部使用相同保留规则。日志复读与原始波形截图都不能写成本轮新仿真。未被原 Git 提交跟踪的本机外部运行目录保持原处，本包不声称收录整台计算机上的所有输出。
