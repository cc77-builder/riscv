# Firstdot：首块直接初始化的实跑结果与可选 C 库

操作 `20261024-LiZufan001-r2s1-firstdot-1458`；@LiZufan001 / Agent；2026-10-24。本页记录独立软件候选的实际资格与取舍。合同分别为 [固定调用窗](FIRSTDOT_CONTRACT.md) 和 [普通 C / 独立库](FIRSTDOT_C_CONTRACT.md)，使用方法与回退见 [FIRSTDOT_README.md](FIRSTDOT_README.md)。

## 1. 结果与采用范围

firstdot 已完成完整四形状、三数据集、同调用路径的性能矩阵；三个整块形状的 reuse vdot 同时优于本轮原 S1 reuse vdot 和最快合格 RVV。K13 的 vdot 虽较 S1 改善，仍慢于 RVV，因此继续保留原稳定 RVV 选择。本轮以独立 `firstdot_gemv_*` 名称提供可选接口，原 [R5 稳定默认入口](../r2-select/STABLE.md)及其库保持原字节。

以下每格均为三数据集 × 四个正式 repeat，共12个样本。数字是固定 GEMV C ABI 调用窗的处理器周期均值；“相对RVV”以同一轮全部合格 basic/reuse、S1/firstdot RVV 的最快者为分母。

| 形状 | S1 reuse vdot | Firstdot reuse vdot | 相对 S1 少周期 | 本轮最快合格 RVV | 相对最快 RVV 的周期 |
| --- | ---: | ---: | ---: | --- | ---: |
| 4×8 | 169.75 | 157.75 | 7.0692% | 187.50（s1 reuse） | 少 15.8667% |
| 8×32 | 292.50 | 282.25 | 3.5043% | 300.75（s1 reuse） | 少 6.1513% |
| 16×64 | 717.25 | 707.00 | 1.4291% | 778.75（firstdot reuse） | 少 9.2135% |
| 4×13 | 219.75 | 204.50 | 6.9397% | 187.00（s1 reuse） | 多 9.3583% |

16×64 的 RVV 分母必须使用本轮 firstdot 侧的778.75，而不是 S1 侧779.50。两个变体 ELF 的 RVV 整个8KiB槽机器码相同，所在程序此前执行的 vdot 不同；本轮未单独识别 RVV 窗口微小差异的原因。这里保留全部样本并选择更快者，没有把差异隐藏成相同周期，也没有据此宣称 RVV 代码被优化。K13 两侧 reuse RVV 均值187.00，相等时报告 S1 一侧。

对应的窗口退休指令计数如下。它使用冻结测量器的 `d.instret-a.instret`，周期窗则是 `c.cycle-b.cycle`；这些数字包含共同的测量边界开销，不是 leaf 函数的机器指令长度。

| 形状 | S1 reuse vdot 窗口 instret | Firstdot reuse vdot 窗口 instret | 最快 RVV 窗口 instret |
| --- | ---: | ---: | ---: |
| 4×8 | 54 | 44 | 54 |
| 8×32 | 202 | 182 | 124 |
| 16×64 | 672 | 632 | 372 |
| 4×13 | 136 | 126 | 54 |

收益是固定 T17 硬件上的软件收益。窗口包括状态建立、加载、计算、完整128位输出写回、真实调用/返回、参数搬移及结果观测指针恢复；测量 wrapper 在窗外保存/恢复栈和自身寄存器，这部分不计入。窗口也不包括任意应用的数据打包、结果重新布局、启动和全部业务流程。没有完整应用、LLM、芯片频率、功耗或新 ASIC PPA 结论。

## 2. 改了什么，以及为何能改

现行项目规格的 dot8 指令从零计算点积并完整覆盖128位目的寄存器，高96位清零，不读取旧目的。原 S1 每个行组先清零各行的最终累加寄存器，再让每行首块的 vdot 写临时寄存器并做一次向量加法。firstdot 让这些首块 vdot 分别直接初始化各行的最终累加寄存器，删去对应清零、首块累加和两次相关配置；后续点积仍按原顺序累加。

变换保留点积条数、输入读取边界、K13 标量尾部及必需配置、毒化初始状态、C ABI 和完整结果语义。首条 vdot 的目的从旧临时寄存器改为 v0，因此本轮重新验证真实新目的寄存器的 bit100 拒错和同 BIN 恢复，不能沿用旧负控的目的/PC。

新增模块通过私有 renderer/检查器实例复用已有团队代码；旧生成器、原验证器、官方权威代码及 RTL 不变。构建可使用最多4个独立任务，避免全局 renderer 替换产生串扰；所有 EMU 性能执行串行。

