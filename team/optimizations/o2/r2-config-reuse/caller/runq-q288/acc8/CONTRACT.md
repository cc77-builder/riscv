# R2-S3：Q288 八行 FP32 累加器驻留筛选

合同 ID：`r2-s3-runq-q288-acc8-screen-v1`。本合同只覆盖第一步实际软件研究：本机严格数值、真实 GNU 独立编译、完整 ELF 路径/ABI/地址和静态成本筛选。不包含新的 EMU 运行或应用周期资格；不得直接改变稳定默认。

## 1. 已观察的问题和单一干预

原 `runq-q288` v2 在提交 `ff873a0e043fcebea0617d08b452d92c64804650` 的完整 ELF SHA-256 为 `7f2c3d6de93f979cc252379a8fe2147e0d7ff121b0a38151f4604ee832884f26`。真实 GNU 11.4 `-O2` 的 `q288_full` 使用 192 字节栈帧、408 字节代码，八行累加数组在每个 group 反复读写，另有逐行和输出复制循环。这是实际机器码证据，不从 C 数组写法推断 spill。

仅把独立的八行展开为八个显式 `float` 累加器；不重排每行的 group0…8，不改变 pack、结构体/ABI、opaque entry、六个整数叶、原始 Ws 布局或独立 oracle。一次完整 Q 仍是 324 次叶调用、2592 次 signed int32→float、5184 次 FP32 乘法和2592次 FP32 加法。每行严格为 `term=float(dot); term=term*Ws; term=term*Xs; sum=sum+term`，每个 tile 从 +0.0f 开始，最后各写一次输出。

沿用父合同全部尺寸、指针不重叠、对齐、RNE、尾部/CSR约定与 `-ffp-contract=off -fno-fast-math`、无LTO/自动向量化等编译限制。两个乘法不可合并尺度，不能用 FMA、跨组整型累计或容差代替逐位输出。不同输出行的加载/算术可以合法交错。

## 2. 公平性与来源

同一个新包装服务全部六个原合格整数叶。必须验证与原 ELF 的每个完整叶体机器码一致；pack 的完整机器码也一致。原消费者固定公开来源、许可、输入生成、原始 row-major C oracle 和逐步舍入 Python golden 均复用父目录，不复制第二套实现。

父目录 `check.py` 只增加显式候选源/运行引擎参数，默认行为保持原样。`trace.py` 默认仍要求原 row 顺序；本新合同显式选择 group 模式，因为真实新 GNU 先加载 row7 再加载 row0…6。group 模式必须在每次叶返回至下一次调用之间核对该 `(tile,group)` 的八个精确 Ws 地址各一次，拒绝重复/缺失/错误组；Xs 的精确顺序不变。不能退化成全局 footprint。历史提交、快照、合同及失败/中断输出不覆写。

FP/向量算术在地址检查器中继续为 unknown。它验证的是机器码、控制流、地址、全宽 callee-saved 恢复和操作计数；本机逐位 oracle 检查数值。它们均不能替代实际目标执行与完整 DiffTest。

## 3. 第一阶段验收与停止条件

1. 真实 native GNU C：原8次输入序列（x0→x1→x0→x2、min-min、max-max、min-max、zero-weight）完整288输出逐位通过，完整pack、输入只读和guards通过；FMA差异见证仍为严格0、融合0xa3800000。
2. 新增一次针对展开的行误接 mutant：把 `s1=s1+a1` 改为 `s1=s0+a1`，保留实际源码/编译原文，由独立数值 oracle 明确拒绝。该错误无法仅由算术总数排除。
3. 新 GNU ELF：六叶完整身份、源快照/实际独立编译/BIN、324次精确实参、全部Ws/Xs、packed/slot/Y范围与ABI通过。
4. 原四项真实 ELF 负控继续通过：signed→unsigned、mul→add、错误尺度索引、错误panel步长。因为新代码使用八个fs寄存器，额外破坏一条真实fld恢复，要求全64位FP哨兵拒绝。
5. 静态门槛：六种完整Q路径均至少减少5%架构指令；FP栈访存只剩8次ABI保存与8次恢复。比较包含函数入口/退出与旧整数叶，不只统计组内片段。报告实际代码大小、栈峰值、分支、所有内存访问类别和指令，不换算成周期。

达到门槛只标记 `ACC8_STATIC_SCREEN_PASS`，可进入新的有界目标合同；否则 `ACC8_STOP_STATIC_SCREEN`，停止且不自动启动EMU。5%是本静态阶段的工程筛选阈值，不是官方评分标准或性能胜出阈值。第一份单对象探索只确认驻留机制，发生在完整静态路径比较之前，保留独立身份。

## 4. 运行和证据

使用 `screen.py --action host|build|verify|elf|compare --output <新输出>`；build/verify/elf/compare 复用原生工作区及冻结 T17/AM 依赖，`--build` 指向本候选完整构建，compare 另需 `--baseline-build` 指向上述固定原ELF目录。最多四核，输出在仓库与冻结输入之外。不创建额外完整工作树，不提供EMU启动子命令。

每次尝试保留实际命令、源码/工具哈希、stdout/stderr、结果及失败；只以成功的最终候选身份交付。研究结论与今后的目标合同须清楚区分软件共同收益、vdot对最快RVV的相对收益及完整模型收益。
