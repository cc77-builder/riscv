# W2 consumer 有限 build/reference 执行合同 v1

本驱动只包装准备器已绑定的 GNU build 或原五例 reference，不生成或启动 EMU，不修改核心 C、derive、build、准备器或原 reference/validate。当前仅完成源代码与接口检查；尚未实际运行本驱动。

## 输入和调用

`--controller` 指向新准备器的完整输出，合同必须为 `r3-dot16-first-forward-w2np-v1`；其中 `binding.json` 包含全部 input/generated pins，必须先匹配调用者提供的完整 `--binding-sha256` 才能导入。所有这些输入、冻结 support 输入、外部驱动与同目录本合同、进程 helper 在运行前后核 SHA，保留实际解析路径。helper 为 `config.w2_source` 所在 GNU 目录的 `inputs/process_helper.py`，固定 SHA `db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3`。

```text
python3 -B run_stage.py --controller <prepared-controller> --binding-sha256 <完整SHA> --output <fresh-build>
  --stage build --cpu 1 --budget-seconds 1200

python3 -B run_stage.py --controller <same-controller> --binding-sha256 <相同完整SHA> --output <fresh-reference>
  --stage reference --build <completed-build> --cpu 1 --budget-seconds 3600
```

`--cpu1` 可代替 `--cpu 1`。`--build` 仅 reference 必需。reference 的 adapter 取 controller 配置，identity 明确取 `dot16_hardware_result`，且要求配置中的 `identity` 已与其一致。输出保持旧 build/reference 的原目录结构，不允许覆盖或续写失败输出。

本轮已准备的 controller-01 binding 为 `e4ccd6e74c31a8b30e9b89088067a5e7364a67f0a2d3e2530ab2eed9bbc687a9`；驱动与本合同留在独立 source 目录，无需改变已冻结 controller。

## 执行绑定

GNU build 使用原 `build()` 的同一个 Python code object 和复制的 globals。只替换 `command`；`g` 的私有代理只把原 `g.parent_inputs()` 包在既有 `support_git_metadata()` 中，读取冻结支持树和其记录的 Git 对象。退出该调用即还原环境，官方 AM 的后续 Git 检查继续发现 AM 自身的 Git。没有修改共享模块或原函数源代码。

`command(argv, out, name, expected=0, timeout=180, environment=None)` 保留原签名、继承 cwd、字典返回值、环境覆盖和 `name.command.json`、`name.stdout.log`、`name.stderr.log`。stdout/stderr 为真实命令原始流，不夹写驱动信息；原 expected exit 检查和完成回执读回保留。

reference 使用原 `run()` 的同一个 code object；仅在其私有 `old.previous` 代理中替换 `spawn()`。原 inputs、image、完整 validate、五例 inventory、BAD/GOOD trap、状态字节、guards、TLS/errno、flags/FCSR 和最终资格判断保持原函数与原条件。负例退出码由原 validate 判断，包装器不会把预期 rc=2 当成构建失败。各例的原内部预算 600 秒、外部 630 秒保持，上限同时受本阶段剩余总时间限制。

## 资源与终态

固定 CPU1、绝对 nice 5、单个外部进程组。build 总预算不得超过 1200 秒，reference 不得超过 3600 秒。清理继承环境，仅保留原 HOME/USER/LOGNAME，并明确 PATH、locale、单线程和不写 pycache；GNU 原 argv 的单 worker 设置仍保留。每个外部进程的 `TMPDIR` 明确设为原函数已经创建的本次输出，GNU 临时文件也留在声明的隔离输出内。单文件软上限 128 MiB，必须有足够硬上限，避免截断约 77 MiB 的完整镜像和 reference 原始文件。

总截止由一次计时信号覆盖预检、导入、Python 校验及执行；自有 Popen 所有权建立和回收区只记录信号，wait 每 0.25 秒检查。每个 GNU/reference 作业有独立进程组；失败、超时或信号沿固定原 helper 的 TERM/KILL/有限等待回收，记录 direct child reap 与整个进程组是否消失。直接进程退出后的残留子组即使成功清理也不能授予阶段完成。

`stage-receipt.json` 与 `stage-input-pins.json` 在原函数创建输出后写入；若在原函数建目录之前失败，已确认隔离的输出最终创建为失败目录保存回执。若输出本身越入输入树或官方 AM，驱动拒绝向该位置写失败文件，错误保留在外层日志。每个真实命令的 argv、cwd、预算、PID、原始日志路径、退出码和清理信息均保留；原 reference 的 case/state/results 回执同时保留。总截止后允许原 helper 完成有限回收，外层运行器另留 60 秒清理余量。

只有原阶段结论成立、输入未变且全部进程回收后，才写阶段完成。build 只证明原静态构建检查；reference 只承认原五例资格。`target_emu_runs=0`、`performance_qualified=false`、`fullcore_qualified=false` 始终不变。任何失败保留原始日志和未完成产物，不自动重跑或降低原判据。
