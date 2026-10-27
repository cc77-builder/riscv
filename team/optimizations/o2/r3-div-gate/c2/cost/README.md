# C2 同约束成本筛选

本轮固定 C2 提交 6704ce3502a7235cdb81697638c01ed23f6914f6，对照 0f12df675378556670afd0dd2153f47fcb330610；不修改生产 RTL，不上传 GitHub。

- CONTRACT.md：执行前冻结的边界、五档条件、45 项路径与面积/控制门槛。
- run_ppa.py：校验源码/依赖/工具/基线身份，生成生产父级、综合并运行五档 STA。
- screen.py：对两版各做五档控制端点 STA，按冻结门槛筛选，区分工具成功与筛选通过。
- archive.py：封存实际命令、输出、来源和独立复核材料。
- RESULT.md：完成后写入实际结论、数据和适用边界。
- evidence/20261025-cost/manifest.json：完成后生成的只读证据清单。

只有成本筛选和独立复核同时通过，才执行新的全核构建、NEMU 差分回归及周期比较。局部功能 PASS、主机准备检查或脚本准备完成均不能替代这些门槛。既有 C2-local 档案保持历史状态，本轮单独新增成本记录。

结果属于相同边界、相同工艺库和相同约束下的布局前工程筛选，不是官方评分、整核面积、布局后时序或功耗测量。

## 已完成状态

C2_SCREEN_REJECT：20/45 项通过，25 项超限。保留 0f，不进入本版 C2 全核/周期。[结果](RESULT.md)、[路径解释](PATH_INTERPRETATION.md)、[证据](evidence/20261025-cost/manifest.json)。

verify_archive.py 校验全部封存载荷，并可用 --output 解压到新目录。audit_portable.py 从解压后的 baseline、work/screen-01、库、候选源码和原 manifest 复算，无需 EDA；参数说明见解压后的 work/independent-review/PORTABLE.md。Linux/Windows 两份实际调用与退出码均在 reviews/。报告中的“审计PASS”表示复算可信，候选是否通过仍看 screening_pass，本次为 false。

证据包携带原基线 143 份成本文件和引用 manifest，所以便携复算无需访问原机器路径。解压文件约 0.83 GB；日常提交只保留本目录中的压缩证据，不加入解压缓存。run_ppa.py/screen.py 要求新的输出目录，不能覆盖已有实验。以后变更 RTL 或合同须另建候选身份，不能用重新运行本版覆盖失败。
