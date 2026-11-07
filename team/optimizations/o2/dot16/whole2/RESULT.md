# dot16 whole2：实际 GNU ELF 与完整函数主机筛选通过

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
