# 团队 Agent 入口

## 当前状态：合并候选已发布，局部验收通过

2026-10-13 已复用双亲合并 `a3a7fd7e53924be08ac9a1dabcebb1573caae13c` 和候选 `45bea984445e6f07d0d9c0ee8e42302e225ba0b3`。本机 Codex 独立完成 Git 内容/版本锁审计、主机检查、新组合 RTL 及真实 FU 仿真和代码复核。G-M1/G-M2/G-M3 PASS。用户已明确确认双方无人开发并授权发布，候选 `734353d01e963610ac864fdddd81e01e91f521fe` 已普通快进发布到团队和 Fork 的 `zufan`，两端回读一致。见 [发布记录](team/merge/2026-10-13-zjhwork-into-zufan.publication.md)。下一班仍需针对实际最终 SHA 记录 ACK/START。

先读 [最新独立验收报告](team/merge/2026-10-13-zjhwork-into-zufan.codex-review.md)、[历史执行报告](team/merge/2026-10-13-zjhwork-into-zufan.result.md) 和 [当前协作约定](team/docs/collaboration-current.md)。原 [合并任务单](team/merge/2026-10-13-zjhwork-into-zufan.md) 是编制时方案，其“尚无 FU”等判断以最新固定候选报告为准，不改写历史。

## 两人共享 zufan 的当前规则

- 目标团队仓库为 `cc77-builder/riscv`；zufan 已包含本次合并，后续供两人共享，James_Hotten 为另一活跃线，main 为稳定线。
- 各自独立工作区/输出目录并行开发和验证；共享远端 zufan 只允许真实约定的当班推送者，按 START→RELEASE→ACK 交接。
- 发布前核对当前远端、dirty/untracked、未发布提交和在途任务。普通快进 Push；不强推、不改写历史、不删除 zjhwork、不自动丢弃成员工作。
- 协调记录在团队唯一位置；Fork `LiZufan001/riscv` 仅在团队成功后按需安全快进同步，不是另一套认领状态。
- 不新增、不调用 GitHub Actions。既有上游 workflow 保留，本次没有修改或禁用它们。
- 本次发布窗口依据用户明确确认双方无人开发；没有伪造个人 ACK。读到文档不产生占用锁或自动接管权限。下一位先核对实际 SHA、记录接收和 START；zjhwork 保留用于追溯。

## 复现与后续边界

原脚本为 `check-vdot-model.sh`、`check-vdot-datapath.sh`、`check-vdot-fu.sh`，均在 team/scripts 下；每次使用新的 VDOT_OUT_DIR。新日志见 `team/evidence/merge-review-20261013/`，保留旧 evidence 的日期/SHA/摘要。

当前包含数学模型、组合算术、非流水 FU、研究与协作成果；没有纳入 James_Hotten 第三线。译码/VFEX4、NEMU、全核 DiffTest、CPU 周期性能和 PPA 尚未完成。比赛规格仍是候选合同，局部通过不替代人工接口签字或赛事确认。

本机 Codex 直接使用本机文件和 Git，不依赖 ChatPC。原工作区在 zjhwork 时，用 `git fetch` 加 `git show <已核实团队远程>/zufan:AGENTS.md` 查阅入口，不用 pull 查看文档。按实际任务授权执行，不因读取入口自动启动其他 Agent、创建 Issue 或 Push。
