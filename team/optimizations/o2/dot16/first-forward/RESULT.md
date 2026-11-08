# dot16 四臂完整 forward：两套镜像目标正确性均已闭合

**当前状态（2026-11-08 UTC）：旧W与新N实验各自四臂正确性、DiffTest及进程回收已闭合；同镜像较快对照的观察倍率分别为1.156325×和1.196049×。TRACE0正式性能资格仍为false。最新终态与证据见本文最后两节；下面早期“在途”文字保留为历史检查点。**

合同：[CONTRACT.md](CONTRACT.md)，`r3-dot16-first-forward-v1`。身份与状态索引：[REFERENCE.json](REFERENCE.json)。

**2026-11-07 UTC 状态：新共同镜像及五项参考验证 PASS；P/PQ/D/DQ 整核目标正在运行，尚无目标周期或正确性结论。** 本轮接续 2026-11-06 的源码准备，实际执行 `prepare.py`、GNU 构建、参考检查、目标准备和 profile 冻结。人工已允许继续工程及针对未执行过期命令重新准备；旧 P/PQ 超时案独立保留，不重放。

## 候选选择与比较含义

[whole2 同镜像 Q288 筛选](../whole2/q288-consumer/RESULT.md)真实通过，W 对 plain D 的平均周期降低15.7665%，两种顺序均改善；选定原完整412B whole2函数进入此新共同程序。本案 D/DQ 的 D **表示选定 whole2**，与 Q 筛选里表示 plain dot16 的 D 标签不同。

| 臂 | K288 矩阵乘 | 激活量化 |
| --- | --- | --- |
| P | paired16 RVV | 原 helper |
| PQ | paired16 RVV | 既有 Q helper |
| D | whole2 dot16 | 原 helper |
| DQ | whole2 dot16 | 同一 Q helper |

四臂 W2 矩阵乘均保留 FR。共同 ELF 保留 FR/G 兼容方法，实际参考集合是四个正例和一个 DQ 反例，目标集合只有四个正常臂。

最终主要比较为本次合格臂 `min(P,PQ)/min(D,DQ)`；同时列 P→PQ、D→DQ、P→D、PQ→DQ、P→DQ 的条件比较，保留全部结果，不预设量化一定更快，不相加百分比。旧 FR/G/P 或旧 P/PQ 的周期不作为新 D/DQ 分母。新四臂不包含 plain D，因此不能据它声称 whole2 相对 plain D 的完整应用增量。

## 已完成的实际验证

- GNU 构建 2026-11-07 09:50:01.7261944Z–09:50:09.2450105Z，操作 `49cbde030e5643f0cccfca5cec8a79c1.1714bcef168071c597e05d965e02f303`，exit0、cleanup_complete=true。共同镜像77,124,000B，`FIRST_FORWARD_DOT16_STATIC_PASS_NOT_RUNTIME`。
- 实际完整函数 W 的412B SHA与 Q 筛选和原 whole2 ELF相同。P/D各七处K288路线、每臂W2的FR路线、各五处量化、实际selector→entry→clone、共同四CSR与fence已经静态核对；不把静态路由计数称为动态调用数或退休证据。
- 新参考操作 `49cbde030e5643f0cccfca5cec8a79c1.c2e74675a5a5888ff21fe614129be653` 完成五案，`FIRST_FORWARD_DOT16_REFERENCE_CAMPAIGN_PASS`。四个正例完整比较3,691,424B state，并核模型/gold、guard、TLS/errno和FCSR；DQ负例被同一比较器以 `complete_state_mismatch position=0 byte=152476` 拒绝。
- 五个reference PID386/387/398/399/400分别exit2/0/0/0/0，真实reaped、process group absent；未把故意反例的exit2改称正例成功。参考执行不能证明香山周期性能。

| 参考臂 | 窗口 instret | 状态 |
| --- | ---: | --- |
| P | 5,175,372 | 完整参考 PASS |
| PQ | 4,784,314 | 完整参考 PASS |
| D | 4,995,116 | 完整参考 PASS |
| DQ | 4,604,057 | 完整参考 PASS |

这些数来自实际报告 `report[18]-report[17]`，只说明参考执行的指令观察。NEMU周期不是香山周期，目标数据仍待完成。

## 在途目标与固定资源

[RUN BEGIN 6705355479](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6705355479) 已登记回读。唯一宿主操作：

