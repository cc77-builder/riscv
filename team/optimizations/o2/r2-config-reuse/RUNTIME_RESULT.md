# R2-S3：重复配置删除的整核运行与普通 C 交付

源码基点：`43e562d5e174763d9469b6c1c2124df0d60dc576`。操作ID：`20261024-LiZufan001-r2s3-runtime-1818`。实际运行输入是该基点加本轮逐文件绑定的新源码，增量、各阶段快照和SHA见运行定位；不是仅以基点HEAD声称包含新代码。本页记录新的 GNU/整核/C 阶段；[原主机阶段](RESULT.md)与冻结合同保留。交付提交由本文件所在 Git 历史定位，实时发布与认领见 [Issue #2](https://github.com/cc77-builder/riscv/issues/2)。

## 1. 结果与采用决定

**本轮完整矩阵支持三个整块形状的选择性使用：4×8、8×32、16×64 的 config-reuse/reuse/vdot 在固定调用计划下同时优于本轮 firstdot 和最快合格RVV。4×13 不采用 S3 vdot，继续选择本轮更快的 firstdot/reuse/RVV。** 全部16个入口的功能资格与各格性能是否采用分别记录；本轮没有授予“全矩阵无退化”结论，也未切换R5稳定默认。

这里的周期是固定 T17 上的 **GEMV 普通 C ABI 函数调用窗**，含既有调用/返回边界；未包括应用输入打包、结果提取或完整 LLM。正式比较只取本轮新执行的测量窗口，每格为三数据集各四次正式 repeat，共12个窗口；独立重放不重复计入均值。

| 形状 | firstdot reuse/vdot | config-reuse reuse/vdot | 较firstdot减少 | 本轮最快RVV | 较最快RVV减少 | 本固定计划选择 |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| 4×8 | 157.75 | 153 | 3.0111% | config-reuse/reuse：185 | 17.2973% | config-reuse reuse/vdot |
| 8×32 | 282.25 | 273 | 3.2772% | config-reuse/reuse：299 | 8.6957% | config-reuse reuse/vdot |
| 16×64 | 707 | 702.75 | 0.6011% | config-reuse/reuse：773 | 9.0880% | config-reuse reuse/vdot |
| 4×13 | 204.5 | 205.5 | -0.4890% | firstdot/reuse：187 | -9.8930% | firstdot reuse/RVV |

“较 firstdot 减少”计算为 `1 - candidate_total / firstdot_total`；“较最快 RVV 减少”使用本轮两变体、basic/reuse 四种合格 RVV 的最小总周期。负值表示候选更慢。所有单元格样本数相同，表中均值只为便于阅读，取舍按整数周期总和完成。

以下列出 firstdot → config-reuse 的全部平均周期：

| 形状 | basic/vdot | basic/RVV | reuse/vdot | reuse/RVV |
| --- | ---: | ---: | ---: | ---: |
| 4×8 | 197.5 → 195.5 | 225.25 → 225.25 | 157.75 → 153 | 187.75 → 185 |
| 8×32 | 645.5 → 643.75 | 356 → 356 | 282.25 → 273 | 300.75 → 299 |
| 16×64 | 2213 → 2211 | 990 → 991 | 707 → 702.75 | 778.75 → 773 |
| 4×13 | 233.25 → 233.5 | 230.5 → 230.25 | 204.5 → 205.5 | 187 → 187.25 |


未选择格的退化同样保留：4×13候选reuse/vdot更慢，不能将删了两条配置写成收益。16×64 basic/RVV、4×13两类RVV虽没有配置删除，其固定窗口也有小幅变化；[上下文观察](evidence/runtime-v1/runtime/control-context-observation-01.json)核对完整12窗、前序调用和未改变的完整8KiB槽。这些差异是可重放但尚未定位到具体微架构原因的上下文现象，不是RVV代码优化，也不能自行设置容差抹除。取舍继续使用实际最快RVV，且不把本固定计划结论推广为任意调用方性能。

全部样本、范围、退休指令数与 FU 观测保存在 [matrix-audit-01.json](evidence/runtime-v1/reports/matrix-audit-01.json)。本轮采用结论不要求所有16函数都使用vdot；库保留全部候选，使用方按形状选择。

## 2. 实际修改与公平比较

本轮复用已证明的 `candidate.py`，新增独立 `runtime_candidate.py`、`runtime_gate.py`、`runtime_experiment.py` 和归档工具。主机候选 SHA256 为 `e1ec595c78f3c14314c1d4dc1cc9f49650929e77275ba38241bce541481b15f7`，未重新设计或改动原删除规则。核心源码由本轮主 Agent 设计实现，独立 Agent 只做只读审查。

GNU 门禁在实际 ELF 上重新核验：完整加载布局、输入、24窗口 AB/BA 计划、API位置、前8字节参数搬运和返回相同；候选只能删除状态证明批准的 `vsetivli x0` 机器字，保留机器字与顺序不变；旧 leaf 范围之外的整个 BIN 字节相同。既有数学模型、实际访问序列、带毒状态、完整128位结果及退休数重新检查。

每个 firstdot 对照的完整 BIN、独立 wrapper 和公共对象必须等于已封存 firstdot 矩阵锚；该锚 manifest 为 `0c8d3159c91aa3c934c7bfb7f2640906844246e812c0b5bfc556cdfb86d0d3b4`。其两个完整 RVV 槽继续等于 S1 锚。config-reuse 对 vdot 和 RVV 使用同一删除规则，因此最快 RVV 也可获得配置删除收益。旧封存物只用于字节身份，不提供本轮的周期或运行 PASS。

新运行合同见 [RUNTIME_CONTRACT.md](RUNTIME_CONTRACT.md)。最小筛选先执行 8×32/dataset0；273周期相对本轮 firstdot 282.25 和最快 RVV 299 都更低，完整正确性及重放通过后，才按事先条件扩大矩阵。

## 3. 真实运行与覆盖

| 阶段 | 真实新进程 | 正式窗口／调用 | 结论 |
| --- | ---: | --- | --- |
| 8×32/d0最小探针 | 5：1负控＋2正式＋2重放 | 32正式窗口；48全窗口重放比较 | 完整128位、CSR、退休、计数、O2、负控恢复和重放PASS |
| 余下22图扩展 | 28：22正式＋6重放 | 352正式窗口；144全窗口重放比较 | 批内检查PASS；单批按设计为PARTIAL |
| 两批聚合 | 33：32正常＋1负控 | 24正式图；384正式窗口；192全窗口重放比较 | 完整矩阵原文审计PASS |
| 普通C | 3：1负控＋同BIN恢复＋独立正常重放 | 16函数；48不同case；每正常进程1008条vdot | 正常恢复和独立功能重放PASS；不测量性能 |

性能矩阵共产生24个真实GNU/AM ELF，另有1个普通C ELF。本轮合计36个新EMU进程：34个正常、2个预期负控。打包、审计、库和使用示例阶段新增EMU/NEMU为0。

独立进程重放覆盖四个形状、两种变体的dataset0，共8图，每图比较全部24个窗口；dataset1/2纳入正式比较，没有另作独立进程重放。普通C功能验证不参与性能表的均值计算。

两个负控分别绑定本轮性能 ELF 和本轮普通 C ELF 的真实首条自定义指令位置，均验证 vd0、`0x0388000b`、bit100、唯一 mismatch、预期非零退出和合法部分 O2 轨迹；随后用同一完整 BIN、新进程及真实正常参考恢复。负控夹具为团队测试程序，官方程序与正常参考保持原样。

| 新负控 | 注入PC／实际mismatch PC | 目的和翻转 | 预期退出码 |
| --- | --- | --- | ---: |
| 性能8×32/d0候选 | `0x80002308` | vd0／`0x0388000b`／bit100 | 1 |
| 普通C候选 | `0x800003d4` | vd0／`0x0388000b`／bit100 | 1 |

普通C原始XSTrap记录的abort event PC为`0x800003f8`；该字段与真实注入／mismatch PC分别保存，没有把二者混为一个PC。资格绑定要求注入PC等于实际mismatch PC。

扩展批的单独 `S3_PARTIAL_PASS` 是预期范围标记：它没有重复负控，也没有重复已完成的8×32/d0探针。最终 matrix 审计聚合两个已完成批次，核验唯一正式图、完整覆盖、跨批时间顺序及所有重放签名，再授予完整矩阵资格。

构建最多4个独立任务；性能 EMU 串行，全部重型 WSL 命令限制在CPU 0–3。输入/输出按构建和进程隔离，不并发运行性能测量与重构建。宿主墙钟耗时仅为运行成本，不作为处理器性能数据。

## 4. 普通 C、静态库与实际用法

公共源位于 [public/gemv.S](public/gemv.S)、[public/gemv.h](public/gemv.h)，独立命名空间为 `config_reuse_gemv_*`。四形状 × basic/reuse × vdot/RVV，共16个函数；完整对象与本轮12个候选形状/数据集单元的对应 leaf 比较，共48次逐字节锚定。

普通 C 验证私有加载冻结 R4 程序，保留原 main、Makefile、48个不同用例、标量参考、输入不变性、边界 canary、完整128位、CSR和O2判定。两个正常进程共96次调用；旧解析器中的 R4 标签不是资格来源，外层合同、源码快照、矩阵锚及真实新运行共同标识本候选。

已交付 [libconfig_reuse_gemv.a](evidence/runtime-v1/library/libconfig_reuse_gemv.a)。库唯一成员为完整合格对象，长27,160字节；不是抽取若干函数后重新冒充原对象。真实C consumer 的16个符号引用、链接后全部leaf、公开命名空间和库成员一致性均通过。

| 交付物 | SHA256 |
| --- | --- |
| 静态库 | `92c8941d440f55b1ebf824b0a937a17648f4a769dfe62de6a53b47054369dc28` |
| 完整合格对象 | `f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3` |
| 公共头 | `d6cbdadb8ed601e1ccd4d308970111588c5fe7e10098b821625630e2b5360be9` |

完整资格与逐函数清单见 [library.json](evidence/runtime-v1/library/library.json)，独立字节检查见 [library-check.json](evidence/runtime-v1/library/library-check.json)。

[完整使用说明](RUNTIME_README.md)提供输入打包、16字节输出槽、显式函数选择、从源构建、离线复算与回退。文档中的完整C示例经真实GNU编译和可重定位链接；公共汇编重编后的整个对象等于合格对象，公共 header 与库 header 直接相同，链接后16个 leaf 字节不变且无未定义符号。**该示例只完成编译链接，没有实际执行或测量应用周期。**

本轮不修改 R5 稳定默认和既有 firstdot 公共库。回退可重新编译为此前 `firstdot_gemv_*` 或 [R5稳定入口](../r2-select/STABLE.md)；原稳定头的开关不控制显式 config-reuse 调用。

## 5. 原文审计、拒错与交付完整性

| 检查 | 实际结果与证据 |
| --- | --- |
| GNU运行门禁 | [12项检查](evidence/runtime-v1/reports/runtime-gate-tests-01.json)全部PASS，无新增编译或EMU |
| 归档拒错 | [五种一致重哈希坏包](evidence/runtime-v1/reports/probe-evidence-tests-01.json)均被语义/覆盖/关联/顺序检查拒绝；归档内输出路径拒绝且不写入 |
| C适配 | [原main/Makefile、确定性生成、16函数/48例及三类身份拒错](evidence/runtime-v1/reports/c-host-01.json)PASS |
| 库消费者 | [四种一致重哈希坏库](evidence/runtime-v1/reports/c-library-host-01.json)均被拒绝：缺consumer、错误成员、缺载荷、错误函数表引用 |
| 文档示例 | [真实GNU源重建、完整C示例编译与链接](evidence/runtime-v1/usage-check/report.json)PASS；不执行示例 |
| 原始归档复算 | [完整matrix](evidence/runtime-v1/reports/matrix-audit-01.json)和[C＋matrix组合审计](evidence/runtime-v1/reports/c-audit-01.json)PASS |
| 独立检出复算 | [受限访问原文审计](evidence/runtime-v1/reports/c-detached-audit.json)与[访问检查回执](evidence/runtime-v1/reports/c-detached-guard.json)PASS；[库字节检查与汇总](evidence/runtime-v1/runtime/detached-detached-summary.json)PASS |

独立检出的C＋matrix报告与原报告不仅JSON内容一致，SHA256也同为`6c76ec251d539dfd7bfef24e12b709d6f9f5ea3015a58a461fddc497d5b452cd`。

归档审计从封存的 ELF/BIN、原始 stdout/stderr、执行回执与源码重算数学、架构、完整128位、CSR、退休、周期、O2、拒错/恢复和重放结论；不会只接受缓存统计或一个PASS字段。

独立检查使用另一份完整历史的 `43e` 源码检出，加逐文件 SHA 核对的未提交候选增量与归档。既有 Python dependency guard 阻断本轮原工作根、T17物理根、firstdot物理根及T12 flash根的文件访问和显式子进程路径，实际重新执行完整 C＋matrix 原文审计。结果与原审计 JSON 逐项一致；库字节检查另在该独立副本中执行。

这证明同主机另一来源目录可以用封存证据重算；guard 是 Python 访问/显式命令检查，**不是操作系统安全沙箱，也不代表新机器安装或人工 ACK**。离线阶段没有重新读取大型物理EMU/NEMU/AM/flash实体，只保留其在实际运行中核验的封存身份。

新证据目录具有独立 `-text` 属性，避免 Git 文本换行转换。最终 Windows 原生 Git 检查精确变更库存、每个100644/stage0 blob与原文件字节、三类归档全部载荷及清单闭包；检查回执自身再单独核验。最终文件数以 [publication-check-01.json](evidence/runtime-v1/reports/publication-check-01.json) 为准，初始快照计数不冒充最终发布库存。

默认`git diff --cached --check`实际未通过：已封存的`test_c_api.py`第135行有一个EOF空行。保留该文件原SHA `3fd521655f776c752c5006551c544639ecab14aff85108f4965e0d60630552d7`；交付检查只接受这一完整诊断、退出码2、空stderr、对应暂存blob/原文件身份和恰好两个末尾LF，其他差异仍拒绝。这是明确的格式例外，不是默认whitespace PASS；没有修改Git全局设置、属性或任何运行输入。旧检查器和[失败/修复回执](evidence/runtime-v1/runtime/publication-recovery-01.json)保留，新检查器单独编号。较早的独立原文审计未执行这个后续发布检查器。

| 归档 | 载荷数 | 原始字节 | 存储字节 | manifest SHA256 |
| --- | ---: | ---: | ---: | --- |
| [8×32探针](evidence/runtime-v1/probe-archive/archive-manifest.json) | 236 | 38,789,918 | 5,073,145 | `281c16eed98ba5306932dfa24150703ba335d290bc106594c3b25a1c0b01fc9f` |
| [完整矩阵](evidence/runtime-v1/matrix-archive/archive-manifest.json) | 1,616 | 256,851,979 | 18,531,089 | `0310fa0f2b3edc2851bb4e16d95b4ee994822ac911c2e448c905d194f9406be2` |
| [普通C](evidence/runtime-v1/c-archive/archive-manifest.json) | 137 | 17,542,224 | 1,226,531 | `4e872d8aeb752145127fa8221a60098de6be1b7f110a858402ec0b428e776604` |

载荷数不包含各包三个固定元数据文件。完整矩阵包已经包含探针输入和执行证据，不能将三个包的载荷数相加当作独立覆盖数。

## 6. 来源与运行位置

| 身份 | 固定值 |
| --- | --- |
| T17硬件源码 | `34bae6d4acceac939f958199dae53c14bc1f6183` |
| EMU SHA256 | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 正常参考 SHA256 | `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` |
| T17身份文件 SHA256 | `4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb` |
| 本轮运行合同 | `r2-s3-config-reuse-runtime-v1` |
| 本轮C合同 | `r2-s3-config-reuse-c-application-v1` |

原指定 Windows 来源入口实际为 `ff58e519091f273c4bc177f5e82cfbbfaf102cc5` 的干净检出，本轮使用独立 `working-r2s3-runtime-20261024-1818` 与 WSL 原生 `/home/lizufan/riscv-lab/r2s3-runtime-20261024-1818`。详细源码差异、实际命令、工具回执、状态和独立检出位置见 [locations.json](evidence/runtime-v1/runtime/locations.json)。

本轮起点为2026-10-24 10:18:11 UTC（18:18:11 UTC+08:00）。下面为实际运行/验证时间；提交及发布收束时间见协调Issue，不将后续发布耗时填入处理器周期。

| 阶段 | 实际UTC+08:00时间 |
| --- | --- |
| 探针5进程 | 18:31:13～18:38:29 |
| 扩展28进程 | 18:40:50～19:32:51 |
| 普通C3进程 | 19:37:58～20:01:24 |
| C封存、库与使用示例完成 | 20:02:52 |
| 独立检出原文审计完成 | 20:05:01 |

准备阶段的初始Windows检出因长路径失败；仅在新工作区启用`core.longpaths`后成功。`build-probe-01`因跨shell根路径参数错误在构建前退出，实际构建使用明确路径的`build-probe-02`。`pending-01`为未执行草稿，最终`pending-02`加强了公共头与合格库的直接身份检查。旧草稿、失败输出及实际执行版本分别保存，不把准备失败或旧PASS计入新运行，也没有重复启动已完成的EMU。

## 7. 工程判断与后续

8×32/d0/reuse/vdot 正式窗口的观测分解支持局部软件收益：firstdot 到 config-reuse，首接受距窗口起点从103变为93周期，接受跨度115→117周期，末响应距窗口结束约62～63→61周期；每个请求仍为2拍响应且无写回阻塞。窗口确实缩短，但接受跨度没有缩短，不能据此声称FU延迟或吞吐率提高，也不能直接归因某条load。

本子项的状态证明、GNU、完整调用窗矩阵和独立C库已按各自范围闭合。后续若有实际应用调用方，优先测量打包、搬运、调用和核内开销，使用最快合格RVV走同一路径，先做8×32有界筛选；不要为保持忙碌重复已完成矩阵或无依据修改RTL。默认入口更新、真实应用集成与任何新链接布局应单独核验影响。

本轮未改变硬件，未开展新面积、STA、频率或功耗验证；不能由软件周期推出ASIC PPA。完整应用/LLM、新机器安装、人工验收和全部赛题要求的最终通过均不由本结果授予。此前旧 B0/H1 合同缺项仍按原状态保留。
