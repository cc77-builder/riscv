# R2-SELECT：合格原镜像选择与精确导出合同

合同身份：`r2-select-qualified-original-images-v1`。入口为 `selection.py`。

## 目标与资格来源

从已发布 S1 v2 的 S0/S1 完整矩阵选择各形状、各 scope 的最快合格实现，并导出能定位实际 ELF/BIN、case、符号、正式窗口和回退的原字节包。该层只选择已经验收的原镜像，不新增目标机调度器。

资格入口固定为 `team/optimizations/o2/r2-vector-accum/evidence/merged-v2`，manifest SHA-256 必须为 `a1af4314c83b29d97b58b7ae9fe65dbc96bb3d050530d2fe7378c022b9415d73`。即使其它归档的 manifest 和自身哈希一致，也不满足本合同。S1 发布提交为 `ec221262ae29522dd9d1a2be7240b405cc23a549`；归档原导出时的源码 HEAD 另从 manifest 保留，不能用发布提交代替。

原架构资格复用两份已发布报告的精确字节：

| 报告 | SHA-256 | 原验证范围 |
|---|---|---|
| `merged-v2-audit-linux.json` | `b035c4b400a7d8cfbca6c45cf41c8582ee965fff1dede5cf59320199912d33be` | 56 正常进程、1 预期负控、768 正式窗口、4 主批重放；原文架构、CSR、精确退休、O2、来源及统计复算 |
| `merged-v2-small-replay-audit-linux.json` | `2165d95cda3282b6c81c0ce9164a42997bec9c0b4bd69d4ef469d505264e4d0c` | 4×8/8×32 的额外 4 次进程重放、96 个签名匹配窗口，新增正式样本为 0 |

每次入口核验整份归档的 stored/raw 字节、精确文件清单、上述报告身份和对应归档身份，并重算统计和导出关系。固定 S1 生成器/门禁/实验入口、复用的旧 ELF/运行模块及其实际导入位置也必须相符。检查磁盘文件哈希不能代替检查实际已加载模块；发现另一检出的同名模块时拒绝继续。

本层明确记录 `architecture_recomputed=false`、`qualified_evidence_reused=true`，不重复已有完整架构审计或 EMU。只接受两个无来源的 `PASS` 字符串不构成资格。

## 样本域与选择规则

完整域为四形状 `4×8、8×32、16×64、4×13`，两 scope `core/endtoend`，两个 variant `s0/s1`，两个 software `basic/reuse`，两个 method `vdot/rvv`，三个 dataset `0/1/2`，四个正式 repeat `2/3/4/5`。

- 正常原记录必须是完整 56 项，包含原 smoke/正式/主批 replay 的准确身份；不得重复或遗漏，也不得混入 S2、firstdot 或其它合同。
- 每个正式进程保留原 24 个窗口。repeat0 为 first、repeat1 为 warmup、repeat2～5 为 measured；不将 first、warmup、主批重放或小尺寸补充重放加到正式样本。
- 正式样本键为 `(variant, shard, software, method, dataset, repeat)`。shape、scope、case ID、镜像身份、seq 与原调用计划分别对应。
- 继续调用冻结的 `experiment.summarize` 重算完整 **768** 窗口，得到 **32** 个 variant/software 行，即 **64** 个方法单元格，每格恰为 **12** 窗口；与原结果和固定架构审计中的统计完全一致。
- 对每个 shape/scope，候选全集为 S0/S1 × basic/reuse × vdot/RVV。按完整 12 窗口**总周期**选最小项，不按 dataset 或单窗口挑赢家，不将两个 scope 的周期相减当作可加成本。
- 总周期相同时依次优先 RVV、S0、basic；并列时不声称对 RVV 加速。
- 同时保存最快合格 RVV，以及 S0 中较快的 vdot 回退；不会先固定 reuse 或预先丢弃较快对照。未知形状、scope、dataset、role 明确拒绝，不把这四个固定形状扩写成任意 GEMV 支持。

当前 S2 强 RVV 探针只用于关闭其扩大采用方向；其每单元格 4 个正式窗口、共 32 个正式窗口的数据不加入本合同。firstdot 尚无运行资格，也不加入。

## 导出与查询

导出全部 **48 份正式原镜像**的完整 canonical 目录，保留每份镜像内 basic/reuse、vdot/RVV 四个 case 及其生成源码、构建回执、ELF/BIN、原调用计划；另复制每份原正式运行的结果回执。原收据的历史绝对路径和来源内容不改写，新选择清单使用相对于导出包的路径。

每个候选的三 dataset 关联必须给出原镜像名、ELF/BIN 哈希、case ID/index、真实 ELF 符号与入口地址、原运行回执、四个正式窗口的 seq/repeat/cycles/instructions；三 dataset 合计必须等于该候选完整总周期。

导出包包含 `selection.json`、`artifacts.json`、`bundle-state.json`、两份原资格报告，以及上述原字节文件。`verify` 从固定源归档重新建立预期清单/映射，再核验完整文件集合、全部字节和完成状态。增删文件、符号链接、改动 ELF/BIN/manifest/回执、篡改选择或伪写 PASS 均不得通过。

`resolve` 先执行同样的完整验证，再按 shape/scope/dataset 和 `selected`、`fastest_rvv`、`s0_vdot_fallback` 返回实际本地路径。它不启动仿真、不隐式执行原 57 进程入口，也不产生新的目标机调用路径。导出包可搬到另一目录；验证和查询仍需要匹配的完整仓库、固定 S1 归档和两份资格报告。

输出路径在任何写入前必须排除源归档及 S1 输入树；报告还必须位于导出包之外。已有导出目录与报告不覆盖。中断或异常保留 FAILED/未完成状态与已有输出；无断点续导出功能，后续核实后使用新的输出位置。

## 性能与采用边界

原镜像保持相同字节与调用计划，选择清单可引用其已有 12 窗口资格。只运行获选 case、删除其它 case、换序、缩槽、重链接、合并 ELF 或增加 caller/dispatcher 都属于新执行路径；不得继承这些均值或用本工具的 PASS 背书。

本层不切换生产默认，不增加硬件构建、DiffTest、面积、时序、功耗、完整应用或 T17 的验收。下一阶段若引入新调用入口，先比较 `8×32 / dataset0 / endtoend` 的真实完整新路径和强 RVV：当前原镜像余量仅 10.75 周期。强 RVV 也须使用相同的新调用入口和计时边界重新实测；原周期只用于确定首个探针，不作新镜像比较分母。通过正确性、真实负控/正常恢复、重放及公平性能后才扩大受影响范围；首条 custom PC 或目的改变时按实际指令重新绑定负控。后续稳定入口仍走 R4/O5 → T17 → R5/G5。
