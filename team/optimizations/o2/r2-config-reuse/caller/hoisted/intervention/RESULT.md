# R2-S3：单镜像前序干预结果

操作：`20261026-LiZufan001-context-intervention-0000`。2026-10-26（UTC+08:00）。
开发来源基点 `537cc2ea28e98ede1e72c1d2d7767613de9f6356`；实现提交
`1a9dd38e6a2d634aa56c07ba6b2b6f23228208ae`。执行者：@LiZufan001 / Pro 主 Agent，两个只读独立审查。

## 结论

本实验按[事前合同](CONTRACT.md)归类为 **`MIXED_PREDECESSOR_ASSOCIATION`**，但没有重现旧 h0/h1 的正式连续 origin 关联。
16 个正式固定 vdot 目标窗口均为 `NO_CONTINUOUS_ORIGIN`；A/B 的 call→leaf 首条退休间隙总和均为 2 拍。
四个 1 拍间隙恰在每个四试次块的第 3 位，随 ABBA/BAAB 顺序交替归属于 B/A。
只有两个 BAAB 块满足“A 间隙和较大”的部分条件，因此保留合同规定的 MIXED，不能把它写成已部分重现连续重定向关联。

目标正式总周期为 A **9611**、B **9613**，每臂 8 个窗口；差 2 拍仅作描述，不形成采用门槛或内核选择。
旧 `HOLD_CONTEXT_VARIATION`、R5 默认、split 原有资格、全部 RVV 回退和生产 RTL 保持原身份。
本轮增加的是有界实验和可复算的工程证据，没有新增完整应用或 ASIC PPA 收益声明。

## 1. 实际完成的工程验证

| 范围 | 结果与证据边界 |
| --- | --- |
| GNU 编译、实际 ELF/BIN | PASS。最终 build-03 的三个完整动态路径、20 项顺序表、两个前序指针、固定目标指针和全部原合格 leaf 机器码通过。目标 full 路径从 START 到 STOP 共 1730 条，实际计时指令数 1725，边界口径不同且逐窗核对。 |
| 编译控制结构 | PASS。实际反汇编确认 20×2 调用同一 take/initialize，目标表保留运行时读取，固定 A/x/workspace/y/context/measurement，全部 UART 在 40 窗及故障控制之后。原文保存在 support.zip。 |
| 真实 bit100 负控 | PASS（预期拒绝）。首个 vdot `pc=0x800014f4`、`word=0x0388000b`、vd0 的 bit100 被实时 DiffTest 拒绝；进程退出码 1，不当作正常程序 PASS。 |
| 正常恢复 | PASS。40 个完整窗口、40 次完整输出/输入/guards/CSR 判定、6 项判定故障控制、640 条 vdot 提交、正常 DiffTest/GOOD TRAP、counter/ROB/PC/word/fence 与完整 O2 协议全部闭合。 |
| 独立进程重放 | PASS。同 BIN、seed=1、不同 PID，全部 40 窗计数器、原退休组/展开前沿哈希、20 个目标的 640 条绑定事务和新关联观察相等。重放不增加独立样本数。 |
| 针对性检查 | [20 项通过](evidence/checks.json)：包括重哈希 ELF 错误顺序/重复前序/错误目标，UART 控制与失败摘要，非零退出/超时，同步修改三份回执中的 seed，负控派生观察篡改。审计前后原负控 JSON 的集合和字节哈希不变。 |
| 原文封存与隔离检出复算 | [原生审计](evidence/audit-linux.json)与[第二检出审计](evidence/audit-isolated.json)完全相同，SHA256 `f1865b6bbbea78d09ff641923b963e8cfb81dd77fae2bb3e05c48df5b912f7d6`。两者均解包后重算完整命令、输入、配置、夹具、时间顺序与原日志；不新增 EMU。 |

本轮仅 3 次真实 EMU：negative、recovery、replay，PID 为 1307、1315、1333，时间互不重叠。
运行阶段为 2026-10-26 00:18:31～00:30:46（UTC+08:00）；完整外层脚本含检查/打包于 00:31:16 结束，exit 0、cleanup_complete=true。
正常两次 validation.json 原字节 SHA 均为
`1681bb991f067578154129a1f30b4c442ea1b5bcee147a57335c90dad9b3341e`。
两个 stdout 原文哈希不同，未声称整份 stdout 字节相等；全部原件分别保留。

## 2. 控制条件与身份

一个 ELF/BIN，固定 8×32、dataset0。前序 A 为 `r4_gemv_8x32_basic_rvv`，B 为 `r4_gemv_8x32_reuse_rvv`，
目标始终是 `config_reuse_gemv_8x32_reuse_vdot`。复用原 hoisted caller 和 timer，官方代码、参考实现、旧合同/原文均未修改。
每次执行前序后，经过相同判定、保存、初始化和计时器路径再调用目标；正式前序计时结束到目标计时开始相隔 **7488～7516 拍**。
这是共同恢复路径后的干预，不能外推为两个 leaf 无中间操作的直接相邻调用。

