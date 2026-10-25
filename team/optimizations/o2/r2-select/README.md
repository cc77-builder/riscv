# R2-SELECT：查询和导出已合格的原 GEMV 镜像

本模块把 S1 v2 的完整矩阵转为可复算的八个 shape/scope 选择，并把每个选择绑定到三数据集的原 ELF/BIN、case、符号和正式窗口。最快 RVV、S0 vdot 回退与全部候选同时保留。详见 [合同](CONTRACT.md)与[实际验证结果](RESULT.md)。

入口 `selection.py` 提供 `export`、`verify`、`resolve`。它复制完整原镜像；原镜像仍按原计划运行四个 case。查询结果中的周期来自原合格窗口，不是新的目标机调度器性能。

## 使用

在 Git 与 Python 均能正常访问的完整仓库检出中执行。依赖为 Python 标准库、Git、已入库的 S1 v2 归档和资格报告；这里不要求重新编译硬件或启动 EMU。下例的 `RESULT_ROOT` 应指向新的实验输出父目录。

```bash
REPO=$(git rev-parse --show-toplevel)
RESULT_ROOT=/path/to/new-r2-selection-output
mkdir -p "$RESULT_ROOT"

python3 -B "$REPO/team/optimizations/o2/r2-select/selection.py" \
  --repo "$REPO" --action export \
  --bundle "$RESULT_ROOT/original-images" \
  --report "$RESULT_ROOT/export.json"

python3 -B "$REPO/team/optimizations/o2/r2-select/selection.py" \
  --repo "$REPO" --action verify \
  --bundle "$RESULT_ROOT/original-images" \
  --report "$RESULT_ROOT/verify.json"

python3 -B "$REPO/team/optimizations/o2/r2-select/selection.py" \
  --repo "$REPO" --action resolve \
  --bundle "$RESULT_ROOT/original-images" \
  --shape 8x32 --scope endtoend --dataset 0

python3 -B "$REPO/team/optimizations/o2/r2-select/selection.py" \
  --repo "$REPO" --action resolve \
  --bundle "$RESULT_ROOT/original-images" \
  --shape 4x13 --scope endtoend --dataset 2 --role s0_vdot_fallback
```

默认归档为仓库中的 `team/optimizations/o2/r2-vector-accum/evidence/merged-v2`。可通过 `--archive` 指向同一归档的另一完整副本，固定 manifest 身份与所有字节仍要一致。`--report` 可省略，JSON 结果始终打印；指定报告必须是新文件、位于导出包和固定输入树之外。

`resolve` 返回获选实现、原 12 窗口统计、实际可访问的 ELF/BIN/manifest/运行回执路径及符号信息；它不提供未经实现或验收的“只跑这一方法”仿真参数。移动导出包后仍可使用相同命令验证，但需要源归档、固定资格报告和匹配仓库。

## 验证入口

```bash
python3 -B -m unittest discover \
  -s team/optimizations/o2/r2-select -p test_selection.py -v
```

测试使用真实 S1 v2 归档，在临时输出中导出和篡改副本；不改冻结输入、不启动 EMU。可用 `R2_SELECT_ARCHIVE` 指定同身份的另一归档副本。性能取舍与新执行路径的验证边界以合同为准；原资料入口为 [S1 验证](../r2-vector-accum/VALIDATION.md)和 [S2 固定布局/强 RVV 结果](../r2-safe-tail/FIXED_RESULT.md)。

## 新增：普通 C 调用入口

获选计算 body 另已形成普通 RV64 C ABI 公共函数，使用和复现见 [ENTRY_README.md](ENTRY_README.md)，新调用路径的实际比较、普通 C 功能验证及资格边界见 [ENTRY_RESULT.md](ENTRY_RESULT.md)。上述原镜像 `export/verify/resolve` 语义保持；新入口的证据独立封存。

## 稳定源码包与回退

新接入推荐采用 [firstdot V2稳定源包](FIRSTDOT_STABLE.md)：四形状普通C源别名、单完整对象静态库及可独立搬移的双头文件。已验证原firstdot机器码、实际GNU调用等价和冻结[V1回退](STABLE.md)；原镜像查询/导出及既有V1使用不自动切换。新增调用者和应用仍须按实际影响验证。
