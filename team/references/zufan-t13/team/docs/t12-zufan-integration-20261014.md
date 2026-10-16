# T12 向团队 zufan 的离线整合验收（2026-10-14）

已将最终受测软件、完整审查历史和原始证据整合为本地候选。普通 merge 为 **`778e552e477fa67cbf529130414d4bbe2ea2c956`**，之后只追加入口/证据修复/验收文档提交。最终候选完整SHA、干净状态和可提取bundle记录在授权工作区 `publish-zufan/FINAL.md`、`FINAL.json`；本文件不是联网发布回执。本次未联网、未push、未改原PR分支，主审ChatGPT负责最终联网核实与正常推送到 `cc77-builder/riscv:zufan`，不代签队友ACK。

## 来源与历史保留

| 固定对象 | 完整SHA | 本机核实 |
| --- | --- | --- |
| 最终实现 | `1ba275411d41b6454b14ecfc537be10cd7202739` | 原`repo`干净；parent=`8af7b21857ba2c65dbc4d835f7b2152cd6684875` |
| 已发布审查 | `f188f6f7588270714d94d970fe36f2f2cdda15b9` | parent=`3a323a18e7e902501ff9968193b65aac3a7ae965` |
| 本机审查后继 | `e5d084bbdcfad6936ccad29dff4c1df00f5abfef` | parent为上述f188；完整纳入 |
| 用户给定团队zufan | `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3` | parent=`1bd6f1d9c9485695876ff37a77fbb175a5125983`；离线对象成立，未冒充实时远端回读 |
| 实际EMU硬件来源 | `fcb16a8764d342339670df0bbf1bc67ef2028b86` | 固定硬件来源，非本次重编 |

1ba与f188/e5d的唯一共同祖先为 **`a4fea8f69f8c2c58f986858481257d3424a903f0`**；6bf是两条线的祖先。merge第一父为e5d，第二父为1ba，完整保留f188、原Draft `f8e8276681e0f4cfdc4ce0d8e2a76ebb4897493e`、独立审计 `6648cbec24079041d20eaba6f1658d4a9de93d45` 及双方后继历史，未squash/rebase/重写。

在全新的 `/home/lizufan/chatpc-workspaces/xiangshan-t12-20261014-r2/publish-zufan` 中正常 `git clone --no-hardlinks`，仅从两个已存在本地对象库fetch固定提交，无alternates或网络来源。原Windows库是 `/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/t12-perf-20261014/supervisor/publication-r2-20261014`；其Linux可见状态实际含464个已跟踪改动，以及未跟踪`parent-audit-r2.bundle`、`parent_audit_t12.py`，不是干净树。全部原状记录并保持，未将未提交改动批量带入候选。所有来源只读，未reset/clean/stash，未改safe.directory、ACL或安全设置。

严格源库检查另发现Windows `.git/index` 文件哈希发生变化，保留实际exit1而不将该项写成PASS：开工`8fa5cd554ca74613efd670a29ca8240ae7f95fc422f0697aefb0ef943e39b9a4`，后读`2ed44a4eaa5c373b176121e6315ada14681cf929b975217914ccfbea5ecf3ad8`，大小均146,311字节，后读mtime为14:28:35 UTC。1145个索引条目仍逐条等于原e5d HEAD，无暂存差异，HEAD/refs/工作树状态和原文件字节一致；两个未跟踪文件未变。本任务没有发出来源写入命令，变更执行者未被观察，不能断言来源`.git`所有原字节均未变。此项与源码/证据内容验收分列，未恢复或覆盖来源索引。

## 合并分析与归档修复

普通merge无文本冲突，未使用全树ours/theirs覆盖。合并树 `85fcd2ac64a14c7a1250ed3b0cfbc686bdf86831` 的1377个最终实现条目与1ba完全相同；另50个审查线独有条目与e5d完全相同。`audit_t12_live.py`及9项测试、旧审查/性能文档、默认未启用的硬件实验包全部保留。后续历史报告仅加前缀标注，原正文逐字节保留；旧AGENTS另存[历史快照](history/AGENTS-before-t12-zufan-integration-20261014.md)。

e5d相对f188新增12个独立审查报告/回执/文本归档文件，无功能代码变化，具有复现价值，应保留。它审查的是固定b827版本；不能把原反例当作后继1ba仍存在的错误，也不能把参考层测试当硬件候选完成。

本次实查发现其 `independent-review-text.tar.gz` 的Git blob不匹配原`archive.json`：原清单4,251,053字节，继承blob仅4,251,007字节，SHA256为`14f748180e3e3f2ad36a9e69bd76878115270ecc4e6e4c6bbdee8e9f6a65f05c`，严格校验实际exit1。原因已逐字节证明：把原gzip中的CRLF替换为LF恰好得到坏blob，上级`team/** text`缺少gzip例外。

从`parent-validation/review-package`恢复原包，同时与Windows工作树原包核同，两份都匹配原声明SHA256 **`8916a64dc4bf2c21e1c772f4d927f338ecb4ec2a290019e423ca5b2c64d03a96`**。原清单未改；恢复后完整gzip CRC及739个成员（738个清单文件+清单本身）通过。追加`.gitattributes`保护压缩字节，并在提交时再核Git blob。坏blob仍在e5d和merge历史中，失败日志也归档；没有放宽校验或重写失败。此修复仅恢复证据字节，不改变测试/RTL功能。

硬件实验包中另有4份历史JSON/hash清单原blob含CRLF，与工作树原字节相同，但上级文本规则会让Git显示待转换。只对这4个路径新增`-text`属性，保持其原blob及所有实验内容不变，没有用重新规范化文本篡改历史清单。

## 源码、镜像与固定资产

