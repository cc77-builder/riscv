# R2-S2：固定完整布局后的独立重测

## 为什么需要新合同

本入口使用 `r2-s2-fixed-layout-screen-v1`，沿用冻结 S2 安全五项尾部及原数学、寄存器、CSR、计时和退休合同，补齐 S0/S2 **完整加载布局**的公平门禁。

历史 [MERGED_RESULT.md](MERGED_RESULT.md) 对应的真实 DiffTest、完整结果、拒错／恢复记录仍保留原始事实。后续 S1 排查发现，旧 K13 配对虽然固定了各内核入口和 RVV 函数机器码，`main` 地址及内核槽外加载字节仍有差别；旧 K13 周期差不能继续作为纯软件变换的采用依据。原运行、旧合同和哈希不改写，本入口重新构建并测量独立的固定布局 S0/S2，不给旧记录补一个追认的公平 PASS。

调查来源见协调 [Issue #2 的旧 S2 布局检查](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6367265269)及[8192 槽／norelax 可行性](https://github.com/cc77-builder/riscv/issues/2#issuecomment-6367718806)。这是内部工程证据，不是新的官方赛题解释。

## 受检假设与决定条件

假设仍是：K13 的安全向量五项尾部能够抵消原标量乘加尾部的开销。主要指标是 **4×13／reuse／endtoend** 的同布局 S2 对 S0 周期；basic、core、全部三个数据集及 16×64 不变控制一并报告。endtoend 为 O3 内核窗口，包含配置、输入读取、计算与输出存储；不代表完整系统、LLM 请求或 wall-clock 时间。

只有数学／边界／真实 DiffTest、完整布局、所有规定样本、确定性重放及控制不变均通过后，才评价周期。无端到端收益或退化则保留 S0；仅局部有效则保留准确适用形状及软件布局。较快合格 RVV 必须保留，不能用较弱 basic 或历史 RVV 放大优势。S1 等其它合同产生的更快 RVV 是后续选型必须纳入的候选；跨合同均值不能自动当作同一配对实验。最终采用仍需 R2-SELECT 在统一布局、窗口和输入下覆盖四尺寸及较快 RVV。

## 改动边界

新增 `fixed_layout.py`、`fixed_screen.py` 和事后 `fixed_evidence.py`。不修改冻结的 `candidate.py`、原 O3／unified-vdot 生成器、黄金值、`linked_gate.py`、`fullcore_screen.py`、`merged_screen.py`、旧审计器或历史证据。没有 RTL、时钟、复位、接口、正常 NEMU 或外部硬件构建改动。

`fixed_layout.bindings()` 只在单个新入口进程中为固定旧 runner 绑定新的生成／构建／配对检查及合同身份；校验 helper 文件位置与 SHA-256，拒绝嵌套绑定，并在异常退出时恢复全部原入口。它不向磁盘改写旧工具、不改变其它进程的检查器，也不把旧合同结果升级为新合同结果。

### 完整布局合同

布局身份为 `r2-s2-8192-norelax-exact-metadata-v1`。

| 对象 | 必须成立的条件 |
| --- | --- |
| 汇编生成 | 从冻结候选完整重生成；原唯一 `.option norvc` 后加入 `.option norelax`；精确八处 `.balign 4096` 改为 `.balign 8192`，其它生成主体不变 |
| 独立参考对象 | GNU 单独编译，`.text` 为四个 8192 字节槽、对齐 8192，无有效 relocation；四个函数从各槽起点开始且不越界 |
| 链接结果 | 四个完整槽（包括函数外 padding）与独立对象 `.text` 逐字节相同；固定地址为 RAM 起点加 `(index+1)*8192` |
| main／布局 | 配对 `main` 地址、长度、机器码相同；所有 ALLOC 节的类型、flags、地址、长度、对齐相同；全部 program headers 和入口相同 |
| RVV 对照 | 两个完整 8192 字节 RVV 槽、生成主体和计数字段完全相同 |
| K13 允许差异 | 仅两个 vdot 槽可改变；槽外只有 cases 行 0、2 的 `dots` 字段允许精确 `uint32 4→8`；字段宽度与偏移来自既有 1104 字节 ABI，禁止按实测差异动态扩大白名单 |
| K13 其余加载字节 | 允许区域清零后，整 BIN 逐字节相同；各自 ELF 与 BIN、编译 cases 与完整 manifest 一致 |
| 16×64 控制 | 不允许上述 K13 元数据例外，S0/S2 整 BIN 相同 |

K13 两个允许元数据字段的 BIN 偏移为 `0x120024` 和 `0x1208c4`，字节必须分别为 `04000000` 与 `08000000`。字段邻字节、字段高字节或任何第三个字段的变化都不是例外。

### 构建来源

每镜像保存源快照、生成文件、真实 AM 链接与独立参考编译的两条命令、stdout/stderr 原文及 SHA-256、开始／结束时间、真实 PID、退出状态、工具路径／哈希和两个 AM 库身份。顶层与分步回执必须一致，argv 必须精确符合本合同，命令必须实际启动、正常退出且没有超时；构建原文哈希亦须一致。

离线审计把历史命令路径按 `PurePosixPath` 解析，实际证据文件按当前平台 `Path` 读取，因而允许归档移位。它还把原 make 构建根绑定到对应 `image.path`，把源码根绑定到运行输入中唯一的实际新入口根；仅有两份互相抄写但来源不相符的回执不能通过。

## 硬件、运行顺序与样本

复用 [MERGED_SCREEN.md](MERGED_SCREEN.md#硬件身份) 固定的单一合并硬件及严格实物核验：源码 `6d2abe403b07c297b8830a7d4f06e370b0a8e070`、EMU `1a23dbab5f919da0fb06873c5a4db3ce5fec9eea7dfb98860cdd5fa2b062ec63`；MinimalConfig、单核、单 EMU 线程、O2 两槽及原 trace。始末核对 429 源码、21,236 依赖及 1,672 生成物；每运行前后核对冻结输入和检查器。新合同不恢复缺失的旧 B0/H1 实物，不代替 MERGE-REG、R4、T17 或面积／时序验收。

26 个 canonical 镜像组成 13 对：K13 smoke 一对，16×64／K13 的 core／endtoend × 三数据集，共 12 对 performance。串行运行仍使用旧 runner 的严格顺序：一次 bit100 负控、同镜像正常恢复、S0 smoke、24 次正式运行、4 次 endtoend 重放。奇数数据集反转 S0/S2 顺序。

完整成功批次要求 **31 次实际 EMU，其中 30 正常、1 预期拒错；384 正式窗口；4 次确定性重放**；实际完成状态见 `FIXED_RESULT.md`。重放、smoke、first 和 warmup 不算新增正式样本。所有正常运行仍检查全 128 位黄金值、保护寄存器／CSR、实际退休计数、DiffTest 身份及 O2 协议／排空；负控仍要求精确 bit100 高半部拒错链及新进程正常恢复。没有降低原门槛。

## 配置和入口

Linux/Python 3.10+、GNU RISC-V 工具链、固定 nexus-am 及实际外部构建／参考输入准备好后，创建不提交的本地 JSON。各路径取当前机器实际位置，共享文档不绑定个人目录。

```json
{
  "am_home": "/path/to/private/nexus-am",
  "cross_prefix": "riscv64-linux-gnu-",
  "hardware_source": "/path/to/verified/merged-source",
  "build_record": "/path/to/verified/build-record",
  "build_driver": "/path/to/actual-recorded/build-driver.py",
  "canonical_build": "/path/to/new/canonical-build",
  "reference": "/path/to/verified/riscv64-nemu-interpreter-so",
  "flash": "/path/to/verified/boot-flash.bin"
}
```

在仓库根执行。下列 `R2_FIXED_*` 变量指向自己的本地配置或新输出；先按协调 Issue 核对认领、资源、旧运行和保护状态。

```bash
R2_FIXED_TEST_CONFIG="$R2_FIXED_CONFIG" \
R2_FIXED_TEST_OUTPUT="$R2_FIXED_TEST_IMAGES" \
python3 -B -m unittest discover \
  -s team/optimizations/o2/r2-safe-tail -p test_fixed_layout.py -v

python3 -B team/optimizations/o2/r2-safe-tail/fixed_screen.py \
  --repo "$PWD" --config "$R2_FIXED_CONFIG" \
  --output "$R2_FIXED_BUILD" --action build

python3 -B team/optimizations/o2/r2-safe-tail/fixed_screen.py \
  --repo "$PWD" --config "$R2_FIXED_CONFIG" \
  --output "$R2_FIXED_PREFLIGHT" --action preflight

python3 -B team/optimizations/o2/r2-safe-tail/fixed_screen.py \
  --repo "$PWD" --config "$R2_FIXED_CONFIG" \
  --output "$R2_FIXED_RUN" --action run
```

配置中的 `canonical_build` 必须等于 build 动作的输出。输出目录必须原先不存在。build 完成只写 `S2_FIXED_LAYOUT_26_ELFS_STATIC_PASS_NOT_RUNTIME`，preflight 为零 EMU；run 才执行新批次。该入口不接受旧 `CANONICAL_ELFS_STATIC_PASS_RUNTIME_NOT_RUN` 作为新布局验收。

## 封存、离线重算与 Git 完整性

```bash
python3 -B team/optimizations/o2/r2-safe-tail/fixed_evidence.py \
  --repo "$PWD" --action pack --run "$R2_FIXED_RUN" \
  --archive "$R2_FIXED_ARCHIVE" --output "$R2_FIXED_PACK_RECEIPT"

R2_FIXED_TEST_ARCHIVE="$R2_FIXED_ARCHIVE" \
python3 -B -m unittest discover \
  -s team/optimizations/o2/r2-safe-tail -p test_fixed_evidence.py -v

python3 -B team/optimizations/o2/r2-safe-tail/fixed_evidence.py \
  --repo "$PWD" --action audit --archive "$R2_FIXED_ARCHIVE" \
  --output "$R2_FIXED_AUDIT"

git add -f -- "$R2_FIXED_ARCHIVE"
python3 -B team/optimizations/o2/r2-safe-tail/fixed_evidence.py \
  --repo "$PWD" --action index --archive "$R2_FIXED_ARCHIVE" \
  --output "$R2_FIXED_INDEX_AUDIT"
```

`pack` 必须从原 live Linux 检出执行：新入口在创建归档前要求 `--repo` 等于 runtime-inputs 中唯一的实际运行源码根。旧封存器按此根收集运行 checker；不能在另一检出用相同源码代替原根进行 pack。独立或移位检出用于 `audit`／`index`。

`pack` 可用重复 `--support` 附上实际主机测试／预检等证据；自动附上新事后审计器源码，并与执行源码逐字节绑定。它不是运行时输入，不追溯追加到冻结 runtime-inputs。保留旧封存器的双重原始／压缩字节验证与三个归档元数据文件格式。所有新审计输出必须位于归档外且原先不存在。

`pack` 只报告字节和完整布局通过。`audit` 额外复用旧审计器，从原始 ELF、日志和事件重算架构、CSR、退休、负控／恢复、重放和全部正式统计；新审计器还重新计算全部 13 对布局、核验新 build 状态及完整 pair 缓存。原审计器不会自动调用新 live canonical 检查，故这层不可省略。外部硬件／正常 NEMU／flash／AM 库保留固定哈希及来源，不伪称离线重新执行或重新验证了缺失实物。

完整架构复算仍以 Linux 执行；冻结生成器的默认文本换行没有改变。原生 Windows 可验证归档字节、内存中的 ELF 配对、原 Linux 命令回执及 Git 索引，不能把这些检查写成 Windows 完整架构复算。

`index` 复用既有准确清单、stage-0 普通文件模式和 Git blob 字节检查，额外执行完整布局／来源关系检查；它不运行架构复算、不替代 `audit`、也不自动暂存文件。只对这份已审查归档使用显式 `git add -f`，不扩大忽略规则。发布前必须在实际索引再次检查，而非只看工作树文件存在。

## 运行保护和恢复

保护范围以 Issue 的真实 UPDATE 和 `runtime-inputs.json` 为准。`state.json` 的 `active_pid`／`active_result`、分运行 `result.json` 及外层真实 Worker/操作回执共同定位活跃程序；PID 可能复用，必须核对实际命令身份。源码、canonical、运行配置及输入不能因新聊天或日志暂时无变化而改写。

本 runner **不支持断点续跑**。失败后保留旧输出，先定位原因；新的 `--action run` 是完整新批次，不是续跑。没有输入变化且已有正确结果时不要为了增加工作量重测。重建 canonical 亦保留独立来源和输出，不能挪用旧版本的静态或运行 PASS。

最终结果、取舍与下一具体动作见同目录 `FIXED_RESULT.md`；认领和运行保护只在协调 Issue 维护，开发计分板保存一条实际工作摘要。
