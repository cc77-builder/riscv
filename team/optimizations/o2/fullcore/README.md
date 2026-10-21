> H1整合构建：`--recipe`选择编译流程，`--profile observe|cost`独立选择观察开关，`--firtool-dir`显式目录进入严格工具合同。G3需observe；cost不能冒充覆盖验证。见[整合记录](../../../docs/h1-integration-20261021.md)。

> 当前基线已封存：G3 INCOMPLETE，仅缺PARTIAL_KILL。seed=1补测未改变该结论。见[最终记录](../../../docs/o5-current-fullcore-20261021.md)。下方执行中措辞为历史阶段。

# 当前源码复验（2026-10-21）

本轮 Linux LF 和显式新输入准备见[当前复验记录](../../../docs/o5-current-fullcore-20261021.md)。3430项软件输入严格预检通过，0484候选全核构建通过，实际回归进行中；负控发现旧门禁未正确处理DiffTest批量提交PC，修复单独绑定2b6c提交并离线复核，原始判决保留。下方 G3 成绩为2026-10-19冻结版本，不代表本轮结果。

内存受限机器可显式选择 `build_fullcore.py --recipe split-v1 --output /absolute/fresh-output`。此独立schema 3合同逐阶段绑定Scala编译、6G/16m FIR展开、单线程firtool、内存生成、断言后处理及g++编译；阶段顺序、工具字节与最终RTL库存必须一致。默认仍为原direct合同，不能将已有direct失败目录续作成功。每次必须使用新的输出目录和空的checkout `build/`，先保存旧产物。软件输入选择使用 `--input-contract`，不得重写冻结证据。

若g++处理大生成文件时内存不足，可显式选择独立的 `--recipe split-clang-v2`，绑定Clang 19的驱动/动态实现、LINK/底层ld、AR及Verilator模板/运行时，其他优化/硬件参数相同。选择新profile需从新 `build/` 构建、重新绑定当前候选检查器；不能把Clang与GCC结果直接用作公平G4配对。分阶段流程降低并发峰值，不保证任意编译单元都低于固定内存上限。旧v1仅保留历史兼容；新Clang构建使用v2。

# 先前整合入口说明（2026-10-20）

当前 live 构建与运行入口使用完整编译输入/依赖库存和原生工具合同，拒绝缺少合同的历史硬件回执。旧证据继续使用封存工具；本次合并的父级验证不替代新的全核 EMU 测量。详见[James 整合与审查](../../../docs/o2-o3-integration-20261020.md)。

# O2 G3 全核验证工程入口

**G3 自动验收及严格离线重审已通过，本地保存，未推送 GitHub。** 完成时间：2026-10-19T16:18:38.167104+08:00。正式 T16 报告继续后置。

本轮用新的 O2 MinimalConfig 单核 EMU 完成原十二项回归与两项补充诊断。最终合格集合为 core-02＋supplements-02；recheck-02 从原始 stdout/stderr、退出码、输入、Git blob 和真实硬件身份重新计算，结果 O2_G3_OFFLINE_RECHECK_PASS。首轮 supplements-01/recheck-01 失败保持原样，不能混入最终合格覆盖。

## 实际结果

- 14 项作业满足各自预期：13 项正常完整通过，1 项 bit100 故障参考库被 DiffTest 精确拒绝；同镜像换回正常库后完整恢复通过。
- 原矩阵为117个唯一用例（80合法、37异常），8分片执行124次，87条合法vdot提交。原F2v独立满足七项控制覆盖，dense独立完成十二窗口并覆盖两槽并发与三事件同拍。
- 最终合格正常程序共 **5378条vdot提交**：原十二项3012，修正后诊断1158，控制补充1208；全部完整128位及身份/元数据审计通过，没有未终结FU/DIV/ROB事务。
- 新诊断检查10×512＝5120字节寄存器状态与每病例7项CSR；控制补充检查256×512＝131072字节寄存器状态及最终CSR集合。
- 实际VFEX4接受序列覆盖vdot/VIDiv/VFDiv全部9种相邻类型组合，末段各6条；12条DIV全部正常完成。日志直接绑定6条vdot的PC/word；DIV日志没有逐条动态PC/word，不扩大该项观察主张。
- 六个独立固定工作量病例共观察到735次连续1拍接受、768次2拍响应；这是本轮协议覆盖，不是公平性能或应用加速比。
- 最终主机测试79＋16＝95项通过。主机负控、真实bit100差分注入与真实RTL/全核运行分别记录，不混为一类。

