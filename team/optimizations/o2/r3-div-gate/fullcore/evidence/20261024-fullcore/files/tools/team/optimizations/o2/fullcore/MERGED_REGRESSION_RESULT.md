# MERGE-REG：当前合并基线的新夹具回归交付

## 结论与范围

合同 `o2-merged-regression-new-fixture-v1` 的现有真实运行与原始流复算通过。
选定集合为 12 个核心任务和 2 个补充任务：13 条完整正常轨迹、1 条预期负控轨迹，
六个 O2 目标覆盖齐全。核心功能／异常矩阵保留 117 个唯一用例、124 次分片执行；
control 独立通过七项 legacy 义务，dense 独立通过原 12 个窗口和双槽重叠检查。

该结论属于既有 6d2 合并硬件和 EMU `1a23dbab…`。
原 campaign 新执行 2 个进程（新负控 → 同镜像正常恢复），其余 12 项沿完整来源链复用。
本轮接续没有新增 EMU/NEMU 执行，也没有重编硬件或测量性能。
旧 `9b3aecf3…` 固定负控仍缺失；旧 B0/H1、S2 组合、T17、ASIC PPA 不由本合同取得通过结论。

## 可复核的交付

证据位于 [evidence/merged-regression-v1](evidence/merged-regression-v1)。

| 层级 | 实际证据与结论 |
| --- | --- |
| 原运行 | 归档内 `campaign/state.json`、`campaign/result.json`、全部 raw 流、输入与来源链 |
| Linux 实物复算 | 归档内 `physical-audit/result.json`，`O2_MERGED_REGRESSION_RAW_AUDIT_PASS`；结果 SHA-256 `57737f9450f74bd76250ad30abcf9eb200894757501d46712b2c7d02521029b9` |
| 不可变归档 | 原 archive-02 按字节保存，558 个载荷文件；原始 306,045,367 bytes，存储 34,134,570 bytes；manifest SHA-256 `42fa2d85ee4eeb6aec0e58ade9d49ddbd98285836052577e0ba03f2d8c6423ba` |
| 本轮完整离线复算 | `archive-audit-linux-final.json`，`O2_MERGED_ARCHIVE_ARCHITECTURE_TRACE_PASS`；从原始流、ELF 与黄金数据重新计算，非仅检查缓存 PASS |
| 修复测试 | `unit-tests-final.stderr.log`，15 项通过，含输入变更与旧恢复替代拒绝 |

冻结运行 controller 的 SHA-256 保持
`b082d34f9e7eed5d56296aacf4a707358cab3c370ae301bf9a4a82174af122a5`。
本轮归档审计工具 SHA-256 为
`69216d4a0594eb47d6de186e7e9ab175a72eda67178a5039006d2c3d9177d6a5`。
完整原 archive-02 不重新打包，保留其中旧 exporter 身份；新审计工具及其回执单独交付。

## 修复依据

前三次归档复算分别在缺省 `timed_out`、选定集合／覆盖和
`runtime-inputs.json` 字节一致性处退出，失败记录保留于 `prior-failures/`。
当前第三个阻断的实际原因：campaign 与 physical audit 的 442 项输入键和值完全相同，
只有 JSON 对象键插入顺序不同；另三份共同输入原始字节也一致。

`merged_regression_evidence.py` 仍先校验每份载荷的存储／解压 SHA-256、长度和完整清单，
然后对两份 JSON 的结构化内容做规范化比较。对象键顺序与格式空白不影响输入身份；
增删键、值、数组顺序、布尔／整数／浮点类型替换、重复键和非标准数值都拒绝。
没有改变冻结 controller、黄金数据、架构／CSR／DiffTest／O2 判定标准或官方程序。

## 复算命令

在仓库根执行，输出选用新的归档外路径：

```bash
python3 -B -m unittest discover -s team/optimizations/o2/fullcore \
  -p 'test_merged_regression*.py' -v
python3 -B team/optimizations/o2/fullcore/merged_regression_evidence.py audit \
  --archive team/optimizations/o2/fullcore/evidence/merged-regression-v1/archive \
  --output /absolute/new/merge-archive-audit.json
python3 -B team/optimizations/o2/fullcore/merged_regression_evidence.py verify-index \
  --archive team/optimizations/o2/fullcore/evidence/merged-regression-v1/archive \
  --output /absolute/new/merge-index-audit.json
```

`audit` 复算封存的架构／控制／覆盖及拒错恢复；不启动仿真，也不重新核验外部实物构建树。
`verify-index` 另逐项检查 stage-0 普通 Git blob 的完整集合和实际字节，不把工作树存在当作已提交。
EMU 未包含在归档；硬件依赖树、生成 RTL、NEMU 源码／构建和系统头文件属于原实物来源，
因此此包是可移交的运行证据，不是完全独立的工具链／硬件重建闭包。

后续工程由 T17 用新的干净构建身份执行，不改变本归档。