| 身份 | 值 |
| --- | --- |
| BIN SHA256 | `62fd9eab3a5e20883b86ca6f0b44e63149c2ced09349e7dcca8d7a3a2056f470` |
| 最终 ELF SHA256 | `35dacba813950924d7b20cea16d3817be7ee7f13096a7086f12ee61c36213336` |
| T17 identity-02 SHA256 | `4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb` |
| 实际 EMU SHA256 | `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f` |
| 硬件源码 | `34bae6d4acceac939f958199dae53c14bc1f6183`，沿用固定 T17 配置 |
| 共同 caller 内 JALR | `0x80000710` / `0x000300e7` |
| 目标 / 前序 A / 前序 B 入口 | `0x800014a0` / `0x800046c0` / `0x80004af0` |
| 完整 payload.zip SHA256 | `0cb9bf31f29863f0b0485000808ad75b2f44f9c97eaf318e575eefb1fc645686` |
| 主封存清单 SHA256 | `129b7e0dbd164f38f402d006569ccbecfb35c0e57ebb659181a05d8906c5a3bd` |

源码、工具链、AM、参考模型、flash、实际命令和退出码由主归档闭合；原物理输入在运行前后验证。
离线审计重算封存身份，不把它写成重新检查所有外部实物。实际路径和操作 ID 见 [locations.json](evidence/locations.json)。

## 3. 预定正式统计

前 4 试次 ABBA 全部保留为预热，正式为 ABBA BAAB ABBA BAAB。每臂 8 次，仅下面 16 个正式目标进入分组。

| 指标 | A 前序后目标 | B 前序后目标 |
| --- | ---: | ---: |
| 周期总和 | 9611 | 9613 |
| 平均周期 | 1201.375 | 1201.625 |
| 中位数 | 1201 | 1201 |
| 周期范围 | 1201～1203 | 1201～1204 |
| 每窗计时指令 | 1725 | 1725 |
| call→leaf 间隙总和 | 2 | 2 |
| 唯一连续 origin | 0/8 | 0/8 |
| 多个连续 origin | 0/8 | 0/8 |

| 块 | 试次（0-based） | 顺序 | A/B 周期和 | A/B 间隙和 | A/B 连续 origin |
| --- | --- | --- | --- | --- | --- |
| 1 | 4～7 | ABBA | 2403 / 2405 | 0 / 1 | 0 / 0 |
| 2 | 8～11 | BAAB | 2402 / 2402 | 1 / 0 | 0 / 0 |
| 3 | 12～15 | ABBA | 2404 / 2404 | 0 / 1 | 0 / 0 |
| 4 | 16～19 | BAAB | 2402 / 2402 | 1 / 0 | 0 / 0 |

每块第 3 位（trial 6/10/14/18）的 call/leaf 首条退休为 **+942/+943**；每块第 1 位则为 **+943/+943**。
两类完整周期都为 **1201**，首 ACCEPT 都是 **+994**。所以这个 1 拍间隙来自 call 更早退休，不能解释成 leaf 延后或额外 1 拍开销。
块内第 3 位同时也是连续同臂的第二次试次，位置和近期历史没有被本计划独立分离，不能据此指定预测器、缓存或其他机制。

所有正式目标首 ACCEPT 均在 leaf 首条退休后 **51 拍**；首 ACCEPT→末 RESPONSE 包络均为 **119 拍**。
全部 20 个目标的 640 条已提交事务 ACCEPT→RESPONSE 均为 **2 拍**；这是原文观察值，合法登记时延/背压仍由冻结协议审计器判断。

### 全部目标试次

“origin”仅指本合同完整 ROB 连续性条件下的 call 关联，0 不代表窗口没有其他 redirect，也不证明间接预测命中。
坐标相对于对应 cycle-start 样本；所有目标计时指令数均为 1725。

| 试次 | 阶段 | 前序 | 目标周期 | call→leaf 间隙 | 连续 origin 数 | 首 ACCEPT |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 0 | 预热 | A | 1395 | 61 | 1 | 1096 |
| 1 | 预热 | B | 1219 | 0 | 0 | 996 |
| 2 | 预热 | B | 1208 | 0 | 0 | 1002 |
| 3 | 预热 | A | 1201 | 0 | 0 | 994 |
| 4 | 正式 | A | 1201 | 0 | 0 | 994 |
| 5 | 正式 | B | 1204 | 0 | 0 | 998 |
| 6 | 正式 | B | 1201 | 1 | 0 | 994 |
| 7 | 正式 | A | 1202 | 0 | 0 | 995 |
| 8 | 正式 | B | 1201 | 0 | 0 | 994 |
| 9 | 正式 | A | 1201 | 0 | 0 | 995 |
| 10 | 正式 | A | 1201 | 1 | 0 | 994 |
| 11 | 正式 | B | 1201 | 0 | 0 | 994 |
| 12 | 正式 | A | 1201 | 0 | 0 | 994 |
| 13 | 正式 | B | 1203 | 0 | 0 | 997 |
| 14 | 正式 | B | 1201 | 1 | 0 | 994 |
| 15 | 正式 | A | 1203 | 0 | 0 | 996 |
| 16 | 正式 | B | 1201 | 0 | 0 | 994 |
| 17 | 正式 | A | 1201 | 0 | 0 | 995 |
| 18 | 正式 | A | 1201 | 1 | 0 | 994 |
| 19 | 正式 | B | 1201 | 0 | 0 | 994 |

