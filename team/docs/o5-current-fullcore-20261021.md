# Linux LF 输入准备与当前 O2 全核复验（2026-10-21）

本轮承接 `7d0630202`。范围为 James_Hotten 的当前源码复验；main 和远端不改，生产 O1/O2 默认开关保持关闭。当前受测构建显式开启 O2，不改变默认选择。本文随实际结果更新，不能把输入就绪当作完整 G3 或 T17 完成。

已完成的输入及主机审查证据先封存于 [o5-inputs-20261021](../evidence/o5-inputs-20261021/manifest.json)，状态为 `INPUTS_AND_HOST_REVIEW_ONLY`。此检查点有47份文件，明确记录当时EMU执行数0、G3/T17未完成；后续全核运行另行保存。

Git封存检查发现原 `team/** text eol=lf` 规则会改写ZIP中的字节，已为本轮两个证据目录添加 `-text` 并恢复正确归档。`a9682f4a3` 的47项Git blob及工作区字节均与封存SHA一致；最初错误提交保留在历史中，不能作为有效归档来源。

## 输入与来源

独立 Linux 检出位于 `/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021/repo`。从本地 Git 已提交对象检出 LF 源码，递归恢复并验证 126 个依赖；没有复制 Windows CRLF 编译输入，也未复用旧 EMU。

原冻结输入的绝对路径依赖不完整，因此新增显式 `o2-g3-current-inputs-v1`。省略 `--input-contract` 仍执行旧合同，原归档不改。新合同路径为本机工作根 `inputs/input-contract-v1.json`：

- 正常 NEMU、负控包装器、hello/flash、8 个矩阵分片重新构建，源码基点 `7d0630202`；两项补充诊断程序使用 `c2c3588e4`。具体源码、命令、工具、输入及产物按各自回执绑定。
- control 与 dense 使用原归档逐字节恢复的镜像和来源材料，不表述为重新编译的软件。
- 矩阵仍为 117 个唯一用例、124 次执行；完整寄存器、异常、控制覆盖和 12 个 dense 窗口要求未改变。
- 严格预检核验 3,430 项输入，全部通过；6 类实际合同破坏探针被拒绝。两项补充程序的完整来源验证通过。
- 当前 11 项检查器按原始 Git blob 绑定，缺少或替换新合同模块均被拒绝。core 与 supplements 必须使用同一输入合同 SHA。

输入合同完整性针对本次选定构建/运行所声明并严格验证的输入集合；不是整台主机或任意机器的软件环境快照。绝对路径、系统头文件、工具字节仍需匹配；异机迁移须重新准备一套新合同，不能修改历史回执。

## 审查与修复

规范审查发现并修复：新矩阵不能只信任自报的源码清单，现要求完整 Git 源码及准确的数据/ELF/bin/AM 清单；NEMU 传递源码、配置和系统头文件纳入运行前后检查；hello 的三条命令必须与实际选定输入输出相符；supplements 绑定相同 AM 来源及完整 Git 源码，生成数据继续匹配固定规格。

需求审查确认：新合同只改变输入来源选择，不降低原回归、负控、恢复和覆盖标准；O5 就绪状态不包含硬件执行、独立成员复现或人工 ACK。新增合同及当前/历史 Git 回放入口分别保留身份。

最终源码复审范围为 `7d0630202..88695f04a`：规范轴未发现尚未修复的可行动问题；需求轴未发现新增代码阻断，并要求将“全核执行中”的措辞改为准确的“构建中，EMU回归未开始”，已修正。这两项源码结论不替代随后实际G3结果；135条展开警告及第三方C++编译警告均保留在原日志，不宣称整个上游工程零警告。

原生直接构建合同升为 schema 2，增加实际 Verilator 编译器载荷、Mill 载荷/启动解释器、GNU time 及 `.mill-version` 的身份。真实启动验证先后暴露两项主机适配错误：Mill 无 shebang 导致直接 exec 失败，以及 Bash 保留字 time 错误解析 GNU 参数；两次失败完整保留，修复后实际 Make → GNU time → Mill 分发验证通过。

内存受限的 `split-v1` 单独使用 schema 3，另绑定 Python、Make、执行器及固定阶段参数。需求审查核对了原 Makefile 的 FIR 选项、内存生成和断言后处理；编译前后严格比较已准备 RTL，防止 Make 重新生成后混用来源。审查发现的两个通用门禁缺口已另行修复：构建工具 SHA 必须匹配声明提交的 Git blob，内存生成器的 PATH Python 必须匹配合同。本次 f44 构建没有这些后加门禁，但独立审计直接核对实际运行进程环境、四项脚本的 Git/回执/当前字节及 Python 路径，均满足相同条件，回执明确保留此区别。

## 当前执行状态

第三次构建候选为 `6a75e7f77bd94098e4777f521e643d155c657e72`，第四次为 `f44d8b1ba73d8f210f55e0818cec05a2681c3481`，第五次为 `3098ceb4e`。硬件源码保持一致，均绑定434项硬件输入、21,236项依赖文件及各自实际原生工具合同。

