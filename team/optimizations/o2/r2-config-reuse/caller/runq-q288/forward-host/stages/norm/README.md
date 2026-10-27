# RMSNorm 输出 RVV、可选 W2 消费者与首 token 验证

这里保留一个有限范围的 RMSNorm 软件候选，以及使用相同候选的纯 W2 消费者。当前采用决定、实际目标周期和证据身份见 [RESULT.md](RESULT.md)。`firstdot` 稳定入口、原 scalar norm、原 W2 消费者及较强 FR 对照继续保留。

## 1. 改了什么

候选从固定原样 `upstream/runq.c` 机械派生，只替换 RMSNorm 最后的输出循环：先计算 `ss * x[j]`，再计算 `weight[j] * (...)`。平方、逐项标量左折叠、除以 size、epsilon、sqrtf 和倒数保持原顺序；没有融合乘加、重关联或 fast-math。新 `norm.S` 用 e32/m8 处理输出，进入/退出保存并恢复 VL/VTYPE。

独立 norm 的输入包括 token 1/7/19、p0..2 捕获的 39 次真实调用及 9 个固定合成用例。48 个输入分别覆盖 scalar/RVV、独立输出/原地输出、清零/预置 sticky flags，共 384 组完整输出。负控实际翻转 case38 最后一个输出字节，并要求在 byte1151 被拒绝。

包括 [CONTRACT.md](CONTRACT.md) 在内的11个原冻结文件保持原字节。原 4M guest-cycle/3600 秒试验的超时记录仍为 FAILED。[BUDGET-CONTRACT.md](BUDGET-CONTRACT.md) 是同镜像、同输入、同判据的一次独立资源补充，规定 6M guest cycles/7200 秒，最多两个并发 EMU，负控先行。重放不增加正式样本数；资源上限改变不放宽正确性或性能门槛。

### 调用域

```c
#include "norm.h"
/* o == x，或者 o/x 两个完整 span 不相交；weight 与两者均不相交。 */
r2_rmsnorm_rvv(o, x, weight, 288);
```

要求 RV64/lp64d、RVV 1.0、VLEN128、RNE、FS/VS enabled、vstart=0，以及三个有效、4 字节对齐的 binary32 数组。输入和权重有限，可以包含正负零和次正规数；运算溢出/下溢仍按原语义发生。保留 errno、frm、sticky fflags、vcsr，并恢复原 VL/VTYPE；向量寄存器按普通 C ABI 视为 caller-clobbered。没有授予任意 size、非有限输入、部分重叠、其他舍入模式或并发模型重绑定资格。

## 2. 可选消费者与回退

[consumer/CONTRACT.md](consumer/CONTRACT.md) 定义独立身份 `r2-s3-forward-consumer-w2-norm-v1`。它只在原 W2 的四个优化 forward 中替换 12 处静态 norm 调用；FR、TA、FR-cache、TA-cache 采用同一 norm 策略，`R2_SCALAR` 仍走原上游 forward。替换可以逐字逆回固定父源码。

新 `consumer-w2-norm.o` 由新编译的纯消费者 core 与原 norm `candidate.o`、`norm.o` 通过 `ld -r --no-relax` 合成。数值验证 ELF 和普通双状态 API ELF 均链接同一个完整对象。四个 K288/K768 GEMV 核的完整机器码保持不变；norm 输出叶函数保持完整字节，norm C 函数只允许合法链接重定位，并检查两个调用目标、两个浮点常量及全部其余指令位。

恢复归档后，候选对象位于 `consumer-build/consumer-w2-norm.o`，公共头文件位于 `consumer-build/source/consumer.h` 和 `consumer_w2.h`。已有 W2 集成只需替换完整 consumer 对象，继续使用原公共 API、state 布局、五份模型输入、四个 GEMV 核及原 ABI/链接约束；具体链接命令保存在构建的 `target-build.command.json` 和 stdout 中。

| 选择 | 链接对象与行为 |
| --- | --- |
| 原 W2 消费者 | 原 `consumer-w2.o`；优化 forward 中的 norm 仍为原 scalar 实现 |
| 本可选组合 | `consumer-w2-norm.o`；四条优化 forward 共用输出 RVV norm，R2_SCALAR 保持原实现 |
| 回退 | 将新完整对象换回原 `consumer-w2.o`，保留原公开 API、模型与 state |

两个完整 consumer 对象都定义同一组 `r2_w2_*` 和上游全局符号，必须二选一链接。不要把其中一个对象叠加到另一个对象上，也不要用全局宏或 linker wrap 假设能够拦截同编译单元内的所有 norm 调用。

本组合完成八个独立原 NEMU 进程，验证 p0..2 的完整 state、五份完整模型、flags、真实末 logit 翻位负控、恢复和重放；随后用同一新对象完成双状态 guarded API。旧 W2 的 p0..255 结果属于旧对象。链接同一新对象的首 token 完整目标入口、资源合同与实际状态见 [target/README.md](target/README.md) 和 [target/RESULT.md](target/RESULT.md)。全序列、完整公平应用性能及 ASIC 资格分别验收，不能由参考退休指令数或 norm 局部周期推导 token/s。

## 3. 构建与运行入口

先按仓库 [环境说明](../../../../../../../../docs/environment.md) 准备已合格的父构建、原 AM、原 NEMU/reference adapter 和固定目标身份。下面各变量必须指向对应真实记录；输出目录必须不存在并位于源码和全部冻结输入之外。脚本会核对源、工具、模型、对象和父资格，不能用改写旧 JSON 的方式迁移资格。

