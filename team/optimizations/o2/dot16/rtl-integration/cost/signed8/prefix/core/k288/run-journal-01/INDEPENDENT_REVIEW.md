# Prefix K288 适配器独立有限审查

## 结论

**最终修订版未发现阻碍本次固定 K288 回归预检/运行的剩余静态缺陷。** 初版有一处会必然使 preflight 失败的 ABI 文件哈希误绑，已向主端即时报告，并在最终版中修正。该结论不代表目标 EMU 已运行或通过。

只读审查了新 runner、合同、derivation，原 runner、已核验的 core-smoke-02 归档和冻结 builder/checker 源码。没有访问 PC/Pro，没有执行预检、门禁、构建或 EMU，没有修改实现或旧证据。仅新增本报告，不增加无关验收条件。

## 最终身份及完整派生

| 文件/函数 | 字节数 | SHA-256 |
| --- | ---: | --- |
| 最终 `run.py` | 25,519 | `d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3` |
| `TARGET_CONTRACT.md` | 4,024 | `18f5b8b22e5be4ccd98a8cc854662376f90210e1c4dbfa55fae4402f50c07447` |
| `source-derivation.json` | 8,680 | `1dabc73f6a113da24991870b08866af50a72039f9ad4f80bfb8d0a485a75749a` |
| 原 `target-source-01/run.py` | 21,707 | `df95f6a05dbf3ffdf4314de38ecd8bce13ff3a7b63ef2583bb99d00f77e29655` |
| `guest_check()` AST 源片段 | 3,797 | `c655964cf23f4827b27c45834266cd0317b9784ce07e703b4c9bd52b5b5de715` |
| `run()` AST 源片段 | 6,952 | `2b359a5bfe5add01896efbd10beb45bac3e795a66904360e67f26d593d26cbc3` |

独立比较原文件与最终文件：`guest_check()`、`run()` 的完整函数源片段分别逐字节相同；10 项声明替换逆序恢复时，每个 replace 片段都恰好出现一次，恢复结果与完整原 runner 字节相同。derivation 的原/新长度和 SHA 与实际文件一致。没有将其 JSON 中的“unchanged/complete_inverse=true”直接当作证明。

## 已发现并修复的阻塞

初版 `run.py` SHA `abea8b16…` 对 `core-smoke-02/abi-run.log` 使用了 SHA `6a4ec332…`。实际归档显示：

- `abi-run.log` 是 129 B，SHA `5d6e133fb80be4c75e3453364f6515b2a33ede5db81f4294f441fedb1238151e`。
- `abi-layout.json` 是 170 B，SHA `6a4ec3322731720f73f878c2211620a17fffb4b7e0a1c454ebae642261e39137`。

两者 JSON 内容相同，但字节格式不同，不能交换 SHA。初版会在 `pin()` 必然失败。最终版仍读取实际 `abi-run.log`，改用正确的 `5d6e133f…`，随后再比较布局值与固定 ABI；derivation 同步更新。已独立回读最终文件确认闭合，不需重跑 ABI。

## 新硬件绑定确有实质检查

新 `prefix_hardware()` 不是把旧硬件报告改一个 SHA：

1. 只接受固定 prefix `core-build-02` 与 `core-smoke-02/result.json` 路径，分别 pin `06b38d23…` 和 `2ec96993…`。六例状态、schema、ABI、core 身份、完成/输入/回收字段及五条命令名称/退出码/回收均核对。
2. runtime-inputs 文件固定为 `9df6be73…`，要求完整 **24 项**并逐项实际读文件核 SHA。我与已核归档比较了 core、smoke、runtime、checker、EMU 常量，全部对应；EMU/reference/flash/gate 四个身份各恰好匹配一条实际路径。
3. 导入的旧 smoke checker 固定为 `cdd3dcd9…`；调用其 `build_record()` 核真实成功的七阶段构建、固定 builder/lock、generated manifest、实际 EMU 的路径/可执行性/大小/SHA，以及实际生成 header。新 EMU 要求 **71,489,976 B / `6387d998…`**，并要求 smoke 中 EMU 对象相等；header 固定 `6a2ce3ab…`。
4. plan 原件固定 SHA `488be250…`，且实际 core 记录中的 generation/native argv 必须等于 plan。两种环境都要求 D16/O2/T14=1、其余五开关=0；Java 要求唯一 MinimalConfig、唯一单核参数与 DiffTest 启用；native 要求单核、单线程、NO_DIFF=0、trace/database 关闭。已核 builder 的实际 plan schema 和 argv 构造与这些访问一致；不是只在 profile 自填 flags。
5. 实际 ABI 原始输出另行 pin 并比对完整 1400 B 布局；三个 smoke raw log 依实际 smoke 记录 pin；最终六例 checks 与实际 reference 路径对应。这里复用的是已完成证据，不重跑六例，也不赋予更大范围资格。

新硬件之外，原 reference 21 命令/10 次运行、完整 originals/snapshots/generated 输入、K288 ELF/BIN 静态审查、目标与参考唯一 UART 控制字差异、样本/flags/FNV/instret 的核对链保持。新 preflight 限定 K=288、normal-0、4,000,000 guest cycles、9000 秒、每流 16 MiB；不再允许原 K768 分支形成实际 profile。

## Profile 生成后的执行条件与权限

原 `run()` 没有要求额外的代码内人工批准字段，但有以下明确条件；内容 SHA 校验不能被误当作平台运行许可：

