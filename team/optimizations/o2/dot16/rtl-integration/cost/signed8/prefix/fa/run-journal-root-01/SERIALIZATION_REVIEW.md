# FA 网表序列化续接：独立静态审查

## 结论

**该适配足够窄，当前 canonical graph 定义足以核对本次序列化前后的完整终端连接保持。** 未发现必须增加映射、RTL/FU/core验证或完整网表等价器的理由。原 FAILED、原文件及原失败日志必须继续保留；新续接只产生独立 serialization-01 结果。

已审 `fa_serialization.py`：13,071 B / SHA256 `82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a`；合同2,047 B / SHA `00db43f49848377d5c01bcec6eb008faf79a96e3956317cfdc0e045de60b1d1c`。本报告另明确下述外层来源冻结是完整方案的一部分。此为静态审查，不是实际序列化或STA成功证明。

## 原失败的适用解释

实际读取了已封存 `actual-failed/result.json`，其SHA为 `476d893ba770a9faf323a61b7f1403c5999f4f00569b68d95b4620ff9b61a473`。两个子进程均退出0、reaped且group absent，控制器仍因 `ValueError('incomplete STA')` 正确保留FAILED。

`sta-feature1.log` 明确记录OpenSTA2.0.17对原mapped.v五处concat-LHS的语法错误；日志同时仍打印完成标记。这说明必须继续使用“无Error＋完整报告”门，而不能仅依靠退出0或完成标记。

独立的 `mapped-fa-bindings.json` 为269 B / SHA `7a51e45bdcdce2b66a9213ddee2745130ae0e58334fcdc37311f28081049f1c8`，记录954FA、4770pin及dut.products/dut.highProducts各477通过。此次失败不是该FA绑定失败，不能把未成立的STA结果当成FA算术反例或时序结论。

## circuit() 的完整性

当前比较包含：

- 全部top port的名字、方向、位宽、offset、upto和signed；每个端口的逐位位置进入连接终端，端序改变不能由临时bit编号重排掩盖。
- 全部cell的名字、type、parameters、完整port方向和每个port宽度；每个cell引脚的逐位位置进入终端。
- 每个电网的完整终端列表，包含重复连接对应的不同bit位置；电网列表按内容排序，不使用原始整数bit ID。0/1/x/z四种常量分别保留标签，不与浮空wire混淆。
- 拒绝memory/process与net init属性。没有电路终端的纯别名不影响本次已映射标准单元连接图；源位置/显示属性和内部别名不作为电路身份。

对于此固定、已flatten、以同一Liberty解释的门级电路，这些项目确定了带单元身份的完整终端连接分区。相等检查不会因为重新编号而误判差异，也不会把短接、断接、引脚互换、常量变化或单元替换当作单纯改名。它证明的是该输入JSON与导出后回读电路图一致，**不是原RTL到完整mapped netlist的形式等价证明**。

## 实际命令路径没有重映射

代码中的序列化脚本仅为 `read_json → splitnets → write_json → write_verilog -noattr -norename`，没有-ports，也没有proc/synth/opt/ABC/dfflibmap。之后的新进程按原Liberty执行read_verilog、hierarchy -check、check -assert和write_json。

原JSON先与split JSON比较，再与新Verilog回读JSON比较，两个门都在STA前。代码还在回读前检查实际文本是否仍有concat-LHS；不应预设splitnets一定消除所有可能的port别名形式，但若本次仍残留，已有拒绝分支会停止，不需要扩大到拆top port或追加自定义Verilog重写。

TCL全路径替换同时使read_verilog指向serialization-01的新网表和新报告目录；反向替换恢复完整旧TCL。原约束只按既有top port和寄存器集合选择对象，不依赖被split的内部别名。954FA、1678DFF、完整top接口、同库面积及五类路径检查继续保留，STA的原Error拒绝逻辑没有放宽。

## 来源冻结说明

控制器初版在运行时读取并记录原mapped.json的SHA，而不是在EXPECTED中写死。为固定“此次已完成的那一份JSON”，主端已选择更小的外层冻结：

