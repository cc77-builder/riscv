# 完整 forward、参考消费者与目标阶段入口

本子项贯通了完整宿主阶段接口、实际 RISC-V 数学/TLS、完整参考消费者和有界目标阶段。阶段覆盖 embedding、RoPE、每层 QKV/attention/FFN，以及最终 norm/quantize/classifier。原样 `runq.c`、官方 AM/NEMU/DiffTest、既有内核和 R5 默认保持。先从 [交付总览](RESULT.md) 阅读实际资格，再进入对应合同；不同实验的 PASS 不互相转借。

| 入口 | 用途与结果 |
|---|---|
| [宿主合同](CONTRACT.md) / [宿主结果](HOST_RESULT.md) | 连续 256 位置的四路完整状态与阶段边界；最终运行器三位置故障与 sanitizer 检查。 |
| [数学闭包](target/CONTRACT.md) / [目标探针合同](target/SMOKE-CONTRACT.md) | 实际 libm archive 选择、单 hart TLS、数学/errno/flags 与真实目标负控。 |
| [双消费者合同](full/CONTRACT.md) / [原生结果](NATIVE_RESULT.md) | 原 scalar 与 RoPE-cache 独立状态，三位置完整参考执行；目标 EMU 次数为 0。 |
| [三消费者合同](projection/CONTRACT.md) / [原生结果](NATIVE_RESULT.md) | 原 scalar、强 FR、TA；37 张 K288/172Q/13 尾块，6 张 K768 W2 仍 scalar。 |
| [RoPE 目标合同](rope/CONTRACT.md) / [计时范围](NATIVE_RESULT.md) | 固定 p2 六层合并、自预热、准备计入的局部目标边界。 |
| [投影目标合同](projection/target/CONTRACT.md) / [目标结果](projection/target/RESULT.md) | 真实 p2、层索引5的完整 W1 与 classifier 最后320行，强 FR/TA 同 buffer 比较。 |
| [研究与决策](RESEARCH.md) | 固定公开源、实际算术反例及严格 RVV 后续候选的条件。 |

完整参考消费者中的 RoPE-cache 与 TA/FR 是两份独立实验，没有授予 TA+RoPE-cache 组合资格。完整目标 forward/token、训练模型质量和新 ASIC PPA 尚未验证。

## 宿主重新执行

需要 Linux、Python 3.10+、GCC、binutils、glibc/libm。输出必须在源码之外且尚不存在；进程自动限制到一个可用 CPU。以下命令默认检查 256 个连续位置，约束来自已有 seq256 模型，并非新增模型质量评测。

```bash
repo=$(git rev-parse --show-toplevel)
module="$repo/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages"
python3 -B "$module/check.py" --repo "$repo" \
  --output /absolute/new-forward-stages-run --sanitize
```

需要更短的接口检查可显式加 `--extended-positions 3`；它只取得三位置资格，不冒充 256 位置验收。`--sanitize` 检查 AddressSanitizer、不可恢复 UBSan 和浮点到整数转换，不运行 LeakSanitizer；首轮执行环境的泄漏扫描失败另行保存。所有 sanitizer stderr 必须为空才能通过。

运行输出包括源码原字节、生成的完整函数、编译/链接命令和终态、二进制、动态库身份、119 段的原始时间戳、四路完整状态以及真实拒错日志。四路分别为：

| method | 实际函数 | 用途 |
| --- | --- | --- |
| 0 | 原样 `forward` | 参考，全位置完整状态比较 |
| 1 | 原算法加阶段标记 | 验证标记不改变状态 |
| 2 | 角度复用候选加阶段标记 | 观察准备与执行边界 |
| 3 | 无阶段标记的角度复用候选 | 验证候选独立于标记仍正确 |

验证版在三条派生路径量化前检查定义域，先执行验证后的原算法，再调用原样参考。timing 版直接使用原量化器，检查、文件输出和完整比较位于外侧调用窗口之后。每一路始终沿自身 KV 状态前进；不同方法共享只读权重。

