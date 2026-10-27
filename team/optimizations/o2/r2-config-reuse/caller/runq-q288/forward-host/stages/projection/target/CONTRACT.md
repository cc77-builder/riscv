# W1 与 classifier 尾边界目标合同 v1

`r2-s3-projection-boundaries-v1`。固定 T17、VLEN128、原 AM/NEMU/DiffTest 和原 TA/强 FR 完整函数体；不修改官方代码或旧冻结输入。

在同一 D288/H768/L6/V32000/S256、seed 0x53485041、连续 token 1/7/19 的真实完整 forward 中捕获 p2/layer5 的 W1 量化输入和768行输出，以及 p2 classifier 的量化输入和全32000行中的最后320行。捕获版与原版每位置完整16 spans相等，并逐位核对既有 full-build-06 的原模型、embedding及三位置状态；不能把末态classifier的xq当成W1输入。

目标 case0 为 classifier 行31680..31999：一个完整288行块和32行尾块；case1 为完整 W1 层5 M768：两个完整块和192行尾。使用与完整 projection 相同的原 q288_pack 布局，完整尾块补零权重、补scale=1；目标预打包只读fixture须与完整projection参考中的对应块逐字一致。预量化、初始化打包在窗口外，两个方法完全共享输入/packed/scales/output地址。

每case使用FR/TA/TA/FR（ABBA）四样本，每样本先执行整个同方法边界作selfwarm并比较全部输出，再重置工作输出、清fcsr，测量整个边界。窗口包含全部2/3次内核调用、context构造、循环和尾复制；cycle与instret读前后均有fence iorw,iorw，实际ELF逐条解码确认。所有有效输出逐字等于实际完整forward捕获值；未使用输出、tail和slots guard不变，补齐行输出为+0，最终完整slots高位与值为0，CSR恢复到原ABI。FNV摘要仅便于原文重放，不替代目标端完整字节比较。

正常进程40Q（20TA/20FR），完整custom提交207360；其中没有旧QKV探针。应用负控在case0第二样本结束后翻转真实末输出一位，必须在case0/sample1/byte1276被拒绝；执行8Q，custom提交41472。正常、负控、恢复、重放均使用原官方DiffTest；预期BAD TRAP是应用负控，不称作新DiffTest判错负控。

先单核负控通过，然后最多3个独立CPU槽位并行normal/recovery/replay；同ELF、同seed、独立cwd/PID/进程组。每进程最多800万guest cycles、7200秒、1GiB每日志，继承硬容量不足直接拒绝。原始custom日志不得静音或删减；全O2协议、队列清空、完整custom PC顺序/数量与官方runtime/fatal检查均通过。完成的日志逐个解析，三个正常运行的原始计数/输出必须精确复现；重放不增加正式样本数。

所得资格仅为这两个具名预量化局部边界的目标正确性与ABBA周期。完整W1算864行而有效768行，额外12.5%；classifier末320行算576行，额外80%，而完整classifier补齐仅0.8%。两个小工作集的selfwarm不能代表完整classifier约10MB工作集，不能倍乘、外推完整FFN/classifier/token收益，不能混入初始化或量化收益。完整projection参考PASS不替代这里的新目标运行，也不转成完整forward香山DiffTest资格。
