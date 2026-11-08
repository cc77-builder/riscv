# Prefix K768 适配器：有限独立静态审查

审查时间：2026-11-08 04:43–04:45 UTC。范围为本目录最终三件源、实际冻结 profile、启动器与资源声明；以已经审查的 K288 适配器为父，只核本次增量。仅在云端读取文件、比较字节与解析记录，未调用 PC/Pro，未运行 preflight、被审 helper、构建、EDA 或 EMU，未修改实现或旧证据。

**结论：未发现阻止这一次 K768 normal 目标运行的确定缺陷。** 五项修改、冻结参考、实际 profile 和启动绑定一致，可继续既定的一次有界试验。本报告不授目标运行 PASS；目标尚须由真实执行及原有回收、输入复核和 guest 门禁给出结果。

## 1. 最终源身份及派生闭包

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| `run.py` | 25519 | `984ff535756419240db26deaea96214b3ee98d65e30b0e10476abcd9cab06ac9` |
| `TARGET_CONTRACT.md` | 5429 | `379fb985f0c403bea0245c7ffbebbc15a1177e1273a4ef34ba8519a3c3d655b3` |
| `source-derivation.json` | 2136 | `b7ede00dad15845efb8f1079065af254537e001f436e1ea04b91107f1895e2dd` |

独立按 derivation 的五项替换逆还原，每项匹配均恰好一次，完整结果与 `../prefix-k288-preparation-01/run.py` 25519 B / `d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3` 逐字节相同。差异仅为合同名、固定 K/周期/墙钟预算、profile 范围说明、preflight 状态名和 CLI K 选项。

`prefix_hardware()`、`guest_check()`、`run()` 均与父文件逐字相同。derivation 中三个函数的长度与 SHA 也独立复核成立，其截取口径包含函数后的一个换行。此前已闭合的 ABI 原始日志绑定保持为 `5d6e133f…`，没有回退至 layout JSON 的 SHA。

因此本次没有改动成熟的 guest 检查、进程组回收和失败处理；复用它们不表示把 K288 的目标 PASS 转授给 K768。

## 2. K768 与冻结参考相容

本地 `reference/result.json` 为 166147 B / `65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0`；`reference/k768/static.json` 为 15282 B / `b3696cc418c12faf83a049adc1d83c1fbdc8646f8bad004393e6ec6ef63e4226`，后者与 result 的 K768 static pin 相符。result 中 21 个命令的退出码符合原合同，两项 negative 为 2，其余为 0，均记录直接子进程已回收、进程组消失。

既有 preflight 对 K768 选择 `k768/images/normal` 和 `w2_scalar`，不会误用 K288 的 `normal-0`/`q288_oracle`。K768 normal 与 replay 的完整 validation 对象相等；static inspection 与 campaign inspection 相等，四个固定 GNU kernel 的长度和 SHA 已进入实际 profile。

| 项目 | 独立核对的 K768 值 |
|---|---|
| 目标 ELF | `47cd616a5c89f27a679d2287998df45675413d96935ec21e1fa2fa8419c83f12` |
| normal 目标 BIN | `48302994e55a5ed4a0dfb9b577d65507eab12d343c3de48af895195b7d247b39` |
| 窗口顺序 | `[1,2,3,4,4,3,2,1]` |
| 每窗 instret | `[58458,34085,58458,34085,34085,58458,34085,58458]` |
| FCSR / golden FNV | `1` / `f909c47ea8f72842` |
| 完整调用规模 | 8 次 warm + 8 次 measurement；每次 288 输出，共 16 次/4608 输出 |
| prepared 有效载荷 | `288 × (768 / 32) × 4 = 27648 B` |
| success PC / control offset | `2147483964` / `513536` |

八个 instret 值由参考 samples 的实际计数差独立计算；每个 sample 的 FCSR、FNV 和错误字段与 normal record、实际 profile 一致，参考 final FCSR 为 1。prepared 的参考 dump 长度为 27776 B，含 128 B 保护区域，与 profile 的 27648 B **有效载荷**无冲突。

