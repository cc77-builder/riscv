# Paired16 完整消费者独立入口：有界参考正确性

合同：`r2-s3-forward-consumer-paired16-v1`。本叶对应 Issue #2 WORK6675138317；只新增可显式调用的入口，不修改稳定默认选择，不解除父 paired16 性能合同的 `HOLD_CONTEXT_VARIATION`。

## 规格与最小接入

新增 `r2_w2_paired16_forward(state, token, position)`，复用已有 `r2_w2_init/reset` 及 `consumer.h` 的所有权、对齐和连续位置约定。固定模型 D288/H768/L6/HQ6/HKV6/V32000/S256/GS32，旧方法枚举 0–4 和方法 5 非法域均不改。新入口标签为 `0x50313631`，不是旧方法枚举值。

直接父源码仍为实际 norm/W2 `consumer-build-02`：result SHA `8ad05a4aa3bee2bd23d14f698c43ebfa445703aa19e2f2951d079b655d76482d`。原 FR-cache 的完整函数复制后，仅将 Q/K/V、Wo、W1/W3、classifier 七处 K288 路由改到 `q288_paired16_rvv`。唯一 W2 行逐字保留原 `route_fr`，因而仍选择 `q768_fr`。不能全局替换八处调用；原路由器根据 K288 函数指针决定 W2 的 FR/TA 分支。所有旧函数、旧公开 API、初始化及状态布局原样保留。

新克隆除名字及七个路由名外，必须能逐字逆向恢复为原 FR-cache 模板。量化、模型打包、尺度、norm、RoPE cache、attention、SwiGLU、FP32 运算顺序和状态写入均不改变。K288 对外使用原六指针上下文；寄存器/CSR/槽契约沿用父 paired16 合同，不增加 ISA。

## 完整 P 函数身份

仅从原 `host-01/generated/paired16.S` 的 `.balign 64` 与 `q288_paired16_rvv` 入口到其唯一 `.size` 提取完整函数，保留 `.option norvc`、`.option norelax`。完整体为 1,096 字节，SHA `a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c`；包括 288 字节 X 扫描、快速计算和 592 字节内嵌 FR 回退。不能在 fast_end、fallback_begin 或第一个 ret 截断。

P 的快速支路仅在 X 不含 −128 时使用两项 INT8 乘积的 INT16 累加；检测到 −128 则完整执行原 FR 回退。因此接入不缩小 signed INT8 输入域。旧 host ELF SHA 为 `fb3c030efa7aa347029a69f6aabe82c912cbbb85294b27cf407a01ea58a314f3`，原 screen 为 `PAIRED16_ACTUAL_ELF_NUMERIC_PASS`（19 正例、6 实际 ELF 负控）。这些是内核既有证据，新消费者仍须独立验证。

## 复用控制器与构建

`bind.py` 以固定 SHA 读取 GS32 消费者的三个自研控制器，在新的外部目录生成 P 专用 `derive.py/build.py/run.py`。每一项改动记录原文、新文、出现次数和位置，逐项及整文件逆向恢复原始 SHA。只改新入口/文件/状态身份、P 原始 screen 路径、完整函数检查及显式支持快照参数。旧 `GS32_REFERENCE_SUPPORT_SNAPSHOT_COMPLETE` 与 `GS32_ORIGINAL_SCALAR_SUBSET_RESTORED` 是历史证据身份，必须保持原文；不能通过换名伪造 P 验证结果。

此派生只复用实现，不继承消费者 PASS。原 GS32 文件不回写，生成的三个控制器须在独立 Python 进程从新目录导入，避免裸 `import build/derive` 命中旧模块。生成清单、输入 SHA 和派生器本体进入新构建与运行输入清单。

复用已有 95 文件 `consumer-support-02` 闭合快照及 `scalar-audit-01` 中从原档案逐字恢复的 scalar 证据；不再生成 golden，不修改历史快照，不重跑旧八方法 campaign。原数值验证器和进程 owner 保持原 SHA。父源码、工具、官方 AM、libm、norm 两个对象、五个模型数组及独立 host golden 均按既有身份核验。官方权威程序不改。

新输出只写隔离目录。实际 GNU 编译复用父编译参数：`-O2`、`-ffp-contract=off`、`-fno-fast-math`、原禁用自动向量化/ISA/ABI，仅替换新源与对象路径；单核、`-j1`。实际 ELF 中完整 P 函数须逐字等于原 host ELF，四个原 K288/K768 汇编函数同样保持，norm 只允许既有检查器接受的链接修正。ELF/BIN 一致性、TLS、全模型及观测区初值均核验。

运行前独立审查实际 ELF 中七处 K288 与 W2 FR 的所有八个调用、真实函数指针准备、W2 的指针比较、旧方法 5 的拒绝及新公开入口的真实调用。证据必须使用新 ELF 的实际地址/机器字，不能只替换旧 review 的 SHA 或凭源代码宣称路由成立。

## 三个独立参考进程

固定 negative → recovery → replay，最多一个参考进程，使用既有 `reference-adapter-04` 和 SHA `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9` 的参考库，不开新 EMU。

1. negative 运行新入口第 0 步，在 guest 中翻转最后一个 logit 的最低位；须 exit2/BAD94，完整原状态比较器在 byte 152476 拒绝，整份状态只允许这个预定比特不同。
2. recovery 新进程执行 tokens 1、7、19 / positions 0、1、2。每步完整 3,691,424 字节状态与原独立 host golden 相同，最终 live state 一致，五个模型数组不变，未使用快照/flags/time 区保持零。
3. replay 又一新进程完整复现 recovery 的状态、flags、参考退休量和参考计数样本。它验证确定性，不增加独立性能样本。

原 W2 `validate()` 数值和过程判定仅通过其既有 bind helper 绑定新镜像构造函数。新协议入口标签进入独立控制/报告字段，不传给旧方法分派。外层使用本合同、P 新入口身份，并明确保存原验证器输出。

运行前重审旧 scalar 实际 raw dump 和回执；新入口三步 fflags 须逐项等于 `[1,1,1]`，保持 RNE。实际 guest 检查未初始化、新入口空状态、越界 token/position 均返回 NULL 且状态无修改，以及旧方法 5 仍返回 NULL。记录 PID、独立进程组、真实退出和回收，未知回收/输入漂移不得 PASS。失败输出与原输入保留，不回写旧结果。

## 资格、比较与回退

PASS 只授予这一固定合成模型、三个连续位置的新消费者参考正确性，不自动覆盖全 256 步、任意模型、训练质量、双状态并发隔离、目标整核或完整应用周期。正确性 harness 的两次全状态零扫描会影响缓存准备，不能直接将其计数与另一种前置流程的 ELF 当作公平性能比较。

父 P 原目标合同仍为 `HOLD_CONTEXT_VARIATION`；原四臂 raw 周期信号不因本叶 PASS 升级为性能资格。若后续比较完整应用，须新合同明确相同完整路径边界、候选硬件/参考身份、初始化与 cache 准备、输入、调用顺序、结果判定和较快合格 RVV 对照。当前只保留事实性的参考退休诊断，不称为香山周期或完整应用加速。

原命名入口、旧消费者和父对象保留，调用者选择旧入口即可回退。本叶不变更默认选择、ISA 或共享发布规则。
