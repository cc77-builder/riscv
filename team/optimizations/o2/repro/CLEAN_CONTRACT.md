# T17 干净源码构建与当前入口复现合同 v1

本合同只适用于 `t17-clean-build-v1` 及其下列配套合同。历史 B0、H1、R4、MERGE-REG 的源码、锁、原始结果和检查器保持原样；它们的 PASS 不自动授予本次新 EMU。操作步骤见 [CLEAN_REPRODUCE.md](CLEAN_REPRODUCE.md)，实际结果见 [CLEAN_RESULT.md](CLEAN_RESULT.md)。

## 1. 目标、执行者与范围

从固定 Git 对象恢复独立源码及递归依赖，实际重新构建 EMU、既有团队 NEMU 扩展及 AM 库，再执行整核、普通 C 调用和公平性能矩阵，最后从封存原文复算。执行者以实际记录为准；Agent 复现不能写成队员人工验收。

本版为**同一主机上的干净源码目录复现**：允许读取本机 Git 对象缓存、已安装工具和下载缓存，但禁止复制旧 `build/`、`out/`、旧 EMU 或缓存工作树改动。新 clone 使用独立对象库、index 和工作树，禁止 object alternates；各目标目录不得已有构建产物。它不证明全新操作系统安装、工具链从零安装或所有历史输入可任意搬迁。

官方权威程序、判定标准和冻结检查器不能修改。正常参考模型仅在新目录复现仓库已有、固定哈希的团队 NEMU 扩展配方；故障注入库是独立测试夹具，不能代替正常参考模型。原件及历史运行目录保持原身份。

## 2. 固定源码与构建身份

| 项目 | 要求 |
| --- | --- |
| 当前源码提交 | `34bae6d4acceac939f958199dae53c14bc1f6183` |
| 硬件比较基线 | `6d2abe403b07c297b8830a7d4f06e370b0a8e070` 的固定输入清单；只比较字节与依赖，不继承其运行结论 |
| 比较清单 SHA-256 | `2c580afa6095cda5e9d1680b7e91939b6f182b21c47357c77402c2d6b09d0a2c` |
| 输入集合 | 429 个硬件文件、21,236 个递归依赖文件、126 个硬件依赖仓库，提交、集合及字节均相符 |
| 生成物 | 构建前 `build/`、`out/` 不存在；实际 `make emu` 退出 0；重新核验输入并记录 1,672 项生成物与新 EMU SHA |
| 硬件配置 | MinimalConfig、NUM_CORES=1、EMU_THREADS=1、observe；fused=1、handoff=0、elastic=1，O2/T13 trace=1，O1/T12 trace=0 |
| 资源 | 总计最多四核；构建 `-j4`、JVM 8G/16m、ActiveProcessorCount=4；实际 affinity 和命令另存 |
| 工具 | 实际版本命令和日志封存；本版不逐个锁定所有工具可执行文件哈希，也不证明工具安装过程 |
| 新身份 | 19 项构建 metadata、构建配方、源码与依赖、实际新 EMU、AUX、flash、正常 NEMU 来源必须相互一致 |

构建实际资源可在 1～4 核内选择，新的命令和 pins 必须一致；性能阶段的单线程 EMU 配置不随宿主构建并行度变化。任何源码、适配器、构建输入或运行配置变化，都需要另一个输出身份，不能覆盖在途输入。

### 本版团队适配器

| 文件 | SHA-256 |
| --- | --- |
| `clean_prepare.py` | `8e59850c3edcf1bb26d6914759632bab626e297fc95f071f23b58a313043e561` |
| `clean_build.py` | `9038f134e5f811b1e99a13893dc8fce081a96cf9be0ffe5a9f546a70818a2c7e` |
| `clean_support.py` | `13d03b2a54c26d192e1757975b7583ba5d41a764e8e732caf5c2bc48d7351566` |
| `clean_profile.py` | `1c4c467f43ede68fd30b1063868d8f02d71fbe8a5442f2da180210468db9a642` |
| `clean_entry.py` | `6aabb8bbd764d1b7b18b643eaf592efc0a0a1d49e6545842dc7a6b337d39a883` |
| `clean_fullcore.py` | `593298f4119d5a8ce8dd925ec5836c70e0d8bf4cbcf7cf0b221570ffc669f1a2` |

