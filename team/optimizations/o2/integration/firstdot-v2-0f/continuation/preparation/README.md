# clean-02 浅克隆元数据恢复记录

本目录保存一次实际环境修复，不修改生产 RTL 或冻结的 T17 clean_prepare 工具。

clean-01 的硬件构建在 Mill 读取 Git 版本时失败。源仓库是 linked worktree，
浅克隆边界位于 common Git 目录；本地 clone 漏掉了该记录。
缺失父提交原本就在浅克隆边界之外，不能据此判断源代码缺失。

在新的 clean-02 中，先核对 133 个独立仓库，仅向主 SOURCE 的独立 .git/shallow
补入原来源的精确字节；没有修改源缓存、HEAD、index 或已存在的目标边界。
Git clone 可合法裁剪不可达边界、去重或排序，因此已存在文件按边界集合包含关系、
对象身份及实际 rev-list HEAD 成功核验，未为追求字节相同覆写它们。
新 NEMU/AM/klib 构建后又完成 145 个仓库的只读复核。

- [固定恢复工具](restore_shallow.py)：仅服务指定 clean-02/c823a878 源身份，不能不加分析用于其他目录。
- [原工具说明及命令](DRIVER_README.md)、[实际执行命令](commands.json)。
- [结果摘要](execution-summary.json)、[归档输入清单](archive-inputs.json)。

实际执行的工具、原始回执保留在 software-import-20261026 原始根，见清单中的绝对路径与 SHA；
此处脚本为同字节归档，不伪写实际执行位置。硬件构建与目标运行状态另见上级[组合结果](../../RESULT.md)；
元数据修复通过不代表新 EMU 或目标回归通过。
