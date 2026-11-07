# Dot16 完整 Q288：目标证据与离线复核

合同：[CONTRACT.md](CONTRACT.md)，`r3-dot16-q288-consumer-v1`。本页是 2026-11-06 UTC 的实际结果；合同保留启动前冻结版本。机器可读索引见 [REFERENCE.json](REFERENCE.json)，原始记录见 [evidence-v1/README.md](evidence-v1/README.md)。

**固定完整 Q288 的正确性经离线复核通过。唯一目标 EMU 正常退出并产生 GOOD TRAP；原主机检查因协议行筛选错误返回失败，原失败记录完整保留。** 使用修正后的解析器对同一份原始输出复核，未增加 guest。D 的两个周期窗口为 33,505 和 33,504；与同镜像 P 的全部窗口均值相比，周期下降约 **22.91%**。这里只成立完整预打包 Q288 调用的正确性与 CSR 观测，尚无完整 forward、正式性能稳定性、完整退休窗口或 ASIC PPA 结论。

## 实现与固定输入

本次把已有 `q288_dot16_vdot` 接入四臂 AM，P、G、FR 完整函数字节保留。形状 M=K=288、组长32、36个行块、每块8行、每行9组；沿用56B context、128B槽和既有严格 binary32 运算顺序。D 返回 VL8/e8/m1、vstart=0、vcsr=7；judge 要求 FRM=0，不要求 fflags=0。没有更改 ISA、RTL、官方程序或参考实现。

原 paired16 target 归档为 `ade9abcd36b904cd84847b6246b4057edc5d88cfebbb612c534952b0206e7aff`。仅更换合同标识、arm2 绑定、满幅调用归属，并追加已有 D 整函数；各源码变换可逆。原 fixtures、prepare、judge、guards、五项共享故障控制、timer 和 dot8 probe 均保留。

| 实物 | 字节数或说明 | SHA-256 |
| --- | --- | --- |
| D 完整函数 | 484B | `ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb` |
| 新 ELF | 实际 GNU 链接结果 | `216ed0418829bed5be00732670aed8d09532ca6f9615a68f9ea720fd05649fe5` |
| 新 BIN | 实际 objcopy 结果 | `dd78e058f8acf29db8da47863bff8587608b333d3809dab2c5d04128fd6a02ac` |
| image-01/elf-check.json | 3120B | `baf4547961bcc1ad0cf8ef4a605f22fdafab0512da3847d99572984f1be86b37` |
| preflight-02/profile.json | 80项输入身份冻结 | `bb6c3be58e5c3992302952cb6684722494c501078b5d38fe419198cc27766c2a` |

镜像检查绑定了 P/G/FR/D 整函数、wrapper 实际地址、kinds/order、功能数组、golden、timer 和 dot8 probe。原六个编译单元、链接与 objcopy 共八个子进程均已回收，进程组不存在，输入前后身份不变。只构建这个 AM 镜像，没有重建硬件、AM库或 NEMU。

固定 EMU 为 `f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d`，feature1 NEMU 为 `cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae`。沿用已核实的1400B ABI与六个合法指令动态证据；O1/O2/T12/T13 TRACE均为0。已有硬件证据是输入来源，本次 Q 结果不新增退休 trace 或 ASIC 资格。

## 唯一目标运行与原失败

[RUN BEGIN 6687675746](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6687675746) 对应逻辑 operation `4f2ec6b0-c72d-47dd-ba53-b96aa3d4df57`。唯一实际目标操作：

`0844a5921b2fa4d9e47903bfc930fdee.b9e59cdda838f6aab491673b143c9389`

外层实际运行时间为 **14:50:57.065–15:26:02.402Z**；runtime记录为14:50:57.631–15:26:01.613Z。EMU PID/PGID均为5697，CPU1、Threads1。预算为6M guest cycles、7200s、每输出流64MiB、seed1、RAM128MiB；外层7500s。期间其他 P/PQ 运行使用CPU0/2，这些主机运行并非本叶的性能样本。

| 层次 | 原始终态 | 含义 |
| --- | --- | --- |
| EMU | exit0，GOOD TRAP，真实 DiffTest banner与指定reference | guest正常结束 |
| 原 runtime/controller-02 | FAILED；`ValueError('complete ordered guest inventory')` | 原主机解析失败 |
| 原 PowerShell 操作 | exit1，cleanup=true，无超时或取消 | 如实保留失败回执 |
| 进程与输入 | reaped=true，group_absent=true；80项输入及profile未变 | 原运行已回收，冻结身份成立 |
| controller-03离线复核 | DOT16_Q288_OFFLINE_AUDIT_PASS | 对同一份原始日志重新判读；0新guest |

错误来自 stderr 第5543和5631行的两条 PERF 统计，其中含 `a_reqBuf: chosenQ_cancel`。原筛选条件接受任何含 `Q_` 的行，因此把43条协议错误计为45条。修正只有一行：

```python
# controller-02：原始目标使用，原件保留
lines = [line for line in plain.splitlines() if "Q_" in line or line.startswith("QW")]
# controller-03：当前 run.py，仅对协议行首进行选择
lines = [line for line in plain.splitlines() if line.startswith(("Q_", "QW"))]
```

正向与逆向整文件精确相等证明只有这一处变化。全日志 failure gate、reference、DiffTest、GOOD TRAP、完整顺序和范围检查均未改。未知 `Q_` 行及畸形 `QW` 仍进入协议清单并被拒绝。

离线审计先复现原45行失败，再用新解析器对相同 raw 通过。三项实际负例均在日志副本上执行：删除一个 Q_CALL 变为42行，因完整清单拒绝；用真实 QW0 替换 QW1，仍为43行，因索引/顺序拒绝；增加未知 Q_ 行变为44行，因完整清单拒绝。原raw、profile、80项输入前后未变，原PID和进程组在审计前后均不存在。原 FAILED 文件未被重写。

