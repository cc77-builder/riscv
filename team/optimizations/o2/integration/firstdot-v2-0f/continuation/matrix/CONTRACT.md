# firstdot 当前组合中断续跑合同

合同：zjhwork-0f-firstdot-v2-continuation-v1。适用于2026-10-26当前组合第一次中断。
生产硬件、24镜像、普通firstdot生成器和原四文件runtime合同保持原样。
旧combination-run-01实际启动13次，完成1次预期negative和11次normal，第13次S1/d2/8×32仅部分运行。
进程已消失但没有实际退出码；登记INTERRUPTED_PROCESS_ABSENT，不虚构失败退出码、完成时间或PASS。

新输出仅运行剩余13个正式镜像和8个dataset0重放，共21个新EMU。
最终33个有效逻辑运行对应34次实际启动（含1次中断）。上述计数分别保留，不能伪称33次总启动。
旧completed-runs及所有旧原文、cwd、PID、命令与实际时刻保持原字节；run-locations.json显式映射来源。
在新目录封存整个旧attempt文件清单与hash，执行前重算11个normal及negative原文，执行后再次核对旧树不变。
新底层EMU记录仍遵守原contract；新增controller、来源映射与中断账本分别绑定，不伪造旧输入闭包。

normal仍要求完整128位输出、高位清零、退休/CSR、GOOD TRAP与O2生命周期。
所有24镜像均核对原构建、配对布局/RVV槽与当前0f硬件身份；全8重放要求全部24窗口一致。
汇总仍含384正式窗口、768全部正常窗口；没有丢弃任何成功结果或选择最快一次。
续跑qualify只核对记录/来源/计数/摘要；完整原文审计另行执行，不把qualify称为干净复现。
本工具限定这一明确中断；再次中断需保留此次attempt并建立后续续跑记录，不能在同目录覆盖。
不改生产RTL、不推送GitHub。
