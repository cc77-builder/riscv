# R5/G5 firstdot V2：实际交付与验证

操作 `20261026-LiZufan001-r5-firstdot-0056`，执行者 @LiZufan001 / Pro主Agent。
来源基点 `a9455e08c06a39be24957d71ef1c905b666a1bc3`；本页与源码、清单、
原始证据同一交付提交，承载提交由Git历史定位。使用入口为
[完整使用与回退](../../FIRSTDOT_STABLE.md)，验收依据为
[冻结V2合同](../../FIRSTDOT_STABLE_CONTRACT.md)。

## 结果与范围

**`R5_FIRSTDOT_STABLE_SOURCE_PACKAGE_PASS`。** 2026-10-26
01:08:41～01:09:20（UTC+08:00）在独立WSL原生目录真实执行；
交付归档于01:15:47完成全部成员恢复与原字节比较。完整结果见
[result.json](result.json)，封存及路径定位见[delivery.json](delivery.json)。

| 实际检查 | 结果 |
| --- | --- |
| 冻结firstdot性能矩阵和普通C原文 | 同一次C审计内部完整重算矩阵一次；与原合格报告相等。覆盖384正式窗、192重放比较、48不同C case及96正常调用 |
| 实际GNU库构建 | 完整27,416B `gemv.o`等于原合格对象；一个archive成员、16原firstdot函数，静态库原字节亦与既有库相同 |
| 默认／显式0／显式1 | 每种模式8个别名，完整caller对象与显式调用对象相等，可重定位link对象相等，无未解析符号 |
| 配置和版本 | 7种非法配置拒绝，宏展开0/1及重复include通过；V1→V2拒绝，V2→V1保持V2 |
| 实质负控 | 重哈希后的错误RVV均值、错误别名目标、错误完整对象分别被选择推导／GNU对象对照／archive成员检查拒绝 |
| 头和库配对 | 缺第二头文件时编译拒绝；错用V1库时`ld -r`退出0但真实未解析符号被检出 |
| 搬移与回退 | 只搬移V2库和双头后，实际示例编译与可重定位链接逐字节相等；冻结V1验证器在新输出目录PASS |
| 文档代码 | 从使用说明抽取唯一C代码块，在搬移SDK上按默认与强制RVV分别真实GNU编译／链接，无未解析符号 |
| 源码保护 | 21项固定输入的SHA256前后相同；原firstdot源码与V1执行输入未修改 |

GNU工具为RISC-V GCC 11.4.0、binutils 2.38，Make 4.3，路径和可执行文件
SHA256均在result中。本轮总CPU预算≤4，正式验证约束到4个可用CPU，
独立GNU模式最多2个worker，库构建均为`-j1`。Pro主Agent实现，
另两名子Agent只读审查路线、协作与最终源码/证据；最终独立审查实核了
5个新增执行输入与报告SHA相同，未替代主Agent验收。

本轮**新增EMU/NEMU均为0**。运行资格来自firstdot原33次性能进程和
3次普通C进程，绑定原T17硬件/参考身份；本轮重新审计原文并证明源别名
及完整对象等价。未新增最终应用ELF运行、应用周期、人工ACK或ASIC PPA。
新应用的链接布局、调用计划、打包和生命周期变化仍需按影响实际验证。

## 选择依据

V2前三个整块默认firstdot/reuse/vdot，K13默认firstdot/reuse/RVV；
8个源码别名不增加ELF符号或运行时分派。完整选择由原矩阵所有8候选/形状、
每候选12正式窗推导，详见
[机器可读清单](../../FIRSTDOT_STABLE_MANIFEST.json)。

4×8包内firstdot/RVV历史均值187.75拍，公平比较保留同轮最快合格S1/RVV的
187.50拍。两者在清单和验证器中分别记录；负控实际将包内均值改成187.50并
重新计算文件哈希，语义比较仍正确拒绝。K13默认RVV187拍与旧V1默认聚合
并列，未把旧vdot219.75拍当作旧默认夸大迁移收益。其他历史数据与适用
窗口见[使用说明的选择依据](../../FIRSTDOT_STABLE.md#4-为什么选择firstdot)。

## 字节身份与归档

| 对象 | SHA256 |
| --- | --- |
| V2验证器 | `2a3ced33e2b3aa7fa131507a220f5aa56fff65cc0e71d20bec0e8674763073ca` |
| V2输入清单 | `8feaa3a6e19c7bc5dcc77ccf0d262523d4f1d014c7c591ef123ed2084f0f5b40` |
| 完整合格库对象 | `b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af` |
| V2静态库 | `9e12de07d363a2627d7d33cff401da257c30487d59b3a3f7029bb3a262fbd33e` |
| 原始交付ZIP | `be5c4be275d5469487b2b933e84d6e6cc3f2686ef8c74d45429587b76025e0c9` |

归档[verification.zip](verification.zip)为360,701字节，426成员，
解压共1,341,806字节；每项成员长度和SHA见
[archive-manifest.json](archive-manifest.json)。全部成员实际写入新的
`sealed-recovery-01`目录，并与原输出逐字节比较通过。`.gitattributes`
将ZIP标为binary，避免文本换行过滤破坏归档。

归档库存：

- `verify-01/`：正式完整原文复算、GNU命令/退出码/stdout/stderr、
  三模式调用对象、负控输入/输出、V1回退、搬移SDK和完整result/state。
- `delivery-01/`：从文档抽取的真实C示例、两种配置的GNU命令与对象。
- `preparation/`：独立原生检出与增量bundle验证日志、准备/传输脚本和
  ChatPC返回的结构化回执。未复制旧仓库或巨大的Git对象供体。

原生检出直接借用固定cd446366自包含供体，并把后继bundle导入本轮自己的
`.git/index`；未延长旧七层alternate链，也未写固定供体、旧工作树/index。
完整个人路径只保存在delivery记录与原始命令中。

准备阶段的两次Shell引用/参数传递失败均已核实exit1和
`cleanup_complete=true`；后改为文件化Python参数调用。首次封存因文档
传输JSON缺SHA字段被检查器拒绝，发生在任何目标目录/文档写入前；
原失败脚本、输入和回执保留，修正为新版本后封存通过。
这些不是功能/EMU失败，也没有把失败记录替换成成功。

## 复算与使用

完整资格重建入口：

```bash
python3 -B "$REPO/team/optimizations/o2/r2-select/verify_firstdot_stable.py" \
  --repo "$REPO" --output /path/to/new-v2-verification
```

`REPO`应为含历史Git对象和冻结证据的完整Linux/WSL原生检出；输出必须
是源码外新目录。此命令真实重建GNU产物和重审原文，不启动EMU。
实际SDK构建、C ABI、版本选择和V1回退详见
[使用入口](../../FIRSTDOT_STABLE.md)。归档中的负控输入用于验证拒错，
不得作为生产库或调用者采用。
