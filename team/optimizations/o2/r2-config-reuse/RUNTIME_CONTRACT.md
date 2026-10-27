# R2-S3 重复配置：GNU 与整核运行合同 v1

合同 `r2-s3-config-reuse-runtime-v1`。源码基点 `43e562d5e174763d9469b6c1c2124df0d60dc576`；沿用[主机合同](CONTRACT.md)的固定语义证明和候选，保留原主机结果及全部冻结输入。新增运行适配只定义构建、测量和证据身份，不修改 `candidate.py` 或任何官方权威程序。

## 1. 假设、范围与取舍终点

假设：在原 firstdot 的固定 GEMV C ABI 路径上，删除已证明为恒等状态转换的重复 `vsetivli x0`，可能降低实际调用窗周期。vdot 与 RVV 使用同一删除规则；静态条数不用于预测性能。

首先只测 8×32 / dataset0：firstdot 与 config-reuse 两个完整加载镜像，每图包含 basic/reuse × vdot/RVV。沿用原调用和返回、输入、24 窗口 AB/BA 计划及其中 16 个正式窗口。每格4正式样本；独立进程重放比较全部24窗口。

采用筛选条件预先固定：config-reuse/reuse/vdot 的正式周期总和同时低于本轮 firstdot/reuse/vdot 及本轮四种 RVV 格子的最小总和，且正确性、布局、负控恢复及重放全部通过，无未解释退化。满足后才扩大到四形状/三数据集与普通C资格；不满足则保持原 firstdot/R5，停止扩大本假设。完整四形状里，K13允许继续保留更快RVV；不为统一名称强行采用较慢vdot。

这个 endtoend 是既有 GEMV 函数调用边界，不是完整应用或LLM。本轮不改变硬件，新增面积、STA、频率和功耗验证为 NOT_TESTED，不从软件周期推出硬件PPA。

## 2. 来源、输入与可修改边界

- 新适配入口为 `runtime_candidate.py`、`runtime_gate.py`、`runtime_experiment.py`；原主机候选、S1/firstdot、R4、模型、计数/退休/数学/O2检查器、官方 AM、NEMU与EMU保持原字节。
- 主机生成合同继续为 `r2-s3-config-reuse-c-abi-v1`，harness banner 仍为 `r4-gemv-c-abi-entry-v1`。外层 manifest 增加独立 runtime 合同和适配器SHA；`runtime_qualified=false`保留。只有本轮构建/运行结果授予其明确范围的资格。
- 两镜像的 firstdot 基线完整BIN、独立 GNU wrapper 对象和公共对象，必须逐字节等于已封存 firstdot matrix 归档。归档manifest SHA为 `0c8d3159c91aa3c934c7bfb7f2640906844246e812c0b5bfc556cdfb86d0d3b4`；选定压缩载荷的存储哈希、原始长度及解压哈希一并核验。
- firstdot图中的两个完整RVV槽还须与该归档内S1图逐字节相同，保留此前较强S1算法及固定入口。最快RVV分母只取本轮新执行的两变体、basic/reuse全部合格RVV，不引用历史周期。
- 硬件复用T17身份SHA `4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb`：源码 `34bae6d4acceac939f958199dae53c14bc1f6183`、EMU `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`、正常参考 `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`。运行前后按原T17物理门禁复核，不转移历史PASS。
- 旧R5默认和firstdot公共库不变化。若扩大并取得普通C资格，可交付独立可选入口，默认切换仍需对应影响验证。

## 3. GNU构建与编译后约束

每个镜像使用独立输出和私有生成器快照。总构建并发不超过四核，AM/klib只读复用，原 make 入口通过 `-o am -o klib -j1` 防止并发重写官方依赖。每图实际构建可执行AM ELF/BIN、独立GNU wrapper/public对象及普通C可重定位链接。

保持原R4门禁：完整ALLOC节布局、五个8KiB的text范围（启动区加四函数槽）、槽外加载字节、API地址、plan和cases/header一致；真实GNU leaf与wrapper内及链接后字节相同；一次 `jal ra`/一次 `ret`、前8字节ABI和7条调用额外开销；实际编译路径解析退休数，禁止手改旧指令计数。

每对leaf再检查：原firstdot body与主机证书父body一致；候选只能删除证书指定的 `vsetivli x0` 机器字；保留字及顺序、ABI前后缀不变；整个BIN在旧leaf范围外逐字节相同。证明由冻结主机候选重新计算，编译后删除检查独立解码opcode/funct/rd。原数学模型对当前GNU完整128位输出、带毒寄存器和访问边界重新执行。

源快照、构建命令/退出、工具链、AM库、ELF/BIN及链接对象全部记录SHA；来源漂移、缺图、重复图、布局变化或不合法删除均拒绝。旧输出、源码重叠输出均在写入前拒绝。失败批次保留；不隐式续跑或覆盖。

## 4. 实际执行与公平性

性能EMU串行，继承最多4个CPU的亲和性；启动前核实同机重任务。保持原 `--seed=1`、128MB RAM、正常参考、flash、2,000,000周期上限及原超时。宿主墙钟时间仅记录运行成本，不作为处理器性能。

最小探针共5个新EMU进程：候选bit100负控1次、同BIN正常恢复1次（计为候选正式结果）、firstdot正式1次、两图各重放1次。负控须发生在本次候选实际路径中的首条vdot，PC由当前ELF解析，匹配vd0/`0x0388000b`/bit100、唯一mismatch、预期非零退出及合法O2部分轨迹；不能复制旧PC。正常恢复使用新PID、同一完整BIN和真实正常参考。

所有正常进程验证全部first/warmup/measured窗口：UART数学值、完整128位结果、CSR、精确退休/调用轨迹、周期校准、O2两槽协议/事务与排空。所有正式统计不含重放和warmup；恢复结果不重复计数。独立重放要求全部24窗口的seq/cycles/instructions逐项相同。

扩大时沿用相同规则，原探针结果在其源码与输入仍固定时直接纳入，避免重复已完成EMU；每个形状dataset0两变体各重放一次。若改动生成器、核心运行门禁或输入，则需独立新身份并按影响补测，不能把旧结果改签。

## 5. 证据、复算与交付

保存成功/失败尝试的state、实际命令、进程/时间/退出、日志原文、源快照、实际ELF/BIN/参考对象、负控夹具和样本。归档与原文审计明确区分字节完整性和语义验证；复算不得依赖旧物理build目录或再启动EMU。物理硬件/工具链在实跑时核验；离线持有哈希的项目不得写作已重新获取实物。

结果至少分开标注 GNU/模型、EMU/DiffTest、周期与重放、普通C/库、PPA、独立复现。工程结果、计分板及Issue只按各自职责维护，不把一个探针写成全矩阵或全赛题完成。
