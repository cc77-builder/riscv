# O1 FTQ 与计数窗口扩展（O2 schema 2）

由现有 `VDOT_O1_TRACE=1` 一并生成，默认关闭；T14/O1 仍须各自显式选择。保留全部 schema 1 EXU/ROB 记录和历史检查器，另用 `O2_` 前缀记录补充证据。只有 `check_extended.py` / `run_extended_core.py` 接受扩展覆盖；旧入口仍只宣称 schema 1 范围。

固定单 hart MinimalConfig：ROB48、FTQ8、PredictWidth16、RenameWidth6、CommitWidth8。ROB、CSR wrapper 和 NewCSR 各自从共同仿真复位开始计时，启动头绑定模式与配置。CSR 的 `FuConfig.ckAlwaysEn` 保证时钟持续运行；不推断或拟合时钟偏移。

- `O2_FTQ_ENQ/COMMIT/REDIRECT` 与每条 O1 ROB 事件按周期、槽位和 ROB 指针一一对应。记录 FTQ flag/index/offset，保留分配到提交的身份，并按真实重定向丢弃年轻事务。环绕覆盖只计已提交 VDot 所见 flag 变化，不把推测跳转当作已提交环绕。
- `O2_COUNTER_ENQ` 使用真实分配条件，排除 redirect 当拍；记录 PC、完整机器码、ROB 和原有 empty/wait/block 控制。`O2_CSR_ISSUE` 提供真正 CSR 请求的 ROB 身份；`O2_CSR_SAMPLE` 在 NewCSR 读取边沿记录地址、实际64位数据和写使能。两者必须同周期一一对应。
- `O2_COUNTER_COMMIT` 记录真实退休的计数器读取，必须匹配分配、采样、PC/机器码和完整数据；取消与指针复用分别处理。
- `O2_RETIRE` 记录 start=`0x51300013` 到 stop=`0x51400013` 的退休流。窗口状态按提交槽依次传递，支持开始后的同拍槽、结束后的同拍关闭和同组再次开始，不依赖上一拍 active 位。每条包含退休指令数、PC/机器码和写回数据。

新检查器严格拒绝缺字段、重复、越界、缺头、错误身份、漏采样、未关闭事务和窗口。随后将已核对的窗口转换为原 T13 纯算法输入，核对实际 ELF 路径、fence 顺序、CSR/全局周期差、instret/逐退休数/静态工作量，以及 UART 记录。计数期望来自真实 CSR 和 ELF，不从 UART 反推。

完整入口执行 hello、控制压力、13校准窗口、batch128的12窗口、八个功能/异常分片（117唯一用例、124执行）及真实 bit100 DiffTest 负控；正常参考库下 matrix-0 使用同一镜像完成恢复。保留失败尝试和真实退出码。完整矩阵检查完整向量寄存器、异常现场和CSR状态；负控绑定实际失败提交组、PC、指令、寄存器及高位差值。

本扩展不会单独证明性能 A/B、STA/PPA、虚拟化或人工签字。原 T12/T13 观察器与 O1 的互斥规则不变。运行命令：

```bash
python3 -OO -B -m unittest discover -s team/optimizations/o1 -p 'test_*.py' -v
python3 -OO -B team/optimizations/o1/run_extended_core.py \
  --core /absolute/source-bound-core --receipt /absolute/build-receipts \
  --pack /absolute/source-pack --reference-root /absolute/verified-nemu \
  --output /absolute/new-run-directory --jobs 2
```
