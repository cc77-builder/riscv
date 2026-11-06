# P1-R1：窗口外准备调用隔离

这是 P2 决定进行的单次最小软件干预。稳定硬件仍为 0f12df67；
候选不替换默认入口，不改 RTL/NEMU，不上传 GitHub。

- CONTRACT.md：干预范围、布局约束、解释边界与停止条件。
- execution-contract.json：四个进程的冻结预算和原 P0 整数门槛。
- build.py / source/condition.c：GNU 构建同布局 control/candidate。
- verify.py：独立验证完整旧载入布局、代码、数据/栈、克隆和全部计时退休路径。
- identity.py：复核原实物身份，明确分离 P0 声明的两份历史 ledger。
- runtime.py：新 control normal，随后 candidate negative / normal / replay；失败不重试。
- test_*.py：静态错误、身份破坏、路径伪造与运行限额的拒绝检查。

本轮只运行 steady-d0 成对探针。通过后才能拟定下一轮扩围合同；不复用旧 RVV 分母、不修改原门槛。
结果、失败与实际进程数保留于本轮证据；运行前检查通过不能写成目标运行通过。
