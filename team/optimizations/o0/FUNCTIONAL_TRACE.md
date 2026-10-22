# O0：用户上传的功能轨迹已完成真实离线重放

基点：`a877e0575ea91392edc7816637e51ae8d1689b36`。本批唯一发布目标为 `cc77-builder/riscv:zjhwork2`，不修改生产 RTL、原 O0/T12 检查器、ISA、NEMU、黄金数据或旧封存材料。本页是工程验证记录，不是 T16 最终报告。

## 先辨认日志，再分析

用户上传的 `stderr.log.gz` 为 **109,257 字节**，Git blob `0b3030b5e51d1619b705db1ab73fc2f10805db8e`，与以下仓库文件完全一致：

`team/evidence/t14-optimization-20261016/fullcore/performance/functional-d0-s06-r0/stderr.log.gz`

注意外层目录也叫 performance，但运行目录是 **functional-d0-s06-r0**。之前选定的性能 pilot 是 **performance-d0-s06-r0**，其 stderr 为 176,256 字节、blob `757ff41dae73226efc6670e6b7c68ccc2a5d7b5d`。本次没有把功能日志重命名成性能日志，也没有改旧 pins 使错误输入通过。

## 本次实际执行

已运行未修改的 `analyze.py`，并通过新增的 `replay_functional_trace.py` 把来源、原始程序输出、48 条全核 CSR 采样、6 条 FU 生命周期与提交事件逐项关联。原始压缩文件和解压流的摘要均已核对。对应 stdout、result 和 analysis 从同一固定仓库版本取得，不拼接其他运行。

| 实际检查 | 结果 |
|---|---|
| 完整上传硬件流 | 解压 3,162,615 字节，20,415 行，原始 SHA256 与归档一致 |
| 程序记录 | 12 次功能调用：6 次 vdot + 6 次 RVV；不是 12 个性能测量样本 |
| CSR 采样 | 48 条逐项核对周期和完整 64 位整数值 |
| FU 生命周期 | 6 接受、6 响应、6 提交，0 FU 取消、0 在途残留 |
| 结果与身份 | 6 份完整 128 位 FU 结果匹配程序目的值；入队/提交 PC、ROB 和 pdest 关联通过 |
| FU 响应 | 六条均为接受后 2 个归一化全核周期 |
| 提交事件 | 六条均为接受后 4 个全核周期；仅为这些样本的观察差，不是普适指令延迟 |
| 等待观察 | VFEX4_WAIT=0、FU STALL=0；本运行没有触发待研究的连续请求阻塞 |
| 新工具回归 | 18 项真实离线重放/内存损坏反例/CLI 测试通过；不是新硬件测试或 RTL 故障注入 |

### 六条实际时间线

| 用例 | ROB | 目的 vd / pdest | 入队 | FU 接受 | FU 响应 | 提交 |
|---|---|---|---:|---:|---:|---:|
| D06 | 1:38 | v31 / 110 | 10895 | 10899 | 10901 | 10903 |
| L01_4 | 0:8 | v8 / 16 | 83048 | 83052 | 83054 | 83056 |
| R00002 | 0:35 | v10 / 60 | 146156 | 146160 | 146162 | 146164 |
| R00011 | 0:7 | v0 / 8 | 208783 | 208787 | 208789 | 208791 |
| R00020 | 0:22 | v10 / 90 | 271592 | 271596 | 271598 | 271600 |
| R00029 | 1:32 | v9 / 24 | 334671 | 334675 | 334677 | 334679 |

FU 原始门控计数的接受时点为 0、3、6、9、12、15；但实际全核接受间隔为 **72153、63108、62627、62809、63079** 周期。不能把原始计数的间隔 3 当成实际连续请求 II。该功能程序以孤立调用核对结果，尚不能量化 O1 同拍交接可能节约的周期。

本次确认的是已有硬件轨迹的一致性，不是重新运行 CPU；没有重新执行 ELF/黄金模型和全部寄存器状态验证。日志内的原始 PASS、checked_regs 与完整架构验收仍是原实验的记录。没有等待记录不等于其他工作负载无瓶颈。

## 可重复执行

在完整 zjhwork2 仓库根目录，Python 标准库即可运行：

```bash
python3 -B team/optimizations/o0/replay_functional_trace.py \
  --output team/out/o0-functional-trace.json
python3 -B -m unittest discover -s team/optimizations/o0 \
  -p 'test_functional_trace.py' -v
```

传入上传原文件时，额外指定 `--stderr /实际路径/stderr.log.gz`。脚本核对固定文件对象和原始摘要，拒绝未知文件和覆盖输出；默认原文件已存在于仓库。成功状态为 `O0_FUNCTIONAL_TRACE_REPLAY_PASS_NOT_THROUGHPUT`。

原性能 pilot 入口保持不变：

```bash
python3 -B team/optimizations/o0/replay_archive.py \
  --output team/out/o0-batch128-trace.json
```

它需要 `performance-d0-s06-r0/stderr.log.gz`，本次上传的 functional 文件不满足该来源约束。性能 pilot、本方案的密集请求诊断矩阵和 O1 父级验证仍待完成；**O0 未关闭，O1 RTL 尚未实现，没有新加速比**。

[实际重放结果](evidence/20261017-functional-trace/trace-replay.json)、[时间线 CSV](evidence/20261017-functional-trace/lifetime.csv)、[测试日志](evidence/20261017-functional-trace/host-tests.log)、[执行与源码回执](evidence/20261017-functional-trace/execution.json)。历史归档未覆盖，自动核验不代替团队人工 ACK。
