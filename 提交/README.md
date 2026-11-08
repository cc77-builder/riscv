# 提交材料

参赛队伍：啊对对对对

| 材料 | 位置 |
| --- | --- |
| 三阶段技术文档 | [技术文档/](技术文档/)：第一阶段执行日志与过程、第二阶段设计与基础测试、第三阶段协同仿真与性能分析，共 3 份 PDF；LaTeX 源码在 [submission/reports](../submission/reports/README.md) |
| 演示视频 | [项目演示视频/](项目演示视频/)：第一阶段环境部署与向量加法、第二阶段解题思路、第三阶段波形仿真与性能分析，共 3 个 MP4 |
| 证明材料 | [测试数据与运行结果证明材料/](测试数据与运行结果证明材料/请先阅读.md)：16 页[证明 PDF](测试数据与运行结果证明材料/测试数据与运行结果证明材料.pdf)、完整测试向量、原始日志、全核波形与数据索引；[审核说明](测试数据与运行结果证明材料/审核说明.md)给出文件校验、来源核对和离线复算结果 |
| 复现操作步骤 | [复现操作步骤.pdf](复现操作步骤.pdf)（[Markdown 版](复现操作步骤.md)） |
| 文件校验清单 | [manifest.json](manifest.json)：各文件大小与 SHA-256 |

全部原始运行日志（含失败记录）另按原路径归档在 [submission/logs](../submission/logs/README.md)，本分支上执行的检查见 [submission/VALIDATION.md](../submission/VALIDATION.md)。

视频和原始全核 FST 波形以 Git LFS 保存，克隆后运行 `git lfs pull` 获取完整文件。波形可用材料目录中的 [GTKWave 视图](测试数据与运行结果证明材料/vdot-positive-portable.gtkw)打开，证明材料的完整性用其中的 `python3 tools/verify_package.py` 检查。