- `build-01`：工具探测失败，未进入 RTL 编译。
- `build-02`：Make 启动失败，未进入 RTL 编译；原输出已移至其独立失败目录保存。
- `build-03`：实际进入展开和 firtool，内核记录 OOM 并终止 JVM；监督进程一并中断，没有生成原生最终退出回执，原 `BUILDING` 文件仅表示最后已写状态。保留内核日志、资源采样和原始输出，另行标记中断，不补造退出码。
- `build-04`：`split-v1` 的Scala、FIR展开、firtool、内存生成及后处理通过；C++编译生成396个目标文件后，GCC编译 `VSimTop___024root__DepSet_hd5918264__151.cpp` 的RSS升至约10.6GiB，原3GiB交换空间耗尽，WSL失去响应。确认只有Ubuntu-HDL运行后人工终止该发行版并重启WSL，原产物全部保留。这次没有内核OOM结论，也没有原生最终退出回执；外层WSL退出1，原 `BUILDING` 状态作为最后写入记录保留。
- `build-05`：`split-clang-v1` 绑定Clang 19.1.1的CXX/CC，但后续实际模板审查发现Verilator另用 `LINK=g++`、`AR=ar`。Scala至RTL后处理全部通过，在Verilator生成阶段受控发送SIGTERM；父构建正常记录FAILED及退出1，EMU执行0次。保留原合同、日志和产物，不将此尝试改称完整Clang构建。此前std::cout小探针未覆盖真实Verilator模板，此审查缺口已明确记录。

- `build-06`：候选 `0484f1feb25d0e8fa9fa281a643f1943eabc7bb5` 使用独立 `split-clang-v2`，从新 `build/` 启动，未复用第五次RTL/目标文件。显式绑定LINK、AR、底层ld、Verilator模板/运行源码、解释器及Clang/LLVM动态实现闭包，并在各阶段前后核验。六阶段及前后来源检查均通过，正式状态 `O2_FULLCORE_BUILD_PASS`，EMU SHA-256为 `b2b8f01324613f44f5c2ab9b1f4948f1bbe7db15457383d450608014d5c1ece9`。生成397个目标文件，包括先前GCC受阻的大编译单元；回归已完成，覆盖缺口见下方最终封存状态。

真实Verilator小模型 `native-clang-link-probe-08` 已完成O3/O0预编译头、归档、指定ld链接和运行，输出42；驱动 `-###` 也确认实际ld路径。旧v1默认PCH可用，不能称为PCH不兼容；中间v2探针只设 `.gch` 导致失败，改为配套 `-include-pch` 后通过，失败探针06/07继续保留。新增源码的规范轴与需求轴复审均未发现剩余阻断，小模型不替代全核验收。

第五次构建前在项目Linux工作目录启用了临时8GiB交换文件，未加入fstab，已在全部EMU退出后停用并移除，cleanup回执随封存保存。它是本次WSL资源缓冲，不是新的软件依赖或性能参数。Clang构建不能直接与旧GCC构建作G4公平配对。

主机验证已完成 G3 103 项及同套 `-OO` 复跑；新增实际 Git 构建脚本身份测试和 G3 schema 3 入口测试分别通过。Clang扩展后的原生合同及分阶段执行24项、O5 9项、O1 performance 30项、O2 performance 43项、O4 44项通过。Clang实际捕获、复核及std::cout编译链接运行通过；需求复审未发现新阻断，要求新候选重新预检并保留独立构建身份。另保存补充 workload 主机测试结果。重复运行不累计为独立测试数。主机检查和历史档案均不替代本次 EMU 执行。

第四次候选的输入归档 `prepared-inputs-v2.zip` 包含3453个绝对路径、2670个去重内容块，大小36,028,953字节，SHA-256为 `2c4b0fb8f00d7c034552615b007d60ec108af48cb7084085d8a2b38d6211ce4d`。v1因使用6a预检与f44检查器混配而被拒绝，失败文件保留；v2使用f44重新预检。

第五次候选重新预检3430项输入及11项Git检查器绑定均通过，其 `prepared-inputs-v3.zip` 同为3453路径/2670内容块，大小36,029,326字节，SHA-256为 `a62e340ff853d1a6188f346ba0c3ab8b747bd396b362f08a0c91041dc2933f3f`，包含3098候选的检查器身份。两份合格归档均通过CRC和每块SHA核验；它们保存输入，不宣称任意目录解包即可执行。

第六次候选重新预检3430项输入和11项Git检查器通过；`prepared-inputs-v4.zip` 包含3453路径/2670内容块，36,030,596字节，SHA-256为 `cf899b8b72d5b8c719e9aefad7ada88198416ce1a0b00edd13708c0b343ee28f`。最终v2原生测试28项、G3主机测试105项均在Linux `-OO` 下通过；其中live G3入口明确拒绝缺少ld、Verilator模板或Clang动态实现的回执。

## 运行与复算

