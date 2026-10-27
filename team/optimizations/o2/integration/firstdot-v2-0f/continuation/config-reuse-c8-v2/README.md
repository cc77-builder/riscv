# 8×32配置复用普通C验证

[结果](RESULT.md) · [完整数据](record.json) · [合同](tools/c8-v2/CONTRACT.md) · [实际公共源码](public/) · [复制哈希](source-snapshot.json)

本目录包含实际已验证的gemv.S/gemv.h、普通C调用程序及48用例、工具快照和精简证据。完整O2日志、构建物与旧失败封存在本地archive，路径和SHA见record.json。材料快照依赖完整香山源码及固定物理输入，不是可单独执行的便携工程。

原运行入口为record.json记载的c8-v2/c8.py --output <新的输出目录>，通过taskset限定CPU；不复用已有输出。V1失败源码保留，仅供追溯。所有已归档工具/源码和原始运行输出保持只读；新试验另设输出。

[收尾回执映射](postprocess-receipts.json)保留首次归档拒绝、修复后归档、材料生成与最终QA的真实命令及退出码；核心69文件快照和第26条记录保持不变。
