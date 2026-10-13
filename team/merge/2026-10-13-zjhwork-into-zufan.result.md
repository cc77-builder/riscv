# zjhwork → zufan：本次实际执行报告

> **后续发布更新：** 用户确认双方无人开发并授权发布后，候选 `734353d01e963610ac864fdddd81e01e91f521fe` 已于 2026-10-13 普通快进发布到团队和 Fork zufan，两端回读一致。见 [发布记录](2026-10-13-zjhwork-into-zufan.publication.md)。以下“待交接/未 Push”描述此前验收快照，作为历史保留。

## 2026-10-13 本机续验收：待交接发布

已在固定候选 `45bea984445e6f07d0d9c0ee8e42302e225ba0b3` 上恢复匹配工具链，独立重跑 G-M1/G-M2/G-M3 全部通过；组合 22+10000 组、FU 6 类/71258 周期及全部负控/非法 VLEN 拒绝通过。代码复核完成，真人交接与暂停写入记录仍待取得，**未 Push**。详见 [本机独立验收报告](2026-10-13-zjhwork-into-zufan.codex-review.md)。

以下保留原 ChatGPT 执行报告，描述 12:43 保存候选时的历史状态；其中环境阻塞和待复核不代表本次最新结果。

---

**状态：本地双亲合并与主机检查完成；环境/独立复核阻塞；未 Push。**

本次由用户在当前对话明确授权“开始合并 zjhwork 到 zufan”。执行者为 ChatGPT，经 ChatPC 操作独立 Windows Git 检出，并在 Ubuntu-22.04 WSL2 运行主机检查。未进入或改写成员的原开发工作区，未终止已有 Codex 任务，未使用 GitHub Actions。目标仓库是 `cc77-builder/riscv`，目标分支为 `zufan`。

## 1. 实际输入与提交

首次远端核查：`2026-10-13T12:33:14.8812526+08:00`。正式合并前再次 fetch，确认输入未变。

| 对象 | 完整 SHA |
| --- | --- |
| 原目标 Z：team/zufan | `4a916689e3dfa74680da19653f1df6b8b984edeb` |
| 最新源 S：team/zjhwork | `ffec67e372d80a0588a74a83496434c9f7c086bb` |
| 共同祖先 BASE | `c1ef31d81d50c209bf0e102af8ad7713c2da6dab` |
| 纯双亲合并 M | `a3a7fd7e53924be08ac9a1dabcebb1573caae13c` |
| M 的树 | `17bb1dd1adf572c15625df7ea931b5575051f081` |

M 第一父为 Z、第二父为 S，父数为二；二者均为 M 的祖先。使用 `git merge --no-ff --no-commit --no-autostash`，自动树与 `merge-tree --write-tree` 预览完全一致。没有 squash、rebase、强推、分支删除或手工覆盖生产源码。

原合并计划使用的 S 为 `5227c030...`。实时 S 新增两项提交：`4a6c08bb9` 实现并验证非流水 FU 包装层，`ffec67e37` 规范测试源码文件权限。因此本次候选**不再只有组合算术**，同时保留真实 `VDot` FU、FuType/FuConfig 变更、FU 测试器及其历史证据。没有纳入 James_Hotten 分支的代码。

## 2. 文件、历史和版本保全：通过

目标侧相对共同祖先变化 34 个路径，源侧变化 52 个路径；唯一交集是 `team/README.md`，Git 无文本冲突地保留双方新增内容。其余目标独有 33 个、源独有 51 个路径均逐项比对 Git blob、文件模式，全部与对应来源相同。

所有 10 个 gitlink 及 `.gitmodules`、`team/versions.env` 在 Z/S/M 三者完全一致。原源码、模型、JSONL、manifest、历史日志和哈希文件均未改写。M 后的记录提交只允许本报告、机器摘要和两个入口状态提示，不含生产代码修改。

## 3. 本次实际重跑：通过

执行环境：本机 Ubuntu-22.04 WSL2、Python 3.10.12、Git 2.34.1；创建合并使用 Windows Git 2.53.0。主机审计运行时间为 `2026-10-13T12:38:07.471647+08:00` 至 `2026-10-13T12:38:14.304358+08:00`。

| 检查 | 实际结果 |
| --- | --- |
| `bash team/scripts/check-vdot-model.sh` | 35 项 unittest 通过；5 个生成文件字节一致；exit=0 |
| R1 `check_candidates.py --output ...` | B6/B7 各 262,144 个模型场景及各 4 个极值通过；exit=0 |
| R2 `check_arithmetic.py --output ...` | 65,536 对字节、4,104 组八项输入、160 组长点积通过；exit=0 |
| 分别对 model/datapath/FU 三个脚本执行 `bash -n` | 三次分别通过；不是把后两个文件当作第一个脚本的参数 |
| 新 FU 历史证据与当前源码对应性 | 16/16 项 SHA-256 匹配 |
| 旧组合证据与其原提交 `5227c030...` | 9/9 项摘要匹配 |

