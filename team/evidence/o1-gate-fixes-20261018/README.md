# O1门禁修复证据

结论与限制见[修复报告](../../docs/o1-gate-fixes-20261018.md)。本目录独立于原始硬件归档，未新增CPU执行；O1默认关闭。

- `checker-sources.json`、`checker-sources.tar.gz`：修复后检查器、入口及相关测试的源码和SHA绑定。
- `tests-final.json`：七套件合计504项；采用初次六套件及最后193项项目回归，不重复计入定向测试。
- `host-tests-01/`：初次七套件502项原始回执；`attempts/project-final.log`为最终193项项目回归。
- `nested-final/`、`review/`：最终嵌套依赖输入检查及真实克隆负控。
- `validation/`：13次原CPU运行复算、15类旧负控、24项FTQ新负控、真实输出保护与126个依赖检查。
- `parent-replay/`：8次真实父级二进制执行日志及回执。
- `archive-recheck/`：本目录`recheck.py`实际成功执行的回执与日志；该入口不执行EMU或父级二进制。
- `attempts/`、`drivers/`：初次失败及后续成功记录、验证驱动；失败原因在报告中说明。
- `old-evidence-check.json`：4套旧证据按各自原始清单复查结果。
- `files.json`：除自身外本目录所有文件的SHA256及大小。

在仓库根目录执行 `python3 -OO -B team/evidence/o1-gate-fixes-20261018/recheck.py --output /tmp/o1-gate-recheck-new`。目录必须全新，当前检查器须匹配封存清单。历史归档保留各自原来源绑定，不能把本轮复算视为新硬件运行或性能提升。
