# S2 在合并版 O2/H1 上的正式软件筛选

## 结论与采用边界

真实完整运行 **PASS**：26 份 canonical ELF、30 次正常 DiffTest、1 次精确 bit100 拒错与同镜像恢复、384 个正式窗口和 4 次确定性重放均通过。运行于 2026-10-23 **08:54:19.116～09:52:38.436 UTC**（16:54:19.116～17:52:38.436，UTC+08:00），终态 `R2_S2_MERGED_SOFTWARE_SCREEN_PASS`，失败或未完成 EMU 数为 0。

**取舍：仅将 S2 的 4×13/reuse 保留为 R2-SELECT 候选；basic 保留 S0，不切换统一默认。** reuse 的 endtoend 平均周期由 209.5 降至 187.25，减少 **10.621%**；core 减少 13.162%。basic 的 endtoend 增加 21.138%，core 增加 26.335%，因此“指令变少就会更快”的假设被实际周期否定。16×64 的全部控制窗口逐项相同。

较快合格 RVV reuse/endtoend 为 190 周期，S2 仅少 2.75 周期，加速比 **1.014686×**。这支持继续选型，不足以宣称宽泛的应用优势。四尺寸全覆盖、S1 向量累加及对等 RVV 优化、所选组合回归与 T17 干净环境真实复现仍未完成。

本结果采用独立的 [merged software screen 合同](MERGED_SCREEN.md)。原 B0/H1 两硬件筛选仍为 BLOCKED：旧 EMU 实物未恢复，不能将当前合并版伪装成任一历史硬件。这里也不宣布 MERGE-REG 整套验收、R4/T17 完成、整核频率或功耗改善。

## 输入和执行身份

| 项目 | 实际身份 |
| --- | --- |
| 软件检出基点 | `ff58e519091f273c4bc177f5e82cfbbfaf102cc5`；新增入口的实际源码按运行输入 SHA-256 封存，承载提交由 Git 历史定位 |
| 运行入口 | `merged_screen.py`，SHA-256 `ff75464c5b0f75349fc4321bdd80a7a85985a54ae415ad347c3ce04fdf4bd885` |
| 合并硬件源码 | `6d2abe403b07c297b8830a7d4f06e370b0a8e070` |
| EMU | `1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63` |
| 正常 NEMU | `efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4` |
| 新 bit100 夹具 | `6e8b3488bb4cc516f05a7aa81c40b9d5e66085e275d4fbe27da85f05748b9a5f`；固定 C 源码、实际编译命令和正常库直接依赖均保留 |
| nexus-am | `086a238062fdfb3281b745a537b361983d0154b5`；私有干净检出，rv64gcv，两个实际库哈希见构建回执 |
| 软件工具链 | GNU RISC-V GCC 11.4 / binutils 2.38；完整版本文本、命令和返回码见归档 |
| 新硬件构建 | 0；复用实际构建并核验 429 源码、21,236 依赖和 1,672 生成物 |
| 本轮构建 | 26 个 canonical GNU+nexus-am 链接 ELF；原候选、黄金值和检查器未修改 |

16×64 的 S0/S2 加载镜像完全相同。所有 S0/S2 配对中，RVV 内核的地址和机器码保持相同。变体标签同时与构建 selection 和 manifest 绑定，不能仅改目录名称冒充候选。

## 实际正确性和拒错证据

新夹具在第一次合法 vdot 的返回状态副本中翻转 bit100。实际负控退出 1，记录 `vd=20`、`pc=0x8000116c`、`word=0x03880a0b`；同 PC/寄存器的高半部差值严格为 `1<<36`，原 stdout 中 mismatch 后紧邻唯一 ABORT。ELF 的真实指令字、被加载的参考库路径和中止前的两槽 O2 部分轨迹均经核验。

ABORT 事件报告的 PC 是 `0x80001190`，不把它误作必须相等的故障指令 PC。夹具不按 S2 尾部 PC 选点，因此这项证据说明真实 DiffTest 能拒绝高位错误；S2 尾部正确性由随后正常运行的全 128 位黄金值、寄存器/CSR/边界检查承担。

负控实际运行于 2026-10-23 08:54:24～08:54:34 UTC，随后同一镜像使用正常 NEMU 的新进程于 08:54:34～08:55:31 UTC 完成恢复。两个正常 smoke 和后续正式窗口使用同一个硬件身份。

## 完整性能结果

以下统计已由封存原文独立复算，与运行结果逐项一致。

