# O1/O2 同镜像公平周期对比合同

本轮G4由用户2026-10-19明确授权，本地分支local/o2-performance-20261019，基点07ed301。本目录是工程测量材料，正式T16报告后置，不推送GitHub。

## 固定输入与构建

使用统一测试ours-images-02的原16镜像：1校准、3功能、12性能。必须逐字节匹配已封存tar内的208项源码/数据/ELF/bin；不重新生成工作负载。共同正常NEMU、flash、seed=1、128MB RAM、MinimalConfig单核/VLEN128/EMU_THREADS1，clang19.1.7及原O3/O0、j2/12G。

O2复用已通过G3的EMU ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57；O1由相同429项硬件源码及21236项依赖重建。功能选择为O1_HANDOFF/O2_ELASTIC=1/0与0/1。共同FUSED_INPUT=1、T12_TRACE=0、T13_TRACE=1；配套合法观察器分别O1_TRACE/O2_TRACE=1/0与0/1。观察器差异只用于各自协议校验，不参与硬件功能。不得把旧O1源码的既有二进制直接当作匹配构建。

使用独立外置BUILD_DIR；生成器固定写入root build的辅助文件必须事前备份、记录新生成身份、复制给新产品，然后恢复并核验原G3 build字节，旧EMU不覆盖。保留每次构建失败及真实退出码。

## 运行与门禁

两模式先校准/功能通过，随后四场景single1、chain256、batch128、stream64，各3数据集、4轮measured，first/warmup全部保留，custom/RVV交替顺序。每模式16次首次镜像运行；dataset0 batch128每模式再补2次全新EMU重放，共36次运行、478校验窗口、192正式性能窗口。重放只证明代表镜像确定性，不增加独立样本数。

同一镜像内两模式顺序运行，跨镜像最多两个进程并发；每项120m、2百万周期上限、seed1。前后核验源码/依赖/EMU/镜像/参考库/flash/检查器摘要。每项必须真实DiffTest、退出0、唯一GOOD TRAP、无致命错误、完整寄存器/高位/CSR/哨兵通过，T13机器码/退休/CSR/全局计数窗口一致；用各自原O1/O2分析器完整核对事务生命周期、精确vdot提交及有限排空。

## 统计与取舍

正式样本为每模式每场景每方法12条。报告原始cycles、均值/中位数/范围、instructions及cycles/dot。加速比使用该模式本次实测sum(RVV cycles)/sum(vdot cycles)。O2硬件收益为1-sum(O2 custom)/sum(O1 custom)，逐dataset/repeat/seq/镜像配对，工作量与退休指令一致，分别列RVV变化。

预定投入目标为batch相对O1降低至少10%；按新测O1计算判断，不把历史362.50直接当分母。其他场景均值退化超过2%必须调查，样本不得静默剔除。不扣空窗或屏障/循环开销，不使用宿主秒数计加速比，不由II直接预测应用性能。结果不产生Fmax/PPA/官方排名/最终采用或人工ACK。
