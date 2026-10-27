# 独立统计复算

`recovery-statistics-input.json` 来自已通过的 v2 恢复轮。`uart` 保留原日志的 UTF-8 字节（含255个CR，共5401B），SHA256为 `08326d1312b8bd75f6966720d495c55b241c20f259a82613e179561cc718f2e8`；plan/rows/selection为解析后的JSON结构，另记各原文件SHA。

`statistics-independent.py` 只用Python标准库，从252条连续SW重建并核对计划，独立计算正式样本、六对接口、锚点和六格门槛，最后才对照附带selection。报告没有导入项目selector，也没有访问原RETIRE/CSR/O2文件。完整来源审计见 [v2归档](../split-input-v2/archive-manifest.json)。

**复算时先将本目录完整复制到仓库外的新目录，再运行 `python3 -B statistics-independent.py`。** 脚本默认在同目录写 `statistics-independent.json`，不要在冻结证据目录原地执行。新目录中的报告会记录新的本地路径；原始输入SHA及统计结论应相同。

独立报告仅确认恢复轮统计，不代替完整campaign、重放或原始日志审计，也不产生新的EMU或性能样本。
