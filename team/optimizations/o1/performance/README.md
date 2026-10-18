# T14/O1 同镜像公平性能比较

> **交付更新：** 本结果随O1父级及全核成果交付 zjhwork，见 [发布说明](../../../docs/o1-publication-20261018.md)。下方“本地保存”及密封证据中的未上传字段为生成时点状态；最终发布以远端回读为准。本次不重复仿真、不修改原始数据。

本轮真实运行及完整离线复核完成，成果本地保存。正式T16报告继续后置。

独立batch128平均周期 453.25→362.50，降低20.02%；O1相对实测RVV为1.870×。

| 场景 | T14均值cycles | O1均值cycles | 周期降低 | O1相对RVV |
| --- | ---: | ---: | ---: | ---: |
| 单次点积 | 71.000 | 71.000 | 0.00% | 1.201× |
| 依赖链256 | 1857.000 | 1857.000 | 0.00% | 2.930× |
| 独立批量128 | 453.250 | 362.500 | 20.02% | 1.870× |
| 加载/计算/存储64 | 1127.500 | 1127.500 | 0.00% | 1.005× |

36次主campaign运行、478个校验窗口通过，其中192个为正式性能窗口；另有1次11窗口O1校准探针不计入统计。额外4次batch128全新EMU重放逐seq周期与退休指令数一致，不作为独立统计样本。最后22项主机检查通过。

[测量合同](CONTRACT.md) · [密封证据](../evidence/20261018-performance-ab/README.md) · [完整结果](../evidence/20261018-performance-ab/files/work/results-01/性能结果与工程记录.md)

两模式使用完全相同的16份ELF/bin、参考库、flash和seed=1；427个硬件文件、21236个依赖文件一致，实际编译器clang19.1.7及C++/硬件生成参数一致（仅归一化输出路径）。唯一功能开关差异为VDOT_O1_HANDOFF=0/1，共同设置FUSED_INPUT=1、O1_TRACE=1、T12_TRACE=0、T13_TRACE=1，MinimalConfig/单核/VLEN128/EMU_THREADS=1。

O1复用原完整回归的固定EMU，T14本次从同一组输入生成并编译；本轮工作负载全部实际重跑。T14初次外置目录构建缺少固定输出的辅助源文件，复制本次生成文件后继续编译；旧恢复脚本曾误固定宿主time.log，事前记录范围修正，并通过finalize_t14.py核验全部不可变生成输入。失败、恢复和最终回执均保留；当前恢复脚本已修正并有专项测试。

O1硬件源码18c0ce08，EMU b13b05a3b03d2dd178d5e07b55bda1e8d99d7a094d44cf30405241f9793170cb。

T14生成源码 72fc206a417e5781dded45433eae0de45f181458，继续编译源码 2dee53fcd8afd4678800b512a0716825c3f15b6f，EMU 081247df2c8220a37ee77be47a2c032bd0da0dba3544cd5e7bf0f63aaad45142。

正式运行器源码 3fa8a70645cf3f38a9d05618ac555a4582041013。后续结果导出工具独立记录身份，不改原始结果。

工作根 /home/riscv/riscv-lab/o1-performance-20261018；本地分支local/o1-performance-20261018。从完整WSL仓库执行，输出路径须全新：

    python3 -B team/optimizations/o1/performance/compare.py --output /absolute/new/campaign
    python3 -B team/optimizations/o1/performance/results.py --campaign /absolute/completed/campaign --output /absolute/new/results

默认入口绑定本机的固定镜像、二进制与参考库。换机需恢复原统一测试镜像tar并显式更新入口路径、重核摘要；本轮不是T17干净机器完整构建复现。

窗口包含循环和屏障开销，不扣空窗；batch为同一输入的四路独立目的，不等于实际GEMV收益。本轮没有Fmax/PPA结论。O1默认关闭，未推送GitHub；团队人工ACK、O3应用/O4时序代价及O5/T17复现仍待完成。
