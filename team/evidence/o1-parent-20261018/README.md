# VFEX4 父级与时钟优化证据

工程结论及限制见[报告](../../docs/o1-parent-20261018.md)。仅在 James_Hotten 本地工作，未推送或修改 main。

- `verification.json`、`mode-0/1/2.log`：真实默认/T14/O1父级运行、事务守恒与时钟结果。
- `harness-01.log`：旧生产RTL、已校准测试入口的观察运行，三路取消后空闲时钟各192个。
- `clock-repro-01.log`：相同旧RTL在严格空闲时钟检查中失败，exit=1。
- `tested-inputs.tar.gz`、`source-binding.json`：第7次最终运行的实际输入字节、初始构建副本绑定、126项依赖与当前编译输入摘要。原快照之后的 ExeUnit 修复和测试入口调整均由最终字节单列，不冒充原快照。
- `validation.tar.gz`：7次完整尝试、旧RTL复现和调试运行；含日志、源码快照、RTL、二进制与向量，省略可重建的C++对象文件。最终输入归档单列；此前失败输入保留。
- `production-and-build.patch`：相对2403719bc的生产源码与build.sc差异；新增适配器/测试源码在输入归档中。
- `contract.log`：17项主机合同检查。`workspace-match.json`核对436项当前编译输入和10项测试输入；规范化Git文本换行，不修改归档原字节。
- `dependency-check.json`：126项依赖的版本、已跟踪文件和未跟踪输入复核均通过。`paired-clock-check.json`确认修复前后使用相同测试程序与向量。
- `archive-replay.json`、`replay.py`：固定归档摘要后，在新目录重跑三种二进制、旧RTL失败与四类负控；全部符合预期。入口为 `python3 -B team/evidence/o1-parent-20261018/replay.py --output /absolute/new/directory`。这是二进制复验，不是独立源码重建。
- `files.json`：目录载荷完整性摘要。真实性以已审阅的Git版本为准，自签摘要不授予执行任意源码的权限。

`package.py`与两个`*-local.sh`是本次归档环境记录，包含本机缓存路径。常规重跑用仓库的 `team/optimizations/o1/check-parent.sh`，设置现有Java/Mill/firtool/Verilator工具后选择新的输出目录。三模式均通过实际lint；唯一局部位宽豁免的理由与表达式守卫见报告及`parent.vlt`。

本轮没有新全核运行、CPU性能A/B、STA/PPA或功耗测量。O1默认关闭；旧T12/T13观察器不支持重叠事务的保护未放宽。
