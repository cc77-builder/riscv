# Row32 W8：真实 GNU ELF 的有限功能筛选

2026-11-06 UTC；合同 [screen-v1](CONTRACT.md)，Issue #2 WORK `6672608444`。

**结论：`ROWLANE32_FINITE_ELF_SCREEN_PASS`。** 新输出行布局已通过真实 GNU 编译、完整机器码身份检查，以及既定有限数值、精确地址、ABI/CSR 和负控筛选。保留为独立软件候选，暂不改变稳定入口或完整消费者，不发布性能优选。当前没有新 NEMU、T17/EMU、DiffTest、应用周期或 ASIC PPA 资格。

## 实现与保持的语义

新符号 `q288_rowlane32_i8` 处理完整 M=K=288、GS32、VLEN128，使用标准 RVV。每个向量 lane 对应一个独立输出行，32 行为一 tile；权重布局为 `[tile32][group32][k][output_lane]`，仍是82,944个 signed-int8 字节。原 q288_context 结构的前六个指针复用，但其 packed 指针必须指向新布局；不能与原 row8 打包缓冲混用。

整数核在 e16/m4 下把 W8 符号扩展后执行 widening MAC，两个 e32/m8 累加器分别处理奇偶 k，组末精确合并。完整 signed-int8 域保留，包括−128。每行仍按 g0→g8 执行 `int32→binary32→×Ws→×Xs→+acc`，不使用FMA、不合并尺度、不重排组序。Ws/Xs 组织保持。最终八个完整128位槽由末八行的整数和及高96位零组成。

packing 是显式的新预处理，尚无目标时间测量；本结果不包含其成本。后续比较应同时报告新旧方案的实际 packing 差额，不能把任一方成本默认为零。[成本分析](COST.md) 也不把静态指令减少当作周期收益。

## 实际构建与正常执行

全部本机任务在已协调的单核 CPU3 上串行执行；没有新硬件或参考库构建，没有启动 EMU。下表耗时是宿主作业墙钟时间，不是候选目标周期。

| 阶段 | UTC开始 | 宿主作业耗时 | 结果 |
| --- | --- | ---: | --- |
| GNU编译、链接、objdump | 00:07:03.320 | 2.559s | exit0，清理完成 |
| 有限ELF正例与独立C oracle | 00:14:25.601 | 4.713s | exit0，清理完成 |
| 真实ELF负控与旧布局误传 | 00:15:53.783 | 1.641s | exit0，清理完成 |

同一新 ELF 中保留旧 `q288_fused_rvv4`。另外独立运行未修改父生成器并编译其输出，旧FR的**完整592B函数机器字逐字相同**；固定公共整数核的原87字证书也通过。此比较证明保留了旧函数，不迁移其历史目标或性能资格。

正常用例为 x0→x1→x0→x2、min×min、max×max、min×max、零权重，共8例；每例同时执行旧FR和新row32的实际ELF有限模型。前四例复用同一packed缓冲及前次向量寄存器状态，后四例分别覆盖W/X偏移12/12、15/3、2/10、5/1的字节对齐。

所有用例均通过：

- 全部288个Y的binary32位型，与未修改的row-major C oracle及独立Python黄金值一致。
- 末八槽的全部128B、全部输入只读、完整宽度callee-saved GPR/FPR与ra/sp保持、正确返回、最终VL/VTYPE/VSTART/VCSR/FRM符合合同。
- 每次完整调用执行81个完整165字整数块；W的82,944B和Ws的10,368B各读一次，X的288B及Xs的36B各读9次，context前48B读一次；Y的1,152B和slots的128B各字节恰写一次。
- 每次调用的FP元素操作保持为2,592次转换、5,184次乘法、2,592次加法。原严格FMA舍入见证保持。

模型使用固定父模块的整数实现binary32 RNE。独立原生C检查覆盖4,337个加法、3,798个乘法及4,108个int32转换；非有限结果排除数分别为3和542。该层不模拟fflags，不授予NaN/Inf、非RNE、硬件异常或目标运行资格。

实际机器码有限模型中，旧FR每次完整函数执行35,670条，新候选14,361条；后者比旧FR少59.7393%。这是一项指令数量结果，不能写成目标周期降低59.7393%。候选有209条静态机器指令、836B，整数核心为660B；ret之后的对齐NOP不属于函数范围。

## 负控及其实际拒绝原因

先完成正常用例，再检查同一ELF的10个机器字变体和旧packed误传。所有原始变体与结果均保存。

