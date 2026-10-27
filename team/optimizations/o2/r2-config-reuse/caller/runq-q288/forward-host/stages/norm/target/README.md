# 同对象首 token 完整目标验证入口

本入口链接已取得八例全状态参考资格的同一 `consumer-w2-norm.o`，运行固定模型的 p0/token1、FR-cache 与 TA-cache 单次完整调用。实际结果见 [RESULT.md](RESULT.md)，工作负载和资源分别由 [CONTRACT.md](CONTRACT.md)、[BUDGET.md](BUDGET.md)定义。

它将核心计算、参考资格和目标验证包装分开：消费者对象不重编译，初始化、完整状态比较、UART 与计时位于包装中。四个 GEMV 函数及 norm 叶完整字节不变；新包装加入双侧 guards、精确 flags 门禁及真正消费 a0 的成功／失败 trap。

## 1. 重建与运行

变量须指向对应真实且已合格的实物。所有新输出必须不存在并位于源码及冻结输入外；遵守四核总预算。新构建与运行不会自动继承本批 PASS。

```bash
NORM_SRC=team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/norm

taskset -c 2 python3 -B "$NORM_SRC/target/build.py" \
  --parent "$CONSUMER_BUILD" --campaign "$CONSUMER_REFERENCE" \
  --output "$FIRST_BUILD"
taskset -c 2 python3 -B "$NORM_SRC/target/reference.py" \
  --build "$FIRST_BUILD" --adapter "$REFERENCE_ADAPTER" \
  --identity "$TARGET_IDENTITY" --output "$FIRST_REFERENCE"

# 四例原参考全部通过后，先生成固定 profile，不启动 EMU。
taskset -c 0,1,2,3 python3 -B "$NORM_SRC/target/run.py" --freeze \
  --build "$FIRST_BUILD" --reference "$FIRST_REFERENCE" \
  --adapter "$REFERENCE_ADAPTER" --identity "$TARGET_IDENTITY" \
  --output "$FIRST_TARGET" --profile "$RESOURCE_PROFILE" \
  --cpus 0,1,2,3 --operation-id "$OPERATION_ID"

# 同一 profile 的唯一正式四例执行；不得对不明状态重发。
taskset -c 0,1,2,3 python3 -B "$NORM_SRC/target/run.py" \
  --build "$FIRST_BUILD" --reference "$FIRST_REFERENCE" \
  --adapter "$REFERENCE_ADAPTER" --identity "$TARGET_IDENTITY" \
  --output "$FIRST_TARGET" --profile "$RESOURCE_PROFILE"
```

每个 EMU 子进程上限为40M guest cycles、28,800秒墙钟、每条原始输出流4GiB；完整 raw 审计及输入复核在 EMU 等待上限外，耗时另记。四例分别拥有镜像、cwd、日志、PID和进程组。原参考先完成真实负控，因此目标四例可在指定四核内并行；campaign 只有等到目标负控和三个正控全部完整审计后才能通过。

`state.json` 的 `new_emu_runs` 在运行中按已完成案例更新，终态重数实际启动收据；运行中不能据零值判断没有启动。恢复必须结合 `active`、每例 `result.json`、真实进程与原工具操作收据；进程退出也不等于 raw 审计已成功。输入改变、超限、残留进程或失败均不自动重跑。

## 2. 原字节封存与离线复核

只有四例实际启动记录齐全、全部已回收且没有未知进程归属时才封存。完整失败可保存为 `FAILED_OR_PARTIAL`；单例失败、TA/replay 不一致或最终输入检查失败不会升级成 PASS。没有被失败收据认领的派生 validation 仅作为原文件保留。

```bash
python3 -B "$NORM_SRC/target/evidence.py" seal \
  --repo "$REPO" --build "$FIRST_BUILD" --norm-build "$NORM_BUILD" \
  --reference "$FIRST_REFERENCE" --target "$FIRST_TARGET" \
  --parent-evidence "$NORM_EVIDENCE_WORK" --output "$FIRST_EVIDENCE_WORK"

python3 -B "$NORM_SRC/target/transport.py" verify \
  --archive "$FIRST_EVIDENCE_WORK/archive/payload.zip" \
  --expected-sha256 "$FIRST_ZIP_SHA256" --output "$RESTORED"
python3 -B "$NORM_SRC/target/evidence.py" recheck \
  --root "$RESTORED" --manifest "$FIRST_EVIDENCE_WORK/archive/manifest.json" \
  --expected-manifest-sha256 "$FIRST_MANIFEST_SHA256" --output "$AUDIT_OUTPUT"
```