`49cbde030e5643f0cccfca5cec8a79c1.1b999cf43afaaebd09ab95c1e9fd28cd`

宿主开始于 **2026-11-07T10:00:28.8813534Z**。逻辑operation为 `f3ec0e2f-4dc5-4d18-a8a7-4b7ec375e217`。初始实际进程读回 P/PQ/D/DQ 分别为 EMU382/383/381/380、CPU0/1/2/3，各1线程；四核总预算，无额外guest。

| 范围 | 一次冻结的上限 |
| --- | --- |
| 每个正常臂 | 40,000,000 guest cycles；43,200秒；每路raw文件16MiB |
| campaign work / TERM grace / hard | 45,000 / 300 / 45,600秒 |
| Windows外层工具 | 57,600秒 |
| 运行方式 | 4 slots、1 wave；无自动重试或预算扩展 |

上限不是预计耗时，成功即收尾。完整状态比较的尾段必须完成，不能以提前出现的计数行当作PASS。采用既有P/PQ owner的原控制函数、TERM/KILL/reap和实际清理回执，新的目标源仅有限派生四臂与TRACE0审计。全日志原有64KiB行/16MiB完整文本边界保持；完整UART的64位CSR观察与静态计时位置分别留证，未采集CSR退休关联或custom退休计数。

686项实际输入已固定，四个正常镜像只有selector四字节范围不同；固定EMU/feature1 NEMU/flash与1400B ABI保持。运行中的输出、profile与所有父输入受保护，Windows正式报告修改独立保留。

## 关键身份与工程入口

| 实物 | SHA256 |
| --- | --- |
| 共同 ELF | `5ba0cd0756a16f38c2747c625bf8fb53d5ba4c9ba9b2bbf222c146df4859b959` |
| 共同 BIN | `359587450bc0630f5dd3128f66f871f43a467fea21c5f1db24194e7230dd2afc` |
| build result | `d933cd08c8815bddbcfffad731beafd426fa01623a997268802065054e234683` |
| reference results | `21dc99a65b9d8d20a99dd71186a0e19980c2de3ca3f05ec30f8c356ec99ac5b4` |
| target controller binding | `29feddc9acb3b4d0c57d466a52ff5d23353be94a567b137406f0cdde3bae9578` |
| 固定 resource profile | `b650534b8c14fe3ecb813232be47decc3a550e279352859c7ec4a1d4d4046d0b` |

原件统一位于常驻WSL `runs/dot16-first-forward-20261107-main/`：`controller-01/`、`build-01/`、`reference-01/`、`target-controller-01/`、`resource-01/profile.json`；在途 `target-01/`、`owner-01/`。完整绝对路径及回执在REFERENCE.json。运行闭合后再归档目标原始证据，当前文件保存不等于发布或独立复现。

## 2026-11-07：N候选已接入准备入口，未启动新forward

原四臂仍使用上文whole2共同镜像和原operation。公共 `prepare.py --kernel` 新增显式选项 `narrow`，登记[固定Q288已通过的N](../whole2/NARROW_Q288_RESULT.md)，并在原符号白名单增加 `q288_dot16_whole8_narrow`。原plain/whole2表项、父输入pins、硬件、方法字、MAGIC与选择器规则保持；没有新增派生层或切换默认入口。

**实际完成一次source-only准备，状态为 `FIRST_FORWARD_DOT16_CONTROLLER_BOUND_NOT_RUNTIME`。** ChatPC operation `49cbde030e5643f0cccfca5cec8a79c1.95ab816dfd09b4496fc74f7ab4166a43` 于14:29:08.7395759Z启动，外层5.002s、exit0/cleanuptrue，无超时或取消；Python准备14:29:10.225131Z–14:29:13.521183Z，CPU1/nice5。未执行GNU、reference或目标EMU；`new_build_runs=reference_runs=target_emu_runs=0`、`target_cases=[]`、`performance_qualified=false`。

输入使用真实冻结父P/PQ准备器、原config/base/quantize/hardware，以及N的实际 `image-01/source/fused.S` 和 `paired16-target.elf`。N完整函数312B、SHA `050bc3db3e2a70bd6e5409cbf9c139868008e8ccb18776b7e0e7104e6a554b75`；汇编来源和ELF身份与N固定Q记录相同。既有提取格式另作只读检查，完整函数在来源文件尾部唯一；新forward中的函数提取、GNU机器码相等和运行正确性尚未执行。

