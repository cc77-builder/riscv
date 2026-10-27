# 真实 K768 W2、完整 consumer 与使用边界

操作 `20261027-LiZufan001-w2-1200`，工作包 `R2-S3/runq-forward-w2`；开发基点 `cffb4cf91acb8c6a94c5617e2cc8444697330037`。本叶新增固定 `M288/K768/GS32` 的强 RVV/自定义 vdot 两入口和可选完整 consumer。发布状态由 Git 历史及 [Issue #2](https://github.com/cc77-builder/riscv/issues/2) 的最终 END/DONE 定位。

## 1. 结果与范围

W2 的标量回退原本仍在完整 forward 中使用。此次沿用已经核对的 Q288 内核结构，保留 24 个量化 group 的浮点左折叠顺序，补齐六层真实 K768 W2，并让新组合使用原参考机执行完整 forward。现有 R5 稳定默认、旧 consumer、原官方 AM/NEMU/DiffTest、生产 RTL 和旧冻结实验保持。

**参考、接口与 W2 目标正确性通过，性能选择为 HOLD。** 最终 `target-02` 的真实负控、正常、恢复和独立重放四个进程全部闭合；三个正常进程的完整验证结果逐项相等。FR 四个正式样本跨度为 **1.643809%**，超过事前 1% 门槛，因此 `comparison_qualified=false`。较低的 TA 原始周期不转化为合格性能收益或优选；不剔除较慢 FR 样本，不改变门槛，不再为本批追加 EMU。

| 验证对象 | 本次实际结果 | 取得的资格 |
|---|---|---|
| 真实 p2/layer5 W2 捕获与派生 | 原自然 forward 捕获前后，三个位置全部 3,691,424B 状态等于原 host gold；实际 GNU FR/TA 全函数各只有三个几何指令变化 | 固定真实输入、严格数值顺序、完整实际函数身份 |
| W2 边界原参考 | `reference-04` 的负控、正常、独立重放通过 | 同 ELF 的完整 288 输出、8×128bit slots、CSR/flags 与输入不可变性 |
| 五方法完整 consumer | `consumer-reference-02` 十个实际案例通过；scalar/FR/TA/FR-cache/TA-cache 各自 p0..2 完整状态匹配原 gold | 新组合在固定模型三个位置的完整参考正确性；五份模型全部回读 |
| 双状态 API | `api-reference-01` 通过；13 次 forward 拒绝、5 次失败 init、6 次有效 init、5 次有效 forward、六对完整状态快照 | 新 pack 参数失败关闭、恢复、独立状态顺序交错和原接口边界 |
| p0..255 完整支持域 | `sequence-reference-01` 的真实负控与正常恢复通过；scalar/FR-cache/TA-cache 共 768 次有效 forward、512 次全状态比较、3 次 p256 拒绝 | 固定 token 序列下三个方法的完整支持范围参考等价；没有第二次全序列独立重放 |
| 真实 W2 香山 DiffTest/计量 | `target-02` 四次实际运行通过；三个正常进程完整重放相等，112 条 CSR 链与 718,848 笔 custom 事务审计通过；性能 HOLD | 只覆盖预量化、预打包、同方法完整 W2 selfwarm 的完整 C 调用边界 |
| 完整香山 forward / token 性能 | 未进行本组合的完整目标执行 | 不把原参考、单阶段、调用数或 MAC 覆盖当作完整应用性能 |
| 模型质量、ASIC PPA | 未测；使用固定确定性未训练 fixture | 不产生训练质量、任意 checkpoint、频率、功耗或新 ASIC 结论 |

标量到向量、强 RVV 到 vdot 的原始周期对比分别保留；本批未通过公平性门槛，不授予性能收益资格。原阶段和 Q288 的历史百分比不迁移、不串乘；原参考的 API 调用数仅用于工程运行预算。

## 2. 源码与精确机器码

权重打包为 `P[t,g,r,k]=W[(8*t+r)*768+32*g+k]`，尺寸 `36×24×8×32=221184B`；权重 scale 保留原 `288×24` 行布局。输入 `hq[768]` 和 `hs[24]` 来自自然 forward 的 `p2/layer5`，输出为全部 `xb[288]`。每行按 group 0..23 顺序执行 signed int32 dot32 → FP32 → 乘权重 scale → 乘输入 scale → 加旧累积；RNE、禁 FMA contraction，不重排、不分片浮点求和。

[generate.py](generate.py) 从固定 Q288 源码完整可逆派生，实际 GNU ELF 再逐机器字比较：

| 变化 | Q288 父函数 | K768 W2 |
|---|---:|---:|
| scale 行跨度 `t3` | 36B | 96B |
| group 数 `t1` | 9 | 24 |
| tile 后 scale 指针调整 | 252B | 672B |

tile 数仍为 36，所有其他机器字相同。

| 实际函数/对象 | 大小 | SHA256 |
|---|---:|---|
| `q768_fr` | 592B | `a163ade8b72cfdf7fb5f34b0eeed5f3e57206f45200d626c6c3a938ce5c556a9` |
| `q768_ta` | 764B | `a276d3e11ccb5ce4dc0d65c34c1184f593785f5e37d6f4dca4edf1da76f6ca64` |
| 原 `q288_fused_rvv4` | 592B | `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab` |
| 原 `q288_tail_vdot` | 764B | `b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3` |
| 完整纯 `consumer-w2.o` | 以归档实际对象为准 | `bacb109bb94662a9390d074d1ec2791d256b34f51f855909ab5a91f4004eebb9` |
| 本次 W2 目标 ELF | 以 `build/result.json` 为准 | `de67e9e57a58650f10e7dce45faf7161802586ac43a3ef1a17a1cb692a10ec2f` |

新 consumer 仅为已知六层 W2 地址选择对应 `q768_fr/q768_ta`，其他 K288、尾部、缓存政策和未知 tensor 的 scalar 回退保持。全部源码改动可逆回父 consumer；四个内核在完整 consumer、API 和序列 ELF 中逐字等于各自合格父函数。纯对象无 oracle、快照、报告或计时依赖，测试包装与核心分开链接。

模型新增借用的 `6×221184=1327104B` W2 pack，不在每次 forward 内重新打包。原、新 consumer 都包含上游全局符号及 `GS`，是二选一的完整对象。新入口、必需汇编/运行库、初始化及回退方式见 [README](README.md) 和 [consumer_w2.h](consumer_w2.h)。

运行沿用固定 RV64/lp64d、VLEN128、RNE 与 T17 身份。正常 NEMU SHA256 为 `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`，EMU 为 `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`，实际硬件来源提交为 `34bae6d4acceac939f958199dae53c14bc1f6183`，AM HEAD 为 `086a238062fdfb3281b745a537b361983d0154b5`。完整输入及物理身份由当时回执固定；本次没有新 RTL 或 ASIC 构建。

## 3. 实际参考与负控

最终完整 consumer 使用 `consumer-build-02`，镜像 95,570,144B；目标、API、完整范围序列分别有独立镜像和合同，不能把各镜像的运行成绩相互替代。

`consumer-reference-02` 的十个案例为应用负控、scalar、FR、TA、FR-cache、TA-cache、FR pack 故障、TA pack 故障、TA-cache 恢复、TA-cache 独立重放。正常方法均执行 token 1/7/19、p0..2，每个位置比较全部状态，包括 scratch、KV 和 32,000 logits，并检查 fcsr/RNE、TLS/errno 和全部模型。恢复及重放的完整验证结果与首次 TA-cache 相等。

应用负控在 p0 真正完成计算后翻转最后 logit 的 bit0，完整状态比较器在 byte152476 拒绝，原参考 BAD TRAP94/退出2；W2 边界负控对应输出 byte1148。两条 pack 负控仅改变同 ELF 中新 W2 pack 的实际数据，原权重、gold、参考程序不变；实际回读新 pack 全零、其他模型不变，完整状态比较器拒绝。这证明新 pack 的真实数据依赖；它单独不构成六层逐层动态覆盖，六层映射另由静态地址与正常完整状态支撑。

API 镜像 121,401,336B，实际链接同一个纯对象。新增 pack 的 NULL、长度少 1 和未对齐输入分别失败并恢复；八项 dump 覆盖两个带保护区的 live state、完整快照和五份 immutable 模型。测试镜像的大快照不属于消费者必须保留的运行存储。

`sequence-build-02` 将相同核心对象链接到独立 91,876,448B 镜像；scalar、FR-cache、TA-cache 使用三个独立 state，token 前三项为 1/7/19，之后为 `(position*7919+1)%32000`。p0..255 每个位置的两项完整状态比较通过，全部 256 组 fcsr 都是 `(1,1,1)`、即 RNE/NX-only；五份模型与前三位置 host gold 全量回读未变，三个 state 的前后 guards、TLS/errno 和 p256 拒绝均通过。

三份最终全部 3,691,424B 状态的 SHA256 同为 `8083f616c4cd233f33d7cce9be74744da65118f28862a26455cb8472761027cf`。真实负控先完成 p0 三次 forward，再仅翻转 TA-cache 最后 logit，byte152476/BAD TRAP94/退出2 均符合预期；随后正常新进程得到 GOOD TRAP/退出0。两个直接子进程均已回收，进程组消失，无超时或残留。

原 team adapter 仅允许最多 10G 调用；本补充在独立合同内构建唯一 10G→48G 常量派生，完整源码反向恢复原 SHA，官方 NEMU 与旧 adapter 不变。实际正常调用数为 39,831,298,261、retired 39,831,298,260，保留 40,088 行原进度采样和全部十项 dump；原 adapter 内报告耗时 1691.706991 秒，在事前 2400 秒内。这些是参考执行成本，不是香山周期。campaign 于 `2026-10-27T06:12:46.523024+00:00` 闭合。

该补充覆盖三个方法和一个固定 token 序列；未缓存 FR/TA 的全 256 位置、第二次完整序列独立重放、任意输入模型质量以及目标应用周期仍不在本项资格内。

## 4. 香山边界计量

合同 [CONTRACT.md](CONTRACT.md) 在执行前固定：scalar/FR/TA 同 ELF、同完整输入和输出地址；预量化、预打包在窗口外；每正式样本先执行并检查同方法完整 W2，再重置输出/slots/CSR/flags，计量整个 C apply。顺序为 scalar,FR,TA,TA,FR,TA,FR,FR,TA；两组向量 ABBA/BAAB，正式样本为 scalar 1 个、每种向量方法 4 个。独立进程重放不增加正式样本数。

正常每进程完整执行 18 次 W2，其中 8 次 TA、221,184 笔 custom。负控 2 次 TA、55,296 笔 custom，预期 BAD TRAP。实际原日志审计包括全部 custom 的数量、PC、顺序、full128 算术、协议终态，以及四个 CSR 的实际机器码与 enqueue/sample/retire 链；窗口计量覆盖完整调用，未声称审计窗口内所有普通指令退休。

CPU0..2 分别运行三个独立正常进程；每进程事前上限 12M guest-cycle、10800 秒、每日志 2GiB。CPU3 留给独立参考/封存工作，总预算四核。性能使用 guest 计数器，host wall time 只用于资源记录；实际跨进程重放必须精确一致。

以下保留首次正常进程的全部正式样本；recovery/replay 的完整验证结果与其逐项相等，不能合并成更多独立正式样本。每个样本均为 fcsr=1（RNE/NX-only），全部输出 FNV 为 `f909c47ea8f72842`。

| 样本索引 | 方法 | cycles | instret |
|---:|---|---:|---:|
| 0 | scalar | 1,280,402 | 1,731,532 |
| 1 | FR | 234,352 | 94,564 |
| 2 | TA | 209,738 | 131,718 |
| 3 | TA | 207,477 | 131,718 |
| 4 | FR | 230,623 | 94,564 |
| 5 | TA | 208,800 | 131,718 |
| 6 | FR | 230,562 | 94,564 |
| 7 | FR | 231,108 | 94,564 |
| 8 | TA | 208,425 | 131,718 |

FR 最大/最小值的跨度 `(234352/230562)-1=1.643809%`，因此原选择器输出 **HOLD**。TA 最慢值与 FR 最快值之间的原始数值差为 9.031844%，两个顺序分组也均有利 TA，但公平性门槛未通过；该数值不具有合格收益或最优内核含义。scalar 的单样本仅保留为同一局部计划的原始对照，不用于完整应用外推。

既有 CSR 记录的精确分解见 [window-analysis.json](evidence/target/window-analysis.json)：所有九个窗口的 `cycle0→instret0` 和 `instret1→cycle1` 间隔各为 59 周期，四个 FR 窗口退休数同为 94,564。四个 FR 的两次 instret 采样间隔为 234234、230505、230444、230990 周期，3,790 周期跨度位于这个区间。该分解没有覆盖窗口内全部普通退休指令，不能归因为缓存、分支或某条指令，也没有给原计时减去任何开销。

正常进程总 guest-cycle 为 6,361,736，低于 12M 上限；原 campaign 于 `2026-10-27T06:40:41.055405+00:00` 闭合，四个直接子进程均回收且进程组消失。每个正常进程 221,184 笔 custom 的接受、搬运、响应、入队和提交均闭合，无遗留事务；三个完整验证结果一致。目标运行和后续离线复算分别留存真实回执。

事前门槛为 FR 四样本 `max/min-1≤1%`；TA 最慢值较 FR 最快值至少减少 0.5%，且两种顺序分组均有利 TA，才选 TA。否则依原门槛保留 FR 或 HOLD，不改变规则以迎合结果。

## 5. 发现的故障与保存的证据

所有故障发生在新团队包装或检查代码；没有修改官方判定标准，也没有给失败结果补写 PASS。

| 现场 | 实际问题 | 修正与保留方式 |
|---|---|---|
| `build-01` | 新 C 包装的编译警告被 `-Werror` 拒绝 | 修正表达格式后新建构建，失败输出保留 |
| `reference-01` | 默认入口经过 AM 初始化，参考执行 88 次 API 调用后发生 store access fault：`mcause=7`、`mtval=1080033292`，最终 `pc_outside_ram_and_boot_flash` | 新团队入口复用已核对的原 projection entry/TLS；原 AM 字节不变，原失败归档保留 |
| `reference-02` | 原 scalar 使用的全局 `GS` 初始为 0，正常案例触及 100M 调用上限 | 新 harness 显式设置 GS32；原 `runq.c` 不改，失败保留 |
| `target-01` | 输出比较已打印 byte1148 拒绝，但新 trap 写成 `0x0000006b`，rs1 为 x0，EMU 因而报告 GOOD TRAP/退出0；严格门正确拒绝 | 核对原 AM 后，新包装改用 `0x0005006b`、rs1=a0；旧源码、完整日志和失败状态封存。`target-02` 的实际负控随后得到 BAD TRAP/退出1 |
| `build-05` | GNU 生成两个 UART 错误分支，静态检查错误地假设只有一个 trap 位点 | 在新版本中核对两个真实位点及 code91，不删除检查；旧构建保持 |
| `sequence-build-01` | 反汇编检查把函数内 `.L/.LVL` 局部标签误认作函数结束 | 改用 ELF symbol 的完整地址/长度和原始机器字，实际 140B 比较函数有两个直接 64bit load、无内层 memcpy 调用；新 build02 独立通过 |
| `sequence-recheck-01` | GCC 依赖文件的两个头文件保留 `include/../` 拼写，首次离线检查直接用原字符串查询已规范化 runtime pins，因而拒绝 | 新复核仅用 `posixpath.normpath` 规范路径字符串并保留原 SHA 精确检查；不读取原机、不按任意同 SHA 寻找别名。原包不变，独立 `sequence-recheck-02` 通过，失败回执/当时 checker 源码保留 |

本轮没有重跑任何未变 RTL/FU/旧性能矩阵。早期正常但被新 trap 包装替代的 `consumer-build-01/reference-01` 仍保留本机原始输出，不将其包装成最终候选的新资格。

## 6. 原字节交付与离线复核

证据清单见 [evidence/index.json](evidence/index.json)。使用原 SHA256 对象 ZIP 去重与 20MiB 分片格式；所有普通原文件逐字保存，不用生成配方重建 dump 或镜像。每包实际执行完整恢复、分片重组及恢复后原验证器复算，来源源码闭包按当时 runtime pins 固定。

| 包 | 恢复文件数 / 原始总字节 | ZIP 字节 | ZIP SHA256 |
|---|---:|---:|---|
| core | 860 / 2,847,573,071 | 343,327,229 | `0de4cc80f2a375fbf5e1988ccdef0310d2982a1ca85746cca7006c90d62e153d` |
| failures | 1115 / 203,243,547 | 13,784,357 | `702f574c62ae0a2265be614412f7bab7b207959b9d265ed1f9d58f20226735f9` |
| sequence | 380 / 1,076,938,489 | 171,445,011 | `35889895cfdac964c115c993270b0325a21a0d7b6346135e406183fcd6bb0429` |
| target | 353 / 1,473,126,631 | 34,241,977 | `b6dee5c25018ff8f52bdac5a5c0f94ef4876ba9097bae43b9d6f13c4c1c893e4` |

core 的 3 个边界参考、10 个完整 consumer 和 1 个 API 案例已由恢复出的原始数据及当时验证器重算；failures 复核确认旧 false-GOOD 仍被原严格门拒绝。sequence 的两个实际案例、同核心/四内核和 adapter 完整可逆派生也已从恢复副本复核。序列与目标分别使用独立 kind，不纳入 core 的 14 案例数量。具体命令见 [README 的恢复入口](README.md#原字节恢复与离线复核)。

每包旁附真实 `offline-audit.json` 和当时执行的 checker 原字节。最终 checker 新增序列分支后，旧 core/target 路径的 12 个共同函数与首次执行源码 AST 相同；[兼容记录](evidence/rechecker-compatibility.json) 明确两份 SHA。序列首次复核失败回执和当时版本也单列保存，不覆盖为成功。

离线复算不启动新 NEMU/EMU；仅在内存中映射已封存数据目录，原 JSON 不改。归档保持文件字节，不保存执行权限，也不将外部工具、官方运行环境或物理 RTL 重新认证；实际构建/运行的外部 SHA、命令、身份和清理回执完整保留。新机器重新运行仍须取得并核对原依赖。

原始运行根为 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/forward-w2-20261027-1200`。发布包含最终候选、必要原始/失败证据和捕获的源码；其他 superseded 原始输出的保留范围在索引中单列。

## 7. 工程判断与后续边界

此次采用小范围几何派生，是因为 K768 的 24 组严格左折叠可在现有结构内保留，且完整 consumer 中仍有实际 scalar W2 路径。真实输入、完整状态比较、原参考、目标局部窗口各自回答不同问题，均有独立证据；不依据 MAC 比例或删指令数宣称瓶颈已消失。

当前可通过显式方法选择 scalar、强 FR、TA 和相同 RoPE-cache 政策的回退；完整应用的目标验证和性能仍须另有明确问题、成本预算与强 FR 同口径对照。后续应优先由实际消费者目标需求决定是否值得运行完整 forward，或选择另一项有实测依据的阶段优化；不自动展开多小时模型重放，也不据本轮局部结果切换 R5 默认。

本批固定 fixture 不提供训练质量证据。任意 checkpoint/tokenizer、模型质量、冷加载、多线程、超过 S256 的序列以及新 ASIC PPA 仍需各自适用的验证。
