# K13 较快 RVV 的统一布局探针

本子项属于 R2-S2 的比较资格补缺。它检验：在固定 S2 vdot、同一 harness／加载布局和同一输入下，加入已经合格的 S1 RVV 后，S2 是否仍值得扩大采用实验。结果见 [FIXED_RESULT.md](FIXED_RESULT.md)，不从另一合同的 RVV 均值拼接加速比。

## 有界假设与停止条件

先只测 **dataset0、4×13、endtoend**，同时保留 basic/reuse。主要判断依据是新 `rvv1` 镜像内的 S2 reuse vdot 与较快 RVV 的完整窗口；全部结果同时报告。若数学、来源、布局、负控恢复或重放失败，停止性能判断并定位。如果 S2 在此探针仍不胜过较快 RVV，就不扩大 S2 采用矩阵；只有可重放的优势才支持继续三个数据集和两 scope 的资格验证。

这里的 endtoend 仍是 O3 内核窗口，包含配置、读取、计算与输出存储，不是完整应用或系统时间。四个 8 KiB 槽属于受控测量布局，周期不能直接转移给紧凑布局、另一 caller 或新的默认入口。

## 源码与布局合同

- 新运行合同：`r2-s2-k13-strong-rvv-probe-v1`。新 manifest 记录 probe 源码、S1／S2 候选及固定布局适配器 SHA-256；不升级旧合同或历史结果。
- `rvv0`：冻结 S2 vdot，加原 O3 RVV。`rvv1`：同一 S2 vdot，加已发布 S1 RVV。S1 候选 SHA-256 为 `0270736b5c09e160626eb7b32d8e760faa193bf05761fea824a979108c3717b9`。
- 新入口只读使用两个冻结候选；没有 S1 vdot 和 S2 尾部的内核组合，也不修改候选、黄金值、原检查器或 RTL。
- 保留原 S2 的二进制 UART 标识、C ABI、四个 case、原数学数据和正反测量计划。新源码／manifest／运行回执明确标识探针，不能拿原 S2 的精确生成校验直接接受它。
- 用原固定布局构建器产生两份真实 AM ELF，再独立 GNU 汇编对照全部四槽；准确再生源快照、汇编、头文件及 manifest。
- 两个完整 vdot 槽（包括 padding）、`main`、所有 ALLOC／program headers、全部其它加载字节必须一致。仅允许 RVV 两槽不同，**没有元数据字段例外**。
- 主机测试另外独立构建固定布局 S2，要求 `rvv0` 的整 BIN 相同。这本身不是对主批原 BIN 的直接核对；实际原镜像的哈希关联另存运行证据。

两个镜像中的 vdot 机器码相同，也不预设其周期必须相同：RVV 槽的改变可能改变相邻测量前的执行历史。保留两边 vdot 数值，不把这种变化归因为新的 vdot 优化。

## 运行、计数与来源

固定合并硬件、正常 NEMU、flash 及严格原文检查与 [fixed-layout 主合同](FIXED_LAYOUT.md)一致。每个实际进程前后核验输入；整批结束前再核验完整两份 canonical ELF、源再生、独立对象、布局缓存、硬件来源及五份进程收据。

顺序为：`rvv1` bit100 负控 → 同镜像新进程正常恢复 → `rvv0` 正常 → `rvv0` 重放 → `rvv1` 重放。S2 首条 custom 的实际目的寄存器仍是 v20；负控仍必须从真实 ELF 绑定指令，并形成高半部拒错链，不能仅靠退出码。使用独立新夹具目录，保留正常参考模型身份。

完整成功探针要求 **5 次实际 EMU，其中 1 次预期拒错、4 次正常；32 个正式窗口；2 次确定性重放**。每单元格为 dataset0 的四个 measured repeats，first、warmup、重放不计入正式样本；不会写成三数据集的 12 样本资格，也不验收 R2-SELECT／MERGE-REG／R4／T17／PPA。

所有输出必须原先不存在；入口不支持断点恢复。配置与主合同的八字段相同，`canonical_build` 指向这次两镜像构建。先核对 Issue 认领、运行保护和真实资源，不与其它重型任务争用。

```bash
R2_RVV_PROBE_TEST_CONFIG="$R2_RVV_CONFIG" \
python3 -B -m unittest discover \
  -s team/optimizations/o2/r2-safe-tail -p test_rvv_probe.py -v

python3 -B team/optimizations/o2/r2-safe-tail/rvv_probe.py \
  --repo "$PWD" --config "$R2_RVV_CONFIG" --output "$R2_RVV_BUILD" --action build

python3 -B team/optimizations/o2/r2-safe-tail/rvv_probe.py \
  --repo "$PWD" --config "$R2_RVV_CONFIG" --output "$R2_RVV_RUN" --action run
```

## 封存与独立复算

从原运行源码根封包；独立检出运行完整 audit。归档同时保留原始和压缩字节身份，源快照、命令、进程、负控、全宽结果／CSR／退休／O2 轨迹及统计可重新检查；外部硬件、正常 NEMU、flash 和 AM 库只保留来源／固定哈希，不声称离线重新取得或执行实物。

```bash
python3 -B team/optimizations/o2/r2-safe-tail/rvv_probe_evidence.py \
  --repo "$PWD" --action pack --run "$R2_RVV_RUN" \
  --archive "$R2_RVV_ARCHIVE" --output "$R2_RVV_PACK_RECEIPT"

python3 -B team/optimizations/o2/r2-safe-tail/rvv_probe_evidence.py \
  --repo "$PWD" --action audit --archive "$R2_RVV_ARCHIVE" --output "$R2_RVV_AUDIT"

R2_RVV_PROBE_TEST_ARCHIVE="$R2_RVV_ARCHIVE" \
python3 -B -m unittest discover \
  -s team/optimizations/o2/r2-safe-tail -p test_rvv_probe_evidence.py -v

git add -f -- "$R2_RVV_ARCHIVE"
python3 -B team/optimizations/o2/r2-safe-tail/rvv_probe_evidence.py \
  --repo "$PWD" --action index --archive "$R2_RVV_ARCHIVE" --output "$R2_RVV_INDEX_AUDIT"
```

封存可重复传 `--support` 附加真实测试、失败定位和实际配置来源；事后审计器自动作为支持源码封存，不追溯加入运行时输入。所有报告必须写在归档外。

`audit` 要求完整 Linux 检出，复用原始检查器并执行精确文本再生。`bytes`／`index` 可在原生 Windows 执行，分别验证封存字节／完整布局和实际 Git stage-0 清单、普通文件模式、blob 字节，不冒称架构复算。针对性归档负测只在内存覆盖层模拟自洽篡改，不修改真实归档；它们检验范围标签、缺失重放、AM 库路径、正常参考来源和原始窗口统计的拒错。