RoPE 候选每次调用计算 24 对角度，供六层/六头复用。两个局部 FP32 数组逻辑容量为 192 B；实际栈帧以编译产物为准。准备位于完整调用之内，不借用上一 token 的表。恢复原算法可直接使用 method 0/1；该候选没有改动 R5，也未集成到 TA/FR 目标入口。

## 如何读时间

`stages.csv` 的时钟是 **宿主进程 CPU 纳秒**。每条记录是半开区间，119 段相加恰好等于首末标记跨度；`outer_ns` 是包含入口和返回的完整函数调用，两者差值单列保留。标记开销没有扣除，固定顺序与前后的完整检查也会影响缓存上下文。

这些数字用于核查探针和阶段覆盖。验证构建还包含量化合法域检查，其时间不用于性能。宿主 scalar matmul、不同布局和当前库调用不能代替香山上的 TA/强 RVV 比较；`performance_qualified=false`、`target_runtime_ready=false` 是有意保留的边界。

GCC 的实际最终宿主二进制含 `powf`、`sincosf`、`expf`、`sqrtf`、`roundf`。其中 sin/cos 与 round 的源码形式经编译器转换，不应仅按源码函数名准备目标依赖。原始 `nm` 和反汇编随证据保存。

## 运行器故障控制

先完成一个成功运行，再在新的输出目录执行：

```bash
python3 -B "$module/test_runner.py" --repo "$repo" \
  --accepted-run /absolute/accepted-forward-stages-run \
  --output /absolute/new-runner-controls
```

这会真实启动受控父子进程，检查超时、中断、父进程退出后残留子进程的处置；还检查已有输出保护、错误参考、篡改阶段原文及 sanitizer 的真实拒错。少量有界等待用于确认已启动子进程不能在约定延时后继续写入。信号/回执异常必须保留为失败，不能从后继文件补造旧终态。

## 不启动仿真的证据恢复与复算

证据使用内容寻址 ZIP，重复文件只保存一个 SHA256 对象；大 ZIP 以原始字节分片发布。先恢复传输，再验证发布 SHA 和每个对象，最后用冻结验证器重算原文。恢复目录必须是源码外尚不存在的新路径，不能覆盖旧输入。只读审查不需要新 Git 检出。

下面是核心包的完整示例，Linux/Python 3.10+ 即可；不调用交叉编译器、EMU 或原机 NEMU 路径。`work` 指可写的新输出父目录。

```bash
repo=$(git rev-parse --show-toplevel)
module="$repo/team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages"
work=/absolute/new-forward-review
python3 -B "$module/restore.py" --archive "$module/evidence/native-v1" \
  --output "$work/core-zip"
python3 -B "$module/archive.py" verify --archive "$work/core-zip/payload.zip" \
  --expected-sha256 6ee185ee3c8dcab8cf03f2b4cc4c78cc74a35794e0c4c8ceb4d5c8570cfda67b \
  --output "$work/core"
python3 -B "$module/recheck.py" --kind math \
  --build "$work/core/smoke-build-03" --campaign "$work/core/smoke-campaign-01" \
  --output "$work/math-review"
python3 -B "$module/recheck.py" --kind full \
  --build "$work/core/full-build-06" --campaign "$work/core/full-campaign-01" \
  --output "$work/full-review"
python3 -B "$module/recheck.py" --kind projection \
  --build "$work/core/projection-build-04" --campaign "$work/core/projection-campaign-01" \
  --output "$work/projection-review"
```

其他包的 SHA、相对根目录及实际恢复回执见 [交付索引](evidence/index.json)。宿主包已是单个 ZIP，直接执行 `archive.py verify`；不用先运行 `restore.py`。RoPE 与投影目标分别使用 `--kind rope` / `--kind boundary`、各自冻结 build/campaign 和新的输出目录。boundary 复算会在新 audit/work 中复制完整原始日志并重建协议、custom PC 与计数器链，需为原日志和派生文件留出空间。