旧组合证据与本次树相比是 8/9 匹配，唯一差异为 `build.sc`：源分支新增 `vdotFu` 目标后，其 SHA-256 从 `ec3196b2...` 变成 `db2adeab...`；与新 FU 证据一致。该差异来自已审查的源分支演进，不是合并损坏。没有为了得到“9/9”修改旧摘要。

完整本地审计保留在 `team/out/merge-20261013-current/audit.json`，其 SHA-256 为 `d4f02ecc8071fe883bde84092bab2ee6190ca5a803fc73ce9bca0c26d3204025`。该文件记录最初的 Bash 检查命令；补充的逐脚本检查结果以同目录 `syntax-by-script.log` 为准。主机日志、baseline/arithmetic JSON 均在该输出目录；这些是本地运行文件，不是假定已经上传的 GitHub 附件。

## 4. RTL 复跑：确实尝试，环境阻塞

已在 M 上分别启动原始脚本，使用全新的输出目录，没有修改检查器或降低测试条件：

```bash
VDOT_OUT_DIR="$PWD/team/out/merge-20261013-current/datapath-attempt" BUILD_JOBS=2 bash team/scripts/check-vdot-datapath.sh
VDOT_OUT_DIR="$PWD/team/out/merge-20261013-current/fu-attempt" BUILD_JOBS=2 bash team/scripts/check-vdot-fu.sh
```

两个脚本均在工具检查阶段退出 1，未生成、编译或运行 DUT。实际状态文件分别为：

```text
exit_code=1 end=2026-10-13T12:40:52+08:00
exit_code=1 end=2026-10-13T12:40:53+08:00
```

这台 WSL 没有 JDK/java、Mill、firtool、Verilator、C++ 编译器、make 或 rg；不是队友文档中已配置的 `/home/riscv/riscv-lab/xs-env/XiangShan` 环境。首个 `command -v java` 检查没有返回工具路径。原始脚本没有额外错误正文，不能把环境缺失编造成 DUT 比较失败。

执行入口为 `Local_PC_MCP.powershell_execute`，操作回执 ID 为 `f38700b7c76f0a9d37758ed721fa5972.a2f2afea248a3a6b0cb1e4ad974b4d09`；接口 request ID 未返回。PowerShell 外层成功记录了预期的两个环境退出码，不代表两个 RTL 脚本通过。日志在本地 `team/out/merge-20261013-current/`。

源分支归档的组合 10,022 组和 FU 71,258 周期是**历史结果**。本次已核对相关源码匹配，但不能替代合并候选的全新 RTL 复跑。NEMU、全核 DiffTest、CPU 延迟/吞吐、综合/STA/功耗均未运行；B5 汇编可选项未运行。

## 5. 独立复核、发布与协作状态

| 原门槛 | 本次状态 |
| --- | --- |
| G-M1 历史/内容保全 | 通过 |
| G-M2 主机回归 | 通过；已解释源分支 build.sc 演进 |
| G-M3 新 RTL 生成与真实仿真 | 环境阻塞，未通过；最新源还需额外复跑 FU |
| G-M4 非作者复核与双方接收 | 未完成 |
| Push 团队/个人 Fork | 均未执行 |

检查到 ChatPC 管理的 Codex 正占用唯一并发槽（active=1、max=1）。没有为复核取消别人的任务、提高并发或绕过任务入口，也没有伪造独立批准。另一成员暂停写入确认、未推送成果情况及双方 ACK 尚未取得；本次仅操作隔离候选，不声称占有团队分支锁。

遵循原任务单的“工具缺失时保存候选、标环境阻塞”路径，本次不以单元测试或历史 PASS 宣布完成远端整合。`zjhwork` 保留且没有宣布停用；`main`、`James_Hotten`、已有 workflow 均未变更。个人 Fork 不自动同步。

## 6. 已保留的恢复材料与后续步骤

Windows 独立工作区：`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\merge-zjhwork-20261013`。原始双分支恢复包为同级 `merge-zjhwork-20261013-before.bundle`，已验证完整历史。最终候选与日志将另外保存为同级 candidate bundle 和 evidence ZIP，路径及 C 的实际 SHA 以任务最终回执为准，不在包含自身的提交中自填最终 SHA。

恢复时先读取本报告和最新远端；保留当前 M，不无条件重复 merge。补齐匹配的固定版本工具链及锁定子模块，重跑组合与 FU 两个脚本，取得非作者复核和实际交接。再完成当前分支操作指引切换，核对源/目标未推进，正常 Push 固定最终候选到团队 `zufan` 并复查。若源新增提交，先审增量；任何操作不得覆盖成员未发布工作。
