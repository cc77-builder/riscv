# 合并执行任务单：zjhwork → zufan

编制：2026-10-13，Asia/Shanghai。目标仓库：`cc77-builder/riscv`。

**当前状态：方案已编制，实际分支合并待执行。** 队友 Agent 收到“执行本计划”的任务后按检查点推进；读到文档不等于获得新的执行授权。本任务不要求再做文献调研，也不要求先完成尚不存在的全核指令。

## 0. 背景、目标与边界

项目负责人已确认：原 `zjhwork` 与 `zufan` 两条开发线要合并，随后两人同分支错峰开发。推荐保留已有研究成果所在的 **团队 `zufan`**，把团队最新 `zjhwork` 合入；另一个活跃开发分支仍为 `James_Hotten`，`main` 暂作为稳定线另计。这是本次方向建议，不把分支名强行解释为真人姓名或固定专业分工。若团队另行指定保留名，先修改目标，不自行反向合并或重命名。

目标：**双方提交可追溯、代码/数据不丢失、现有局部测试能复现、当前入口与进度一致、下一班能接手。** 不在合并中扩流水、改 ISA、改 NEMU、升级工具链或实现性能优化。

| 允许事项 | 不在本次范围 |
|---|---|
| 最新两条团队分支的正常合并，必要的入口/协作说明更新，新验收记录 | 向 `main` 或 `James_Hotten` Push，合并第三条开发线 |
| 隔离本地检出、临时本地合并提交、既有测试 | 删除/重命名远端分支、强推、重写成员历史、公开代码 |
| 双方暂停写入后，由一名集成人推进 `zufan` | 伪造在岗 Issue、擅自启用机器人、锁服务或分支权限变更 |

`zjhwork` 先保留原引用；完成验收和成员接收后仅约定停止继续 Push，不自动删除。个人 Fork 同步也不是本次团队 Push 的自动附带操作。

## 1. 编制时核实的快照

执行时重新 fetch，不能把这些 SHA 当作明天仍然最新的合并源。

| 团队引用 | 编制时 SHA | 相对共同祖先 |
|---|---|---|
| `zufan` | `76bc6f7a5ea0264f02820868cd62cddead53b2f7` | 5 个独有提交、29 个新增研究文件 |
| `zjhwork` | `5227c030fdae9b6087fd995a00a3535b15f6aefc` | 3 个独有提交、33 个变化路径 |
| 共同祖先 / `main` | `c1ef31d81d50c209bf0e102af8ad7713c2da6dab` | 两边从此分叉 |
| `James_Hotten`（不纳入） | `a978b3b8fe731dd9422a41f80d9d53e40c775656` | 只记录、不改动 |

zjhwork 三个独有提交依次为 `720dd3d668929123b8ab35e947c67f68ef595c65`（模型/数据）、`ec7c2a4cc762fc6f616a9ebdb5ec0e37ea7187bf`（接口）、`5227c030fdae9b6087fd995a00a3535b15f6aefc`（组合算术）。个人 Fork 的源分支上次只到 `720dd3d`，不得代替团队源。

双方变化路径交集为 0。Git 2.53.0.windows.3 的 `merge-tree --write-tree` 返回 0，预览树为 `10445e0ac8a7df05a9fab4389704ca9c2494a51a`。**这是加入本方案前的预览树，不是合并提交。** 本方案发布后，zufan 的提交数/变化路径数/预览树都会变化，不应机械要求仍为 5:3、29:33。

已将预览树的 team、build.sc 和组合算术源码导出至隔离临时目录，真实运行：9 项历史源码摘要匹配；35 个模型 unittest 通过，5 个生成文件一致；B6/B7 主机检查各 262,144 例及极值通过；R2 算术的 65,536 对字节、4,104 组八项输入、160 个长点积检查通过。详见 [预检记录](2026-10-13-preflight.json)。**本次编制没有运行 Verilator、NEMU、全核或 PPA，也没有移动两条待合并分支。**

