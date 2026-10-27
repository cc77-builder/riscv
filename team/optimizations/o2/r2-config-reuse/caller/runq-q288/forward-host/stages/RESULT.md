# 完整 forward 阶段与真实消费者：交付总览

操作 `20261027-LiZufan001-forward-stages-0300`，叶级包 `R2-S3/runq-forward-stages`；@LiZufan001 / Pro 主 Agent 设计实现，子 Agent 独立只读审查。开发基点 `b1d3f136dafae81cf76d2c1f35079cb1465ce7af`。本记录随成果提交，承载版本由 Git 历史定位；发布状态与资源释放见 [Issue #2](https://github.com/cc77-builder/riscv/issues/2)。时间使用北京时间 UTC+08，原始回执保留 UTC。

**本轮把完整模型从宿主观察推进到实际 RISC-V 参考执行，并为 RoPE 和真实投影建立独立的目标阶段入口。** 完整参考模型保持 D288/H768/L6/heads6/kv6/GS32/V32000/S256、确定性未训练权重和连续 tokens `[1,7,19]`。没有缩小词表或 KV 容量，也没有以参考值回填候选状态。完整 forward/token 的香山 DiffTest 与性能仍未取得资格。

## 1. 已完成的工程与验证

| 层次 | 实际成果 | 结论边界 |
|---|---|---|
| [完整宿主阶段](HOST_RESULT.md) | 四路完整 forward，连续256位置共1024次调用；其中512次带标记调用各120边界/119区间，完整16 spans比较；最终运行器三位置、五项消费者破坏控制和实际 sanitizer 拒错 | 宿主功能与阶段接口通过；不是目标周期。LSan未通过，旧失败/未知回执原样保留。 |
| [数学/TLS](NATIVE_RESULT.md) | 十个实际 libm 入口、24个输入；正常/错误golden/栈保护失败/恢复/重放，共5次EMU | 固定目标探针、errno、fcsr、TLS与原DiffTest通过；不代替完整模型。 |
| [scalar 与 RoPE-cache](NATIVE_RESULT.md) | 每正常参考进程完整执行3位置×2消费者，六份状态逐字匹配原宿主；正常/负控/恢复/重放4进程 | 完整RISC-V参考数值资格；没有目标EMU或应用性能资格。 |
| [scalar、强FR、TA](NATIVE_RESULT.md) | 37张K288矩阵→172Q/13尾块；6张K768 W2保留scalar；每正常进程9次完整forward和3份最终live state，4参考进程 | 真实候选输出推进各自状态；逐矩阵与完整状态通过。91.262%仅原MAC覆盖，不是周期收益。 |
| [RoPE目标阶段](NATIVE_RESULT.md) | 负控后3独立正常EMU；p2六层合并、自预热ABBA、192B准备计入；后补全部counter链复算 | 固定T17/ELF局部平均周期140101→19027.5，约7.36倍。未审计全部中间退休路径，不外推token或最佳通用非缓存实现。 |
| [真实投影目标边界](projection/target/RESULT.md) | classifier末320行和层索引5完整W1 768行；负控和3正常EMU、同ELF/同buffer、自预热ABBA、全协议与104条CSR链通过 | 固定边界TA均值周期分别少9.078110%/9.046628%；最慢TA对最快FR分别少8.356953%/8.584735%。FR锚点跨度1.311666%/0.659693%，不外推完整应用或通用优选。 |

scalar+RoPE-cache 与 scalar/FR/TA 是两份独立消费者。当前 projection 没有叠加 RoPE cache，不能把两组 PASS 写成组合已通过。官方代码、原验证器、旧冻结输入、R5默认及强RVV回退保持。

## 2. 实现选择与依据

### 完整状态与真实输入

宿主四路各有独立 RunState，逐位置比较完整 logits、所有 KV 行及其余状态，共16类 span；阶段序列、边界相邻关系、模型只读和方法间不别名也单独检查。生成器能去掉标记并恢复原正文，原样参考不改。RoPE缓存只在一次调用内复用24对角度，不跨token借用表。

完整参考消费者使用团队 memory-only entry。原AM startup在固定参考配置下遇到UART store access fault；诊断保留了mcause/mtval/mepc和原超时日志。各入口初始化自己的栈、FP状态与TLS，projection入口额外启用向量状态VS；继续使用原链接脚本、预编译库与NEMU，没有修改参考、模拟UART成功或跳过指令。

### 复用合格机器码，明确尾部成本

FR完整函数592B、TA完整函数764B在新最终ELF中逐字核对旧资格对象，且五个真实目标块另做最终ELF模型验证。W1/W3的192有效行和classifier的32有效行补到完整288行调用，补零权重和scale=1，再复制有效行。每个完整forward额外405504 MAC，原组内FP32运算顺序保持。

新目标边界覆盖完整W1和classifier最后320行，后者只验证尾部接入和对应成本；80%的局部补齐开销与完整classifier仅0.8%的补齐开销不可混用。预打包/预量化、小工作集selfwarm均属于显式条件，不能外推完整classifier约10MB工作集。

### 先判定数值，再安排后续优化

固定公开源码研究支持多行布局和输入复用，但FP16 scale、倒数乘法、FMA及unordered widening不能直接移植到本合同。实际宿主见证已经出现量化7→6和固定分母算术差一位。后续RMSNorm、量化和Softmax建议见 [RESEARCH.md](RESEARCH.md)；它们是条件方案，尚无新目标候选资格。

## 3. 最终运行对象身份

所有 SHA 为 SHA-256。完整源闭包、工具版本、外部输入、命令和原始回执仍以对应构建/campaign清单为准，不能只凭下表认定运行成功。

| 构建 | 实际最终 ELF | 实际正常 BIN |
|---|---|---|
| `smoke-build-03` | `1c0f4d865eec38034677401fa8d49ab411ec1d3df692d3c2e07add66b04a86ff` | `e7102b179f4d5817c5b17df67d20353d1d550a31b2e28d4c14f838bfc4eba220` |
| `full-build-06` | `134ad022298749c4227d47a5669a56ae5896822cabe46d9ca6e95aee939fc66b` | `ef5574af82e662cf8e82d20cc284c9c14025b2bfe0e0ae71502382db1322dccc` |
| `projection-build-04` | `6b04c2ff9e116c0741bbe902b37d65ff9d72fc9b8cca5cc451d7e336d8aa57e3` | `e41348ba3d173101f6a6ccb60d297497c40d0cb34cd911a3bebb2cb1d9169899` |
| `rope-build-05` | `ac07fa1b827627da26937a6854d39c7dd165d9f154474f8f6bb73666426009e5` | `91102427accaffd6327099b13f9f439edd6ba71d3d28611b5194c5b0e1961337` |
| `projection-target-build-02` | `f4c047768c095e09e0335257bb743515f4d37861cca3e46bc008f580c01ecaa3` | `292c5012e4f7637aea7c8c68c595ee8129d6d38226378886f697b027037e8a7f` |

固定EMU SHA `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`；参考共享库 SHA `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`；AM HEAD `086a238062fdfb3281b745a537b361983d0154b5`。原 `upstream/runq.c` 与 `observe.c` 的 SHA 分别保持 `ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548`、`92bd2986e8bca35dc2ed30d0338eac2a0c96ef6a54d766835c793ad6fb9e8236`。

## 4. 原始证据与离线复核

[evidence/index.json](evidence/index.json) 是发布包、发布SHA、原始路径、标签和实际恢复/复算回执的入口。[README](README.md) 给出完整命令。归档为内容寻址ZIP；大包只做原字节分片，恢复后必须按发布SHA核验全部对象，不把封存成功视为实验PASS。

| 发布组 | 原始文件/逻辑字节 | ZIP字节 | ZIP SHA-256 |
|---|---|---:|---|
| `host-v1` | 696 / 1,049,692,671 | 6,409,832 | `cad1baa7860ff11ee8c80bfb83c15fcc0bf60c8d77ffd204bef7446b3ebc9a9d` |
| `native-v1` | 1,341 / 4,102,216,583 | 208,708,000，13片 | `6ee185ee3c8dcab8cf03f2b4cc4c78cc74a35794e0c4c8ceb4d5c8570cfda67b` |
| `rope-v1` | 432 / 28,626,425 | 3,531,934 | `2fac84af398d2b60bebe639962fb5e80cef2ce1cc208277c8c5b341face889c9` |
| `target-v1` | 307 / 1,820,791,241 | 67,876,659，5片 | `92e0ad39890bc428c04c1412e8b5dc336957bcf8fb860b3a16a82d9c2723d1ee` |
| `delivery-v1` | 308 / 29,935,017 | 1,335,802 | `f4b4da49ebc56703d70d499150c2d426f6e88a193e5a563788f82c77c634e3a8` |

核心包含数学、完整双/三消费者、UART诊断、失败/中间构建、输入闭包和算术见证。RoPE包含全部RoPE构建/运行、后补counter原文审计、固定T17计时源码、计数器/fatal控制及控制首轮失败。target包保留两个投影边界的失败/最终构建、四进程原始证据和运行后输入复核；delivery包保留新旧离线工具、控制、恢复与复算决定、原操作回执及准备失败，重复原日志只在逐字验证后以完整映射引用target包。

五包均已实际完整恢复。数学/完整双消费者/三路投影已从恢复目录用冻结原验证器重算，负控身份和独立PID重新检查；正常/恢复/重放全部验证值相同。RoPE还实际重新解码原ELF/BIN中的围栏与CSR，用封存后补函数重建全部56条链，并逐字段匹配旧审计。投影目标的v4复算于06:47:18通过，再次重建四份日志的完整协议、custom PC和104条CSR链；06:49:35交付复核包恢复通过。原机物理硬件身份没有在离线步骤重检，没有增加EMU、参考进程或性能样本。

交付工具保留六项实际控制：小包完整恢复、已有输出保护、损坏分片、乱序分片、正常记录冒充负控、重复PID。旧工具确实接受合成的负控冒名，修复后拒绝；合成测试视图明确标识，不能计作新实际campaign。原文件未变。归档器另有20项文件系统/成员/对象控制，17拒绝、3正控。

## 5. 失败与未验证项

初次LSan环境失败、旧started/汇总不一致回执、初轮中断控制、数学重定位误判、UART超时、若干构建中间版、TLS地址被编译器折叠导致主体消失、目标首版GNU缩进告警、首轮计数器控制正则未真正改变输入，均保留原始证据。后续修复和新目录成功不回写旧状态。具体原因与适用范围见各结果页和原 `failure-review.json`。

尚未验证：完整新消费者的香山DiffTest、完整token周期、TA+RoPE-cache组合、训练checkpoint/tokenizer与质量、任意输入域或所有舍入模式、LeakSanitizer、新RTL/FU/ASIC面积和时序。本轮没有改RTL，因此没有启动无关综合或重复旧硬件回归。完整参考镜像的API/退休次数只用于复现与限额，不作为香山性能。

## 6. 使用、回退与接续

本模块为独立工程入口，构建/输出都在源码外。现有R5稳定入口保持；强FR与原scalar路径始终保留。新阶段的调用环境、最终ELF或输入改变后重新验证，不直接复制旧百分比。普通C的既有显式入口和FR回退仍从 [phased接口](../../fused/phased/README.md) 使用；新完整验证程序不冒充通用运行库。

下一步先评估完整调用链的目标验证与测量成本，明确验证和性能镜像的身份对应，再按目标端阶段数据选择K768 W2、量化、norm或非线性。这服务于项目的长期应用性能目标；当前赛题条款没有完整LLM token/s硬门槛，不应因此反复扩大昂贵仿真。各局部收益不可串乘，MAC份额不可当作周期份额。若完整目标成本暂不合理，使用能改变下一决策的具名边界，并保留完整应用仍未验证的结论。
