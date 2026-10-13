# 团队 Agent 入口

## 合并执行进展：仅本地候选，尚未发布

2026-10-13 已按本次用户授权在独立工作区创建双亲合并 `a3a7fd7e53924be08ac9a1dabcebb1573caae13c`，吸收 `zjhwork@ffec67e3` 的数学模型、组合算术和新 FU。内容保全与主机回归已通过；本机 RTL 工具链缺失，独立复核和双方 ACK 尚未完成。**没有 Push，不得将本地候选当作团队分支已合并，也不得自动停用 zjhwork。**

恢复执行先读 [本次实际执行报告](team/merge/2026-10-13-zjhwork-into-zufan.result.md)，核对候选及最新远端，补足原任务单 G-M3/G-M4；不要重复创建同一合并或用旧 RTL PASS 顶替本次复跑。

## 2026-10-13 当前协作约定

- [三人两线协作机制：当前执行约定](team/docs/collaboration-current.md)：独立工作区并行开发，共享远端 `zufan` 同时只允许一名当班推送者，按 START → RELEASE → ACK 交接；普通快进 Push、固定 SHA 验收。
- **不依赖 GitHub Actions** 管理分工、交接、构建或 Fork 同步；上游已有工作流文件保留作参考，不意味着它们被禁用。
- 协调主记录放团队仓库的唯一位置，Issue/Discussion 或 Markdown 任选其一；个人 Fork 只能按需从团队正常快进同步，不能作为第二套实时协调状态。
- 以上是协作规则，不表示当前合并已完成、具体人选已冻结或已有活跃的占用锁；不得仅因读取文档自动接管分支。

## 当前交接：zjhwork 与 zufan 合并

2026-10-13，项目负责人已确认要合并原 `zjhwork`、`zufan` 两条开发线，由两人随后在同一分支错峰工作。**当前交付的是方案，不表示合并已完成。**

收到执行这项合并的任务后，先完整阅读：

- [合并执行任务单：zjhwork → zufan](team/merge/2026-10-13-zjhwork-into-zufan.md)
- [编制时的只读预检及隔离验证](team/merge/2026-10-13-preflight.json)

本方案建议保留团队 `cc77-builder/riscv:zufan` 作为共享开发分支；保留双方历史，暂不删除 `zjhwork`；`main` 和 `James_Hotten` 不在本次合并范围。现有 Issue/交接模板仍是候选机制，不因本文件而自动启用。

不要因读到本文件就自动开始合并、启动其他 Agent、创建 Issue 或 Push。执行仍以当前任务授权为准。操作前重新获取团队远端，保护现有未提交修改和仍在运行的任务；个人 Fork 的旧 `zjhwork` 不能代替团队源分支。

原工作区还在 `zjhwork` 时，可先 `git fetch`，再用 `git show <已核实的团队远程>/zufan:AGENTS.md` 读取入口；**不要用 `git pull <团队远程> zufan` 当作查看文档的方法**，那可能直接开始把目标合入当前分支。

本机 Codex 直接操作本机文件和 Git；ChatPC 是 ChatGPT 访问本机的入口，不是 Codex 的文件访问依赖。比赛规格仍是候选合同；组合 RTL/主机测试通过不等于全核、NEMU、DiffTest 或性能验收通过。
