# 运行日志

原先索引的 **5,356 个日志文件全部保留**；另外补入 1,199 份文本/状态日志，共 6,555 个日志文件，并保留 3,124 份命令、配置、身份、结果或校验记录。

它们按原字节放入 7 个独立 ZIP 文件，每卷可直接打开，成员保持原路径。日志中的版本标识记录了每次运行时的源码、配置和工具身份。

- [完整索引](index.tsv)：类别、原路径、ZIP 文件、字节数和 SHA-256。
- [机器可读清单](manifest.json)：同时保留来源 Git blob 和固定来源提交。
- [阶段一常用记录](stage1/)：hello/vadd 摘要、工具版本、配置和事件 CSV，可直接打开。
- [最终组合结果记录](final-result/record.json)：最终硬件与软件组合的验收运行记录。

从仓库根目录运行：

```bash
python3 -B submission/logs/read_log.py list --contains stage1
python3 -B submission/logs/read_log.py show team/evidence/model-20261012/check.log --head 40
python3 -B submission/logs/read_log.py verify
python3 -B submission/logs/read_log.py restore --to /absolute/new/log-view
```

`show` 自动解开 gzip 供阅读，`verify` 按原始存储字节校验。`restore` 建议恢复到仓库外的新目录，已有的不同文件不会被覆盖。

通过、失败、取消、中断的日志都按同样规则完整保留。
