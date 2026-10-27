# Q288 tail-agnostic 目标对照合同 v1

合同：`r2-s3-runq-q288-tail-agnostic-target-v1`。这是新实验；不得改判旧 phased、fused、acc8、split 或任何历史 HOLD。

## 假设、基线与修改

只有上一份 phased target 的 negative/recovery/replay、原文归档和隔离新源复算闭合、并按原规则选择 phased 后，才运行本合同。新候选仅将 `q288_phased_vdot` 函数偏移 60、336 的 e8 配置 `0xc0047057` 改为 `0xc4047057`，新入口 `q288_tail_vdot`。两者完整函数都为 764 字节、49602 条动态函数指令。其余机器字、访问次数、FP 顺序、ABI、最终 TU/CSR 恢复不变；原 FV、PV、FR 函数仍保留以作精确身份核对。

固定 T17 的结构性依据见上级 HARDWARE.md：普通无掩码 TA load 在对应 VL 非零且已知后，可以解除保存尾部所需的旧目的寄存器等待和 RF 读请求。自定义 dot 已经没有旧目的依赖，VL 和地址/访存依赖仍保留。源码机制不预告性能；这份实验的完整 Q 周期决定是否采用。不增加或改变 RTL，面积/时序实现沿用原 T17，未获得新功耗数据。

## 公平计划与事前门槛

三路：PV=`q288_phased_vdot`、TV=`q288_tail_vdot`、FR=`q288_fused_rvv4`。同一个新 ELF、同一 seed、T17/NEMU/AM/flash；8 个计时窗：

`FR,PV,TV,FR | FR,TV,PV,FR`

每个计时窗之前执行一次相同方法的完整 Q selfwarm；warm 和 measured 各自采用相同 prepare。三路各执行 x1/x2 功能检查。总计 22 个 Q：6 功能、8 warm、8 measured；6336 个输出、7128 个整数核、独立叶调用 0。每个正常进程 custom COMMIT=124417（含一个故障检测探针），计时 custom=41472，CSR_SAMPLE/COUNTER_ENQUEUE 各32。FP元素操作 convert/add各57024，mul114048。

四个 FR 全部进入锚点与比较。锚点稳定必须满足 `100*max(FR)<=101*min(FR)`。TV 升级还必须同时满足 `200*max(TV)<=199*min(PV)` 和 `200*max(TV)<=199*min(FR)`；另保留两块原始对照。锚点失败返回 HOLD，不选核。TV 未胜过两者时，若 PV 仍合格胜过 FR，则保留 PV，否则选择 FR。不得删窗、改阈值、追认有利子集；replay不是额外样本。地址/代码布局引起的剩余上下文效应属于此固定新 ELF 的范围，不能宣称普适收益。

## 正确性与封存

1. 先通过独立静态 screen：实际 GNU ELF 仅两位变化、低64乘加代数、任意尾部非干扰、完整8个值/地址/ABI案例，以及3项双重语义反例和4项尾部/身份反例。
2. 新目标 build 必须验证实际 GNU 命令、权威 object 不变、全部生成文件/数组、三路各数据集的完整函数/定时路径、实际指令计数和 frozen source closure。保留明确 `--undefined=q288_full` 链接根与普通 GC，不修改原生成器或参考。
3. 目标 ELF 阶段破坏5项数组/表和三路FP顺序，各须被拒；TA的3项语义反例与尾部控制复用实际新目标 ELF；五项 selector 反证继续使用全部锚点和 incumbent。
4. 单 EMU 串行 negative→recovery→replay，总CPU≤4。正常每进程最大12000000 guest cycles、7200秒；运行前冻结完整源、镜像及外部输入身份并登记保护。运行前后无输入变化。negative须拒绝高96位错误；两个正常进程须完整DiffTest/输出/调用计划/计数/全阶段custom PC序列通过并一致。
5. 原文 ZIP、manifest、历史必要对象和补充审计器封存后，在新 Python 进程只用归档源闭包复算；保留原依赖guard和逐字节结果相等判据。复用已固定 durable helper，仅把宿主审计子进程预算由180秒调整为900秒；保存子进程原始stdout/stderr与失败证据，不扩大 guest 预算或改变判定。

只限合成预打包 288×288、GS32 的完整 Q。pack、量化、首次权重准备、token、模型质量和ASIC不在本性能资格内。R5默认不变，既有强RVV与历史入口继续作为回退。
