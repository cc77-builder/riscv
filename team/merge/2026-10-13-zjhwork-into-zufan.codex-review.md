# zjhwork → zufan：本机独立验收报告

> **后续发布更新：** 用户确认双方无人开发并授权发布后，候选 `734353d01e963610ac864fdddd81e01e91f521fe` 已于 2026-10-13 普通快进发布到团队和 Fork zufan，两端回读一致。见 [发布记录](2026-10-13-zjhwork-into-zufan.publication.md)。以下“待交接/未 Push”描述此前验收快照，作为历史保留。

日期：2026-10-13，Asia/Shanghai。状态：**待交接发布**。复核者为本次本机 Codex，非原 ChatGPT 合并执行者。

## 1. 范围与当前结论

复用已有 C，在 Ubuntu-22.04 WSL2 原生 Linux 文件系统中从候选 bundle 建立独立检出，恢复匹配工具链并重新生成、编译、仿真组合 RTL 与真实 FU。G-M1、G-M2、G-M3 均 PASS，代码独立复核完成；G-M4 的真人交接条件尚未满足。**没有向团队或 Fork Push，没有调用或新增 GitHub Actions。**

本次新增内容仅为入口文档、复核记录和新测试证据；未修改生产 RTL、build.sc、测试器、黄金数据、模型、版本锁或已有历史证据。现有 M/C 保留，不重新合并或改写历史。全核/NEMU/DiffTest/PPA 未验收。

## 2. 已确认输入与约束

| 对象 | 完整 SHA / 结论 |
| --- | --- |
| 原目标 Z；团队 zufan 当前查询值 | `4a916689e3dfa74680da19653f1df6b8b984edeb` |
| 源 S；团队 zjhwork 当前查询值 | `ffec67e372d80a0588a74a83496434c9f7c086bb` |
| 共同祖先 | `c1ef31d81d50c209bf0e102af8ad7713c2da6dab` |
| 纯合并 M | `a3a7fd7e53924be08ac9a1dabcebb1573caae13c` |
| M 第一父 / 第二父 | Z / S，严格二父 |
| M 树；本次重新计算的自动合并树 | `17bb1dd1adf572c15625df7ea931b5575051f081` |
| 被测候选 C | `45bea984445e6f07d0d9c0ee8e42302e225ba0b3`，第一父 M |
| 个人 Fork zufan 当前查询值 | `4a916689e3dfa74680da19653f1df6b8b984edeb` |
| 新证据提交 E | `03c357cdecb380fcbe9a723ec16ddb45e85ab710`，第一父 C |
| 新增文档/证据提交 | 提交后完整 SHA 见仓库外最终回执，避免在包含自身的提交内自填 SHA |

实际 URL 为 `https://github.com/cc77-builder/riscv.git` 与 `https://github.com/LiZufan001/riscv.git`，不根据远程别名推断身份。开工重新 fetch 并 ls-remote；结束再次查询值保存在证据目录 `remote-final.json`，仍需在发布前重新核实。

原 before/candidate 两个 bundle 均验证为完整历史。Windows 候选起点干净，HEAD=C；WSL 检出同一 C。两侧独有路径 33/51 项逐个检查 blob 与文件模式；双方共同修改仅 team/README.md，双方相对 BASE 的新增有效内容保留。Z/S/M/C 的 10 个 gitlink、.gitmodules、team/versions.env 一致。所有子模块按固定 gitlink 递归初始化，未使用 update --remote。

## 3. 技术说明与独立复核

详细复核见 [逐项代码审查](../evidence/merge-review-20261013/independent-review.md)。直接审阅 VDotDatapath、VDot 状态机、FuncUnit/VecNonPipedFuncUnit、DataHoldBypass、FuConfig/FuType、RobPtr，以及平坦适配器和 C++ scoreboard；未发现需要修改的实质性 RTL 错误。

关键结论：signed8×signed8 经 16→17→18→19 位归约，低 32 位符号扩展、高 96 位零；握手时快照源与身份，RESP 的 valid 不依赖 ready，反压期间整份响应保持；匹配 flush 当拍撤销响应并优先于握手，较老事务继续；reset 清空在途资格；非法请求响应一次、保留身份且禁写。最小启动间隔为 4 周期，E0 接受/E2 沿后 valid/E3 最早响应握手，这是 FU 接口时序，不是 CPU 指令延迟。

检查器按独立的接受时间与环形 ROB 距离建立期望，逐拍核对事务守恒，完整比较 128 位结果和控制身份。负控在读回路径注入，不能称为生产 RTL 故障覆盖率。尚未接入译码/VFEX4、写回仲裁和 ROB 精确异常，相关全核风险仍保留。

