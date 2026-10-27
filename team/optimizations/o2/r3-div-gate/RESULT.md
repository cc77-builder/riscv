# R3 DIV 取消关钟修复：FU／真实父级结果

> 后续状态（2026-10-25交付复核）：源码已固定为本地提交0f12df6，新EMU与14项全核/NEMU回归通过，见[全核结果](fullcore/RESULT.md)。下文保留2026-10-24局部G1/G2完成时点的范围和未测项，不能据此覆盖后续证据。未推送GitHub。

2026-10-24，@cc77-builder / Agent。**最小修复及本轮局部验证完成；尚未提交或推送 GitHub。**
基点4669c487f3024ee5fce514c37270297f99066b2a；当前工作树为O2＋H1＋DIV取消关钟候选。旧全核EMU不会因源码改动自动更新。

## 改了哪里，解决什么

唯一生产文件是 ExeUnit.scala。O2的VIDiv/VFDiv复用divBusy和所保存ROB的needFlush，在匹配取消时清理uncer_en_reg。
取消当拍依靠旧保持位仍得到真实清理边沿，下一拍无新输入时关闭；非取消redirect保留在途DIV时钟，新请求仍可唤醒。

VDot P/R占用门控、算术和32位结果存储不改，输出仍为完整128位。legacy/T14/O1分支清除条件仍是原out.fire；本轮只有其静态范围审查，没有重跑这三个模式。
原[O2合同](../CONTRACT.md)关于DIV保持原样的范围由本候选[局部合同](CONTRACT.md)明确替代，旧证据和旧合同原件保留。

新测试不仅检查摘要：C++每拍检查真实ClockGate，离线检查器从原始逐拍日志重建48个取消窗口和144个紧邻采样。假造时钟并同时修正汇总的负例仍会被拒绝。
新门禁适用于本候选和旧版红测；历史归档继续用各自冻结检查器复算，不回填新门禁后冒称历史已满足。

## 实际结果

| 验证层级 | 结果 |
| --- | --- |
| 旧H1＋新严格门禁 | 预期拒绝PASS：构建成功、真实父级仿真exit1；DIV-cancel-92，tick13330取消后第一拍触发clock错误 |
| 新候选独立FU | PASS：原22定向＋10000随机、全128位结果、反压／取消／身份／异常；4类观察值负控均实际exit1且精确检出 |
| 新候选真实VFEX4父级 | PASS：真实VDot＋VIDiv＋VFDiv＋ClockGate，13组测试、35075帧，16类观察值负控全部检出 |
| 严格取消后空闲 | 48窗口／144拍，额外脉冲0；每种DIV各24窗口／72拍 |
| ROB与复位增补 | 28组ROB定向：12杀、16幸存；DIV复位12次，其中6次与匹配取消重合，复位唯一终止 |
| 其他真空闲采样 | 全迹线1040个真空闲边沿均关钟；取消当拍清理时钟仍存在 |
| 主机检查器 | 49项PASS，包含轨迹与汇总一起篡改仍拒绝等反例 |
| 原文归档复算 | 167载荷压缩／原文SHA和库存PASS；冻结检查器再次复算完整父级及4＋16负控PASS |
| 新候选全核／NEMU、同镜像周期、面积／STA、功耗 | NOT_RUN／NOT_MEASURED，本轮不转授资格 |

父级事务守恒为13611接受＝13122响应＋426取消＋63复位丢弃，结束无在途事务。
独立FU为23311接受＝22460响应＋739取消＋112复位丢弃。

无反压的10022条父级点积仍为接受间隔1拍、首响应2拍。包含反压的完整父级运行中，VDot延迟范围2～25拍；不能把“所有响应2拍”扩大到反压场景。
35075是本地验证刺激的总时钟数，新增用例改变了刺激长度，不是应用benchmark周期，不用于计算性能提升。

旧红测打印出的0～13329共13330帧与绿测逐字节一致，包括时钟字段；旧版在下一拍才被严格门禁拒绝。取消边沿13329的整数DIV时钟存在，排除了“通过提前断钟掩盖取消”的做法。
红绿生成的VDotElastic、VIDiv、VFDivSqrt、ClockGate四个子模块SV逐字节一致，变更位于父级关钟控制。不能由此替代全核或物理时序测量。

## 来源、命令和复算

候选 ExeUnit.scala SHA256：
fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa。

[原始证据清单](evidence/20261024-local/manifest.json)按逻辑path列出全部载荷、来源路径、压缩与原文SHA；大型日志采用无损gzip。
清单中的主要逻辑路径：

- support/local-result.json：本轮汇总、来源绑定和生成子模块比较。
- runs/red-parent-01/result.log：真实旧版预期失败原文；失败构建／driver状态保留。
- runs/green-fu-01/、runs/green-parent-01/：命令、退出码、原始结果、负控、工具版本、依赖及生成文件/二进制哈希。
- support/review-tests/actual-results/audit.json：另一Agent对实际轨迹和退出码的独立只读复核。
- source-candidate/：生产改动及冻结检查器/测试源码；source-baseline/和support/candidate-source/div-cancel-gate.patch保留回退与差异。
- support/review-tests/frozen-tests.json：五份测试的冻结SHA。原runner的source.json未收录check_trace.py/test_trace.py，已用该补充清单、源码副本和运行前后逐字节核对补齐；没有修改旧runner。

原始生成RTL、编译缓存与仿真可执行文件只保留本地，未加入日常提交；归档内有生成清单及身份。黄金向量未改变，三次运行vectors.tsv哈希相同，由仓库原数据和prepare_vectors.py重建。

在仓库根离线复算本轮归档（不会执行RTL）：

~~~bash
python3 -B team/optimizations/o2/r3-div-gate/audit_evidence.py \
  --archive team/optimizations/o2/r3-div-gate/evidence/20261024-local \
  --output /tmp/r3-div-gate-new-audit.json
~~~

输出必须是新的归档外文件。[最终复算回执](evidence/archive-replay-02.json)与[执行命令](evidence/archive-replay-02-command.json)已保留。
第一次归档复算因新适配器引用FU检查器的函数名错误退出，修正为既有check接口后通过；[失败回执](evidence/archive-replay-01-command.json)及当时脚本保留，原始RTL／测试／归档没有因此改变。

本地实际运行位置和命令在证据内；重跑硬件前先按[合同](CONTRACT.md)确认旧版红测与候选的源码身份，使用全新输出目录，不能把本地旧EMU当成候选。

## 当前边界与下一步

本轮达到的是候选G1/G2局部通过，旧O2＋H1仍保留为全核已验证基线。当前源码尚未完成新的全核、NEMU差分或周期不退化验收，不能直接标为最终采用。

DIV复位沿用TE=1原约定；VDot保留原TE=0覆盖，不宣称已经覆盖DIV所有TE=0复位。VFDiv同封装还包含sqrt，本轮动态用例只覆盖既有DIV路径，sqrt仅有静态取消通路审查。
4＋16负控是C++观察值损坏，非RTL故障注入。

下一阶段应固定本候选新身份，构建新全核EMU并做受影响正常／异常／控制／NEMU差分；通过后再做同镜像周期不退化和同工具同约束面积／STA，关注新增取消控制路径。先不改默认入口，不干扰已有T17冻结运行，也不把门控活动改善表述为加速比或功耗数字。