407个生产/依赖条目，包括`src/`、`build.sc`、`.gitmodules`及10个gitlink，与1ba、e5d、6bf及fcb一致。`src`树为`df6e6533b7d34fa6b6daacc639c6161f8f67435e`；`build.sc` blob为`ab8f2f0c9741996528ff011064f3582db1df0641`；`.gitmodules` blob为`599b75dda3f5ad9faca659bddb579cd90d024743`。608个非报告/证据源码文件逐字节、逐模式与1ba核同。

11个实际构建/运行/判定输入全部与1ba及lean受测源`8af7b21857ba2c65dbc4d835f7b2152cd6684875`的Git blob相同。原190仍按其a4源绑定：其中`main.c`、`generate_t12.py`、`t12-tests.py`、`check_t12_compact.py`四项与后继不同；其余7项一致。独立复核按各自原SHA读取真实BIN/ELF/生成输入/编译和进程回执，不把候选SHA冒充旧镜像的构建SHA。1ba新增最终复核/证据内容全部保留。

黄金补丁及manifest保持团队6bf已验收的1.1.0；实际NEMU源码、5项固定外部依赖、生成输入、平台配置和共享库由原`artifact_guard.py`完整复核，输出与原FINAL记录逐字节一致（SHA256 `e96114470ec07ff44f1ce77c0f17ea9d0ff7e0a368b7903fbc382fd3a985ab10`）。fcb是更早的硬件来源提交，当时补丁仍为历史1.0.0；1.1.0由1bd/6bf既有验收引入，本次未修改黄金结果或CSR比较。

| 固定资产 | SHA256 / revision |
| --- | --- |
| EMU | `43fd7b094a3fb8676395dc97ca08443fb2d2d37d1dbfea0d7b9078c67087718f` |
| NEMU reference | `e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae` |
| flash | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994` |
| AM | `086a238062fdfb3281b745a537b361983d0154b5`，原树干净 |

原FINAL的51项工具链/便携库及主机工具hash也重新核实。没有安装工具、EDA/AM/全核重编，没有修改时钟/复位、128位接口、signed19精确和范围、单uop或共享busy/ready合同。

## 本次真实验收范围

每条实际命令的argv、cwd、开始/结束时间、exit及日志hash在[小型证据归档](../evidence/t12-zufan-integration-20261014/README.md)；本机原始回执在`publish-zufan/evidence/commands/`。

| 本次运行/复核 | 真实结果 |
| --- | --- |
| 合并后Python测试 | `team/tests`全部107项通过（含审查线9项），exit0 |
| 原算术/编码模型 | 35项通过，5份生成数据原字节一致，exit0 |
| C judge普通与UBSan | 原judge25检查、T12 judge98,321检查，各普通/UBSan模式均exit0；不翻倍计唯一用例 |
| `verify_t12_evidence.py`复核实际original190 | 5片完整190计划身份、原源/工件/工具/进程/DiffTest/GOOD TRAP/最终ELF跨度复核通过，exit0 |
| 同脚本复核实际lean199 | 5片完整199计划身份，同类完整复核通过，exit0 |
| 旧矩阵shard0日志复核 | 15唯一用例通过，实际旧回执exit0；不是本次新DUT执行 |
| 固定NEMU短参考层 | 16,800双路组+75 known+75 batch重新通过，7/5/14条序列；不计全核 |
| 归档/来源 | 原T12全部275个blob、266个归档来源、3份SHA256SUMS共295条、既有139个gzip及21份历史失败原件核验通过 |
| 原始性能记录 | 27 original+36 lean=63窗口，四个64位计数、AB/BA/empty顺序、JSON/CSV均与实际重读结果一致 |

**本次新增DUT运行0**；本次是已跑全核的源/工件复核和主机/参考层回归。整合没有功能代码变化，无需以新全核重跑或EDA重编阻滞交付，也没有用单测冒充全核验收。旧T10/T11历史117唯一用例曾全核通过；此前本轮T12重新编译运行15/117，剩余102本轮未重跑。original190和lean199是两个重叠计划，不能合计为389个唯一ISA用例；a4没有的循环计数/恢复前快照证据不回填到a4。

初始输出不完整、compact及000/003/006/008的timeout124、限周期exit0非PASS均保持原结论。所有窗口原样保留，没有最快筛选、空窗口扣除或宿主时间换算。

## 时序边界、发布范围与未完成项

本次明确允许已验收的软件、验证和证据成果合入zufan。早期“全部STA完成前不得合并”的整体闸门由当前授权和实际验收范围取代；[历史门禁](t12-review-gate-20261014.md)只保留其对**硬件候选晋升**的有效要求。

`NewPipelineConnect`数据寄存器切断RF/OG2/旁路至融合乘法的跨级组合推断；ready控制仍须独立分析。详见[时序前审](t12-timing-precheck.md)。E0接受/E2沿后有效/E3响应/II4仅为现有局部FU合同；II3融合未启用。rdcycle流水/序列化未校准，63窗口不能宣称精确FU latency、Fmax、时序闭合或官方性能成绩。

未完成项目继续明确保留：102项旧矩阵本轮复跑；年轻vdot已发射后取消、真实ROB/FTQ索引绕回、共享WB碰撞的事件观察；候选真实RTL A/B、门控/OG2/WB/ROB集成；STA/Liberty/PVT/SDC/布局后setup与hold/PPA；官方规格确认、M/HS/VS委托虚拟化和人工签字。没有启动新硬件开发目标。

本次沿用用户预设`gpt-6-astra/max`会话，没有子代理、嵌套Codex或其他模型调用，未修改模型/系统/网络/沙箱。原树和未跟踪工件完整性由交付回执再次确认；最终联网发布仍由主审处理，本报告不虚构任何push/远端新SHA/ACK。
