# signed8 候选的 R 结果位宽实验 v1

合同：`dot16-signed8-result-width-local-v1`。这是隔离的源码候选，创建时尚未运行；实际状态由独立输出 result.json 和原始命令回执说明。生产代码、常驻缓存和已冻结目标实验不改动。

## 规格与唯一功能表示变化

复用已经通过真实源生成、无约束 product SAT、两态完整 FU 和真实父模块验证的 signed8 datapath，SHA `50522c0cd2700f7f852872049533bc31f79ce811ad2ed53da2c1d333cece45e2`。本次只改变 VDotElastic 的 R 级数据表示：feature0 保存19位，feature1 保存20位；输出时符号扩展到低32位，高96位仍为零。原 wrapper SHA `63911b937a526b97ddaa67e34526fd19bbd2fa2801eadfda10ae6c2fa4b9fe9e`，候选 SHA `70dcc27381d3e7226eeff333c943d35b982ec1fdd37b75b680060a13aaf94e2a`。source-derivation.json 的五个精确文本变更必须逆向恢复实际原件全部字节。

保持原时钟和复位、P/R两槽、完整控制与perf身份、ready/valid、redirect/kill、接收/移动使能、非法指令及dot8兼容判定。当前生成实现为上升沿时钟和同步高有效valid复位；数据与metadata仍不增加复位。无阻塞时E0接收、E1移动、E2最早响应，II=1；接口保持原完整128位数据输出和全部控制端口。输入向量字节序、操作码、VL/SEW/LMUL等参数不变。

原feature0的写入已经是19位sum的符号扩展或非法零；feature1已经是20位sum的符号扩展或非法零。这对任意P中的SInt16项成立，且包含dot8高半区清零。新表示保存该低19/20位，输出重建原32位。第一次move后，两表示完全相等；后续hold保存相等关系，move重新建立关系。R有效只能来自move，reset/kill只撤销资格，因此未写入的内部数据不产生有效响应。这里是精确表达式与使能状态的论证，不宣称已经完成全FU顺序形式化证明。

## 实际验证和复用边界

1. 从原独立cost生成合同和固定完整classpath编译两份真实Scala覆盖源；分别实际生成cost/FU × feature0/1共四套消费者，不能直接用手改SV授予源码资格。
2. 四套实际 Products、SignedByteProduct、Reduce须与 signed8 local-03逐字节一致，才复用该次无约束product SAT。local-03 result原件SHA `19f90c867022ba2259b83fb2600bb56ef7066eda54023cead03c6e35bf23b7d7`；相同算术不重复证明。生成VDotElastic须实际具有19/20位rPacket_res_data，其余公共top和Reduce保持原字节。
3. 运行原两态完整FU C++/vectors、原coverage门和identity/wen/high/cancel观测负控；不修改检查器或向量。负控是原观察分类，不冒称完整RTL故障覆盖。实际lint、build、正例、负例和分类都须结束并回收。
4. 同完整FU边界、同Nangate45库、同ABC约束、同名义1ns STA模板进行一次匹配测量；保留全部五类路径及失败slack。公共端口须与原common-FU一致；DFF应只减少feature0的13位、feature1的12位。记录相对旧宽乘法基线和已合格signed8基线的差异，不把源级位数当作映射面积结果。
5. 所有输入/快照/缓存/类路径及生成文件前后核验，完整过程仅一个CPU、absolute nice5、单worker、默认总1200秒且最大1800秒，原有限子命令和进程组回收保持。输出目录必须全新；失败原件保留，不扩预算或重放。

该实验不产生新的整核构建、EMU、完整应用性能、parent或core PPA资格。只有实际完成的层级可以标为通过；若采用这项表示变化，父模块和后续适用整核验证需用该候选实际执行。当前完整N/P目标继续使用其原硬件与原operation，不能转移本实验资格。面积目标20000和名义1ns都以真实测量判断，不能从少量寄存位预先宣布达成。
