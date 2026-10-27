# R0：固定原生 Git 供体与独立源码检出

操作：`20261025-LiZufan001-r0-native-store-1541`。基点：`cd4463660686079d365705bfd8f37a86c73161d4`。本轮只补源码准备能力；生产 RTL、官方程序、冻结验证器、R5 默认和既有性能结论不变。

## 结果与采用范围

**PASS：新建自包含的固定裸仓供体，新工作区直接引用这一个供体，拥有自己的 `.git` 和 index。** 已验证从该供体创建新工作区，再导入后继提交的增量 bundle；新对象落在接收工作区，供体不更新。旧七层供体链仍保留，没有迁移、解除依赖或退役旧目录。

| 核对项 | 实际结果 |
| --- | --- |
| 固定提交／树 | `cd4463660686079d365705bfd8f37a86c73161d4` / `6f7b0339fd276fae40eb6c00aa8259958a92f18b` |
| 完整输入 bundle | 356,796,375 B；SHA-256 `21b13ecfd04603376fdb5b642a1ed0ee797bfce928fb4d15cce919e52c777331`；在空裸仓中先 verify，再 fetch |
| 自包含供体 | 无 alternates、浅克隆、promisor、替换引用／graft、符号链接或硬链接对象文件；完整 `git fsck` 通过；pin 和 HEAD 固定，pack/idx 原字节写入清单 |
| 最终源码 | 工具 SHA-256 `1b6598d63bbe561882b59e2bfc6f4e25b25952d4701051cfcc157d2b59670a05`；测试 `61ebd6986172a73695f83f8f9361198bedb6a0c3acadce5dea7f94b10657c62f` |
| 真实 Git 用例 | 最终 12 项在 WSL Ubuntu 22.04 / Python 3.10.12 / Git 2.34.1 通过；同一源码在独立 Linux / Python 3.12.14 / Git 2.51.1 通过 |
| 真实工程消费者 | 原 `clean_entry.bind_sources()` 在固定基点和后继源码检出均通过；5 项冻结 R4 绑定、7 项源 blob 绑定、5 个 T17 adapter 身份保持 |
| 历史对象 | 消费者实际使用的 6 份 `24cb8b2e…` 历史源码，在旧链、新供体和新检出中的 Git OID、SHA-256、长度全部一致 |
| 后继提交接续 | 工具提交 `a1da37e7cb69a192db3dcfff67c6adcb3685e37b`，树 `cbb06b591f87bad6549b1413bbb5045344fa3bce`；7,611 B 增量包经新检出 verify/fetch 后，完整提交／树、祖先关系、源码 SHA、干净状态、单供体、无默认远端和完整 fsck 均通过 |
| 旧数据保全 | 七个原生仓库的 objects、HEAD/config/index/packed-refs/refs 共 128 个实际文件、563,574,012 B，文件集合和每项字节数／SHA-256 前后相同；这不是旧工作树全目录重新验收 |

[evidence.json](evidence.json)保存合同、来源链、实际命令与 stdout/stderr、供体清单、原 Git 文件清单、后继接续及恢复回执。完整 bundle、物理供体和原始操作回执保存在下述运行根，不把大型对象包重复提交进团队仓库。

## 为什么采用固定供体

本轮实测原生 Git 对象依赖跨越七个历史实验目录。继续以最近一次实验检出作为下一次 `clone --shared` 的来源，会延长对历史目录的依赖。新的供体只保存固定提交可达的完整 superproject 历史；每个新任务直接从它创建自己的仓库和索引。

