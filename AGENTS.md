# 团队 Agent 入口

## 本轮交付：T13，目标 zjhwork

用户最新明确指示“上传到 zjhwork 分支”，授权本轮将已验收 T13 提交 `4526d857937def29ea1598a7c878aa539e2ef1f6` 及这次入口说明普通快进推送到 `cc77-builder/riscv` 的 `zjhwork`。本次发布前已确认远端为 T12 基线 `2c0bf8e283d400c1c946ca75f890f266d7758411`，是本地成果的祖先。本节覆盖下方旧任务中的暂不上传、禁止写 zjhwork 等历史限制；不授权写入其他分支或任意后续推送。

本批次只更新文档入口，实际硬件、程序、校验器与证据仍以 T13 报告和固定摘要为准。普通推送成功后需回读远端 SHA；发布操作回执保存在本地 T13 交付目录。下方和归档中“未上传”为当时状态，原字节保留。没有新增人工 ACK；后续优化仍须按既有计划复核。

## 历史阶段：T13 公平周期比较完成时的发布前记录

先读 [T13 报告](team/docs/t13-performance.md)、[测量约定](team/spec/measurement.md) 与 [离线证据](team/evidence/t13-performance-20261015/README.md)。T12 已按用户指示发布到 zjhwork，基线为 `2c0bf8e283d400c1c946ca75f890f266d7758411`；本轮 T13 在独立本地分支 `local/t13-performance-20261015` 完成，用户明确要求做完先不上传 GitHub。没有 Push、PR、main 合并或新的人工 ACK。

本轮 108 次全核功能调用、1,404 个性能窗口及 13 个校准窗口通过；三个全新 EMU 重放逐窗口一致。硬件仅添加观察器，实际 EMU 来源与后续软件/文档提交分开固定。先由队友复核测量合同和离线数据，再按计划 G5 选择一个优化做 A/B。不能把通用调用中 CSR 管理开销产生的最大比值宣传为通用应用收益；PPA、虚拟化、官方语义确认及人工签字未由本轮补齐。

## 历史阶段：T12 自动回归通过时的记录

先读 [T12 报告](team/docs/t12-regression.md) 与 [可离线复核的证据](team/evidence/t12-regression-20261014/README.md)。本轮本地分支 `local/t12-regression` 基于 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`；11 项实际运行满足预期，主机 108 项检查通过。硬件源码、执行软件 SHA 和实际二进制摘要分别列出，不把文档提交当作重新构建。共享分支尚未发布本轮成果；禁止据此虚构 START/RELEASE/ACK 或人工评审。下一项为公平 RVV/vdot 周期对照；T13、PPA、虚拟化和人工签字均未完成。以下保留 T10/T11 历史阶段信息。

## 历史阶段：T10 最小全核接入、T11 固定功能矩阵已验收

先读 [本轮验收与边界](team/docs/t10-t11-acceptance-20261013.md)、[可独立复算的实际证据](team/evidence/t10-t11-fullcore-20261013/README.md) 和 [两线协作约定](team/docs/collaboration-current.md)。固定被测源码 `1bd6f1d9c9485695876ff37a77fbb175a5125983`，其生产 RTL / build.sc 与实际 EMU 来源 `fcb16a8764d342339670df0bbf1bc67ef2028b86` 相同。后续发布提交只增加验收器修复、来源记录与文档。

本轮真实 MinimalConfig 全核 DiffTest 通过 117 个唯一用例（48 定向、32 固定随机、37 精确异常）；8 片仅 D00 重复，124 条 extension 记录，另有56个自检和24个harness预期拒错。vdot 的 bit100真实差分注入在对应 PC/目的寄存器报错；同一镜像换回正常参考库后 shard-0 完整通过。不能把这批功能矩阵当成所有乱序/虚拟化/性能验收。

## 已授权开发与交接

团队唯一上游为 `cc77-builder/riscv`，共享开发目标为 `zufan`；个人 `LiZufan001/riscv` 只是按需快进同步。用户本轮要求完成剩余任务，本轮发布仍须先核对实时远端和无冲突的快进关系。本文不伪造两位成员的 ACK，不创建锁，不授权读到文件即自动开工。最终完整提交 SHA、Push 与双远端回读以实际任务回执为准，不在包含自身的提交中预填。

两人使用独立工作树和输出目录；仅共享远端 Push 按 START → RELEASE → ACK 有序交接。保留既有未提交和未发布成果，不 reset/clean/stash 掩盖他人工作；不强推、不改写历史、不删除 zjhwork，不向 main/James_Hotten/zjhwork 写入。GitHub Actions 完全不依赖，原 workflow 未改。

## T10/T11 时点的后续工作（历史）

优先 T12：需要真实触发与观察的 VL/CSR 紧邻依赖、RAW/WAW、共享 VFEX4 与写回竞争、年轻 vdot 发射后被取消、ROB/FTQ 绕回；随后做公平 RVV 配对周期测量。M/HS/VS 委托与虚拟化尚未验证；综合/STA/功耗、官方规格确认、人工接口签字仍未完成。现有 FU 的 E0/E2/E3/II4 仅是局部握手时序，不是全核指令周期或频率。

原模型、datapath、FU、decode 入口在 `team/scripts/`；每次真实运行用新输出目录。当前 NEMU 补丁为1.1.0及显式平台配置；禁止混用旧参考库、跳过vdot差分或修改黄金结果来消除错误。原Windows WIP目录保留；本轮Linux发布工作区见验收报告，不直接覆盖原开发目录。

旧入口见 [历史快照](team/docs/history/AGENTS-before-t10-closure-20261013.md)，旧阶段报告、测试日志、补丁1.0.0原字节均保留。
