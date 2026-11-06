# P4-G1 生成物与禁用模式独立只读复核

审查者 /root/p4g1_fu；2026-10-28T17:08:56.271079+00:00。

**结论：这三组已生成实物支持“关闭或未设置开关时功能HDL保持”的限定结论。候选FU中pProducts已消除，保留两个32位结果寄存器。没有启动构建、仿真、综合或STA，也没有修改任何冻结材料。**

## 默认关闭的比较范围

- off-fu-equality.json：4个HDL文件清单相等，3个逐字节相同；其余仅 VDotElastic.sv 的诊断差异。
- off-parent-equality.json：56个HDL文件清单相等，54个逐字节相同；其余仅 LogPerfEndpoint.sv, VDotElastic.sv 的诊断差异。
- default-unset-equality.json：4个HDL文件清单相等，3个逐字节相同；其余仅 VDotElastic.sv 的诊断差异。

逐个回读所有真实HDL并核对记录的before/after SHA256；未只信任结果JSON中的PASS。采用比原工具更窄的独立规则重算，全部成立：

1. VDotElastic的.scala:数字变化只出现在单行$error字符串；没有修改条件、数据、寄存器、写使能或$fatal行为。独立检查要求每次替换实际位于$error诊断所在行，不能把任意数字作为行号删去。
2. LogPerfEndpoint实物只有input，没有output/inout、内部reg/wire/logic、assign、initial、force/release；唯一posedge过程恰好三个由PRINTF_COND、各自x1_bore/1/2及~reset条件保护的$fwrite，目标均为stderr 32'h80000002，没有$fatal/$finish。
3. logger三个完整guard+调用块的集合相等，只是文本排列和字符串中的JVM对象id不同；每个触发条件、类别、参数仍绑定同一条日志。外部接口及其余内容保持。诊断输出顺序不保证逐字相等，但这不是功能电路差异。

原compare_default_off.py对.scala行号的正则是全文件作用，logger匹配也不是通用SystemVerilog语义证明器；本次实物经过上述更窄人工/程序复核，实际归一化范围符合说明。未来换生成格式或增添logger行为应重新审查，不能无限复用“无output就一定无副作用”的假定。当前结论不是形式等价签核。

## 候选数据路径

实际文件：/home/riscv/riscv-lab/software-import-20261026/p4-g1-short-latency-20261029-01/p4-fu-01/rtl/VDotElastic.sv

SHA256：a0134fb1cbd3589bae58d75b1dc5efa7abe41bcf970461ea0e837244932f7072。

- 全文件不存在pProducts标识；未连接的旧乘积寄存器对象已由生成流程消除，本轮先前的未决点得到实物回答。
- 存在pResult[31:0]与rPacket_res_data[31:0]，保持P/R valid及完整ctrl/perf。
- 只有一份VDotProducts与一份VDotReduce，8路products wire逐项直接接reduce，没有复制两套乘加。
- 生成物保留旧P move优先、directR备选，enqueueP保存新包；输出仍为96位零拼接R低32，不存在算术到输出的组合穿透。
- 这些是未映射RTL结构事实，不是DFF映射数、面积、STA或功耗测量，不能将此写为节约434.112μm²实测。

## FU运行证据复核边界

已回读p4-fu-01/result.log与state.json，并用冻结正向checker离线重查：10022组完整128向量、10022次一拍响应、10021个II1间隔；接受24215、响应23545、取消600、reset丢弃70守恒。另外逐项绑定commands.json的真实退出码与9个inject日志，冻结负控checker离线重查全部通过；未新增DUT运行。

父级02正在由根Agent执行，本记录不授予其资格，不将FU通过扩大为真实父级/SQRT、全核或物理时序通过。

## 输入身份

- /home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/integration/firstdot-v2-0f/continuation/short-latency-p4/g1/tools/compare_default_off.py: 6080ef4bbf2d998bb54c10f7db1dad907589b1b6b97859d5f60451e19c4de389
- /home/riscv/riscv-lab/software-import-20261026/p4-g1-short-latency-20261029-01/off-fu-equality.json: d7983b5ea6804d702d0b1d8f824f81b5d6dc0a395abfb50ab3ed5ce6e277ea29
- /home/riscv/riscv-lab/software-import-20261026/p4-g1-short-latency-20261029-01/off-parent-equality.json: 8d1c570087a50020468f5f61b6491d9bec127efceaf21a1b98c19e820f2528c6
- /home/riscv/riscv-lab/software-import-20261026/p4-g1-short-latency-20261029-01/default-unset-equality.json: d7983b5ea6804d702d0b1d8f824f81b5d6dc0a395abfb50ab3ed5ce6e277ea29
- /home/riscv/riscv-lab/software-import-20261026/p4-g1-short-latency-20261029-01/p4-fu-01/rtl/VDotElastic.sv: a0134fb1cbd3589bae58d75b1dc5efa7abe41bcf970461ea0e837244932f7072
- /home/riscv/riscv-lab/software-import-20261026/p4-g1-short-latency-20261029-01/p4-fu-01/result.log: 356981d4a80c8fbf4288b9b8a58312bc35850d1663d57e1482aab09714a2be79
- /home/riscv/riscv-lab/software-import-20261026/p4-g1-short-latency-20261029-01/p4-fu-01/state.json: e406e48e87a0ef89a28d244117f61a458361d06e860deacfbe542065bad2b24f
