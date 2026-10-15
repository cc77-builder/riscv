# James_Hotten 整合验证（2026-10-15）

本轮真实执行的主机/组件测试及历史归档复算。代码固定到 `e5df93c7b`，完成时 native 检出干净；后续仅新增报告与证据。结果见 [整合报告](../../docs/james-integration-20261015.md)。

- `runs.json`：每条实际命令、退出码、预期码、工作目录和耗时；负控的 exit1 是预期检错。
- `validation-source.json`：实际编译/检查输入、生成的四份 RTL SHA256、源码提交与结束状态；`modules.json` 固定126个依赖提交。
- `.log.gz`：完整原始输出压缩，`archive-manifest.json` 同时保存压缩文件与解压字节 SHA256。
- `branch-inclusion.json`：两仓库全部非main分支的固定提交均在合并历史中。
- `merge-preservation.json`：三个来源的933/798/820个归档文件分别保持同一Git blob（集合重叠，不是新增文件数）；生产源码与zjh固定来源一致。
- `zufan-offline-recheck.json`：274项归档摘要、两份tar可读性、历史源码重新生成190/199输入并逐片检查原始日志。未在本机验证原开发机上的EMU/工具二进制，也不是新运行。
- `validate*.py` 与 `recheck-zufan.py` 是本次执行记录，含本机绝对路径及新建目录要求；复现应换全新目录，不能覆盖本归档。

中间尝试：新增2项取消反例在修复前均未抛异常，修复后29项检查器测试通过。初次Windows主机检查155项有2个本机GCC子进程编译错误；最终规定的WSL/Linux环境157项全部通过。首次直接启动缓存Mill遇到Exec format error，改用Bash启动同一工具后构建通过。这些尝试不计为通过仿真。

新全核运行数 **0**。测试既有MinimalConfig真实FU/译码，并不替代EXU/ROB整体执行。trace开/关FU均通过同一6类控制测试，不能将其外推为全核trace开/关等价证明。历史117/control及190/199日志继续保留原来源。