```bash
NORM_SRC=team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/norm

# 独立 norm：新构建与新参考资格。
taskset -c 2 python3 -B "$NORM_SRC/build.py" \
  --full-build "$QUALIFIED_FULL_BUILD" --output "$NORM_BUILD"
taskset -c 2 python3 -B "$NORM_SRC/reference.py" \
  --build "$NORM_BUILD" --adapter "$REFERENCE_ADAPTER" \
  --identity "$TARGET_IDENTITY" --output "$NORM_REFERENCE"

# 已定义的一次资源补充。仅在对应 CPU 空闲且总预算允许时执行。
taskset -c 0,1 python3 -B "$NORM_SRC/budget.py" \
  --build "$NORM_BUILD" --reference "$NORM_REFERENCE" \
  --identity "$TARGET_IDENTITY" --output "$NORM_TARGET" \
  --cpu-count 2 --operation-id "$OPERATION_ID"
```

`run.py` 仍是原 4M/3600 合同的冻结入口，保存它是为了复算原证据。不要为了得到 PASS 覆盖旧输出、追加成功样本、删首样本、改变预热或继续扩预算。新工作负载、镜像、顺序、日志策略或验收规则应有独立身份。

```bash
# 新组合：固定父 W2 + 已通过独立参考的 norm 对象。
taskset -c 2 python3 -B "$NORM_SRC/consumer/build.py" \
  --parent "$W2_BUILD" --campaign "$W2_REFERENCE" \
  --norm-build "$NORM_BUILD" --norm-reference "$NORM_REFERENCE" \
  --output "$CONSUMER_BUILD"
taskset -c 2,3 python3 -B "$NORM_SRC/consumer/run.py" \
  --build "$CONSUMER_BUILD" --adapter "$REFERENCE_ADAPTER" \
  --identity "$TARGET_IDENTITY" --output "$CONSUMER_REFERENCE" --cpus 2,3

# guarded API：必须链接已经通过上述八例的同一个对象。
taskset -c 2 python3 -B "$NORM_SRC/consumer/build.py" --api \
  --parent "$CONSUMER_BUILD" --campaign "$CONSUMER_REFERENCE" --output "$API_BUILD"
taskset -c 2 python3 -B "$NORM_SRC/consumer/api.py" \
  --build "$API_BUILD" --adapter "$REFERENCE_ADAPTER" \
  --identity "$TARGET_IDENTITY" --output "$API_REFERENCE"
```

参考进程上限保留 2B API calls、600 秒内部/630 秒外部、128MiB 单文件；norm 原参考为 100M API calls、300 秒内部/330 秒外部。参考调度器和原数值比较器直接复用，只对新文件名、独立合同和 API 的一个旧身份常量做显式绑定；原模块、原 JSON 与数值/进程门槛不变。全部构建/验证共同遵守四核总预算。

## 4. 原字节恢复与离线复算

[evidence/index.json](evidence/index.json) 给出分片包、ZIP、manifest 和复算报告的真实摘要。使用既有 [restore.py](../restore.py) 重组 ZIP，再用 [archive.py](../archive.py) 完整解包核验：

```bash
STAGES=team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages
python3 -B "$STAGES/restore.py" \
  --archive "$PUBLISHED_PARTS" --output "$REASSEMBLED"
python3 -B "$STAGES/archive.py" verify \
  --archive "$REASSEMBLED/payload.zip" --expected-sha256 "$ZIP_SHA256" \
  --output "$RESTORED"
python3 -B "$STAGES/norm/evidence.py" recheck \
  --root "$RESTORED" --manifest "$REASSEMBLED/manifest.json" \
  --expected-manifest-sha256 "$MANIFEST_SHA256" --output "$AUDIT_OUTPUT"
```

保留 `evidence.py` 的完整仓库相对层级；也可使用包内 `metadata/tool-source/.../stages/norm/evidence.py`。每类 campaign 在新的 `python -B` 进程中导入自己的冻结源码闭包。复算将实际文件、构建记录和原 runtime pins 三方对应，核对独立 PID/清理收据，重新读取完整 dump 和原始日志，并重算四份计数/协议派生文件及原性能决定。旧 target 的两个被终止进程必须继续被原 process gate 拒绝。

离线复算不启动 NEMU/EMU，不访问未归档的原物理工具/硬件路径，也不重新认证当前机器的 RTL。结果明确写 `new_reference_runs=0`、`new_emu_runs=0`、`physical_runtime_identity_rechecked=false`。重新构建或在新机器执行是另一项工作，需要对应的新环境和实际运行证据。

## 5. 文件分工

| 文件 | 职责 |
| --- | --- |
| `generate.py`、`norm.S`、`norm.h` | 固定来源的机械派生、RVV 输出叶和调用域 |
| `export.c`、`scalar.c`、`main.c` | 真实输入捕获、原 scalar 对照、功能/负控/八窗口程序 |
| `build.py`、`reference.py`、`run.py` | 原静态、完整参考、目标运行和冻结验收 |
| `budget.py`、`BUDGET-CONTRACT.md` | 同原实验的一次独立资源补充 |
| `consumer/` | 新可替换对象、八例参考与同对象 guarded API |
| `target/` | 同完整对象的首 token 目标包装、参考资格、冻结四例运行与流式审计 |
| `evidence.py`、`evidence/` | 原字节归档、完整恢复和冻结验证器复算 |

各次构建、失败、命令、原始输出和恢复证据均由结果索引定位。没有修改官方程序、上游权威原文、RTL、旧 HOLD 或稳定默认入口。
