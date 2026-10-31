# P5 稳定版收口核查

[结论与必要缺项](RESULT.md) · [结构化结果](RESULT.json) · [冻结核查合同](CONTRACT.md) · [身份清单](evidence/audit.stdout.json) · [下一轮指令](NEXT_STEP.md)

此目录记录现有稳定版的只读收口，不是一个新的性能版本。[原 R5/G5 验收](../../acceptance/RESULT.md)、[原 C8 接入结果](../../package/c8/relink/RESULT.md)及各研究候选原记录保留。当前路线是仓库唯一的任务入口，本目录不维护另一份任务表。

audit.py 仅读取现有文件/Git、计算 SHA 并把 JSON 输出到标准输出；不导入构建器或调用目标运行器。它使用本机证据路径，搬迁时先核对身份，不直接改写旧清单。输出及退出码保存在 evidence。无需为了阅读结论再执行旧实验。

本轮无目标运行、无 RTL/构建、无 GitHub 写入；新结果不追加到实测档案，47条历史记录保持原字节。
