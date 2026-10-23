# R2-SELECT：合格原镜像选择、查询与导出结果

本次关闭 **R2-SELECT 的原镜像选择与精确导出子项**。新增 `selection.py` 将已合格 S1 v2 的完整矩阵复算为八项选择，实际导出全部 48 份正式原镜像，并通过 Linux、Windows 的真实归档测试及跨平台查询。没有新增目标机 dispatcher、重链接镜像或切换默认入口；本层 PASS 不提供这些新执行路径的资格。

操作 ID：`20261024-LiZufan001-r2select-0001`；执行者：`@LiZufan001 / Agent`。工程开始为 `2026-10-23T17:54:04Z`（2026-10-24 01:54:04，UTC+08:00），最终执行收据于 `2026-10-23T18:16:08.5786756Z` 结束，后续交付检查和发布以计分板及 Issue 为准。实际独立工作区、原生 Linux 检出、输出和进程定位见[运行位置记录](evidence/selection-v1/runtime/locations.json)。

## 1. 身份、假设与实现范围

交付与原生 Linux 检出的基点均为 `fdef4e45dcfab46ee85ca6d3574fb8e8d33943bd`。新增源码当时为未提交覆盖，不能把此基点写成已含新入口的提交。承载本报告的提交由 Git 历史定位。

| 输入或源码 | 精确身份 |
| --- | --- |
| 最终 `selection.py` | `8230162c9f28356614cefb0b22a5f88efc1dbcfff66eb7b216853e1bec43f60b` |
| 最终 `test_selection.py` | `824b64302d6caa32bdc7252f388fc33030c67902ef991ca12dc80a8ea8ded5c7` |
| S1 v2 归档 manifest SHA-256 | `a1af4314c83b29d97b58b7ae9fe65dbc96bb3d050530d2fe7378c022b9415d73` |
| S1 资格发布提交 | `ec221262ae29522dd9d1a2be7240b405cc23a549` |
| 原归档记录的导出源码 HEAD | `bca14d45b07ff07a86a7f54bce2b25870e60e2f3` |

待检验假设是：现有合格矩阵可以形成可重复、完整且不会挑窗口的选择，并精确定位对应原镜像、case、符号、运行回执和回退。采用条件为全矩阵重算一致、全部原字节相符、实际路径可访问以及针对性拒错通过。无需为这个数据层变更重跑已有效的整核样本。

入口固定检查 S1 归档、两份已发布架构审计、冻结生成器/检查器及实际加载模块位置；重新核对完整 56 项正常记录和正式调用计划，调用冻结的统计入口重算 768 个正式窗口。选择按同 shape/scope 的完整 12 窗口总周期进行，保留全部候选、最快 RVV 和最佳 S0 vdot 回退；相同时优先 RVV。`verify` 和 `resolve` 都重建映射并检查完整输出清单，拒绝伪 PASS、缺文件、额外文件、符号链接和输入身份变化。完整行为及资格边界见[合同](CONTRACT.md)。

## 2. 原窗口的选择结果

以下均为 **S1 v2 原合格镜像**的周期均值，每候选为三个 dataset × 四个正式 repeat，共 12 窗口。正式样本未加入 first、warmup 或 replay。比值为同一归档下最快合格 RVV 的完整均值除以获选均值，不是本次新执行路径的测量。

| 形状 | scope | 获选实现 | 获选周期 | 最快 RVV 周期 | RVV / 获选 |
| --- | --- | --- | ---: | ---: | ---: |
| 4×8 | core | S1 reuse vdot | 111.50 | 131.25 | 1.177130× |
| 4×8 | endtoend | S1 reuse vdot | 155.00 | 175.00 | 1.129032× |
| 8×32 | core | S1 reuse vdot | 237.25 | 248.50 | 1.047418× |
| 8×32 | endtoend | S1 reuse vdot | 278.25 | 289.00 | 1.038634× |
| 16×64 | core | S1 reuse vdot | 634.25 | 698.00 | 1.100512× |
| 16×64 | endtoend | S1 reuse vdot | 701.25 | 768.25 | 1.095544× |
| 4×13 | core | S1 reuse RVV | 131.25 | 131.25 | 1.000000× |
| 4×13 | endtoend | S1 reuse RVV | 175.00 | 175.00 | 1.000000× |

K13 的 S0 reuse vdot 回退仍为 core 165、endtoend 210 周期。S2 探针中的 RVV 175.25 来自另一明确身份的探针合同，不用它替换上表的 175，也不将探针每格四窗口并入这里的十二窗口。S2 采用决定继续引用[固定布局与强 RVV 结果](../r2-safe-tail/FIXED_RESULT.md)。

