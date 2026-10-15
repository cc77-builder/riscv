# 团队 Agent 入口

## 当前状态：T12 已验收的软件与验证成果完成离线整合

先读 [T12 整合报告](team/docs/t12-zufan-integration-20261014.md)、[本次复核回执](team/evidence/t12-zufan-integration-20261014/README.md)、[原始全核证据](team/evidence/t12-r2-20261014/README.md) 和 [独立审查归档](team/evidence/t12-r2-independent-20261014/README.md)。最终实现来源为 `1ba275411d41b6454b14ecfc537be10cd7202739`；普通 merge 保留已发布审查 `f188f6f7588270714d94d970fe36f2f2cdda15b9` 及本机审查后继 `e5d084bbdcfad6936ccad29dff4c1df00f5abfef` 的完整历史。

既有真实全核运行：original190（源 `a4fea8f69f8c2c58f986858481257d3424a903f0`）与 lean199（源 `8af7b21857ba2c65dbc4d835f7b2152cd6684875`）分别完整通过 DiffTest、GOOD TRAP 和实际 exit0；两个计划输入重叠，不能相加为389个唯一ISA用例。T10/T11历史117唯一用例曾全量通过；此前本轮T12仅重跑15/117，其余102未重跑。本次整合只复核源/镜像/日志并运行主机与参考层检查，新增DUT运行数为0。

生产 `src/`、`build.sc`、`.gitmodules` 和10个gitlink与团队 `6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3`、实际EMU来源 `fcb16a8764d342339670df0bbf1bc67ef2028b86` 一致。黄金NEMU保持已验收1.1.0及固定配置/二进制，不修改时钟、复位、位宽、吞吐率或共享busy/ready合同。保留全部63个计数窗口、失败记录与未启用实验包。

## 本次合入范围与硬件晋升门禁

本次允许合入已验收的软件、判定器、测试、证据和审查文档。旧报告要求“所有STA完成前不得合并zufan”的总闸门已由本次用户明确授权取代，不能用于无限延后这些成果。硬件候选保持独立晋升门禁：输入融合/II3未启用；真实候选RTL A/B、共享门控/OG2/WB/ROB集成、STA/Liberty/PVT/SDC、布局后setup/hold及PPA均未完成，不能写成已通过。

仍未取得年轻vdot已发射后取消、实际ROB/FTQ索引绕回和共享WB碰撞的事件证据；rdcycle流水/序列化未校准，局部E0/E2/E3/II4和原始窗口不能当全核指令延迟、Fmax或官方成绩。官方规格、M/HS/VS委托虚拟化、人工接口签字仍待后续明确任务。本次不启动新RTL优化。

## 发布与协作

团队唯一上游 `cc77-builder/riscv`，目标分支 `zufan`。当前交付只在新的 `publish-zufan/repo` 本地追加提交；最终候选完整SHA、干净状态、bundle及校验值在工作区 `publish-zufan/FINAL.md` / `FINAL.json`。最终联网核实与普通推送由主审ChatGPT负责；本入口不声称已push，不代签任何队友ACK。

保留所有原树/WIP/未跟踪工件，不reset/clean/stash、不强推、不重写历史，不改原PR分支及main/James_Hotten/zjhwork。当前任务禁止联网、安装工具和修改系统/网络/沙箱；不依赖GitHub Actions。既有协作约定见 [collaboration-current.md](team/docs/collaboration-current.md)，行动以用户当次明确授权为准。

当前实现入口：`team/scripts/t12-tests.py`、`verify_t12_evidence.py`、`audit_t12_live.py`、`team/tests/generate_t12.py`。复核输出必须使用全新目录，真实重跑须另获任务授权并固定来源；不得覆盖历史证据或把参考层/主机测试冒充全核。旧入口原字节见 [整合前快照](team/docs/history/AGENTS-before-t12-zufan-integration-20261014.md)。
