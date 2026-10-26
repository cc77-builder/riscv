# 固定上游完整 forward：调用观察与融合 Q 数值接续

2026-10-26；合同 [`r2-s3-runq-forward-host-v1`](CONTRACT.md)。结果 **`COMPLETE_UPSTREAM_FORWARD_HOST_AND_CAPTURED_Q_PASS`**。

本轮实际运行了固定版本 llama2.c 的完整 `forward`，捕获其中全部 Q/K/V/O 投影的真实量化输入，并把它们送入两个融合函数的固定 GNU ELF 有限机器码模型。它补齐了消费者调用、量化复用、一次 pack 后复用和状态生命周期的有界证据。完整上游 forward 仍然使用原 `matmul` 的结果；本结果不授予候选替换整模型、目标端运行、训练模型质量或完整应用性能资格。

## 1. 不变的上游和明确的输入身份

上游 [`karpathy/llama2.c`](https://github.com/karpathy/llama2.c/tree/350e04fe35433e6d2941dce5a1f53308f87058eb) 固定在 `350e04fe35433e6d2941dce5a1f53308f87058eb`。
随源码保留原 MIT 许可；[`upstream/runq.c`](upstream/runq.c) 为原 Git blob 的完整字节副本：

- Git blob：`42360ae97c724d28e11ac4545e30f57b7a9c9a8e`。
- SHA256：`ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548`。
- 长度：43,357 字节。使用上游已有的 `TESTING` 宏排除 CLI main，没有改写 `quantize`、`matmul`、`forward` 或参考判定。

配置为 D=288、H=768、L=6、heads=kvheads=6、vocab=32,000、seq=256、GS=32，依据固定 [训练默认值](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/train.py#L48-L58)、[hidden_dim 公式](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/model.py#L167-L176)、[量化组选择](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/export.py#L182-L195) 和 README 配置说明。没有下载 checkpoint，也没有声称核验过实际模型文件头。

测试权重使用固定 xorshift32 种子 `0x53485041` 生成 signed [-8,8] 字节和正的二进制精确尺度，是**确定性未训练权重**。按原 `memory_map_weights` 布局生成 17,101,440 字节权重，embedding/classifier 共享；原函数实际反量化得到 36,864,000 字节 embedding。每次完整 forward 后都对全部权重和 embedding 与原快照逐字节比对。

## 2. 实际运行和数值结果

| 验证层 | 实际完成范围 | 结果与限制 |
|---|---|---|
| 完整上游宿主 forward | 两套独立分配、清零的 RunState，各执行 token 1/7/19、位置 0/1/2，共 6 次 | 全部 32,000 logits 和完整 KV cache 在新状态重放中逐位相同；同进程、同实现、同只读权重，不是第二个独立算法 oracle |
| 原始调用观察 | 每次 43 matmul、25 quantize、13 RMSNorm、36 softmax；量化 315 组、10,080 元素 | 数量来自真实函数进入/退出记录，与固定源码调用图一致 |
| 被动 C 对照 | 144 次 Q/K/V/O 调用，以实际量化输入、固定 acc8 C 包装和普通 signed int8 host leaf 计算 | 每次完整 288 输出与原 matmul 逐位相同；结果仅比较，不写回上游状态 |
| 原始捕获 | 3 位置 × 6 层 × Q/K/V/O，共 72 个位置/矩阵案例 | 量化输入字节实际去重为 36 种；同层同位置 Q/K/V 输入必须相同，O 使用 attention 后的重新量化结果 |
| 融合 GNU ELF 有限模型 | 72 案例 × vdot/RVV4 两方法，共 144 条完整机器路径、41,472 个输出比较 | 全部通过；同时检查末组全部槽、ABI、CSR、输入只读、精确地址 footprint 和每 Q 的 324 个整数核；不是目标端/NEMU 执行 |

量化前读取实际 state 数组，检查所有数值有限、每组最大绝对值大于零、实际 binary32 尺度为正且有限，以及 `round` 后的值可转换为 int8；量化后再检查原函数实际写出的尺度。没有补丁改变上游全零组的行为；触及本合同输入域边界就失败并保存证据。

每次完整 forward 检查各层完整 256 行 KV cache：仅当前位置允许变化，当前行须有限且非退化；以前位置和未来位置均须保持原字节。三个真实的一位 logit 破坏均被比较器拒绝，然后恢复原值。第二套 RunState 重放的接受项是完整 logits/KV；不把它扩大为 72 份捕获文件各自重放。

24 份 Q/K/V/O 权重在所有 forward 之前各 pack 一次，新增 **1,990,656 字节（约 1.8984 MiB）**，之后跨位置、跨两套状态复用；每份 packed W 的全部 82,944 字节均有对应检查。量化激活不 pack。

## 3. 为什么不能把局部 Q 改善直接称为完整应用加速

固定上游 [forward](https://github.com/karpathy/llama2.c/blob/350e04fe35433e6d2941dce5a1f53308f87058eb/runq.c#L344-L479) 的形状给出以下 INT8 乘项清单。这里没有把 RMSNorm、RoPE、attention、softmax、SiLU、残差、量化或 KV 访问折算成乘项。

| 矩阵 | 输出 × 输入 | 每 forward 调用数 | INT8 乘项 | 乘项占比 |
|---|---|---:|---:|---:|
| Q | 288 × 288 | 6 | 497,664 | 3.2767% |
| K | 288 × 288 | 6 | 497,664 | 3.2767% |
| V | 288 × 288 | 6 | 497,664 | 3.2767% |
| O | 288 × 288 | 6 | 497,664 | 3.2767% |
| W1 | 768 × 288 | 6 | 1,327,104 | 8.7379% |
| W3 | 768 × 288 | 6 | 1,327,104 | 8.7379% |
| W2 | 288 × 768 | 6 | 1,327,104 | 8.7379% |
| classifier | 32,000 × 288 | 1 | 9,216,000 | 60.6796% |
| 合计 | — | **43** | **15,187,968** | **100%** |

一次 288×288 Q 为 82,944 乘项，占总量 0.5461%；六层 Q 合计 3.2767%；全部 24 次同形状 Q/K/V/O 为 13.1068%。共享 embedding/classifier 减少存储，没有消除最终 classifier 计算。attention 还随位置 `pos+1` 增长。

实际 Amdahl 计算必须使用**实测基线周期份额** `f_c`：`S = 1 / ((1-f_c) + f_c/s)`，其中 `s` 为对应部分的实际加速。只有在“INT8 乘项等成本、其他工作为零”的假设模型中，24 个 Q/K/V/O 局部 2× 才对应约 1.07013× 全体加速；这不是实测值，也不是真实应用加速上限。若局部加速为 2×，要达到整体 1.10×，其原周期份额需至少 18.18%；局部仅为 1.20× 时需至少 54.55%。

因此，本轮先完成融合 Q 的公平目标端比较；后续是否扩大到 W1/W2/W3/classifier，应由真实消费者的周期占比、维度约束和收益决定。不能仅凭分类器乘项最多，就把本轮固定 288×288 合同改造成未验证的大形状方案，也不为追加完整应用结论而直接启动昂贵的大模型 EMU。

## 4. 源码、机器码和证据

实现为 [`observe.c`](observe.c)、[`check.py`](check.py) 和固定上游副本。观察器 TU 使用 GCC 函数 instrumentation，回调和观察器辅助函数禁用自递归 instrumentation；固定 acc8 C 独立编译。关闭 OpenMP、LTO、FP contraction、fast math、自动向量化及相关跨过程优化，实际 affinity 为一个 CPU。

宿主为 x86_64 Linux / glibc 2.39 / Python 3.12.14。结果记录包含 GCC、实际 libm/libc/loader 的 SHA、完整构建/运行 argv 和原始 stdout/stderr；没有跨平台逐位相同承诺，也没有宿主时间向香山周期的换算。

| 身份 | SHA256 |
|---|---|
| 实际宿主可执行文件 | `53ed780cb5b11683290bb8904a68ec04c63705fe319af270f1d88263e9d588bb` |
| 固定 GNU 融合参考 ELF | `6975d57aecd77f9ec6337cbf3aa5b031033e8a7b86dcad4bcd7e78b33b2dc97d` |
| 原始证据 ZIP | `feb835c4f1e910676772a858ae39ce3f919d3e78d68d37a23ae3c04c9fed4985` |

参考 ELF 来自既有 [`fused` 静态验收](../fused/RESULT.md)，并非 [`fused/target`](../fused/target/CONTRACT.md) 的目标端 ELF；两者资格不能互相替代。

[`evidence/host-v1/raw.zip`](evidence/host-v1/raw.zip) 为本次实际云端隔离输入上的原始结果，254 个成员、15,628,095 字节原内容，ZIP 3,038,458 字节。包括 11 份源码快照、固定 ELF、宿主二进制/对象、实际命令/日志、result、捕获数值结果及 225 份捕获文件；捕获本体共 15,337,248 字节。成员长度/SHA 见 [`members.json`](evidence/host-v1/members.json)。转存到原生工作区时逐成员验字节；这次转存不冒称再次构建或再次执行了 forward。

## 5. 复现入口和当前结论

在有 GNU C 编译器、Python 3.10+ 和 glibc/libm 的 Linux 中，从仓库根执行，输出须位于仓库外且不存在：

```sh
python3 team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/check.py \
  --repo "$PWD" --output /absolute/outside-repo/new-forward-check
```

默认从固定 `fused/evidence/screen-v1/raw.zip` 读取并验 SHA 的实际 ELF；也可用 `--fused-elf` 指向同 SHA 的原 ELF。复现使用一个 CPU，不需要 checkpoint、RISC-V 工具链、EMU 或 NEMU。源文件、上游完整 Git blob、动态库在运行前后均受校验；失败输出保留。完整捕获已经随原证据保存，不要求运行者依赖原云端路径。

当前接受：完整消费者在限定输入上的可运行性、实际调用与生命周期、候选对消费者实际输入的数值适配。当前未接受：训练质量、候选替换后的完整模型执行、实际 token 延迟/吞吐、完整应用加速。R5 默认入口、官方参考实现以及已有性能 HOLD 均不因此改变。
