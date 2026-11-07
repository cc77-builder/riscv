# dot16 whole2：实际 GNU ELF 与完整函数主机筛选通过

> **2026-11-07 K768 接续：** N/P 的 M=288、K=768 派生已完成新 GNU 几何与真实 W2/末组边界参考资格，见本文末节及 [w2-np/REFERENCE_CONTRACT.md](w2-np/REFERENCE_CONTRACT.md)。尚无 K768 新目标周期或完整应用资格。

> **2026-11-07 接续：** 同一 412B whole2 函数已完成[固定 Q288 整核筛选](q288-consumer/RESULT.md)，29 次 Q / 8,352 个输出、DiffTest、判错控制及 GOOD TRAP 通过；相对同镜像 plain dot16 两窗平均少 15.7665% 周期，相对同镜像 P 少 35.2684%。已选择 whole2 进入[新的 P/PQ/D/DQ 完整 first-forward](../first-forward/RESULT.md)；后者参考已通过，目标运行仍在进行，尚无完整应用周期结论。下文保留 2026-11-06 主机合同的历史边界。
>
> 新增[whole8 源级候选](WHOLE8_CONTRACT.md)与[窄派生器](whole8.py)：仅合并两批连续 W 加载，源级账本为 43→30 条核心指令、21,090→16,878 条完整函数动态指令。实际生成及可逆/字节映射检查已完成，保留源 SHA 为 `df2983a2…`、新组合源 SHA 为 `c0c5a99561500894453b1fd04d310195ab0f0cea29f89dbf1a394b3be410fdce`。目前 **SOURCE_DERIVED_UNBUILT**，没有 GNU、参考、整核或性能资格，不替换当前运行的 whole2。

> **2026-11-07 N 组合候选：** whole8+narrow 已完成新的[完整 Q288 整核筛选](NARROW_Q288_RESULT.md)：同镜像 W=28,430/28,015、N=26,385/26,165 cycles，两序均改善，均值少 **6.9005%**；29Q/8,352 输出、满幅、CSR/guards、五项共享判错控制、DiffTest/GOOD TRAP、85 pins 和回收通过。保留 N 为后续完整 forward 候选，先等已在途四臂的完整结果；没有新的应用性能或完整退休资格，也没有将 N 的通过赋给独立 whole8-only H。原始[87 成员证据](narrow-evidence-v1/raw.zip)与新代码、合同均保留。

