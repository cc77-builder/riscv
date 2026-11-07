# 完整状态比较器：8 字整数批处理原型

## 状态与范围

2026-11-07 UTC，`r3-first-forward-compare-batch8-prototype-v1` 已完成 **宿主 C 语义检查和真实 RISC-V GNU 编译/反汇编复核**。没有运行该原型的 NEMU、香山 EMU 或周期测试；`target_runtime_qualified=false`、`application_performance_qualified=false`。

这是团队自有 `main.c/complete_compare()` 的窗外工程效率候选。原官方程序、NEMU/DiffTest、现行四臂 `r3-dot16-first-forward-v1` 及其冻结输入均未改变。新 ELF 只供这次静态检查，仍保留原报告标识，**不能作为原 v1 合同的可运行替代镜像**。现行四臂仍按自己的原 operation 接续。

权威实现为 [compare_batch8.py](compare_batch8.py)，本文件集中记录合同、结果和采用边界；不另建通用比较框架。

## 输入和精确变换

输入为四臂实际构建的 `build-01/source/main.c`，6571 B、SHA256 `339f00055b30cd1b033f10617a43eb55a0c5006e0e78c58c726a7620167ec116`。原完整函数体517 B、SHA256 `15b26a473323dcb6c53887fbcaebfa535da067c25f9804998cc2f2ecb5a51e10`。派生器先核整个输入和唯一函数体，再作可逆的局部替换；反向变换必须还原原文件每个字节。

比较长度固定为3,691,424 B，即461,428个64位字。新循环对八对完整64位字计算：

```text
difference = OR(k=0..7, actual[i+k] XOR gold[i+k])
```

它保持全部64位。对稳定输入，结果为零当且仅当八对字全部相同；不同字的错误不会像跨字 XOR 归约那样互相抵消。两侧读取总字节数没有减少。

完整批次为57,678个64 B，随后仍有4字/32 B。循环只在剩余至少八字时读取完整批次；遇到非零差异，保留该批起始索引，进入原逐字/逐字节定位逻辑。因此原首错 `reject(94, byte)` 与原逐字不一致 `reject(95, word_start)` 保留。若批次已判断非零、标量复扫却未找到任何差异，额外以95在首个可疑批起点失败，不能写成功长度。原 `alias_word` 的 `may_alias`、只读输入、完整长度和成功报告位置保留。

未改变模型/gold、guard、TLS/errno、FCSR、负例的byte152476、调用及计时源代码。候选 body SHA256 为 `43d7c16ebf060af7bbc5689757e0b5810bf3163ff560b2bd88252d40f9bd6766`；派生整文件为 `d47110df167dddd73baeb853a3cfc4ea98b01e0fec2856364b52d63a112fa522`。

## 已执行验证

### 宿主 C

`compare-batch8-host-02` 实际编译和执行均exit0，compile/run stderr均为空，1661个用例通过。每例都运行原函数和候选函数，并分别与独立逐字节oracle的首错位置或全等结果比较。

覆盖包括160 B小缓冲区每字节每bit翻转；完整3,691,424 B缓冲区的批边界、最后32 B、原byte152476负例、高32位/bit63；多个字相同XOR掩码；跨批首错和固定种子的双错误样本。两侧逻辑末端后立即为不可读guard page；启用AddressSanitizer和UndefinedBehaviorSanitizer。该结果只证明宿主C语义及本组边界，不替代RISC-V执行。

第一次 `compare-batch8-host-01` 编译成功，但执行因托管宿主ptrace环境下LeakSanitizer不支持而失败；原stderr和失败回执保留，没有写成PASS。第二次关闭LeakSanitizer，保留地址/未定义行为检查与显式guard page；通过时间约0.982秒，不作为性能测量。

测试时派生器SHA为 `458b7dacdfd9a7ff3d6e8d81a88cfdd216e93274bdbbf56dc7fa7a47f6dd4c81`。之后只加强宿主回执条件：`UBSAN_OPTIONS=halt_on_error=1`，且要求run stderr为空；当前派生器SHA为 `2f7f612d50f46cd68f73aae1722a50c0ed4175a17b28a4eb323a640f0a70e81b`。已核测试C与候选函数体字节均未变，旧成功运行stderr也确为空；没有声称重新执行了测试。生成的测试C SHA为 `53f0f5e784706e8fa3620f6005a7aa71cde781bad3e52957a5ce69d43244b529`。

### 真实 GNU

复用已冻结构建的实际GCC和LD命令，仅替换新的main源/object/ELF/map输出路径，逐项验证命令反向恢复。原objects、链接输入和工具只读；派生、编译、链接、反汇编和符号读取五条命令均exit0并确认reaped及process group absent。CPU1、nice5、单线程，未启动guest。

