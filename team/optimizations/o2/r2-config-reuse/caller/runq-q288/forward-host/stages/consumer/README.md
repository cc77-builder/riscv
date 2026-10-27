# 固定模型纯 forward 消费者

本模块把完整前向计算与观察、转储及结果比较分开，提供显式的 scalar、强 FR、TA 及其 RoPE-cache 组合。五条路径已在原正常 NEMU 参考中完成独立三位置完整状态验证；双状态交错、初始化失败恢复和真实应用负例另有验证。**完整香山 forward DiffTest 与性能尚未取得资格。** 实际结果、证据和成本决策见 [RESULT](RESULT.md)。

这是固定 `D288/H768/L6/HQ6/HKV6/V32000/S256/GS32`、确定性未训练 fixture 的工程入口。源码生成依赖原样 `upstream/runq.c`、生成的 `consumer.inc`、`q288.h` 和已合格 FR/TA 目标符号；应使用下述构建入口生成完整输入。初始化不会加载任意 checkpoint 或 tokenizer。

## 接口与方法

公开接口见 [consumer.h](consumer.h)，语义和验收依据见 [计算合同](CONTRACT.md) 与 [共享对象/目标合同](TARGET-CONTRACT.md)。

| 方法 | 投影路径 | RoPE |
|---|---|---|
| `R2_SCALAR` | 原 scalar | 原实现 |
| `R2_FR` | 强 FR | 原实现 |
| `R2_TA` | TA | 原实现 |
| `R2_FR_CACHE` | 强 FR | 每次调用内准备并复用 24 对角度 |
| `R2_TA_CACHE` | TA | 同一缓存政策 |

37 张 K288 矩阵接入 172 个完整 Q 调用和 13 个补齐尾块；六张 K768 W2 仍使用原 scalar 左折叠。cache 准备属于每次完整 forward，未移到计时区外。

| 调用者持有的输入 | 精确字节数 | 地址对齐 |
|---|---:|---:|
| 权重 | 17,101,440 | 4 |
| FP32 embedding | 36,864,000 | 4 |
| packed 权重 | 14,266,368 | 16 |
| tail scales | 134,784 | 4 |
| 每个 `r2_consumer_state` | 3,691,424 | 类型所需对齐 |

`r2_consumer_init()` 成功返回 0，失败返回 -1 并清除全局绑定。它检查指针、长度、对齐与固定布局；模型内容及 packing 对应关系由构建/运行包装器验证。即使使用 scalar 方法，当前接口也要求四份模型输入齐全。输入缓冲区由调用者管理，必须在使用期间存活且不可写。

先成功初始化，再为每条序列分配独立、不重叠且不与模型重叠的状态，调用 `r2_consumer_reset()`。从位置 0 连续推进；位置连续性与非别名是调用者前提，API 不替代这两项检查。正常 `forward` 返回该状态内部的 32,000 个 logits，后续同状态调用或 reset 会覆盖它们；范围错误、空状态或未初始化返回 NULL。

```c
/* 先由合格构建装载并核对 weights / embedding / packed / tail_scales。 */
static struct r2_consumer_state state;
if (r2_consumer_init(weights, R2_CONSUMER_WEIGHT_BYTES,
                     embedding, R2_CONSUMER_EMBEDDING_BYTES,
                     packed, R2_CONSUMER_PACKED_BYTES,
                     tail_scales, R2_CONSUMER_TAIL_SCALE_BYTES) != 0)
    return INIT_FAILED;
r2_consumer_reset(&state);
const int tokens[3] = {1, 7, 19};
for (int p = 0; p < 3; ++p) {
    float *logits = r2_consumer_forward(&state, R2_TA_CACHE, tokens[p], p);
    if (!logits) return FORWARD_REJECTED;
    /* 在下一次调用前消费 logits。 */
}
```

目标环境为该批核对的 RV64 LP64D、VLEN128、RNE、FS/VS 及对应内核。模型绑定为单实例；已验证的是独立状态的顺序交错调用，尚未验证多线程或调用中重新绑定。固定 fixture 的量化域要求有限数、每组非零最大绝对值和可表示转换；当前 API 不提供任意模型数据的通用域修复。

## 构建与真实参考验证

所有输出均须在源码外、使用未存在的新目录。实际工具、AM/libm、原 NEMU、flash、T17 与继承输入必须通过冻结清单；不能只改绝对路径字符串来绕过身份验证。以下变量由使用者指向已验证输入：

```bash
repo=$(git rev-parse --show-toplevel)
module="$repo/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/consumer"
work=/absolute/new-consumer-run
# full_build: 旧 full-build-06；kernel_build: 合格 active target-build-03
# adapter: 原 reference-adapter-04；identity: 对应 parent-identity.json
python3 -B "$module/build.py" --output "$work/build" \
  --full-build "$full_build" --kernel-build "$kernel_build"
python3 -B "$module/run.py" --build "$work/build" --adapter "$adapter" \
  --identity "$identity" --output "$work/reference" --cpus 0,1,2
```

