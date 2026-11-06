# FR / GS32 / Paired16：同镜像首次完整 forward

合同：`r2-s3-first-forward-rvv-v1`。本叶 WORK6675484229，是三个软件入口的独立组合与固定场景观测；不改变默认选择，不解除 paired16 原 Q288 合同的 `HOLD_CONTEXT_VARIATION`。正式实验结果以本叶新镜像、参考和目标回执为准，父版本 PASS 只作来源证据。

## 1. 比较对象与语义

固定既有合成模型 D288/H768/L6/HQ6/HKV6/V32000/S256/GS32。每个独立进程从同一零状态镜像启动，完成共同 prepare 后，仅调用一次 token=1、position=0 的完整 forward。七个 K288 静态矩阵位置在六层中形成37个矩阵，唯一 W2 静态位置执行6次K768 FR，共43个矩阵。静态位置不是目标周期占比；MAC、instret、目标周期分别报告。

| 实验控制字 | 实际公开入口 | K288 路由 | W2 |
| --- | --- | --- | --- |
| `3` | `r2_w2_forward(state, R2_FR_CACHE, 1, 0)` | 原 FR | 原 `q768_fr` |
| `0x47533332` | `r2_w2_gs32_forward(state, 1, 0)` | 冻结 GS32 v2 | 原 `q768_fr` |
| `0x50313631` | `r2_w2_paired16_forward(state, 1, 0)` | 完整 paired16 | 原 `q768_fr` |

后两项是实验私有标签，绝不强转成旧公开方法枚举。旧方法0–4及方法5非法域保持原语义。

三入口共用同一编译单元中的 `initialized`、模型绑定、状态结构和 `r2_w2_init/reset`。从实际 norm/W2 FR-cache 模板追加两个完整克隆，只替换七个K288路由名；唯一W2行逐字保留，两个克隆都须可逆恢复为原模板。旧 `consumer.c` 除新增私有路由和公开入口外须精确可逆，旧 include 的全部字节作为前缀保留。原五个模型缓冲、packed-W、scale、量化、norm、RoPE cache、attention、SwiGLU、尾部以及FP32运算顺序不变；沿用原 `-ffp-contract=off`、`-fno-fast-math` 和其余编译参数。

完整GS32为420B、SHA `2d95481faa1c79f7a8a06ef65fc02154e30cf731e6ba5c990a7209c2e90c32ab`；完整P为1096B、SHA `a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c`，包含原X guard及内嵌FR回退，保留全部signed INT8输入域。两函数只从冻结程序集的唯一完整 `.size` 边界提取；新ELF须逐字等于原screened ELF中的完整体。原四个K288/K768汇编函数与norm链接身份同样核对。不新增ISA，不改生产RTL、参考、官方AM或验证程序。

## 2. 同一初始化与计时窗口

共同前端从实际冻结 norm first-token `main.c`（SHA `4537a39c9b07bd4d2e61f6b7e48aae7f241b7905abd18fb198402fce356976ad`）窄派生并保存逆向证明。沿用FS/VS、VLEN128、TLS/errno、state guards和同一init。build直接检查完整raw镜像的state/report/TLS为零；不引入G/P三步正确性harness的两遍 `state_empty()`、其API负控、自热或单臂reset。

计时前正常目标路径打印完全相同的 `CONSUMER_BEGIN token=1 position=0`，随后统一设置 `errno=12345`、FCSR=0（RNE、无累计标志）。方法控制字的读取、方法合法性判断及分派**全部位于计时窗口内**，避免前置短路分支差异。四次CSR为 `cycle → instret → 完整入口 → instret → cycle`，每次读数沿用两侧IORW fence，先将四值保存至局部变量再写report；方法身份也在四次读取后写入。小量共同分派成本计入，不作估算扣除。

终态FCSR在状态比较、计数UART及后续工作之前取得，须为1（NX，RNE）；完整输出/state与errno、guard检查保留。目标周期只取 `c1-c0`，instret只取 `i1-i0`。NEMU参考读数、EMU主机耗时、guest从启动到trap的总周期均不替代forward窗口指标。