## 2. 合并策略与内容保全

采用正常双亲 **merge commit**，不 squash、cherry-pick、rebase，也不复制文件冒充合并。原提交已有共享历史和测试出处，保留原 SHA 最容易核查成果完整性。[G1]

拆成两个可审查提交：**M 是纯合并**，第一父为执行时固定的目标 Z，第二父为源 S；**D 是当前入口与验收记录**，只改文档，不改生产源码、数据和历史研究/证据。最终候选 C 通常等于 D，测试与评审完成后再发布。不要把代码归并、方案优化和组织迁移揉成一次不可解释的大修改。

| 内容 | 合并要求 |
|---|---|
| `team/models/vdot/**`、`check-vdot-model.sh` | 保留 zjhwork 的独立模型、数据和 manifest，禁止为消除失败重写黄金数据 |
| `VDotDatapath.scala`、`team/rtl/vdot/**`、`check-vdot-datapath.sh` | 保留组合算术及测试器，不顺手加入时钟、流水、新 FU |
| 根 `build.sc` | 保留独立 `vdotDatapath` 目标，不覆盖其他目标、不升级依赖 |
| `team/spec/vdot.md`、`team/spec/rtl-interface.md` | 保留合同、接口草案及未完成标记，不改成“官方确认” |
| `team/research/2026-10-12-vdot-review/**`、`2026-10-13-vdot-round2/**` | 保留 zufan 的研究、候选汇编、实验和历史结论 |
| 已有 `team/evidence/**` | 原样保留；旧日期/分支/SHA 是历史事实，不批量替换 |
| `.gitmodules`、全部 mode=160000 的 gitlink、`team/versions.env` | 编制时双方一致，本次不得静默改变锁定版本 |
| 根 `AGENTS.md`、本方案和预检 | 保留为可追溯入口 |

### 必须避免的语义误读

合并后本次引入的正式 RTL 仍只有无时钟组合 `VDotDatapath`。VFEX4、单请求 FSM、2 周期结果 valid / 3 周期最早响应握手 / 4 周期最小启动间隔，是 zjhwork 接口文档中的设计口径，不是实测。研究 H1/H2、II=1 同样是候选，不在本次替换实现。

另一条 `James_Hotten` 中的 `VdotExec`、NEMU 补丁或 RVV harness **不会自动出现**。不能因为研究引用了它们就声称合并后已具有这些组件，也不能按名字相似删除独立实现。后续整合第三条线另立任务。

共享分支现有内容包含实际 RTL，不把旧 H/SV 抽象机械解释成“zufan 只能写软件”。三人的模块责任和当班推送权分开记录；本任务不指定未经确认的真人分工。

## 3. 前置交接与工作区

两位开发者先明确集成人、双方未推送成果的处理方式、各自最新 SHA、仍在运行的 Codex/构建任务。在本次来源固定至发布/交接完成期间，不再推进这两个远端分支。另一位可对固定快照评审/测试，但不改集成工作树。

载体可以是现有沟通、任务卡或 Issue，**不强制新建 Issue**。最低记录：集成人、任务、Z/S、实际开始时间、在途任务、暂停写入确认。Git 不检查谁当班，预计结束时间也不是自动抢占许可。

现有工作区先查 dirty/untracked、本地未发布提交、子模块及外部 NEMU 状态，保全它们。禁止自动 stash、reset --hard、clean -fdx、终止他人任务或直接在脏目录 pull。无法确认还有没有写入者时，先停止会改变远端的阶段。

下面命令供 **Ubuntu 22.04 / WSL2 的 Bash** 按阶段执行，不是 PowerShell 语法。Agent 自行核实已有 Linux 环境，优先新建独立 clone；不要把多人共享分支误做成共享目录/索引。带复杂子模块的 worktree 有使用限制，本任务不依赖它。[G2]

## 4. 编号步骤：准备 → 合并 → 验证 → Commit/Push → 交接

### 4.1 独立检出与来源固定

