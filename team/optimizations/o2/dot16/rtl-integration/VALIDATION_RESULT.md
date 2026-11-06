# Dot16 生产 FU 验证结果

## 结论

2026-11-06 UTC，六路径接入候选在真实生产 `VDotElastic` FU harness 中分别通过 `VDOT_DOT16=0` 和 `VDOT_DOT16=1` 验证。两次均完成 Chisel elaboration、生成 RTL 的 lint、Verilator 编译、正测、四项原观察错误注入及源码/依赖前后校验。开态验证包含 dot8/dot16 混合算术、满速接收、ROB 取消和复位。

这是 **FU 级资格**。当前结果不包含整条指令译码、父执行单元、架构寄存器别名、整核 DiffTest、应用周期或 ASIC PPA。FU 测试中的 `cycles` 是该测试序列的推进拍数，不是 GEMV 或模型推理周期。

本记录追加于 `README.md`、`review.json` 的接入准备快照之后；原静态审查文件和原始失败记录保持原样。规格及验收条件见 `VALIDATION_CONTRACT.md`，完整机器记录见 `validation-result.json`。

## 输入与执行身份

检出基点为 `c981529dc6e493fb7deee8429b9ce05fd197497b`。生产补丁 SHA-256 为 `5b5824bac200c2a775598686e550854f8276d5db007b72f4b7be92437b4d3416`，六个结果文件及两个未改依赖逐项匹配 `source-manifest.json`。00:57:24 UTC 在常驻 WSL 工作树完成 `git apply --check` 及应用；HEAD 和 index 未改变。Windows 主仓生产 RTL 在该应用记录中仍为未应用状态。

| 输入 | SHA-256 |
| --- | --- |
| 新运行器 `run_fu.py` | `db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3` |
| 测试派生器 `derive_fu_test.py` | `e5f5daa27840e69ac873d59466587de95721de0ba154308c0875e8ef6b4f6196` |
| 新验证合同 | `aa14f9c18152651f4ec5bfc3fe4765316d7e18f48e512411dfc557ab06b824a2` |
| 原 O2 运行器 | `125cd5a308fa0253c7bd0dbc6d9ea7593afea6e7a118e3b544bfd1dab0fd7922` |
| 原 FU 测试 | `d4dc81c7c206f1d395856023b01a32e76bf1dbef957b9023f8debc0a549bc01d` |

原运行器和测试未修改。新运行快照分别记录机械派生结果，能逆向恢复原文件全部字节。两个 flag 使用相同源码输入清单：433 个文件，清单 SHA-256 `80637d38348fbecd928f6442fd0c69fab763a918ac8da8642a5a3667dacdc9c2`；126 个固定子模块，清单 SHA-256 `de4cf9023b946028d6c50594e5faa2ef3d59d4d6031859e2ae84622819cf47ba`。两次结束均有 `SOURCE_AND_DEPENDENCIES_UNCHANGED`，控制文件和运行快照也前后一致。

证据根目录为：

```text
/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-production-20261106-0014-pro2
```

| 运行目录 | 实际外层起止时间（UTC） | 外层用时 | 终态 |
| --- | --- | ---: | --- |
| `flag0-01` | 00:59:41.572–01:06:35.006 | 413.4 秒 | 版本资源生成失败；无 FU 仿真 |
| `flag0-02` | 01:18:55.757–01:27:04.223 | 488.4 秒 | `DOT16_FU_FEATURE_0_PASS` |
| `flag1-01` | 01:28:03.945–01:28:34.196 | 30.2 秒 | `DOT16_FU_FEATURE_1_PASS` |

三个外层回执均确认清理完成；两次通过运行的控制器还确认本次进程组已消失。各次均固定 CPU1、jobs=1，预算 900 秒。第二次成功运行使用第一次成功运行的独立 Scala 缓存，但执行了新的 `runMain`、RTL 生成及仿真；开态 elaboration 实际用时约 10.94 秒。

## 实际覆盖与结果

| 指标 | 关态 `flag0-02` | 开态 `flag1-01` |
| --- | ---: | ---: |
| 原冻结输入数量 | 10,022 | 10,022 |
| 总接受数 | 23,327 | 43,699 |
| 已比较响应 | 22,476 | 42,736 |
| 被 ROB 取消 | 739 | 835 |
| 被复位清除 | 112 | 128 |
| 复位用例 | 8 | 24 |
| 原 dot8 连续接收间隔 | 10,021 | 10,021 |
| 追加关态 op1 拒绝 | 8 | 不适用 |
| 追加关态未知 op 拒绝 | 8 | 已计入开态非法配置 |
| 追加合法结果比较 | 不适用 | 20,124 |
| 追加非法配置 | 不适用 | 40 |
| 追加混合流连续接收间隔 | 不适用 | 20,043 |
| 追加混合流首响应延迟 | 不适用 | 2 拍 |
| 追加混合 ROB 取消组合 | 不适用 | 96 |