只有全程首个目标 trial 0 存在唯一连续 origin，redirect→call/leaf 退休间距分别为 4/65 拍。
它同时处于启动阶段且属于 A，不能区分 A 与启动、训练或缓存等历史效应，也不能混入正式统计。
随后 19 个目标均没有符合条件的 origin。未重现旧正式模式，不表示所有前序效应不存在。

## 4. 失败、修订与证据保护

- build-01 的 GNU 编译完成，但真实 ELF 校验因单元素 const 目标表被常量折叠并回收而拒绝；未启动 EMU。
  在新构建中将目标表声明为 const volatile，保留实际运行时读取，未放宽表项/路径条件。
- build-02 通过构建及 12 项检查，未运行 EMU。首次运行前复核发现“必须恰好 2 拍”不是合同门槛，
  改由既有完整协议检查合法时延和背压、保留实测直方图，并在 build-03 绑定最终审计源码。
  build-02/03 的 BIN 逐字节相同；所有实际 EMU 使用 build-03。
- 初次 native 准备的 shell 引号错误、一次长任务期间的同目录观察请求被互斥拒绝（applied=false）、构建原日志/回执均保留。
  未重放未知副作用，未为查看进度取消或重启 EMU。
- 发布前逐文件 Git blob/原始字节核对拦截了继承 text eol=lf 对 ZIP 的转换；原始 ZIP 未改动，尚未生成发布提交。
  本模块新增 *.zip binary 属性并重新暂存两包；[发布检查](evidence/publication-check.json)保留被拦截回执、修复前后身份和全部交付文件核对。此次修复不改变已执行源码、BIN 或实验结果。
- 原 caller/hoisted 检查器、官方参考程序及旧失败/成功证据原样保留。适配只发生在新合同的独立 Python 进程中。
  封存审计复用完整输入/命令/时间闭环，并在临时日志副本重算会写派生文件的负控 helper。

主[归档](evidence/qualified-v1/archive-manifest.json)为 **116 成员、29,483,020 原始字节、2,092,286 压缩字节**。
[支持清单](evidence/support-manifest.json)及 support.zip 保留前两次构建、原始辅助命令、实际反汇编、源码索引检查和相关控制层回执；不删除原现场。
独立检出直接使用固定 cd446366 Git 供体及增量 bundle，持有自己的 .git/index，没有继续串接旧临时工作树。
主 Agent 在第二检出完成原文复算，不冒充另一成员的人工验收。

## 5. 使用与复算

需要包含实现提交及既有合格对象的完整仓库、Git 和 Python 3.10+。主封存保留来源快照，但它不是独立完整 Git 检出。
下面的离线入口不会启动编译器/EMU，也不会改原运行日志：

```bash
intervention=team/optimizations/o2/r2-config-reuse/caller/hoisted/intervention
repro_root=$(mktemp -d /tmp/predecessor-audit-XXXXXXXX)
python3 -B "$intervention/intervention.py" --repo "$PWD" \
  --action audit-archive --archive "$intervention/evidence/qualified-v1" \
  --output "$repro_root/audit.json"
```

完整新构建/三进程运行入口见 [CONTRACT](CONTRACT.md)；它需要固定 T17 物理依赖可用、全新外置输出目录和四核预算。
同身份原结果已完成，不建议无新问题重复这组 EMU。若要观察长运行阶段，外层命令可保留 pipefail 并用 tee 同时留日志和输出，
本轮原执行命令仍按 support 中的原文保留；未修改 ChatPC/PPA 配置。

## 6. 路线影响

本计划收束，不因 MIXED 加顺序、样本、seed 或周期预算。旧 hoisted/fixed-weight HOLD 不由新镜像结果解除；不发布最快 RVV 或 vdot 方法。
下一软件工作应先获得真实 consumer 的形状、量化语义、A/x 生命周期与调用序列，再验证完整应用路径。
若未来另有会改变工程决策的控制流问题，需要新合同把位置、近期调用历史及恢复路径分离；当前 1 拍退休坐标本身不足以支持扩大矩阵。
本轮不改官方程序、生产 RTL、赛事材料或提交，也不新增 ASIC PPA 资格。
