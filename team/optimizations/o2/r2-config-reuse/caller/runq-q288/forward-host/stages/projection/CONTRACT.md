# 完整 forward 的 K288 投影复用合同 v1

合同：`r2-s3-forward-projection-v1`。本目录是团队消费者适配，不改上游参考、官方 AM/NEMU/DiffTest、既有 TA/FR 汇编或旧实验输入。

## 范围与数学语义

固定原 D288/H768/L6、6 heads/6 KV heads、V32000/S256、GS32、seed `0x53485041`，连续 token 1/7/19。三份完全独立的 RunState：原样 scalar `forward`、强 RVV `q288_fused_rvv4`、TA `q288_tail_vdot`。候选仅将原完整 forward 的 `quantize` 调用换为检查原量化域的包装，将 `matmul` 调用换为严格路由包装；自动逆变换须逐字恢复原函数。不叠加 RoPE 缓存、不修改量化公式、不分割 K、不从参考回填候选结果。

37 张 K288 矩阵按输出行 M 分成 172 个原 Q288 调用：24 张 Q/K/V/O 各 1，12 张 W1/W3 各 3，classifier 112。6 张 K768 W2 保留原 scalar。矩阵身份、原 n/d 和 43 次调用顺序同时检查；不能按权重字节数判断 W1/W3 与 W2。每次候选 forward 原量化调用 25 次、315 组、10080 元素；37 routed、6 scalar、172 blocks、13 tails。

完整块调用原 `q288_pack`，原 Ws 直接引用。192/32 行尾块用完整 288×288 scratch 补齐零权重，用完整 288×9 scales 补齐 `1.0f`，仍调用同一 pack/内核；完整输出到有前后 guard 的 288-float scratch，仅复制有效行。有效行保持 g0..8 的 `((float)dot * Ws) * Xs`、再独立加法。额外 405504 MAC/forward 是被替换工作量的 2.9255%，不是免费计算。

## 运行与验收

新团队纯内存启动入口启用 FS/VS、FRM=RNE，检查 VLEN128；静态 errno TLS、原 AM 链接脚本、原预编译 klib/libm 和固定参考动态库不变。最终 ELF 的两个完整函数体必须逐字等于旧合格 target-build-03 ELF；旧 PASS 只证明被复用字节身份，不能替代新消费者运行。

候选真实激活在量化前检查 finite/nonzero-group/positive finite scale/可表示舍入值，再调用原 quantize。每个 routed 输出均与原 matmul 对同一实际 q/scale 的独立结果逐位比较；参考只写独立 scratch，不进入消费者。每个 block 核对向量 CSR、所有完整 128-bit slots、尾补齐输出及 guards。每 token 三方法保存 16 spans/3691424 B 完整状态，外部与独立宿主原版快照比较，同时核对整个模型、embedding、packed 与 tail-scales 原始转储。

正常、bad-tail、恢复、重放为四个新参考进程。bad-tail 在第一个候选 classifier 尾块最后有效输出翻转 1 bit，经过真实复制后必须在行 31999 被独立矩阵比较拒绝；禁止把预期应用拒绝称为 DiffTest 负控。每进程 API 调用上限 40 亿、内部 1800 秒、外部 1830 秒，单日志/转储 128 MiB；不使用 CPU/CSR 回写、跳过或 reference 结果回填。保留完整首次失败、进程与信号回收证据。

本合同只授予固定完整模型/三位置的 RISC-V 参考数值与消费者资格。这里的额外域检查、逐层重算和完整内存转储是验证开销；不是性能镜像。未获得新完整消费者的香山整核 DiffTest、完整应用周期或 ASIC PPA 资格。约 91.262% 是原 int8 MAC 覆盖率，不是加速比例。后续目标性能须包含全部 172 次调用、路由、尾复制、W2 和其他 forward 工作；初始化打包单独报告并计入初始化加 N token 总成本。
