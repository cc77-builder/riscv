# O1/O2 同镜像公平周期对比

本轮G4已获用户授权，正在本地执行，尚无最终结果。正式T16报告继续后置，不推送GitHub。

工作分支local/o2-performance-20261019，起点07ed301；输出/home/riscv/riscv-lab/o2-performance-20261019。O2复用G3固定EMU，O1从完全相同硬件输入重建；源码、编译、运行及结果整理的身份分别记录。

[测量合同](CONTRACT.md)。沿用16冻结镜像与四场景，预计36次运行、478校验窗口、192正式窗口。加速比使用各自新测RVV；不会直接复用旧362.50/678作为本轮统计输入。

从完整checkout执行，所有输出必须全新：

    python3 -B team/optimizations/o2/performance/build_o1.py --output /absolute/new/o1-build
    python3 -B team/optimizations/o2/performance/compare.py --o1-pins /absolute/completed/o1-build/hardware-inputs.json --output /absolute/new/campaign
    python3 -B team/optimizations/o2/performance/results.py --campaign /absolute/completed/campaign --output /absolute/new/results

本机默认路径绑定当前固定输入。不要启动已经运行的campaign；先读state.json及每项runtime/result。失败尝试完整保留，新尝试使用新目录。build_o1.py使用外置产品目录并在finally恢复原G3生成物；原EMU保持字节不变，不清理旧构建。

compare.py按两模式各自协议与共同T13计数器做真实检查；build_profile.py核验同源码、工具和路径归一化后的实际编译指令；results.py从原始分离日志、退出码与Git绑定工具重算全部结果，输出逐窗口CSV及工程记录。

构建j2/12G、单线程EMU、宿主并发最多2。G4完成也不等于最终采用、PPA、应用收益、人工ACK或T17新机器复现；O2默认仍关闭。