以下命令在同一 Bash 会话内执行；换终端先从记录恢复变量并复核。

```bash
set -euo pipefail
umask 077
TEAM_URL='https://github.com/cc77-builder/riscv.git'
RUN="$(mktemp -d "${HOME}/riscv-merge-XXXXXXXX")"
REPO="$RUN/repo"
git clone --no-checkout --no-tags --origin team "$TEAM_URL" "$REPO"
cd "$REPO"
git config core.autocrlf false  # 仅新 clone；保持 manifest 的 LF 字节
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
git --version
git remote get-url team
git remote get-url --push team
```

URL 必须确实指向团队库，不按 origin/team 的名字猜。身份缺失时只在新 clone 配置真实执行者身份；不改全局，不冒用其他成员，也不虚构人工签字。

```bash
git fetch --no-tags team \
  refs/heads/zufan:refs/remotes/team/zufan \
  refs/heads/zjhwork:refs/remotes/team/zjhwork
Z="$(git rev-parse refs/remotes/team/zufan)"
S="$(git rev-parse refs/remotes/team/zjhwork)"
mapfile -t BASES < <(git merge-base --all "$Z" "$S")
test "${#BASES[@]}" -eq 1
BASE="${BASES[0]}"
printf 'Z=%s\nS=%s\nBASE=%s\n' "$Z" "$S" "$BASE" | tee "$RUN/inputs.txt"
date -Is | tee "$RUN/started-at.txt"
git ls-remote --heads "$TEAM_URL" > "$RUN/remote-heads.before.txt"
git log --left-right --oneline "$Z...$S" | tee "$RUN/unique-commits.txt"
git -c core.quotepath=false diff --name-status "$BASE" "$Z" > "$RUN/zufan-paths.txt"
git -c core.quotepath=false diff --name-status "$BASE" "$S" > "$RUN/zjhwork-paths.txt"
git bundle create "$RUN/before-merge.bundle" refs/remotes/team/zufan refs/remotes/team/zjhwork
git bundle verify "$RUN/before-merge.bundle"
```

bundle 在仓库外，仅作恢复材料，不上传。无需新建第三条远端开发/备份分支。核对 Z/S 是否仍是编制快照的后继；新增方案文档可审查纳入，S 的新增生产修改必须补充范围与测试。遇历史重写、多个 merge-base、不相干历史、不明第三线改动，停止自动流程。

若 `git merge-base --is-ancestor "$S" "$Z"` 已成功，先检查是否另一 Agent 已合并，或曾经 revert。走“核验现状/补交接”路径，不重复合并；**祖先关系不能证明被撤销的代码还在**。

### 4.2 树级预演

```bash
if git merge-tree --write-tree "$Z" "$S" > "$RUN/merge-preview.txt"; then
  PREVIEW="$(head -n 1 "$RUN/merge-preview.txt")"
else
  rc=$?
  printf 'merge-tree stopped: exit=%s; see %s\n' "$rc" "$RUN/merge-preview.txt"
  exit "$rc"
fi
```

该命令计算 Git 对象，不改变工作树/索引/分支；0 为无文本冲突，1 为冲突，其他值为命令错误。[G3] 不支持该子命令时报告版本，可在全新隔离 clone 中受控预合并，不在原工作区试错。存在冲突按第 5 节处理，不用 `-X ours/theirs` 或 `-s ours` 全局择边。

### 4.3 纯合并提交 M

```bash
git switch --detach "$Z"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
git merge --no-ff --no-commit --no-autostash "$S"
test -z "$(git diff --name-only --diff-filter=U)"
git diff --cached --check
test "$(git write-tree)" = "$PREVIEW"  # 仅自动无冲突路径
git diff --cached --stat
git commit -m 'merge: integrate zjhwork into shared zufan development line'
M="$(git rev-parse HEAD)"
test "$(git rev-parse "$M^1")" = "$Z"
test "$(git rev-parse "$M^2")" = "$S"
test "$(git rev-list --parents -n 1 "$M" | wc -w)" -eq 3
git merge-base --is-ancestor "$Z" "$M"
git merge-base --is-ancestor "$S" "$M"
printf 'M=%s\n' "$M" | tee "$RUN/merge-commit.txt"
```

