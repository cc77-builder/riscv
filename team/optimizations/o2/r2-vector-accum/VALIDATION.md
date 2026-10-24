# R2-S1 实施与合并硬件筛选

规范 `run-02` 已实际完成 **57次整核进程、768个正式窗口，状态 PASS**；主批的数学／CSR／全宽结果、精确退休、O2事务、新负控与正常恢复、四次原计划重放及最终输入复核均通过。独立小尺寸补充完成 **4次新进程、96个精确匹配窗口，状态 PASS**；新增正式窗口为0。两项跨检出的完整原始证据重算、原生Windows字节核验及2797个封存文件的实际Git index检查均已通过。三个整块形状的S1 reuse进入后续选择；K13不采用S1 vdot，保留更快RVV。

## 身份与范围

操作 `20261023-LiZufan001-r2s1-2100`，实际 GitHub 身份 `LiZufan001`。本轮开始为 **2026-10-23 21:00:41 +08:00（13:00:41 UTC）**。指定来源是 `working-zufan-full-20261022`，来源分支 `zufan`、完整 HEAD `ff58e519091f273c4bc177f5e82cfbbfaf102cc5`、干净工作树及团队远端均已核实；随后使用独立完整克隆 `working-r2s1-20261023-2100`、独立 index、分支 `work/r2s1-20261023-2100`，同步至远端基点 `bca14d45b07ff07a86a7f54bce2b25870e60e2f3`。原工作树未改。

本包只实现独立 S1 及对等 RVV。原 S0/S2 生成器、黄金值、旧检查器、链接脚本、RTL/NEMU 和他人输出均保持原样。MERGE-REG 旧认领没有明确交接，本轮没有接管；本包结果不等同于 MERGE-REG、历史 B0/H1、完整 T17、面积／时序／功耗或人工独立验收。

### 已执行候选身份

| 项目 | v2 固定布局身份 |
| --- | --- |
| 生成合同 | `o2-r2-vector-accum-s1-v2-fixed-layout` |
| 运行合同 | `r2-s1-merged-software-screen-v2-fixed-layout` |
| candidate.py SHA-256 | `0270736b5c09e160626eb7b32d8e760faa193bf05761fea824a979108c3717b9` |
| gate.py SHA-256 | `ab07b578f5fe2dc7782ef9af64e722e051363d1dfddfcd0f1939efb209346b6d` |
| experiment.py SHA-256 | `75a26c36531b547ecb09c5ff19ecef1b338622779aedb2099f7775efd74cb7dd` |
| 构建时 Git HEAD | `bca14d45b07ff07a86a7f54bce2b25870e60e2f3`，新增候选以以上字节身份和逐镜像源码快照绑定 |
| 合并硬件源码 | `6d2abe403b07c297b8830a7d4f06e370b0a8e070` |
| EMU SHA-256 | `1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63` |
| 正常 NEMU SHA-256 | `efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4` |
| flash SHA-256 | `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994` |
| 私有 AM 提交 | `086a238062fdfb3281b745a537b361983d0154b5` |
| AM / klib 预构建库 SHA-256 | `50443c3abb089f8d8e586d03cabb7770e5ac75738bbc1b44dc8b730ae3e67505` / `eec19a2a8e55ac89331ad63fba29095f2f76e2fa207ef31c3baa41105eb4bc76` |

硬件为已有 O2 两槽＋H1 32 位合并版 minimal/VLEN128，128 MB RAM、seed=1、每次单进程 EMU。完整来源门禁覆盖 429 项硬件源码、21236 项依赖和 1672 项生成物；实体工具链版本、哈希及命令在每份构建收据内。

## 发现并否决的 v1 布局

`build-01` 的 52 份真实 AM 镜像通过了当时的构建、静态 ELF、有限模型数学／CSR末态和四内核入口检查，未代表52份整核运行通过。运行中新增更强的比较检查，发现入口相同不足以保证 caller 和 AM 代码不移动：首个 16×64/endtoend 配对的 `.text` 长度分别为 48304、43824 字节，`main` 分别在 `0x8000bcb0` 与 `0x8000ab30`，相差 **4480 字节**。四个 8 KiB 槽以外有 **9797 字节**不同；两版 `cases.h` 的 SHA-256 则完全相同：`890ff8b1fcf96624420a38280dd18ede706976b32184f5abd94fec2670611530`。

真实 GNU 对象各含八条 `R_RISCV_ALIGN`，对象 `.text` 分别为 90112、81920 字节；末尾剩余对齐数据使冻结链接脚本中 orphan `.text.startup` 和其他 AM 段移动。显式加入 `.option norelax` 后，同一探针两版对象 `.text` 均为 32768 字节、无重定位；真实 AM 两形状探针的 main 均为 `0x8000a000`，非内核加载字节相同。

进一步检查原对象最后一条 ALIGN 的覆盖终点，后方分别仍有 **7344** 和 **2864** 字节未覆盖的零填充（字节为 `00`，不是 NOP）。`40960 + 7344 = 48304`，`40960 + 2864 = 43824`，两者差值精确解释了本例的 4480 字节 caller 位移。实际 GCC 11 的 `-### -mno-relax -c kernels.S` 展开命令没有把 `-mno-relax` 传给 `as`；不能仅凭 GCC 参数认定实际对象已禁用 relaxation。本记录是该工具链和命令的实测，不泛称 GNU 缺陷。证据在 `layout-root-cause.json`。

