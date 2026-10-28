# 首token离线证据复算的有界并行

本工具的离线调度合同为 `r2-s3-first-token-frozen-offline-audit-v2`。它只改变已经结束的历史证据如何安排CPU复算，不改变原目标工作负载、输入、预算、判定条件或历史运行结论。

## 调度与判据

`evidence.py recheck --jobs 1..4` 默认串行。选择较大并发度时，只有target的四个独立case进入Linux fork进程池；reference和可选PC profile仍逐个独立进程执行。启动affinity必须包含至多四个允许CPU；case只能从启动时捕获的集合选择CPU，任务结束恢复工人此前的affinity。所有工人保留在外层已登记的同一进程组，不创建新的session。

原验证要求继续保留：

- 完整manifest和恢复树成员、所有字节的前后inventory。
- 每个历史启动、退出、进程组回收、配置、资源合同、原argv和实际输入身份。
- 仅在内存收据中映射image读取路径；不改归档原文。
- 原冻结 `module.a.validate()`、五项原始派生产物逐字相等、历史validation及成功aggregate相等。
- 四个唯一case、同名helper源码SHA一致；成功campaign必须TA/replay完全相等。
- 历史失败只绑定原raw、错误和退出码，保持不合格；新的离线验证异常不能当作历史失败已成功保存。

每例新监督收据写入审计输出的 `supervision/`，不进入原五项派生产物目录。父级报告记录实际工人PID、affinity和调度合同；pool复用PID不改变原四次EMU的独立进程要求。

## 监督与资源边界

外层从封存的target源码闭包加载原 `stages/full/run.py::spawn()`，经源码身份检查后复用。它先登记独立session的PID/PGID，再等待并回收。新入口显式将SIGTERM/SIGINT转成异常，让finally回收逻辑可执行；工人SIGTERM恢复默认终止行为，SIGINT由父级监督处理。

每个reference、target或profile worker的外部等待上限为7200秒。target并行池的等待预算为 `6900 − worker前置检查已耗时`；Pool构造和join不另承诺6900秒硬上限，仍由外层7200秒覆盖。任务异常或池等待超时会terminate并join整个池。`jobs=1`没有内部池计时器，继续受外层7200秒监督。

只有直接子进程回收、进程组消失、无残留、未超时且exit0，才接受worker成功。无法证明回收时保留 `cleanup_unknown`，不修改记录来通过门禁。整个原件树最终还需再次核对。原目标未全部终态时，不运行这次多核归档复算。

GB原始日志仍流式读取，但每个case还会分配完整BIN/ELF，不能把内存预算只算作Reader缓冲区。根据真实可用内存选择1–4工人；`--jobs 4`不意味着已有四核资源可供使用。离线复算不启动新NEMU/EMU，不授予公平性能、当前物理硬件或全部普通指令退休窗口资格。

## 实际机制验证

2026-10-27 16:31:55–16:31:58 UTC，在WSL中仅限CPU3，使用 `offline_mechanism_check.py` 对真实进程进行五项小型检查：

| 场景 | 实际检查 |
| --- | --- |
| 正常完成 | 四个fork工人；顺序结果和计算值正确；join后组消失 |
| case抛出异常 | 原异常标记保留；worker失败且所有已观察子进程消失 |
| 池等待超时 | 内部TimeoutError；terminate/join；没有误报外层超时 |
| 外层等待超时 | 真实owned timeout；整组回收，原PID generation不再存在 |
| SIGTERM取消 | 至少两个工人实际进入后向监督进程发SIGTERM；同一生产handler捕获并回收整组 |

五项均通过，所有回收检查确定，没有新增NEMU/EMU。检查输出明确 `synthetic_only=true`、`real_archive_rechecked=false`：这仅验证调度和监督机制，真实first-token归档仍需按原始raw完成整体验收。

机制验证代码可在完整项目源码树中使用。`REPO` 和 `FRESH_MECHANISM_OUTPUT` 必须是绝对路径，输出必须不存在；`NORM_SRC` 沿用 README 中相对于仓库的路径：

```bash
taskset -c 3 python3 -B "$REPO/$NORM_SRC/target/offline_mechanism_check.py" \
  --tool "$REPO/$NORM_SRC/target/evidence.py" --output "$FRESH_MECHANISM_OUTPUT"
```

本轮测试源SHA256为 `6f7379303c408a9c671dac0e4471b0335f10f90e740671e14a02fad3136ecf5c`，实际受测工具为 `a4dcff0588ae8947a3c46df56506e8b4d9e27906082e3d14e7e15869ba5bb4b9`。原监督helper为 `bee89ca4424110f244560b1ab0529c80fd4e9736dd274c49690026754dbf8475`。完整原始收据保存在本轮 `offline-parallel-mechanism-01/`；将其作为具名extra封存，不向既有冻结输入写入。

## 完整归档实证（2026-10-28）

本轮在2026-10-28 13:12:18（UTC+08:00）完成 [first-token/audit/result.json](../evidence/first-token/audit/result.json)，实际加载的工具仍为上述 `a4dcff0588ae8947a3c46df56506e8b4d9e27906082e3d14e7e15869ba5bb4b9`。全部1,646文件/15,071,206,214B已实际恢复，reference、四例target及可选profile的原文复算、五项派生字节、输入绑定、完整TA/replay及最终inventory均通过。target使用4个fork工人，CPU限制0–3；三个外层worker的owned进程组均已确定回收。实际完整审计输出为41文件/221,647字节，没有额外复制GB原始日志。

这次真实归档结果独立于上述五项合成机制检查；二者都保留。完整审计不新增NEMU/EMU，且没有扩大首token工作负载、公平性能或普通退休窗口资格。归档/复算及分片重组的具体命令、收据和运行定位见[发布索引](../evidence/index.json)。

当前seal入口要求四个case均已有真实启动记录及确定的终态、清理收据。`FAILED_OR_PARTIAL`允许这四例中的失败或部分成功，不承诺接受只启动了一部分case、未知进程归属或缺失收据的中断目录。此类原件仍需保留，不能补造记录来通过门禁。