| 本次准备实物 | SHA256 / 范围 |
| --- | --- |
| 公共prepare.py | `e6f8149f2471d1ca3688583dcc64a3e5e0345552b6900fdad2c39832c9e595b7` |
| 公共derive_extension.py | `b6aa50371a908573450f884e8fc43da33f226cb0f866228811cf6630cc62c0a1` |
| 本次合同快照 | `735df8d8053f6ff948135cd4f6b2188138d751b1f0ad9e1842ca59a44166ea59` |
| 新binding.json | 88,411B；`f67ed9e3831ecd58748ec9bcb23565ff38ce95b566a88cc1d746836306a66364` |
| 输入与输出闭合 | 94项输入pin；80件generated文件读回一致；顶层无run.py/audit.py |
| 原四臂profile | 前后仍为 `b650534b8c14fe3ecb813232be47decc3a550e279352859c7ec4a1d4d4046d0b` |

原件位于 `runs/dot16-whole8-narrow-q288-20261107-main/` 的 `forward-source-01/`、`forward-controller-01/`、`forward-prepare-01/`。本次[原始准备归档](narrow-source-prepare-20261107.zip)包含87原始文件、91成员，474,080B，SHA `429e247cd150fdddf5bc0a41996db582b6ba36ef0ba9b80e0c6e90bc39e27130`；CRC、逐成员SHA、来源前后字节及独立文件读回通过。含原调用脚本、参数、终态回执、完整控制器与manifest；外部94项输入仍按binding指向原冻结实物，本ZIP不是自包含运行镜像。

本次prepare核对了输入身份、控制器变换的逆向证明和Python语法，未执行 `derive.core/main`。生成的四个正常参考臂和DQ负例只是模板配置，不表示已运行或选定下一轮目标矩阵；D/DQ共用一个内核的现有接口也不自动提供同ELF的W/N比较。先取得原四臂终态，再确定固定量化的W/N比较或保留较快RVV的有限新实验。没有把N的Q局部6.90%收益、这次绑定结果或旧ELF周期升级为N完整应用结论。

## 结论边界与接续

已经成立的是这个固定合成D288/H768/L6、共同prepare后首次p0/token1组合的**参考正确性**。目标正确性、完整应用周期排序仍未取得；formal-performance、full-retirement、ASIC PPA均false。正式LaTeX的dot8微基准、C8调用、旧FR/G/P及生产dot8面积/STA继续各自保留原范围，本次不替换它们的数值。

下一步读取唯一在途操作的真实终态，核四臂完整原日志、DiffTest、GOOD TRAP、全过程输入及资源清理，再用本次较快合格RVV作分母报告实测收益。若失败，保存原始失败并按具体原因决定修复，不自动扩预算或重跑。稳定默认入口未切换，无部署。

## 2026-11-07：N 与 K768 N/P 已完成完整应用 GNU 和参考验证

新实验合同为 `r3-dot16-first-forward-w2np-v1`，权威源码入口在 [w2-np/W2_CONTRACT.md](w2-np/W2_CONTRACT.md)。本节是独立的新共同镜像；上文 P/PQ/W/WQ 实验已于18:09:29 UTC结束；原 operation、输入、预算和结果仍保持独立归属。新实验的 `dot16`/`dot16_quantize` 方法字分别表示 N/NQ，不能与上文 W/WQ 标签混用。

| 臂 | 七处 K288 | W2 的 K768 | 激活量化 |
| --- | --- | --- | --- |
| P | paired16 RVV | paired16 RVV | 原 helper |
| PQ | paired16 RVV | paired16 RVV | 同一 Q helper |
| N | whole8 narrow dot16 | whole8 narrow dot16 | 原 helper |
| NQ | whole8 narrow dot16 | whole8 narrow dot16 | 同一 Q helper |

接入只改变四个既有 clone 的 W2 路由，并加入已实际通过 K768 数值/末组边界/负控参考验证的完整 N/P 汇编函数。保持七处 K288 调用、五处量化、FP 运算次序、模型及层数、56B context、221184B packed W2、方法字和四 CSR 测量窗口。旧 FR/GS32 与兼容 TA 入口保留。逐项逆向变换恢复完整旧源码，最终 ELF 中 K768 N 的312B及 P 的1096B与实际 GNU 和参考 ELF 逐字节一致。

### 实际完成的验证

