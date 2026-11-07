# dot16 四臂完整 forward：参考通过，目标运行中

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