| 身份 | 固定值 |
| --- | --- |
| 软件来源基点 | `137b44befb041439a018a1079577cc000df1ee03`，附本轮新增源码哈希 |
| T17 硬件源码 | `34bae6d4acceac939f958199dae53c14bc1f6183` |
| EMU SHA256 | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 正常 NEMU SHA256 | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` |
| 原 T17 identity-02 SHA256 | `4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb` |
| candidate / gate / experiment | `79c1c808…` / `fc113878…` / `90ade145…`，完整值在归档源码清单 |

硬件仍为 O2 两槽/H1；无停顿首响应2拍、II=1。时钟、复位、FU接口、位宽和硬件流水线没有修改。本轮复用其既有硬件实现，通过当前软件的真实整核执行验证影响，不新增硬件综合或STA结论。

## 3. 性能资格与证据闭环

最小8×32/d0实验先完成5个进程：新 bit100 负控、同 BIN firstdot 恢复、S1 正式、两变体全窗口重放。通过事先的“同时胜过 S1 和最快 RVV”条件后，只构建并运行剩余22个正式图和6个重放，复用先导原始执行，不重复计算样本。

| 层级 | 本轮实际结果 | 证据入口 |
| --- | --- | --- |
| 变换 / 并发 / 身份 | 32个原探针对照、24串行与24并行精确再生；形状/输出/覆盖与产物篡改检查通过 | [host-03.json](evidence/firstdot-v1/reports/host-03.json) |
| GNU / 编译后模型 / 布局 | 24个性能图通过；每个新 S1 BIN/内核/公共对象等于对应 T17 封存对照；变体槽外字节和全部 ALLOC 布局一致，两个 RVV 整槽不变 | [矩阵归档](evidence/firstdot-v1/matrix-archive/archive-manifest.json) |
| 负控与恢复 | 性能负控的实际指令 PC `0x8000230c`，word `0x0388000b`，vd0 / bit100，预期退出1；同 BIN 新进程正常恢复 | 同一矩阵归档的 probe 原文 |
| 完整矩阵 | 24正式图、384正式窗口，数学、完整128位、CSR、真实退休路径、计数器标定和O2协议通过 | [matrix-audit-01.json](evidence/firstdot-v1/reports/matrix-audit-01.json) |
| 独立进程重放 | 四形状dataset0 × 两变体，共8次；每次24个 first/warmup/measured 窗口，192项 cycles/instret 比较完全一致 | 同一原文审计报告 |
| 证据拒错 | 对已重新计算归档哈希的4种语义篡改仍拒绝：缓存性能、正常退出、负控目的、伪完整矩阵 | [probe-evidence-tests-01.json](evidence/firstdot-v1/reports/probe-evidence-tests-01.json) |
| 普通 C / 库 | 3次实际进程：1次新负控、正常恢复与重放；16函数、48不同case、96正常调用；完整库对象与链接叶函数一致 | [C审计](evidence/firstdot-v1/reports/c-audit-01.json) / [库检查](evidence/firstdot-v1/library/library-check.json) |
| 独立来源目录审计 | 独立基点检出＋逐文件哈希候选快照；无build/out，限制访问原运行根，完整矩阵/C原文复算及库字节检查通过，C报告与原件完全一致 | [独立审计回执](evidence/firstdot-v1/reports/c-detached-guard.json) |

性能部分共33个真实EMU进程：32正常、1预期负控。矩阵归档包含1467个载荷，原文253,252,835字节，存储17,634,226字节；manifest SHA256 `0c8d3159c91aa3c934c7bfb7f2640906844246e812c0b5bfc556cdfb86d0d3b4`。原文审计报告 SHA256 `bd515ccff25f1922b9ee7b6c83a853daf0edd95634ad51b244ae8a4ae6e9fd2e`。

现场运行前后核对真实 T17 输入身份；封存时核对输入闭包。离线审计从保留的 ELF、源、命令、退出及原始轨迹重算，未启动 EMU，也不重新验证未分发的 EMU/NEMU/AM/GNU 大型实体。旧内部 R4 UART/状态标签保留，资格由本轮外层合同和精确身份确定。先导归档另保留，以便复算当时的4种语义拒错检查。

## 4. 指令减少如何体现在周期上

basic 与 reuse 必须分别判断；不能用少指令数量代替周期证据。

| 形状 | S1 basic vdot 周期 / 窗口 instret | Firstdot basic vdot 周期 / 窗口 instret | basic 少周期 |
| --- | ---: | ---: | ---: |
| 4×8 | 206.75 / 68 | 197.50 / 52 | 4.4740% |
| 8×32 | 648.50 / 308 | 645.50 / 276 | 0.4626% |
| 16×64 | 2216.50 / 1108 | 2213.00 / 1044 | 0.1579% |
| 4×13 | 254.00 / 168 | 233.25 / 152 | 8.1693% |

例如8×32/basic 少32条窗口退休指令，但只少3周期；reuse 少20条却少10.25周期。这直接说明删指令比例不能预测周期收益；本轮没有单独识别依赖、供数或配置各自的贡献。

对已审计的8×32/d0/reuse四次正式重复，保留了按实际接收顺序配对的 enqueue/accept/response/commit 记录，处理同周期ROB退休与重新分配。观察如下：

| 事件均值（相对该窗口开始） | S1 | Firstdot |
| --- | ---: | ---: |
| 序列中首个被接受的 vdot 的 enqueue | 87 | 80 |
| 该指令 enqueue→accept 间隔 | 22 | 23 |
| 该指令 accept | 109 | 103 |

这里的 enqueue 指“序列中首个被接受的指令”的入队，不表示所有指令中最早的入队。该探针中 firstdot 第一次接受早6拍；first→last accept 间隔119→115，末响应到窗口末62.50→62.25。三段差值合计10.25周期，仅是可观测事件间隔的算术分解；不能分别命名为“加载节约”“配置节约”或“存储节约”。该诊断中的 `VFEX4_WAIT` 事件为0；已有协议诊断显示这些窗口响应2拍、无写回阻塞。证据见 [有序轨迹诊断](evidence/firstdot-v1/reports/probe-order-01.json) 和矩阵审计的 `fu_window_diagnostics`。

源观察还发现 firstdot/reuse 的重复字面向量配置次数，在4×8、8×32、16×64、4×13分别为3、7、13、2；对应RVV分别为1、1、3、0。三数据集函数体相同，观察器绑定完整矩阵及其审计哈希。[configuration-observation-01.json](evidence/firstdot-v1/reports/configuration-observation-01.json)保留具体位置。

这只是“相同AVL/vtype、之间没有显式配置写”的源事实，不是已经证明可删除，更不是预测可节约若干周期。可选下一步是 R2-S3 的单一有界假设：同时检查 vdot 与 RVV 的重复配置，先证明正常完成/vstart和编译后状态不变，再做8×32/d0同入口强RVV配对；有收益才扩大。当前轨迹不足以优先支持改变FU乘加延迟、队列深度或写回宽度，故本轮没有开展新RTL。

## 5. 普通 C 与可使用交付

普通 C 批次使用新的 firstdot 公共符号，但沿用原普通 C harness、Makefile、标量黄金值和判定要求。48个不同case覆盖16个函数与三数据集；真实正常恢复和独立进程重放各执行全部48个case，每次1008条vdot提交。数学结果、高96位、输出canary、CSR、live DiffTest与O2事务均通过。C负控绑定实际故障指令 PC `0x800003d8`、word `0x0388000b`、vd0 / bit100，退出1；其后同BIN正常恢复。日志中的 XSTrap abort-event PC `0x80000400` 单独记录，不与失配指令PC混淆。

C批次于08:18:12～08:41:37 UTC完成。运行结束state的 `active_pid`、`active_result` 均为空；本轮合计36个EMU进程，34正常、2预期负控。普通C批次不测性能，也不增加性能矩阵的正式样本。构建阶段把16个公共叶函数与三数据集的矩阵版本逐一比较，共48项机器码对应；因此公开源码的身份与矩阵资格相连，而不是只凭函数同名继承结果。

实际导出后的 `gemv.S` SHA256 为 `1e1aa8ca665559efa6acab2648f4614c6121422aaf400d78c192e6accad5da47`，`gemv.h` 为 `8ff3e08d098f000962beeaf898730939ee83bd4ea8eaf9be1c03c80f93c9db83`。C归档含129个载荷，原文17,493,608字节、存储1,185,337字节；manifest为 `47859f1c12d5311ef554803c6976c8699ebafc164e2bdd876cfd0c6a6f2a2ec1`。其原文复算连带重新审核完整性能矩阵，报告SHA256为 `e178c590836330e9ed29b6b083527422c5d544e2dbde01b911c0e4978e2644cc`。

独立 `libfirstdot_gemv.a` 的SHA256为 `9e12de07d363a2627d7d33cff401da257c30487d59b3a3f7029bb3a262fbd33e`；其中完整27,416字节对象为 `b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af`，与合格普通C构建对象逐字节相同。真实GNU链接覆盖全部16函数，保留16项 `R_RISCV_64` 入口表引用，所有leaf机器码一致。[库拒错检查](evidence/firstdot-v1/reports/c-library-host-01.json)还拒绝了重新计算包装哈希后的四种坏产物：缺consumer、错成员、缺产物和错入口表引用。

[使用说明的实际编译检查](evidence/firstdot-v1/usage-check/report.json)从发布汇编重建出同一个完整对象，并编译文档内的 `gemv8` C11示例、用 `ld -r --no-relax` 链接静态库；16个leaf一致，无未解析强符号。该示例本身没有实跑，也没有新增应用性能测量。最初的示例提取步骤受跨Shell反引号展开影响，在GNU命令之前失败；已完成的C运行、导出、封存和库检查没有重跑，只在新 `usage-check-02` 输出中补齐剩余步骤，保留原失败回执。

公开接口均位于独立命名空间，四形状各basic/reuse × vdot/RVV，共16个函数。输入为紧接的行优先INT8矩阵和向量；每行输出占16字节，不能传紧密INT32数组。对齐、状态、打包例子、静态库链接、源重建和回退步骤见 [使用说明](FIRSTDOT_README.md)。库中的全符号consumer只作链接覆盖，不是可运行的多形状应用示例。

R5 默认及其回退继续可用；显式 `firstdot_gemv_*` 不受旧 `XS_GEMV_FORCE_RVV` 宏控制。回退须改回稳定入口并重新编译调用端。新caller、最终布局、平台或应用不自动继承本轮固定窗口周期。

## 6. 发布与接续边界

在独立Linux目录以 `--no-hardlinks` 建立完整历史检出，基点仍为 `137b44befb041439a018a1079577cc000df1ee03`，再传入逐文件哈希核对的新增源码和证据快照；这不是已经提交的干净候选，也不是新机器安装。检出内无 `build` / `out`。复用未修改的T17访问保护器，限制Python文件/枚举访问及显式子进程参数，拒绝访问本轮原运行根、T17原根和旧T12根，保护器自检通过，审计中没有命中禁止访问。

该独立审计于08:53:57～08:54:36 UTC实际完成，重新读取已分发原文，完整性能矩阵和C资格通过；生成的C报告与原审计逐字节相同，SHA256仍为 `e178c590836330e9ed29b6b083527422c5d544e2dbde01b911c0e4978e2644cc`。随后在该目录执行库字节检查，结果也与原件一致。[快照清单](evidence/firstdot-v1/runtime/detached-source-snapshot.json)明确基点与未提交增量，[独立汇总](evidence/firstdot-v1/runtime/detached-detached-summary.json)保留实际范围。该访问保护不是操作系统沙箱，也没有重建硬件或增加EMU/NEMU运行。

跨系统交付逐文件比较SHA256，NTFS工作树的索引检查使用Windows原生Git。[发布检查器](evidence/firstdot-v1/runtime/publication-check.ps1)要求本轮全部源码、公共源和证据的准确库存、stage-0索引与原始字节一致；唯一例外是原计分板已有的CRLF，单独证明其Git LF形式没有其他变化。校验原始工作文件字节数与已暂存字节数的含义不同，不混称两者。索引回执见 [publication-check-01.json](evidence/firstdot-v1/reports/publication-check-01.json)；回执自身不进入自己的库存，随后单独暂存并核对blob。发布提交及正常快进窗口以 [Issue #2](https://github.com/cc77-builder/riscv/issues/2) 的实际事件为准，不回填本提交自引用SHA。

收束阶段保留了两次快照准备失败：一项在启动WSL前超过Windows命令行长度，另一项因脚本拼接形成语法错误、只留下脚本副本。最终使用经过语法检查的明文脚本文件及短启动参数完成；没有重跑任何已合格EMU、C或库步骤。

全部原生尝试、驱动、源码传输、物理路径及状态入口在 [runtime/locations.json](evidence/firstdot-v1/runtime/locations.json)；完整原文在模块既有 evidence 层级。未修改原来源工作区、旧冻结基线、官方权威程序、PPA配置或部署环境。

本轮闭合首块初始化子项和其独立C交付，不宣称全赛题技术要求全部完成。新机器安装、成员人工ACK、任意完整应用/LLM，以及新的ASIC面积/时序/功耗仍在各自原合同边界外。后续先复用本轮原文与独立接口，再根据实际收益决定推进 R2-S3 或单独更新稳定选择；不因本轮存在候选而重复已完成的33次性能仿真。