`--no-ff --no-commit` 为提交前检查保留停点；单独 no-commit 不能阻止 fast-forward 移动引用。[G1] 不跳过已有 hooks。detached HEAD 避免移动操作者原本的本地开发分支；稍后按固定 C 推送目标。

在仍无交集的快照中，所有变化路径必须分别与原侧保持相同：

```bash
mapfile -d '' -t Z_PATHS < <(git diff --name-only -z "$BASE" "$Z")
mapfile -d '' -t S_PATHS < <(git diff --name-only -z "$BASE" "$S")
if ((${#Z_PATHS[@]})); then git diff --exit-code "$Z" "$M" -- "${Z_PATHS[@]}"; fi
if ((${#S_PATHS[@]})); then git diff --exit-code "$S" "$M" -- "${S_PATHS[@]}"; fi
git diff --exit-code "$Z" "$M" -- .gitmodules team/versions.env
```

NUL 分隔用于正确处理中文/空格文件名。另用 `git ls-tree -r` 比较**所有** mode=160000 条目，不只列几个记得的子模块。若执行时已有共同改动，则严格逐侧相等仅检查独有路径，交集单列三方解决证据；不能为了通过验证删掉检查或覆盖其中一侧。

### 4.4 当前入口整理 D（不修改历史）

在 M 上只做下表必要调整：

| 允许文档 | 当前入口需更新内容 |
|---|---|
| `team/README.md` | 加研究/合并入口；写清组合 RTL 已有、FU/全核未完成；开发目标为共享 zufan |
| `team/models/vdot/README.md` | 修改今后的 clone/开发分支指引；保留最初 T05 在 zjhwork 的历史 |
| `team/rtl/vdot/README.md` | 当前复现 switch 改为 zufan；保留原测试分支及历史事实 |
| `team/香山vdot赛题_三人分工与Git协作.md` | 顶部补日期明确的现行约定；旧按任务建分支示例标为历史方案，不重写赛规 |
| 根 `AGENTS.md` | 根据真实验收状态更新待执行标记，链接新报告 |
| `team/merge/2026-10-13-zjhwork-into-zufan.result.md`（新建） | 输入、M、测试、阻塞和交接，见第 8 节 |

旧研究 README/STATUS 中“当时未推送团队”、旧 SHA/日期是历史记录，不追改。通过当前入口说明后续已发生的事情即可。manifest、JSONL、source.sha256 和历史日志不改。`team/spec/vdot.md` 的原链接调整随 M 纳入，本次 D 不改 opcode、合法域、位宽、结果布局或未冻结状态。

逐个暂存已审查的路径，不用 `git add -A` 把环境文件/大输出带入。需要超出表格时先交代具体原因与范围，不顺手实现 FU、合并另一模型或修改公共配置。

### 4.5 测试与真实验收

在最终候选工作树运行，另建输出目录，禁止覆盖历史证据：

```bash
OUT="$REPO/team/out/merge-$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$OUT"
set -o pipefail
sha256sum -c team/evidence/rtl-datapath-20261012/source.sha256 \
  2>&1 | tee "$OUT/source-hashes.log"
bash team/scripts/check-vdot-model.sh 2>&1 | tee "$OUT/model.log"
python3 -B team/research/2026-10-12-vdot-review/experiments/check_candidates.py \
  --output "$OUT/baseline-host.json" 2>&1 | tee "$OUT/baseline-host.log"
python3 -B team/research/2026-10-13-vdot-round2/experiments/check_arithmetic.py \
  --output "$OUT/arithmetic.json" 2>&1 | tee "$OUT/arithmetic.log"
```