在确认比较缺陷后，对本操作的 controller 发送了经过 argv 身份核实的 SIGINT。`run-01` 在 **2026-10-23T13:54:15.953255+00:00** 写入 `FAILED / KeyboardInterrupt`；driver exit=-2，外层作业 exit=1 且 cleanup_complete=true。其 17 次实际 EMU 启动中，1 次预期负控、15 次正常运行已完成，最后 1 次正常运行中断。13:54:52Z 确认 controller PID369 与最后 EMU832 均不存在。**v1 周期一律不进入采用比较；整批不记 PASS。** 原输入、输出和源码保留，不覆盖后重启。

v2 的硬门禁同时固定四槽入口、`.text` 总长、所有 SHF_ALLOC 段的类型／地址／大小／flags／对齐，以及四槽外整个 BIN 字节；单件 reference 必须恰好 32768 字节且无 REL/RELA。`old-layout-negative-check.json` 已用这个新检查器直接拒绝 v1 实际 ELF，报 `size-dependent kernel section suffix`。这是对比较条件的修正，没有放宽原正确性检查。

## 对历史 S2 选型证据的影响

同类问题促成对已提交 S2 `merged-screen-v1` 的只读复核。该归档 manifest SHA-256 为 `1d42aa417c2793b997fbf1db89f05c1d2a5dcb49644ff14aa29395621bd129ed`；本次逐项核对使用到的93份载荷的存储及原始字节哈希，未修改旧证据或原检查器。

| 历史配对 | main：S0 / S2 | `.text` 字节：S0 / S2 | 结论 |
| --- | --- | --- | --- |
| 16×64/core，三数据集 | `0x80007ce0` / 同 | 31968 / 同 | 三对整个 BIN 相同 |
| 16×64/endtoend，三数据集 | `0x80007cb0` / 同 | 31920 / 同 | 三对整个 BIN 相同 |
| 4×13/core，三数据集 | `0x80005f14` / `0x8000500c` | 24340 / 20492 | main 位移 -3848 字节，加载段布局不同 |
| 4×13/endtoend，三数据集及 smoke | `0x80005ee4` / `0x80005fdc` | 24292 / 24540 | main 位移 +248 字节，加载段布局不同 |

4×13 配对的四个内核入口仍一致；按 sealed manifest 辨认的两段 RVV（indices 1、3）的地址和完整机器码仍一致。`cases.h` 中另有合法的 vdot 预期计数4→8变化，不能误称其非内核数据完全相同。复核记录完整保留各 ALLOC 段变化、输入哈希与计数字段差异。

**旧功能／CSR／退休／负控 PASS 保留；旧 4×13 reuse endtoend 的 -10.621% 保留为历史观察，暂不作为 R2-SELECT 的采用依据。** 这里只证明了比较条件存在混杂，没有证明收益全部来自布局，也没有给出可扣除的“布局成本”。后续应使用新的固定完整布局合同重新测量 S0/S2，严格限定预期计数元数据的必要差异，并保持代码地址、非内核指令和其他加载字节相同；不能改旧合同来追认原性能结果。证据为 `historical-s2-layout-review.json`，SHA-256 `7145b7bb89eb5ad880d3d94c89f6c9edbe5e44ba95b087566f5ed14f3a31aee7`，协作事件见 [Issue 6367265269](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6367265269)。

### 已完成的最小修复可行性探针

作为这次公平性调查的延伸，在独立 `layout-s2-feasibility-probe-01` 输出中做了四份真实 AM ELF（K13、dataset0、core/endtoend、S0/S2）。原 S2 生成器及源码快照不改；仅对探针生成汇编插入 `.option norelax`，将八处 `.balign 4096` 改为 8192，并使用独立的探针合同，保留改写前汇编与 manifest。实际运行从 **2026-10-23T14:35:39.640239+00:00** 到 **14:35:40.666144+00:00**；没有启动 EMU。

两对真实链接结果均为 `TWO_SCOPE_FIXED_LAYOUT_METADATA_FEASIBILITY_PASS_NOT_RUNTIME`：`.text` 固定40960字节、全部 ALLOC 段布局相同；main 均为 `0x8000a000` 且完整字节相同；RVV 两个完整8KiB槽相同。除 vdot 槽0、2外，整个 BIN 的差异恰好只有 `0x120024`、`0x1208c4` 两处字节 `04→08`，对应固定1104字节 case ABI 中行0、2的 `dots` 字段；这两个 uint32 的其他字节仍为零。没有扩大到整个 cases 段或任意4字节白名单。

四个单件都经过原 `inspect()` 的 ELF/BIN、独立 GNU 汇编、source/机器指令计数和 compiled-case 检查，并完成每个内核9组有限模型输入（固定三组、两组极值、四组随机）的全128位结果／CSR／行边界检查。探针程序、完整来源快照、构建命令与结果均在该输出内。此结果只证明固定布局和严格元数据例外可实现；没有正式 S2 比较运行器、全矩阵性能、负控恢复或 replay 验收，也没有采用 S2 或组合 S1+S2。