FU 历史 source.sha256 与 C 为 16/16；组合历史在 `5227c030fdae9b6087fd995a00a3535b15f6aefc` 上 9/9，当前 8/9。唯一差异 build.sc 来自 S 新增 vdotFu 目标，当前摘要与 FU 记录一致；旧摘要没有重写。

## 4. 待确认事项与发布条件

G-M4 的 Agent 代码审查已完成，**团队成员 ACK 未取得**。已请求用户补充双方暂停写入、未发布成果、运行中任务、发布窗口与接收记录，尚未收到记录；没有证据就保持 UNKNOWN，不从远端静止推断队友已停工。GitHub 只读查询返回开放 PR=0、开放 Issue=0，不能证明外部沟通/队友电脑无任务。WSL 开工无 Java/Mill/Verilator 构建进程；其他成员主机和远端运行任务未验证。

发布必须取得真实团队约定，明确唯一推送者与窗口，处理未发布工作；再次 fetch 确认 Z/S 未出现未处理增量，审核固定最终 SHA 后普通快进 Push 到团队 zufan。团队远端完整 SHA 回读一致后，若 Fork 可安全快进，再同步并核验。任何新分叉、权限拒绝或未知写入均先停发布分析。不 Push main/James_Hotten/zjhwork，不强推，不删除分支。

## 5. 验证与证据

主机检查实际时间：15:14:57–15:15:02 +08:00。独立 Git/摘要复核结果见 `independent-audit.json`，主机完整命令/时间/退出码见 `host-runs.json`。

| 检查 | 状态 | 数量 / 退出码 / 日志 |
| --- | --- | --- |
| G-M1 Git 历史/内容/模式/锁 | PASS | 33+51 独有路径、10 gitlink、README 新增内容；independent-audit.json |
| G-M2 模型 | PASS | 35 unittest，5 文件重生成字节一致；exit=0；model.log |
| B6/B7 主机模型 | PASS | 各 262144 场景+4 极值；exit=0；baseline.json/log |
| R2 主机算术 | PASS | 65536 对字节、4104 八项、160 长点积；exit=0；arithmetic.json/log |
| 3 个原脚本 bash -n | PASS | model/datapath/FU 逐个执行；exit=0 |
| G-M3 组合 RTL | PASS | Chisel 生成 + Verilator 重建；22 定向+10000 随机，完整128位；exit=0；datapath/check.log/status |
| 组合 bit 0 / bit 127 负控 | PASS（预期拒错） | 两次实际 exit=1，VDOT_DATAPATH_MISMATCH；datapath/inject-*.log |
| G-M3 真实 FU RTL | PASS | 6类、71258周期；--assert 构建；exit=0；fu/check.log/status、results.log |
| FU identity / cancel-leak | PASS（预期拒错） | 两次实际 exit=1；fu/inject-*.log |
| VLEN=256 | PASS（预期拒绝） | 原脚本非零退出且原因匹配；额外独立目录重跑记录精确 exit=1；fu/invalid-vlen.log、invalid-vlen-explicit.status/log |
| 独立代码复核 | PASS（本次局部范围） | ready/valid、身份、反压、异常、取消、reset、事务守恒；independent-review.md |
| G-M4 真人交接 | PENDING | 暂停写入/在途任务/接收记录 UNKNOWN |
| 团队/Fork 发布 | SKIP | 门槛未满足，未尝试 Push |
| B5 汇编、NEMU、全核 DiffTest、CPU 性能、PPA | SKIP | 本次未运行，不以主机/组合/FU结果替代 |

FU 本次计数与历史一致：accepted=11245，responded=10960，killed=271，reset_dropped=14，illegal_responses=90，stall_cycles=25700；最终无在途请求，11245=10960+271+14。原脚本和黄金数据未改动。

组合运行开始 `2026-10-13T15:17:32+08:00`；结束状态 `exit_code=0 end=2026-10-13T15:18:29+08:00`。
FU 运行开始 `2026-10-13T15:18:29+08:00`；结束状态 `exit_code=0 end=2026-10-13T15:20:12+08:00`。

