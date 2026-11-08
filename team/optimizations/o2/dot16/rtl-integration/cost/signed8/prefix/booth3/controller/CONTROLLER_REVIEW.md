# Booth3控制器：独立有限审查

## 结论

**未发现阻止本次单点本地FU/cost筛查的控制器静态问题。** 新三行P输出、三/六输入R模块和实际新SAT已分别绑定；旧两/四输入SAT不转授。父控制器的绝对截止修正保持。这里只审控制器、派生及证据边界，源码数学与checker正确性由并行审查负责；未运行EDA、构建、仿真或访问本机，也未修改候选源。

审查身份：

| 文件 | 字节 | SHA256 |
| --- | ---: | --- |
| controller/booth3.py | 49573 | `bcde44c580003a0a99e18cc30a2795a9c7a9af08ed56ef38a8f740987ec8241f` |
| derive_controller.py | 7750 | `960d1824fa90b531b2bfae35b95927f948bb8045e664e25b9f5891c1d731d572` |
| controller/controller-derivation.json | 10984 | `265632793b2b1f74df2f78994ba375241db5a99173df6cf7601478ded0df1bf1` |
| controller/BOOTH_CONTRACT.md | 5814 | `805b354eb7001c1c2c5bf36ca00bf3e54138b37b6eff4f427068a278d9f2b8ca` |

## 1. 完整派生与变化范围

在内存中逐项执行24个唯一替换，正向精确生成当前49,573 B控制器；逆序执行则精确恢复父Booth2控制器46,330 B / `6681fce5cc739206c5922e025d76ae0a75334d57502b089902b5a7a72f05ea60`。重新生成的统一diff与controller.diff完全一致，未仅采用JSON的exact_inverse自述。

source-derivation的16项编辑确为datapath7项、wrapper9项。分别逆还原当前源码，完整恢复原prefix：datapath `1d02d8a3…`、wrapper `912c1a03…`；当前候选SHA分别为`880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680`和`1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238`。当前source-derivation为18,751 B / `202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876`，与控制器常量一致。

新增wrapper编辑只扩展每半第三行、rowWords遍历、Finish输入数和接受边的row2保存。原时钟/reset、valid槽协议、accept/move、kill/flush、ctrl/perf及架构输出扩展没有新增编辑；R算术变化明确披露，未宣称旧完整Finish源码不变。

## 2. 新P3 checker与实际wrapper绑定

控制器固定的新checker为17,469 B / `c0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587`。它从快照执行并读取本次实际生成CSA，要求BOOTH3专用PASS、完整模块解析、all_inputs_equivalent、实际RTL/验证器SHA，以及272 FA、19 HA、七层、7168 recode cases、256 byte decompositions和既定偏置。四套新cost/FU消费者的CSA须逐字相同，结构证明不复用旧记录。

`wrapper_binding()`要求每个CSA恰有两个输入和三个输出共五个唯一端口，包含row2；feature0完整声明3×19位P行，feature1为6×20位。所有低半保存表达式逐行检查低19/完整20，高半dot8固定保存(2^19,0,0)。Finish实例的全部3/6输入直接连接对应保存行，禁止缺行、重复端口、旧符号扩展或后置模式修正。唯一R写表达式仍为illegal-zero或prefix结果。

这结合完整源码逆派生、实际非数据赋值比较及新的FU测试构成当前验证路径；不冒称整个wrapper的顺序SAT证明。

## 3. 必须重新证明实际三/六输入R模块

新result.prefix_miters初始化为空，并明确prefix_miters_reused=false。旧2/4输入SAT原件仍作为已冻结历史输入保存，但没有复制到新结果列表。新cost/FU对应Finish字节必须相同；已删除与旧Finish字节相同的要求。

随后固定执行(19位,3输入)和(20位,6输入)两项新证明：

- 实际DUT头部须具有精确模块名、全部3/6个同宽输入及结果口。
- 独立Gold为所有未受约束输入的同宽模和；Gate逐端口实例化本次实际生成的Finish，证明脚本直接读取该实际DUT。
- Yosys使用miter/flatten及`-prove trigger 0`，solver上限30秒、命令上限60秒。不存在输入assume或只限制到旧行表示的条件。
- 每项必须rc0、恰有一次明确SUCCESS、无反例及ERROR；失败/超时立即标FAILED并抛出，不重试。两项全部PASS的门禁位于任何FU lint/build/run及cost mapping之前。

gold、gate、prove脚本和成功日志进入generated pins，并记录实际DUT SHA；失败日志也保留SHA与失败原因。原乘法SAT的UNKNOWN不变，不与这两项新R证明混合。

## 4. 预算、输入与输出保持闭合

通过AST比较，当前command、check、interrupt与已修正父版本完全一致：总1200秒从run入口开始；每个命令在Popen前固定min(总截止,当前时间+限额)，check核总截止及信号；成功结果落盘后再check，晚到超时/信号重写FAILED。两项新SAT沿用同一command和deadline，没有另起预算。错误路径仍按固定helper回收独立进程组并记录reaped/group_absent。

输出必须不存在且与全部指定输入树互不包含；控制器限定CPU2、nice5、make-j1。候选/基板/工具/原FU输入、原SAT历史文件及新快照的绑定保持；成功前复核原输入、快照、生成class、RTL/资源表、实际证明材料与原classpath。实际启动器的资源占用核对仍由主端回执说明，本审查不据静态源码推定本机状态。

新的FU和cost尚须由本次运行取得。parent/fullcore/application/core-cost资格默认false、new_core_builds/new_core_runs为0，生产默认不变。面积和五类路径按原条件记录实际DFF与slack，未将预计位数增长或局部完成标志当作1ns/PPA通过。

本报告没有增加新的验收要求，也不授予任何未实际执行的PASS。控制器中的真实生成、checker、新R SAT、FU及cost门禁决定后续实际结果。
