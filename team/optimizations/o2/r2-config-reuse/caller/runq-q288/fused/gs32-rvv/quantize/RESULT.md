# GS32 激活量化：有限参考资格

合同：`r2-s3-gs32-quantize-v1`。2026-11-06 10:56 UTC 的 `attempt-02` 已完成 **正常30例及三个有效负控**，状态为 `GS32_QUANTIZE_BOUNDED_REFERENCE_PASS`。这是独立量化函数的原 NEMU 参考资格；尚无完整消费者接入、香山目标周期或应用加速比结论。`performance_qualified=false`。

## 实现与边界

团队候选 `r2_quantize_gs32_rvv` 在 GS32、正且32整倍数长度、RNE、合法向量状态及各组有限非零最大值/normal scale 条件下工作。保留原 FP32 `max/127` 和逐元素除法；用 RMM 向量整数转换实现原 `round`，随后恢复**除法之后**的 FCSR，保持原除法标志并隐藏转换附加标志。任何不合条件的组恢复调用入口环境并整调用回退到原 `quantize`。接口、写入范围、不别名要求及 CSR/ABI 条件以 [CONTRACT.md](CONTRACT.md) 为准。

**合同文字勘误（不改冻结文件）：** CONTRACT第2节的“无栈/无其他数学调用”和ft0–ft2等临时寄存器列表仅适用于快路径。回退尾调用原 `quantize`，它使用112B栈、调用 `fabs/round`，并可使用fa等其他caller-saved寄存器；完整调用只承诺原ABI要求的callee-saved、返回栈和相关环境，不承诺保留caller-saved。原冻结合同字节继续作为历史输入保存，本次30例资格不作为该过宽文字的证明。逐组flags等价来自源码/机器码推理；dump实际采集的是调用前后状态。

本次未修改九份冻结输入；未修改、替换或重建官方 NEMU、AM、原 scalar 或数学库。原 `quantize` 的100条/400B、`__round` 的15条/52B、`__fabs` 的2条/6B实际指令与既有原件逐项核对，只允许明确列出的重定位 immediate 变化，并核对实际调用目标、127.0分母和2^53常量。官方输入在运行前后未变化。具体 SHA、命令和结果见 [REFERENCE.json](REFERENCE.json)。

## 实际验证

共用同一 ELF/BIN，通过控制字选择正常函数或三个错误变体；各自运行于独立参考进程，全部固定 CPU1 串行，GNU `-j1`。每进程上限20,000,000 API调用及120秒；本次每个约5.08–5.13M API，未触及上限。

| 模式 | 实际结果 | 失败用例 | 指定见证 |
| --- | --- | --- | --- |
| 正常 | GOOD，30/30通过 | 无 | 完整输入、q/scale及未用尾部、guards、context、FCSR、向量状态和callee-saved检查全通过 |
| bad-rne | BAD94，预期拒绝 | 0、26 | case0半点的±1错误变成0 |
| bad-keep-flags | BAD94，预期拒绝 | 0、1、2、3、11、26、29 | case0 FCSR由原0变为0x81；省掉恢复同时残留RMM和NX，并非只注入NX |
| bad-entry-flags | BAD94，预期拒绝 | 1、2、11、29 | case1原除法NX=1错误变为0 |

每个模式保存完整30×17,568B case记录、128B report和16B control，以及初末寄存器/CSR；guest比较与host对原始数据的比较一致。正常case11的FCSR双方均为3，保存UF与NX；case29覆盖最大有限值、极小元素和不同合法VL/VTYPE。三负控验证本批用例能检出指定实现错误，不构成全部输入域的证明。

四进程PID为17201–17204，退出码0/2/2/2；全部子进程已回收、进程组消失、未超时。外层作业 `f8121a0446d523f59d5ad321ed8d4e6b.d9c55d7ad4d9e849e80200e4ca7c47ae` 于10:56:39.647–10:56:44.189Z执行，exit0、4502ms、`cleanup_complete=true`。内部控制器10:56:42.419–10:56:43.920Z完成四模式。外层stderr有WSL代理提示及here-document结束符警告；完整回执原样保存，不把外层警告隐去，也未为消除它重跑。各参考进程自身stderr为空，终态和完整数据已实际取得。

应用优化专家于11:08 UTC直接读取归档，在未运行本叶 `verify.py` 的情况下独立重建30例配置/输入位型、按C布局解码完整dump、核实际ELF的context指针及各负控；未发现阻塞本次有限参考结论的问题。独立汇报为团队消息 `a8bc5ba416a84698a15b322f022ce86b`，同时指出上述合同措辞边界。

## 指令观测与工程判断

以下只列正常模式的实际 `instret` 窗口，包含相同的store/call/采样开销，未估算扣除。输入由测试构造；匹配消费者长度不代表实际模型activation分布。

