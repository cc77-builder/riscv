# R2-S3：hoisted 上下文的退休与重定向原文诊断

日期：2026-10-25（UTC+08:00）。操作 `20261025-LiZufan001-r2s3-context-1343`，
软件来源基点 `3d56e84aca5cc63bf235f6fbcf76ce8079c9581c`。
交付接续：`20261025-LiZufan001-context-delivery-1432`，沿用同账号原 WORK。

## 结论与适用范围

本轮把旧 hoisted 的差异从“首个 vdot ACCEPT 以前”进一步定位到实际动态指令和间接调用附近。
五个 hoisted 镜像共 60 个正式 vdot 窗口中，33 个有可连续关联到调用 ROB 项的非自清理重定向，
对应调用退休到叶函数首条退休的间隙为 7 或 9 拍；其余 27 个未观察到符合条件的重定向，间隙为 0 或 1 拍。
这提供了具体的控制流上下文证据，但没有独立观测到标量分配代号、重定向原因、预测/实际目标或取指恢复时刻。

**原 `HOLD_CONTEXT_VARIATION` 保持。** 本轮新增 EMU 为 0，不改旧门槛、正式样本、内核、caller、
生产 RTL、参考实现或 R5 默认。它是对已封存原文的可复现派生分析，不是新的应用性能、整核正确性或 ASIC 资格。
原包装优化及旧筛选资格仍按 [RESULT](RESULT.md) 与 [SCREEN_CONTRACT](SCREEN_CONTRACT.md) 各自范围解释。

实现：[context_prefix.py](context_prefix.py)；针对性检查：[context_checks.py](context_checks.py)。
完整结果及原始组/动态位置/事务见 [结果 JSON](evidence/context-prefix-v1/result.json)、
[逐位置压缩数据](evidence/context-prefix-v1/frontiers.json.gz)、
[检查结果](evidence/context-prefix-v1/checks.json) 和 [交付清单](evidence/context-prefix-v1/manifest.json)。

## 1. 输入及实际重算

输入是已发布的六个完整封存包 b4、h0、h1、h2、h3、h4，
[screen-v2/index.json](evidence/screen-v2/index.json) 的 SHA256 固定为
`38c2b5b1613a849272cbe1d5e1e9dd9db2596eef4660a7881a92a56137505173`。
每包原成员清单、解压后字节、构建/ELF/BIN、原资格审计和相关源码均重新核对身份。
不把历史 PASS 自动转移给不同输入。

实际重算覆盖：

- 六包各 recovery/replay 的全部 36 窗，共 **432 窗**：从实际 ELF 的受约束标量路径复核动态 PC/word、
  退休组覆盖、四个 CSR 样本、前后 fence、counter/ROB 身份和完整 O2 协议。
- 每相各 **72 个正式 vdot 窗口**，每窗 32 条实际退休 vdot：按完整 ROB 指针和分配代，
  关联 ENQUEUE、ACCEPT、RESPONSE、COMMIT，排除只因时间落窗的投机事务。
- 正常与重放的逐位置退休记录、原组来源、全部绑定事务及新重定向观察完全一致；重放不作为额外独立样本。
- **27 项针对性检查通过（7 正向、20 拒错）**，覆盖路径/计数器、压缩退休、同拍 slot/ROB 身份、事务绑定、同拍 ROB 重用、
  仅内部坐标变化的重放、符号坐标、文件身份/链接，以及标量重定向连续性。

复用的 ELF 路径、计数器和 O2 审计 helper 都从包内精确 hash 固定的团队源码载入。
旧文件、旧合同和原日志没有被修改；新代码的拒错及诊断适用范围单独列出。
历史原始负控、NEMU/EMU 实物和构建资格按完整封存身份复用，本轮不声称重新运行了它们。

## 2. 两种统计口径分别保留

旧采用门槛比较每镜像每数据集的 **4 个正式窗总周期**。单窗极值只用于诊断，不能替换原门槛。
只取 h0～h4、repeat 2/3/4/5；没有混入 b4、first 或 warmup。

| 数据集 | h0 / h1 / h2 / h3 / h4 的四窗总周期 | 总周期极差 | 最大/最小−1 | 20 个单窗范围 |
| --- | --- | ---: | ---: | ---: |
| 0 | 4861 / 4815 / 4867 / 4862 / 4823 | 52 | 1.079958% | 1200～1223 |
| 1 | 4877 / 4822 / 4886 / 4878 / 4823 | 64 | 1.327250% | 1201～1227 |
| 2 | 4895 / 4830 / 4889 / 4875 / 4807 | 88 | 1.830664% | 1199～1228 |

三组仍超过原 1% 锚点门槛。23/26/29 拍的单窗极差与 52/64/88 拍的四窗总和极差没有冲突。

## 3. 从首个差异到调用边界