原逻辑仍重新 `screen.inspect` 完整 ELF/BIN，并验证目标与参考镜像仅 UART 控制字从 `[0,0]` 改为 `[0,1]`。本审查读取静态记录与源码，不冒充重新执行该检查；实际 preflight 完成情况由根端取得的回执负责证明。

## 3. 实际 profile、启动路径和资源

`actual-profile.json` 为 93667 B / `c8afad336dc289e76cb7055b6430399a3df77632232eed2dfc8e77e4c5b248f9`，其状态仍为 `FROZEN_BEFORE_EMU`。独立解析确认上述 geometry、镜像、四 kernel、窗口、flags/FNV、success PC 和正常控制字全部一致。

457 项 pins 包含新 core-build-02 结果 `06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2`、smoke02 结果 `2ec969938a8c4f790e10ba7067befe22f890946b58f2a533276d3051c0cc6eda`、smoke runtime 表 `9df6be73…` 和 EMU `6387d998c3f715a9ced1f44c4410f0f29f76780a96ec15c1830c8828ded6f887`。原参考的 298 项 original inputs、41 项 snapshots、111 项 generated inputs 均保留同一 SHA。实际运行源指向新目录的 `preflight-01/inputs/run.py`，其 SHA 与最终 `984ff535…` 相同。profile 的 flags 和 1400 B ABI 全部偏移保持 K288 已审查值。

| 启动文件 | 字节数 | SHA256 |
|---|---:|---|
| `launch.py` | 3349 | `57fbf06b56f8d844c17ee2e18c9b7243078f3d7df9c9265131ba30409194c351` |
| `launch.ps1` | 4331 | `5866de2c1b398c4d186b972f948d7bcb38184e909648cb0812d0eb82e1933e1b` |
| `launch-resources.json` | 8382 | `a5796226b08465fe61165f75e36c5458a1389d3b40c0888d255dbb0b587a5b58` |

PS here-string 内嵌 Python 与 `launch.py` 相同，仅末尾空行不计。启动器绑定三件最终源的长度/SHA及本次真实 profile 长度/SHA，重新核全部 pins 后，以 `/usr/bin/python3 -B` 执行冻结 snapshot，实参传入正确 `--profile-sha256`；不依赖 copyfile 为 snapshot 设置可执行位。run 本身继续核 profile、runtime_source 和全部输入。

按路径分量匹配，并将 `/mnt/d/` 与 Windows `D:\` 对应后，40 项声明覆盖全部 457 pins；profile、三件 input 源、Python、`/proc` 等额外读取也有对应声明。唯一 write 为新 `dot16-prefix-k768-20261108-main/target-01`，无输入位于其下。没有写入 K288、原参考或旧 core/smoke 输出的声明。

固定 CPU1、nice5、6,000,000 cycles、7200 s 内层、每流 16 MiB，与合同/profile/启动器一致。启动前仍检查 CPU 占用、四核总预算、可用内存和磁盘；这些是实际启动时的检查，本云端审查不声称已经验证此刻主机可用性。原 signal latch、TERM/KILL/reap、失败证据及最终输入复核未改。

7800 s 外层必须由实际工具提交参数落实；源码和 PS 自身不设置这层工具期限。按最迟 05:10 UTC 启动计算，内层 07:10、外层 07:20，距 07:50 收尾分别有 40/30 分钟。启动器的 05:10 检查位于 exec 前，实际 EMU 开始时间以执行回执为准；本次应按既定计划及时启动，不在时间边界依赖静态推算代替事实。

## 4. 本次结论的范围

没有提出新增源码修复或额外验收门槛。原参考 normal/replay 与负例证据适用于参考链；新 K768 目标仍只有计划中的一次 normal EMU。成功可产生该固定完整调用的 target runtime 资格及局部 CSR 周期观察；本报告与 profile 均不授整应用性能、全退休窗口、退休自定义指令计数、完整目标内存 dump 或 ASIC PPA 资格。

较快合格 RVV 对照仍由同次四组窗口保留。prepared 准备在窗口外、额外存储与准备成本没有消失，八窗口也不构成整应用加速或统计置信区间。无需为本次有限试验追加 target 负例、回放、TRACE 或完整 G3。