完整八项选择和 64 个候选的三 dataset 关联见[实际选择清单](evidence/selection-v1/bundle-02/selection.json)。每项含原 ELF/BIN 哈希、case/index、符号和入口地址、四个正式窗口及运行回执；`selected`、`fastest_rvv` 和 `s0_vdot_fallback` 均能查询。不同形状的同名符号属于各自原 ELF，不能跨镜像拼接。

## 3. 实际导出与验证

最终输出为运行位置记录中的 `bundle-02`。其 48 份原镜像保留原四 case 及调用计划；1296 个原始载荷共 **101,861,823 字节**，另有三份清单/状态及两份资格报告。原生成源码、构建回执和历史绝对路径保持原字节；实际查询路径由当前导出根定位。

| 验证层级 | 实际结果与证据 |
| --- | --- |
| Linux 主机/真实归档测试 | **PASS，21 项**；使用独立完整原生 Git 检出及最终两份源码；[原命令](evidence/selection-v1/runtime/tests-02-command/command.json)、[测试输出](evidence/selection-v1/runtime/tests-02-command/stderr.log) |
| Linux 实际导出与查询 | **PASS**；导出全部原载荷，实际查询 8×32/endtoend/d0 获选项和 K13/endtoend/d2 S0 回退；[汇总](evidence/selection-v1/runtime/linux-final-validation.json)、[导出报告](evidence/selection-v1/runtime/export-02.json)、[获选查询](evidence/selection-v1/runtime/resolve-8x32-02.json)、[回退查询](evidence/selection-v1/runtime/resolve-k13-fallback-02.json) |
| 原生 Windows 主机测试 | **PASS，21 项**；Python 3.13.13，最终源码；Windows 普通/extended 路径别名分支实际执行，POSIX 符号链接分支由 Linux 覆盖；[原命令](evidence/selection-v1/runtime/tests-windows-02-command/command.json)、[输出](evidence/selection-v1/runtime/tests-windows-02-command/stderr.log) |
| Windows 跨 WSL UNC 访问 | **PASS**；对同一 `bundle-02` 完整校验并查询，实际 ELF/BIN/manifest/运行回执路径存在；[汇总](evidence/selection-v1/runtime/windows-final-validation.json)、[校验](evidence/selection-v1/runtime/verify-windows-02.json)、[查询](evidence/selection-v1/runtime/resolve-windows-02.json) |
| 原 S1 架构资格 | **复用原 PASS**；两份报告精确字节及归档/源码身份均核验。本次 `architecture_recomputed=false`、`qualified_evidence_reused=true` |
| 新目标入口、整核、NEMU、默认切换 | **NOT_TESTED／未实施**；新增 EMU/NEMU 进程均为 0，新 dispatcher 资格为 false；没有把主机 PASS 转为新运行时 PASS |
| 外部物理输入再核验、T17、PPA | **NOT_TESTED**；独立检出的主机复算不等于干净硬件构建或 T17，未新增面积/时序/功耗结论 |

测试覆盖真实完整矩阵、最优 RVV 不被预丢弃、并列规则、缺失/重复窗口与记录、first/warmup/replay 排除、样本形状/数据/case/镜像绑定、错误合同与执行状态、错归档、预加载异源模块、原载荷与映射篡改、资格升级、未完成/伪完成状态、移位后查询、未知请求、输出输入隔离及禁止覆盖。两平台都没有 unittest skip；条件分支的执行范围按上表区分。

最终 `selection.json` SHA-256 为 `b50aafa5c143e9f1430c1a9bbf8b3281fb0baa5deb59664ad6e04147c3de3a09`，`artifacts.json` 为 `cfa2b676022a0ce8548333179159f038545afc7cc473b55b157a8636758fa4bf`，两平台结果一致。载荷完整索引见[artifacts.json](evidence/selection-v1/bundle-02/artifacts.json)。

## 4. 实际失败、修订与保留范围