后续 S2 新合同还须显式带上当前最快的合格 RVV：新 S0 vdot→S2 vdot 用来隔离尾部变换，S2 vdot→最快合格 RVV 用来判断竞争力。优先把有明确源码身份的较快 RVV 放入新批次实际测量；若复用本模块最终合格结果，须证明加载布局、测量合同和运行身份仍可比，不能只凭相同8KiB槽跨批拼接，也不能自动退回旧 S2 较慢的 RVV 分母。引入较快 RVV 属于新合同，不能冒充冻结的原 S2 生成物。

## 比较方法与解释边界

每个形状保留 basic/reuse、core/endtoend、三组原固定数据；每镜像含 2 software ×2 methods，原计划的 first/warmup/四次 measured 均保留。S0/S1 在 shard/dataset 内交替执行，正式矩阵为 48 次 EMU、768 个测量窗口；4 次 replay 单独验证，不增加正式独立样本数。最快 RVV 从同一形状／scope 的 S0/S1 × basic/reuse 中选取，总周期的分母保留所有 12 个正式窗口。

57次主批的专门新进程 replay 只覆盖 **dataset0 的16×64和4×13 endtoend、S0/S1各一次**。小尺寸另使用独立 `complete_replay.py` 合同和 `replay-small-01` 输出，对dataset0的4×8、8×32 endtoend、S0/S1各做一次新进程重放；须逐一匹配每个原过程的全部24个窗口，共96个匹配窗口、新增正式窗口0。主批57次、48次正式运行和768个正式样本的计划及记录均不改。

报告的周期下降定义为 `(S0 周期总和 - S1 周期总和) / S0 周期总和`；加速比使用相应周期总和之比。同一组合的十二窗口属于三组固定数据及同一确定性模型，不能当作十二个独立应用或主机随机试验。必须同时看绝对周期、最快 RVV 和退化项，不能只选有利窗口。

core 和 endtoend 是原 O3 的两个独立受检窗口。后者包括原 CSR 配置及完整输出存储，仍不是完整 LLM／系统应用时间；二者周期差不能直接解释为可加的“存储成本”。FU trace 的接受间隔和响应延迟仅描述校准区间内事务，不能单独归因整个窗口耗时。代码缩短或退休数下降也不直接等于周期下降。

这些周期绑定本批四个8KiB槽及完整加载布局。进入紧凑链接布局、按形状选择的新镜像或新的真实调用路径后，应重新验证受影响的代码／数据布局与完整窗口，不能直接沿用当前周期作为新入口的性能验收。

### 小尺寸补充重放和实际进程身份

独立补充合同为 `r2-s1-small-endtoend-replay-v1`，执行入口 `complete_replay.py` SHA-256 为 `f68fe2978248776ba6556fe15d941fb32df02a5ceeb20247424fd08374babba7`，同时绑定 `evidence.py` 的 `2d07f72b78314a0775694c12124f793d452bb9a752ae722d6cc1c6182048c5fd`。它从主批原source_root执行，读取原四个规范镜像；运行前后都核验主批、源码、镜像及完整硬件身份，不修改原计划或输出。

`replay-small-01` 实际区间为 **2026-10-23T15:56:57.677592～16:06:42.804126+00:00**，最终 `R2_S1_SMALL_ENDTOEND_REPLAY_PASS`。四份正常运行均通过原数学／CSR／精确退休／O2事务门禁，并与对应原正式进程的全部24个窗口逐一匹配 `(seq, cycles, instructions)`。结果 SHA-256 `5a98cf21c999a543b7bd22b95ee2501a7a23912ddbc4a26a6c33be798e8f8ece`；state SHA-256 `ceb97953915963f401c5dd4f479d348635f083fc44d2ff8028613ee5ea31a6ac`。合并主批与补充的覆盖后，四个形状均有dataset0、endtoend、S0/S1各一次专门新进程重放；不扩大到所有数据集或core均有这种重放。

预检先核对四份真实ELF及两对完整布局，并验证未完成父批、不同source_root均在创建输出前拒绝。`small-replay-precheck-02` 的测试驱动曾错误捕获 `AssertionError`，遇到预期的 `ValueError` 后记录FAILED；修正驱动类型后，03只补两个入口拒错，显式引用02中已完成的ELF／布局结果，不改运行源码或放宽检查。更早的预检启动01被平台取消且没有创建目标文件，取消原因未报告；原回执和随后实际缺失检查保存在 `small-replay-precheck-launch-01.json`，不记为模型或硬件PASS。

外层作业 `716a6ee805ae260048ab831b3dbbd5fe.638cb34848effc9eec18bc1be32be557` 已 exit0、cleanup_complete=true。首次完成检查看到旧driver PID299已被WSL复用于 `/bin/login`，因仅判断PID存在而拒绝；没有停止该新进程。随后以实际argv及外层自然退出收据核对，16:08:31.100356+00:00确认本批driver、controller、四个EMU均已退出、EMU列表为空。两次检查都保留在 `replay-small-01-completion-first-check.json` 和 `replay-small-01-completion.json`。这不改变四次重放已通过的结果，也说明跨轮恢复须核对身份，不能只看PID。

