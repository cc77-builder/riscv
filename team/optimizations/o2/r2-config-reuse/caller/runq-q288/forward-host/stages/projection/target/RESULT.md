# 真实 W1 与 classifier 尾部：目标边界结果

合同 [`r2-s3-projection-boundaries-v1`](CONTRACT.md)，所属操作 `20261027-LiZufan001-forward-stages-0300`。本页记录两个实际消费者边界，完整参考执行见 [原生结果](../../NATIVE_RESULT.md)，完整应用资格不由本页推导。

**最终状态：`PROJECTION_BOUNDARY_DIFFTEST_CAMPAIGN_PASS`。** 实际 campaign 于2026-10-27 05:33:27开始、06:37:46完成（UTC+08）；一份指定应用负控和三份正常运行均按合同结束，所有进程组已回收。官方DiffTest、完整输出、全部custom协议/PC序列及计数器链共同通过，三个正常validation完全相同。资格限本页两个具名目标边界。

## 1. 输入与比较范围

固定模型为 D288/H768/L6/heads6/kv6/GS32/V32000/S256、seed `0x53485041`，连续 tokens `[1,7,19]`。捕获程序从真实完整 forward 取得位置2的量化输入与输出，每位置全部16 spans与原样参考一致；原模型、embedding及三位置状态也与既有 `full-build-06` 逐字匹配。

| case | 实际边界 | 原完整 projection 块 | 有效输出行 | 每次调用的 Q288 数 |
|---:|---|---|---:|---:|
| 0 | classifier 行31680…31999 | 170、171 | 320 | 2 |
| 1 | 层索引5（从0计数，第6层）的完整 W1 | 39、40、41 | 768 | 3 |

两者使用各自真实量化输入，W1 输入不是 classifier 的末态 `xq`。五块 packed weights/scales 与完整 projection 参考程序的对应块逐字相等。尾块补零权重、scale=1，仍调用原完整288行内核，再复制有效行；没有改内核以跳过补齐工作。

同一 ELF 中 FR 与 TA 共用 input/packed/scales/output 地址。每个 case 的顺序为 FR、TA、TA、FR，每个样本先执行相同方法的完整边界作 selfwarm，比较全部输出，再重置输出并测量。窗口包含2/3次内核调用、context 构造、循环和尾复制；预量化、初始打包、selfwarm、输出重置、比较和 UART 在窗口外。

目标端每次检查全部有效输出字节、未使用 output 的 poison、补齐 tail 的 +0、完整128 B slots 及前后 guards。CSR 要求为 `vl=8/vtype=0/vstart=0/vcsr=7`；清零后的 `fcsr` 最终为1（NX）。FNV只帮助外部核对，不能替代这些完整比较。

## 2. 最终构建与失败保留

实际采用 `projection-target-build-02`：

| 对象 | SHA-256 |
|---|---|
| `projection-boundaries.elf` | `f4c047768c095e09e0335257bb743515f4d37861cca3e46bc008f580c01ecaa3` |
| `projection-boundaries.bin`，489704 B | `292c5012e4f7637aea7c8c68c595ee8129d6d38226378886f697b027037e8a7f` |
| `bad-tail.bin` | `e42ee1a94d6e303ad14c1fbd9726f1c07138c734bb3ad9747a6e6c851fa5740e` |
| 冻结 `run.py` | `35bcaef3443b17cfaaa8fbd3bf0149d090b67425d89ccb8d88b6063121cb598a` |
| `ta-custom-pcs.bin` | `f62aeb50a3dcf7335962fcac1760e34cc9b625c1dd0f6d98d695b424d3448088` |
| `model-results.json` | `a58c55d7b9952f14cbc272f34ec53100dfc3b30cb580689978c37a1ce8b5d07c` |

最终 ELF 中 FR 的592 B函数体、TA的764 B函数体分别与旧合格对象完全相同；五个真实块各执行两种最终 ELF 模型，共10条机器路径通过。TA每Q完整路径含10368条 custom，动态指令49602；FR为35670，且没有custom。这些静态/模型结果不替代目标运行，也不直接决定周期优劣。

四个计数器 PC 为 `0x80001378/0x80001384/0x800013a0/0x800013ac`，CSR顺序为 cycle、instret、instret、cycle。最终 ELF 逐条确认各读取两侧的 `fence iorw,iorw`。首版 `projection-target-build-01` 因 GNU `-Werror=misleading-indentation` 失败，修正只把对应 return 另起一行；失败原输入、编译命令和日志保留。

## 3. 实际目标运行

固定 T17、原 AM/NEMU/DiffTest；先单核应用负控，再用CPU0/1/2分别运行 normal/recovery/replay。每个进程限800万guest cycles、7200秒及每日志1 GiB。日志完整保留，未静音custom。

负控在 case0 第二个正式样本结束、尾复制完成之后翻转真实末输出 byte1276，按 `TILE_REJECT 0 1 result 1276` 拒绝。已完成两测量窗口、8条CSR链，但仅第一窗口打印样本；第二窗口在比较时退出。该进程8Q、4TA、41472custom、退出码1，进程组已消失。它证明指定应用输出破坏能被拒绝，不称作新的官方DiffTest架构差异注入；负控镜像的周期也不并入正常性能表。

三个正常进程均退出0，实际回收记录时间分别为 normal 06:31:29、recovery 06:31:27、replay 06:31:28（UTC+08）；之后在全部EMU回收完毕的条件下串行解析完整原文，06:37:46完成整批门禁。正常每进程40Q、20TA、207360custom，完整16次目标输出比较通过。