发布分片先使用上一级 `stages/restore.py` 重组原 ZIP，再执行上述流式 verify。大日志使用 `target/transport.py`，每次以1MiB块处理，保持已有 SHA256 对象 ZIP 格式、全部对象去重及恢复普通文件；避免旧归档器把数GB对象一次载入内存。

完整 recheck 先核对全体恢复文件及成员，再分别启动两个新的 Python 进程，执行各 campaign 自己封存的 reference / target 校验器。实际加载的自身、norm evidence、transport、archive helper 与包内摘要绑定。目标原 argv 先按历史路径核对，之后只在内存收据中把 image 路径映射到恢复目录；原记录不改。

父 norm 包不重复复制。新包记录其 ZIP、manifest、raw 复算结果及同对象 SHA，并把新构建实际消费的父构建记录、八例参考的 results/state/runtime-inputs 与父 manifest 逐项对应。父包须独立按 norm 的恢复说明复核；新包没有冒称再次运行父 raw。

离线复核不启动 NEMU/EMU，不重新认证当前物理硬件或外部依赖。原字节和失败证据保留；复算不会把 p0/token1 资格延伸到连续 token、其他模型或完整公平性能。

## 3. 可选参考 PC 诊断

已有最终四例参考资格后，可按 [PROFILE.md](PROFILE.md) 对相同 guest 镜像执行一次 FR-cache 和一次 TA-cache 的参考退休PC诊断。输出独立，CPU必须计入当前四核总预算；不增加目标EMU，不修改原参考实现。

```bash
taskset -c 3 python3 -B "$NORM_SRC/target/profile.py" run \
  --build "$FIRST_BUILD" --reference "$FIRST_REFERENCE" \
  --adapter "$REFERENCE_ADAPTER" --identity "$TARGET_IDENTITY" \
  --output "$PC_PROFILE"
```

封存该已完成诊断时，在上节 `evidence.py seal` 命令追加 `--extra "profile=$PC_PROFILE"`；失败的编译尝试可另用具名 extra 原样保留。归档保持 reference／target 两类主 campaign，诊断单列 `diagnostics.profile`。外层将诊断的原 build/reference 根、完整历史输入、间接 norm baseline 和实际源码闭包绑定到同一包，再从 `profile/closure/repo/.../norm/target/profile.py` 启动独立 Python 原文复算，输出位于恢复树之外。声明包含的诊断若复算失败，完整包复算不能跳过它报通过。

原始 `retired-pcs.tsv` 与 `pc-profile.json`、每例 `analysis.json` 提供逐PC和按实际ELF函数范围汇总的动态退休指令分布。全部15份 guest 二进制仍须逐字等于合格参考。这里的分布用于后续选题，不是香山周期或目标耗时占比；全部普通目标退休窗口仍未审计。

## 4. 输出含义

| 输出 | 证明内容 |
| --- | --- |
| `validation.json` | 完整原 DiffTest 终态、程序完整比较／精确负控、四 CSR 链、整个 custom 协议 |
| `audit/custom.json` | 实际64个允许 custom 站点的 ELF PC/word、退休 PC 分布与序列摘要；不预先编造动态提交数 |
| `audit/protocol.json` | 原 O2 两槽事务、算术响应、redirect/ROB/FTQ 清理及流结束无待决事项 |
| `audit/counter-audit.json` | 四次 CSR 的实际指令、入队、采样、退休与 UART 原值 |
| `audit/result.json` | 从完整归档 raw 重新得到的资格及失败保留结论 |

所有该实验结果的 `performance_qualified=false`。单个冷窗口即使完整通过，也没有多样本公平比较资格；`full_retirement_window_audited=false` 表示本工具没有记录和审计全部普通指令退休轨迹。它审计的是原 DiffTest、完整程序状态比较、custom 事件和四 CSR 链。