两种开关的接受数均等于已比较响应、取消数与复位清除数之和。开态新增算术比较由 10,022 个冻结输入各执行 dot8/dot16 一次，以及 40 个定向输入各执行两种 op 构成；定向输入包含有符号极值、上半区独有贡献和逐元素贡献。

原四项 `identity`、`wen`、`high`、`cancel` 注入在两次运行中均真实返回 1，随后原 checker 均返回 0 并给出对应拒错通过标记。这些是 observation fault，表明原 scoreboard 能拒绝相应错误；本次没有新增 RTL 变异实验，也不将这些结果称为 DiffTest。

| 关键产物 | 关态 SHA-256 | 开态 SHA-256 |
| --- | --- | --- |
| `status.json` | `ce754ed4351dae06120121a64f42a8d1e5f99546409bd5d838b06dcd2f1dd069` | `3dd0b4a052e45c36b37512714442568b778a14db5944a6b2d205f018e0727156` |
| `campaign/result.log` | `a24135b76fb0398d8ccae9295bc9898c6661170147dd29dc5fc1b5c418782d5e` | `90bde2c7d07ce7e0f7add924f2672feab70c37923ffebc334817ccfb20b133a5` |
| `rtl/VDotElastic.sv` | `f28ac5bc52d2e0736b3733f8a69756daf860480b72812472abad0bc1306eba2d` | `c15778eb5c7089af40422b7002fde00d552dd7274b88cecb5f132d15e984ed1e` |
| 仿真可执行文件 | `e9aefc0f0406b79b8239bee34fb6b896f3f2f225b8e9632a7e6a281a978f43c9` | `254bbd04909fbf6b730bd7c833a95d264a14dad899eba17a02cf5e4ec9621b01` |

两次使用相同冻结向量文件，SHA-256 `901a7be30e62b81bcd3df55b20538a5ba9c879ba9c7c34f28b8c0421d8e6a327`。独立结果读取再次核对了向量和可执行文件的实际大小、SHA 与原产物清单相符。

## 首轮失败与恢复依据

`flag0-01` 已完成全部相关 Scala 编译，包括 377 个 XiangShan 源文件和一个 FU harness，随后 `VcsVersion.vcsState` 中的 Git 调用返回 128，报告无法找到仓库。它尚未产生本次 FU 的 RTL/仿真结果，失败日志 SHA-256 为 `3b328e0fe5d235a52c111fb61d0ae4bba25701a3ecdd50c4fa0b9951f66bc28f`。

[Mill 0.12.3 的固定源码](https://github.com/com-lihaoyi/mill/blob/a6b3b7225a989ff8e8aa548f1af74278dcaac18f/runner/client/src/mill/runner/client/MillProcessLauncher.java) 将实际进程工作目录设为输出目录内的 sandbox；[VcsVersion 0.4.0](https://github.com/lefou/mill-vcs-version/blob/55c7a025659895c00825d9cb7ea81f3f6d9031b5/core/src/de/tobiasroeser/mill/vcs/version/VcsVersion.scala) 以及本仓固定 `build.sc` 的部分 Git 调用未指定 cwd。将 Mill 缓存放在仓外时，这些调用不能通过父目录找到真实仓库。

恢复仅放宽本次自有运行合同中的缓存位置：使用同仓、无符号链接、已由现有 `.gitignore` 忽略的 `out/dot16-fu-20261106-pro2`。正式运行输出仍在上述仓外证据目录。未改官方依赖、build.sc、旧运行器或 Git 元数据，未设置全局 `GIT_DIR`，未复制旧缓存内的绝对路径元数据。原失败目录和原仓外缓存保留。

预检记录位于 `recovery-02/state.json`，SHA-256 `312980fc7976d9644fb752e4e90fb55f2df03283b7db2fba5356ae3a71ee025b`。新的独立缓存目录内，Git 顶层确认为常驻源码根，十个顶层子模块均处于指定版本。运行器还以快照 `MILL_JVM_OPTS_PATH` 明确设置实际 Mill 主 JVM 的 4 GiB 堆上限与单核参数；该选项文件参加快照完整性核对。

## 后续边界

本次只建立两个开关状态的 FU 资格，不改变已有较快 RVV 对照或任何冻结实验结果。后续如继续，应分别建立 dot16 译码/父执行单元及整核的新运行身份，再在合格 reference 和公平条件下比较实际应用性能。独立原型面积、局部指令数或本次 FU 仿真拍数均不能代替这些结论。