RoPE 的后补计数器资格需显式带 `--counter-audit`。假设 `rope-v1` 已按其发布 SHA 恢复到 `$work/rope`：

```bash
python3 -B "$module/recheck.py" --kind rope \
  --build "$work/rope/rope-build-05" --campaign "$work/rope/rope-campaign-01" \
  --counter-audit "$work/rope/rope-counter-recheck-01" \
  --output "$work/rope-review"
```

这会先运行原冻结 RoPE 验证器，再从原 ELF/BIN 重解码四个围栏 CSR，并复用固定 SHA 的后补 `counter_audit` 函数，重建四次运行的全部 56 条计数器链。平放的 `runner-source.py` 只提取其原函数与字面周期上限，不执行无关构建/运行入口；每项身份与原 audit 的 inputs 绑定，所有输出与旧审计 JSON 完全比较。负控第二窗口没有 UART 样本，这一事实保留。未传该选项只复算原 campaign，成功回执中的 `extra_rope_counter_audit_reproduced` 明确为 false。

投影目标的完整恢复与复算示例：

```bash
python3 -B "$module/restore.py" --archive "$module/evidence/target-v1" \
  --output "$work/target-zip"
python3 -B "$module/archive.py" verify --archive "$work/target-zip/payload.zip" \
  --expected-sha256 92e0ad39890bc428c04c1412e8b5dc336957bcf8fb860b3a16a82d9c2723d1ee \
  --output "$work/target"
python3 -B "$module/recheck.py" --kind boundary \
  --build "$work/target/projection-target-build-02" \
  --campaign "$work/target/projection-target-campaign-01" \
  --output "$work/target-review"
```

`recheck.py` 校验完整运行集合、固定负控类型、distinct PID、进程回执与原始文件 SHA，再调用该 campaign 封存的原验证器。正常、恢复、重放的全部验证值必须相等；冻结源码/构建字节及导入闭包也重新核验。日志中的旧绝对路径只作为历史字符串，不访问旧机文件；`physical_runtime_identity_rechecked=false`。此工具不产生新样本，也不会清理历史 PID。失败证据和旧未知回执恢复后仍保持原状态。

## 新目标构建与运行的依赖

重新执行目标实验需要实际 RV64/lp64d 工具链、原 AM/klib/libm、受检固定 T17/参考/flash 身份和足够资源。已有构建路径不是可任意搬迁的便携 SDK：构建记录和运行 identity 含真实工具及外部输入路径；环境变化必须重新核实并建立新实验身份，不能仅改字符串绕过检查。

| 构建器 | 显式依赖参数 |
|---|---|
| `target/closure.py` | 实际工具链与 archive 探针；`--output` 新目录。 |
| `target/build_smoke.py` | `--parent-build` 旧合格目标构建，`--closure` 数学闭包，`--output`。 |
| `full/build.py`、`rope/build.py` | `--math-build` 合格数学构建，`--output`。 |
| `projection/build.py` | `--full-build`、`--kernel-build` 合格原 Q288 构建，`--output`。 |
| `projection/target/build.py` | `--projection-build`、`--projection-campaign` 已完成完整参考消费者，`--output`。 |

数学、RoPE 和投影目标运行器均显式接收 `--identity --build --output --operation-id`；后两者可用 `--cpu-count` 限制独立槽位。full/projection 的参考运行器另需 `--adapter` 实际编译并核验的团队 memory-only adapter。最终 ELF、fixtures、官方输入和 source closure 都在启动前固定，输出必须隔离，并保持各合同规定的负控、恢复与重放顺序。具体上限见各 CONTRACT 和原始 argv，不因换轮次重跑已有 PASS。

生成的 `forward.inc` 是带显式边界的函数片段，依赖类型、算子和标记接口；完整团队目标入口由 `full`/`projection` 提供。验证镜像含大量完整比较与转储，不作为性能镜像。新增性能包装须单独闭合源码/ELF/输入及实际正确性，避免把宿主 observer 或验证工作计入模型收益。