Git 的 `--no-hardlinks` 只避免对象文件硬链接，并不保证解除来源原有的 alternates 依赖。共享模式仍依赖供体存在和对象保留，独立模式使用 `--no-local` 传输并检查无外部对象依赖。语义依据：[git-clone](https://git-scm.com/docs/git-clone)、[git-bundle](https://git-scm.com/docs/git-bundle)。本工具不以 Git worktree 共享 common-dir，也不引入自动更新、后台维护或历史目录迁移器。

## 使用入口

在 Linux/WSL 原生目录使用 Linux Git。Python 需要 3.9 或更新版本；本轮实际验证版本如上。Windows 工作树上的 Git 操作继续使用原生 Windows Git。本工具不初始化子模块，不复制未提交改动、未跟踪文件、外部工具链、EMU/NEMU/AM 或冻结实验产物。

以下工具命令从包含本工具的已更新源码根执行，也可改用脚本绝对路径。固定 `cd446366…` 的供体和初始检出尚不包含本工具；先使用另一个已更新检出中的工具创建工作区，再按第 3 步导入后继提交。本机可从下表的 `development/source/team/scripts/prepare-native-source.py` 调用。

### 1. 创建一次固定供体

优先复用已经验证的供体。确需另一固定身份时，使用新目录，并指定完整的 40 位小写提交 SHA：

```bash
python3 -B team/scripts/prepare-native-source.py store \
  --source /absolute/path/to/complete-repository-or-full.bundle \
  --revision cd4463660686079d365705bfd8f37a86c73161d4 \
  --output /absolute/native/path/new-store --threads 2
```

目录输入必须是普通工作树根或裸仓根，不接受任意子目录、普通仓库内的 `.git` 目录或 linked worktree。已存在的输入仓库可通过其原有本地 alternates 提供已提交对象；新输出仍须完整自包含。输入为 bundle 时必须是完整包：工具在空仓中验证，故增量包不能冒充初始来源。

输出中的 `state.json` 应为 `NATIVE_STORE_PASS`；`manifest.json`记录固定提交、树、输入 bundle SHA 和各对象文件字节身份。供体目录及其 manifest/pin 保持不动，不向它 fetch/push，不运行会改变其对象清单的维护操作。需要新固定身份时另建供体。

### 2. 给每个任务创建独立工作区

```bash
python3 -B team/scripts/prepare-native-source.py checkout \
  --store /absolute/native/path/store \
  --mode shared --output /absolute/native/path/new-task --threads 2
```

源码位于 `new-task/source`，状态为 `NATIVE_CHECKOUT_PASS`。`shared`只有一条直接指向固定供体的 alternates，自己的对象、引用和 index 独立；它**不是自包含副本**，不能移动或删除其供体。需要可单独迁移的副本时使用 `--mode independent`，工具会复制完整可达历史并确认无 alternates、符号链接或硬链接对象依赖。

新检出停在固定提交的 detached HEAD，且没有默认 Git remote。需要开发分支或团队远端时在该工作区显式创建；这避免普通 `git push` 意外写入固定供体。不要再以某个实验检出作为下一层共享来源。

### 3. 导入固定基点之后的新提交

固定供体无需随每次团队提交更新。可从具备目标提交的独立仓库导出增量 bundle，在新检出中接收。以下操作仅作用于新工作区及新命名 bundle/ref；先按协作规则确认归属和干净状态。

```bash
# 导出方；target-ref 必须指向已经核实的目标提交。
git -C /absolute/path/export-repository bundle create /new/path/update.bundle \
  cd4463660686079d365705bfd8f37a86c73161d4..target-ref

# 接收方；验证时可通过固定供体取得 bundle 的前置对象。
git -C /absolute/native/path/new-task/source bundle verify /new/path/update.bundle
git -C /absolute/native/path/new-task/source fetch --no-tags --no-auto-gc \
  --no-write-fetch-head /new/path/update.bundle \
  FULL_EXPECTED_COMMIT:refs/heads/imported-task
git -C /absolute/native/path/new-task/source checkout --detach FULL_EXPECTED_COMMIT
git -C /absolute/native/path/new-task/source merge-base --is-ancestor \
  cd4463660686079d365705bfd8f37a86c73161d4 FULL_EXPECTED_COMMIT
```

`FULL_EXPECTED_COMMIT`必须替换成真实完整 SHA，且为 bundle 宣告的提交。导入前后核对 bundle SHA-256，记录最终 HEAD/tree、源码清单、干净状态和新的来源回执，再按具体任务合同验证。最初的 `NATIVE_CHECKOUT_PASS`只证明初始基点准备完成，不自动给后继提交功能、性能或硬件资格。不要改写旧创建状态使它看似验证了新 HEAD；新的证据单独保存。

本轮实际走通了上述接续路径，源工具提交与导入树完全一致；随后文档和证据提交仅交付本次结果。向共享 `zufan` 发布仍须 Issue #2 短暂窗口、最新远端核对和正常快进。

## 实际位置、失败与资源

本机位置是本次运行定位，不是脚本硬编码或新机器前置条件：

| 内容 | 位置 |
| --- | --- |
| 本轮原生根 | `/home/lizufan/riscv-lab/r0-native-store-20261025-1541` |
| 固定供体 | 上述根下 `store/repository.git`，配套 `store/manifest.json`、`store/state.json` |
| 开发工作区 | 上述根下 `development/source` |
| 已验证的后继检出 | 上述根下 `replay-1ude0v7l/checkout/source`；保留该次汇总失败及接续现场 |
| 原始命令与证据 | 上述根下 `evidence/`；最初工具在 `tool/`，与最终交付工具的 SHA 区分 |
| Windows 传输与回执根 | `D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\monitor-r0-native-store-20261025-1541` |
| Windows 临时裸仓 | 同父目录下 `working-r0-native-store-20261025-1541`；它是认证传输中转，仍借用原 Windows 来源对象，不是本轮自包含供体 |

最终测试包含：七层借用来源、脏／未跟踪内容排除、独立 index、独立副本在来源及供体不可用时仍可读、完整／增量 bundle 区分、旧输出和嵌套输出拒绝、源 `.git`／子目录拒绝、缺失提交、shallow/promisor/graft、被移动的 pin/HEAD、manifest／对象损坏和外部 `GIT_*` 污染。工具设置 1～4 个 Git 打包线程，Linux 上同时限制当前进程的 CPU affinity；本轮取 2，未运行构建或 EMU。它不是全机资源调度器，仍须考虑其他 Agent 的占用。

真实操作中的失败分别留证：WSL 无 GitHub 凭据导致只读远端探测失败，改用已有 Windows Git 认证中转；初次 PowerShell 参数数组拼接错误，在核实已完成 clone 后仅继续未完成步骤；文件工具不自动创建父目录，未写入的子目录尝试改用已有目录中的新文件；最终增量接续的汇总代码误将 `stat().st_size` 当函数，所有 Git／消费者命令已经 exit 0，核实终态后只读复核现场并补齐结果，没有重放 commit/fetch/consumer。早期合成破坏测试曾因未先调整临时 Git 对象只读位而失败，修正仅作用于合成夹具；实际供体文件未改权限或内容。失败不计作 PASS，最终合格身份和恢复操作分别记录。

这不是空间清理：新供体分配量实测 360,402,944 B（约 343.7 MiB），首个完整检出分配量 852,656,128 B（约 813.2 MiB）；原目录、Windows 完整 bundle 和后继检查现场继续保留。成本换取后续任务直接引用一个固定供体，不宣称已释放旧目录空间或测得构建／应用加速。

工具拒绝已有输出；失败输出不覆盖、不自动恢复或删除。先核对终态回执和现场，再选择新输出或明确的只读收尾。新供体成功不会解除旧未知操作、冻结输入、失败证据或其他 Agent 的保护。

## 后续边界

R0/native-source-store 子项已闭合，已覆盖的源码准备可以复用。R2-S3 仍需真实消费者的形状、量化、A/x 生命周期和调用序列；R3 已关闭的假设不因此重开。原 B0/H1 缺项、完整新机器安装、子模块／工具来源、人工 ACK、整核功能、应用性能和 ASIC PPA 都不由本结果转授。本轮新增 EMU/NEMU 为 0。