本轮总计实际启动78次EMU：被否决v1的17次、规范v2主批57次、独立补充4次。前17次不进入性能采用；后两项分别按自身合同验收，不能把78次统称PASS。补充沿用同一候选和主批已完成的新负控／正常恢复，不声称又新增了负控。

## 正式矩阵与当前取舍

以下是已完成主批中48次正式运行的768个 measured 窗口；每个均值包含三数据集×四次重复。主批于 **2026-10-23T13:59:13.409730～15:47:56.865774+00:00** 完成57次整核进程：56次正常、1次预期负控，正常项包含4次smoke／恢复、48次正式运行和4次原计划replay。原始最小值、最大值、标准差、退休数及逐窗口数据均由最终 `run-02/results.json` 保存，结果 SHA-256 为 `d1328a7c708055b5ef9e9dacff1d50e3fe507ef79dce39991e0414842a69700e`。

| 形状 | scope | software | vdot S0 | vdot S1 | RVV S0 | RVV S1 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 4×8 | core | basic | 161.25 | 151.75 | 270 | 167.25 |
| 4×8 | core | reuse | 118.25 | 111.5 | 148 | 131.25 |
| 4×8 | endtoend | basic | 205.25 | 195 | 314 | 211 |
| 4×8 | endtoend | reuse | 164.5 | 155 | 190 | 175 |
| 8×32 | core | basic | 609.5 | 599.75 | 445 | 305 |
| 8×32 | core | reuse | 276 | 237.25 | 289.25 | 248.5 |
| 8×32 | endtoend | basic | 647 | 637 | 476.5 | 342 |
| 8×32 | endtoend | reuse | 318 | 278.25 | 332.5 | 289 |
| 16×64 | core | basic | 2145 | 2135.25 | 1382.25 | 906 |
| 16×64 | core | reuse | 771.75 | 634.25 | 826 | 698 |
| 16×64 | endtoend | basic | 2214.5 | 2205 | 1442.75 | 976.75 |
| 16×64 | endtoend | reuse | 846.5 | 701.25 | 893.75 | 768.25 |
| 4×13 | core | basic | 201 | 204 | 274.75 | 172 |
| 4×13 | core | reuse | 165 | 169 | 148.25 | 131.25 |
| 4×13 | endtoend | basic | 246 | 249.25 | 320 | 216.5 |
| 4×13 | endtoend | reuse | 210 | 212.75 | 190.25 | 175 |

### endtoend 选择依据

最快 RVV 在四个形状中均为 S1 reuse，分母取该组合全部12个正式窗口的周期总和。下表的百分比为 vdot 周期下降，负值代表退化；加速比为最快 RVV 总周期除以 S1 reuse vdot 总周期。

| 形状 | reuse vdot S0→S1 | vdot 周期下降 | 最快 RVV 均值 | 最快 RVV / S1 vdot | 数据支持的方向 |
| --- | ---: | ---: | ---: | ---: | --- |
| 4×8 | 164.5→155 | 5.7751% | 175 | 1.129032× | S1 reuse 进入后续选型 |
| 8×32 | 318→278.25 | 12.5000% | 289 | 1.038634× | S1 reuse 进入后续选型 |
| 16×64 | 846.5→701.25 | 17.1589% | 768.25 | 1.095544× | S1 reuse 进入后续选型 |
| 4×13 | 210→212.75 | -1.3095% | 175 | 0.822562× | 不采用 S1 vdot；保留 S0 vdot 回退及更快 RVV |

三组数据集的 reuse/endtoend 每组四次重复均值逐组一致，未通过挑选数据集获得表中收益。8×32 的优势只有10.75周期（相对最快 RVV 为1.038634×），不扩大成所有输入／应用的宽裕优势。K13 的 S1 vdot 增加2.75周期（1.3095%）；即使保留较快的 S0 vdot 210周期，也慢于175周期的 S1 RVV，其比值为0.833333×。因此尾部形状继续以较快 RVV 为性能对照，不能把旧 S2 对较慢 RVV 的历史余量直接沿用。

S1 basic 的三个整块形状虽有绝对周期下降，仍均慢于对应的最快 RVV；不能用同为 basic 的较慢 RVV 分母来宣称它们胜出。主批次、补充重放和归档验收现已实际通过，三个整块形状的 S1 reuse 可作为 R2-SELECT 的合格单项候选；K13 vdot 保留回退。生产默认入口、S1+S2 组合、R4/T17 尚未在本轮完成。

## 实际机器码的指令账本

`static-instruction-accounting.json` 对 dataset0 的32个 core 内核体逐条解码，以实际 ELF 哈希绑定输入；结果与生成 manifest 的源码指令数逐项一致。下表只计受检内核体；运行窗口的 `instret` 还包括原合同固定的7条指令。endtoend 版本在两种候选上均额外增加 `4 + 2M` 条指令，这不是可以从周期中扣除的固定时间。