| 形状／窗口／布局 | S0 vdot 平均周期 | S2 vdot 平均周期 | S2 周期变化 | 最快 RVV 平均周期 | 最快 RVV / S2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 16×64 / core / basic | 2145.00 | 2145.00 | 0.000% | 826.50 | 0.385315× |
| 16×64 / core / reuse | 766.25 | 766.25 | 0.000% | 826.50 | 1.078630× |
| 16×64 / endtoend / basic | 2214.50 | 2214.50 | 0.000% | 894.00 | 0.403703× |
| 16×64 / endtoend / reuse | 848.25 | 848.25 | 0.000% | 894.00 | 1.053935× |
| 4×13 / core / basic | 201.25 | 254.25 | +26.335% | 148.50 | 0.584071× |
| 4×13 / core / reuse | 165.25 | 143.50 | -13.162% | 148.50 | 1.034843× |
| 4×13 / endtoend / basic | 246.00 | 298.00 | +21.138% | 190.00 | 0.637584× |
| 4×13 / endtoend / reuse | 209.50 | 187.25 | -10.621% | 190.00 | 1.014686× |

表中变化按 `(S2 / S0 - 1) × 100%` 计算，负值为周期减少；加速比按 `RVV / vdot`，大于 1 才表示 vdot 更快。最快 RVV 均为 reuse，在 S0/S2 下对应均值相同。basic 的 S2 即使比 basic RVV 快，也明显落后于这个更强对照。

4×13 basic RVV 在 S0/S2 下的均值相差 0.25 周期；reuse/core 的四轮顺序也有差异，但均值相同。所有原值均保留，机器码／地址相同不被写成所有 RVV 周期相同。16×64 的逐窗口不变检查另行严格通过。

每单元 12 个正式样本来自三个数据集、各四轮 measured。first、warmup、smoke 和四次确定性重放均不增加正式样本数。core 和 endtoend 分别比较，endtoend 指 O3 内核窗口，包含配置、读取、计算和输出存储，不包括框架的 VS 启用和哨兵初始化，也不是完整应用系统延迟。

4×13 的三个数据集在对应配置下给出相同的四轮周期序列；以下逐行适用于 dataset0、dataset1、dataset2，归档仍分别保留三次真实运行，没有把一次运行复制成额外样本。四轮顺序为 repeat2～5。

| 窗口／布局／变体 | vdot 四轮周期 | vdot 每轮退休数 | RVV 四轮周期 | RVV 每轮退休数 |
| --- | --- | ---: | --- | ---: |
| core / basic / S0 | 197, 205, 199, 204 | 141 | 274, 274, 275, 275 | 77 |
| core / basic / S2 | 254, 254, 255, 254 | 113 | 274, 274, 275, 274 | 77 |
| core / reuse / S0 | 165, 165, 166, 165 | 112 | 149, 148, 148, 149 | 57 |
| core / reuse / S2 | 144, 143, 143, 144 | 78 | 149, 149, 148, 148 | 57 |
| endtoend / basic / S0 | 239, 253, 239, 253 | 153 | 320, 320, 321, 320 | 89 |
| endtoend / basic / S2 | 298, 298, 298, 298 | 125 | 320, 320, 320, 320 | 89 |
| endtoend / reuse / S0 | 210, 209, 210, 209 | 124 | 190, 190, 190, 190 | 69 |
| endtoend / reuse / S2 | 188, 187, 187, 187 | 90 | 190, 190, 190, 190 | 69 |

## 指令和瓶颈解释

从本轮实际链接 ELF 提取并与生成源码核对的结果见归档 `support/static-4x13-analysis.json`：4×13/reuse 的 endtoend 主体静态指令由 117 减至 83，basic 由 146 减至 118；实际 instret 还包括固定计时边界中的七条指令。S2 的 4×13 basic/reuse vdot 内核各增加四次 dot8；basic 的 `vsetivli` 从 14 增至 30，reuse 从 6 增至 10。新增清零、向量读取、配置与跨域搬运均计入原窗口，不能用减少的退休数直接推断周期收益。RVV 的两个内核地址与机器码在本次实际 ELF 中分别相同。

完整离线复算另提取192个正式 vdot 窗口的 FU 观察。其中4×13的96个窗口共有576次响应，全部为2拍，写回停顿事件为0。下表每行分别汇总三数据集、每配置12个窗口；跨度是窗内末次 ACCEPT 减首次 ACCEPT，不是整个内核周期。

| 4×13窗口／布局 | 每窗ACCEPT：S0→S2 | ACCEPT跨度：S0→S2 | 末次RESPONSE至窗尾：S0→S2 |
| --- | --- | --- | --- |
| core / basic | 4→8 | 76～87→139 | 57～62→52～53 |
| core / reuse | 4→8 | 5→25 | 97～98→52～53 |
| endtoend / basic | 4→8 | 75～85→139 | 84～88→77 |
| endtoend / reuse | 4→8 | 5→25 | 122～123→77～78 |

这些 GEMV 窗口没有显示 FU 响应或写回拥塞；basic 的请求供给间隙和增加的配置／搬运值得优先调查。reuse 虽增加四次 dot8，整体窗口仍缩短。末次响应到窗尾还包含剩余指令、存储、栅栏、计数／退休收尾和可能的执行重叠，不能全部归因于标量尾部，也不能用本表推导每条指令的独立延迟。下一软件假设优先放入独立 S1 向量累加／对等RVV原型或有定位依据的R2-S3子项；本结果不支持仅因basic退化就修改FU。

## 证据、复算与接续