准备器产出86个生成文件并绑定295项输入，binding SHA `e4ccd6e74c31a8b30e9b89088067a5e7364a67f0a2d3e2530ab2eed9bbc687a9`。GNU 阶段内部实际时间17:40:46.054450–17:40:57.908744 UTC，host operation `49cbde030e5643f0cccfca5cec8a79c1.6d7a9c466be394ee701325144fcb810d`；10个命令全部exit0，得到 `FIRST_FORWARD_W2NP_STATIC_PASS_NOT_RUNTIME`。

最终机器码中，四个正常 clone 的8处 kernel-pointer 调用均逐点核对。W2 selector 的76B实际指令片段对 FR、P、N、有效旧TA四个固定输入分别指向正确 K768 函数；并核 incoming a5 到callee-saved x20的唯一复制、支配关系、相关路径上的寄存器保留及外部跳转边界。检查依赖通常 RV64 调用约定，不宣称任意指针或全程序形式化证明，也不把静态8调用称作动态退休次数。

参考阶段内部实际时间17:42:49.056044–17:43:17.465758 UTC，operation `49cbde030e5643f0cccfca5cec8a79c1.5a0ad3cf304ce8170048f04b75e921a1`；五例由原完整 reference/validate 检查，结果 `FIRST_FORWARD_W2NP_REFERENCE_CAMPAIGN_PASS`。原 reference.py 12,537B，SHA `586fdc74ccfdb640ec30703ec9efab048fc9a19048a679dd5d20dcdc3a363ad7`，逐字节未改。仅使用 [run_stage.py](w2-np/run_stage.py) 的有限命令/进程包装，CPU1、nice5、单worker，GNU总预算1200s、reference3600s。

四个正常臂完整3,691,424B state与同一gold相等，两侧共32B guards、96B TLS、errno=12345、flags/FCSR=1及六项完整模型/gold dump保持。正常 `guarded-state.bin` 均SHA `027e4200fcbbd6453806591c355b616df27acbd219d4008d24893ac685bd814a`。负例先运行，在预设byte152476处被原比较器拒绝，BAD TRAP94/PC0x80002a74；负例仍执行完整forward，不应说它在forward之前终止。正常均GOOD TRAP0/PC0x8000013c。

| 参考臂 | 窗口 instret（report[18]−report[17]） | 窗口外总退休数 | 完整状态 |
| --- | ---: | ---: | --- |
| P | 4,958,760 | 3,693,394 | PASS |
| PQ | 4,567,702 | 3,693,394 | PASS |
| N | 3,239,096 | 3,693,394 | PASS |
| NQ | 2,848,037 | 3,693,394 | PASS |

这些是参考模型的指令观察，不能当作香山周期或应用加速比。15个外部命令/参考进程全部回收，进程组消失；两阶段各480项固定输入前后SHA复核一致。独立只读审查再次核全部实际state、寄存器/CSR/report、镜像12B控制差异、输入清单覆盖和原始trap日志。GNU保留原忽略OpenMP、未使用prev_token、上游chat可能未初始化next的警告，未改官方上游代码；五例reference stderr全空。

### 身份、原件与目标入口

| 实物 | SHA256 |
| --- | --- |
| 共同 ELF（74,849,960B） | `62a73b9d16cea43ad03eec3ec09b27edfab7da90ce895d33baa72bf9d84723c4` |
| 共同 BIN（77,125,408B） | `fcc05cf2d1ccd2cc80c74e259d007da86b7758a626f58b7cb63dc6793c698365` |
| GNU result.json | `3d855fa040c05c91e079a5b7c52e6ce783510332369e297150f301fb3d64b4c7` |
| reference results.json | `181145ca820ed345bcb2a0f319e8d3af200ee9e1602d2589f7721b6c4a93f983` |
| 新 target-controller binding | `11925922dc1faf7a8a03b97f368e28cf260c2f53ff304369370867316548eb69` |

原件位于常驻WSL `runs/dot16-w2-forward-20261107-main/{controller-01,build-01,reference-01,target-controller-01}`，Windows同名runs目录保留三组冻结源码。`prepare_target.py`/`launch_target.py`只对原入口作workload/resource/status字面身份变更，逆向可恢复原文件；保留原owner、检查器和进程回收。目标准备operation `.143b812d121fa2d1a646b816da452d05` 实际exit0/cleanuptrue，**未冻结新resource profile，未启动新EMU**。目标合同见 [TARGET_CONTRACT.md](w2-np/TARGET_CONTRACT.md)。