| 形状 | basic vdot S0→S1 | reuse vdot S0→S1 | basic RVV S0→S1 | reuse RVV S0→S1 |
| --- | --- | --- | --- | --- |
| 4×8 | 54→42 | 40→28 | 70→42 | 50→28 |
| 8×32 | 322→274 | 216→168 | 242→146 | 162→90 |
| 16×64 | 1218→1058 | 782→622 | 898→546 | 578→322 |
| 4×13 | 134→142 | 105→110 | 70→42 | 50→28 |

在没有标量尾项的三个形状中，vdot 静态减少 `M×(K/8+2)` 条；K13 反而增加 `M+G` 条，其中 basic 的 `G=M`，reuse 的 `G=M/4`。RVV 静态减少 `3MC+2GC+2M` 条，`C=ceil(K/16)`，`G` 定义相同。这说明独立 S1 对 K13 的 vdot 搬运存在额外成本，也说明对等 RVV 的改进必须保留。实际采用仍由完整 endtoend 周期决定，不能用静态指令数替代。

### 16×64 的 FU 观测与优化方向

`completed-large-shape-fu-diagnostic.json` 从已完成的12份16×64正常运行原始 stdout/stderr 重算 O2 事务，核对每份原始日志哈希和既有 observation 一致；涵盖两种 scope、S0/S1、basic/reuse、三数据集及四次正式重复，共96个 vdot 窗口。检查器 SHA 为冻结的 `27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496`，报告 SHA 为 `38d5023de7b53447f5021e2cce939642d0a4bb05ca6507aba8a0d5c892423205`。

| 16×64/endtoend | 窗口平均周期 | 首次至末次接受的平均跨度 | 每窗接受数 | 观测响应延迟 | 写回阻塞事件 |
| --- | --- | --- | --- | --- | --- |
| S0 basic | 2214.5 | 2032 | 128 | 全为2周期 | 0 |
| S1 basic | 2205 | 2032 | 128 | 全为2周期 | 0 |
| S0 reuse | 846.5 | 640.75 | 128 | 全为2周期 | 0 |
| S1 reuse | 701.25 | 502.5 | 128 | 全为2周期 | 0 |

basic 的 core/endtoend、S0/S1 所有相邻接受间隔均为16周期，尽管 S1 实际少160条指令。S1 reuse/endtoend 的12个窗口共有1152个1周期接受间隔，恰为每窗32组、每组4条 dot 的组内间隔；剩余组间间隔为13／14／15周期。FU 已能在这些组内逐拍接收，记录中没有输出写回阻塞。

因此，当前证据支持优先继续软件的初始化和组间供数／配置安排；它没有给出优先重做 FU 峰值 II 或响应延迟的依据。这是由轨迹形成的优化方向判断，不是对具体 load、vset 或调度器瓶颈的因果证明。接受跨度不是空等周期，不能从总周期直接扣除；退休批次间隔同样不等于某条指令的执行延迟。该诊断没有启动新 EMU，其状态不代替整批验收。

### 首块直接初始化的后续子项

静态账本与内部 vdot 全128位覆盖合同支持一个更小的后续假设：每个行组的首个 dot 直接写最终输出，去掉开头的输出清零和首块相加；其余块仍按 S1 累加，RVV 不变。为检验可实现性，本轮继续在独立输出执行了 [first_dot_probe.py](first_dot_probe.py)，最终源码 SHA-256 `0bb3de513d8a542829be8ca11f19b55b477ca3dff63949469fefe6978f1042d8`。它只在进程内为冻结生成器替换经过精确匹配的内核体，原 candidate／gate／experiment 文件均不改，并以 `r2-s1-first-dot-initialization-probe-v1` 单独标识 manifest 和收据。

最终 `first-dot-probe-02` 的实际执行时间为 **2026-10-23T15:09:55.287051～15:09:58.148756+00:00**。四形状、core/endtoend、S1/firstdot 共 **16份真实 AM ELF、8对完整布局检查、64个内核体各9组模型输入 PASS**。八份探针 S1 对照 BIN 与 `build-02` 对应 dataset0 规范镜像完全相同；配对 cases.h、非内核加载字节和 RVV 两个完整槽均相同。全128位结果、带毒初值、行边界、CSR、实际 GNU 编码和指令差额检查均通过。

此前 `first-dot-probe-01`（执行入口 SHA `a2651f699509a1224773afe34b2c92648543a03ff5f25cbfd170fa03299b6a32`，15:05:24.953116～15:05:27.830298+00:00）已经完成相同16 ELF 检查，原结果保留。独立源码复核随后发现通用入口未禁止从另一目录执行脚本并复制仓库中的不同版本，本轮补上 `__file__` 与所选 repo 的同源检查；不改算术变换。`first-dot-entry-negative-01` 实际从外部副本执行新源码，exit=1、报 `probe module roots`，且在创建输出前拒绝；修订后以新源码和新输出完成上述最终探针，没有把新摘要回填旧收据。

| 形状 | basic vdot core：S1→探针 | reuse vdot core：S1→探针 | basic／reuse 减少指令 |
| --- | --- | --- | --- |
| 4×8 | 42→26 | 28→18 | 16／10 |
| 8×32 | 274→242 | 168→148 | 32／20 |
| 16×64 | 1058→994 | 622→582 | 64／40 |
| 4×13 | 142→126 | 110→100 | 16／10 |