| 控制 | 实际检出 | 能证明的边界 |
| --- | --- | --- |
| AVL32改为31 | 不支持的累加器向量模式 | 模式fail-closed；未把短VL当正常数值覆盖 |
| W步长32改为64 | 访问超出精确调用方缓冲 | 地址越界 |
| 首个X字节偏移0改为1 | 完整Y位型不匹配 | 数值检错 |
| signed扩展改为unsigned编码 | 未支持指令 `0x4b832e57` | 编码fail-closed，非无符号变体数值证明 |
| widening MAC改读v24 | 完整Y位型不匹配 | 数值检错 |
| widening目的改成不对齐v1 | 非法寄存器组 | 组对齐检查 |
| 省略最终零向量初始化 | 完整slots不匹配 | 高96位检错 |
| 省略vcsr重置 | CSR/FRM末态不匹配 | CSR检错 |
| 返回配置写入s0 | 完整宽度ABI不匹配 | callee-saved检错 |
| 交换Ws/Xs两次乘法 | 完整Y位型不匹配，FP操作数量仍相同 | 舍入顺序见证 |
| 将原row8 packed直接传入 | 完整Y位型不匹配 | 新布局ABI不可混用 |

负控拒绝不能代替正常候选正确性；上表与此前8例正例共同构成本阶段证据。

## 身份、证据与复现

| 项目 | SHA256 |
| --- | --- |
| 新完整ELF | `fdb39f36e351c3907b3184d52233d1ee16c33e94b98b1317046823045a41ed22` |
| row32函数机器码 | `f74b1a753a731dec5d803c9fca6afb1e1ca293737a85414f974b715d5912ea00` |
| 保留的完整FR函数 | `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab` |
| 原始证据ZIP | `7a26ca8ae38603a125c3105ccebe741df709e19eb245d0e843b66db001005d1c` |
| 成本分析源码ZIP | `4e44dc60437a8dc9e0e6b325932acfafd5e5c0187f3fd97fc6b74e21614b616e` |

[summary.json](evidence/screen-v1/summary.json) 给出实际结果；[members.json](evidence/screen-v1/members.json) 列明 [raw.zip](evidence/screen-v1/raw.zip) 的87成员、508,143B展开大小与每项SHA。ZIP本身124,648B，包含四个候选源文件、全部固定依赖源码快照、GNU命令/原始日志/ELF、未改基线、C oracle、所有正常结果和负控ELF。原ZIP及所有成员已逐字节验证。源码路径、真实工具版本、命令与运行身份以这些原始记录为准。

首次封存辅助脚本把Path对象排序与字符串排序直接比较，因`source`/`source-snapshot`顺序差异而失败，尚未写入发布目录。随后只读诊断确认成员集合、CRC和每项原字节均正确，直接保留原ZIP并完成复制；没有重跑或改写功能结果。[失败与诊断回执](evidence/screen-v1/archive-failure.json) 保留这一过程。

从仓库根使用已有GNU工具链及Python 3.10+，选一个新的仓库外输出目录；复现时按实时协作预算绑定一核：

```bash
export PYTHONDONTWRITEBYTECODE=1
python3 team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/rowlane32/screen.py --repo . --output /path/to/new/rowlane32-output --phase build
python3 team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/rowlane32/screen.py --repo . --output /path/to/new/rowlane32-output --phase numeric
python3 team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/rowlane32/screen.py --repo . --output /path/to/new/rowlane32-output --phase controls
```

每阶段拒绝覆盖已有阶段输出，后两阶段重新核对原构建输入身份。无需改动父生成器、公共源、oracle或既有实验。只复算证据时可先核ZIP和成员SHA；不必为阅读本结果重复目标运行。

## 当前取舍

保留独立候选和失败可追溯性；现有完整消费者、生产RTL、官方程序、强RVV及稳定默认均未改变。新W布局尚未取得目标功能与实际周期，完整应用和packing成本尚未测量。完整成本分析显示宏指令下降明显，但Vimac计算分片增加，且解码数量差的一部分来自VSET附加操作；因此暂不单凭本筛选申请长整核或应用campaign。

下一步如有足够收益机制，应在新合同中保留当时最快合格RVV与TA、同ELF地址/调用/预热条件和全部锚点，先验证新的真实参考执行及有界Q，再决定是否扩展K768或完整消费者。历史PASS、当前有限模型PASS及其他候选的目标资格不能互相替代。