前五份源码写入 T17 identity；整核控制器另由 campaign 固定。运行启动后这些输入不可编辑。独立归档审计器的版本与测试记录另外封存，不反写运行证据。新工具只给私有团队模块绑定经过验证的新构建身份；原生成器、数学模型、ELF、CSR、退休、异常及 O2 规则保持固定字节。

新增 `clean_portable_evidence.py`（SHA `df1be9196293bb637d356c9bfe69a991130297e4f9f77e9ce95e02aa06a9b628`）使用独立传输合同 `t17-portable-entry-v2`。它在冻结打包器的原始输出之外建立新归档，不修改上述运行身份、原九份脚本、支持证明或运行记录。传输工具版本由最终归档另行绑定。

## 3. 干净依赖与支持库来源

`clean_prepare.py` 恢复 133 个仓库，包括主源码、126 个硬件子库、xs-env 及 NEMU/nexus-am/DRAMsim3 相关仓库。xs-env 取缓存的实际 HEAD 并记录，不把一个未核验的固定版本写入结果。

`clean_support.py` 另恢复 NEMU base/reference 及各五个依赖，共 12 个新仓库。在独立目标中执行既有 `prepare-nemu-vdot.sh`（SHA `bef805d62c5b64aedae63c295c1bb0a8d065147c48187a2ca7406afb92348e8a`），NEMU `-j2` 与 AM/klib `-j2` 可并行，总预算不超过四核。AM 源码构建前后审计相等。

`support-proof.json` 必须连接：145 个仓库的 restore 命令、提交/origin/无 alternates；准备与支持构建原始日志；三项真实命令、退出码与时间；正常 NEMU 的源码/配置/补丁 provenance；AM 库实物 hash；当前 identity 与审计器源码。归档还要将 patch manifest 和库身份连接到实际运行输入，不能只相信布尔声明。

## 4. 新整核运行：t17-fresh-fullcore-v1

必须新执行 14 个 EMU 进程，禁止以历史执行判定代替：

- 12 个 core：hello/vadd、8 个功能/异常分片、control、dense、负向注入。
- 2 个 supplement：O2 diagnostic 与 control diagnostic，保持两槽观察 schema。
- 功能矩阵保留 117 个唯一用例、124 次分片执行；D00 的重复按原合同计算。
- 正常轨迹必须完整 DiffTest 通过；负向轨迹必须精确捕获预期高位故障；随后同镜像、新进程、正常参考模型恢复成功。
- control 原有七项义务全部通过，完整结果位宽、异常、取消、退休条件和 dense 原门禁不降低。
- 合并 core 与 supplement 后，MULTI_INFLIGHT、TRIPLE_OVERLAP、FULL_STALL、KILL_P、KILL_R、PARTIAL_KILL 六项 O2 覆盖均满足。

冻结 workload 镜像及构建回执继续作为输入，新 EMU/正常 NEMU 和新路径绑定的故障夹具承担实际执行。冻结镜像的旧 AM 构建来源与本轮新 AM 库是不同范围；新 AM 通过后述 R4 ELF 构建和实际运行使用。

每个进程独立 cwd、AUX、stdout、stderr、run.log、runtime.json 与最终记录。原始 spawn 回执和最终记录逐项核对命令、输入、cwd、环境、PID、退出码、timeout 和实际执行声明；`run.log` 必须精确等于 stderr+stdout。控制器与输出 identity、输入集合、时间及完整 14 项索引闭合。

正确性可用最多四个 worker；本轮为与普通 C 运行共用预算采用 3+1。控制器没有自动断点续跑协议；失败或中断时先核实真实进程，线程池可能等待已排队任务，不能从命令返回或第一项失败推断全部进程结束，更不能盲目重发。

## 5. 当前 GEMV 入口：t17-current-entry-reproduction-v1

性能矩阵沿用冻结 R4 生成器、同一普通 RV64 C ABI 调用路径和公平窗口：

