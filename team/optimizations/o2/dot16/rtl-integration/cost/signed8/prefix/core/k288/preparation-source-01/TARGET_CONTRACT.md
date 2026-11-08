# 新 prefix 整核的固定 K288 完整调用回归

合同 `r3-prefix-k288-eight-window-regression-v1`。目的为新prefix EMU的功能集成增量：沿用原K288八窗口镜像、参考和guest检查，覆盖重复dot16、whole8/narrow、浮点处理、循环、完整输出/槽/guards/CSR。不进行新packed布局筛选、不修改软件算法，不把旧f149的周期成绩转授给新硬件。

## 新硬件身份

真实prefix core-build-02结果为 `06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2`；EMU为71489976 B / `6387d998c3f715a9ced1f44c4410f0f29f76780a96ec15c1830c8828ded6f887`。五阶段原六例smoke结果 `2ec969938a8c4f790e10ba7067befe22f890946b58f2a533276d3051c0cc6eda`、24项runtime pins `9df6be73b603e5b47f6f4bfc6bc9d84af75899f310bb8fbbdec71c8730fab4a2`及真实1400B ABI探针输出重新核身份；不重跑ABI。复用固定prefix smoke的build_record，检查七阶段构建、builder/lock/manifest、实际EMU/header。实际plan SHA `488be2506d8027b93aaa7d3954347b754207170eced5353c8ba1fa050587ff37`，核generation/native argv对应原回执及D16/O2/T14=1、其余五开关0、单核单线程MinimalConfig、DiffTest启用、TRACE0/DB0。不得构造旧e825报告或只改其SHA来冒充新身份。

芯片接口/时序沿原prefix规格：128位架构接口，低/高64位各8个signed8乘积；P两行19位、feature1结果20位；上升沿E0接收/E1推进/E2最早响应、无阻塞II1；P/R两槽及同步高有效valid reset保持。本次不改变硬件，不测物理core频率。原FU、父级与六例结果保持各自资格。

## 不变镜像、参考与判据

原目标runner为21707 B / `df95f6a05dbf3ffdf4314de38ecd8bce13ff3a7b63ef2583bb99d00f77e29655`。新runner是声明补丁的可逆派生；`guest_check()`与`run()`函数原字节不变，变化限合同标识、preflight的新硬件验证、固定K288/资源范围、真实profile元数据和CLI。衍生记录必须完整反还原原SHA。

原reference结果 `65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0`、21命令/10例和全输入检查沿用。K288 ELF `7b164fd3a6e08840f1bcc5824f48295e310e4d19544d41000740a8742fd58426`；normal-0目标BIN `5efdb3f53786490fd2752b44e0ec48053bbfab98ce829a82ec7fcc8b5db2a756`。仍由原screen.inspect核完整ELF、四GNU函数、RAM/BSS/栈、双侧fence的CSR采样、唯一success PC。目标与已跑参考仅原UART控制字不同，不改image、guest、reference、oracle、gate或parser。

P/N/packedP/packedN顺序仍[1,2,3,4,4,3,2,1]，八warm+八测量共16次完整288输出比较，4608输出及完整活动/非活动槽、guards、CSR/FCSR、prepared bytes保持。prepare在窗口外；唯一DiffTest启用、reference/image加载、原失败门禁、BEGIN/八SAMPLE/PASS、GOOD TRAP、精确窗口instret/FCSR/FNV均按原guest_check逐项判定，不新增负控/回放或trace阻塞，也不删原判据。

## 范围、预算与失败

仅K288 normal-0、CPU1单核nice5、seed1、RAM128MB、4,000,000 guest cycles、9000s内层、每流16MiB、9600s外层含回收。最迟2026-11-08 04:30 UTC实际启动，不能及时完成审定则取消本窗口；时间来自本轮工程安排，不是按旧速度保证必结束。禁止自动加时、重跑、转K768或新构建。只写新独立preflight/target输出；全部旧输入与新profile前后核SHA，进程组/信号/deadline/TERM/KILL/reap原逻辑保持。

成功只授这一固定调用的target_runtime_qualified与局部周期观察，不称完整G3、非法/trap矩阵、全应用或稳定生产切换。performance_qualified、application_performance_qualified、full_retirement_window_audited、retired_custom_count_verified、full_target_memory_dump和ASIC PPA仍false。记录新硬件各方法实际窗口；若比较方法只使用同一新profile/同一ELF中的较快合格RVV，不与旧f149周期拼接。超时、异常和回收失败原样保留。
