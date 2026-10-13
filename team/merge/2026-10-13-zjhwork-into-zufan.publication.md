# zjhwork → zufan：发布完成记录

2026-10-13，Asia/Shanghai。状态：**已完成合并发布，团队与个人 Fork 回读一致**。

## 1. 真实授权与发布结果

用户在当前对话明确确认：“我确定双方无人在开发，你可以合并了”。本次以该用户协调确认补齐发布窗口，并依照已有正常发布授权执行。没有生成其他成员的个人 ACK，也没有声称核查过队友电脑中未提交文件；本次只发布已经固定和验收的候选。

| 对象 | 发布前 | 本次成功发布并回读 |
| --- | --- | --- |
| 团队 cc77-builder/riscv:zufan | `4a916689e3dfa74680da19653f1df6b8b984edeb` | `734353d01e963610ac864fdddd81e01e91f521fe` |
| Fork LiZufan001/riscv:zufan | `4a916689e3dfa74680da19653f1df6b8b984edeb` | `734353d01e963610ac864fdddd81e01e91f521fe` |
| 团队 zjhwork | `ffec67e372d80a0588a74a83496434c9f7c086bb` | 保留原引用，未推送或删除 |

团队 Push：`exit_code=0 time=2026-10-13T15:44:00.5919629+08:00`。Fork Push：`exit_code=0 time=2026-10-13T15:44:26.9924524+08:00`。两次均为普通快进 Push，使用完整固定 SHA 和显式 `refs/heads/zufan`。团队成功并回读后才同步 Fork。发布前 fetch 确认 Z/S 未变，工作树干净，开放 PR=0，祖先关系与 diff --check 通过。

本文件属于**发布成功后的独立文档提交**，记录已经发生的 F 发布；文档提交自身的最终 SHA、随后推送结果和完整远端回读放在项目根 `publication-20261013/final-receipt.md/json`，不在包含自身的提交中预测结果。新文档提交必须再次核对远端及范围后正常快进发布。

## 2. 验收与历史保全

M=`a3a7fd7e53924be08ac9a1dabcebb1573caae13c`，第一父 Z=`4a916689e3dfa74680da19653f1df6b8b984edeb`，第二父 S=`ffec67e372d80a0588a74a83496434c9f7c086bb`；实际被测 C=`45bea984445e6f07d0d9c0ee8e42302e225ba0b3`，证据提交 E=`03c357cdecb380fcbe9a723ec16ddb45e85ab710`，首次发布 F 如上。所有提交保留，没有重新创建合并、rebase、squash 或强推。

G-M1/G-M2/G-M3 已通过，详见 [固定候选的完整验收报告](2026-10-13-zjhwork-into-zufan.codex-review.md) 和 [新测试证据](../evidence/merge-review-20261013/)。35 项模型单测、5 文件一致性、B6/B7、R2，以及组合 RTL 22+10000 组、真实 FU 6 类/71258 周期、全部负控与 VLEN 拒绝已真实完成。独立复核覆盖 ready/valid、身份、反压、异常、flush/reset、事务守恒。

发布续办只改当前文档状态，生产源码、黄金数据、原测试脚本、10 个 gitlink、版本锁和旧 evidence 不变，因此保留原固定源码的有效验收，不宣称本次重新执行 RTL。没有调用或新增 GitHub Actions。未更新 main/James_Hotten/zjhwork。

## 3. 下一班接手

两人后续使用独立工作区在团队共享 `zufan` 开发，读取 [当前协作约定](../docs/collaboration-current.md)。下一位先 fetch，核对最终完整 SHA，保全自己未提交/未推送工作，再记录真实 ACK 和 START。发布任务完成后，本执行者不继续占有推送窗口；此次确认不能替代下一班实际接收。

原 zjhwork 引用继续保留用于追溯。后续开发使用共享 zufan；若发现未发布旧线成果，先在独立工作区比对并协调，不能覆盖或强推。

全核译码/VFEX4、NEMU、DiffTest、CPU 性能和 PPA 仍未完成。局部 FU 通过与本次 Git 发布不表示这些项目已经验收。
