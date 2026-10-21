> James_Hotten 整合注记（2026-10-20）：以下状态与数字来自 zjhwork 9b6cf0749；原 O4 工程以 676ec7372 为起点，未包含本地 769b3b4b1 的 DIV 取消时钟修复。其离线复算只验证历史证据，当前源码面积/时序须另行重测。O2 是外部分支的后续开发建议，当前源码 O1/O2 仍默认关闭；O5/T17、G5 与人工确认尚未完成。本地整合审查另见 [记录](../../docs/o4-integration-20261020.md)。

# O4复现命令与口径

本轮仅本地评估，不切换默认、不push。生产源树与G4一致，build.sc仅新增vdotCost目标。
必须在完整香山仓库的Ubuntu22.04/amd64环境执行，Windows材料目录不能直接构建硬件。

## 1. 工具

~~~bash
# 下面各输出目录均必须不存在；不要覆盖旧证据。
python3 -B team/optimizations/o4/prepare.py /home/riscv/riscv-lab/o4-reproduce-NEW
~~~

只apt-get download并dpkg-deb -x到独立目录，无sudo和系统包安装。
Deb、Liberty、配置和许可证均由toolchain-lock.json固定SHA256；若仓库不再提供同版本，不能静默换版本。
原先实际准备的日志、ldd、可执行文件/共享库摘要另见证据tools/。工具不是随仓库分发的二进制。

当前入口在准备结束生成 `tools/contract.json`，绑定实际解析后的 Yosys/ABC/STA 路径、字节、版本、共享库及受限环境；Liberty、config 和许可证始终核对 lock 中的固定 SHA。综合和 STA 启动前后均复验该合同，四组比较及逐阶段原始回执须使用相同合同。旧工具目录缺少合同时应重新准备新工作根，不能给封存证据补写新合同。

## 2. RTL生成、综合、STA

~~~bash
cd /home/riscv/riscv-lab/zjhwork2-review-20261018/repo
O4_WORK=/home/riscv/riscv-lab/o4-reproduce-NEW
python3 -B team/optimizations/o4/elaborate.py o1 fu "$O4_WORK/o1-fu"
python3 -B team/optimizations/o4/synthesize.py "$O4_WORK/o1-fu" "$O4_WORK/o1-fu-map" --work "$O4_WORK"
python3 -B team/optimizations/o4/timing.py "$O4_WORK/o1-fu-map" "$O4_WORK/o1-fu-sta" --work "$O4_WORK"
~~~

O2将o1改o2；真实父级将fu改parent。四项顺序运行，不并发重型生成/综合。
elaborate.py明确FUSED_INPUT、HANDOFF、ELASTIC和全部trace，调用既有activate.sh；
JDK21/Mill0.12.3，firtool1.62.1路径必须实际存在。不同机器调整工具路径时保留改动和身份。
每次生成/综合/STA的实际完整命令、flags、退出码、生成文件SHA保存在输出目录。
首轮automatic语法失败、旧STA解析问题与所有原始输出保留在本次证据，不把失败混入最终合格集合。

映射为同一135单元Liberty输入，经synth -flatten -noabc、dfflibmap、固定ABC的1000ps目标和BUF_X1/5fF约束。
ABC可用单元子集由库的dont_use、功能和时序属性决定，原始日志记录跳过项。
不删除原DIV，不将ClockGate短接：三处真实门控映射CLKGATETST_X1，另有16状态转移与连接审查。
映射网表每个单元必须能在固定库找到面积，面积和须与Yosys stat独立一致。

STA显式ns/fF；typical25C/1.1V；固定库的5K_hvratio_1_1 wire-load/top模型。
周期1ns、uncertainty0.05ns、输入/输出延迟各0.1ns、输入和时钟转换0.05ns、输出5fF。
另对同网表测0.5/2ns及1/20fF；不是不同约束下重新综合。
功能testEnable=0，reset/flush/ready不加false path。
常量输出告警逐项核对；功能case-zero的3个ICG SE端点须证明直连testEnable且实际Tcl设为0。任何动态未约束、无时钟或未知工具错误拒收。
父级用canonical.py将已映射标准单元按bit ID写为简洁网表，经Yosys重读并核对完整驱动拓扑、门控、常量及每个输出位后才STA；不改逻辑。
包含r2r/i2r/r2o/i2o及ready链；父级增加Vdot关联寄存器子集和ICG E端setup检查。
报告data arrival时使用路径到达行，不能误取slack计算中重复的负到达行。

## 3. 已封存结果的离线复算

~~~bash
python3 -B -m unittest discover -s team/optimizations/o4 -p test_audit.py -v
python3 -B team/optimizations/o4/recheck.py team/optimizations/o4/evidence/20261020-cost
~~~

recheck在临时目录校验全部原始/压缩字节后重建所需文件，复算面积、接口、路径、实际Tcl约束和常量例外。
不调用Yosys/OpenSTA/EMU，不冒称重新综合或队友T17干净构建。
如需审查本次未压缩工作目录，使用audit.py /home/riscv/riscv-lab/o4-cost-20261020。
该脚本选择的是本次已完成尝试名称；全新综合后的审计须显式更新selection到新目录并记录差异，不能误用旧文件。

当前全新实验使用 `audit.py "$O4_WORK" --selection "$O4_WORK/selection.json"`，不需修改审计源码。清单必须包括四组，每组按顺序给出工作根下的综合、STA 目录名，例如：

~~~json
{"o1-fu":["o1-fu-map","o1-fu-sta"],"o2-fu":["o2-fu-map","o2-fu-sta"],"o1-parent":["o1-parent-map","o1-parent-sta"],"o2-parent":["o2-parent-map","o2-parent-sta"]}
~~~

新审计还比较四次生成的完整源码/依赖库存及原生生成工具合同。`provenance_scope` 明确标为当前合同或历史复算；历史通道仅识别原四份生成回执的固定 SHA，不能用于新结果或与新工具合同混合。归档根据实际 selection 保留合格生成文件，便携复算重新使用该选择清单。这些入口修复本身不构成新面积、时序或 T17 结果。

## 4. 结论边界

所有面积是Liberty cell area之和；所有时序是参考库、理想时钟、经验wire-load下的setup分析。
无布局布线、CTS、SPEF、OCV、实际香山工艺库和功耗活动率；不能据此宣称整核Fmax、实际面积、功耗或官方评分。
负slack表示当前1ns参考目标未满足，不影响本次“代价评估完成”与“综合/审计流程通过”的区分。
O5/T17独立复现、G5最终采用和团队人工确认仍需另行完成；正式T16报告继续后置。