## 新的全核覆盖

| 实际覆盖 | 计数（事件／周期） | 合格来源 |
| --- | ---: | --- |
| 两槽同时占用 | 2829 | control：284；dense-batch128：668；o2-diagnostic：893；o2-control-diagnostic：984 |
| 响应／移动／接受同拍 | 2133 | control：57；dense-batch128：564；o2-diagnostic：768；o2-control-diagnostic：744 |
| 满槽输出反压 | 13 | control：13 |
| P槽取消 | 37 | control：3；dense-batch128：6；o2-control-diagnostic：28 |
| R槽取消 | 29 | control：2；dense-batch128：2；o2-control-diagnostic：25 |
| 只取消一槽、另一槽幸存 | 1 | o2-control-diagnostic：1 |

实际确认的部分取消窗口为控制补充中的周期609217：P请求seq1741取消，R请求seq1740同拍响应并在609283提交，完整128位结果为0x000000000000000000000000ffffe421。须以最终合格supplements-02原始轨迹及离线复核为准；live-observer-check-10核验最终合格原流，09保留首轮同镜像独立审查，身份与来源保持区分。全核运行期reset未注入，反向年龄等G1/G2覆盖不能自动移算为本轮全核覆盖。

## 版本与复现

| 身份 | 固定值 |
| --- | --- |
| 本地工作分支 | local/o2-fullcore-20261019 |
| G1/G2基点 | 901687a478370c829865ad42cf25183938532de5 |
| 真实硬件构建源码 | b218cbc6e6b135e4ff219a902a9284a59d3c82c9 |
| core-02运行工具 | e2d9c063ac716665f4596bc95a806bd62a56d3a7 |
| supplements-02运行工具 | 079351c122e35b77c1a0e01a6c3b60d562eac1cd |
| EMU SHA-256 | ac0123280bf6c742d27a7650505bc1d91db350d1519806edfd0be9c7ea208a57 |
| ISA | vdot-s8x8-r32-v0.1，SEW8/VL8/VLEN128 |

使用O2_ELASTIC=1、O1_HANDOFF=0、T14_FUSED_INPUT=1、O2_TRACE=1、O1_TRACE=0、T12_TRACE=0、T13_TRACE=1，实际环境变量均带VDOT_前缀。默认O2开关仍为0。构建使用两编译线程、12GiB JVM，EMU单线程，最多同时两个EMU。

[观察协议](SCHEMA.md) · [工作负载及修复](WORKLOADS.md) · [复跑与离线核验](REPRODUCE.md) · [封存证据](../evidence/20261019-fullcore-validation/README.md)

工作输出：/home/riscv/riscv-lab/o2-fullcore-20261019。文档与归档工具提交不等于新硬件构建。

## 保留的失败及修正

1. build-01主动中止；build-02遇到Chisel子模块观察节点可见性错误。修复只读tap及reset观察方式，真实VFEX4 elaboration后build-03成功，功能控制未因此改动。
2. core-01首屏空R槽的原始ROB索引为63，旧检查器误将无效槽当作活跃请求。修复仅允许无效槽保存6位原值，有效请求仍严格0..47；主动中断记录保留。
3. supplements-01的第十诊断病例因SEW8的vmv.x.s提取宽度与生成器signed32常数不符，产生非法VL16并双重异常。修复仅六个AVL常数，原黄金寄存器/算术结果、前九病例与1158提交数不变；新的逐指令主机模型及实际ELF审计均检查8/32位符号扩展。
4. 同一错误日志同时出现CRITICAL ERROR、GOOD TRAP与退出码0；旧完整病例门禁已拒绝该运行。新增O2原始日志致命错误门禁，明确拒绝critical/double trap/PMA错误，保留bit100预期负控。
5. 现有原core十二项日志未重跑、未修改，由recheck-02重算；两项补充在新工具下重跑。首次集成测试桩缺新helper的失败与后续95项通过回执均保留。

## 完成边界与下一步

本轮完成G3功能、异常、控制和观察器验证；**尚无O2公平加速比、PPA或最终采用结论**。下一项是G4同镜像O1/O2公平性能比较，须使用冻结镜像、各自实测RVV及原样本规则；本次未执行。O3应用、O4时序/结构、O5/T17独立复现和两名成员人工ACK仍待完成，不代签。正式T16报告待工程结束后集中编写。

归档保存原始字节与失败历史，便携审计只复算字节及13份完整/1份故障部分轨迹，不在Windows重新执行EMU，不替代Linux输入来源和全部架构用例审计。
