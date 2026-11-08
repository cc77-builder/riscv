# Prefix K768：较长归约上的固定八窗口完整调用试验

合同 `r3-prefix-k768-eight-window-regression-v1`。这是一份独立的新实验合同，接在已闭合 K288 回归之后；它不延长、不重放 K288 原作业。目的为在同一新 prefix 核心上，验证冻结 packed-Ws 四种完整调用在 K=768、输出数288时的正确性和局部周期，判断较长归约是否仍值得采用打包布局。没有新硬件或软件算法修改，也不开始完整 forward。

## 决策依据与固定身份

K288 的新 prefix 目标已由原 operation .283ac7e7562e9d6789507846b5ca9e76 于2026-11-08 04:19 UTC闭合，16次调用/4608个输出通过；八窗口均值与旧硬件相同。这个结果没有证明K768目标，也没有新增硬件周期或整应用加速。

原已冻结八窗口 reference-02 的结果 SHA256 `65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0` 同时覆盖K288/K768；21命令、10次参考包括normal/replay与共享比较器负例。K768 reference退休1566414条，只用于确认已有参考覆盖和选择有限预算，不保证EMU墙钟。preflight重新读取所有原输入、snapshot、generated pins及选中normal/replay完整相等，不能只信历史叙述。

K768 ELF固定 `47cd616a5c89f27a679d2287998df45675413d96935ec21e1fa2fa8419c83f12`，normal目标BIN固定 `48302994e55a5ed4a0dfb9b577d65507eab12d343c3de48af895195b7d247b39`。原GNU四函数、main、完整fixture、reference、oracle、runtime gate与guest检查不变。目标与参考镜像仅原UART控制字不同。原screen.inspect重新检查完整ELF/BIN、RAM/BSS/栈、四函数、fence和CSR采样、success PC；不改官方参考/验证器。

新core-build-02结果 `06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2`，EMU 71489976B/`6387d998c3f715a9ced1f44c4410f0f29f76780a96ec15c1830c8828ded6f887`；六例smoke结果 `2ec969938a8c4f790e10ba7067befe22f890946b58f2a533276d3051c0cc6eda`。原prefix_hardware()逐字不变，检查真实七阶段build/plan/builder/lock/generated、24个runtime pins、1400B ABI原始日志与全部偏移、MinimalConfig单核单线程、DiffTest启用、D16/O2/T14=1、其余五开关0、TRACE0/DB0。ABI原始129B日志SHA `5d6e133fb80be4c75e3453364f6515b2a33ede5db81f4294f441fedb1238151e`；不重探ABI，不伪造旧硬件报告。

## 派生范围、接口与判据

新run.py以已经实际通过K288的25519B/`d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3`为父。只有合同标识、固定K/预算条件、profile范围描述、preflight状态名、CLI五项精确替换；完整逆还原必须恢复父文件。prefix_hardware()、guest_check()、run()原字节保持。旧K288源码、profile、target、原失败准备版本均不改。

本试验不改时钟、复位或接口：128位架构接口，低/高64位各8个signed8乘积；P两行19位、feature1结果20位；上升沿E0接收/E1推进/E2最早响应、无阻塞II1；P/R两槽和同步高有效valid复位保持。EMU guest cycles不等同物理ASIC频率。

四方法P/N/packedP/packedN按[1,2,3,4,4,3,2,1]运行；八次warm加八次测量，各完整比较288输出，共16次/4608输出，并核活动/非活动槽、guards、恢复CSR和精确FCSR。K768 prepared有效载荷27648B在测量前准备，结束后全字节再次检查。每窗instret应按原K768参考动态核对（本冻结normal记录为[58458,34085,58458,34085,34085,58458,34085,58458]），FCSR=1、golden FNV=f909c47ea8f72842。唯一实际DiffTest启用、image/reference、BEGIN/8 SAMPLE/PASS、GOOD TRAP success PC及所有原失败门禁保持。

## 独立资源与结束条件

仅K768 normal，一次EMU；CPU1单核、绝对nice5、seed1、RAM128MB。固定6,000,000 guest cycles（在原runner已允许上限内）、7200秒内层wall、每流16MiB，7800秒外层含有限回收。预算是有界投入，不是性能预测。最迟2026-11-08 05:10 UTC实际启动；不能及时冻结与审定则不启动。即使到最迟启动点，外层应在07:20 UTC前闭合，为07:50收尾留出空间。

仅写新dot16-prefix-k768-20261108-main的input/preflight/target及专用证据输出，不写K288或任何固定输入。全部原输入和新profile前后SHA核验；CPU/内存/当前其他任务在真实启动前检查，总CPU不超过四核。没有自动延期、重试、额外fixture、第二EMU或新构建。采用原进程组、signal latch、deadline、TERM/KILL/reap逻辑；失败/超时/取消与原始日志、状态、回执均保留。

## 比较与资格

报告八个原始窗口、四组同次均值及较快RVV与较快custom的比值；不能删掉更快的合格RVV对照，不与其他ELF/旧硬件窗口相除。prepare不在窗口，不能把额外存储和准备成本当成零；两次顺序观察不代表统计置信区间。host墙钟与aggregate诊断不得用作应用或硬件加速比。

成功只授此固定完整调用的target_runtime_qualified及局部CSR周期观察。performance_qualified、application_performance_qualified、full_retirement_window_audited、retired_custom_count_verified、full_target_memory_dump、ASIC PPA保持false。不新增目标负例、回放、TRACE或完整G3作为此试验的额外阻塞条件；它们未执行就如实记载。能否用于生产应用仍需整体成本与现有合同范围判断，不能把本试验当成50%整应用成果。
