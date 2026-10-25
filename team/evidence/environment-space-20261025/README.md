# Windows 副本收拢审查、WSL 缓存清理与审计检出保全

操作 ID：`20261025-LiZufan001-space-0510`；@LiZufan001 / Pro 主 Agent。工程基点 `e301a360d21a0a942882921f8b481c81eff1e478`。空间工作从 2026-10-25 05:10（UTC+08:00）开始，准确运行时间见封存回执，发布结束见 [Issue #2](https://github.com/cc77-builder/riscv/issues/2)。本包记录环境与保全事实，不授予新的构建、功能、性能、PPA 或人工验收资格。

## 已完成结果

| 范围 | 实际结果与边界 |
| --- | --- |
| Windows 外部收拢 | 用户另行授权的 Codex 任务将 22 个工程检出减至 5 个。本轮 Pro 独立审查通过；17 个原路径不存在，集中恢复资料继续保留。外部任务口径的逻辑净减少为 10,066,946,446 B，约 **9.38 GiB**。本轮 Pro 没有追加 Windows 删除。 |
| WSL 精确缓存清理 | **1,038 个文件实际删除**，原逻辑量 1,360,788,167 B，原分配量 **1,363,247,104 B（1.2696 GiB）**。26,064 个保护文件前后 SHA-256 相同；清单无保护项交集，残留目标为 0。 |
| T17 生成 C++ 保全 | 324 个生成 C++／头文件的 833,746,958 B 原字节保存在 Windows 的 **27,472,009 B ZIP**。全成员解压大小与 SHA 通过，删除前再次核验。不是再生成成功。 |
| 七个历史审计检出 | **七棵均已实际恢复验证通过**；178,801 个路径项的完整工作树／Git／元数据被保全，原分配量 **6,182,318,080 B（5.7577 GiB）**。原七目录仍存在且未修改；这只是可退役方案准备完成，不是已经删除。 |
| 最新整盘观察 | **22:59 UTC** 的 Linux 已用为 **45,332,054,016 B（42.2188 GiB）**；VHDX 长度和 `GetCompressedFileSizeW` 报告均为 **55,285,121,024 B（51.4883 GiB）**。本轮没有关闭 WSL、修改 swap 配置、trim 或压缩 VHDX。 |

缓存清理完成于 **2026-10-24 22:08:28 UTC**。文件系统已用量在该操作前后由 46,590,922,752 B 降至 45,233,942,528 B，实测净减少 1,356,980,224 B；它与删除清单分配量的差异包含新记录及同期文件系统活动，不能强行视为同一个数。

扣除新保留的 C++ ZIP，仅按“原文件逻辑字节减 ZIP 文件字节”计算为 1,333,316,158 B（1.2417 GiB）；该值**不含新增日志、清单和后续审计保全成本，也不是宿主 D 盘实际空闲增量**。七目录保全另行记账。

## WSL 删除合同与恢复依据

只处理已经结束任务的精确中间文件，不运行官方清理目标，不修改官方源码、参考实现或判定程序。

| 实际删除组 | 文件数 | 原逻辑字节 | 原分配字节 | 保全／恢复依据 |
| --- | ---: | ---: | ---: | --- |
| T17 `emu-compile/*.d` | 354 | 623,270 | 1,638,400 | 已结束构建的依赖缓存；仅此显式目录 |
| T17 `emu-compile/*.o` | 351 | 93,767,456 | 94,527,488 | 已结束编译对象 |
| T17 内部 `VSimTop__ALL.a` | 1 | 93,073,398 | 93,073,408 | EMU 编译中间归档，非 AM 交付库 |
| T17 `*.gch` | 2 | 337,401,744 | 337,408,000 | 预编译头缓存 |
| T17 生成 `*.cpp` | 318 | 787,305,205 | 787,959,808 | 删除前独立 ZIP 保全原字节 |
| T17 生成 `*.h` | 6 | 46,441,753 | 46,452,736 | 同一独立 ZIP |
| hoisted 的 `vdot-perf.txt` | 6 | 2,175,341 | 2,187,264 | 固定 objdump 与原 `-d` 参数逐字节再生一致 |

T17 目录为 `/home/lizufan/riscv-lab/t17-clean-20261024-0854/clean-02/source/build/emu-compile`；保留 `VSimTop.mk`、`VSimTop__verFiles.dat`、`VSimTop_classes.mk`。六个文本的精确路径见 `wsl-large-cleanup-plan-01.json`，不将同名模式扩展到其他目录。

**明确保留：** 所有最终 EMU、参考 NEMU、flash、AM 最终库、NEMU 依赖文件及身份输入、Git 供体链、正式和失败日志、原始 FST、官方源码，以及 T17/T04 合同要求的物理文件。T17/T04 合同中的冻结输入及两份同 SHA 的 `SimTop.fir` 均保留，不能因 SHA 相同而合并。

实际执行工具 `wsl-clean-exact-02.py` 的 SHA-256 为 `2495afb79b03046118191d0540be70dbbe2eb65fd7bdc37f4268af0e4ea0b572`。脚本拒绝 Python 优化模式；删除前绑定路径、普通文件类型、链接数、inode、mtime、大小与 SHA，并检查运行占用。逐项意图／完成写入日志，成功后核对所有目标不存在和全部保护字节。机器结果为 `wsl-large-cleanup-result-01.json`，SHA `b8f2100eb039ac32645418571723103124fd7a977b71890979a9c21cc07ebbce`。

### 原失败与替代路线

先前六个文本清理两次均在 `unlink` 前被进程守护阻止，历史阶段删除数为 0；`cleanup-after-01.json` 保留这一事实，不能改写成后来 1,038 项清理的结果。后续使用可读的 PID/start、父进程可执行文件与参数、UID、cgroup 共同识别 systemd 用户 PAM 辅助进程；不可读的 FD/maps 仍记录为不可读。没有提权、杀死该系统进程或更改安全配置；旧 PID 已结束，其完整身份不追认。

T17 C++ 曾尝试用固定工具和原 Verilator 命令、仅改变输出目录再生成。240 秒时仍无 324 份匹配输出，终止自己的进程组，子进程退出 -15，25,179 保护输入未变。`t17-regeneration-comparison-01.json`、原 stdout/stderr、失败目录及回执均保留；**不记再生成 PASS**。随后采用原字节压缩保全，避免继续消耗构建资源。

### T17 C++ 恢复入口

必须保留：

`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\runtime-space-20261025-0510\retained-t17-generated-01`

其中：

- `t17-generated-cpp-h.zip`：SHA `d7027b4bf97082eaaa13baa295d712fe5d8c2dcf52ddf72254752978fcf501b8`。
- `manifest.json`：SHA `30bc3521614873922d89d11aa96d9b06a0f538b7adacc382bdd7b0b9edff87d6`。
- `restore.py`：SHA `6e8a82772cc4c64a0bcc14bc6bda31d0de1a6d6b71d9261ec8e236ec69814c99`。

在 Linux 用 `python3 restore.py` 默认只核验；`--restore-to 新建目录` 才恢复字节、mode 和 mtime，已有目标目录会拒绝。本轮默认核验实际 PASS（324 项），见 `t17-restore-helper-verify-01.json`。此归档不包含可重建对象／PCH，不代表工具链重建已经逐位等价，也不会赋予新 EMU 资格。

## 七个历史审计检出的可恢复保全

七个目录都是已经结束的审计／复查检出；它们仍可能含大量未提交状态或 no-checkout 差异，不能 reset/clean 后再备份。其父目录中的原报告、失败现场和回执不在退役建议范围内。

公共前缀：`/home/lizufan/riscv-lab/`。

| ID | 精确相对目录 | 角色 | 原分配字节 |
| --- | --- | --- | ---: |
| source-01 | `r2s1-firstdot-detached-20261024-1458/source` | firstdot 独立 C＋矩阵审计 | 1,001,058,304 |
| source-02 | `r2s3-runtime-detached-20261024-1818/source` | config-reuse 独立 C＋矩阵审计 | 1,051,590,656 |
| source-03 | `r2-s1-20261023-2100/replay-checkout-01` | S1 主批／补充原文复算 | 747,659,264 |
| source-04 | `r2-s2-fixed-audit-20261024-0001/replay-checkout-01` | S2 固定布局／强 RVV probe 审计 | 838,107,136 |
| source-05 | `r2-select-20261024-0001/replay-checkout-01` | 原镜像选择／导出复核 | 822,353,920 |
| source-06 | `t17-clean-20261024-0854/merge-review/source` | MERGE-REG 离线收尾 | 860,745,728 |
| source-07 | `t17-clean-20261024-0854/portable-audit/source` | T17 最终封存证据独立审计 | 860,803,072 |
| 合计 | 七个 source／replay-checkout 本体 | 父级与其他实验目录不包含 | **6,182,318,080（5.7577 GiB）** |

`source-06` 的身份由 [MERGE-REG locations](../../optimizations/o2/fullcore/evidence/merged-regression-v1/locations.json) 和 [最终审计回执](../../optimizations/o2/fullcore/evidence/merged-regression-v1/final-audit-receipt.json) 明确绑定；本轮又读取父目录原 `archive-audit-02.json` 核对最终工具身份。不能把 T17 portable PASS 转给 MERGE-REG，二者各有原始证明。

最终结果 `audit-backup-preparation-result-03.json`（SHA `e8d07843ef3c22f268aa954e5547bb7b329c4e6f676b98d6681c303815e8c687`）为 `READY_FOR_RETIREMENT_REVIEW_NOT_EXECUTED`。最终 v3 运行从 22:52:57 至 22:55:47 UTC，exit 0、宿主 cleanup complete；这不表示原始目录已经退役。

七棵原普通文件合计逻辑量 6,508,098,842 B；去重后 14,099 个载荷成员、原字节 1,433,333,462 B，ZIP 为 1,173,334,644 B。逻辑量、`st_blocks` 分配量与压缩量不是同一口径。七棵合计 178,801 个路径项（含根、目录和符号链接）。

| 阶段 | 实际验证结果 |
| --- | --- |
| 初次归档／v1 | 全 ZIP 流式 SHA 通过，source-01 实际恢复字节／元数据通过；严格 Git status 相等检查失败，保留原 stderr 与恢复现场。 |
| v2 | source-01 完整恢复／Git fsck／身份通过，5 项针对性拒错通过；随后 source-02 出现另一项换行转换差异，整体停止，未宣称七棵通过。 |
| 预先固定的全量普通文件画像 | 扫描七棵 127,564 个现存 stage-0 普通文件；每棵排除的 10 项 gitlink 等分别记录，不声称覆盖所有 Git 类型。固定 8 处有限规范化差异：七份同一 CRLF CSV 和 source-02 的一份 gzip。 |
| 最终 v3 | 复用 source-01 已完成的 v2 实际恢复证明；对 source-02 的既有真实恢复副本重新核验；source-03～07 新建目录实际恢复。七棵均通过原字节、元数据、Git 身份／refs／完整 fsck；Git 只读操作前后 index 字节不变。另 6 项拒错通过。 |

额外的 Git `M` 来自原索引 stat 缓存与原 `text eol=lf` 规则：新 inode 触发内容重检，filtered hash 与原始 blob 不同。原件、ZIP 和恢复件的原字节相同，不能把状态差异写成归档损坏。接受范围由实际恢复前已固定的 source-ID／HEAD／原路径／有限文件画像绑定；新出现的无关状态、重复画像状态、原有状态消失及身份错配均拒绝。**七棵 Git status 并非逐字节相同**；有穷差异和所有原状态在回执中逐项保留，不能用“忽略所有 M”概括。

source-01 的 v2 证明没有冒写为 v3 重跑，source-02 也没有再次解压。v2/v3 累计在证明通过后移除本轮新生成的 7 份临时恢复副本，三个临时根均为空；这些副本是本轮刚创建的验证产物，不计作原有工程数据的额外清理收益。初次和第二次失败回执、诊断及全部原七目录保持。

### 七目录恢复入口与保全成本

必须保留：

`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\runtime-space-20261025-0510\retained-audit-checkouts-01`

| 文件 | 大小 B | SHA-256 |
| --- | ---: | --- |
| `payload.zip` | 1,173,334,644 | `5d479fae7c94bf54fc27ce975a7a96098eb3f6bb2287812fd9e7bfd301ca901d` |
| `manifest.json` | 84,825,596 | `87311d16105e03cff7f839307b7caeb3b20f4ee72370a308f0f31d70fb689af4` |
| `restore-v3.py` | 15,669 | `958a5ecad5f9f38635917719d1f2168fcd67bfb58346a4bdd71a9e5eb147eec5` |
| `normalization-profile.json` | 19,034 | `521323f64962642af0b397ac7cbd500687e82a9e5cf42f0c5b15f02acf8bd736` |
| 历史 `restore.py`（v2） | 15,243 | `18746112a89a86fd0c8d0cd153d95ab893d08c2410895526f620c290cba5d1fd` |

以上五件合计 **1,258,210,186 B（1.1718 GiB）**，宿主 API 报告与各自文件长度一致；不把它称为含全部 NTFS 簇／元数据的精确成本。若以后退役原七目录，原 Linux 分配量减这些保全文件字节约 **4.5859 GiB**，仅是跨存储口径的规划差额，尚未实现，也不包括新日志和仓库交付包。

在同 UID/GID 的 Linux 环境，保持上表的 ZIP、manifest、profile 与 helper 同目录：

```bash
python3 restore-v3.py
python3 restore-v3.py --source-id source-03 \
  --restore-to /home/lizufan/riscv-lab/NEW_DIRECTORY \
  --receipt /home/lizufan/riscv-lab/NEW_RECEIPT.json
```

第一条默认只核验备份；第二条仅向不存在的新目标恢复，拒绝覆盖原七目录，receipt 必须在原件／恢复树外。helper 不删除任何目录。不声称可在 Windows 上完整重建 Linux 元数据。

22:59 的补充就绪快照解析三个已知项目根的 384 条 alternates（含相对路径），0 条借用原七目录，0 条未解析；未观察到目标进程匹配。不过有 14 个进程身份存在不可读的 cwd/exe/fd/maps 字段，因此不是“整个系统绝无占用”的证明，也不能代替退役前的新检查。


保全范围包含完整 `.git`（所有引用及无引用对象、index、config、refs、reflog）和全部工作树文件。按内容去重仅发生在新 ZIP 载荷中；恢复为独立普通文件，不硬链共享原仓库对象。原目录与恢复目录的 Git top-level、gitdir、common-dir 都实际核对；拒绝相关环境覆盖、`core.worktree`、alternates、Git 元数据符号链接、硬链接、特殊文件和非当前 UID/GID。恢复比对完整路径集合、普通文件 SHA/大小，以及根目录／目录／符号链接的所列 mode、UID/GID、xattr、mtime；不声称重建 inode、ctime 或原 atime。

**原七目录当前未删除。** 删除源码物理副本超出本轮原先仅清理可重建中间文件的范围，需要用户对这份具体清单决定保留形式。历史 DONE 和恢复证明不代替该决定。执行前还须重检新增内容、借用者及当前占用；原目录若发生变化则保留该项。归档及其恢复工具不得随原目录退役一起清理。

## 为什么目前不能承诺 10 GiB

以下分类与重复普查来自 22:15:56～22:17:12 UTC 的 `wsl-duplicate-census-01.json`／`wsl-duplicate-summary-01.json`，并非 22:59 的再次全量扫描。

下面是三个项目根的只读分类，按普通文件的实际分配字节归类，未包含目录开销等，因此不能与 `df` 逐项严丝合缝相加。路径优先级为 `.git → team → out → build/rtl → other`。

| 类别 | 文件数 | 分配字节 | GiB |
| --- | ---: | ---: | ---: |
| `team` 下混合源码／文档／证据 | 419,483 | 12,281,470,976 | 11.4380 |
| Git 元数据／对象 | 26,940 | 8,070,123,520 | 7.5159 |
| build（含冻结输入） | 19,241 | 6,365,876,224 | 5.9287 |
| Mill out | 88,538 | 1,852,407,808 | 1.7252 |
| 其他源码／工具／运行内容 | 230,278 | 8,052,723,712 | 7.4997 |

三个根为 `/home/lizufan/riscv-lab`、`/home/lizufan/xiangshan-t10-t11-supervisor-20261013`、`/home/lizufan/xiangshan-validation-20261013`。清理后主 lab 约 30.38 GB（字节口径），另两棵历史树仍约 7.05 GB；不是整个 WSL 都由可丢弃缓存组成。

对其中 **≥1 MiB** 的 4,683 个独立 inode 做内容 SHA，发现 439 个重复组，重复分配上界 **13,038,112,768 B（12.1427 GiB）**。这不是全量小文件去重普查，也不是可删除清单；包含冻结双份 FIR、独立 Git 副本等。该上界与七目录范围有重叠，**不得相加**。新备份占用也必须另计。

即使七目录全部获准退役，仅按当前测量粗减，Linux 已用仍约 **36.46 GiB**（基于 22:59 的 42.2188 GiB 样本减去 5.7577 GiB）。这个估算不证明 10 GiB 永远不可达；它说明还需要明确更多已结束数据的长期保留形式。也不能把 VHDX 51.49 GiB 与 Linux 已用 42.22 GiB 的差额，当作已保证可压缩回收的额度。

后续优先级：先决定并验证具体历史检出的归档退役；再从现有盘点识别有较大净收益且无运行／冻结依赖的大项；数据整理结束后，如用户授权维护窗口，再评估 VHD 回收。不要为了空间目标改变冻结独立对象库的合同，不对现存仓库做跨库硬链接或未经证明的 prune。

## Windows 外部清理的独立复核

外部操作 ID 为 `20261025-codex-xiangshan-consolidation`，恢复根：

`D:\Projects\daily\codex\diagnostics\xiangshan-consolidation-20261025`

本轮 `windows-review-02.py` 实际核对：

- 364 项原完整性清单的原字节 SHA 全部相符；
- 14,210 个唯一 ZIP 成员逐项解压哈希，252,036 条文件映射引用；
- 恢复库 126,515 个 Git 对象（10,985 commit／74,958 tree／40,572 blob），178 条引用，其中 61 条专门保留原无引用对象；
- 新执行 `git fsck --full --no-reflogs` 通过，无 alternates；原有 17 项实际恢复 PASS 回执的身份和范围已核对，本轮没有再跑 17 次恢复；
- 17 个删除目录均不存在，5 个保留目录的 HEAD／分支／状态与外部记录一致；
- 其他 R3 工作树的计分板 934 B 追加保留，原前缀一致；本轮没有替外部任务提交该脏工作树。

原第一次审查因可选字段未统一而失败，原文保留；第二次修正只读审查通过。外部恢复以字节和 Git/index 语义为目标，不声称重建所有 NTFS 元数据或旧 common-dir 目录布局。

恢复脚本使用集中 `recovery.git`；原脚本的验证模式会写原 OUT 回执，不应为了“再确认”覆盖冻结备份。只对某个恢复 clone 做 repack 并不允许删除集中恢复库，它还保存其他 refs 和原孤立对象。恢复根、`files.zip`、`recovery.git`、清单和工具应整体保留。

外部报告中 D 盘空闲的观测增加约 9.89 GiB；这与逻辑净减少 9.38 GiB 是两种口径，不能声称全部由该操作单独造成。后来 21:43→22:09 UTC D 盘空闲又少约 5.76 GB，因果仍未闭合：VHDX 长度未变，22:15 实际分配仍为 55,285,121,024 B，当时旧 `D:\WSL\wsl-swap.vhdx` 不存在，列出的 Windows pagefile 仅在 C 盘。不能据历史环境说明归咎于 D 盘 swap，也不能把这个未知差额算进已证实的清理收益。

## 当前仓库的两处原字节保护

恢复诊断发现，当前根规则 `team/** text eol=lf` 也会影响两个已经冻结的证据文件。本轮只增加两个精确路径的 `-text -whitespace` 规则：

- `team/optimizations/o2/r2-config-reuse/.gitattributes`：增加 `evidence/host-v1/host-evidence.tar.gz`。
- `team/optimizations/o2/r2-kernel-audit/.gitattributes`：增加 `evidence/instruction-counts.csv`。

Windows 原生 Git 的工作树与 cached 属性均核对为 `text: unset`；两项 `hash-object` 原始／过滤／既有索引 blob 相同。gzip 保持原 2,081,426 B，SHA `85558c3670289b74d544cfa6da38fa4f825f0fa56e1e7e7bfbf218fc8eba93a9`；CSV 保持原 1,184 B，SHA `864d6c5fe53b6dd90a52be5430b61ac0ff74bcd30055d1e15e32d372f34db2d6`。结果 `current-attribute-after-01.json` 的 SHA 为 `1f9d5edb0db8553d167682c31c34aad6ac60aa894d45235957ffcd35e7d9bafe`。

未重写这两个载荷，没有对历史七棵源码追加规则，没有执行 renormalize，也没有修改官方程序。这两条规则防止未来正常暂存时破坏被冻结证据的原字节。

## 交付、复核与接续

[manifest.json](manifest.json) 对 [payload.zip](payload.zip) 及其中每份原件固定大小和 SHA。包内保存本轮检查／清理／保全脚本、阶段原文、失败记录、关键宿主回执及外部审查依据；外部大恢复载荷不重复塞入 Git，具体位置及 pin 见上述恢复入口和 manifest 的外部依赖。

复核应先验证 ZIP 与逐成员 SHA，再读取相应阶段结果；只有访问实际物理恢复根，才能重做恢复检查。仓库小包本身不包含七棵源码与生成 C++ 的全部恢复载荷，不能声称仅靠本页就已离线恢复它们。

环境文档仍保留 2026-10-09 的历史 20 GB 内存／16 GB swap 配置，不能当作现在实况。22:59 实测 `C:\Users\LiZufan\.wslconfig` 不存在；本轮实际 Linux `MemTotal` 为 16,094,264 KiB，swap 4,194,304 KiB 且采样时使用为 0；未修改配置。

工程反馈：重复复制完整 `team` 和历史 Git 库已成为主要空间成本。以后新的独立审计应在其合同允许范围内，预先规定所需固定源、证据输入及任务结束后的保全形式，继续使用独立恢复验证；不要在每轮之后临时判断能否删除。此建议不自动追溯修改冻结合同，也不新增自动清理任务。

此前 R3 首次传输的未知 worker 回执及旧锁继续按 [R3 handoff](../../optimizations/o4/reduce/evidence/handoff.json) 保护，本轮没有重放未知操作或删除对应目录。最终推送采用正常快进；认领与集成窗口以 Issue 的 END/DONE 为准。


## 2026-10-26：本账号本机工作区收拢结果

操作 20261026-LiZufan001-workspace-reuse-0141 复用既有常驻原生检出，
将指定 Windows 主仓正常快进至 926b2e2a3a2f2f6a5eb6208e00efd8e79e3ddd05。
按实际占用、对象借用和原件保全检查，退役 4 个近期原生重复检出、
7 个旧 Windows 检出/工作树和 3 个传输裸仓，本轮未新建完整源码检出。
详细身份、逐项回执、保留项与原路径见[本次证据](workspace-reuse-20261026.json)。

原生分配空间减少 3,420,065,792 B；Windows 被移除文件逻辑量
4,736,351,951 B。D 盘从本轮开始的 76,488,978,432 B 可用变为
80,990,674,944 B，包含期间主仓更新、备份等活动，不能与 Linux 内部空闲量
混称为 VHD 物理回收。没有关闭 WSL 或压缩 VHD。

未提交文件、暂存区、Git 元数据及全部 8 个未在主仓对象库出现的旧 Git
对象已保存、逐项校验；额外对象 pack 通过 index-pack --strict 和 verify-pack。
恢复资料在本机 monitor 的三个 retained-* 目录。干净原生检出由原 HEAD 与
保存的 .git 元数据恢复，仍依赖固定原生供体。Windows 工作树先在原 HEAD
建立工作区，再按 ZIP 内 files/ 和两份 binary patch 恢复工作区与暂存内容，
原 Git index 也已保存。独立 Windows 仓库的普通对象从主仓复用，补充保存的
extra pack，再恢复各 ZIP 中的 Git 元数据。所有这些备份继续保留。

先前七个审计检出已于 2026-10-25 21:11+08 在另一项已完成操作中删除，
不计本次回收。仍有历史原生供体链与冻结运行输入保留，不把它们称作已经
收拢删除。T17 EMU、参考库、AM、flash 继续供真实验证使用。团队共享开发规则
未修改，本账号本机工作方式写入其私有项目提示词。
