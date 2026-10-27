# 真实 K768 W2 与可选完整 forward 接入

本叶补齐固定模型的六张 W2：`M=288 / K=768 / GS=32`。提供强 RVV 的 `q768_fr`、自定义 vdot 的 `q768_ta`，以及含 scalar、FR、TA 和同政策 RoPE-cache 回退的独立 `consumer-w2.o`。最终结果、每项资格和原始证据见 [RESULT](RESULT.md)。

这里的目标计量对象是自然 forward 在 `p2/layer5` 的完整 W2；完整 forward 的组合验证另用原 NEMU。合同分别为 [W2 边界](CONTRACT.md)、[完整 consumer](consumer-CONTRACT.md) 和 [256 位置参考补充](sequence-CONTRACT.md)。完整参考状态相等不能代替完整香山 forward DiffTest 或 token 性能。

本批完整参考与 W2 目标正确性通过，性能选择为 **HOLD**：FR 四样本的跨度为 1.643809%，超过执行前冻结的 1% 门槛。保留全部样本与强 FR 回退，不据较低的 TA 原始周期推荐性能优选，也不切换 R5 默认。下方示例显式使用 `R2_FR_CACHE`；调用者可在本批已验证的固定条件内选择其他方法。

## 内核与精确数值顺序

[w2.h](w2.h) 的两个入口使用相同 56 字节 RV64 context。权重按 `P[t,g,r,k]=W[(8t+r)*768+32g+k]` 打包，共 `36×24×8×32=221184` 字节；scale 保留原 `[288][24]` 行布局。输入含 768 个 int8 和 24 个 FP32 scale，每次覆写 288 个 FP32 输出。

每一行严格按 group 0..23 执行：有符号 int32 dot32 转 FP32，乘该组权重 scale，再乘输入 scale，再与旧累计值相加。编译必须保持 RNE、禁 FMA contraction 和 fast-math。不把 K768 拆成三次独立浮点 Q 累加，因为那会改变左折叠顺序。

生成器从已固定的 Q288 FR/TA 源码仅派生三处几何常量。构建进一步比较实际 GNU ELF：FR/TA 全函数分别保持 592/764 字节，仅 scale 行跨度、group 计数与 tile 跨度的三个机器指令不同。其余指令逐字相等，新增局部标签独立命名。

```bash
python3 -B team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/w2/generate.py \
  --repo /absolute/source --output /absolute/new-w2-kernels
```

输出包含 `w2.S`、原父函数 `parents.S` 和完整生成身份。量化、权重打包、内存分配均由调用者在内核之外完成。接口对齐、非别名、FS/VS、VLEN128 和浮点条件见头文件；边界 harness 的 scalar wrapper 还使用原模型全局组长 `GS=32`。

## 可选完整 consumer

[consumer_w2.h](consumer_w2.h) 复用旧 consumer 的 state 和 method 枚举，公开独立 `r2_w2_init/reset/forward`。它增加一份 16 字节对齐的 `1,327,104B` 模型输入，按 layer 0..5 连续放六张 W2 pack。原权重、embedding、K288 pack 与 tail scales 的大小和所有权条件沿用旧接口。

```c
/* consumer.h 与 consumer_w2.h 均加入 include 路径。
 * 先核对五份 immutable 模型缓冲区与相应 packing。 */
static struct r2_consumer_state state;
if (r2_w2_init(weights, R2_CONSUMER_WEIGHT_BYTES,
               embedding, R2_CONSUMER_EMBEDDING_BYTES,
               packed, R2_CONSUMER_PACKED_BYTES,
               tail_scales, R2_CONSUMER_TAIL_SCALE_BYTES,
               w2_packed, R2_W2_PACKED_BYTES) != 0)
    return INIT_FAILED;
r2_w2_reset(&state);
float *logits = r2_w2_forward(&state, R2_FR_CACHE, token, position);
if (!logits) return FORWARD_REJECTED;
```

| 方法 | K288 投影 | 六层 K768 W2 | RoPE |
|---|---|---|---|
| `R2_SCALAR` | 原 scalar | 原 scalar | 原实现 |
| `R2_FR` | 强 FR | `q768_fr` | 原实现 |
| `R2_TA` | TA | `q768_ta` | 原实现 |
| `R2_FR_CACHE` | 强 FR | `q768_fr` | 每次 forward 内的同政策缓存 |
| `R2_TA_CACHE` | TA | `q768_ta` | 同上 |

初始化失败会清除绑定。修正输入并重新成功初始化，再 reset 独立 state，从位置 0 按连续位置推进。模型缓冲区必须保持存活、不可变且与状态不重叠。模型绑定是单实例，资格只包括独立状态的顺序交错使用，未覆盖并发重绑定或多线程。

