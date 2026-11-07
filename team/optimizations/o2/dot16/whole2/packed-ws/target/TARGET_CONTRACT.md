# Packed-Ws 八窗口目标小试 v1

合同 `r3-packed-ws-eight-window-target-v1`。一份profile只启动一个固定K、固定fixture的原香山EMU实例；没有自动串行第二K或长forward。当前计划仅K288 normal-0。先用这个真实小试决定打包布局是否值得继续，不把参考指令数当目标性能。

## 已有证据与实际输入

八窗口新reference已经实际闭合：`reference-02/result.json` 166147B，SHA256 `65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0`。两K共21命令、10例参考，包含两个共享比较器负例、normal完整回放，全部子进程已回收；正式performance仍false。K288整体reference退休731770条，K768为1566414条，不能据此给出目标墙钟保证。

参考controller为 `41907943f78825afb3accde2ead8f9952e01b60770fe76cec8e2b6436b4ea76e`，main为 `6933f5a75a9b61b4b6ee96cdaae1f2e4649312ef0ef726272c7d521c08bc2b4d`。前置九窗口reference `cec287cff44cdda1070539515a3d426fd81e6a4025e0a84ac6bcb632ef7f1f5a` 保留原scalar交叉；新目标不声称重新执行scalar。

| K | 新ELF SHA256 | 原编译BIN/normal目标镜像SHA256 |
|---|---|---|
| 288 | `7b164fd3a6e08840f1bcc5824f48295e310e4d19544d41000740a8742fd58426` | `5efdb3f53786490fd2752b44e0ec48053bbfab98ce829a82ec7fcc8b5db2a756` |
| 768 | `47cd616a5c89f27a679d2287998df45675413d96935ec21e1fa2fa8419c83f12` | `48302994e55a5ed4a0dfb9b577d65507eab12d343c3de48af895195b7d247b39` |

preflight重新计算reference全部原输入、snapshot及generated文件pin，检查10例闭合状态、21命令真实退出、选中default与replay完整相等。通过原冻结 `screen.inspect` 重新检查完整ELF/BIN含BSS、节/栈/RAM、四个完整GNU函数及RX位置、实际成功/失败trap、四处双侧fence的CSR采样。目标使用原编译镜像normal=0、UART=1，与已跑reference image相比仅8B控制范围中的UART字0→1。

硬件继续使用EMU `f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d`、feature1 reference `cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae`、flash `a3360212cf7bb784119c1719c9258362f8567803601b2359aee2c104864fa994`。完整1400B ABI与D16/O2/T14=1、O1handoff/所有trace=0通过固定hardware-result `e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f` 和全部runtime pins绑定。没有重建EMU、改官方工具、重新探测ABI或应用新RTL候选。

## 窗口及公平比较

原P、原N、packedP、packedN的方法号分别1、2、3、4；固定顺序 `[1,2,3,4,4,3,2,1]`。每窗先独立warm，正常16次完整调用。每次仍做全部288输出、完整活动/非活动槽、guards、恢复CSR和精确FCSR检查；actual PREPARE与独立完整packed-scales比较在测量前，结束后再次比较全部prepared字节。

准备成本不在这些窗口内。打包增添的Ws存储和准备读写不能视为免费，生产应用是否值得接入需另评估。四函数全部在同一ELF、同一硬件、同一fixture内比较；须保留两种合格RVV中实际较快者，不因packedP更快而删掉它。不与其他ELF旧周期相除，不减猜测固定开销，不叠乘历史百分比。

## 目标验收与观察边界

运行原子进程成功退出后，严格检查：指定镜像/reference加载、一次真实DiffTest启用、原失败门控无错误、唯一GOOD TRAP PC恰为新ELF的success symbol；PWS日志恰为BEGIN、八个有序SAMPLE、PASS。每条sample需满足精确方法顺序、正且在原guest界内的周期差、对应新reference窗口的精确instret差、完整FCSR期望和原gold的FNV。任何缺行、重复、未知PWS行、错PC、错误flag或hash都拒绝。

实际的16次全输出/双槽/guards/CSR检查由冻结guest完成，UART成功序列与原DiffTest共同证明其执行通过；不声称采集了目标内存dump或完整CSR导出。终态aggregate只作运行诊断，不能替代窗口或应用性能。报告保留八个原始窗口、四个双顺序均值、布局增量及较快RVV/自定义候选比值，不声称两次观察构成统计置信区间。

成功资格仅为固定完整调用正确性与局部周期观察：`target_runtime_qualified=true`。`performance_qualified=false`、`application_performance_qualified=false`、`full_retirement_window_audited=false`、`retired_custom_count_verified=false`、`full_target_memory_dump=false`保持。没有把目标负控、目标回放或新TRACE升级为本小试额外门槛；这些并未执行，必须如实列出。

## 资源、回收与保护

当前K288计划：CPU1、绝对nice5、一worker，4,000,000 guest cycles、9000s内层wall、每流16MiB、9600s外层含回收余量。它是有界投入，不是预计耗时。原四臂forward的进程、CPU、输入及期限不变；不同时另开其他有计算负荷的辅助worker。K768是否运行须在K288结果/资源审查后另冻结profile，不自动连续执行。

`run()`复用旧完整Q288 runner `ed585cfa849358b4ee28eae0cd46afeb56ca089a77c09acdc359b36e765fb55e` 的进程组、signal latch、deadline、TERM/KILL/reap和最终所有pin审计；仅资源绑定、状态名和范围描述按派生记录修改。profile SHA和冻结runtime源码必须在启动前再核。唯一新输出为preflight与target树，其他输入只读。不得自动延期、重复启动或用新ID重放未知结果。

外层operation、profile、实际owner/EMU PID/PGID、原始两流SHA/长度及终态保存；进程必须reaped、group absent，输入/profile不变。超时、取消、失败、回收异常的证据完整保留，不升级为PASS。
