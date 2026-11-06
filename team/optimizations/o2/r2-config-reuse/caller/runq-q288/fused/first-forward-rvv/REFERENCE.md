# FR / GS32 / paired16 首次完整 forward：参考资格与交付入口

合同：`r2-s3-first-forward-rvv-v1`。

**最新运行状态（2026-11-06 05:37 UTC）：目标外层作业处于 running，资源 profile 已冻结。** 本次已经实证的新组合 GNU 构建、五例参考和原 T17 完整物理身份预检可独立交付；三臂实际回执与周期结果将在原 owner 终态导出后汇总。运行身份和观察范围见[第6节](#target-run-status)。

**04:15 UTC 参考与预检检查点：新组合 GNU 构建、五个独立参考进程及原 T17 完整物理身份预检已经通过；当时目标整核尚未运行，性能未合格。** 三种方法共用一份实际 core、ELF、模型和初始化逻辑。controller-05 使用原 first-token 的92项冻结目标闭包和原NEMU manifest；全部原校验保持启用。

## 1. 交付对象与语义边界

本候选比较 token=1、position=0 的一次完整 forward。FR、GS32、paired16 只在七个 K288 静态调用点选择不同的 RVV 内核，唯一 W2 静态调用点继续使用原 FR 路由。三个消费者共用模型指针、初始化和状态布局；FP 运算顺序、量化、scale 消费与既有结果合同保持不变。没有修改生产 RTL、官方程序、赛事材料或稳定默认选择，也没有解除旧 paired16 性能实验的 HOLD。

正常目标镜像共 77,115,360 字节，只允许偏移 `[73421464, 73421468)` 的方法控制字不同。其余字节全部相同，negative=0、UART=1。截至04:15检查点，三个目标镜像身份已经在内存中实际构造并逐字节比较，当时尚未生成并启动三份目标 EMU 输入；参考用镜像的 UART=0。当前目标作业的启动记录见第6节。固定 BEGIN 文本在计数器窗口之前；方法控制字读取、校验和实际分派位于窗口内。四个有 fence 的 CSR 读取按 cycle、instret、instret、cycle 排列，全部读取完成后才写报告。没有引入 GS32 正确性专用 wrapper 的两次全状态预扫描。

计时范围是既定准备状态下的完整 forward，不含模型载入或离线 packing。不能将该窗口称为包含预处理的端到端首次 token 延迟。当前所有 instret 数字来自 NEMU 参考执行，不能替代 XiangShan cycles、IPC 或应用加速比。

## 2. 实际参考结果

五例参考 campaign 实际从 `2026-11-06T03:22:58.659389+00:00` 运行至 `03:23:14.535641+00:00`。五个不同 PID 均实际启动、直接子进程回收、进程组消失，最终 active_pid=null；该参考 campaign 的目标 EMU 次数为 0。

| 参考例 | PID | 实际退出码 | 窗口 reference instret | 结果 |
| --- | ---: | ---: | ---: | --- |
| paired16 负例 | 491 | 2 | 5,175,371 | 预期 BAD，完整比较器定位 byte 152476 |
| FR | 493 | 0 | 7,502,886 | 全部 3,691,424 字节状态及 guards/TLS/model/gold 检查通过 |
| GS32 | 494 | 0 | 4,828,788 | 同上 |
| paired16 | 499 | 0 | 5,175,371 | 同上 |
| paired16 独立重放 | 500 | 0 | 5,175,371 | 完整 validation 与 paired16 相等 |

所有例的精确 fflags 均为 1。负例在计数器窗口之后注入，正常比较器拒绝位置必须与合同一致。重放用于确定性和资格核验，不算独立性能样本。FR、GS32、P 的 validation 不要求整体相等，因为方法标识和指令数本就不同。

### 2.1 已有参考指令差的限定解释

本次构建的 `gs32.S` SHA `ae014eafe83878378c09fdf53f831a41be406e91c2813f0324571dc966bc6036` 与固定 GS32 v2 生成器的纯文本展开逐字节相同；实际完整 GS32 函数420字节、SHA `2d95481faa1c79f7a8a06ef65fc02154e30cf731e6ba5c990a7209c2e90c32ab`。未变 FR 函数为592字节、SHA `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab`。固定源路径每Q分别为 `11+36*(4+9*109+5)+19=35670` 与 `16+36*(4+9*61+5)+19=20123` 条宏指令。

原 caller 的37个 K288 矩阵对应 `24+36+112=172` 个完整Q288调用，包括13个补齐尾块。因此内核指令差的源码投影是 `172*(35670-20123)=2674084`；本次真实 NEMU 窗口差为 `7502886-4828788=2674098`，剩余14条未逐PC归因。总窗口指令下降35.6409%，仅描述已记录的参考执行，不代表香山周期下降。

172次是固定源码几何与调用路径的投影，不是新动态PC轨迹证明；原 `routing-review.json` 的 `dynamic_call_count_claimed=false` 保持。未为这项解释重跑构建、参考或目标。paired16的真实窗口数继续完整保留，不能只按指令数决定两种候选的周期排序。

## 3. 冻结身份

WSL 运行根目录：

```text
/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/first-forward-rvv-20261106-pro5
```

| 对象 | 运行根下路径 | SHA256 |
| --- | --- | --- |
| 最终构建记录 | `build-02/result.json` | `4aed3c533561caefd420c5909fdbc84ebc457ccf3d43b6b57f5d033a292dd045` |
| 实际 ELF | `build-02/first-forward-rvv.elf` | `be6c3ead424d88b565d212e3d343eb6a3fd3216a227da933d3066bd691fa16b8` |
| 公共 raw / FR 正常镜像 | `build-02/first-forward-rvv.bin` | `160b4863098e97ba0150e98e295391c92ea47fd0aaa2d161f9fec3f4bc865e49` |
| GS32 正常镜像身份 | `normal-images-02.json` 中 `gs32` | `9df8d48aad61f0d78875af4d07c36b313c0005727e4d08946cb54412081e0aa3` |
| paired16 正常镜像身份 | 同上 `paired16` | `186e65469b200d33760b7df7c75eb20975cff8de67090fbd07f5eb5bcdf112f8` |
| 三镜像比较记录 | `normal-images-02.json` | `a23497e39326a50c10979825e68085dc326cb532dc6cae7ee8108e95142d6229` |
| 五参考原始汇总 | `reference-02/results.json` | `3454efa3ef44981ff824d504e100551b78778c97921653fe55267c811c226804` |
| 五参考终态 | `reference-02/state.json` | `2051ebf91ecaf8053e62ab91713a6b0afff12f5c62a101c286c03121f9f05e05` |
| 01→02 实际代码等同性 | `inspection-02/code-equivalence.json` | `f959eca6b9663726a1ed7fa746bbe8fa0d30fd507d25f2ded13593f18b5d8e01` |
| 03 支持闭包补全证明 | `controller-03/support-completion.json` | `240d858662a4a3ec27e38bc218f74e3c8c5215d0cc9bffc83012db14cbe51d96` |
| 原 first-token 闭包本机核验 | `frozen-closure-audit-01/result.json` | `d9a8fe8976730647ce8ec334034de4171be085687ca2619f4929fba48dce1d82` |
| 04 原冻结目标闭包绑定 | `controller-04/frozen-target-closure.json` | `c291af28a3fc4d88251759a6b176e323208e84df4568c67f71bc39025a637348` |
| 04 实际 Python 执行来源 | `preflight-04/executed-python-sources.json` | `5c24b9cb173744ba1015bc635755fa168fa26a3a0bd97a25c7d14059e8f06d37` |
| 05 完整物理预检通过 | `preflight-05/result.json` | `998ce7c328636e53ee066345b297cd7b2663a0c7db51c50c247fc2378bfa608f` |
| 05 控制器绑定 | `controller-05/binding.json` | `0e03ff7964bd17f7d06cdf32e1f984b3ba5c7765a073b10f3e17f6492a431bca` |
| 05 唯一非代码数据补全 | `controller-05/frozen-target-data.json` | `cd00f6e3e945646c2a0693206eb57d0dff004f84a04143669ef85205da8fd367` |
| 05 原物理身份快照 | `preflight-05/physical-profile.json` | `8c473866494044724f5ff3824f2056ec96772e90bb9b86317923afe88b649459` |

01、02 的整个 raw 镜像相同，35 个实际可执行 section 的地址、长度和字节 hash 相同；六份实际 C/汇编输入也相同。ELF 和可重定位对象的整体 SHA 不相同，未将它们宣称为同一文件。02 的五参考资格来自实际新运行，不是从 01 迁移 PASS。

`controller-02`、`build-02`、`reference-02` 及其输入保持冻结。`controller-03` 是原 02 控制器的独立逐字节副本，仅补入一个未被 module 属性遍历发现的 `from ... import ...` 依赖：`team/optimizations/o1/build_inputs.py`，SHA 为 `5378f6e81d1b802effe6ba2605996bc2500d6f7c2134ad97f0b8968c40db00cb`。`seal.py` 保存父 binding、原文件 SHA、新增清单及来源；原有 helper 发生字节冲突会拒绝复制。03 的 guest、derive、reference、audit、run 代码均未改变。

## 4. 失败记录与物理身份预检边界

第一次参考准备在任何 NEMU 启动之前被 `S3 runtime module roots differ` 拒绝。原因是新调用把实际仓库根传给了冻结快照模块。修正仅位于新控制器的绑定层，沿用已有 GS32 的只读 Git 元数据上下文；物理硬件检查在该上下文外执行，避免 `GIT_DIR` 覆盖硬件仓库。`short-reference-01` 原记录保留，实际新增 NEMU 为 0。

`inspection-02` 预检随后发现 helper 快照遗漏 `build_inputs`；`controller-03` 补全后，该导入错误已消除。03 使用原 `qualified()` 再审同一构建、五例原始 dumps/receipts 和 P 重放，并继续进入原物理硬件检查。03 的失败位置是：

```text
/home/lizufan/riscv-lab/t17-clean-20261024-0854/clean-02/source/team/scripts/prepare-core-baseline.py
FileNotFoundError
```

调用链为 `clean_profile.hardware_profile → run_suite.hardware_guard → live_inputs.verify → build_inputs.verify_dependencies → runpy.run_path`。后续只读核查证实，旧 T17 的实际 HEAD `34bae6d4acceac939f958199dae53c14bc1f6183` 的 Git 树中不含 `prepare-core-baseline.py`、`build_inputs.py` 或 `live_inputs.py`，原硬件清单也没有这些项。因此这不是文件被删除的证据；原因是新控制器误选了面向当前 live build 的守卫版本。原失败记录见 `preflight-03/check.stderr.log`，SHA 为 `87d71a3a7660a0c3c8455539d6d8af95ca19d6cdf38dad204ff2f4ea35baabe6`。没有向旧 T17 树补文件或跳过校验。

原 first-token 发布 manifest（`norm/evidence/first-token/manifest.json`，固定提交 `d98b5be4795c4b61b553f62c6863610f0313dce8`，SHA `df00872b6b493d9a89c37ca72c226d96bf7d5ed2882afc232186e765d68475ef`）内两份 target 闭包均为相同的 92 项、981,710 字节。本机原 `norm-resume-20261027-2000/first-token-target-01/runtime-source` 的全部文件与之匹配，原 runtime-inputs、resource-contract、parent-identity 也匹配发布记录。

`controller-04` 保持所有原自有控制器代码和 input pins，独立恢复完整原目标闭包：7 项 helper 版本恢复，4 项当前 live-build 专用 helper 从新执行目录排除，补齐原闭包的39项文件。旧控制器、构建与五参考完全保留。`rebind_frozen.py` 不从当前仓库发现或加载新 helper，也不修改旧 T17 源目录。

04 的实际短预检在 `2026-11-06T04:00:23.2916894Z` 启动、`04:00:35.8790926Z` 终态退出1，cleanup=true、输入无变更。五参考已再次审查，原物理守卫走过硬件、依赖和生成物核验，随后在 `artifact_guard.verify_nemu` 读取新 target-support 下 `team/patches/nemu/manifest.json` 时失败。该数据文件不在原92项归档内。实际执行记录包含79份工程 Python 来源，当前软件仓库执行来源为0，521次子命令全部为 Git；实际使用旧 `run_suite=7bc68d73…`、`build_profile=1650856f…`、`artifact_guard=95eabdc0…`，`clean_profile=1c4c467f…` 来自既有 GS32 冻结 support，旧硬件树 `build_fullcore=8a66fb75…`。不能将前半段通过称为完整物理 PASS。

已逐函数核对原 artifact_guard：`verify_nemu(reference)` 的 helper-ROOT 非代码数据依赖仅为该 manifest，未打开 patch 文件。原 T17 提交与上述发布提交中的 manifest 字节相同，1062字节、SHA `1fee8f48616d7d09f46fd5924fb677f4a042ab7a6e2098a4af93e5e4e6a495a1`。05已核对本机原文件、原硬件HEAD Git blob与该完整SHA相同；原NEMU provenance等于父身份，manifest全部六字段与provenance一致。随后原校验器再次执行全部源码、配置、依赖、编译输入、二进制和metadata检查。

05在 `2026-11-06T04:07:34.1749595Z` 启动、`04:07:49.5925249Z` 终态退出0，外层15.370秒，cleanup=true、输入无变更。`qualified()`重新审查原五参考并通过完整物理身份检查：429项硬件源码、21,236项依赖、1,672项生成物、十九metadata、原EMU与NEMU provenance均保持父身份；运行输入共651项。实际exec记录有81份工程Python，当前软件仓库exec来源0，533次子命令全部为Git。没有重建客体或重跑NEMU，也没有启动目标EMU。在04:15检查点，CPU0已释放，三路目标资源profile尚未建立；后续启动记录见第6节。

两位独立 Pro 已核查最终 ELF 的三分派入口、全部24个静态 route 调用、W2保留FR、共享模型/状态、四个CSR链和控制字读取边界，并回读五参考实际回执。其结论限定于这些客体身份与测量窗口；05物理预检为另一次实际执行，目标运行仍待完成。

## 5. 证据与复现入口

`evidence/reference-v1/` 保存构建、五参考及至 preflight-03 的原字节元数据、原始外层进程回执和 SHA 清单。[evidence/preflight-v1/raw.zip](evidence/preflight-v1/raw.zip)和[清单](evidence/preflight-v1/manifest.json)保存24份来源、04失败、05成功及实际执行脚本/物理身份原记录；zip为424092字节，SHA `ac77797a378d8ea1e4c946a78558d7e9b00e4b00cd38400dfd61ae9a8f5ac064`。所有原始目录仍保留在上述运行根及下述 Windows 回读目录。它是元数据交付；完整 ELF、raw 镜像、五例逐字节 dumps、日志、运行输入和所有失败目录仍保存在上述 WSL 运行根，不在此重复复制大文件。

Windows 轻量回读副本和各次启动脚本位于：

```text
D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\runs\first-forward-rvv-20261106-pro5
```

复现入口为已通过预检的 `controller-05/run.py`，使用已有 `build-02` 和 `reference-02`；adapter/identity 精确路径在根目录 `config-01.json`。下面描述新的独立复现流程：取得共享CPU协调窗口后，以新 operation ID、fresh output/profile 和明确 CPU 槽调用 `--freeze`，随后执行同一 profile 的三例正常 campaign。本轮已启动作业的原身份与路径见第6节。目标计划只有 FR、GS32、P 三个新进程，没有追加负例或第四个重放目标进程。原四CSR退休链、custom协议、DiffTest、trap、资源和清理检查继续生效；`full_retirement_window_audited=false` 保持。

本节交付的是已闭合的参考结果与物理身份预检。目标 DiffTest 和完整 forward 的周期观察将在原作业完成后分别报告；GS32 与 P 的周期排序以该实际结果为依据。

<a id="target-run-status"></a>

## 6. 三臂目标作业已启动（2026-11-06 05:01 UTC）

在上文04:15检查点之后，共享CPU正式交接；人工要求的协作研究汇报完成后，主端于04:56:23 UTC恢复原合同。本节是新的运行状态，前述原始失败、预检和五参考记录保持原样。

唯一外层ChatPC作业 `d9b025210fdcd3c1fd06c2f645cfad75.9ff2bf48040065fbc99e3c3509bc2522` 于 `2026-11-06T05:01:06.0549488Z` 实际启动；实验操作ID为 `f3e06512-04c6-427c-a0cf-5bfe42a2120c`。原 `--freeze` 于05:01:20.421730 UTC产出 `FROZEN_BEFORE_EMU`，资源合同926434字节、SHA `16c27202595792f3bd80eba42e8f1664877ba1128d46bdda541a6d262b97c1e3`。它声明FR/GS32/P分别使用CPU0/2/3，仍为每臂40M cycles/28800秒、单线程、seed1/128MB、每个原始输出流4GiB；`performance_qualified=false`。

实际owner为运行根 `launch-target-01.py`，SHA `ec93e1afe5404caa8f9196f9dadce3adf0f68a3d1ce4e008d4fa76596a646537`；原 `controller-05/run.py` SHA `976cacfb48631042e57e9d2393ddca4653866cc07142e1b0b49185b7719e18f6` 不变。owner顺序调用原冻结与campaign入口，保留其全部前后守卫、预算和进程清理。没有重新构建客体、增加参考执行、追加目标负例或重放。

输出为上述WSL运行根的 `target-01/`；owner记录为 `target-launch-01/`，冻结profile为同根 `target-01.resource-contract.json`。Windows同名运行目录的 `target-launch-01/resource-contract.json` 已回读字节与SHA；owner终态会回存小回执。运行保护已登记并回读 [Issue #2 comment 6677347729](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6677347729)。

05:05 UTC可确认外层running和profile冻结；各臂实际PID及进展尚未获得合法读取结果，不把外层状态当作三个EMU均已启动。只读PowerShell观察请求因同目录长作业锁被拒绝且未启动；专用FileOps不接受该WSL UNC路径。没有换目录或资源声明绕过锁，没有重放外层。原作业继续受其超时、输出上限和清理约束；后续以原进程回执和原始输出给出结论。