必须保留 pipefail；不能只读取 tee 返回值。Python 不用 `-O`，否则 assert 可能被禁用。数据检查失败时不要运行重生成覆盖命令消除差异。

| 门槛 | 必须获得的证据 | 含义 |
|---|---|---|
| G-M1 历史/内容 | Z/S 祖先和 M 父顺序正确，独有路径/模式/gitlink 保全 | Git 及文件完整性 |
| G-M2 主机回归 | 9 源摘要、35 unittest、5 文件一致性，B6/B7 与 R2 host 检查通过 | 模型/数据，不是 ISA |
| G-M3 真实组合 RTL | 合并后的生产源码重新生成、Verilator 编译，22+10,000 组完整比较，bit0/127 负控按预期拒错 | 组合 DUT，不是 FU/全核 |
| G-M4 独立交接 | 另一成员/Agent 在独立检出复核固定最终候选 C，当前入口明确，两人接收记录 | 非作者复现与协作 |

G-M3 不要求编译完整 SoC。独立 `vdotDatapath` 仍依赖根 build.sc 所引用的子模块构建定义，因此只在**新 clone** 初始化它的锁定子模块：

```bash
# 先核对新 clone 的 .gitmodules/gitlink；不使用 --remote。
git submodule update --init --recursive --jobs 1
# JAVA_HOME / CHISEL_FIRTOOL_PATH 使用已有匹配配置，先核对版本。
VDOT_OUT_DIR="$OUT/rtl" BUILD_JOBS=2 \
  bash team/scripts/check-vdot-datapath.sh
cat "$OUT/rtl/check.status"
```

默认并发 2 延续现有脚本保守设置，实际资源不足可以调低。不要为组合测试运行完整 `stage1.sh emu`，也不要调用 `prepare-dependencies.sh` 改写已有 xs-env/NEMU 等外部检出。本次不需要更新这些外部源码。子模块/工具缺失时明确报告缺项，不换默认最新版本凑环境，不降低门槛后宣称通过。

G-M3 要有 `VDOT_DATAPATH_PASS ... total=10022`、两条 `FAULT_DETECTION_PASS`、`VDOT_DATAPATH_CHECK_PASS`，且 check.status 的 exit_code=0。如果最新 S 已扩充测试，应实际运行新增集合并解释计数变化，不能只认固定 10022。

B5 汇编是可选补充，源码未改且历史证据完整时，缺 Clang 不阻塞此次迁移；未运行明确写未运行：

```bash
python3 -B team/research/2026-10-13-vdot-round2/experiments/check_assembly.py \
  --output "$OUT/assembly.json" --symbols-output "$OUT/assembly-symbols.txt"
```

**NEMU、全核 DiffTest、处理器周期/吞吐、综合/STA/功耗不是本次已经完成的项目。** 它们是后续工作，不能要求先做完才整理分支，也不能用 G-M1～M4 替代这些验收。

保存必要小日志、输入/源摘要和工具版本到新结果记录；波形、生成 SV/C++、obj_dir、bundle 不入 Git。D 的最后修改仅限入口和报告；提交后重查摘要/核心模型，确认没有代码变化。独立验收必须绑定最终 C，不能只评 M 就批准后来不同的源码。

### 4.6 Commit、独立核验、普通 Push

```bash
# 先仅 add 4.4 中实际修改且已审查的路径。
git diff --cached --check
git diff --cached --stat
git commit -m 'docs(team): activate shared zufan workflow and record merge acceptance'
C="$(git rev-parse HEAD)"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
git merge-base --is-ancestor "$M" "$C"
git merge-base --is-ancestor "$Z" "$C"
git merge-base --is-ancestor "$S" "$C"
git diff --name-status "$M" "$C"  # 只允许入口/新验收记录
```

