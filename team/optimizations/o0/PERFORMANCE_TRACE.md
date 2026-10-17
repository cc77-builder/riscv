# O0：T14 batch128 性能原始轨迹诊断完成

本批开发基点 `91b94073a06c7e81c1abb1f8e2e4a926e183f780`，唯一发布目标 `cc77-builder/riscv:zjhwork2`。这是旧硬件原始日志的离线重放，不是重新运行香山或已经实施 O1。旧 O0/T12 检查器、生产 RTL、ISA、NEMU、黄金数据和封存证据均未修改。

## 文件身份与真实执行

此次上传 `stderr (2).log.gz` 为 176,256 字节，Git blob `757ff41dae73226efc6670e6b7c68ccc2a5d7b5d`，与 `team/evidence/t14-optimization-20261016/fullcore/performance/performance-d0-s06-r0/stderr.log.gz` 完全一致。解压 4,086,304 字节、29,530 行，SHA256 为 `b539264f42164a220b5835983ebf54f6454365bf58037d590d19fbfb018c17ef`。

原 `replay_archive.py` 严格 trace 模式实际退出 0，状态 `O0_PILOT_TRACE_REPLAY_PASS_NOT_FULL_O0`；不是 program 模式降级通过。stdout、result、analysis、pins 和两个旧解析器均通过固定 Git 对象校验。新增 `summarize_performance_trace.py` 继续关联 48 条原始 CSR 采样、动态 ROB 分配、响应与提交、窗口和下一条请求身份。

## 诊断结果

- 768 次 FU 接受、768 次响应、768 次提交；全部响应延迟 2 个归一化全核周期，0 次 FU 取消、0 次写回反压、无遗留事务。
- 780 次 vdot 入队中有 12 次在接受前被重定向取消；不能把入队数当成执行/提交数。
- 1,470 个 vdot `busy=1` 等待事件，另有 4 个 `busy=0` 等待事件。
- **738 个旧响应周期同时出现 `busy=1` 的新 vdot 等待；738 次均核对到同一等待 ROB 身份在下一周期被接受。** 这些匹配周期没有观察到同拍重定向。
- 6 个 vdot 窗口内部共 762 个接受间隔：3 拍 744 次、4 拍 8 次、10 拍 3 次、11 拍 1 次、13 拍 1 次、14 拍 5 次。5 个跨窗口间隔单独排除。

| vdot 窗口 | 周期 | 接受/提交 | busy 等待事件 | 响应同拍等待且下一拍接受同一请求 | 窗口内接受间隔 |
|---|---:|---:|---:|---:|---|
| first / seq0 | 480 | 128/128 | 237 | 119 | 3×120、4×4、10×2、13×1 |
| warmup / seq3 | 483 | 128/128 | 237 | 119 | 3×120、4×4、10×1、11×1、14×1 |
| measured / seq4 | 465 | 128/128 | 249 | 125 | 3×126、14×1 |
| measured / seq7 | 464 | 128/128 | 249 | 125 | 3×126、14×1 |
| measured / seq8 | 464 | 128/128 | 249 | 125 | 3×126、14×1 |
| measured / seq11 | 464 | 128/128 | 249 | 125 | 3×126、14×1 |

另外 6 个 RVV 窗口没有 vdot 接受事件；其原始周期为 712、696、678、678、678、678。完整 12 窗口见本批 `windows.csv`。正式轮次与首次、预热分别保留，不将同一确定性运行算成多个独立实验。

### 一组原始全核时间线

| 周期 | 旧请求 ROB 1:19，pdest99 | 新请求 ROB 1:20，pdest14 |
|---|---|---|
| 39743 | FU 接受 | 已入队 |
| 39744 | 运算在途 | VFEX4_WAIT，busy=1 |
| 39745 | FU 响应握手 | VFEX4_WAIT，busy=1，尚未接受 |
| 39746 | 已完成 FU 响应 | FU 接受 |
| 39747 | ROB 提交 | 运算在途 |
| 39748 | — | FU 响应握手 |

生产 `ExeUnit.scala` 的观察条件是 `io.in.valid && !io.in.ready`，且现有输入 valid/ready 都被 `!busy` 门控。因此这里不是凭空猜测“可能没有下一条请求”：旧结果返回时，新请求确实已经到达父级输入，但在当前协议下没有被接受。

## 对 O1 的决定与未证明事项

**这个 batch128 pilot 已为优先评估 vdot→vdot 同拍交接提供实际依据。** 下一步最小改动应同时检查 VDot ready/状态、ExeUnit busy 放行和完成+接受优先级、旧结果与旧 ROB/pdest/写使能的绑定，以及单元/父级测试器的新协议。

738 是已观察的匹配事件数，**不是可直接节省 738 周期**。每个正式窗口的 125 次匹配也不能直接从 464/465 周期中扣除。改变接口可能改变发射、唤醒、投机和循环重叠；是否能达到 II=2、实现多少全核收益，仍需新硬件与相同测试 A/B。

本日志未出现 FU 写回反压，因此没有依据首先提高写回仲裁优先级。14 拍间隔及其他空拍仍需独立解释，不能仅据此命名为缓存/带宽/唤醒瓶颈。此处为旧 T14 测试，不与新四项目统一基准 453.25 周期直接相减。

**已完成：此性能 pilot 的完整原始流重放和身份/窗口诊断。尚未完成：O0 四场景及 1/2/4 路不同输入矩阵、O1 生产 RTL/真实父级联调、新全核 DiffTest、性能 A/B、STA/PPA 和人工复核。** 不再把该文件传输列为阻塞，也不声称全部 O0 已关闭。

## 复现与测试

在完整 zjhwork2 仓库根执行，Python 3.10+ 标准库即可；输出目录须不存在：

```bash
python3 -B team/optimizations/o0/replay_archive.py --output team/out/o0-batch128-replay.json
python3 -B team/optimizations/o0/summarize_performance_trace.py --output team/out/o0-batch128-detail
python3 -B -m unittest discover -s team/optimizations/o0 -p 'test_performance_trace.py' -v
```

新增 16 项测试实际通过，含完整真实 pilot、CSR/PC/目的身份损坏反例、窗口计数、跨窗口间隔排除及 CLI 拒绝覆盖；旧 functional 18 项测试也实际重跑通过。这些是离线检查器测试，不是新 RTL 故障注入。完整逐笔结果通过上述命令重新生成；本批仓库保存精简摘要、12 窗口 CSV、执行及源码摘要，原始大日志继续引用旧封存路径。

[本批证据](evidence/20261017-performance-trace/summary.json) · [执行回执](evidence/20261017-performance-trace/execution.json) · [O1 原接口合同](../o1/CONTRACT.md)。