差额为 `2M+2G`，endtoend 同差额，RVV 差额为零。K13 处理标量尾项之后、`vmv.x.s` 之前的 e32/VL4 配置保留；不能因为删除了首块配置就让提取宽度变成 e8。完整输出的建立依赖当前内部 vdot 成功执行时低32位给结果、高96位清零、不读旧目的值的合同，只适用于已有且至少包含一块 dot8 的形状。

状态为 `FIRST_DOT_16_AM_ELFS_MODEL_AND_PAIR_LAYOUT_PASS_NOT_RUNTIME`。**没有新 EMU、NEMU、周期、高位故障注入或运行采用结论；该探针不冒充 v2 规范构建。** 接续时把它作为 R2-S1 的一个子项，先增加独立的精确再生／运行合同，确认首条实际 custom 目的变更后的拒错及正常恢复，再以原 S1 和最快合格 RVV 做完整配对 endtoend 测量；不得把探针的静态少指令记成性能收益，也不得覆盖 `build-02/run-02`。最终来源、32份构建命令与结果保存在 `first-dot-probe-02`，driver 收据在 `first-dot-probe-02-driver/result.json`。

## 检出迁移与审计入口验证

在新的 Linux `replay-checkout-01` 中使用 `git clone --local --no-hardlinks --no-checkout` 取得完整对象，再以 `core.autocrlf=false` 检出基点 `bca14d45b07ff07a86a7f54bce2b25870e60e2f3`；不共享可写 index 或对象硬链接。新模块六份 Python 文件逐字节复制并记录 SHA，candidate／gate／experiment 与活动运行的冻结身份完全相同，原 Git 对象 `24cb8b2e0fa0b17cad65c82246c572347a351d43` 可实际取得。

2026-10-23T14:41:59.962375～14:42:00.494609+00:00，实际执行 **19项 GNU／模型测试＋19项证据测试，全部 PASS、无跳过**。最终 `test_candidate.py` SHA-256 为 `79f808cefc706076767ecb569235a6bb2e782534fb44151a6f26468e30f419ae`；其中布局测试不向 GNU driver 传 `-mno-relax`，直接验证生成源码中的显式 `.option norelax`。证据测试包含真实临时 Git index 的缺项／旧字节／元数据边界，结果有独立的命令、PID、时间、源码及原始日志哈希收据。

随后在同一检出实际核对52镜像的 **104份构建命令收据**、负控夹具的 **3份命令收据**，并从已完成的 s00/dataset0 两份正常运行原始日志重算数学／CSR／退休／O2事务，以及32个退休诊断窗口和16个FU诊断窗口。状态为 `RELOCATED_SELECTED_RECEIPTS_AND_RAW_RECOMPUTE_PASS`，范围只限所列输入，不能替代完整57次归档审核。以上步骤均未启动新 EMU，不构成新的硬件 T17 或另一成员的独立验收。

## 验证状态与封存交付

本轮封存为 [evidence/merged-v2](evidence/merged-v2/archive-manifest.json)，manifest SHA-256 **`a1af4314c83b29d97b58b7ae9fe65dbc96bb3d050530d2fe7378c022b9415d73`**。2794份载荷的原始大小为529,841,527字节、压缩后存储32,371,267字节；另有三份根元数据。主批和补充保持各自合同及计数，全部原始／存储字节都有SHA-256。支持附件包含失败定位、预检失败及修订后的真实收据、静态探针和本轮运行完成证明。

| 层级 | 实际状态 | 证据与适用范围 |
| --- | --- | --- |
| 主机／实际GNU／有限模型 | PASS | 最终19项候选测试＋19项证据测试，无跳过；全128位、CSR、行边界和明确负测，不冒充整核 |
| 真实AM ELF及比较布局 | PASS | 52镜像、26对完整加载布局；四槽外BIN逐字节相同，独立对象无REL/RELA且恰为32768字节 |
| 合并EMU上的R2主矩阵／DiffTest | PASS | 57次进程：56正常＋1预期负控；768正式窗口及4次原计划重放，新负控后同镜像正常恢复 |
| 小尺寸补充进程重放 | PASS | 4正常、96个完整签名匹配、0新增正式窗口；dataset0的4×8／8×32 endtoend，S0/S1各一次 |
| O2 FU事务观测 | PASS，限所测整核窗口 | 原始接受／响应／排空和提交门禁通过；主审计重算384个正式vdot诊断窗口。没有新增独立FU或真实父级硬件回归 |
| 主批跨检出原文重算 | PASS | [Linux主审计](evidence/merged-v2-audit-linux.json)：52 ELF、104构建命令、3夹具命令、57原始进程、负控恢复、统计及768个退休诊断窗口 |
| 补充跨检出原文重算 | PASS | [Linux补充审计](evidence/merged-v2-small-replay-audit-linux.json)：4原始运行、严格身份和96签名；与主审计绑定同一manifest |
| 原生Windows归档字节 | PASS，architecture_recomputed=false | [字节结果](evidence/merged-v2-bytes-windows.json)，使用未改变的检查器和扩展路径，未重新运行EMU |
| 实际Git暂存库存与字节 | PASS，限封存目录 | [index结果](evidence/merged-v2-index-windows.json)：2797普通stage-0文件，全为100644，missing=0、extra=0；读取实际blob并与存储字节一致 |
| 归档外报告与命令日志交付 | PASS，字节与库存层级 | [外置交付检查](evidence/merged-v2-publication-check.json)：31份已有外置报告／日志的普通stage-0 blob与工作树逐字节一致，检查回执自身另行暂存核对 |
| Git whitespace检查 | FAIL，已定位且保留 | `git diff --cached --check`只报candidate.py:143、experiment.py:318、gate.py:172三个EOF空行；八份实测Python源码保持原哈希，没有为格式整理改写源码或关闭检查 |
| 历史B0/H1固定合同 | BLOCKED，原边界保留 | 没有用合并EMU替换旧固定对照，也未重跑未变化的缺项 |
| firstdot及S2布局修复探针 | PASS，仅编译／模型／布局 | 分别16与4份AM ELF；无新运行采用或周期结论，不并入本批性能候选 |
| MERGE-REG、R4、T17、PPA | NOT_TESTED，本轮未接管／未执行 | 不转移上述子集PASS；没有完整干净硬件复现、面积／时序／功耗或成员人工ACK |

