# 真实 W2 完整边界合同 v1

身份 `r2-s3-real-w2-v1`。固定 M288/K768/GS32、VLEN128/RV64/lp64d/RNE；生产RTL、官方AM/NEMU/DiffTest、原runq.c及既有冻结代码保持原字节。本叶是可选新实现，不改R5或既有consumer默认。

## 输入与运算

在固定D288/H768/L6/V32000/S256、seed 0x53485041、token 1/7/19的自然完整forward中捕获p2/layer5的ffn_down前hq[768]/hs[24]与后xb[288]。捕获版和原版每位置全部3,691,424字节相等，并与已冻结原host-state逐字相等；独立调用原matmul复核完整288输出及NX-only标志。

新FR和TA仅从既有同名Q288父函数派生：t3=36→96，t1=9→24，tile后a4加252→672。全父源码可精确恢复；实际GNU函数字节只有这三个指令不同，其余机器字相同。每行24个组严格按0→23左折叠，int32 dot32→FP32→乘Ws→乘Xs→加旧值，不重排、不FMA、不按288/288/192浮点片段求和。打包P[t,g,r,k]=W[(8t+r)*768+32g+k]，36×24×8×32=221184B；权重scale仍原[288][24]。最终8个完整128位槽等于最后tile/group的独立dot32，低32精确、高96全零。

## 同口径目标计划

原scalar、强FR、TA同ELF/输入/output地址，预量化/预打包及初始化在窗口外。每样本先完整执行同方法W2并比较，再重置工作输出/slots/CSR/flags，计量整个C apply（context、分支与调用包含），四个CSR实际机器码及两侧IORW fence解码绑定；不扣除推测开销。

正常次序scalar,FR,TA,TA,FR,TA,FR,FR,TA；两组向量ABBA/BAAB，共9正式窗口、18完整调用。scalar原始row-major与向量packed来自同一权重，模型打包成本未计入，资格限权重可预打包的调用。正常每进程8次TA/221184个custom；负控使用同ELF数据control进入单TA样本，warm后计量，再翻转实际最后输出bit0，必须sample0/method2/result/byte1148拒绝；2次TA/55296个custom，预期BAD TRAP。负控不进入性能统计。

先真实参考验证和一次原DiffTest负控；随后三个独立normal/recovery/replay，独立输出/进程组，最多3核并行，所有资源总CPU≤4。每进程12M guest-cycle、10800秒、2GiB每日志上限；预算到期保持FAILED/PARTIAL，不从头自动重跑。原始O2/T13/控制台全量保存，使用既有已差分验证的流式O2审计；全部custom的数量、顺序、完整128位结果及终态清空通过，四CSR enqueue/sample/retire与UART逐窗一致，唯一canonical trap、原参考初始化/完整DiffTest及失败标记判据保持。

三正常进程原始窗口、flags、输出必须精确重放。FR四样本max/min跨度≤1%；TA最慢样本相对FR最快至少减少0.5%才称本计划vdot优选，否则保留更快合格RVV或HOLD。scalar→向量化与FR→TA收益分列，重复进程不增加正式样本数。结果不外推完整forward/token、任意序列/模型、冷缓存、功耗或ASIC PPA。

## 接入验证与交付

新全forward变体从现有纯consumer派生，仅把K768 scalar分支替换为相同方法的新W2入口，其他源码精确可恢复；旧consumer不改。固定模型三个连续位置的完整状态、模型原字节、fcsr及实际负控恢复通过后，才能给出这条组合的参考正确性资格。它不替代新组合的完整香山DiffTest/应用周期。

构建记录完整源码/工具/外部输入SHA、最终ELF/BIN/函数身份；运行保存命令/CPU/边界/退出码/进程组清理与原始/失败证据。发布正常快进，提供普通C源码/对象入口、scalar及FR回退和独立原文复算。