- 以真实 preflight 成功输出中的 `profile.json` 和实测 `profile_sha256` 启动。`--profile-sha256` 必须是该 profile 的 SHA，不能传 runner、合同或 preflight result 的 SHA，也不能提前猜一个值。
- 优先用该 preflight 的 `inputs/run.py` 快照，经 Python 调用其 `run` 子命令。`run()` 要求执行源码 SHA 等于 profile 的 `runtime_sha256`；`shutil.copyfile()` 不保证保留可执行位，因此直接把快照当可执行程序启动并无必要。
- profile 合同和 `FROZEN_BEFORE_EMU` 状态必须正确；全部 pins 在启动前、成功路径和最终收尾再核。profile 自身在运行期间也按传入 SHA 再核，源码/合同冻结后不能再改。
- 目标输出必须全新、绝对且不包含任何固定输入；主端按本次独立 `target-01` 使用。外层实际执行资源范围应包含 profile、全部 pins、运行快照的读取，以及新 target 树的写入，并覆盖 CPU1、9000 秒内层和 9600 秒外层/回收条件。预检动作的许可不能被假定自动覆盖真实长时间 EMU 操作；本审查未访问平台，未判定已有外层授权不足，也不要求重复索取已存在的用户授权。

04:30 UTC 是主端调度的实际启动截止；保留字节不变的 `run()` 只控制相对运行预算，不自行检查这个绝对时刻。主端应在该窗口内完成真实 profile 核验并启动；过时按合同取消，不自动改限额或重跑。

## 原行为与有限资格保持

`guest_check()` 仍要求唯一 DiffTest/reference/image/GOOD TRAP、固定 BEGIN/八 SAMPLE/PASS，逐项方法顺序、instret、FCSR 与 FNV，核 16 次完整调用/4608 输出及 guest slots/guards/CSR 结果。`run()` 的 CPU/nice、进程组、信号、deadline、流大小、TERM/KILL/reap、最终输入/信号再核原字节保持。

成功结果只记录该固定完整调用的 target_runtime_qualified 和同一新 profile 下的局部周期观察。旧 f149 周期不转授新 EMU；完整 G3/非法 trap、应用性能、全退休窗口、自定义指令退休计数、全目标内存 dump、ASIC PPA 等边界保持原限制。此次静态审查没有产生新的 runtime PASS。

审查开始：2026-11-08 04:01:43 UTC。最终源码/合同/派生及修复回读：04:04:33 UTC。唯一确定阻塞已修复；其余条件交由原 preflight 和既有执行流程按实际输入完成。

## 实际 profile 与启动器补记（04:08:25 UTC）

主端提供实际 preflight 成功后形成的 profile。本地独立回读 `actual-profile.json` 为 **93,672 B / SHA `ff1fede1efbd70926b6f3ddb00ba1579efcba8a059b8292e514e7888215ffc8c`**，状态 `FROZEN_BEFORE_EMU`，含 457 个 pins。新 core/smoke、EMU、ABI、flags、K288 ELF/BIN、9000 秒/4,000,000 cycles/16 MiB、CPU1/nice5 与已审条件一致；runtime_source 为 `preflight-01/inputs/run.py`，SHA 为最终 `d49d657f…`。runtime、image、ELF 的对象 SHA 同时出现在自身 pins 中。

启动文件身份：

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `launch.py` | 3,351 | `b1384c68556e2c638d8d549e38b8c51ae0fb1f8d6a26a59d95c21efe8f5afe98` |
| `launch.ps1` | 4,333 | `f00121ea5b3342ec5a182abecb411dd5b9eb994a0e7f7a2a3f7e83342281a47a` |
| `launch-resources.json` | 8,382 | `b67d4d5be86931e6c6555b0f395355b08626dab4704b71449945baf52713e7a1` |

没有运行启动器。静态读取确认 PS 使用 Ubuntu-22.04 的 `/usr/bin/python3 -B -c`，内嵌 Python 与 `launch.py` 内容一致（忽略尾部空行），以 ArgumentList 传参。启动 Python 核对三件 input-02 源文件、profile 长度/SHA、profile 固定字段、全部 457 pins、新鲜 target、资源余量/CPU1 占用与 04:30 UTC 截止，再 exec 已冻结的原 `run()`；实际 `--profile-sha256` 正是上述 profile SHA，没有误传 runner SHA。exec 保持启动进程身份，原 runner 继续承担独立 EMU 进程组与有限回收。

对 40 项资源声明作路径分量核对，并将 profile 中 `/mnt/d/...` 与声明中的 Windows D: 路径对应：**457/457 pins 均有读取覆盖，缺项 0**。profile、input-02 三文件、preflight 快照、Python 和 `/proc` 额外读取也均覆盖；唯一 write 为新 `dot16-prefix-k288-20261108-main/target-01`，其中不含任何固定 pin。此核对是资源声明覆盖检查，没有声称在云端重新读过本机全部输入内容；执行时启动器和 runner 都会实际重查。

未发现新增启动阻塞。外层 **9,600,000 ms** 必须来自实际工具执行配置，PS 自身不另设这个 watchdog；主端已明确按该值提交，本审查未调用平台提交接口。04:30 检查发生在 exec 前，实际开始仍以原 runner 的 `PROCESS_STARTED` 事件/host 回执为准。静态核查及 profile 冻结不等于目标已启动或已通过。