另一位成员在独立检出验收 C，可用本地 bundle 传递而不新增长期远端分支。至少复核内容保全、运行模型/摘要、核查 RTL 日志的 DUT/版本/输入/退出码；不要求再重复整场全核编译。没有独立复核时标“待 G-M4”，不虚构批准。默认完成复核后再发布；如团队明确允许先提交已过 G-M1～M3 的开发候选，须记录该授权和待复核状态，仍不得归档旧分支或宣布交接完成。

发布前重新检查冻结来源：

```bash
git fetch --no-tags team \
  refs/heads/zufan:refs/remotes/team/zufan \
  refs/heads/zjhwork:refs/remotes/team/zjhwork
test "$(git rev-parse team/zufan)" = "$Z"
test "$(git rev-parse team/zjhwork)" = "$S"
git push team "$C:refs/heads/zufan"
REMOTE_C="$(git ls-remote --heads "$TEAM_URL" refs/heads/zufan | awk '{print $1}')"
REMOTE_S="$(git ls-remote --heads "$TEAM_URL" refs/heads/zjhwork | awk '{print $1}')"
test "$REMOTE_C" = "$C"
test "$REMOTE_S" = "$S"
git ls-remote --heads "$TEAM_URL" > "$RUN/remote-heads.after.txt"
printf 'VERIFIED team/zufan=%s source=%s\n' "$REMOTE_C" "$REMOTE_S"
```

只推一个 ref，使用固定 C，不用可能被另一进程改变的含糊 HEAD。保护策略拒绝时保留真实错误，走获准的 PR 流程，不关闭保护/换凭据绕过。临时 PR 分支须另有明确允许，不默认增设活跃开发线。

上述两次读取不是跨两个引用的原子锁。目标/源变化时重新 fetch 审查，不强推、不无界重试。发布后源已推进：C 包含原 S，但不能称吸收最新源；暂停归档，另做增量审查/合并/验收。目标已推进到 C 的后继：核对是合法队友提交，不能把它覆盖回 C。

Push 响应丢失或超时时先查远端是否已有 C，不能盲目重放。远端等于 C 记成功；是其已核实后继则记“成功后已有更新”；否则记未确认。main/James_Hotten 若期间被别人推进，只记录外部变化，不回写旧 SHA。个人 Fork 不自动同步。

### 4.7 两人切换与旧分支停用

各人独立更新本地检出。仅对干净且没有未发布提交的工作区：核对团队远程，fetch，切换/创建跟踪团队 zufan 的本地分支，再 `git merge --ff-only <团队远程>/zufan`。不要在仍有私有工作的 zjhwork 目录直接 pull 目标。

有 dirty、额外本地提交或仍在运行 Agent 时，先保全并列差异，再单独迁移，不为统一分支丢弃工作。双方回复实际检出 C 或已审查后继、测试状态、下一任务后，旧 zjhwork 约定停用但保留引用。删除/重命名留待另行确认。

共享线继续分开记录工作包负责人、当前执行者、推送者和评审 SHA。Issue/Discussion/已有任务记录任选一个团队主记录，不同时维护多份占用状态；不把个人 Fork 的 Issue 当作团队分支锁。原 zjhwork 的硬件工作与 zufan 的研究/验证工作都保留，具体分配按模块与能力认领。

## 5. 冲突、变化和阻塞的处理

| 情况 | 处理方式 |
|---|---|
| 路径仍不重叠 | 自动树 + 逐侧保全，不人工复制覆盖 |
| 仅当前文档冲突 | 保留双方新增内容，集中 D 处理，逐处记录理由 |
| RTL/build.sc/模型/manifest/版本锁冲突 | 停止自动择边，列 base/Z/S 与语义影响，负责人确认后重测 |
| 新 S 包含全核、NEMU、第三线成果 | 重新审查本次范围/验收，不能套组合模块计划 |
| 模型/摘要失败 | 保存首错，不改期望，不用旧 PASS 顶替 |
| 工具/依赖缺失 | 保存候选、缺项、命令，状态为环境阻塞，不报 RTL 通过 |
| 来源/目标被重写或不明推进 | 保留候选，重新 fetch 比较，不强推、不重写共享历史 |

