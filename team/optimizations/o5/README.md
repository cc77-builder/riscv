# O5 输入准备：当前 O2 的 G3 复现前提

本入口只整理当前机器的冻结输入就绪情况。它不构建 RTL/EMU、不运行模拟器、不生成性能结果，也不完成 O5/T17、G5 或成员人工 ACK。O1/O2 默认开关保持关闭。

## 使用

从 Linux 完整 checkout 根目录运行，指定准备复现的 **40 位提交 SHA** 和 checkout 外尚不存在的结果文件：

```bash
python3 -B team/optimizations/o5/preflight.py \
  --source-commit <已提交候选的完整SHA> \
  --output /absolute/new/o5-inputs.json
```

可明确提供 `--t12-root`、`--t14-root`、`--dense-build`，含义与 O2 `fullcore/run_suite.py` 一致。脚本聚合缺失文件、SHA 漂移、错误参考库位置及 Git 工作区状态；每次使用新输出文件，保留失败尝试。退出码 0 为 `READY_INPUTS_ONLY`，1 为 `NOT_READY`。

`--source-commit` 必须是本机 HEAD。报告的 `source.checked_paths` 列出本轮检查的硬件源码与 G3/O5 工具路径；这些路径存在未提交/未跟踪文件时不得给出就绪结论。报告保存检查前的候选身份及脏文件列表，并比较检查前后的 Git 状态。为避免重复扫描历史证据，此处不检查其他文档路径；也**不覆盖忽略目录里的编译输入或子模块状态**。完整依赖门禁仍由后续构建入口执行。

## 冻结输入及限制

- 正常 NEMU、故障参考库、flash、hello、8 个功能/异常分片及各自数据/构建来源。
- 原 F2v 控制程序的完整冻结构建清单。
- dense batch128 的 bin、ELF、数据、源码与构建回执。
- NEMU 配置、原始源码清单，以及构建回执引用的源码、数据与 AM 库。

已知文件逐项核对；缺失构建回执时无法展开其传递依赖，因此报告中的清单计数只是当前可列出的前提，`inventory_expansion_complete` 会明确为 false。所有已知前提齐全后，调用 **现有 O2 严格 `preflight`**，进一步验证原始 NEMU、矩阵、控制与 dense 来源。只有该检查通过且候选 Git 状态干净时，才能报告 `READY_INPUTS_ONLY`。

故障参考库编译时绑定原正常 NEMU 的绝对路径：

```text
/home/riscv/riscv-lab/t12-regression-20261013/nemu/reference/build/riscv64-nemu-interpreter-so
```

复制相同二进制或修改命令行根目录无法解除这一约束；矩阵的历史数据/AM 来源也绑定原绝对路径。不要改冻结 SHA、回执或旧证据来制造可迁移性。可恢复完整原依赖；若确需新路径或重新构建输入，应使用另行版本化的新输入合同与新证据，并保留旧档案原样。

## 就绪后仍须完成

此入口**不核验**完整硬件编译输入、递归依赖 pin、原生工具链、两项补充诊断构建或受测 EMU。报告中相应 `*_checked` 字段均显式为 false；不能据 `READY_INPUTS_ONLY` 启用优化或宣称硬件通过。

随后按 [O2 复现说明](../o2/fullcore/REPRODUCE.md) 使用新的完整编译/依赖/原生工具合同构建当前源码；执行 core 与 supplements，再按任务范围完成匹配的性能、面积/时序复验。独立成员从最终候选执行 T17，人工 ACK 由本人填写。

2026-10-21 的开发期检查允许生成 `NOT_READY` 回执：候选仍有未提交修复时，报告中的 `source.head` 只代表检查基点，不代表这些修复已经提交。提交后必须以新 SHA 重新检查。

主机测试：

```bash
python3 -B -m unittest discover -s team/optimizations/o5 -p 'test_*.py' -v
```