原四路operation `.1b999cf43afaaebd09ab95c1e9fd28cd` 已于18:09:29 UTC实际完成，exit0、cleanup_complete=true，四个目标正确性PASS且CPU资源回收；TRACE0性能仍为UART观察，未收集完整退休窗口证据。接续本新镜像前仍须冻结实际profile及核实时资源；不要重放或扩大旧预算。本新实验的主要比较为同ELF中合格的 `min(P,PQ)/min(N,NQ)`，保持较快合格RVV分母。新的reference PASS不转移到在途旧镜像，也不把旧目标结果转移到本镜像。稳定默认入口未切换；无新signed8整核构建或应用性能资格。

[原始完整应用证据 raw.tar.zst](w2-np/raw.tar.zst) 为 **31,715,244B**，SHA `7c7c792c2a38238ee1bd58f3b30b9a9d4bb02994c68ab960f7bfa81aec6cd5dc`，含546个文件、1,020,793,811B原始内容。用标准tar/zstd保留新共同ELF/BIN、全部五份实际参考镜像和完整原始dump，不用补丁替代原始数据。仅省12个可重建build对象，原件未删除；所有archive member的长度/SHA、源文件前后字节与归档进程回收均核验。外部仓库、工具链及历史冻结输入按manifest定位，不宣称单包自含全部环境。解包到新目录可用：

```sh
tar --use-compress-program='zstd -d --long=29' -xf raw.tar.zst -C /absolute/fresh/restore
```

## 人工50%目标的工程测算（不修改正式LaTeX）

依据当时当前 `team/submission/latex-v1/sections/stage3.tex`（SHA `6b2bfc3d343b2b41639b9b3cee7db095bdc92d964205f551354a1546aae51dc3`）和 `team/optimizations/o2/r3-div-gate/performance/results/samples.csv`（SHA `ad0577b1908e99b84d7a1e6016f28efb46b096b49c5ce46a48cd96e05fe8a18f`）核算。下面按CSV中after且纳入统计的12个窗口计算。若保持同一参考周期R，要求旧加速倍率R/V再乘1.5，新的VDot周期必须≤原V的2/3；这与周期减少50%不同。

| 旧dot8场景 | VDot周期V | RVV周期R | R/V | 倍率再×1.5要求的新V上限 |
| --- | ---: | ---: | ---: | ---: |
| 单发 | 71 | 85.25 | 1.200704 | 47.333 |
| 256依赖链 | 1,857 | 5,440.5 | 2.929725 | 1,238 |
| 128点吞吐批次 | 221 | 678 | 3.067873 | 147.333 |
| 64项流式 | 1,127.5 | 1,133 | 1.004878 | 751.667 |

59-cycle空窗口是另一个实际镜像的观测，不是可直接扣除的开销或跨镜像形式化下界；单发47.333目标比这一观测还小，因此不能承诺仅靠改FU达成。依赖链要看完整issue/read/execute/writeback/wakeup环，不只是FU的E2。当前II1下128个点乘的理想服务数已有128拍量级，吞吐批次147.333的目标余量很紧；不能机械地把空窗口59与128相加。流式包含load/store/地址/分支，接近1x不能单独证明有或没有50%优化空间。旧dot8表和新dot16 Q288/完整应用必须分别核验。

对局部P→N的实测Q288比例 `s=43473/26275=1.6545385`，Amdahl计算 `S=1/(1-p+p/s)` 的p必须是真实应用时间占比；达到整体1.5x要求p至少84.2598%，不能用MAC数或指令比例替代。对已优化W→N的局部 `s=28222.5/26275=1.0741199`，即使p=1也只有7.4120%的这一项增量。当前新W2接入扩大了优化覆盖，但仍要等实际同ELF目标周期，不能将参考指令减少、局部内核周期、FU面积下降相乘成为整应用性能结论。**本轮没有宣称全部旧倍率再提升50%，也没有宣称实际FU面积已≤20000。**

## 2026-11-07：原 P/PQ/W/WQ 四臂目标已完成并保存完整原件