2026-11-06 UTC；合同 [CONTRACT.md](CONTRACT.md) 为 `r3-dot16-whole2-host-v1`；工作包 `20261106-LiZufan001-paired16-rvv-pro6`，范围登记及回读见 [Issue #2 / 6674886539](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6674886539)。

**结论：独立符号 `q288_dot16_whole2` 首次真实 GNU/主机筛选通过。整数核心43条，新完整函数412B；八组实际ELF路径均执行21090条指令，完整Y、128B最终slots、FP顺序、足迹和ABI/CSR通过。三个合法机器字反例均正常返回后由完整Y比较拒绝；五个保留函数与独立构建的旧集合逐字节相同。当前没有新目标核、DiffTest、周期或完整应用性能资格，不修改稳定默认入口。**

这是供数软件改进，沿用已有dot16算术合同，未新增ISA操作，也未修改旧dot16生成器/筛选器、P/G/TA/FR冻结函数、硬件、NEMU或官方程序。候选已交主端和consumer负责人用于后续决策；本次没有启动新EMU。

## 实际执行与完整身份

Windows源工作树在运行前后均为 `zufan / c981529dc6e493fb7deee8429b9ce05fd197497b`。将18个明确依赖复制为独立薄输入视图，在常驻WSL原生runs目录执行；不是新克隆或完整检出。Windows源、薄视图和筛选内source-snapshot字节前后保持一致。

唯一执行操作 `d9b025210fdcd3c1fd06c2f645cfad75.17a0ae02d841883a8617e133072aa8cc`：Windows回执开始 `2026-11-06T02:20:09.048593Z`、结束 `02:20:12.1447588Z`，持续3057毫秒，`exit_code=0 / cleanup_complete=true`、未超时/未取消。Linux子进程为 `02:20:09.594745–02:20:11.922714Z`，2.327961秒；direct child已回收、process group已不存在。两套记录原样保留，墙钟只描述验证成本。

使用CPU affinity `[2]`，所有编译与主机检查串行。GNU RISC-V工具的参数为 `-march=rv64gv -mabi=lp64d -mno-relax`，链接使用静态、无启动库、禁用relax、固定text地址；实际编译器SHA为 `0c54895c55568be5b5fee49e2426abcc8fb05ca2c121ca5685dea2cbc24a1c13`。独立C oracle使用原辅助器的严格FP参数及RNE设置。

| 项目 | SHA-256 |
| --- | --- |
| 本轮 [generate.py](generate.py) | `553459635da18319493f1027329da23e0aeb94ee560861e34abdc512a295f9e9` |
| 本轮 [screen.py](screen.py) | `c5d12b55a7b835d605d175977ebb24ecf9c05b92ce101edb9096f7db3bdd2f7f` |
| 冻结合同 | `25dcbe2a65474c74fc55f49a14bcc3e0ec37551b84b2e0fe4496e98d633640ac` |
| 实际GNU ELF，10712B | `0ea09990c578faccab105afd1942d66a3f6f9905876b2e5462ae7e0f7a0e2adc` |
| `q288_dot16_whole2`完整412B函数 | `b2b5b7fa44ecf9646a7c07fdaf971df8fad6430aec58161ffc3e2c3332d934a6` |
| 实际43条整数核心，172B | `c1bcdde5973fe83db38abf028123200d254b6bce82c62e79b283bc09a8a7aabd` |
| 独立构建的旧集合ELF | `8dca229c81b13adab7191341c0be46d355663ef386c85651227c33b5dc3881d3` |
| 原始主机结果，[host-result.json](host-result.json)，10895B | `ec013889562ac589db9ae3e94288d54db82a8e5e524670922c44f986e5635001` |

实际运行根为 `/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-whole2-20261106-pro6`。`inputs-01/source` 保留18文件完整依赖，`host-01` 保留生成汇编、两份GNU ELF/对象、原/新机器字证书、C oracle、八组检查、三个损坏ELF及命令日志。新符号是软件候选，运行它的目标必须另行具备已验证的dot16支持。

## 为什么能减少供数，又保持结果

原plain16每组用18次16B向量加载及17条地址addi；whole2将相邻两半一次装入两个寄存器，改为9次32B加载及8条地址addi。**每组输入仍是256B W和32B X，总字节数没有减少。** X固定于v14/v15；四行W批次固定于v16…v23，完成该批次两半点积后才覆盖下一批。v8…v13中的原FP状态保持。

整数核心不推进X指针，原后缀保持 `a1+=32`，每tile九组覆盖完整288B X。低/高半的精确整数和先合并，随后完全沿用原逐组FP转换、两次乘法和累加；不跨组重排，不引入FMA。整数核心之后的45条原后缀只改变两处相对分支位移，逻辑目标仍为函数偏移60/44。

### RVV依据与适用前提

[官方RVV规范§30.7.9](https://docs.riscv.org/reference/isa/v20240411/unpriv/v-st-ext.html)规定whole-register操作的有效长度由NFIELDS、VLEN、EEW决定，独立于当前vl/vtype。NFIELDS=2、VLEN=128、EEW=8给出32B；偶数基寄存器和低地址到低寄存器的映射与本候选一致。该目标的最小SEW为8，因此此EEW8形式不新增16B/32B内存对齐要求。这里的证书只覆盖完整可读32B、vstart=0正常路径，不提供异常中途恢复资格。

两次配置分别为VL16/e8/m1/TA/MU和VL4/e32/m1/TU/MU。high96为零来自自定义dot16的完整结果合同以及四个整数lane的相加，**不来自TA策略**；标准agnostic尾部可保留旧值或写全1，见同一规范§30.3.4.3。新模型显式检查TA/MU，未误用旧paired16的TU条件。

## 实际ELF证书与正向检查

证书直接解释GNU链接后的机器字，独立于生成器的寄存器映射，跟踪每次whole2写入的两个寄存器和全部字节来源。八行输出各自恰含32个 `(row,k,k)` 乘积，high96为空/零；每组256B W、32B X各读一次，原FP寄存器不写，X核心/后缀净步长为0/+32。

独立旧集合与新集合中五个完整函数的机器字完全相同，之后原dot16机器字证书也通过：

| 保留函数 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `q288_fused_vdot` | 800 | `9a155c33b9f27ca04d68ab3e0d883d6819876db6dc1c5d6f55ba9a3faa435648` |
| `q288_phased_vdot` | 764 | `78893b4754e0e1f5b0d2599d29e9ad50ff675cae088797ea7207eedfd5b78d9b` |
| `q288_tail_vdot` | 764 | `b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3` |
| `q288_fused_rvv4` | 592 | `66a12c0ec3cb7c0d1cdceadf04e4c658607438d83a2a958892100422343117ab` |
| `q288_dot16_vdot` | 484 | `ee92c07b7803b04c5340ba4412cb36326b8f5ed42fbf0677fc2f210bcd6711bb` |

八组数值检查为原dataset调用0→1→0→2、min/min、max/max、min/max和zero-W。重复调用复用packed W对象及前次向量状态；后四组W/X字节偏移分别为(12,12)、(15,3)、(2,10)、(5,1)。每组完整288个Y逐位匹配独立row-major C/Python oracle，并检查最终八个完整128位slots；严格FMA差异见证保持。

每组均完成324次完整整数核心、21090条入口到ret的函数指令、5184条dot16、2592条vadd和2916条whole2 load。FP元素操作为2592次转换、5184次乘法和2592次加法。输入/context保持，逐字节读写足迹、普通返回、标量/浮点ABI及最终向量CSR通过；栈使用为零。模型未提供fflags、非有限FP、非RNE或完整处理器异常资格。

## 三个实际机器字反例

三者均保持ELF大小并实际执行到普通ret，动态函数指令数仍为21090；证书拒绝后，数值检查再次以 `whole2 actual full-Q bitwise output` 拒绝。解码异常、越界或未返回不能计为通过。

| 反例 | 实际字位置（函数内，零起始） | 语义错误 |
| --- | --- | --- |
| `wrong-x-high-half` | 29 | 首个高半dot16将X源v15误改v14 |
| `premature-second-w-batch` | 29…40 | 第二批四行W提前覆盖第一批尚未消费的高半W |
| `old-plus16-x-footer` | 74 | 原+32后缀误改为+16，使后续组X重叠 |

三个实际损坏ELF、完整输出SHA及符号/数值拒绝原因均在归档 `files/host-01/controls/`；没有增加其他反例或扩大主线验收。

## 指令计数与下一项决策

| 边界 | 既有plain16固定合同 | 本轮whole2实际ELF |
| --- | ---: | ---: |
| 整数核心架构指令 | 61 | 43 |
| 每组循环架构指令 | 82 | 64 |
| 完整函数静态字节 | 484 | 412 |
| 完整函数主机模型路径的动态架构指令 | 26922 | 21090 |

完整函数减少5832条架构指令；旧plain16计数来自其已冻结模型合同，本次没有为此重跑旧完整数值筛选。新函数仍比GS32v2的20123条完整函数指令多967条；不能拿GS32旧计时区20134条与新函数直接比较。

此前静态账本给whole2核心63个声明微操作：两条vset按4个、九条whole2加载含基址操作按27个、八条地址addi按8个、十六条拟议dot16按16个、八条vadd按8个。这是固定T17源码配置及dot16单微操作假设下的账本；既有T17不因此获得dot16支持。vset的rd=x0声明nop也包含在内，不代表全部实际占用执行端口。它不模拟RF仲裁、加载拆流、依赖等待、缓存、频率或目标周期。

已取得的结果足以把这个更省供数的plain16候选交给consumer和目标验证，不足以决定硬件路线获胜。下一项能改变决策的证据是：绑定相同完整函数/消费者、实际dot16硬件与reference身份之后，相对更快合格RVV的公平应用比较；包括接口/布局和必要计时边界。由主端安排，当前没有新增EMU、默认切换或新性能承诺。

## 原始证据与复现

[host-01-evidence.zip](host-01-evidence.zip) 已封存79个原始文件，共620357B，另含manifest与原执行回执；压缩文件170498B，SHA `4e1167fc4b1c635c56ef104201489c9f24e85af624ff0f0c73461e4b8fcbe05b`。所有归档原始成员及源文件重新计算SHA一致。归档操作 `d9b025210fdcd3c1fd06c2f645cfad75.bc77dcf10f417c43dde1602299ad4f8f` 于02:23:42.060–02:23:44.545Z完成，2420毫秒、exit0/cleanup=true；只做保存和字节核验，没有重跑GNU或模型。

解压后使用包内完整薄视图及新的外部输出目录；不要直接从另一个scratch目录运行screen.py再指定不包含该脚本的repo。`screen.py`会将实际使用源按repo相对路径保存，并拒绝复用已有输出。

```bash
whole2_snapshot=/path/to/extracted/files/inputs-01/source
whole2_output=/path/to/fresh-external-output
taskset -c 2 python3 -B \
  "$whole2_snapshot/team/optimizations/o2/dot16/whole2/screen.py" \
  --repo "$whole2_snapshot" --output "$whole2_output"
```

本叶六文件供主端统一集成；冻结输入和原运行证据保持。提交/推送状态以实际Git和协调Issue为准，本报告不将文件保存等同发布完成。

## 2026-11-07 K768 N/P：真实 GNU 几何与固定 W2 参考资格通过

**结论：已把 N（whole8+narrow）和合格 RVV P 从 K288 窄派生到
M=288、K=768、GS=32，并完成新的真实 GNU 构建及四例 NEMU 参考验证。**
这两份函数可以作为后续完整 consumer 的明确候选；本次没有新目标核运行，
不把 Q288 周期、NEMU 指令计数或本次墙钟当作 K768/完整应用加速。

权威入口为 [w2-np/raw.zip](w2-np/raw.zip) 内
`raw/reference-01/result.json`，SHA256
`7d46f70b4cb105bd468577815e21c97fe9fa249fb447eeec3c977d9236e3b8c1`；
状态 `K768_N_P_REAL_FIXTURE_AND_EDGE_REFERENCE_PASS`。
派生和验证分别使用 [W2_NP_CONTRACT.md](w2-np/W2_NP_CONTRACT.md)、
[REFERENCE_CONTRACT.md](w2-np/REFERENCE_CONTRACT.md)。

### 实现与适用边界

复用原56B context、VLEN128、RV64/lp64d、FS/VS开启与RNE。
W采用[36][24][8][32] packed布局（221184B），行尺度[288][24]，
X为768个signed byte及24个FP32尺度。完整输出为288个FP32值；
最后八个slots均比较完整128bit。每组保留原INT32转换、乘Ws、乘Xs、
左折叠累加顺序，无FMA、无跨组重排。返回vl=8、vtype=0、vstart=0、
固定profile的vcsr=7，不宣称任意vcsr保持。

派生只将原整函数中的36/9/252几何常量改为96/24/672，并重命名独立符号。
实际GNU ELF对比覆盖完整函数，而不是源码中某个循环片段：

| 实际函数 | 字节 | 允许变化的机器字索引（从0计数） | 新完整函数SHA256 |
|---|---:|---|---|
| N：`q768_dot16_whole8_narrow` | 312 | 9、14、56 | `b4a0e512feafd3ae8ea7e4531e13e1a23b12f97d80b3b007be6c52c3bdea56be` |
| P：`q768_paired16_rvv` | 1096 | 3、25、34、104、135、140、252 | `26f972751fb9882f92118ac30b98f2d0b4d1df9225be5d9cd136e7ed5c4629d3` |

P的保护分支、快速路径和完整fallback全部在上述比较内。其余机器字完全相同，
源级逆变换恢复原字节；父函数先与各自已冻结Q288实际ELF核验。
新参考镜像再次汇编并核对相同的两个完整函数SHA、RX段、无动态/TLS段、
完整ELF/BIN含BSS一致性、栈/堆范围、实际好/坏trap及四个带fence计数读点。

### 复用真实 fixture 的四个独立参考进程

原 W2 build-06 的 position2/layer5 数据、八份fixture和gold保持冻结；
不重跑三位置host exporter。原权威matmul及AM库/构建规则只读。
团队main只做四处可逆改动：声明N/P及expected-flags、method1/2路由改为P/N、
两处flags比较绑定所选fixture的精确期望。保持`0xa5`输出/slots初始化、
完整比较器、guards、CSR、原九调用顺序、两控制字和byte1148负控。

完整复用原W2 `validate` 函数，逆变换检查通过。只增加第八份
expected-flags fixture的不可变比较，并将flags字面值替换为固定record值；
没有接受“0或1均可”，也没有让DUT输出选择gold。各例独立镜像由host选择
完整数据集合，每个镜像与唯一确定的完整字节构造对应。

| 用例 | 实际结果 | 边界 |
|---|---|---|
| negative | 预期BAD/code91，adapter exit2；精确output byte1148差异、实际拒绝PC | 精确负控，非任意非零退出 |
| normal | GOOD/code0；完整输出/slots/guards/CSR/fixture通过，FCSR=1 | 真实W2数据，X没有−128，覆盖P快速路径 |
| replay | 新进程再次通过，完整validation对象与normal完全相同 | 独立重复身份与结果 |
| edge | GOOD/code0；FCSR精确为0，全部输出/slots逐字节通过 | 最后GS32组的两个−128配对 |

edge其余X/W为零，只令X[751]、X[767]及W[287][751]、W[287][767]为−128，
全部尺度为精确+1.0。最后输出应为32768.0（FP32 `0x47000000`），
最后slot低32位为32768（`0x00008000`），高96位及其余输出/slots全零。
完整packed重新按原公式生成，仅偏移221167/221183非零。该用例针对旧9组
保护若遗漏末组时的两项int16归约溢出，不能外推为所有输入的证明。
`0xa5`初始化防止大量零gold掩盖漏写。

原adapter、参考库、1400B ABI及现有硬件身份全部固定，新运行没有替换旧参考
合同的SHA来借用资格。各例检查完整寄存器/CSR转储、actual trap PC及无异常；
normal/replay各执行4430650条退休指令，edge为4720922，负控为86498。
这些是NEMU该验证程序的指令计数，不是香山周期或应用性能。

### 实际执行、归档和接续

GNU operation `.df141f7a5b1b778de1ac9a42d89bf24b` 于
15:51:47.896–15:51:50.959Z完成，8条命令全exit0，11个原输入pins稳定。
参考operation `.4c764ad5d34d3e1fb69f3045d88ff283` 于
16:33:35.033–16:33:52.833Z完成，outer17.724s/exit0/cleanup true。
两者共同前缀为 `49cbde030e5643f0cccfca5cec8a79c1`。
参考的7条命令均按预期闭合：负控exit2，其余exit0；无超时、取消或遗留组。
内层参考结束时间为16:33:52.779Z；采用CPU1/nice5、单worker、
总1200s及各命令既定有限预算，没有修改在途四臂的输入或执行方式。

- 参考ELF SHA：`8d7c7b95b45d4e555912f914ee5d72482123ff4e10cd534112681824939dc86c`。
- 参考BIN：484692B，SHA `fce72a766a5c681bca09111da54f7b8f04c50608838a0257711a6b0e8c855eb3`。
- GNU组合源 `w2_np.S`：8361B，SHA `fbe3a93f642ec3468da92ae776e1b547c29c527d4dffc30456191b437d1272c5`，另存为 [w2_np.S](w2-np/w2_np.S)，并保存在归档与参考source快照。
- `raw.zip`：3198360B，SHA `d70f90f41f8bf9a467404ee685b2ad360a0696c939f04ae10a26cb18bcba1a1d`。
  178成员（177原始/审计文件，共10305807原始字节，另含manifest），
  全部CRC、长度、SHA和原件字节逐一核验；165个合并输入/生成pins再次检查，
  15个原子进程组均不存在。只省略可重建reference对象/依赖中间件；
  原始运行目录不删改。
- [derive_w2.py](w2-np/derive_w2.py) 与
  [qualify_np.py](w2-np/qualify_np.py) 保留实际执行版本及合同。
  在新隔离输出中按各自 `--help` 与固定输入身份复现；
  不直接覆盖冻结gnu-01/reference-01目录。

**后续关键接入点：** 当前完整consumer的非FR K768分支仍会走旧TA；
只换Q288 N函数不会自动让W2使用N/P。应在新的明确身份下修改这一选择，
保留合格RVV P对照，并重新核实际ELF路由和完整state参考。
本结果授予上述两个K768实现及两套fixture的参考资格，
`target_runtime_qualified`、`performance_qualified`、
`application_performance_qualified`仍为false，新的EMU次数为0。

## 2026-11-07：N/P packed-Ws 完整源码、GNU 与两代参考通过；K288 目标小试已启动

**已完成四个独立 packed-Ws 函数及其位保持准备函数，取得 K288/K768 的真实 GNU 与固定参考资格。** 目标是减少原跨行尺度读取的访存开销，实际周期收益尚待本节末尾的 K288 小试。这里没有完整 consumer 接入、准备成本摊销或正式应用性能结论；原生产路由保持。

### 实现、接口与完整机器体

新增 [packed.S](packed-ws/packed.S)、[packed_ws.h](packed-ws/packed_ws.h) 与 [pack.c](packed-ws/pack.c)，合同见 [CONTRACT.md](packed-ws/CONTRACT.md)。固定 RV64/lp64d、VLEN128、M288、GS32、RNE，K 为288或768。原 row-major context 和入口继续保留；新尺度对象使用不同类型，大小为10,368/27,648B、64B对齐，新 context 仍56B、字段偏移0/8/16/24/32/40/48，slot为16B且16B对齐。不存在把旧尺度指针强转为新布局的兼容承诺。

令 `G=K/32`，完整映射为：

```text
packed[(tile*G + group)*8 + lane] = bits(Ws[(tile*8 + lane)*G + group])
```

准备函数通过字符访问复制每项原始4B表示，不求值浮点，不预乘尺度；覆盖全部填充行。必须在首次使用前及每次权重尺度更新后重新准备。原 `INT32→FP32→乘Ws→乘Xs→按组左折叠相加` 次序逐字保留，没有FMA或重新结合。P的完整−128保护和fallback均保留。

每个N只修改三个机器字：`vlse32.v`改为`vle32.v`、组步进4→32、tile额外步进252/672→0；每个P在fast和fallback各做同样三项。保留不再需要的stride初始化和零加法，以固定函数长度并核查其余全部字节。新旧函数必须分别汇编成对象再链接，内部 `.L` 标签没有改名，不能直接把新旧源码拼入同一个 `.S`。

实际 GNU 构建先将四个父函数与完整 N/P forward ELF `62a73b9d16cea43ad03eec3ec09b27edfab7da90ce895d33baa72bf9d84723c4` 对齐，再独立构造允许改变的编码，并比较整个函数及GNU符号长度：

| 新函数 | 字节 | 允许改变的机器字索引（从0计） | 完整新函数 SHA256 |
|---|---:|---|---|
| K288 N | 312 | 43、50、56 | `4d53878105559d9bbc9d4b221f22a8bfcbd919507ceda0620d80feab81e368db` |
| K288 P | 1096 | 91、98、104、239、246、252 | `7c14ed922c8d914f0fde2013531aef2fc40729115be96a5301114589a59e3214` |
| K768 N | 312 | 43、50、56 | `99db793d14f8691a20444523402814569d287b71f493d5d432459252219fcf34` |
| K768 P | 1096 | 91、98、104、239、246、252 | `2e0c4920dfd8777c74f3a7aceaa3b748428065e3da0c90baf24193a14f20a816` |

GNU阶段10条命令均exit0，实际RV64编译通过typed ABI断言；原输入、快照和完整机器体保持身份。另有独立host位复制检查：实际未改的pack.c以ASan/UBSan及poisoned guards验证10组位模式，全部47,520 words / 190,080B一致。首次LeakSanitizer因ptrace环境限制失败；第二次仅关闭leak检测，ASan/UBSan保留。两次完整源码、binary、退出与日志均收入 [cloud-reviews.zip](packed-ws/cloud-reviews.zip)，不把host测试当作RV64运行。

### 两代固定参考及缩减理由

第一代九窗口依次包含scalar、原P/N和packedP/N，完整标量交叉已通过。K288 fixture从原冻结narrow ELF的完整符号提取，并保留三套normal与fullmin；K768复用已冻结W2 normal/edge。提取阶段只验证binary32数值，flags明确未解决；后续独立host flags与RISC-V参考交叉后，才为每个fixture绑定唯一精确值：K288 normal-0/1/fullmin为1、normal-2为0，K768 normal为1、edge为0。

第一代正常guest参考退休数为K288 2,032,427、K768 5,057,095，其中scalar测量窗分别636,520/1,731,532条。以两倍窗口估计其warm+measurement，约占62.64%/68.48%；这只是参考指令成本估算，不是目标周期比例。为避免小试重复支付已完成的scalar交叉，第二代main仅四处可逆修改：samples长度9→8、顺序去掉scalar、循环9→8、成功计数9/18→8/16。第二代重新构建独立ELF并完整运行同一十例参考，没有沿用旧ELF的PASS。

第二代固定顺序 `[P,N,packedP,packedN,packedN,packedP,N,P]`，每个测量窗前先warm；16次完整调用分别检查全部288个输出、完整活动/非活动slots、guards、向量CSR及精确FCSR。实际准备数据在测量前与独立完整排列逐字节比较，结束后再次核对；4处CSR读取保留两侧fence，结果校验和UART位于窗口之外。没有从old/new输出中互选gold或放宽flags。

| 实际参考记录 | 九窗v1 | 八窗v2 |
|---|---:|---:|
| 命令 / NEMU案例 | 21 / 10 | 21 / 10 |
| 退出情况 | 19×exit0；2×预期exit2 | 19×exit0；2×预期exit2 |
| K288 normal-0整体退休 | 2,032,427 | 731,770 |
| K768 normal整体退休 | 5,057,095 | 1,566,414 |
| K288 P/packedP窗口instret | 各22,173 | 各22,173 |
| K288 N/packedN窗口instret | 各13,025 | 各13,025 |
| K768 P/packedP窗口instret | 各58,458 | 各58,458 |
| K768 N/packedN窗口instret | 各34,085 | 各34,085 |

每代十例包括两K的normal/独立replay、K288额外normal-1/2/fullmin、K768末组edge及每K一个共享比较器负控。负控完成一次warm后，在原N的测量调用结束、取完计数及FCSR后翻转output byte1148，准确进入BAD/code91，warm=1、samples=0；预期exit2并不是任意非零退出即可通过。normal/replay的完整validation及raw dump身份相同。完整输出、双slots与guards、全部prepared表示及原fixture逐项比较；初末寄存器/CSR均完整导出，核对长度、原始身份及normal/replay一致性，末态FCSR与实际trap另作精确检查。每例保存15份完整memory dump和4份register/CSR dump。

两代共八个完整leaf机器体SHA及对应八窗instret逐项相同。单位步长仍是一条架构load换另一条load，故这里没有指令数量收益；实际访存拆分和依赖是否改善由目标周期判断，不能先验声称四倍访存或应用加速。

### 已闭合原件与复现入口

下列host operation共同前缀为 `0250d6044ba18f5fd71831ae3131d2ce`，均exit0、cleanup=true；内部命令亦按对应合同全部回收、源/工具pins不变。

| 阶段 | host operation后缀 | UTC实际起止 | 主要原结果 SHA256 |
|---|---|---|---|
| GNU | `.599c35c7b05b66c4b70df0fe592c25ff` | 20:16:06.832–20:16:11.121 | `369307b6a392df26e1e34f5a643feb2cadb96f84ada8006214625ba6e27ebb8e` |
| K288提取 | `.736be37ddbbf39848d313c2165d01b81` | 20:39:47.755–20:39:49.336 | manifest `13d05882e6f1876993a6e6b63c8d5041c1067bdfb73ba061adf41f91d66f2bd1` |
| 九窗参考 | `.972f8367a36e9cd4d393ae1dae2d4f82` | 21:03:10.467–21:03:30.717 | `cec287cff44cdda1070539515a3d426fd81e6a4025e0a84ac6bcb632ef7f1f5a` |
| 八窗参考 | `.61f2f6c1d821afda6e1f2489cb063d3c` | 21:12:56.948–21:13:12.620 | `65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0` |

[reference-raw.zip](packed-ws/reference-raw.zip) 为11,059,275B，SHA256 `20598d3ee465ce7fab91180d1172efc7d83680b04a6ac75c39dbefe3ee77a0b1`。归档operation `.614e4cd47435bdbff612f4d2654e3a21` 于21:36:03.990–21:36:25.144 UTC闭合：1047文件、94目录、1142成员，完整原始字节41,495,393B；753个执行pin、380份完整raw dump、全成员CRC/长度/SHA及原件after-scan均通过，没有省略文件。使用最终result的snapshots/generated_inputs，而非只用早期inputs.json；两代原件、负控、GNU对象和所有日志均保留。137项外部依赖按原path/SHA记录，未重新打包工具链或旧工程，不宣称证据包能脱离环境运行。

归档命名空间为 `wsl/{source-01,gnu-01,q288-fixtures-01,reference-01,reference-02}` 与 `windows/{source-01,fixture-source-01,screen-source-01,screen-source-02,archive-source-01}`。源级派生、原程序和全部构建输入均可从对应snapshot定位；GNU用 [check_gnu.py](packed-ws/check_gnu.py)，新参考用 [screen.py](packed-ws/reference/screen.py) 及 [REFERENCE_CONTRACT.md](packed-ws/reference/REFERENCE_CONTRACT.md)。旧 result/profile 含原绝对路径及其 pins，改CLI根目录或ZIP解压位置不会自动重定位这些依赖；应恢复对应环境和原固定身份。恢复匹配依赖后按CLI传入原固定输入、全新的隔离输出；不要覆盖原运行目录，也不要把固定记录SHA替换成无关版本以绕过身份检查。

### K288目标小试：截至21:38 UTC为已启动、未闭合

启动前operation `.c4f2c397c1ac74d03b657b3c41297f78` 于21:31:42.290–21:31:45.698 UTC完成，重新核对432个实际输入；没有新build、ABI probe或guest。profile 88,784B、SHA256 `b48e4dfd3f6d1bc13c741f6cacc00b9097c946844abeb24c3ffd52d0a1100181`。运行器 [run.py](packed-ws/target/run.py) SHA `df95f6a05dbf3ffdf4314de38ecd8bce13ff3a7b63ef2583bb99d00f77e29655`，复用原完整Q288进程组、deadline、TERM/KILL/reap及最终pins检查；独立审查发现并修正了cycles=UINT32_MAX的单点边界。合成parser检查保存在cloud-reviews，不算实际target运行。

实际target host operation `.be44a4d254afc57af4be96e78c6f3a08` 于 **21:37:33.146 UTC** 启动，原回执记录EMU PID/PGID=8067、CPU1。新K288 ELF为 `7b164fd3a6e08840f1bcc5824f48295e310e4d19544d41000740a8742fd58426`，BIN为 `5efdb3f53786490fd2752b44e0ec48053bbfab98ce829a82ec7fcc8b5db2a756`；使用已固定EMU `f1491865…`、reference `cc768488…`、1400B ABI、D16/O2/T14=1及TRACE0，未应用新CSA/prefix硬件。正常目标BIN与已跑reference image仅UART控制字不同，完整ELF/BIN及全部机器体再次核对。

合同见 [TARGET_CONTRACT.md](packed-ws/target/TARGET_CONTRACT.md)：CPU1、绝对nice5、单额外worker，4M guest cycles / 9000s内层 / 16MiB每流 / 9600s外层；只跑normal-0，不自动重试、延期或扩跑K768。原四臂N/P完整应用operation与输入保护保持；新保护记录为Issue #2 comment6713336725。启动/profile副本见 [target-launch.json](packed-ws/target-launch.json) 与 [target-profile.json](packed-ws/target-profile.json)，活跃输出仍归原operation所有。

只有完整八窗协议、精确flags/hash/instret、唯一GOOD PC、原DiffTest、正常退出与全部回收/输入复核通过后，才能授予这次固定完整调用的target资格。窗口排除prepare，保留原P与packedP中实际较快的合格RVV，并分别比较P→packedP、N→packedN；不能跨ELF拼分母、合并历史百分比或把超时/截断解释成某臂较慢。target内存完整dump、target replay/negative及完整退休审计未列为本小试已完成事项，正式performance/application资格仍为false。K768须依据本次实际结果和剩余资源另作决策。