| 用例/输入 | n | 原scalar | 候选 | 相对变化 |
| --- | ---: | ---: | ---: | ---: |
| case2，有限伪随机、9组快路 | 288 | 11,827 | 293 | 减少97.523% |
| case3，有限伪随机、入口flags=0x1f | 768 | 31,469 | 728 | 减少97.687% |
| case29，极值/极小元素、合法不同VL/VTYPE | 768 | 31,456 | 728 | 减少97.686% |
| case13，末组全零后整调用回退 | 288 | 11,596 | 11,866 | 增加2.328% |
| case14，末元素quiet NaN后回退 | 288 | 11,822 | 12,093 | 增加2.292% |
| case15，末组subnormal scale后回退 | 288 | 11,829 | 12,105 | 增加2.333% |

这些结果支持先做一次有界的完整消费者参考接入，验证实际activation、全state和FCSR。它们不能换算成香山cycle：向量指令可能拆成多个操作，除法延迟、CSR开销及存储系统影响尚未测量。

既有6层消费者有5个量化静态调用位置：循环内3个n288、1个n768，循环后1个n288，动态合计19×288＋6×768，共315组。若全部命中上述快路，同一probe口径的候选计数投影为9,935条；这只是条件计算，不是完整消费者观测或收益保证。后组回退需要重做原调用，实际命中率是下一步的重要未知量。

建议复用既有消费者派生与完整state比较器，在独立新镜像中仅追加一个可逆的量化候选clone，保留相同GEMV路由及五个模型缓冲，不改变当前FR/G/P冻结实验。比较对象应保留实际较快的合格RVV；先取得完整参考资格，再依据收益和排期决定目标测量。本次未实施该接入或启动新EMU。

## 证据与复现

源码身份绑定九个文件SHA，而非把Windows主仓HEAD `926ffd7cdf736e12586009cb4b2d22f76ff31f16` 的历史PASS转移给候选。ELF SHA为 `a428f20d3c6d67ab074320f33932289a35243d485e909148f5e9bbdccdc722ec`，BIN SHA为 `2fc2d935eb4324dfcbd658f93647f1ac06a4c64be7dc03436ecd4f4faea56d72`。

原始结果在常驻WSL开发区的 `runs/quantize-gs32-20261106-pro3/attempt-02`，同根保留 `controller-02`、`launch-02.json`和控制器日志。Windows导出位于：

```text
D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\runs\quantize-gs32-20261106-pro3\attempt-02-export
```

`quantize-attempt-02.zip` 为573,692B、140个成员，SHA256为 `12baad29d9c3f723081eebae2ad3ca5929c594b18d0c1af427bb1e79c9a1dd37`；已逐成员读回校验。含源、ELF/BIN、全部dump、输入与工具身份、过程回执和完整外层工具回执。同目录 `manifest.json` SHA为 `5aded03bf7746a00de683223c53eaff1aa8bcfe49dbaa131442f769fecef5163`；`readback-summary.json` SHA为 `552f457d18b99c2c2d9d878a077a167eb7a8f59e136ec163aedc2c439dc44b33`。

复现入口是未改的 `verify.py`，必须在已协调的CPU1执行，传入原parent对象目录、AM目录、adapter及reference路径，并使用不存在的新输出目录；完整实际argv和全部输入SHA保存在archive的 `launch-02.json`、`attempt-02/inputs.json`及各receipt，不能覆盖已有attempt。

`attempt-01` 的启动失败证据保持原样：它在AM UART初始化失败，未进入量化用例；不记为算法失败。原准备后取消的操作 `.51ba776cad83c0708becc23861c9d7a0` 已查证仍为cancelled，没有重放。本次使用已冻结的团队无设备入口和链接脚本，新操作只运行一次。此前 `pause-01` 归档及其失败证据继续保留。

### 共享仓库中的原始证据

以下文件由上述原始导出逐字节复制，保留首次失败与本次成功两条证据线；解压后的输入、原始dump、进程回执和逐成员SHA见各自manifest。证据目录的Git属性禁用换行转换，源码及冻结合同未重写。

| 文件 | 字节数 | SHA256 |
| --- | ---: | --- |
| [quantize-pause-01.zip](evidence-v1/quantize-pause-01.zip) | 757,690 | `c0ed8f4a9a18fef09e89717e1a1b02da4fc728c717f754414e0e2a9b648fa524` |
| [pause-01-manifest.json](evidence-v1/pause-01-manifest.json) | 16,131 | `1df5cfc2b03c7a261c92ac4951778ba74f6ae37d12ad303cbda6fc516c35191f` |
| [quantize-attempt-02.zip](evidence-v1/quantize-attempt-02.zip) | 573,692 | `12baad29d9c3f723081eebae2ad3ca5929c594b18d0c1af427bb1e79c9a1dd37` |
| [attempt-02-manifest.json](evidence-v1/attempt-02-manifest.json) | 22,090 | `5aded03bf7746a00de683223c53eaff1aa8bcfe49dbaa131442f769fecef5163` |
| [attempt-02-summary.json](evidence-v1/attempt-02-summary.json) | 60,582 | `552f457d18b99c2c2d9d878a077a167eb7a8f59e136ec163aedc2c439dc44b33` |
