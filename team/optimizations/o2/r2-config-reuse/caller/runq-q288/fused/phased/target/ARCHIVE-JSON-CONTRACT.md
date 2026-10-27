# Phased 封存的 JSON 表示适配 v1

此适配只修复团队封存工具中的 Python tuple 与 JSON list 表示差异，不产生新目标实验或改变既有性能选择规则。

2026-10-26 13:59 首次封存被原 `split/archive.py` 的完整缓存比较拒绝。现场对 `build-03/elf-validation.json` 与重新执行的冻结 `verification()` 递归比对，只有 `phased_certificate.mode_phases` 下四个元素的 Python 类型不同：缓存为 JSON list，复算为 tuple；值依次为 `(8,8),(4,32),(8,8),(4,32)`。缓存 SHA256 为 `d3ab20bbb54d0ed6f878d804efa2ab5d6208b5d4a83470ecf7805761496f4d31`，全结构经 JSON 表示转换后完全相同。诊断及失败回执原件保留。

`archive_json.py` 继续调用原封存和 guard 引擎，并原样重新执行冻结 `verification()`。它严格要求上述单一字段是四个指定整数 tuple，只把它们表示为 JSON list；不从缓存复制值、不忽略字段、不使用近似比较、不修改源代码、缓存、ELF、BIN、原始日志或运行收据。其余结果原样传给原严格完整相等检查。改变任何模式值仍须拒绝；改变其他字段仍造成原完整比较失败。

原106项源码及原补充审计器继续保留。此适配和本文作为额外补充审计输入纳入哈希、归档 manifest 及 fresh-source 拷贝。隔离新进程执行同一适配，继续执行原八个拒绝根、依赖探针和完整原文结果相等判据。旧失败目录不覆盖，新封存使用独立 `*-02` 输出身份。此前 negative/recovery/replay 不重跑，guest预算和性能结论不变。