归档入口为 `evidence/merged-screen-v1/archive-manifest.json`。完整原始记录包括 26 份链接镜像、31 次实际运行、编译来源、输入 SHA、stdout/stderr、计时/退休事件、O2 接受响应、正常完整结果与负控链。归档按原始字节与确定性压缩字节双重校验，外部 EMU/NEMU/flash/AM 库保留来源及哈希，不重复放入 Git。

复算命令见 [MERGED_SCREEN.md](MERGED_SCREEN.md)。离线 PASS 表示从封存字节重做 ELF、黄金数据、CSR/退休、事务、拒错/恢复、重放和统计；不会冒充新的 EMU 执行或当前机器外部实物核验。

## 实际验证状态与接续

| 层级 | 状态与证据 |
| --- | --- |
| 主机／入口拒错 | **PASS：80项**；[实际命令、时间与退出码](evidence/merged-screen-v1/files/support/host-tests-02.json)、[原始测试输出](evidence/merged-screen-v1/files/support/host-tests-02.stderr.log) |
| canonical GNU+nexus-am链接和静态门禁 | **PASS：26 ELF**；构建、源快照、实际机器码和工具版本原文封存在 `files/canonical/` |
| 当前合并硬件真实DiffTest／周期筛选 | **PASS：31次、384正式窗口、4次重放**；[终态](evidence/merged-screen-v1/files/campaign/state.json)、[完整结果](evidence/merged-screen-v1/files/campaign/results.json.gz) |
| 新负控及恢复 | **PASS**；[夹具来源](evidence/merged-screen-v1/files/campaign/negative-fixture/fixture.json)、[精确拒错链](evidence/merged-screen-v1/files/campaign/runs/negative-s2/negative.json)；同镜像正常恢复回执在 `files/campaign/runs/smoke-s2-d0-s07-r0/` |
| 归档原始／压缩字节 | **PASS：962文件，273,863,707原始字节／55,138,570保存字节**；[字节检查](evidence/merged-screen-v1/archive-check.json)，清单SHA-256为 `1d42aa417c2793b997fbf1db89f05c1d2a5dcb49644ff14aa29395621bd129ed` |
| 完整Linux离线复算 | **PASS**；[架构／计数／轨迹／统计复算](evidence/merged-screen-v1-audit-linux.json)，从封存原文重新检查，不执行新EMU |
| 原生Windows归档字节 | **PASS**；[Python 3.13.13回执](evidence/merged-screen-v1-bytes-windows.json)，全部962文件的原始和保存字节核验；Windows完整架构复算 **NOT_TESTED** |
| 可发布Git归档 | **PASS：965文件**（962项内容＋3份归档元数据），清单完整且Git blob逐字节一致；[完整索引门禁](evidence/merged-screen-v1-index-check.json)。新增门禁实际[拒绝漏303文件的初始索引](evidence/merged-screen-v1-index-probe.json)，再仅对这批归档补全暂存；未放宽忽略规则或字节检查 |
| 原B0/H1固定60跑合同 | **BLOCKED**：固定旧EMU实物未恢复；本次不改变旧哈希或旧验收 |
| MERGE-REG整套、R2-SELECT四尺寸、所选组合回归、T17、PPA | **NOT_TESTED／未完成本轮新验收**；不转移历史PASS |

实际静态统计原文：[16个已链接内核的指令统计](evidence/merged-screen-v1/files/support/static-4x13-analysis.json.gz)。归档中的 `support/merged-preflight-01/` 保留一次真实失败：初始新profile把实际builder误当作原仓库入口，核对外部资源适配脚本及pins后修正新profile；第二次完整实物预检通过。旧脚本、旧pins和失败回执均未改写。独立只读Agent分别审查入口、离线审计和取舍边界；跨时区恢复排序问题已在新增审计器中补充真实时间比较及负测，运行入口 `ff75464c…` 未变。这些审查不冒充另一成员的干净环境构建／执行或人工验收。

**下一项具体动作：**按协调Issue确认空闲后认领 `MERGE-REG` 的新夹具子项。配置中的 `build_record` 父目录保留同一6d2／1a23的旧11正常＋2补充记录：先追溯adopted任务的真实来源，再独立复核全部原始日志、输入和checker；以本次新6e8夹具对原canonical matrix0补一次精确拒错，随后同镜像启动新的正常恢复进程。新functional-0替换旧functional-0参与集合判断，不能把先前的正常PASS当作故障后恢复。只有精确12项core＋2补充、全部六个O2目标及来源一致才给出新合同结果；旧9b3缺项保持。

随后按路线将4×13/reuse候选带入R2-SELECT四尺寸比较，并推进独立S1与对等RVV。若MERGE-REG被占用，S1寄存器审查已给出独立模块入口；不修改冻结的 `candidate.py`，不重复运行已合格的S2批次。具体本机配置和输出来源已保存在本归档 `support/`，实时认领、运行保护及成果交接只在[Issue #2](https://github.com/cc77-builder/riscv/issues/2)维护。