本节接续原合同 `r3-dot16-first-forward-v1`，只更新其已闭合目标状态；共同 ELF 仍为 `5ba0cd0756a16f38c2747c625bf8fb53d5ba4c9ba9b2bbf222c146df4859b959`。上文“目标未取得”描述的是较早检查点，不再代表这一旧实验的当前状态。本节的 W/WQ 不是新共同镜像 `62a73b9d…` 的 N/NQ，不能跨镜像拼接分母。

原 host operation `49cbde030e5643f0cccfca5cec8a79c1.1b999cf43afaaebd09ab95c1e9fd28cd` 实际从2026-11-07T10:00:28.8813534Z运行至18:09:29.8473281Z，exit0、cleanup_complete=true。对应逻辑 operation 为 `f3ec0e2f-4dc5-4d18-a8a7-4b7ec375e217`；没有为补报告重跑目标，也没有扩大原预算。

### 正确性与同镜像窗口观察

四个原始目标均得到 `FIRST_FORWARD_DOT16_TARGET_DIFFTEST_PASS`：原 DiffTest、完整3,691,424B state比较、固定程序flags==1门、三条完整CONSUMER记录及GOOD TRAP0/PC0x8000013c通过；四路stderr为空。各直接子进程均回收、进程组消失，原owner/campaign完成且固定输入未变。原目标摘要为 `FIRST_FORWARD_DOT16_TARGET_OBSERVATIONS_COMPLETE`。

| 原实验臂 | UART CSR窗口cycles | UART CSR窗口instret | EMU guest总cycles |
| --- | ---: | ---: | ---: |
| P | 17,378,319 | 5,175,372 | 23,962,961 |
| PQ | 16,594,945 | 4,784,314 | 23,178,721 |
| W | 15,139,851 | 4,995,116 | 21,724,206 |
| WQ | 14,351,452 | 4,604,057 | 20,934,496 |

完整64位counter_hex按整数差分核算，不能经过浮点JSON转换再回写原值。四路窗口instret另与原参考报告的report[18]−report[17]逐项相等；该一致性不是独立CSR采样时点证明。原始窗口与guest总周期范围不同，不能混用。

在这次同ELF、同硬件、同输入的四臂集合内，较快RVV为PQ、较快dot16为WQ；其**观察倍率**为 `16594945/14351452 = 1.1563251579003992`，窗口cycles减少13.5191348932%。这覆盖固定合成D288/H768/L6模型、按合同准备后的首次p0/token1完整forward；不含模型准备，也不代表真实模型、多token端到端或其他工作负载。

原资格字段继续原样保留：

- `target_correctness_qualified=true`；
- `counter_retirement_verified=false`、`full_retirement_window_audited=false`、`performance_qualified=false`；
- custom动态退休与事件协议为 `NOT_COLLECTED_TRACE0`。

实际TRACE0没有四CSR入队/采样/退休关联和完整有序窗口记录，不能从静态函数、DiffTest或instret总量相同追溯补出。上述限定的观察可用于优化方向判断；缺失的扩展资格不自动成为所有下一项优化的新增阻塞条件。它不改变已有dot8正式微基准、参考正确性或此前局部Q结果的适用范围，也没有达到“旧倍率再×1.5”的结论。

### 真实原件与可复现入口

| 实物 | 字节数 / SHA256 |
| --- | --- |
| 原campaign-results.json | 21,791B；`1b1a1532d74387f2b211a82e51ca1b872a074693f7172e1b875170afd354f1a8` |
| 原resource profile | `b650534b8c14fe3ecb813232be47decc3a550e279352859c7ec4a1d4d4046d0b` |
| 原目标EMU | `f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d` |
| [完整目标原件 raw.tar.zst](target-20261107/raw.tar.zst) | 26,365,231B；`809a93b5a44f899145b6833e34758c3bf0eb6ed235815c1ee8bb7b6bcaa9b8b8` |

归档包含179个文件、310,807,901B原始内容，保留全部四份完整目标镜像、原stdout/stderr、验证结果、原owner/campaign/profile、执行回执、独立counter复核和归档控制器。没有省略文件，没有修改原目录，没有将原始数据替换为可重建差分。每个成员长度/SHA、源文件集合和前后字节、原完成/进程清理、镜像控制字与原日志均核验。

归档操作 `.f60eb58b75929330be455ebb9a274d45`（同host前缀）于18:46:31.9420683–18:46:51.4654244 UTC完成，exit0/cleanuptrue；只验证运输完整性，没有新guest、构建或性能资格。原件保留在常驻WSL `runs/dot16-first-forward-20261107-main/{target-01,owner-01,resource-01}` 及Windows同名runs的 `target-owner-01`、`archive-target-source-01`、`archive-target-01`。标准解包命令：