三份正常目标镜像从同一最终ELF/BIN构造：negative=0、UART=1、模型、初始state及所有其他字节相同，差异仅为method控制字的4B。冻结时实际逐字核对该条件并记录三份SHA；每次目标启动再绑定其SHA。三臂分别fresh进程，不在一个进程中连跑。代码/数据整体布局共同固定，克隆入口仍位于不同地址；记录真实符号与地址，结果属于该最终镜像的完整入口表现，不把全部差额归因于K288算术。

这里测量的是**既有预打包模型、规定共同prepare后的首次完整forward**。窗口外的模型生成/packing、进程启动和init成本不包含在结果中，须随结果披露；入口内部实际绑定、量化、RoPE等工作均留在窗口内。不声称缓存全空、含预处理的冷启动、连续token吞吐或任意模型性能。

## 3. 构建、参考与实际路由

`bind.py` 将原norm target的reference/audit/run脚本做逐项记录、整文件可逆的有界派生；原件不回写。新builder重新编译组合consumer，不能继承旧“同一CORE未重编译”或旧八方法资格。保留新源码、编译命令、实际ELF/BIN、完整kernels、TLS、norm、四CSR与模型/零初值身份。

GS32既有95文件支持快照和已按原字节恢复的scalar视图只读复用；它们不包含的norm-target辅助工具从当前仓库原文件只读发现实际导入闭包，逐字保存至新controller的`target-support`，绑定固定SHA后从新快照加载，原文件不改。保留原源码路径的身份核验，但不要求仓库HEAD长期不变。官方AM保持指定Git revision及原文件，复用预建库。输出只在新仓外目录，不新克隆，不使用其他Agent的index。

新ELF的机器字检查枚举FR/G/P三个cached consumer各八处route调用，重算a5真实kernel指针、call目标、准备区间及唯一W2 FR选择；核对两个公开入口各到自身clone、共同计时点只调用共同dispatcher、dispatcher包含三个真实入口。该证据是固定ELF的有界静态指令审查，不声称全程序符号执行或动态矩阵调用计数。另由独立审查者核方法映射和实际指令。

短资格按单核、五个独立参考进程串行执行：negative(P)、FR、GS32、P、P-replay。复用原first-token比较器及进程owner，保留原参考库和adapter身份。不能拿三步consumer比较器直接代替p0比较器。

- negative在guest翻转最后一个logit最低位；须exit2/BAD94，完整比较器恰在byte152476拒绝，原完整state/guards只允许该指定比特差异。
- 三正常入口分别比较完整3,691,424B state、两侧guards、五模型缓冲、gold、TLS/errno、report/控制字、RNE/flags与实际trap，正常exit0。
- P-replay须与P的完整validation、参考退休量和计数原值相同。它验证参考侧确定性，不增加目标性能样本。
- 五个实际PID必须独立、子进程及进程组全部回收，输入前后无漂移；失败和未知状态保留，不自动重试。

## 4. 目标执行与结论

目标队列与参考队列分开，只有FR/GS32/P三个正常fresh进程。运行原T17 EMU、原正常NEMU DiffTest、seed1、128MB、原UART和观测设置；冻结具体硬件/参考/flash/配置/输入、CPU槽位及资源合同后由主端统一启动。所有三正常臂的architectural custom COMMIT必须为零；ELF内保留未选中的旧TA函数不构成执行许可。完整协议、fatal、DiffTest、guest全状态比较和四CSR退休链检查沿用成熟判据。

默认首轮不追加第四个耗时target replay，不机械搬用Q288的1%或0.5%稳定性门槛，不生成巨量普通指令全退休trace。三次正常完成授予本固定边界的三条目标观测及正确性；不授予目标重复一致性、跨输入/布局稳定性、完整256位置、任意模型、ASIC PPA或默认优选。`performance_qualified=false`、`full_retirement_window_audited=false`保持真实；后续采用判断应注明新取得的实际证据与有限范围。

原P Q288 HOLD不被新合同覆盖；新完整结果可以改变下一步工程排序。若P局部优势在完整调用中消失或GS32更快，采用实际证据调整；若接入扩大成重写K768、tail或packing，暂停扩大并回到主端评估。