| 实际失败 | 定位、修订及结果 |
| --- | --- |
| 最初只读清单检查假设不存在的 `logical` 字段；首次新文件写入时父目录不存在 | 分别改用已有 `Archive.records` API、显式创建授权的新模块目录；没有修改原归档，没有部分源码写入。原失败身份和诊断保留于[准备记录](evidence/selection-v1/runtime/preparation-notes.json) |
| 首次 CLI 负测包装脚本捕获了错误异常类型 | 导出和两次查询已成功；输入树内输出被产品正确拒绝并 exit1。旧 `fullcore_screen.command` 抛出 `ValueError`，包装脚本误捕获 `RuntimeError`。读取已有拒错回执及输出不存在事实，仅继续此前未启动的报告负测和独立校验，没有重跑已成功导出；两份预期拒错收据均保留 |
| 最初 Windows 校验读不到 52 个深层归档文件 | 普通 Windows 路径超限；只读诊断证实 extended 路径下 52 个文件全部存在且 stored SHA 一致。只改新入口的数据路径规范化，并将写保护比较两端统一规范化；旧源码/归档均未改。[原失败及逐类诊断](evidence/selection-v1/runtime/windows-path-failure.json)、[原命令](evidence/selection-v1/runtime/verify-windows-01-command/command.json)保留 |
| 首次 Git 索引逐字节检查拒绝两份原始 Windows JSON 回执 | 根属性把原 CRLF 规范化为 LF；只读诊断证实差异分别为 25 和 13 个换行，其余字节不变。新增本模块 `.gitattributes` 的 `evidence/** -text`，保留证据原字节后重新暂存并执行同一逐 blob 校验；原回执和固定哈希不改。[失败收据与诊断](evidence/selection-v1-publication-repair.json)保留，最终结果另见发布检查报告 |

`sources-01` 的 20 项 Linux PASS 和 `bundle-01` 均保留原身份；最终使用独立 `sources-02`、21 项测试及 `bundle-02`，没有把旧版本 PASS 移到新代码。Windows 修复覆盖归档、导出包、报告及相应写保护路径；当前仓库根采用普通路径。源码 import/pin 读取不承诺任意超长仓库根，显式 extended `--repo` 与普通脚本路径混用仍可能安全拒绝同一检出，未声明该组合支持。

本次把 100 份原始报告、清单、源码快照和命令收据按原字节复制入证据目录，另保存执行总收据与位置记录，见[复制校验收据](evidence/selection-v1/copy-receipt.json)。完整约 102 MB 的解压后运行载荷仍在独立输出；Git 已有固定 S1 原归档，可用本入口重新导出，不再次提交相同大载荷。原始来源路径保存在运行记录，共享使用命令采用配置变量。

## 5. 接续动作与退出条件

当前原镜像选择/导出子项可使用[README 的已执行同类命令](README.md)在新输出位置复现。移动包后仍需匹配完整仓库、固定归档及两份资格报告；不能只拷贝清单后声称包自足。先通过 `verify`，再以 `resolve --shape 8x32 --scope endtoend --dataset 0` 分别查询 `selected` 和 `fastest_rvv`，即可得到下一项真实对照的源码、原镜像和正式窗口身份。K13 回退查询用 `--shape 4x13 --scope endtoend --dataset 2 --role s0_vdot_fallback`。

下一工作项为 **R4/O5 的获选组合／实际入口影响闭合**：新操作 ID 先核对 Issue 认领和物理输入，固定所选软件与既有 O2/H1 硬件身份。若继续完全相同的原镜像与调用计划，可复用相符资格；若增加 caller/dispatcher、只跑获选 case、重排或合并 ELF，先建立其独立运行合同，在 `8×32 / dataset0 / endtoend` 上完成真实正确性、负控拒错→同镜像正常恢复、重放，以及包含入口成本的公平性能。强 RVV 必须走**相同新调用入口和计时边界重新实测**；原 289 周期及 10.75 周期余量只决定首个试验的选择，不作新镜像性能分母。首条 custom PC 或目的改变时重新绑定真实负控，不替换旧固定哈希。

只有新入口仍胜过同条件强 RVV、正确性与重放通过，才扩大三 dataset 和受影响形状；失败先定位，入口成本吃掉收益则保留当前原镜像工具及 RVV，不无依据扩大运行。随后按现有路线进入 T17 和 R5/G5。若 R4/O5 被占用，按 Issue 选未冲突的 S1 firstdot 运行合同子项或已有 R3 只读消费者分析；不接管 MERGE-REG 有效认领。

本包未启动 EMU，最终命令已 exit0、cleanup_complete；原 S2 运行保护的结束状态及其它 MERGE-REG 待核实保护仍只由 Issue 的真实事件管理，本报告不解除它们。停止写入、释放认领、最终提交与推送身份在本操作 ID 的 END/DONE 中记录。
