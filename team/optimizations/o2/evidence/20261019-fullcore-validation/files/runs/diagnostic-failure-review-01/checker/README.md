# O2 补充诊断失败复核（checker 子任务）

结论：日志中的直接失败原因是生成工作负载在 SEW=8 下用 vmv.x.s 读回点积结果，却用完整 signed32 结果构造后续 AVL 的异或常量。真实日志与 ELF 指令序列一致，未观察到两槽 FU 协议违规。

末段证据：

- PC 0x80002be8 的首条切换点积：seq=1152，cycle=111675 接受，VL=8、illegal=0；cycle=111677 返回完整值 0x000000000000000000000000ffffe421。
- SEW=8 的 vmv.x.s 只读最低 8 位，实际得到 0x21=33。工作负载的常量却按 signed32(-7135) 与 8 异或，得到 0xffffffffffffe429；实际 AVL 因而为 0xffffffffffffe408，下一次 e8/m1 设置饱和为 VL=16。
- PC 0x80002c00、ROB 1:16 的下一条点积：seq=1153，cycle=111696 接受，VL=16、illegal=1；cycle=111698 返回 data=0、写使能均为 0、exception=4。这符合既有非法指令合同。
- cycle=111718 的 ROB redirect 对 ROB 1:16 self=1，真实父级 flush 在下一拍。随后出现取指地址 0 的 PMA 错误及 double trap。程序没有第 10 项通过行和最终 summary。

冻结分析器对完整原流执行显式 partial 审计，所有已观察事务均符合身份、时序、算术和取消规则；这是失败运行诊断，不是补充测试或 G3 通过。

同时确认冻结 runtime_gate.py 未匹配 HIT CRITICAL ERROR、double trap 或 isa pma check failed，因此它单独会放过这份 exit=0/GOOD TRAP at 0xe 的失败日志。当前补充测试仍被完整程序标记门禁拒绝，没有形成测试成功；建议后续另版本增加明确致命标记拒绝，并保留本次原始失败证据。冻结文件未改。
