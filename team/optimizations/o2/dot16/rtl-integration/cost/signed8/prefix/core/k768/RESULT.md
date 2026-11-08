# Prefix core02：固定 K768 完整调用结果

日期：2026-11-08 UTC。合同 `r3-prefix-k768-eight-window-regression-v1`。

**同一新 prefix EMU 实际通过 K768 normal 的八窗口完整调用试验。** 本次只取得该固定例的 `target_runtime_qualified=true` 和局部 CSR 周期观察。没有新 RTL 或软件算法修改，不授予完整应用、G3、非法指令/trap、完整退休审计或 PPA 资格。构建与原六例 smoke 的边界见 [core-build-02 / smoke-02](../RESULT.md)。

## 实际执行与冻结身份

[status.json](status.json) 记录 `PACKED_WS_EIGHT_WINDOW_TARGET_PASS`、`process_started=true`、exit 0、输入身份未变、进程已回收且进程组不存在。采用 CPU affinity `[1]` 单核、nice5、seed1、128 MB RAM，保护上限为6,000,000 guest cycles、7200秒内层预算及每流16 MiB。

[运行与归档记录](run-journal-01/) 中的 host 回执起止为 **2026-11-08T04:46:27.9074509Z–2026-11-08T05:23:51.8534469Z**，回执执行时长为 **2,243,885 ms**。UART stdout 另报 `Host time spent: 2242265ms`；两个耗时值保留各自口径，不能互换，均不作为芯片执行时间、物理频率或硬件加速比。

[profile.json](profile.json) 冻结本次 K768 的457个输入 pins；实际运行记录和归档审计均绑定该 profile，归档阶段再次核对全部457项。EMU 与已闭合 K288 相同，K768 的 runner、镜像和窗口独立绑定：

| 对象 | SHA-256 |
| --- | --- |
| K768 `run.py`（25,519 B） | `984ff535756419240db26deaea96214b3ee98d65e30b0e10476abcd9cab06ac9` |
| `TARGET_CONTRACT.md` | `379fb985f0c403bea0245c7ffbebbc15a1177e1273a4ef34ba8519a3c3d655b3` |
| 实际 profile（93,667 B） | `c8afad336dc289e76cb7055b6430399a3df77632232eed2dfc8e77e4c5b248f9` |
| 新 prefix EMU（71,489,976 B） | `6387d998c3f715a9ced1f44c4410f0f29f76780a96ec15c1830c8828ded6f887` |
| K768 ELF | `47cd616a5c89f27a679d2287998df45675413d96935ec21e1fa2fa8419c83f12` |
| K768 normal 目标 BIN | `48302994e55a5ed4a0dfb9b577d65507eab12d343c3de48af895195b7d247b39` |

准备阶段的独立审查确认，K768 runner 仅对 K288 父版本作合同、固定 K/预算、profile说明、preflight状态及CLI的五项适配；硬件绑定、guest检查和执行/回收函数保持原字节。实际目标使用新 prefix EMU，本次资格由本次运行产生，不转授 K288 或旧 f149 的其他目标结果。

## 八个样本与同次比较

stdout 的八条 `PWS_SAMPLE` 与 [checks.json](checks.json) 逐项一致。实际顺序为 **P、N、packedP、packedN、packedN、packedP、N、P**，即 `[1,2,3,4,4,3,2,1]`。下表列出全部八个周期样本及其四组算术均值：

| 方法 | 实现 | 第一次 cycles | 第二次 cycles | 平均 cycles | 每窗 instret |
| --- | --- | ---: | ---: | ---: | ---: |
| P（1） | 原 paired16 RVV | 165,126 | 164,089 | 164,607.5 | 58,458 |
| N（2） | 原 whole8/narrow custom | 124,682 | 126,337 | 125,509.5 | 34,085 |
| packedP（3） | packed-Ws RVV | 163,372 | 162,602 | 162,987 | 58,458 |
| packedN（4） | packed-Ws custom | 108,373 | 108,924 | 108,648.5 | 34,085 |

在本次相同镜像、相同 K 和输入条件内：

- **N 自身打包收益**：`1 − 108648.5 / 125509.5 = 13.4340428414%` 周期下降。
- **P 自身打包收益**：`1 − 162987 / 164607.5 = 0.98446304%` 周期下降。
- **保留最快 RVV 对照**：packedP／packedN 为 `162987 / 108648.5 = 1.5001311569×`，对应 **33.339162% 周期下降**。

最后一个比值若按相同工作量、相同频率下的周期倒数换算，窗口吞吐增幅约为 **50.0131%**。这是对同一窗口数据的另一种数学表述，没有独立测量物理吞吐；不能写成周期减半、prefix硬件改善50%或完整应用改善50%。

**prepare位于测量窗口外。** 这些观察没有包含打包准备成本，也不代表重复采样的统计置信结论。[K288结果](../k288/RESULT.md) 中 N 自身打包周期下降约6.2076%，这里只并列记录不同 K 下各自的打包效果；不能跨 K 相除或把两种倍率合成为速度提升。

## 正确性与有限资格

本次为 **8次 warm + 8次测量，共16次完整调用、4608个输出比较**，每次输出288项。**27,648 B 是 prepared 有效载荷**，由 guest 全字节检查，不能混同为输出比较的字节数。checks记录完整活动/非活动槽、guards、CSR/FCSR及 prepared bytes 检查通过；八窗 flags 均为1、FNV均为 `f909c47ea8f72842`，窗口 instret 与固定 reference 相符。stdout包含本次镜像/reference、实际DiffTest启用、完整八窗、`PWS_PASS`及GOOD TRAP。

`cycleCnt=2844653`、`instrCnt=1593502` 是聚合运行诊断；`aggregate_is_kernel_or_application_metric=false`。不得用其代替窗口样本或完整应用指标。

`performance_qualified`、`application_performance_qualified`、`asic_ppa_qualified`、`full_retirement_window_audited`、`retired_custom_count_verified`、`full_target_memory_dump`、`target_replay_performed`、`target_negative_performed` 均保持 false。本次未做目标重放、目标负控或完整目标内存 dump；原参考链的其他验证不改变这些本次目标边界。旧 f149 的 NQ/PQ完整forward结果不转授，本次K768固定调用也不外推为完整forward收益或生产默认切换。

## 已闭合原始归档

[raw.zip](raw.zip) 为 **173,544 B**，SHA-256 `90aba0cff7e4e459475126b2c648f97b3cb6c70acda070d25e1355e873f83aea`。归档含 **17个原始 payload 文件 / 3,263,383 B**，省略文件数为0；manifest SHA为 `ee469171204c11a0dde25f0143434a2c813c3c855305bd691d1e91d69012b51a`。

[audit.json](audit.json)（972 B，SHA `2b02bb8d5b730e3034ded349a9019ce4fcbef8ba26336707f256e1fd6b357f27`）记录成员SHA/CRC通过、源库存及内容未变、457 pins再次核验，以及32395/32396两个进程组均不存在。归档阶段0新EMU运行、0新构建，不与此前这一次实际目标运行混淆。

审计绑定的 status SHA为 `d5a8d1422db42c38d086d7689bb39182dcbfa79e8eb804dfa1779a7301a0c456`，checks SHA为 `4c0f3bd2254ec4043d996635718ac6e7751d2d0d118332a70bb16fa8889e1775`；与本文引用文件一致。归档通过说明该批证据保存完整，不新增资格或独立重建能力。