| 工具 | 本次实测 |
| --- | --- |
| OS / Python | Ubuntu 22.04.5 WSL2；Python 3.10.12 |
| JDK | Oracle GraalVM 21.0.12+7.1 |
| Mill | 0.12.3 |
| Scala / Chisel / 插件 | 项目锁定 2.13.15 / 6.6.0 / 6.6.0 |
| firtool | 1.62.1 |
| Verilator | 5.052，源码 ea338be98e1e838d3518809ce8899f85a009963c |
| clang++ / g++ | 19.1.7 / Ubuntu 11.4.0 |
| Git | Windows 2.53.0.windows.3；WSL 2.34.1 |

新工具置于 `/home/lizufan/xiangshan-validation-20261013/tools`；WSL 新增 Ubuntu 编译依赖和 LLVM 官方 apt 的 clang-19，没有修改 Windows 全局工具链。Java/firtool 下载经官方 SHA256 核验，下载来源/摘要和安装日志保留在仓库外 validation-20261013。Mill 从官方 0.12.3 release 取得；依赖从 Maven Central 下载，项目 Scala/Chisel 配置保持不变。配置见归档 env.sh。

首次下载辅助脚本把 firtool 的裸摘要当作含文件名清单，退出1；补齐文件名后官方摘要匹配通过。首次独立审计尝试要求 README 过时基线行仍存在，失败后根据三方 diff 改为核验双方新增有效内容；这是审计断言修正，不是 DUT、黄金数据或测试标准修改。安装失败原始日志和上述审计问题说明保留。

官方工具来源：[GraalVM JDK 21 下载](https://download.oracle.com/graalvm/21/latest/graalvm-jdk-21_linux-x64_bin.tar.gz)、[Mill 0.12.3](https://github.com/com-lihaoyi/mill/releases/tag/0.12.3)、[CIRCT firtool 1.62.1](https://github.com/llvm/circt/releases/tag/firtool-1.62.1)、[Verilator v5.052](https://github.com/verilator/verilator/tree/v5.052)、[LLVM apt](https://apt.llvm.org/)。GraalVM latest URL 本次实际取得 21.0.12，后续不得盲用移动 URL 代替版本/摘要核验。

实际命令（在 WSL 独立检出、source env.sh 后）：

```bash
bash team/scripts/check-vdot-model.sh
python3 -B team/research/2026-10-12-vdot-review/experiments/check_candidates.py --output <新目录>/baseline.json
python3 -B team/research/2026-10-13-vdot-round2/experiments/check_arithmetic.py --output <新目录>/arithmetic.json
VDOT_OUT_DIR="/home/lizufan/xiangshan-validation-20261013/runs/20261013-151732-281/datapath" BUILD_JOBS=2 bash team/scripts/check-vdot-datapath.sh
VDOT_OUT_DIR="/home/lizufan/xiangshan-validation-20261013/runs/20261013-151732-281/fu" BUILD_JOBS=2 bash team/scripts/check-vdot-fu.sh
```

生成 RTL SHA256：VDotDatapath.sv=`ea88154631ca52068442cd77b51de23e556349f28f81098d7471b94736141187`；VDotFuTestTop.sv=`a95ab1b4abb5dead3a7ae16bc29d90fa6b1c297b5d7106b21e8877ba7c25cc36`。两份新生成 RTL 均与对应历史 RTL 摘要完全相同；源/模型摘要见每个运行目录 source.sha256。

在 15:23:08–15:23:13 +08:00 对非法 VLEN 做补充运行，精确退出码为1、拒绝原因为 `VDot requires VLEN=128`。同次逐脚本语法检查通过，Linux 检出仍干净，递归子模块状态与初始化后清单相同；见 supplement.log。

## 6. 接手位置与下一步

- Windows 候选：`D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\merge-zjhwork-20261013`。
- Linux 独立检出：`/home/lizufan/xiangshan-validation-20261013/repo`，原被测 C 保持可查。
- 原始新运行产物：`/home/lizufan/xiangshan-validation-20261013/runs/20261013-151732-281`（含生成 SV、Verilator 对象/可执行文件和日志）。
- 版本化精简证据：[merge-review-20261013](../evidence/merge-review-20261013/)。
- 环境安装日志、完整恢复材料及最终提交/远端回执：项目根 `validation-20261013/`；新 bundle/证据 ZIP 由最终回执列出，不覆盖旧恢复包。

下一位先读本报告和最终回执，核对当前 HEAD、工作树、remote URL 与最新团队分支，再补真实发布窗口/成员交接。后续文档提交仅改变文档/证据，需核对源码树仍与 C 一致；若有生产变化，重新运行受影响验证。发布和 ACK 后，两个成员各用独立工作区在 zufan 错峰 Push，遵守 START→RELEASE→ACK；zjhwork 先保留，停止旧线写入须基于真实约定。