Git 无冲突不等于文档一致。特别检查：README 仍要求往旧 zjhwork 推送；研究引用的第三线组件实际并未纳入；把性能目标写成实测。它们都要在当前入口中澄清。

## 6. 回退和中断恢复

**M 未提交：** 在干净的隔离 clone 用 `git merge --abort`，核验 HEAD 回到 Z。原先有未提交修改时 abort 不保证完整还原，因此不在原开发目录试合并。[G1]

**M/D 已提交但未 Push：** 保存候选 SHA、bundle、日志，必要时另开隔离检出重新开始，不 reset 团队/队友工作区。下一次先查远端是否已完成，避免重复操作。

**已经 Push：** 优先修复前进；获得明确回退授权后，在团队当前 head 审查并 `git revert -m 1 <M>` 生成新撤销提交，不强制退回 Z。这里 mainline=1 只因已核实 M 第一父是原 zufan，不能对任意 merge 机械套用。D 的“已整合”入口也要修正，并检查后续提交对 M 的依赖。[G4]

revert 不抹去合并历史，再 merge 相同 S 通常不会恢复被撤销内容；重新引入要审查撤销的撤销或新修复提交，不能重复 merge 后误报已恢复。[G4]

中断恢复先核验 Z/S/C、M 父提交、工作树、在途任务、日志状态与实际时间。预计下班时间不是锁到期，旧 PASS 不证明最新候选通过。

## 7. 完成标准与后续任务边界

可写：**“指定 zjhwork/zufan 快照已保留历史整合至团队 zufan；局部模型与组合 RTL 复现通过；已完成独立复核及两人交接。”** 缺哪项就明确留在对应阶段。

不能写“vdot 全核完成”“已通过 NEMU/DiffTest”“H1 更快”“Git 已强制保证两人互斥”。下一批才是包装层/全核接入、强 RVV 目标验证、与 James_Hotten 成果去重协同等任务，不能借合并顺手实施。

## 8. 执行报告模板

执行时新建 `team/merge/2026-10-13-zjhwork-into-zufan.result.md`；不要提前生成假成功报告。

```text
实际开始/结束（带时区）：
执行者、独立验收者、当前任务授权：
团队仓库/目标分支，暂停写入确认，在途任务：
输入 Z / S / BASE；M 与两父提交；被测源码/树摘要：
路径交集、人工解决、生产/数据/模式/gitlink 保全：
命令、版本、退出码、源摘要：
35 unittest / 5 文件一致性 / B6-B7 / R2 host：
组合 RTL 的 DUT、源码摘要、22+10000、两项负控、退出码、日志：
汇编可选项：通过/失败/未运行：
明确未运行的 NEMU/全核/PPA 等：
当前文档改动，旧证据保留，独立验收对象和剩余问题：
Push 与远端复查，失败的真实错误/时间/请求 ID（未返回则明示）：
两人 ACK、下一工作包、仍在运行任务与交接边界：
```

报告不自填包含自身内容的最终提交 SHA；记录 M 和被测源码摘要，提交后在最终回执给出 C。必要小日志可归档，重复的大型输出不入 Git。复核/ACK 可放在团队既有记录中并引用，不新造锁服务。

## 9. 参考与证据边界

- [G1 Git merge](https://git-scm.com/docs/git-merge)：双亲合并、no-ff/no-commit、干净工作区与 abort。
- [G2 Git worktree](https://git-scm.com/docs/git-worktree)：独立检出及子模块限制；本任务优先 clone。
- [G3 Git merge-tree](https://git-scm.com/docs/git-merge-tree)：树级预演及退出状态。
- [G4 Git revert](https://git-scm.com/docs/git-revert)：主线选择、撤销对后续合并的影响。

项目事实以固定团队快照和 [预检记录](2026-10-13-preflight.json) 为据。Git 官方说明只支持命令语义，不证明本项目功能或性能。执行当天仍须复核最新状态。
