# T17 干净源码构建与新身份运行结果

**T17 在 [CLEAN_CONTRACT.md](CLEAN_CONTRACT.md) 的同主机 Agent 复现范围通过。** 本轮实际重建源码、EMU、团队正常参考扩展及 AM 库，完成 **50 次新 EMU 执行：47 次正常、3 次预期拒错**；最终整核、矩阵与普通 C 归档均在没有 build/out 的独立源码检出中完成原文复算。未继承历史运行 PASS。

操作 ID：`20261024-LiZufan001-t17-clean-0854`；执行者：`@LiZufan001 / Agent`。本轮开始于 2026-10-24 08:54:26 +08:00；工程汇总于 12:06:13 +08:00 生成，交付和发布时间另见计分板及 Issue。完整步骤见 [CLEAN_REPRODUCE.md](CLEAN_REPRODUCE.md)。

主要入口：[工程汇总](evidence/clean-reproduction-v1/reports/acceptance.json)、[跨构建比较](evidence/clean-reproduction-v1/reports/reproduction-comparison.json)、[运行定位](evidence/clean-reproduction-v1/reports/runtime-locations.json)、[最终交付暂存检查](evidence/clean-reproduction-v1/publication-check.json)。工程汇总不替代各份原始审计；Git index 和发布有单独回执。

## 1. 实际工作与验证

以下执行时间均为 2026-10-24 UTC。WSL 与 Windows 宿主时钟存在秒级差异，各自原始回执保持原值。

| 项目 | 本轮证实的结果 |
| --- | --- |
| 干净依赖 | 133 个独立源码仓库，含 126 个硬件子库；独立 Git 对象/index，无 alternates，不复制缓存工作树或旧生成物 |
| 新 EMU 构建 | 01:09:15～01:26:17；实际 make 退出0；429硬件文件、21,236依赖文件、1,672生成物核验 |
| 新支持库 | 01:23:59～01:24:35；NEMU/AM/klib实际构建，另恢复12个仓库；145仓库来源链通过 |
| 新软件构建 | 24个性能 ELF 和1个普通 C ELF，数学、布局及静态 ELF 门禁通过 |
| 软件字节比较 | 24/24 BIN、manifest、kernels.S、cases.h 与旧R4封存相同；完整ELF不同，但所有加载段字节相同，差异限于未加载debug及RISC-V属性段 |
| 普通 C | 01:39:08～02:05:28；3次新执行，1预期负控、2正常；16公开函数、48不同case、96正常case执行；每次正常运行1008条vdot提交 |
| C物理审计 | 02:07:50～02:07:59；实际输入、全宽结果、CSR、退休及原始轨迹通过；新EMU/NEMU均0 |
| 整核 | 01:51:18～02:36:06；14次新执行，12 core＋2 supplement；13正常、1预期负控；117唯一case／124次执行，control七项义务及六类O2覆盖完整 |
| 整核物理审计 | 02:37:13～02:37:43；原始日志与14组spawn回执逐项绑定，完整正常轨迹和负控/恢复通过 |
| 公平性能矩阵 | 02:44:36～03:44:56；24正式＋8 replay＋1负控，384正式窗口、192全窗口replay比较全部通过；进程严格串行 |
| 独立检出复算 | 最终整核、矩阵M03、普通C C02在04:02～04:04完成；原物理目录Python访问及显式子进程路径受限，运行期拒绝事件为空 |
| 边界测试 | 原审计器17项实际夹具测试通过；旧discover路径17项明确SKIP，未计为PASS；新增传输层另以真实缺陷重现及最终包独立复算验证 |
| 跨构建复核 | 24个加载镜像完全相同；旧/新两批768个对应窗口的cycles和instructions全部相同，其中384个正式measured窗口全部相同 |