运行次序为真实负例、五方法、恢复与独立重放，共八个实际进程；每个正常方法自然执行 tokens `[1,7,19]`、p0..2，每次比较完整 3,691,424 字节状态及全部模型字节。运行器保留每个进程组的真实终态；启动器退出本身不能解除子进程归属。

API 与目标包装链接同一已通过参考验证的 `consumer.o`，不重新编译核心：

```bash
python3 -B "$module/aux_build.py" --kind api --parent "$work/build" \
  --campaign "$work/reference" --output "$work/api-build"
python3 -B "$module/aux_run.py" --build "$work/api-build" --adapter "$adapter" \
  --identity "$identity" --output "$work/api-reference"
python3 -B "$module/aux_build.py" --kind target --parent "$work/build" \
  --campaign "$work/reference" --output "$work/target-build"
python3 -B "$module/aux_run.py" --build "$work/target-build" --adapter "$adapter" \
  --identity "$identity" --output "$work/target-reference"
```

目标包装的独立参考验证通过显式数据控制关闭 UART；原正常 NEMU 单独执行时不支持该 AM UART。实际目标必须打开 UART、使用原 DiffTest，不跳过任何参考指令或模拟成功。

## 成本探测与日志工具

本轮实际目标探测为 TA+cache、p0/token1、单 CPU、30 万 guest cycles、1,200 秒和每日志 128 MiB 上限。原 `--log-end=0` 不会关闭裸 O2/T13 输出，也不关闭 DiffTest；原始日志完整保存。探测没有完成 forward，只能说明本次前缀的运行与日志成本。

```bash
taskset -c 0 python3 -B "$module/target_run.py" \
  --build "$work/target-build" --reference-campaign "$work/target-reference" \
  --adapter "$adapter" --identity "$identity" --output "$work/probe" \
  --method 4 --max-cycles 300000 --timeout 1200 --log-mib 128 \
  --operation-id unique-consumer-cost-probe
python3 -B "$module/audit_probe.py" --probe "$work/probe" \
  --output "$work/probe-audit"
```

`audit_probe.py` 是本次固定截断 profile 的复查器，要求真实 cycle limit、未完成 ROB、仅两个已退休的起始 CSR 读数，并要求原 complete checker 拒绝；它不会为完成的长运行授予完整资格。未来完整目标实验需另行闭合完整状态、终态、计数器链与公平重放。

新的 [stream_audit.py](stream_audit.py) 按完整周期保存状态，检查每个原协议和 full128 算术条件；完整原日志仍是证据。它保留显式资源上限，超限拒绝，不截断数据。范围见 [STREAM-CONTRACT](STREAM-CONTRACT.md)。

```bash
python3 -B "$module/check_stream.py" --output "$work/stream-controls"
python3 -B "$module/check_saved_protocol.py" --output "$work/json-controls"
python3 -B "$module/recheck_stream.py" --baseline "$frozen_boundary_run" \
  --output "$work/boundary-stream-review"
python3 -B "$module/stream_audit.py" "$stderr_log" "$stdout_log" \
  --partial --output "$work/prefix-protocol"
```

`recheck_stream.py` 对固定旧投影运行的每笔有序 transaction、所有协议摘要、提交 PC 流、T13 链和应用 `TILE_` transcript 做比较，并连接旧回执内的代码/ELF SHA。该入口仍需那些原绝对路径存在；它不是可任意搬迁的旧运行加载器。通用 `stream_audit.py` 可直接读取已恢复的日志，不访问旧硬件路径。

## 证据恢复与回退

发布包、字节 SHA、根目录和实际恢复结果见 [证据索引](evidence/index.json)。复用上级 `restore.py` 和 `archive.py verify` 恢复原文件；`recheck.py` 在恢复目录调用各原 campaign 捕获的验证器，重新计算全部 21 个参考案例。它不启动参考或 EMU，不访问历史 PID；数值复算与物理运行环境的重新资格分开记录。完整命令见 RESULT 的恢复说明。

回退 TA+cache 时选 `R2_FR_CACHE`，保持相同缓存政策；需要排除缓存因素时选 `R2_FR` 或 `R2_SCALAR`。发生异常、状态不明或初始化失败后，修正输入并成功初始化，reset 或换一个独立状态，再从位置 0 重放相同前缀。R5 稳定默认及既有普通 C 库保持原有入口；此模块的显式方法选择不改变默认版本。

当前没有新长上下文、任意 checkpoint、文本质量、多线程、冷模型加载、完整 token 周期/steady-state token/s 或 ASIC PPA 结论。局部历史收益、独立参考指令数和本次仿真主机耗时均不转化为完整应用加速比。
