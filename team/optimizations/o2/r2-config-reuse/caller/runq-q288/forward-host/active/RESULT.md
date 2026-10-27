# 活动 forward 状态接续结果

合同：`r2-s3-runq-active-forward-v1`。本轮在未修改的上游参考之外建立独立团队消费者，TA 与 FR 使用各自的激活、临时缓冲和持续 KV cache。两候选每次投影运行已合格 RISC-V ELF 的完整函数模型，再把该模型的实际输出写回状态；不是把独立算术 golden 写进消费者。

## 已证实的范围

固定未训练确定性模型 D288/H768/L6/heads6/kvheads6/V32000/seq256/GS32，tokens `[1,7,19]`、positions `[0,1,2]`。权重来自原有工程夹具；不包含真实训练 checkpoint 或质量评价。

| 项目 | 本轮结果 |
| --- | --- |
| 原参考 | 上游文件完整 SHA-256 与旧观察器 SHA-256 均保持；派生 forward 除明确函数名/包装/四类调用点外的完整源码文本与顺序相同 |
| 候选状态 | Reference、TA、FR 三套 RunState，16 类可写缓冲完整范围两两分离；权重只读共享 |
| 正常实际 ELF 调用 | TA 72 次、FR 72 次，共 144 次完整 Q/K/V/O、41,472 个输出 |
| 完整接续 | 每方法每位置的 32,000 logits，以及全部 6 层×256 行×288 元素 key/value cache，均与原参考逐字节相同 |
| 历史/未来状态 | 每次仅当前位置 KV 行变化；其余行、权重、embedding 与持久 packed 权重均逐字节保持 |
| 每次完整 forward | 24 个 QKVO 候选调用＋19 个其他 matmul，25 次量化、315 组、10,080 元素；reference 另确认13 RMSNorm/36 softmax |
| pack 生命周期 | 24 份权重各 pack 一次，1,990,656 B，跨位置复用 |
| 目标执行 | 本项新增 EMU 0 次；完整目标 QKV 作为[独立合同](target/CONTRACT.md)验证 |

每次候选回调都检查实际 ELF 数值、完整输出、末槽高位、精确读写范围、只读输入、普通 ABI、CSR 与 FP 顺序。回调前把全部 288 输出置 NaN，完整覆盖才允许消费。候选使用自身激活执行原样量化；每层 Q/K/V 共用同一次量化的 x/xs，O 在 attention 之后另行量化。这种 QKV 共享本来就存在于上游，不能记作本轮新优化。

## 消费前负控

负控在实际 ELF 的局部检查已经通过、输出即将参与模型状态时注入。正常与三个负控分别使用新进程和新状态。

| 控制 | 位置 0 | 位置 1/2 | 判定 |
| --- | --- | --- | --- |
| K[0] 加 8（层0、位置0） | 完整 key cache 不同；单位置 softmax 下 logits 仍相同 | logits、key、value 均不同 | 历史 K 被后续 attention 实际消费 |
| V[0] 加 8（同位置） | logits 与 value cache 已不同；本固定多层输入最终 key 也不同 | logits、key、value 均不同 | 错误 V 当场并持续推进状态 |
| 第一次回调成功返回却不写输出 | 288 项 NaN 毒化无法完全消除，exit 2，明确 `callback overwrote every output` | 不继续候选 | 漏写不可能伪装成正常完成 |

K、V 两次负控各实际执行72次模型投影；正常＋负控共288次模型调用。上表中的完整文件比较由独立 Python 回读再次核实，原参考不受污染。完整传播结论仅覆盖这三个位置和固定输入。

## 源码与运行身份

| 对象 | SHA-256 |
| --- | --- |
| 上游 `runq.c` | `ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548` |
| 原观察器 | `92bd2986e8bca35dc2ed30d0338eac2a0c96ef6a54d766835c793ad6fb9e8236` |
| 实际 TA/FR ELF | `610c499f46f1fe73074f626d8990bdcbdbc5f78c30ce8fc4a835495b0e392faa` |
| `active.c` | `ffbd57059987977d704767f8f87f4b1f1d98b1e479a053026f95f449076236f3` |
| 最终 `check.py` | `90cf98d1e6554324c373870a3c5178d659add80c57a461ba8ea72a040e20230e` |
| 本批宿主 `active.so` | `0e4b248611c0d57f3c4fcb2a0d3e60f3a6a012dfe7252a86c345e8968dbe0f2a` |

成功主批为 `check-03`，从既有已发布归档的 `build/vdot-perf.elf` 自动取出上述 ELF。宿主 Python 3.10.12、glibc 2.35，GCC、libm、libc、动态装载器及24项完整源码闭包身份均记录于原始结果。编译保持严格 binary32、禁止 fast math/FMA 收缩/自动向量化/内联/IPA 合并/LTO；参考与候选链接相同运行库，全部单 CPU 执行。

原 `check-01` 使用显式 ELF 已通过；`check-02` 因默认发布归档路径漏掉 `archive/` 在编译前失败。修正路径并补齐源码绑定、独立负控文件比较及命令终态回执后，`check-03` 重跑全部流程通过。额外错误 `--repo` 控制按明确源码身份错误拒绝。失败日志保留；缺失的旧 checker 快照只按记录的 SHA 精确还原并单列来源，不冒充当时直接保存的原件。

## 证据与复验

[使用说明](README.md)给出活动 forward、归档新源复验及普通 C QKV 接口。

| 证据 | 实际闭合 |
| --- | --- |
| [原始归档清单](evidence/active-v1/archive/manifest.json) | 2,300 成员、198,528,311 B 原文；正常、失败、完整状态、捕获、ELF、宿主库和24源闭包均保留 |
| [封存新源复验](evidence/active-v1/replay/result.json) | 新临时源码与独立 Python 进程重新编译、重跑四项验证；新增288次模型投影；1,090 个状态/回调证据文件、98,566,761 B 逐字节相同 |
| [复验原始命令与产物](evidence/active-v1/replay/proof/manifest.json) | 完整命令、源码、宿主库、证书与比较保留；重复状态/ELF按已核实的原归档成员字节引用，22份logits全部在比较集合 |
| [K污染](evidence/active-v1/observations/corrupt-k.json) / [V污染](evidence/active-v1/observations/corrupt-v.json) | 三个位置的完整文件比较直接可查；[漏写原stderr](evidence/active-v1/observations/omit-output.stderr.log)保留特定拒错 |

原始活动归档 SHA-256：`2df2da8bd64a53927fcacd3cb20c2b0f54b6a00eb96835164d076c3f8ed66fcc`。复验只使用归档中的24源和固定ELF，仍依赖宿主Python/GCC/libm；并非操作系统沙箱。原始与重新生成的完整现场继续保留，复验产生的新目录和时间回执不与旧运行混同。

本结果不提供目标完整 forward/token 周期、吞吐率、训练模型质量或新增 ASIC PPA；也不把既有预打包 Q 的百分比乘到全应用。R5稳定默认、旧实验与旧HOLD均保持原资格。当前工程增量是把被动捕获推进到真实候选输出驱动的完整状态接续；实际 FP32 量化＋QKV 目标边界另列结果。
