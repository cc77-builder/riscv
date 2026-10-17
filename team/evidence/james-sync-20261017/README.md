# James_Hotten 分支同步复核（2026-10-17）

基点 7ff3a3e88，来源 zjhwork2@a877e0575（包含 zjhwork@3d051f0d8）。
本目录仅新增复核回执，不修改来源归档；全部历史硬件复算均不是新 DUT 运行。

- host-tests.log：186 项集成主机测试，Python -OO。
- o0-tests.log：79 项诊断/归档门禁测试；o0-trace.json 为完整旧 pilot 硬件流重放。
- unified-tests-v3.log：10 项新增测试通过。首次测试框架错误（类属性 run 遮蔽 unittest.run）在 unified-tests.log 中保留，修复不改变被测规则。
- T13 23 项及 T15 模型 11 项测试也在本轮执行通过，原终端输出未另行归档。
- t15-replay.json：独立 s8x8/s16x8 RTL 记录重算、八项参数拒绝，不是全核 SEW16。
- unified-replay.json：加固后检查器重验 64 镜像 / 860 窗口、所有逐运行及 suite 样本与封存记录一致；439 文件原字节核对。完整解包与复算驱动 recheck-unified.py 保留，运行前从仓库根将它复制到一个新的 team/out 作业目录并调整 OUT；不可向本目录输出。
- t14-offline-receipt.json：用 a877e0575 的冻结源码重新计算历史 13 校准窗口 / 126 运行 / 1404 性能窗口，结构与成对数据通过。t14-frozen.py 记录提取源码、执行与固定版本。其缓存/输出路径是本次记录，复跑须另选未存在目录。
- t14-current-control.json：当前集成检查器独立接受两种模式的控制日志，保留新旧 counts 差异。t14-replay.log / t14-compat.log 保存直接使用集成工具遇到的派生计数/旧校准构建绑定拒绝；没有修改旧结果或放松校验。
- o0-parser-compat.json：新旧事件解析与 FU 时钟映射 AST 完全一致；新解析器保留 James 的 ROB 取消修复。当前分析器/适配器继续固定源 blob。

309 个测试方法（186+23+11+79+10）与历史复算不等于新集成硬件验收。
来源归档、失败记录和本次输入/工具摘要分别保存。封存后不改写本目录。