旧 `consumer.o` 与新 `consumer-w2.o` 是二选一的完整 consumer 对象：二者都包含上游全局函数和 `GS`，不能因为公开接口改名便推定能同时链接。新对象内部已有五种显式方法，回退 TA-cache 时选择同缓存政策的 FR-cache，需要原 scalar 时选择 `R2_SCALAR`。

`consumer-w2.o` 是完整计算核心对象，仍需按本批合格构建的链接输入配齐 Q288 汇编、由 `w2.S` 构建的 K768 汇编以及运行库。替换时移除旧 `consumer.o`，不要再单独链接另一份 `runq.c` 或重复的 consumer 实现。独立边界入口使用 [w2.h](w2.h) 和生成的 `w2.S`；完整 consumer 的生成源码和准确链接命令保存在构建证据中。

## 构建与验证入口

所有输出必须是源码之外、尚不存在的新目录。示例变量应指向经证据清单核对的输入，不能只更改 JSON 中的路径来跳过身份检查。

```bash
module=/absolute/source/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/w2
work=/absolute/new-w2-run
# full_build: 原 full-build-06
# kernel_build: 原 projection-target-build-02
# parent_consumer: 原 consumer/build-02
# adapter: 原 reference-adapter-04；identity: 同 T17 parent-identity.json
taskset -c 3 python3 -B "$module/build.py" --output "$work/build" \
  --full-build "$full_build" --kernel-build "$kernel_build"
taskset -c 3 python3 -B "$module/reference.py" --build "$work/build" \
  --adapter "$adapter" --identity "$identity" --output "$work/reference"
taskset -c 0-2 python3 -B "$module/run.py" --build "$work/build" \
  --reference "$work/reference" --identity "$identity" --output "$work/target" \
  --cpu-count 3 --operation-id unique-w2-campaign
```

目标实验先通过完整应用负控，再运行正常、恢复与独立重放。每个窗口先执行同方法完整 W2 并检查结果，再重置输出/slots/CSR/flags，计量整个 C apply。向量顺序为 ABBA/BAAB，scalar 单列。全部 custom retirement PC 与 full128 算术、四 CSR 的实际机器码和 enqueue/sample/retire 链均从原始日志核对。原日志、计量值和失败证据保持，不以 host wall time 衡量 guest 性能。

目标运行最多占 CPU0..2；其余任务须计入用户授权的总四核预算，不能重复使用正在运行的 CPU。新的函数、构建、输入或合同需独立验证。每次恢复先检查 state、进程组和输入保护，不能据 shell 退出就自动重跑。

```bash
taskset -c 3 python3 -B "$module/consumer_build.py" \
  --parent-build "$parent_consumer" --w2-build "$work/build" \
  --output "$work/consumer-build"
taskset -c 3 python3 -B "$module/consumer_run.py" \
  --build "$work/consumer-build" --adapter "$adapter" --identity "$identity" \
  --output "$work/consumer-reference"
taskset -c 3 python3 -B "$module/api.py" build --parent "$work/consumer-build" \
  --campaign "$work/consumer-reference" --output "$work/api-build"
taskset -c 3 python3 -B "$module/api.py" run --build "$work/api-build" \
  --adapter "$adapter" --identity "$identity" --output "$work/api-reference"
```

新完整 consumer 以第十项 dump 回读全部 W2 pack，五方法的自然 token 1/7/19 和 p0..2 各自比较完整 3,691,424 字节状态。应用负控翻转实际最后 logit；两条 pack 负控仅改变同 ELF 的 W2 数据，检查真实数据依赖。后者单独不宣称六层逐层动态覆盖；六层映射由静态指针/地址核对和正常完整状态比较共同支撑。

生成目录提供实际 GNU 链接使用的 `source/consumer.c`、`consumer.inc`、头文件和原 `upstream/runq.c`，以及独立 `consumer-w2.o`。核心对象不包含 oracle、快照、报告或计时回调；验证包装单独链接它。原始生成器/官方源码的身份与许可证保持。

[api.py](api.py) 直接链接这个已合格对象，不重编译核心；从固定旧双状态 harness 完整可逆派生。它增加新 pack 的 NULL、长度少 1 和未对齐指针三组失败初始化与恢复检查；最终须观察到 13 次 forward 拒绝、5 次失败 init、6 次有效 init、5 次有效 forward 和六对完整状态快照。八项内存 dump 覆盖两个带保护区的 live state、完整快照及全部五份模型；TLS/errno、RNE、flags 与模型不可变性同时检查。大快照只属于测试镜像，不是调用者必须保留的运行存储。