以 h0 为参考，按相同 dataset/repeat 对齐 h1～h4，共 48 对正式窗口。
其中 47 对存在退休坐标差，另 1 对相对坐标完全相同。
这 47 对的首个差异都在动态位置 11～17，即包装函数入口附近的
`0x80000700`～`0x80000718`；双方坐标均为 cycle-start 样本后 41～45 拍。
程序也分别输出“任意坐标首差”和“双方均在计时窗内的首差”；本数据中二者相同。

首个可见差异不是最大差异的原因证明。沿真实动态路径增加调用边界后，旧极差对应的两镜像四窗聚合如下。
各值都是较慢组减较快组的**坐标差之差**，不能当成可相加的独立执行成本或某部件的因果贡献。

| 数据集/组别 | 完整窗差 | 首 ACCEPT 以前 | 末次相关循环分支退休→调用退休 | 调用退休→leaf 首条退休 | leaf 首条退休→首 ACCEPT |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0：h2−h1 | 52 | 44 | 14 | 25 | 0 |
| 1：h2−h1 | 64 | 55 | 18 | 34 | 0 |
| 2：h0−h4 | 88 | 82 | 16 | 34 | 0 |

调用位置来自动态路径中 leaf 入口的前一项，并核对它位于 caller_full、是 rd=ra 的 JAL/JALR、
独立退休且完整 PC/word/slot/ROB 一致。hoisted 的调用是 `0x80000788` 处的 `0x000300e7`
（`jalr ra,t1,0`），目标入口为 `0x800015a0`。
同一原始退休组展开出的指令共享观测拍号，并保留 group_count/offset；例如入口的两条 move 可以同组退休，
不能把展开记录理解为每条指令都有独立执行打点。
循环仍按 ELF 回边和动态访问次数编号，JSON 保留 PC、目标和访问次数，不仅凭“第三个循环”推断功能。

六包 72 个正式窗口中，首 ACCEPT 相对 leaf 入口退休均为 **+51 拍**。
每相 2304 条正式已提交 vdot 的 ACCEPT→RESPONSE 均为 **2 拍**，没有被筛掉的窗外事务。
+51 包括叶函数入口后寄存器、CSR、向量配置及加载准备的坐标关系，不是算术延迟或分支恢复时延。

## 4. 间接调用与重定向的连续性关联

| hoisted 镜像 | 唯一连续 origin / 正式窗 | 有 origin 时 call→leaf 退休间隙 | 无符合条件 origin 时的间隙 |
| --- | ---: | --- | --- |
| h0 | 11 / 12 | 9 拍 | 0 拍 |
| h1 | 0 / 12 | — | 0 拍 |
| h2 | 11 / 12 | 7 或 9 拍 | 0 拍 |
| h3 | 11 / 12 | 7 或 9 拍 | 0 拍 |
| h4 | 0 / 12 | — | 0 或 1 拍 |

33 个关联 origin 到 leaf 首条退休的观察间距均为 **13 拍**。它是两个已记录事件之间的间距，
不等于目标取指、开始执行或真实预测惩罚。事件没有打印原因；本结果不把 self=0 直接命名为已观测的 target misprediction。

关联并非只看时间邻近。新代码先通过完整 O2 协议审计，再要求：

1. origin 位于本 marker 覆盖内、早于调用退休，完整 `flag:index` 与调用一致，且 self=0；
2. 下一拍 VFEX4_REDIRECT 的指针/self 一致；
3. 从 origin 到调用的 `(cycle,slot)` 区间没有该 full ROB 的原始退休组，没有会杀死该指针的后续 redirect；
4. 调用当拍同 full ROB 的退休组唯一，且调用身份全部匹配；任何 T13 退休与 ROB redirect 同拍均拒绝；
5. 无匹配或多个仍连续的 origin 均如实输出，不强制凑成唯一结果。

**有效源前提仍由固定 RTL 提供。** 日志未记录 scalar ENQUEUE、entry.valid 或分配代号；
上述检查排除了起点之后可见的退出/复用，不独立证明起点不是陈旧源，也不新增硬件正确性资格。
完整原始日志及固定 capture 身份是必要依据，单个 O2_TRACE_PASS 并不独立证明所有标量事件绝无遗漏。

