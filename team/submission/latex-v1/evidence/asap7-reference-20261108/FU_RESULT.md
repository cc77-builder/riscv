# 项目隔离环境与ASAP7初步对照

后续进展：完整VFEX4父级的双库映射、门控和五档setup复验已另行完成，见[父级结果](PARENT_RESULT.md)。本文保留先前独立FU的实验范围与数值，不将其正slack转授父级。

2026-10-28，James_Hotten整合基点e1815c073。完整原始日志、网表、RTL和运行脚本见[验收清单](../../../evidence/asap7-environment-20261028/summary.json)。未提交、未推送；生产默认O1/O2仍关闭。

## 已部署环境

本机为WSL Ubuntu-HDL，Linux x86_64，项目独立目录：

```bash
source /home/amesotten/.cache/codex-rvinno/eda-asap7-20261028-03/activate.sh
yosys -V
sta -version
```

已准备Yosys0.9、ABC1.01、OpenSTA2.0.17、Tcl8.6.14，Nangate45 typical和ASAP7 RVT/TT NLDM五库。版本、下载哈希及实际链接库见[deployment.json](../../../evidence/asap7-environment-20261028/deployment.json)。激活只影响当前shell；未修改系统包或既有仿真环境。新机器用[部署入口](deploy.py)，输出新目录，详见[部署说明](README.md)。两个平台均通过8位加法＋寄存器真实映射及STA自检。

## 当前生产FU的初步比较

不是小电路结果：使用项目CommonFuCostTop完整生产FuncUnit接口，在独立源码副本重新生成O2/H1 RTL；不是测试顶层。O2实验显式开启，O1及全部trace关闭；MinimalConfig单核、VLEN128、ROB48。421个生产源码／配置／成本入口文件与当前检出按LF归一化核对；依赖复用先前当前父级生成环境，未宣称全新机器独立复现。隔离副本的本地Git提交仅供构建资源识别，不能当项目源码提交身份。

本轮两边使用同一份生成RTL、同一工具、ABC目标1000ps、输入／输出delay均0.1ns、uncertainty0.05ns、输入／时钟transition0.05ns、输出5fF、理想1ns时钟。各用对应库BUF_X1／BUFx2_ASAP7_75t_R驱动；Nangate为1.10V/25℃，ASAP7为0.70V/25℃，比较的是两套标称工艺条件而非相同电压。为避免Nangate默认wire-load与ASAP7缺省条件混比，两份派生库均加入零互连wire-load，STA显式选择；原库未改。这与历史O4默认线负载合同不同，旧数值不直接混入本表。

| 指标 | Nangate45 typical | ASAP7 RVT/TT | 判读 |
| --- | ---: | ---: | --- |
| 标准单元数 | 8,891 | 11,617 | 库结构不同，不能以数量单独判优 |
| 标准单元面积之和（μm²） | 17,266.858 | 1,263.05082 | 少92.6851%，不是布局／整核面积 |
| 所报最坏setup路径arrival（ns） | 1.103528 | 0.825544 | 少25.1905%，端点可不同；不是整核提频比 |
| 该最坏setup路径slack（ns） | −0.181771 | +0.118721 | 在本轮约束下分别VIOLATED／MET |

面积单位并非推测：实际用到的Nangate45共45种、ASAP7共51种单元，其Liberty area逐项与固定版本1x LEF的宽×高核对，全部一致，见[面积核验](../../../evidence/asap7-environment-20261028/area-check.json)。没有按45/7节点比例缩放。ASAP7来源LEF为`asap7/lef/asap7sc7p5t_28_R_1x_220121a.lef`，Nangate为`nangate45/lef/NangateOpenCellLibrary.macro.lef`，均来自library-lock所列ORFS提交；原件封存在对照ZIP。

## 检查与证据边界

- 两边映射都没有未知／未映射单元；canonical网表重新读入并通过独立连接拓扑摘要核对，防止旧STA语法兼容处理改变连接。
- 两份STA均生成实际setup路径且无警告／错误。Yosys对Nangate八种扫描触发器的库表达式存在跳过警告，最终使用普通DFF_X1，不使用这些扫描单元；原日志保留。
- 首轮工具准备、Tcl初始化、多库模板遗漏、生成副本缺Git元数据等失败保留。初轮FU映射的默认互连结果也保留，正式初步表只取统一条件后的fu-map-02。
- 本轮没有执行全库门控等价、完整父级/DIV、hold／电气约束全集、PVT多角、布局布线、功耗或新全核DiffTest。ASAP7 FU的正slack不等于完整设计已达到1GHz，更不是流片签核。
- 未作映射前后形式等价或门级功能仿真；上述连接一致性仅验证网表格式转换。结果状态为FU_PRELIMINARY，不授整个项目PPA资格。
- 工艺映射不改变当前软件指令数、II或RTL仿真周期数；未新增应用性能提升结论。

原始[机器可读结果](../../../evidence/asap7-environment-20261028/fu-result.json)和约4MB的[生成／映射／STA证据包](../../../evidence/asap7-environment-20261028/fu-comparison.zip)可供复查。后续完整父级须先按当前ClockGate语义验证ASAP7门控替换，再补路径分类、动态未约束端点检查及物理／多角条件；不能复用上表宣称父级通过。
