# PARTIAL_KILL 定向语料 v2

独立于冻结的 `workloads/generate_control.py`。旧测试只保留来源和必要的兼容复核；不重跑历史完整硬件回归，不以旧机器 PASS 代替当前覆盖。

假设来自本机 seed1/2 诊断：较老 v16 在取消前 5～17 拍已结束，而上游 group14 曾出现 v16 存活、v24 被取消。保留 group14 的 15 次浮点写回竞争、两条 decode gap、向量输入和分支结果顺序；仅将除数有效宽度固定为 32、36、40、44、48、52、56、60 位。`SRT16Divider.scala` 的迭代计数由操作数前导零差决定，因而这组输入用于提前分支解析时刻。八个函数占相同 2048 字节槽。它不是周期性能比较，也不能假设每个宽度必然对应固定发射/取消周期。

一次构建、一个 seed=1 EMU 进程、128 次试验；最多 1800 秒／5000000 周期，不自动搜索种子。检查全部 65536 字节向量结果、每组五个 CSR、准确 VDOT 退休数量、真实 DiffTest 和完整严格 O2 轨迹。目标通过额外要求：同一取消周期两槽有效，仅年轻事务取消，存活事务最终正确退休，取消事务没有退休。没有目标事件时记功能通过／覆盖缺失，不关闭 G3。

Linux LF 检出中使用已验证硬件和输入（参数为本机绝对路径）：

```sh
python3 -B team/optimizations/o2/fullcore/partial_kill/run.py \
  --hardware-root "$HARDWARE_REPO" --hardware-pins "$HARDWARE_PINS" \
  --input-contract "$INPUT_CONTRACT" --am-home "$AM_HOME" \
  --tool-bin "$TOOL_BIN" --output "$NEW_OUTPUT"
python3 -B team/optimizations/o2/fullcore/partial_kill/run.py \
  --action check --output "$NEW_OUTPUT"
```

运行源码必须已提交；实际构建源码、生成语料、ELF/BIN、原始双流、命令、完整环境、退出码及来源记录保留在输出。新运行前后核验原硬件依赖与参考模型，不改原构建树。O1/O2 的生产默认开关保持关闭；测试使用已有明确启用 O2 观测的实验 EMU。

主机测试：`python3 -B -m unittest discover -s team/optimizations/o2/fullcore/partial_kill -p 'test_*.py'`。模拟 UART 的单元测试只核查拒错逻辑，不提供硬件覆盖。
