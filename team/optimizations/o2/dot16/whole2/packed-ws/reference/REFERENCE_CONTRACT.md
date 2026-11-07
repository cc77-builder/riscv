# Packed-Ws 八窗口参考合同 v2

合同 `r3-packed-ws-eight-window-reference-v2`。这是已闭合九窗口参考实验的明确新版本，为后续小规模目标比较减少重复标量执行成本。原 `reference-01` 和原 ELF、源码、全部原始证据保持不变。本合同仍只构建及运行独立 NEMU，不启动目标 EMU，不授予正式性能或完整应用资格。

## 固定前提与改变

先绑定原九窗口 result：142366B、SHA256 `cec287cff44cdda1070539515a3d426fd81e6a4025e0a84ac6bcb632ef7f1f5a`。它实际完成两种 K、五臂、十个 reference case，含标量原 oracle 对四个汇编函数的完整值/精确 flags 交叉、两个负例和独立回放。其全部 source snapshots 和 generated inputs 仍须保持原 SHA。

唯一 guest 行为改变是去掉方法0的 warm/measurement，八个窗口顺序为 `[1,2,3,4,4,3,2,1]`，分别是原 P、原 N、packed P、packed N 及其反序。每窗仍先 warm 一次再测一次，正常合计16次完整调用。samples 对象由9×8×8B改为8×8×8B，即512B；report仍为512B。成功协议相应改为 `samples=8 full_comparisons=16`。方法0实现与原 oracle 源仍保留，不能把本轮未执行的标量窗口记成新目标结果。

`main.c`只做4处精确可逆替换；controller从已闭合31329B版本派生，保留完整子进程命令、信号、截止和回收实现。`source-derivation.json`记录完整 before/after 锚点、SHA及字节级逆向复原。两组K固定几何不变：M288、K288/768、GS32、VLEN128、RV64/lp64d。相同P/N及packedP/N完整函数体仍分别与GNU阶段固定SHA/长度一致，旧新汇编仍分对象编译。

## 数据与检查

K288继续使用固定提取manifest `13d05882e6f1876993a6e6b63c8d5041c1067bdfb73ba061adf41f91d66f2bd1`，cases为normal-0/1/2/fullmin。原fullmin保留原Ws和dataset0 Xs。严格host oracle实际flags须重得已交叉的字典：normal-0=1、normal-1=1、normal-2=0、fullmin=1；不猜测所有样本flags都相同。K768继续使用原闭合normal/edge fixtures和flags。

每次调用仍比较全部1152B输出、活动槽完整128B与gold、非活动槽完整A5、16B前后guards、VL/vtype/vstart/vcsr以及完整FCSR。prepared仍为实际PREPARE输出，与独立原Ws字节置换期望逐字节比较，64B前后guards，K288总10496B、K768总27776B。准备和首尾检查在计数窗外，不能把准备成本视为零或把本地收益当完整应用收益。

负控仍固定方法2原N，在首次实测结束后翻输出byte1148的一位。必须code91、warm=1、提交样本0、全部512B samples为0；它验证共享比较器，不是packed-N专属指令负控。正常末方法1与负例方法2终态仍是原槽gold、新槽全A5。

原完整 W2 validator 在此前两个可逆扩展之外，只把两处正常report计数9改为8。dump大小512B及8元素ORDER共同约束全部八样本，正常样本完整顺序、非零counter差、精确flags及gold hash仍逐个核验。1400B register、32768B CSR、完整15个内存对象/fixture、trap/异常与完全相同的独立replay判据不变；不把NEMU dump声称为目标EMU dump。

## 执行、输出与资格

沿用10例：K288 negative、normal-0、replay、normal-1、normal-2、fullmin；K768 negative、normal、replay、edge。仍是21条串行命令，CPU1、绝对nice5、make -j1，默认总预算1200s，reference每例100M步/180s且受外层210s和总剩余预算限制，单文件32MiB。所有子进程必须reaped且group absent；不自动重放失败或超时。

全部输出写fresh独立目录，原九窗口输入、硬件、AM、NEMU、checker和工具只读。源清单含main、flags_host、controller、此合同和完整派生记录。最终归档采用result中的完整snapshots/generated_inputs，初始inputs快照不替代后续新增输入清单。

成功状态仅为 `PACKED_WS_EIGHT_WINDOWS_REFERENCE_PASS`。`target_emu_runs=0`、`target_runtime_qualified=false`、`performance_qualified=false`、`application_performance_qualified=false`保持。参考的cycle/instret是参考执行计数，不是香山实测。目标小试另有固定K/预算/原EMU身份的合同；是否继续K768由K288收益和剩余资源决定，不自动启动两种长仿真。