### 完整支持序列的独立补充

[sequence.c](sequence.c) 同样链接已合格核心对象，使用 scalar、FR-cache、TA-cache 三个独立 state。每位置按固定 token 计划完成三次实际 forward，比较全部状态、fcsr、errno 和 guards；前三位置再与原 host gold 比较。正常完成时报告 768 次有效 forward、512 次全状态比较、三个 host 前缀比较和三个 p256 越界拒绝。实际最后 logit 的 one-bit 负控使用同一比较逻辑。

普通参考旧 team adapter 的 10G 调用上限不足以覆盖该标量对照。补充只对它派生独立 48G 上限版本，完整源码可反向恢复；原 adapter、官方 NEMU 及数值/终态判据保持。正常上限 2400 秒，超限明确失败，不自动扩大预算。新 adapter 的构建、来源和实际使用身份都单独封存。

```bash
taskset -c 3 python3 -B "$module/sequence_build.py" \
  --parent "$work/api-build" --campaign "$work/api-reference" \
  --output "$work/sequence-build"
taskset -c 3 python3 -B "$module/sequence_run.py" adapter \
  --parent "$adapter" --output "$work/sequence-adapter"
taskset -c 3 python3 -B "$module/sequence_run.py" run \
  --build "$work/sequence-build" --adapter "$work/sequence-adapter" \
  --original-adapter "$adapter" --identity "$identity" \
  --output "$work/sequence-reference"
```

这是固定未训练模型、固定 token 序列、三种方法 p0..255 的参考正确性补充，不是五方法全范围、第二次完整序列独立重放或香山应用周期。实际完成与复算结果见 [RESULT](RESULT.md)。

## 原字节恢复与离线复核

[evidence.py](evidence.py) 只为已闭合的输出准备精确副本、补齐当时 `runtime-inputs.json` 所固定的源码闭包，再调用原 [archive.py](../archive.py) 的 SHA256 对象去重。没有图像或 dump 重建配方；相同完整文件共用一个对象，不同文件保持各自原字节。20 MiB 分片使用原 [restore.py](../restore.py) 拼回同一 ZIP。

证据索引给出每包的 manifest 与 ZIP SHA。`published_parts` 指向所选 `evidence/<包名>`；`published_zip_sha`、`published_manifest_sha` 从该包的索引记录取值；`joined`、`restored`、`fresh_recheck` 必须是源码之外尚不存在的新目录。先恢复原归档，再按包类型复算：

```bash
python3 -B "$module/../restore.py" --archive "$published_parts" --output "$joined"
python3 -B "$module/../archive.py" verify --archive "$joined/payload.zip" \
  --expected-sha256 "$published_zip_sha" --output "$restored"
taskset -c 3 python3 -B "$module/recheck.py" --kind core --root "$restored" \
  --manifest "$joined/manifest.json" --expected-manifest-sha256 "$published_manifest_sha" \
  --output "$fresh_recheck"
```

| 包 | `--kind` | 离线复核范围 |
|---|---|---|
| core | `core` | 3 个边界参考、10 个完整 consumer、1 个双状态 API 案例 |
| failures | `failed-target` | 原严格退出门仍拒绝旧 false-GOOD；其他失败文件按 manifest 原字节恢复 |
| sequence | `sequence` | 两进程完整 raw、256 位置报告/状态、同核心/四内核及 48G adapter 完整可逆派生 |
| target | `target` | 实际四个 EMU 的完整原日志、CSR/custom 协议、精确重放及公平比较 |

只映射 core/API 的资格数据目录和 target 的 image 参数内存副本，原 JSON 保持原字节；sequence 无需数据路径映射。离线复算不会执行新的 NEMU/EMU，也不重新认证原机器上的物理 RTL、工具或官方运行环境。归档恢复原文件字节，不保存可执行权限；要重新运行构建或程序，还须依照冻结身份准备原外部环境。

## 使用边界与恢复

资格绑定固定 D288/H768/L6/HQ6/HKV6/V32000/S256/GS32、确定性未训练 fixture、RNE 和本批工具/硬件身份。它不包括任意 checkpoint、模型质量、长上下文、多线程、冷模型加载或新的 ASIC PPA。实际较快的合格 RVV 始终保留，是否采用 TA 由同计划的公平比较门槛决定。

完整证据、失败原因、逐文件恢复及使用原验证器重新计算的命令列在 [RESULT](RESULT.md) 和证据索引。原始运行与离线复算分别记录；复算不冒称重新执行了目标。