- 固定实际native plan-only文件：12,887 B，SHA256 `38967267758c4a76589b0af1bb3d73708d425a5628a15db7461f1a207e5613cb`。
- 启动器先核整个plan SHA，再逐一核其全部original_pins，包含确切mapped.json、两份续接源、原输入及工具/库，然后才exec同一冻结控制器。
- 原目录与源目录声明只读；控制器在末尾继续核全部输入，结果记录原JSON SHA及canonical graph SHA。

这能固定本次续接输入，不需要修改已审源码或创建重复版本。以上plan身份与启动安排由主端提供；**本报告写入时尚未读取实际launcher源码，待其到达只核上述顺序及执行范围。** 不应把外层冻结描述为控制器单独已经内置的硬编码pin。

## 取舍与边界

现方案复用安装版本的官方序列化pass，并用已定义连接图校验补上身份链，比临时手写concat赋值拆分器更易限定范围。没有必要依赖该版本未提供的-simple-lhs，也不建议为同一映射点加入新的PPA参数或重跑ABC。

若图不等、concat-LHS残留或STA仍报错，保持新续接FAILED并停止，原FAILED继续保留。若通过，只报告原映射点的格式兼容续接与实际成本/STA；`mapped_netlist_equivalence_tested=false`、无FU/core/应用资格转授及默认实现不变仍适用。

本审查只读云端已封存证据和当前代码，并写此报告；没有执行EDA、访问PC/Pro或修改实现/失败结果。


## 实际启动器与执行状态补充（2026-11-08）

**外层来源冻结已完成实际源码核对；本次格式续接为FAILED，未进入STA。** 本节完成上文“launcher尚未读取”的待核项；既有静态结论和原文保持，不回写旧运行结果。

实际读取 `serialization-launch.py`：2,389 B，SHA256 `7140ae1bbe8094802cd522ab264584dcd42e2362b4d1c81af55ecd8e677bac42`。启动顺序符合约定：

1. 核两份固定续接源的长度与完整SHA；
2. 核PLAN_ONLY.json的12,887 B及完整SHA `38967267758c4a76589b0af1bb3d73708d425a5628a15db7461f1a207e5613cb`，并检查PLAN_ONLY状态和目标目录；
3. 遍历 `original_pins` 的全部项目逐一核SHA，没有筛选或跳过其中的mapped.json；
4. 核新输出不存在以及有限资源条件，打印实际绑定后，通过 `os.execv` 执行 `/usr/bin/python3 -B …/input-serial-01/fa_serialization.py --execute`。

启动stdout明确记录原mapped.json SHA：`7117718b7d29be886b948d70d7a0486a472f341e1ffcf1bec827728b8cc8f53c`。因此，上文建议的确切原JSON来源绑定已由固定plan及实际启动器落实，不需要修改已审控制器。

实际host回执为 `serialization-host.json`：2,585 B，SHA `fc783489cf20b582c88ede40f208d401dd6acbc8aec71136dd1a827a758f1684`；operation为 `0250d6044ba18f5fd71831ae3131d2ce.46e412ef7746dba2dc2a9aac5344635e`。其started_at为 `2026-11-08T03:51:12.2331027Z`，updated_at为 `2026-11-08T03:51:15.2947376Z`；记录duration_ms=3017、exit_code=1、cleanup_complete=true、cancelled=false、timed_out=false。

stderr将拒绝点定位到原控制器第159行：`serialized Verilog changed complete circuit graph`。按所审控制器的顺序并结合主端终态说明，实际序列化文本已无concat-LHS、split.json图比较通过；reparsed.json完整图比较不等，故在STA调用之前按原门禁停止。没有重新运行ABC或映射，也没有因失败放宽门禁、重跑或把结果写为成功。旧local-01的FAILED及此次serialization-01失败均继续保留。

本次只核launcher顺序和已有回执，不重新计算连接图，不判断具体图差异原因；该有限诊断已由主端另行委派。连接图不等意味着此次续接尚未满足原合同，不能据此前静态计划可行的意见授予成功或时序资格。此审查至此完成。
