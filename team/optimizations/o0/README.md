# O0：先量化接受间隔和等待，再修改接口

当前进度见 [2026-10-18记录](../../docs/o0-progress-20261018.md)。旧 T14 pilot 和统一微基准四场景原始轨迹已重放；固定256点积矩阵完成18镜像编译、II4基线54次新运行/648窗口验收。T14 同矩阵对照仍未完成，O0 未关闭。[O1 源码候选](../o1/README.md)已并入 James_Hotten，默认关闭，尚未通过完整父级/全核验收。

## 工具与证据边界

检查器安全修复后，用 `python -OO -B team/optimizations/o0/recheck_matrix.py --output /new/directory` 对封存54次运行应用当前门禁。该入口先认证原始归档，记录新旧检查器身份，并要求每次结果与封存结果一致。原 `summarize_matrix.py` 和证据目录的 `verify.py` 保持严格来源检查；复现旧工具时使用 b12a97b86，不改写旧摘要以迁就新源码。

- `analyze.py`：单核旧单请求协议的原始轨迹诊断。基础模式响应延迟3拍，T14融合输入模式2拍；不接受O1同拍交接。固定 T12 解析器 blob 为 `4093e685388f915dd78a15729889631999dba74d`。
- `replay_archive.py`：固定旧 T14 batch128 pilot，见 [原入口](ARCHIVE_REPLAY.md)。
- `replay_scenarios.py`：固定统一微基准归档清单与镜像包，重新验证 ours 的16镜像/215正确性窗口，再诊断12性能轨迹/144窗口。所有模式先验证原始证据，不从派生汇总猜测硬件事件。
- `generate_matrix.py`：256点积、1/2/4路独立目的、相同/不同输入、vdot/RVV、3组输入。18个分片镜像、216个计划窗口。
- `compile_matrix.py`：独立导出固定AM源码，交叉编译18个镜像，直接检查ELF常量、完整状态数据和256次点积的机器码路径；不会启动DUT。
- `matrix_check.py` / `run_matrix.py`：绑定本次固定构建回执与既有 d3706f0b8 II4 EMU，先验证一个真实pilot，再执行全18镜像各3次确定性重放；保留原始流，检查完整退休路径、CSR边界、UART负控和FU生命周期。
- `summarize_matrix.py`：独立复核全部54次运行，性能汇总只取各镜像的replay 0，不将确定性重放当作独立样本；[封存归档复算](../../evidence/o0-baseline-20261018/README.md)无需EMU或编译器。

FU 的 GTimer 是门控时钟计数，诊断按每笔事务绑定父级 VFEX4 全核接受周期。接受间隔按实际工作负载统计，不能直接等同硬件II；busy与响应同拍是观察，不能证明同拍交接合法。计数包含投机事务，不能直接替代退休点积数。日志没有完整每周期上游需求、仲裁授权或所有idle状态，不能对全部空拍作因果归因。

矩阵固定算术工作量，但1/2/4路的循环次数和动态指令数不同；单路的same/different输入天然一致，保留为控制项。主机生成、编译、归档复算和新DUT执行分别记录，不混用状态名。

## 运行

主机测试仅依赖Python标准库（含真实归档与编译ELF的负控）：

```sh
python3 -OO -B -m unittest discover -s team/optimizations/o0 -p 'test_*.py' -v
```

从仓库根重放四场景，输出目录必须不存在：

```sh
python3 -OO -B team/optimizations/o0/replay_scenarios.py --output /tmp/o0-four-scenes-new
```

独立诊断已有完整原始流；模式参数必须对应真实EMU，不得为消除失败修改：

```sh
python3 -B team/optimizations/o0/analyze.py \
  --stderr /run/stderr.log.gz --stdout /run/stdout.log.gz \
  --exit-code 0 --fu-latency 2 --output /tmp/o0-diagnosis-new
```

生成单个固定工作量分片：

```sh
python3 -B team/optimizations/o0/generate_matrix.py \
  --dataset 0 --shard 0 --shards 6 --output /tmp/o0-matrix-data-new
```

使用已有GNU RISC-V工具链在Linux/WSL编译；AM从Git固定提交导出，原仓库不修改：

```sh
python3 -B team/optimizations/o0/compile_matrix.py \
  --am-repository /path/to/nexus-am --output /tmp/o0-matrix-build-new
```

运行入口刻意只接受本次固定构建回执和基线二进制。重新编译的路径/工具日志会改变回执，需先审查并更新独立pin，不能编辑回执强行匹配。新模式或新硬件来源必须另立证据门禁。

```sh
python3 -B team/optimizations/o0/run_matrix.py \
  --images /path/to/frozen-matrix-build --output /tmp/o0-baseline-runs-new \
  --emu /path/to/pinned-emu --reference /path/to/pinned-nemu.so \
  --flash /path/to/pinned-flash.bin --jobs 8
```

既有结果见 [证据目录](../../evidence/o0-progress-20261017/)。所有执行/输出目录均须新建，不覆盖失败或历史结果。这里的旧 `host-check.json`、`host-tests.txt` 仅记录最初来源分支的合成轨迹测试，不表示当前环境缺工具或真实重放尚未完成。