实际 bit100 负控暴露了旧门禁的误拒绝：注入 VDOT 的 PC 为 `0x80001c4c`，DiffTest 比较报错打印的是同一提交组首条 PC `0x80001c40`。独立核对 DiffTest 源码和完整提交环，最新组有6条提交，目标 VDOT 唯一位于其中，vd10、高半部 bit100 XOR、实际退出1和 ABORT 均符合预期。旧检查器错误要求两个 PC 相等，原 `negative-vdot/result.json` 的 FAILED 和整个原 campaign 判决保持原样。

修复提交 `2b6c5d6c1d29cc4a933f73853ce2ccbfc449f2fa` 改为严格绑定完整最新提交组、准确条数及环形索引、组首 DUT/REF PC、唯一指令 PC/word/写使能/目标寄存器。缺项、重复、超界、不一致以及混入其他组均拒绝；同 PC 日志若带组证据也不能绕过校验。实际原日志由红转绿，10类破坏负控全部拒绝，3份历史冻结负控兼容通过。Linux `-OO` 下 O1 audit 30、O2 G3 108、O1 fullcore 44，共182项相关测试通过；其中21项门禁测试已包含在30项中，不重复累计。规范与需求复审均已核对 DiffTest 批量提交语义。

新版离线入口显式选择 `--runtime-gate-commit` 完整40位提交，并要求执行中的 `recheck.py` 与该提交逐字节相符，同时从同一 Git 提交加载修复门禁。默认仍使用原始门禁；此选项不修改原运行的检查器身份或结果。实际部署只在全部运行结束后替换离线审计器，第一次修正审计时Linux HEAD、原门禁及11项运行检查器保持 `0484f1feb`，避免破坏原输入合同和 supplements 回放。修正审计另存 `recheck-02` 和独立启动回执，原 FAILED 不覆盖。

构建通过后，使用相同 `hardware-inputs.json`、EMU 和输入合同顺序执行 `run_suite.py`、`run_supplements.py`，最多两个单线程 EMU。保存分离 stdout/stderr、真实退出码和失败尝试。随后 `recheck.py` 从原始日志、Git blob、硬件 pins 及输入来源复算完整 G3。

只有新构建、完整 core、两个 supplements、真实 bit100 拒绝与同镜像恢复、覆盖及离线复算全部通过，才能关闭当前源码 G3 复验。性能 A/B、PPA、T17 独立成员执行及人工 ACK 均另行判定。

## 最终基线封存状态

2026-10-21 本机 O2 基线：Linux LF、126个依赖、3430项输入及新全核构建通过。实际16次启动，选定14项作业；117个唯一矩阵用例/124次执行、5378条正常VDOT提交、bit100拒绝及恢复通过。严格重审为 INCOMPLETE，仅缺 PARTIAL_KILL；固定seed=1补测仍为0。原FAILED和两次INCOMPLETE均保留。该结果属于0484构建，不能用于随后H1整合源码的验收。O1/O2默认关闭，未推送，main不改；T17/人工ACK/新性能与PPA未完成。

证据：[完整清单](../evidence/o5-current-fullcore-20261021/manifest.json)、[选定审计](../evidence/o5-current-fullcore-20261021/native/runs/recheck-03/result.json)、[派生汇总](../evidence/o5-current-fullcore-20261021/native/current-g3-summary.json)。这是一份保留缺口的检查点，不是G3通过凭据。

`core-01` 的原 FAILED 来自旧负控PC门禁；`recheck-02` 使用已提交修复2b6严格重审，确认core与supplements通过，但PARTIAL_KILL缺失。随后仅按预先确定的seed=1执行两项supplements-02，未修改EMU、镜像、输入合同或覆盖阈值；仍未触发PARTIAL_KILL。`recheck-03` 重审core-01与supplements-02，结果仍INCOMPLETE。原core12项、supplements-01两项及supplements-02两项共16次启动；最终选定14项中包含1次预期bit100拒绝，其余13项正常通过，正常提交5378条。两个补测集合不能重复累计成更多唯一功能用例。

补测工具提交为 `afe589bffc1fe98785784100187d45e953b421e9`，已通过 `6ae8a9695` 合并至James_Hotten。原生HEAD切换至afe，但11项共享core驱动保持0484字节；独立审计器仍为2b6精确Git blob。explicit-seed-v1要求命令、runtime、preflight和最终Seed输出一致，旧隐式seed=0证据不重标。主机G3完整114项通过，随后仅终端周期格式兼容调整，6项seed测试重新通过；这些是主机合同检查，不补足硬件覆盖。

8GiB临时交换文件已清理，未改fstab。原构建01–05的失败/中断及build06的成功保持独立来源。v4输入包保留原0484检查器身份。归档包含原始日志、全部判决、启动器及输入包，复制前后核对审计绑定的SHA；不包含完整EMU、所有工具/依赖或可直接跨机器运行的环境。

后续H1整合另行记录。当前基线缺失PARTIAL_KILL需通过定向场景解决；不能借用上游不同源码/工具环境的H1覆盖声称此处完成，也不能依靠无界换seed筛选成功结果。
