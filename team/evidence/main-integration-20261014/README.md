# main 本地整合检查（2026-10-14）

对应[分支对比与进度整合](../../docs/main-integration-20261014.md)。本地 main 从 `5389bde79` 快进到本地 James_Hotten 的 `9bb544812`，整合时完整Git树相同。随后只增加文档和本记录，不修改硬件或运行脚本。未推送远端 main；此前删除的 dev 不重建。

- `commits.txt`、`changes.txt`、`diff-summary.txt`：来源交付提交与完整528文件差异。
- `source-binding-check.json`：当前规范化硬件编译输入与T10冻结包一致，440项根输入、126个子模块版本匹配；仅此记录不替代全依赖字节审计或重新仿真。
- `inherited-archives.json`：12份既有归档、898个文件逐项SHA256核对。
- `python-tests.log`、`python-tests.status`：本次Windows Python实际运行日志，33个方法通过、退出0。包括优化模式与实际产物路径绑定的拒绝场景。
- `integration-check.json`：整合检查结果，明确重型仿真没有重跑、T11与成员验收没有完成。
- `delivery-check.json`：后续文档链接、交付范围、继承运行检查器字节核对结果。
- `verify-main-integration.py`：本次检查工具原件；使用本机`team/out/t10-source-pack-20261014-v5`对照，复现须准备该包。其HEAD/树等值检查用于记录快进完成的时刻，新增文档提交后应针对该来源提交复现，不能把当前提交误认为当时整合HEAD。

6项原Scala/RTL单元/lint、20项真实全核DiffTest、三组24项普通vadd和波形材料按相同源码与原始日志继承。本轮新运行仅为Python回归；历史日志保持原样，不写成main当天重跑。

`archive.sha256`记录本目录除自身外所有文件的原始字节摘要；`.gitattributes`禁止换行转换。