```sh
tar --use-compress-program='zstd -d --long=29' -xf raw.tar.zst -C /absolute/fresh/restore
```

外部冻结源、EMU、参考模型及工具链仍按原manifest定位；本包不宣称包含全部开发环境。

### 新 N/P 实验的独立运行状态

新共同ELF `62a73b9d…` 的P/PQ/N/NQ目标已在完成自己的GNU/原参考验证后另行启动。新profile `5574eb19932197186f9ea587020bc6909a6142ad7169f886b7d93eb90d5d2575` 绑定863项输入；四份77,125,408B镜像只在方法字的4B处不同，保留同一EMU和原检查器。CPU0–3各一例、原40M guest cycles/43,200s/16MiB日志上限，未扩大原单例预算。

新host operation为 `49cbde030e5643f0cccfca5cec8a79c1.ed135ec164a525ededcc42c31676ba4a`，2026-11-07T18:21:18.276683Z启动；逻辑operation `3eaaab12-1f79-42b3-86d9-586bdebd642c`。19:21 UTC原status回执仍为running，尚未取得新目标终态或周期排序。这个状态只说明当时的原作业，不把旧四臂PASS或周期转给新镜像。后续沿原operation读取状态，不能因会话更换或工具暂时失败而重复启动。

## 2026-11-08：新 P/PQ/N/NQ 四臂目标正确性闭合，观察倍率1.196049×

本节更新独立合同 `r3-dot16-first-forward-w2np-v1` 的实际终态。共同ELF仍为 `62a73b9d16cea43ad03eec3ec09b27edfab7da90ce895d33baa72bf9d84723c4`，共用BIN为 `fcc05cf2d1ccd2cc80c74e259d007da86b7758a626f58b7cb63dc6793c698365`。上文的新N“在途”记载属于较早检查点，不再表示当前运行状态；旧W/WQ实验保持自身身份与结果。

原host operation `49cbde030e5643f0cccfca5cec8a79c1.ed135ec164a525ededcc42c31676ba4a` 从2026-11-07T18:21:18.276683Z运行至2026-11-08T01:26:19.2622268Z，状态succeeded、exit0、cleanup_complete=true，无取消或超时。逻辑operation仍为 `3eaaab12-1f79-42b3-86d9-586bdebd642c`；原40M cycles/43200s单例与45000/300/45600/46200s owner边界没有延长，未重启或补跑。

### 原始目标结果与比较

四路均为 `FIRST_FORWARD_W2NP_TARGET_DIFFTEST_PASS`，campaign为 `FIRST_FORWARD_W2NP_TARGET_OBSERVATIONS_COMPLETE`。原DiffTest、完整3,691,424B state比较、guards与约定CSR门、flags=1、三条完整CONSUMER记录和GOOD TRAP0/PC0x8000013c通过。四个原EMU407–410及对应launcher已回收，进程组消失，固定输入未变；Issue #2的6715717931记录了原运行资源释放，冻结证据继续保留。

| 本次同镜像方法 | UART窗口cycles | UART窗口instret | EMU guest总cycles |
| --- | ---: | ---: | ---: |
| P | 16,920,555 | 4,958,760 | 23,504,848 |
| PQ | 16,129,141 | 4,567,702 | 22,713,500 |
| N | 14,276,120 | 3,239,096 | 20,860,018 |
| NQ | 13,485,355 | 2,848,037 | 20,068,095 |

四路counter_hex、原始stdout与validation逐项一致，完整64位数使用整数差分复核；没有经过浮点JSON往返后改写原件。窗口instret与此前该镜像的参考观察分别一致，但这种一致性不补出CSR退休关联。窗口周期和EMU guest总周期是不同范围。

比较仍取本次同镜像、同硬件、同输入的较快合格RVV：PQ比P快，NQ比N快，故主观察为 `16129141/13485355 = 1.1960486765087015×`，窗口cycles减少16.3913626894%。工作负载仍是D288/H768/L6固定合成模型、合同准备后的首次p0/token1完整forward；模型准备不在窗口内，不等于真实模型或多token端到端性能。

