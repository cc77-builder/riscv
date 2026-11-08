# SP1 最终20项验收矩阵

按原20项统计；其余19项复用已固定来源，第19项由原镜像完整检查与M4定点补测共同收口。

|序号|用例|结果|依据记录|
|---|---|---|---|
|1|performance-d0-s00|PASS|62|
|2|performance-d0-s01|PASS|51|
|3|performance-d0-s02|PASS|69|
|4|performance-d0-s03|PASS|70|
|5|performance-d1-s00|PASS|64|
|6|performance-d1-s01|PASS|58|
|7|performance-d1-s02|PASS|69|
|8|performance-d1-s03|PASS|70|
|9|performance-d2-s00|PASS|66|
|10|performance-d2-s01|PASS|60|
|11|performance-d2-s02|PASS|69|
|12|performance-d2-s03|PASS|70|
|13|c8-performance-d0|PASS|53|
|14|c8-performance-d1|PASS|54|
|15|c8-performance-d2|PASS|55|
|16|c8-sdk-final-functional-48calls|PASS|88|
|17|legacy-control|PASS|80|
|18|o2-all-pairs|PASS|80|
|19|o2-control|PASS|120|
|20|timed-div-sqrt|PASS|102|

第19项原镜像16组、256次试验、1208次custom退休、131072字节寄存器检查保持；补测41调用、77次退休填补S0/S1。未借用0f槽位覆盖，未删除原检查。原1500秒合同HOLD保留，本轮使用执行前冻结的新独立预算。

第16项C48以记录88新合同验收为准。CSR/ABI证明边界保持原合同：目标自检、DiffTest及静态叶函数审计，不能泛称每条普通指令或每个CSR均有独立观测。
