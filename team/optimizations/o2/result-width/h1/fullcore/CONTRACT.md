# H1 全核构建与 NEMU 差分回归合同

2026-10-21，用户已授权本轮全核构建和回归。工作根 `/home/riscv/riscv-lab/o2-h1-fullcore-20261021`，源码仓库 `/home/riscv/riscv-lab/zjhwork2-review-20261018/repo`。

沿用 H1 局部验证通过的生产源码：R 槽存低32位，公开输出128位。观察器读公开输出，不需调整协议/检查器；所有完整宽度、身份、取消、反压门禁保持原样。通过普通本地 Git 提交锁定硬件与 builder，不推送远端。

验收范围：新 H1 MinimalConfig 单核、O2观察配置EMU；hello/vadd、117唯一功能/异常用例（8分片执行124次）、原F2v控制、dense十二窗口；bit100故障NEMU差分拒错与同镜像正常库恢复；两个诊断补充；严格从原始流、退出码、输入和Git blob离线复核。原14项作业全部满足预期且六项O2覆盖完整才通过。

源/ISA/NEMU/黄金数据、默认模式、原R0 B0锁和旧封存载荷不改。正常NEMU和补充镜像来源已核对，复用冻结输入。原B0 build目录完整保存在工作根之外的独立目录，记录原EMU SHA；新EMU必须有独立硬件pins和SHA。不得使用旧EMU冒充H1。

资源：一次一个重构建，j2、JVM12G；EMU单线程，最多两个并行EMU。所有失败、命令和日志保存，完成步骤不无故重跑。全核运行期reset、G4公平性能、R2、默认切换、GitHub推送和真实成员ACK不在本轮完成范围。正式T16后置。

构建入口沿用 team/optimizations/o2/fullcore/build_fullcore.py；suite/supplements/recheck沿用已验证工具。先读本目录README中的恢复入口，避免中断后重复启动。
