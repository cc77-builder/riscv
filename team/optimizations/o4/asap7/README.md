# ASAP7接入可行性核查

2026-10-28，James_Hotten源码基点ca86695da801bda34e4d0ad23eeda25b69dcb027。

结论：可作为新的预测工艺综合／STA平台；本轮已下载并检查库身份，尚未完成工具读取、映射、STA或本设计PPA验证。Nangate45冻结合同和结果保持原样，O1/O2默认关闭。

## 已取得的库

来源为[OpenROAD-flow-scripts固定提交](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/tree/bf3f9b344bf7d9d999f199778a722833bccbd33c/flow/platforms/asap7)，与旧平台来源提交一致，并非声称该提交为最新版本。使用7.5-track、RVT、TT、NLDM五类库：AO、OA、INVBUF、SIMPLE、SEQ。全部原文件保存于工作区外部缓存`.cache/asap7/<commit>`，仓库保存[文件大小、SHA256及参数清单](library-lock.json)。另外取得平台配置、README、latch及clockgate映射共9文件。

五份Liberty的原始许可头均为BSD-3-Clause，保留版权、许可及免责声明；不得借版权方名义背书。平台根LICENSE请求404不代表库无许可，许可直接位于库文件头。

| 参数 | 实际Liberty头部 |
| --- | --- |
| 工艺定位 | ASAP7，预测7nm FinFET参考平台，不是生产代工签核PDK |
| 阈值／角 | RVT／TT |
| 标称电压 | 0.7 V |
| 标称温度 | 25 ℃ |
| 标称process参数 | 1，无量纲模型参数，不是1nm |
| 时间单位 | 1 ps |
| 电容单位 | 1 fF |
| 漏电功率单位 | 1 pW，不代表设计已经测得功耗 |

注意：平台config.mk的TC_TEMPERATURE写0C，实际下载的五份TT库nom_temperature均为25。后续合同按Liberty真实参数记录，不照抄配置标签；不修改原始库掩盖差异。当前仅下载TT，未验证FF／SS。

## 接入差异与验收条件

1. 独立建立ASAP7合同与输出，不能覆盖旧Nangate45结果。先做库读取和小电路映射／STA冒烟，再跑生产FU及真实父级。
2. 原synthesize.py固定BUF_X1、CLKGATETST_X1和单Liberty；新平台需要多库组合、RVT单元名与DFF／latch适配。原timing.py固定5K_hvratio_1_1及门控SE规则，均不能照搬。
3. 明确ps与ns转换，ABC和STA分别核对；面积需核对Liberty与物理LEF缩放后才能跨平台报告，不直接按45/7比例外推。
4. 保留ClockGate的低电平透明锁存TE|E行为及CK/E/TE/Q连接。上游cells_clkgate_R.v的OPENROAD_CLKGATE未定义分支直接透传时钟，且包装未暴露TE；不能直接用作本设计门控替换。须核对真实ICG或等价实现、功能及E／测试端时序检查。
5. 明确互连模型。旧Nangate线负载名称不适用于新库；引脚负载估算与物理RC提取分开，不能混报。
6. 在同一ASAP7库／角／约束下比较基线与候选，再补其他角；工具旧版本兼容性必须实测，不能由OpenROAD支持ASAP7推断Yosys0.9／OpenSTA2.0.17已通过。

本轮验收仅为9文件取得、哈希记录、5库许可与标称参数检查。尚无ASAP7频率、面积、能效或1GHz达成结论；Verilator RTL功能仿真不因更换STA库自动改变周期数。此文件是平台研究记录，不另建活动开发队列。
