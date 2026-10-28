# clean-02 浅克隆元数据恢复

范围固定为 clean-02、source commit c823a8786e052c6e26f6915563c42b6d730dd8e3。本工具不改 MAIN、冻结 clean_prepare.py、prepare-state.json、任何源码、对象库、HEAD 或 index；不 fetch，不重用失败 clean-01 的生成物。

根因：从 MAIN linked worktree 做本地 clone 时，目标漏带 common Git 的真实 shallow 文件，导致 mill VcsVersion 遍历不存在的浅克隆边界父提交。已存在 shallow 可能被 Git 合法裁剪/去重/排序，按边界集合子集和真实 commit 对象检查，不覆写它。

执行前提：clean-02/checkout/prepare-state.json 已完成133仓库；实际修复前硬件 source/build 和 source/out 尚不存在。工具先检查全部133再执行唯一可写动作：目标主SOURCE没有shallow时，按字节独占创建 .git/shallow，内容必须匹配源真实SHA f785f2b3aead4449129beede03711c25f57349392c41ea41e25b4d1a7f0afcbc 和唯一边界16ae9ddc…；异常缺口和已有外国边界直接拒绝。

## 主 Agent 执行

以下命令未由子 Agent 执行。每个receipt必须是不存在的新文件。

~~~bash
WORK=/home/riscv/riscv-lab/software-import-20261026
TOOL="$WORK/reviews/clean-shallow-repair-01/restore_shallow.py"
PREPARE="$WORK/clean-02/checkout/prepare-state.json"

python3 -B "$TOOL" --prepare "$PREPARE" \
  --stage after-prepare --action plan \
  --receipt "$WORK/clean-02/shallow-plan.json"

python3 -B "$TOOL" --prepare "$PREPARE" \
  --stage after-prepare --action apply \
  --receipt "$WORK/clean-02/shallow-repair.json"
~~~

apply 完成后所有133仓库 rev-list HEAD必须成功；source Git HEAD/index/shallow 与检查前完全相同；目标只有主SOURCE shallow可以增加，目标HEAD/index不变。保存完整源/目标SHA、原clone receipt、边界commit存在证据、前后遍历结果、所有只读Git命令。

在 clean_support 真正PASS后检查全部145仓库（此阶段只读，无任何repair）：

~~~bash
python3 -B "$TOOL" --prepare "$PREPARE" \
  --support "$WORK/clean-02/support/repositories.json" \
  --stage after-support --action plan \
  --receipt "$WORK/clean-02/shallow-after-support.json"
~~~

该阶段允许硬件build/out已存在，因为没有写入动作；--action apply被明确禁止。所有已有目标边界必须是源边界子集，各边界对象为commit，全部目标HEAD遍历成功。

## 已做的检查与限制

- readonly-existing-clone-test.json：对保留的clean-01实际133仓库运行相同只读inspect逻辑，全部通过，仅主SOURCE被识别为待修复；未执行apply，也没有修改失败现场。
- help.txt：CLI帮助exit0。
- 实际clean-02 plan/apply/145仓库验证尚未执行，等待主Agent调用；不据只读测试声称已修复。
- 外部receipt和工具SHA须并入本轮provisioning证据，并随干净复现材料归档；不替换冻结prepare记录。
- 保留源shallow原始重复行，不人为宣称完整历史。下载Git对象缓存和浅历史继续保留属于同机复现范围。