外层operation `49cbde030e5643f0cccfca5cec8a79c1.abcb171fba2ea9249f4c0ee8b34b9676`，开始 `2026-11-07T12:28:07.3430983Z`，exit0，cleanup_complete=true。结束前全部已记录输入仍匹配；后续宿主回执加固没有改写这份测试快照。

| 产物 | SHA256 |
| --- | --- |
| 静态原型ELF | `de5bec611102d93d37794b3aac488f8cdb556618cb56716f14515e8e9af11216` |
| 新main.o | `78601980dd8e20f2b513ee2cb849986eeea6a8dc4fa32b99351fca377805988c` |
| 原基线完整main反汇编 | `bb86f6875936a5f801f70a9f8d695ed016eb4c44c0082870eaec946a536dd5bc` |

原基线ELF也重新只读核为 `5ba0cd0756a16f38c2747c625bf8fb53d5ba4c9ba9b2bbf222c146df4859b959`；只读反汇编operation `49cbde030e5643f0cccfca5cec8a79c1.b2d4e06ef6f65b1a17406f4e85da7179` exit0、cleanup_complete=true，原输入未修改。

## 实际机器码观察

原相等循环每64位字8条架构指令。新 `0x80002a00` 热路径对两侧各读取偏移0、8、16、24、32、40、48、56；全部为64位ld，8个XOR经7个OR合并，无批内spill、call或store。

| 每个相等64 B批次 | 条数 |
| --- | ---: |
| 两侧八字ld | 16 |
| XOR / OR | 8 / 7 |
| 保存索引、索引加八、差异分支 | 3 |
| 两个指针加64、批次结束分支 | 3 |
| 合计 | 37 |

相对原64条/64 B，完整批次静态架构指令数减少42.1875%。57,678批对应2,134,086条；在正常全等执行假设下，从比较器入口 `0x800029cc` 到长度写入 `0x80002ad4` 的控制流共2,134,169条，包括入口、尾部及编译器交错的一次UART标志读取。这些是反汇编推导，**不是已测instret、周期或wall time**。

终点分别为461,424/461,428字，最后四字覆盖完整。实际GNU对第一个尾部gold字使用8次lbu加移位/OR重组，其余三字走标量ld；这是一项一次性尾部开销，范围正确。主函数仍有144 B栈帧，但没有逐批栈访问。

四次计数读取位于 `0x800028d0/28dc/28f0/28fc`，比较器在其后。源码只改窗外比较函数，然而重新链接也改变了ELF布局，因此不得用新旧镜像的应用周期作直接性能分母。较长OR依赖链、读取量不变等因素仍可能限制实际收益。

## 证据与复现

| 归档 | 内容 | SHA256 |
| --- | --- | --- |
| [compare-batch8-host-20261107.zip](compare-batch8-host-20261107.zip) | 17成员：两次host原始源、程序、命令、stdout/stderr、成功结果、测试时派生器和清单；失败一并保留 | `8709f6e5955970481dbf42e064b12cab0d24cab0698304c03686105d2a9ef0e1` |
| [compare-batch8-gnu-20261107.zip](compare-batch8-gnu-20261107.zip) | 24成员：测试时派生器、原/新函数和main、GNU命令/输入、main.o、map、全部日志、原main反汇编和清单 | `63b3c15403fe759a0d0db2416aef95359e6432d72b8ed730e67c99e13d60d7a2` |

GNU原件与完整原型ELF保留于：

```text
/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/first-forward-compare-batch8-20261107-main
```

归档未复制约75 MB的完整ELF，保留其原路径和SHA；原对象/工具依赖在inputs与commands中明确。旧Windows生成器的SHA是构建当时输入；可复现副本为归档中的 `compare_batch8.py`，不能要求后续已加固的工作文件仍为旧SHA。两份zip均逐成员读回核SHA并通过CRC检查。

有限复现入口为：

```bash
python3 -B compare_batch8.py screen --output /absolute/new/host-screen
python3 -B compare_batch8.py derive --input /absolute/frozen/main.c --output /absolute/new/source
```

GNU命令以归档的实际 `commands.json` 为准；输入改动须新身份，不能覆盖旧结果。

## 采用决策

保留这个窄原型，暂停手写RVV比较器及通用框架探索。当前不追加昂贵EMU队列，也不把本原型验证升级为现行四臂的验收门槛。

若以后本就需要新的完整forward候选，应先给新比较器独立的合同/镜像身份，再沿原完整reference正例和byte152476负例核实完整状态、guard、TLS/FCSR及真实退出；所有被比较臂共同采用同一新ELF。只有实际观察到验证成本改善后，才报告目标或主机效率收益。应用性能继续由应用计时窗口及同镜像较快合格RVV对照决定。