硬件身份来自 [T17 identity-02](../../../repro/evidence/clean-reproduction-v1/reports/identity-02.json)：
源码 `34bae6d4acceac939f958199dae53c14bc1f6183`、空工作补丁，EMU
`ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`。
本轮只读核实了该版本的
[Rob](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/rob/Rob.scala)、
[CtrlBlock](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/CtrlBlock.scala)
及 [RedirectGenerator](https://github.com/cc77-builder/riscv/blob/34bae6d4acceac939f958199dae53c14bc1f6183/src/main/scala/xiangshan/backend/ctrlblock/RedirectGenerator.scala) 的相关条件：

- O2_REDIRECT 在非 reset、实际 Rob.io.redirect.valid 时打印，不受 marker 或 vdot 活动过滤；
- 普通 entry 清除通过 commit 或 redirect 派生 needFlush；异常/flushPipe 也经 ROB redirect 路径；
- 上游有效 WB、flush 过滤及 misprediction 后退休阻止维护正常 origin 的有效性。

因此结果支持继续检查**前序调用和共同间接调用点的上下文**。它不能单独区分具体预测器、缓存、前端阶段或解释全部总周期差。
T13 退休仍只覆盖 marker，前序 UART、judge 和初始化的完整路径不可见；O2_REDIRECT 的全局覆盖不能替代这些退休路径。

## 5. 复算与证据布局

需要 Python 3.10+ 标准库；链接拒错检查在 Linux/WSL 原生临时目录执行。无需编译器、EMU 或 EDA。
从包含本提交及旧 screen-v2 封存包的仓库根目录运行：

```bash
context_module=team/optimizations/o2/r2-config-reuse/caller/hoisted
context_repro_root=$(mktemp -d /tmp/hoisted-context-XXXXXXXX)
python3 -B "$context_module/context_prefix.py" \
  --evidence "$context_module/evidence/screen-v2" \
  --output "$context_repro_root/diagnostic"
python3 -B "$context_module/context_checks.py" \
  --evidence "$context_module/evidence/screen-v2" \
  --output "$context_repro_root/checks.json"
```

输出必须不存在，且不得放进输入证据目录。输入及祖先目录的符号链接会被拒绝。
`frontiers.json.gz` 解压后包含全部动态位置、原退休组、完整事务和调用关联；只保存压缩版，不重复复制旧 EMU 原文。
交付 gzip 的 SHA 用于本次文件完整性；跨 Python/zlib 环境比较以 JSON 解压后的 `raw_sha256` 为规范身份，
不能因为设置了 mtime=0 就假定所有环境的压缩字节相同。

原执行命令、退出码、Python/zlib/CPU 亲和、原始 stdout/stderr 与输入传输核验保留在
`evidence/context-prefix-v1/`。原 Windows Git 导出因四份被忽略的日志而未完成，
其 ChatPC 操作仍未确认清理；本次没有重放该脚本、修改原工作树/index 或解除锁。

### 独立环境交付复算

接续在独立 Linux 快照中完成。源码与十二份旧证据通过 ChatPC 专用只读工具取得，
六个已发布封存包按固定 index 的大小/SHA256 逐项核验；源文件再次回读的哈希不变。
使用 Python **3.12.14**、zlib **1.3.2**，在四核总亲和范围内并行执行原诊断器与原检查器：
432 个窗口、两相各 72 个正式 VDot 前沿及 27 项检查通过。
逐位置 JSON 解压原文与原 Python 3.10.12/zlib 1.2.11 输出逐字节相同，
检查 JSON 也逐字节相同；结果 JSON 除 gzip 字节数和压缩哈希外完全一致。
本次不重复保存另一份大 gzip；交付原压缩文件及新环境的执行/比较回执。

- [独立执行回执](evidence/context-prefix-v1/independent-execution.json)
- [原文比较](evidence/context-prefix-v1/independent-comparison.json)
- [来源和未结束控制层保护](evidence/context-prefix-v1/recovery-receipts.json)
- [交付方式与范围](evidence/context-prefix-v1/delivery.json)
- [逐文件清单](evidence/context-prefix-v1/manifest.json)

清单包含大小、SHA256 和按原字节计算的 Git blob ID。
候选通过 GitHub Git-data API 基于原远端完整 tree 构造，保留未涉及的全部路径；
发布仍按 Issue 短窗口、父提交及预期分支 SHA 校验，只作正常快进。
这不声称原 Windows Git 导出成功，也不解除原未知操作对本机目录的保护。

详细 gzip 只保存一相的 72 个正式窗口；另一相由完整 recovery/replay 复算证明相等，
不能把 144 个验证前沿当作 144 个独立性能样本。本次无新 EMU、GNU 构建、RTL 或 ASIC 测量。

## 6. 路线影响及接续

本轮收束于可复现的退休/控制流诊断，不通过增跑、删除样本或放宽门槛解除旧 HOLD。
若后续确需追查旧 hoisted 的上下文，最小有意义的干预是单镜像、固定同一计时目标/地址/初始化，
仅在两种前序 RVV 实现之间切换并事先固定顺序；结果后置输出，判断是否重现该调用关联与早期偏移。
重现只证明受控前序足以产生效应，未重现也不自动续开预热或完整算法矩阵。
这属于新合同，不借旧门槛或本次事后观察选出最快方法。

当前获选 split 接口和 R5 稳定默认继续按各自合同使用。fixed-weight consumer 的原实跑不需要因本诊断而重跑；
其旧封口 operation 仍按 Issue #2 的未知状态保护处理，不能把本包发布当成解除其锁或接管其输出的依据。