正常stderr各408,925,813 B，三份SHA完全相同：`ba06c41855938864aa47c19383ec877425400cb508f76e138787c8521a172788`。三份validation SHA同为 `171f1003100bc2d4551798e64006fef56e7234e4a5c91d56755c32aaf67d40ed`；stdout包含各自宿主运行信息，不声称三个stdout文件相同。完整custom退休PC序列SHA为 `c5b437edf6e0372e44ce00334c329ca1f16177d535cb54e4c7f7795673ebd4c8`。

运行器对最终 ELF 完整custom PC序列、全部 O2 协议、队列/ROB清空、banner/fatal、官方DiffTest和目标应用输出共同验收。同周期提交按真实ROB年龄排序，避免按printf行顺序误判。正常每进程8计时窗口和32条CSR链；全批包括负控共26窗口、104条完整CSR链。ACCEPT/MOVE/RESPONSE/ENQUEUE/COMMIT各事件的计数为正常每进程207360、负控41472、四进程合计663552；四个进程的pending、pending_div及unfinished_ROB均为0。

每条CSR链绑定实际ELF PC/word、enqueue/sample/retire、只读CSR、ROB身份、采样值到唯一退休值、emptyROB及时间顺序；cycle的模2^64差分等于独立全局观察周期差。已打印样本的cycle/instret均与UART一致；实际counter enqueue wait/block为0/0。仍保留 `full_retirement_window_audited=false`：本审计没有重建窗口中全部中间退休指令，不借用旧实验的完整退休路径或“+11”结论。

## 4. 周期解释与使用边界

以下是任一正常进程的完整八样本；另外两进程逐项精确复现，全部fcsr为1。classifier摘要为`2e1740514bd5f43d`，W1摘要为`b5107bba20e433a8`。

| 边界 | 样本 | 方法 | raw cycles | raw instret |
|---|---:|---|---:|---:|
| classifier最后320行 | 0 | 强FR | 162,279 | 71,551 |
| classifier最后320行 | 1 | TA | 146,392 | 99,415 |
| classifier最后320行 | 2 | TA | 146,792 | 99,415 |
| classifier最后320行 | 3 | 强FR | 160,178 | 71,551 |
| 完整W1 768行 | 0 | 强FR | 265,194 | 107,467 |
| 完整W1 768行 | 1 | TA | 239,986 | 149,263 |
| 完整W1 768行 | 2 | TA | 240,839 | 149,263 |
| 完整W1 768行 | 3 | 强FR | 263,456 | 107,467 |

| 同一边界内的派生观察 | classifier最后320行 | 完整W1 768行 |
|---|---:|---:|
| FR均值 | 161,228.5 | 264,325 |
| TA均值 | 146,592 | 240,412.5 |
| 均值周期减少 `1-mean(TA)/mean(FR)` | 9.078110% | 9.046628% |
| 最慢TA对最快FR `1-max(TA)/min(FR)` | 8.356953% | 8.584735% |
| FR锚点跨度 `max(FR)/min(FR)-1` | 1.311666% | 0.659693% |

这些是表内原值的算术比较，最慢/最快比较不是总体置信区间。TA的退休指令更多而周期更少，再次说明不能用静态指令数替代真实目标周期。

每个case只有一个固定输入和四个ABBA顺序样本；三次独立进程的精确重放验证确定性，不增加统计样本数。这里的ABBA观察没有继承旧QKV合同的1%锚点门槛，也不据此发布通用最优选择；需同时报告实际FR锚点变化和保守观察比较。

完整W1有效768行、实际计算864行，多12.5%；classifier最后320行实际计算576行，多80%。完整32000行classifier的补齐开销仅0.8%，不能把尾边界的比例当成整classifier成本。两个局部工作集的selfwarm也不能代表完整classifier约10 MB权重工作集。

因此这里只比较两个具名、已量化/预打包边界的完整调用周期。它不包含FP32量化、初始化打包、整个FFN/classifier、attention或完整token，不与RoPE约7.36倍局部比值相乘。强FR与原scalar保持回退，R5默认不变；完整 projection 的参考PASS仍不等于完整模型的香山DiffTest。

## 5. 原始证据与复算

原生运行根为 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/forward-stages-20261027-0300`。`projection-target-build-01/02` 保存失败与最终构建；`projection-target-campaign-01` 保存 source closure、179项主运行输入、进程回执、全部原始日志及逐进程 validation/protocol/counter/custom-PC。包含各run复制辅助文件后，交付前实际重核187项输入仍全部相同，回执在`projection-target-meta-01/post-run-inputs.json`。发布包、完整SHA和实际恢复回执见 [交付索引](../../evidence/index.json)。

计数器检查的六项实际破坏控制在 `projection-target-controls-02`：删除sample、非空ROB、错误word、采样/退休值不一致、虚假UART差分、observer中断fatal，均拒绝。首轮正则未真正改动指定输入的失败及原操作回执保存在 `projection-target-controls-01`。两目录已随 `rope-v1` 保留，不重复包装。

最终目标包含307个原始文件、1,820,791,241逻辑字节；ZIP为67,876,659字节，SHA `92e0ad39890bc428c04c1412e8b5dc336957bcf8fb860b3a16a82d9c2723d1ee`，以5片发布。完整恢复和原字节重组均通过。随后使用 [README](../../README.md) 中的v4 `recheck.py --kind boundary` 从冻结源复算，于06:47:18取得 `FROZEN_FORWARD_RAW_RECHECK_PASS`，在新输出中重建完整协议、custom PC与counter结果，并逐字/逐字段匹配旧结果。复算没有启动EMU或增加性能样本；实际回执与工具SHA见交付索引，原恢复与复算过程收进 `delivery-v1`。