新实验将K288与K768同时接入N/P路线，RVV和dot16两侧都改变。因此不能用旧W实验更慢的PQ 16,594,945作为新NQ的分母，也不能把两次实验的倍率相乘、全部归于硬件或与prefix面积组合。旧同镜像PQ/WQ为1.156325×，新同镜像PQ/NQ为1.196049×，分别留证。

资格原样保留：`target_correctness_qualified=true`；`counter_retirement_verified=false`、`full_retirement_window_audited=false`、`performance_qualified=false`；custom退休与事件协议仍为 `NOT_COLLECTED_TRACE0`。原完整退休窗口未采集，不从静态源或DiffTest倒推出正式性能资格；这一额外资格边界也不自行升级为其他优化的新阻塞门槛。现有证据没有证明人工提出的旧技术文档各项性能再提高50%。

### 终态摘要、原件与后续采用

录制方于01:53 UTC明确解除临时避让后，已完成[完整原始目标归档](w2-np/target-20261108/raw.tar.zst)：**26,374,766 B**，SHA256 `cff9a569518a6437b5bb6f14f847b684debb6ded53b03159b7d7e142337fb66d`，179个文件、311,076,225 B原始内容，零省略。包含全部四份原image.bin、完整stdout/stderr、原campaign/owner/profile、归档源与原host回执。完整归档与下面的轻量终态摘要用途不同。

原归档host `0250d6044ba18f5fd71831ae3131d2ce.a0334be27653c6dc0d1ba03d406580ee` 于01:55:40.7393972–01:55:46.0261094Z闭合，exit0/cleanuptrue；内部create与流式verify两子进程均回收、组消失。CPU1/nice5、tar/zstd单线程、600秒总上限，实际3.508秒；源集合/前后SHA与每个归档成员均核验，所有原件保留，无新guest/build。此运输不增加目标功能或性能资格。[archive-audit.json](w2-np/target-20261108/archive-audit.json)保留实际回执；标准解包为 `tar --use-compress-program='zstd -d --long=29' -xf raw.tar.zst -C /absolute/fresh/restore`。

| 实物 | 字节数 / SHA256 |
| --- | --- |
| 原target results.json | 21,805B；`13c45f846a8a26ad27996c6cd41faabd942da541131282f024c09dd5bb7e38f0` |
| 原target state.json | 12,672B；`10f2a7a4d09ecfcecdec77cabbd8bb2b96cf3a08214c03e3a43479bc8b90f79c` |
| 原owner state.json | 5,403B；`0c179518076d6b23cbf4b77926a1a7f3161a63a1929fd05b47714be7ef5bab4c` |
| 原profile | `5574eb19932197186f9ea587020bc6909a6142ad7169f886b7d93eb90d5d2575` |
| 原目标EMU | `f14918658fcd2f19c9fb6c1d493025d98f727ac985ea73129edc58270fa6977d` |
| [终态摘要 summary.zip](w2-np/target-20261108/summary.zip) | 23,290B；`011a48db16cb5a4656298bca724961e4a4f7b997ec1e9d5bee3002ad41ab23c1` |

摘要包含16个成员、78,031B原始内容：原campaign/owner/host终态、四份完整stdout及validation、只读整数复核器和其结果、成员清单。所有成员逐字节读回，原results/state/owner的完整SHA与原owner/host相符。摘要不包含四份完整目标镜像、空stderr文件、原resource profile或全部环境，不称作完整运行归档。

完整原件继续保留在常驻WSL `runs/dot16-w2-forward-20261107-main/{target-01,owner-01,resource-01}`；Windows同名runs的 `target-closure-01` 保存上述摘要原件，`archive-target-source-01` 保存有界完整归档入口和原host回执。录制保护期间未启动新的重构建、仿真或大内存压缩。摘要只是运输与复核，不重跑guest/checker，不增加资格。解压到新目录后，`python3 -B audit_closed_summary.py` 可重算摘要中的原始整数关系；它明确不验证缺席的目标镜像或完整环境。

本次工程交接优先保留NQ和同镜像PQ对照，旧W/WQ及原RVV入口继续作为回退参考。该选择限于已验证的固定工作负载；不因此切换生产默认或声称任意应用收益。prefix仍另需独立整核验证，packed-Ws仍只有其局部完整调用结果。代码和对当前技术PDF的指标说明统一见 [工程交付](../../../../evidence/dot16-engineering-delivery-20261108/README.md)，正式PDF/LaTeX由人工维护。
