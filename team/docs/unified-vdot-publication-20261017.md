# 四项目统一测试：zjhwork 交付记录

日期：2026-10-17（Asia/Shanghai）。任务编号：`UNIFIED-VDOT-20261017`。

用户要求“上传github到zjhwork分支，留个记录”。本次将统一测试程序、实际结果与必要证据交付至 [cc77-builder/riscv:zjhwork](https://github.com/cc77-builder/riscv/tree/zjhwork)。这是T15后增加的横向比较记录。

## 解决的问题与结果

公开项目使用不同工作量、基线和统计方式，原有比值不能直接横比。本轮将四个实现接入同一香山16ae基础版本，固定MinimalConfig、单核、VLEN128、dot8/full128契约、内核与数据布局、共同RVV算法和统计规则，实际跑完64个全核镜像、860个窗口，其中384个正式性能样本。

| 实现 | 单次 | 依赖链256 | 四路×32 | 加载/计算/存储64 |
|---|---:|---:|---:|---:|
| 本项目T14 INT8 | 1.201× | 2.930× | 1.496× | 1.005× |
| Jade | 1.218× | 3.398× | 2.605× | 1.006× |
| 试水 | 1.201× | 2.930× | 2.322× | 1.005× |
| Redoop＋dot8适配 | 0.953× | 1.481× | 0.929× | 0.981× |

每行采用该实现上实测的共同RVV周期总和÷自定义实现周期总和，三组数据、每组四轮正式测量；不扣空循环。绝对周期、范围和逐样本数据见 [完整报告](unified-vdot-comparison-20261017.md)。

## 改动及版本

- `team/workloads/unified-vdot/`：公共C判定器、四种编码/适配生成器、固定链接布局、构建/运行驱动、严格日志与ELF校验、跨镜像一致性审计和统计程序。
- `team/docs/unified-vdot-comparison-20261017.md`：结果及解释边界；本页和team/README/AGENTS更新交付入口。
- `team/evidence/unified-vdot-20261017/`：约20MB密封归档逐字节副本、压缩日志、必要镜像/ELF快照、版本/补丁/审计、439项哈希及发布前核对回执。原始归档保留生成时点的“未上传/no_github_push”状态。

发布前远端基础：`05e07deaf7ba1f8c0dbb2d2c2bd2d2db7e051a37`（T15）。此前本地源码/说明提交按顺序为 `4e883b39947bd0f62822c05a73795e9530e9a347`、`a40b99715e94c961d46b6c015599f5ee5180f3b7`、`1b47c72b3ba1edda6c4475050a0f9063dd0b421b`；本次另提交证据和交付入口。最终发布SHA以远端回读及本地Git交付回执为准，不在包含自身的提交中预填。

公共来源固定为：Jade `a17e38128e589d745152f3ef4b595b4572b22b3d`；试水 `4421d88beb39f8e95e23e25c78eaaaf1a7de4b52`；Redoop `fba90f8eb0818ed9539aa097691b371fd852f7a1`。详见程序README和证据审计。用户生产INT8路径复用T14实际构建源码 `2443fb1c101dfc5974ac208275a8b86d68a11e0f` 的封存EMU；T15独立INT16验证不参与本次性能比较。

## 发布前验证

[publication-preflight.json](../evidence/unified-vdot-20261017/publication-preflight.json) 记录本次实际核对：439项归档存储字节一致；64个运行检查均PASS；860个窗口；384个正式样本逐项一致；16条统计独立重算一致；Python源码语法检查通过。完整原日志→样本→统计与硬件源封存验收见归档的验收记录。

原全核运行入口为 `python3 -B team/workloads/unified-vdot/run-suite.py --variant ... --images ... --output ... --emu ... --reference ... --flash ... --jobs ...`，各实际命令、输入及依赖SHA见逐运行runtime/result记录。原分析入口为 `python3 -B team/workloads/unified-vdot/analyze.py --root <原实验工作区> --output <新目录>`。从新克隆做存储字节核对的命令见 [证据README](../evidence/unified-vdot-20261017/README.md)。本次上传复核没有重新构建或执行硬件。

## 边界与后续状态

Redoop原生为分lane dot4累加，表中计入统一dot8接口的完整软件适配开销。RVV与适配均是透明的共同算法，并非软件最优性证明；各接入版本的RVV周期可能不同，保留实测分母及绝对周期。窗口外C检查辅助代码未要求逐字节一致，未完全隔离微架构状态；不对细小周期差异强排名。

本轮没有统一工艺的STA/Fmax/PPA，不能据此给实际芯片时间、功耗或获奖排名。上传不代替成员人工ACK，不自动启动T16。此次目标仅为zjhwork，原硬件、指令规范、NEMU和既有密封证据不因发布而重写。

实际推送命令、前后分支SHA与回执保存在本机 `doc/四项目统一测试_20261017/Git交付/`。