- 4×8、4×13、8×32、16×64；三个数据集；S0/S1；basic/reuse、vdot/RVV；四个完整调用窗（endtoend，shard 1/3/5/7）。
- 重新使用本轮 AM 库构建 24 份 ELF，数学、静态/ELF、固定布局和调用退休门禁全部通过。
- 33 次实际 EMU 进程：24 次正式、8 次全窗口 replay、1 次预期负控；384 个正式窗口、192 个全窗口 replay 比较。
- 正常参考恢复与故障拒错均成立；正常进程的提交数与原合同一致；不把循环附近的局部数字当完整调用周期。
- 性能进程严格串行；运行期间无其他重型构建、EMU 或原文压缩审计。实际资源状态与运行起止记录保留。
- 每个形状保留最快合格的同入口 RVV 对照。按 endtoend 调用窗周期作采用判断，保留所有候选路径和数据集；未赢 RVV 的 vdot 不强行采用。本批不另测旧 core 窗，也不把调用窗扩称为完整应用周期。

普通 C 使用另行重建一个 ELF，16 个公开函数、48 个不同 case；1 次精确负控和2次正常执行，共96次正常用例执行。调用者、ABI、全宽结果、CSR、退休和结果检查沿用冻结 R4 C 门禁。它证明普通 C 使用正确，不单独产生性能收益。

## 6. 原文复算与交付

| 层级 | 必需证据与边界 |
| --- | --- |
| 物理审计 | 活跃源码、构建产物、参考模型和原始日志全部重新核验；新 EMU 执行数为0 |
| 封存矩阵/C | 用 `clean_portable_evidence.py` 调用原 `clean_evidence.py` 与冻结 R4 门禁；保留原打包输出，另建最终包；C 归档绑定最终矩阵 identity/manifest |
| 封存整核 | 用 `clean_fullcore_evidence.py` 精确封存 campaign、物理审计、直接输入、支持证明与审计源码；从原文重算14项，不能信任缓存 PASS |
| 不重复存放 | executed-builder.py 兼有 metadata 与 driver 两个角色，归档只存一次，但仍逐项验证全部19个 runtime metadata 身份 |
| 外部范围 | EMU 二进制、完整物理源码/依赖树和工具安装不是 Git 小型证据包的自包含重建环境；清单保留身份。封存正常参考库及直接验证输入后，离线审计不得悄悄读取宿主缺失文件替代 |
| 传递/发布 | 跨 Windows/Linux 复制验证原始字节；Windows 原生 Git 索引逐 blob 核验文件集合/大小/hash。正文使用仓库链接，个人绝对路径只留运行记录 |

整核包根目录含两个清单文件，载荷另存于 `files/`；矩阵/C 沿用原归档格式。不得用另一种包的 index 清单规则跳过差异。失败尝试、退役的 identity 或审计器版本保持可定位，并明确未用于最终运行。

传输 v2 只改变精确输入的封存位置：矩阵中的 `hardware_source/build/emu` 保留原运行 SHA、改为 external；C 中同一 EMU 也为 external，两项全局 AUX 引用矩阵的 `hardware/` 载荷。每个运行私有 cwd 的 AUX、镜像、日志、回执及其他载荷保持原始存储字节。重封时逐项检查，最终包记录原 manifest、映射和工具 SHA；原 raw auditor 继续完整复算，不降低数学、ELF、CSR、退休、异常或 replay 门禁。独立审计不重新读取原源包证明重封过程，该过程由实际重封回执及保留的源清单说明。

最终整核、矩阵、C 包还必须在无 `build/`、`out/` 的独立源码检出中复算。记录脚本、输出 SHA、实际 cwd 和访问限制：本版用 Python audit hook 拒绝原物理目录的文件/目录访问及显式指向这些目录的子进程参数/cwd。它是依赖检查，不是 OS 沙箱；已安装工具及子进程内部文件访问不受完整系统级监视。EMU 的封存哈希仍与 pins、identity、原始运行回执相连，离线复算不冒充重新验证物理 EMU。

## 7. 决策边界

只有构建、来源、整核、普通 C、性能、最终封存及独立检出原文复算全部完成，才可在本合同范围写 T17 PASS。`whole_suite_acceptance=false` 等旧软件层字段保持原义，由本合同分别列明各验证层，不能改字段把独立结果混成历史合同 PASS。

本轮没有 RTL 算法改动；429/21,236 输入等同用于说明历史 FU/ASIC 成本证据的适用边界，不构成新的整核频率、功耗、面积或应用端到端提升。性能如与旧合格样本不同，必须按本轮新身份解释和重新决定。

T17 通过后才进入路线 R5/G5 的稳定版本/默认入口工作。它不自动完成赛事材料、正式提交、官方未答复语义项或队员人工验收。
