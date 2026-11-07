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