整核与普通C正确性阶段采用3＋1最大并发，统一CPU affinity 0～3，总预算最多四核；性能开始前这些进程及重型原文审计均已终结。性能前后指定构建/仿真进程检查均为空，保存了[前](evidence/clean-reproduction-v1/reports/performance-resource-before.json)/[后](evidence/clean-reproduction-v1/reports/performance-resource-after.json)事实。这是进程边界观察，不是整机CPU全程监控。

## 2. 固定身份

| 对象 | SHA-256 / Git提交 |
| --- | --- |
| 硬件执行源码 | `34bae6d4acceac939f958199dae53c14bc1f6183` |
| 新 EMU | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 新正常 NEMU | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` |
| 新 AM 库 | `57501f59d55d1b15116d9022ffc2d5efcc74bcde8c5674d7f31db0714e04b933` |
| 新 klib | `f45d8c2049384123642b8c5d4a86f46be285d785ac5d16438eee510347eafda1` |
| 有效 identity-02 | `4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb` |
| 整核控制器 | `593298f4119d5a8ce8dd925ec5836c70e0d8bf4cbcf7cf0b221570ffc669f1a2` |
| 支持来源/矩阵基础审计器 | `bd3878cec30f63394ecbfe9bdd5ad08bbb15be2e04fdd6e439371229ffb8bd75` |
| 整核独立审计器 | `20bebd4f5526a3522a09c2324e683d34b55997930c5078e89c3e5d04a6733412` |
| 传输v2工具 | `df1be9196293bb637d356c9bfe69a991130297e4f9f77e9ce95e02aa06a9b628` |
| 独立访问依赖探针 | `57f31bb70dafa3154dc22e09c635dde1f4c140405717d98053d781dc2ca43cd4` |

实际构建工具记录为 GraalVM JDK21.0.12、Mill0.12.3、Verilator5.052、Clang19.1.7、GNU Make4.3、Python3.10.12、firtool1.62.1。工具已安装，未声称本轮重新安装或逐个锁定全部可执行文件。

## 3. 本轮性能与采用判断

每个候选为三个数据集、合计12个正式measured样本。比较对象是同一C ABI完整调用窗中所有合格RVV候选的最快者；四个形状的最快RVV均为S1/reuse。下表的周期降低按 `1 - vdot周期 / 最快RVV周期` 计算。

| 固定形状 | S1/reuse vdot均值周期 | 最快RVV均值周期 | vdot周期降低 | 当前证据支持的选择 |
| --- | ---: | ---: | ---: | --- |
| 4×8 | 169.75 | 187.50 | 9.47% | S1/reuse vdot |
| 8×32 | 292.50 | 300.75 | 2.74% | S1/reuse vdot |
| 16×64 | 717.25 | 779.50 | 7.99% | S1/reuse vdot |
| 4×13 | 219.75 | 187.00 | −17.51% | S1/reuse RVV |

这里复现了原R4的固定调用窗结果，没有制造新的软件或硬件加速收益。384正式窗口和192内部replay比较来自本轮新EMU执行；与旧批768窗口相同是事后观察，不作为本轮运行验收的替代条件，也不保证未来布局/工具/程序仍相同。4×13继续保留较快RVV；完整统计含所有S0/S1、basic/reuse与vdot/RVV候选，见矩阵原文审计。

本包不修改默认函数选择或新增dispatcher。下一步R5/G5可据此发布固定符号清单、使用入口和回退说明；任何改变调用者、数据布局或测量窗口的新程序，仍需自己的验证。上述数字不等于完整LLM或任意应用端到端性能。

## 4. 最终归档和真实可迁移性缺陷

| 最终包 | 载荷文件＋根文件 | 原始载荷字节 | 存储载荷字节 | Manifest SHA-256 |
| --- | ---: | ---: | ---: | --- |
| [整核](evidence/clean-reproduction-v1/fullcore-archive/archive-manifest.json) | 432＋2＝434 | 203,184,356 | 13,066,329 | `f6f45c7a99e3004d4e98b1a622a8b7c6f1e7c249f5a2fb47328a59d81c020719` |
| [矩阵M03](evidence/clean-reproduction-v1/matrix-archive/archive-manifest.json) | 1377＋3＝1380 | 256,971,458 | 17,752,535 | `bc766760a098f5d775615a9ec8e383920914f502a10b480ccce1ad4b188092d7` |
| [普通C C02](evidence/clean-reproduction-v1/c-archive/archive-manifest.json) | 115＋3＝118 | 16,928,444 | 1,111,872 | `5a54192270903ae155fa5d372088169f0b4547cce5674863d3401dabda7cf0f1` |

原冻结打包器按“位于repo之下”分类工具，把本轮 `build/emu` 封入了 `tools/build/emu.gz`，多存71,178,528原始字节，与排除声明不符。M01在同目录及独立无build检出都可通过原审计，不能误记为运行失败；但原C归档的审计流程对全部tools文件逐一与当前repo比较，实际在独立检出因缺少 `build/constantin.txt` 拒绝，见[预期失败回执](evidence/clean-reproduction-v1/prior-attempts/c-staging-rejection-02.json)。

新增传输工具保留冻结源码及原打包输出，只重封精确EMU和全局AUX位置。最终EMU仍由原SHA表示，C的两项全局AUX引用矩阵既有载荷；每个运行私有AUX不动。其他载荷在重封时逐文件验证原存储字节。新工具还阻止报告/归档写入源包、矩阵锚点或运行输入目录。补齐输出保护前的M02/C01仅作中间封存尝试保留，最终使用M03/C02；这些变更均未重跑EMU。

最终[矩阵原文审计](evidence/clean-reproduction-v1/reports/matrix-archive-audit-03.json)、[C原文审计](evidence/clean-reproduction-v1/reports/c-archive-audit-02.json)、[整核原文审计](evidence/clean-reproduction-v1/reports/fullcore-detached-audit-01.json)与三个guard报告绑定各自输出SHA，均通过。探针能拒绝Python文件/目录读取和显式子进程原路径，但不是OS沙箱，也不监控子进程内部所有文件访问。已安装GNU工具和临时抽取目录仍可使用。

Windows初次矩阵索引因普通路径长度限制失败，原始回执已保留；改用扩展路径后，1380个矩阵文件与118个C文件均通过原生Git索引检查，整核434文件此前已通过。未修改系统设置、归档或冻结检查器。

跨系统复制逐文件核对原始字节；归档索引分别按各自2根/3根格式检查。交付总集合、源码文档与外部报告由最终暂存检查逐blob核验，报告本身再单独核验后提交。源码、归档及原始失败证据不会因发布重建或改写。

## 5. 保留记录与边界

初次源码准备因Linux Git扫描NTFS缓存产生不适用的工作树判断而失败；修正为只clone对象后使用全新clean-02。退役identity-01、早期支持来源审计、测试兼容版本、原矩阵封存、传输中间版及原C归档依赖失败均保持可定位，见[运行定位](evidence/clean-reproduction-v1/reports/runtime-locations.json)与 `prior-attempts/`。有效identity-02、原九份脚本、运行日志和最终整核包均保持其已验证身份。

这是同一主机、保留工具/下载缓存、独立源码与产物的Agent复现，未取得新机器安装资格或成员人工ACK。冻结官方权威判定器、旧运行证据和旧合同没有修改；正常NEMU使用既有团队扩展配方在新目录复现。本轮未改变RTL算法，未新增ASIC面积、时序、频率或功耗结论，也没有完成赛事材料或赛事提交。

MERGE-REG已单独完成并发布，见[对应结果](../fullcore/MERGED_REGRESSION_RESULT.md)及提交 `c9132b8d7f284ad7e76550315214b5b2ca431f79`。本T17结果不回填旧B0/H1或旧负控9b3的BLOCKED状态。工程下一步是稳定入口/回退交付与尚有实际价值的性能工作，而不是继续重复这些已完成的仿真。