封存实际执行时间为 **16:11:55.941594～16:14:42.119004+00:00**。随后将整份归档复制到独立完整Linux检出，从其最终源码执行主审计 **16:15:05.170162～16:16:06.722193+00:00** 和补充审计 **16:16:06.743348～16:16:11.037193+00:00**，三个命令均exit0。完整命令、PID、原始stdout/stderr哈希及外层cleanup收据在 [Linux验证收据](evidence/merged-v2-verification-linux/result.json)。主审计报告SHA为 `b035c4b400a7d8cfbca6c45cf41c8582ee965fff1dede5cf59320199912d33be`，补充报告为 `2165d95cda3282b6c81c0ce9164a42997bec9c0b4bd69d4ef469d505264e4d0c`。

归档重算使用提取后的规范镜像、精确再生、原始日志、数学／CSR／退休及事务检查，不只接受缓存PASS。它只对普通support附件做字节核验；补充运行由独立helper再次做架构重算，其余探针不声称离线重新执行。EMU、正常NEMU、flash、硬件／依赖树、AM库和原GNU工具实体没有随归档分发，独立审计不重新验证这些物理输入，不等同于T17。运行阶段的前后实体身份检查则保留在原始批次中。

### Windows长路径的实际定位与修复方式

首次原生Windows字节命令exit1，报292字符深层附件路径不存在；原失败命令及日志在 [普通路径失败收据](evidence/merged-v2-verification-windows/command.json)。同一文件用普通路径再次读取仍失败，用 `\\?\` 扩展路径则得到与manifest完全一致的SHA `014841c334ad962ded17a96edef030acb0e621944a1f827dda49b271d4f10055`。在同一Python 3.13.13、Windows 11环境中，用扩展repo／archive／output路径调用原 `evidence.py --action bytes`，于 **16:20:09.708155～16:20:11.870152+00:00** 完成全部2794载荷校验；没有删附件、改清单、改检查器或修改系统注册表。诊断及完整命令见 [扩展路径成功收据](evidence/merged-v2-verification-windows-longpath/command.json)。

实际暂存使用命令级 `git -c core.longpaths=true`，仅对本模块属性文件及明确封存目录操作；随后原index入口使用相同扩展repo路径，实际Git根仍为原独立工作区。**16:22:53.904425～16:23:02.438410+00:00** 完成暂存及全部2797 blob核验，报告SHA `8b61359f1d3c0e1c49a0b95168e88ac5aee75abaa1b9db515a1f7b6394b01f46`；[index命令收据](evidence/merged-v2-verification-index/result.json)保留实际过程。归档外报告及日志另随成果暂存，不能用封存目录的index PASS替代它们的交付检查。

封存后的README补充了这次发现的Windows长路径及外置日志暂存说明；归档中的README保留导出时的58d32dc9…版本。全部八份Python源码与验证时字节保持一致，已封存的manifest及载荷不改。

发布前对归档外31份报告／命令日志另做实际index逐blob核验。首次检查在Git whitespace步骤exit2；随后直接读取原诊断，确定仅为上述三份冻结源码的EOF空行，工作树未暂存差异检查为exit0。保留这项格式FAIL和首次操作身份，不将其改写为整项PASS；该问题不改变机器码、模型或运行身份。外置交付检查记录精确字节、文件链接及完整原始诊断，其自身也单独核对暂存blob；没有修改全局Git配置或降低任何运行／证据门禁。

## 接续条件与具体下一动作

后续先按协调Issue确认叶级认领和实际运行；不得把本轮结果的封存或推送当成他人MERGE-REG已经移交。已有输出不覆盖，未改变的主批、主机测试和探针不重复运行。

1. **选择已经合格的S0/S1。** 本模块主批、补充重放及归档验收已闭合，R2-SELECT可直接以完整矩阵评估三个整块形状的S1 reuse；K13保留S0 vdot回退及S1 reuse RVV。先固定按形状选择的候选身份，再为实际选择入口完成受影响的回归。S2和firstdot尚未具备的资格不阻止这项选择；生产默认入口仍按路线完成R4/O5和T17后切换。
2. **若继续当前默认的S2修复方向，先补新合同，后测周期。** 读取封存逻辑路径 `support/layout-s2-feasibility-probe-01/probe.py` 与 `state.json`，在独立新模块中把已验证的norelax、四槽8KiB、完整ALLOC／非内核比较及两个精确dots字段例外接入正式构建门禁。保留冻结旧S2生成器和旧归档；在新批次纳入本轮更快RVV并实际测量，覆盖原两形状、三数据集、basic/reuse、core/endtoend、负控恢复和replay。旧K13的209.5→187.25仅作历史记录，不用于候选排序。
3. **若S2已被认领，可独立接续firstdot子项。** 源码从本模块 `first_dot_probe.py` 的最终0bb3de…版本及 `first-dot-probe-02` 起步，不重做已经通过的可行性探针。先定义独立精确再生／运行合同，把首条实际rd改变后的高位拒错目标和正常恢复验证清楚；然后才用新输出与原S1及最快合格RVV配对测量。正收益进入选择，退化或前提失败则保留本轮合格版本；不得转借本轮S1的动态PASS。

通用已确认命令见README。本轮没有实现新的S2或firstdot正式运行入口，因此不提供未经本轮验证的“直接运行”命令；并发后续实现的进度与输入保护以协调Issue及其成果为准。两项都是已有包的明确接续，不额外创建主任务包或长期锁。

## 本地运行记录与恢复入口

本节保留单次运行定位，通用命令和配置字段见 [README.md](README.md)。

- 独立工作区：`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\working-r2s1-20261023-2100`。
- WSL：`Ubuntu-22.04`；结果根目录 `R=/home/lizufan/riscv-lab/r2-s1-20261023-2100`。
- 私有 AM：`$R/deps/nexus-am`；配置为本模块被忽略的 `runtime.local.json`；来源见 `$R/dependency-setup.json`。
- 被否决的首批：`$R/build-01`、`$R/run-01`、`$R/run-01-source`、`$R/run-01-stop.json`、`$R/run-01-stop-confirmation.json`；差异诊断 `$R/pair-layout-diagnostic-01.json`。
- 修复探针：`$R/layout-probe-01`、`$R/layout-build-probe-01`、`$R/old-layout-negative-check.json`。
- 完整根因及历史影响：`$R/layout-root-cause.json`、`$R/historical-s2-layout-review.json`、`$R/layout-s2-feasibility-probe-01`。
- 指令与轨迹诊断：`$R/static-instruction-accounting.json`、`$R/retirement-diagnostic-s00.json`、`$R/completed-large-shape-fu-diagnostic.json`。
- 新规范构建：`$R/build-02`，真实开始／结束为 `2026-10-23T13:57:47.249653+00:00`／`13:58:02.225717+00:00`，52 镜像和26对布局检查 PASS。
- 新硬件批次：`$R/run-02/state.json`、`$R/run-02-driver.json` 及同级 stdout/stderr；内层实际区间 `2026-10-23T13:59:13.409730～15:47:56.865774+00:00`。ChatPC operation `716a6ee805ae260048ab831b3dbbd5fe.8a2be27f5710ca21f6ada377fc677e4f` 已 succeeded、exit0、cleanup_complete=true；15:48:45.677873+00:00 确认 driver/controller PID296/372 已不存在、EMU 进程为空，证明在 `$R/run-02-completion.json`。最终state SHA-256 `ee0a47aeb848b5d65a733b21adbaef85e1ecad722f037b516a724494816be337`。
- 小尺寸补充：`$R/replay-small-01/{state,results}.json`、`$R/replay-small-01-driver/result.json`、`$R/replay-small-01-completion.json`；已自然结束，四次正常及96签名匹配PASS。其活动输入保护收束见 [Issue 6369287032](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6369287032)。
- 第一份主机测试脚本曾发生 Python 列表／字符串拼接错误，保存在 `$R/host-tests.*`，不是硬件错误；修正后 `$R/host-tests-02.*` 的13项实际 GNU 测试通过。固定布局版 `$R/host-tests-03.*` 的19项测试通过。
- Linux 独立检出与验证：`$R/replay-checkout-01`、`$R/replay-checkout-setup-01/result.json`、`$R/relocated-host-tests-01/result.json`、`$R/relocated-audit-precheck-01.json`。
- 首块初始化子项探针：`$R/first-dot-probe-02/state.json`、`$R/first-dot-probe-02-driver/result.json`；入口拒错在 `$R/first-dot-entry-negative-01/result.json`。旧探针及旧源码另保留在 `$R/first-dot-probe-01`。这些短任务均已结束，没有活动 EMU 或输入保护。

本模块运行不支持断点恢复。重新构建与重新运行都要求新输出，不能覆盖原证据或称作续跑。认领、在途进程和保护释放只以 [协调 Issue #2](https://github.com/cc77-builder/riscv/issues/2) 的实际事件为准；本文件不建立第二张持有人表。