原 `target-01/status.json` 的 `target_runtime_qualified=false` 保留；独立 `offline-audit-01/result.json` 的 `target_runtime_qualified=true` 仅表示此次固定 Q288 的原始日志重审成立。两者记录不同检查阶段，不把原操作改称成功。

## 正确性与全部原始窗口

实际完整协议包含29次 Q调用、8352个检查输出和10个计时窗口，调用数 P6/G6/D7/FR10。八次普通功能调用覆盖每臂datasets1/2，D另执行all−128满幅288输出检查；每个计时窗口包含一次同臂warmup和一次计时调用。五项原故障控制仍是首个P/dataset1的共享judge检错证据，不称为D专属负控。满幅调用不进入性能样本。

36288条dot16加1条旧dot8是源码计划数量，未验证实际退休数量。原全局统计的instrCnt=991818、cycleCnt=1706341也不能替代自定义指令退休计数。

| 原窗口索引 | 臂 | CSR cycles | CSR instructions |
| --- | --- | ---: | ---: |
| 0 | FR | 67600 | 35681 |
| 1 | P | 43994 | 22149 |
| 2 | G | 54102 | 20134 |
| 3 | D | 33505 | 26933 |
| 4 | FR | 62804 | 35681 |
| 5 | FR | 62776 | 35681 |
| 6 | D | 33504 | 26933 |
| 7 | G | 53958 | 20134 |
| 8 | P | 42928 | 22149 |
| 9 | FR | 62744 | 35681 |

| 臂 | 样本数 | 全部窗口平均cycles | 最大值−最小值／均值 |
| --- | ---: | ---: | ---: |
| P | 2 | 43461 | 2.4528% |
| G | 2 | 54030 | 0.2665% |
| D | 2 | 33504.5 | 0.0030% |
| FR | 4 | 63981 | 7.5898% |

以上不删除首个较高FR窗口，也不把该差异未经验证地归因于缓存。按全部窗口算术均值，D相对P减少22.9090%周期，P/D周期比为1.297169；相对G减少37.9891%，相对FR减少47.6337%。D每窗26933条指令，反而比P的22149条增加21.5992%，说明本样本的指令数排序不能代替周期排序。

这是同一新ELF、同一新EMU/reference、固定调用顺序下的CSR观察。样本数量有限，不授予正式性能稳定性资格，也不从这些窗口推断完整forward加速比。P/G/FR及既有较快合格RVV入口继续保留。

## 控制器与实际操作证据

controller-01和preflight-01原件保留。controller-02在目标启动前完成五处有限进程控制修正：TERM/INT只记录信号，取得Popen句柄后轮询monotonic截止，原stop_group只在finally清理，取消不能被后续exit0冲销。真实Python子进程探针覆盖句柄交接前TERM及清理期间第二次TERM，子进程5379最终exit−9并回收、进程组消失；运行器保持FAILED/cancelled=true/target=false。该探针是主机进程控制验证。

| 阶段 | 实际UTC时间 | 原ChatPC操作 | 终态 |
| --- | --- | --- | --- |
| AM镜像构建 | 14:14:59.604–14:15:01.014 | `0844a5921b2fa4d9e47903bfc930fdee.e7ca28ec1a61ac01158cd97f1284f63f` | exit0/cleanup=true |
| 取消探针及preflight-02 | 14:42:08.906–14:42:20.502 | `0844a5921b2fa4d9e47903bfc930fdee.c1c415a494eb0b2070d0df16a04b7024` | exit0/cleanup=true |
| 唯一目标EMU外层 | 14:50:57.065–15:26:02.402 | `0844a5921b2fa4d9e47903bfc930fdee.b9e59cdda838f6aab491673b143c9389` | 原host exit1/cleanup=true |
| 原raw离线复核 | 15:40:19.890–15:40:24.692 | `0844a5921b2fa4d9e47903bfc930fdee.c189e2a0a8190b38732de506fd4dd2cc` | exit0/cleanup=true |
| 证据归档并逐成员复核 | 15:44:55.511–15:44:57.411 | `0844a5921b2fa4d9e47903bfc930fdee.33573b01fbe3d530c1098d3251cb6f8a` | exit0/cleanup=true |

## 交付、回退与范围

[evidence-v1/evidence-01.zip](evidence-v1/evidence-01.zip) 共1495216B，SHA-256 `9056f62f93718b2afbe1dcea103b15b64f70292ae27546b78f544bb2249915f9`，保存111个原文件（9918838B）及内部manifest，包括实际镜像、源码派生、前置检查、原失败、原stdout/stderr、主机回执、离线复核和三个负例。全成员CRC/SHA及归档前后原件身份已验证；外部EMU/NEMU/compiler/AM依赖保留原profile路径及完整SHA，不重复收纳大型二进制。

WSL原件根为 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-q288-20261106-pro3/`。Windows审阅入口为 `D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\runs\dot16-q288-20261106-pro3\review-03\`；其offline-audit-01/original保存原raw，controller-03保存新解析器及原失败主机回执。具体成员映射见 [manifest.json](evidence-v1/manifest.json)。

[RUN END 6688977013](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6688977013) 已发布并全文回读，释放本次CPU1运行资源；WORK6670578319 / UPDATE6670959414和冻结成果仍保留，其他运行不受此RUN关闭影响。

后续若比较whole2或接入完整forward，应使用独立新叶、明确的新合同、镜像与profile，经协调后运行；本页不转移这些未执行候选的资格。回退只需不选用本独立镜像，既有稳定入口、旧实验和官方代码保持原状。
