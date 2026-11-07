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

## 结论边界与接续

已经成立的是这个固定合成D288/H768/L6、共同prepare后首次p0/token1组合的**参考正确性**。目标正确性、完整应用周期排序仍未取得；formal-performance、full-retirement、ASIC PPA均false。正式LaTeX的dot8微基准、C8调用、旧FR/G/P及生产dot8面积/STA继续各自保留原范围，本次不替换它们的数值。

下一步读取唯一在途操作的真实终态，核四臂完整原日志、DiffTest、GOOD TRAP、全过程输入及资源清理，再用本次较快合格RVV作分母报告实测收益。若失败，保存原始失败并按具体原因决定修复，不自动扩预算或重跑。稳定默认入口未切换，无部署。
