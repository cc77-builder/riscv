# R2-S1 首块直接初始化：独立 C ABI 配对合同

合同 `r2-s1-firstdot-c-abi-v1`，2026-10-24；操作 `20261024-LiZufan001-r2s1-firstdot-1458`。
这是新软件实验，不修改已发布的 S1/R4/T17 合同、RTL、官方程序或稳定默认库。

## 1. 假设、规格与修改边界

按现行 [vdot 内部规格](../../../spec/vdot.md)，每条 dot8 从零计算，完整覆盖目的128位：低32位为有符号点积，高96位为零；不读旧目的，`vm=1` 时允许 v0。
因此每个行组可用首条 vdot 直接初始化最终累加寄存器，省去组首 e32/VL4 清零、首块 e32/VL4 配置与加法，后续点积仍写临时寄存器并按原S1累加。8×32/reuse 精确少20条指令，点积条数不变。

保留8项 INT8、VLEN128、合法 e8/m1/VL8/vstart0，K13的标量尾部及其 e32/VL4 提取配置保留。矩阵、向量、完整输出槽、带毒初始寄存器、调用ABI、向量状态和所有读取边界沿原 [C调用合同](../r2-select/ENTRY_CONTRACT.md)。软件变化不改变时钟、复位、FU接口、两槽 O2/H1 硬件的首响应2拍和无停顿II=1；本轮不宣称新增硬件时序/PPA资格。

`firstdot_candidate.py` 每次创建私有 renderer，避免旧探针全局替换与并行构建串扰。纯变换与冻结 `first_dot_probe.py` 算法比较；旧探针本身保持原样。
两个变体明确叫 `s1` 和 `firstdot`，不把新基线误称S0。新manifest含 `firstdot_contract` 和精确源码SHA；为保持对照BIN完全一致，payload保留原R4 harness banner。外层构建、运行、结果始终采用本合同，不冒称旧R4/T17新验收。

## 2. 固定输入与最小实验

- 软件来源基点：`137b44befb041439a018a1079577cc000df1ee03`，附本轮新文件精确哈希；官方及旧生成器/检查器原字节不变。
- 硬件只读复用已合格T17：源码 `34bae6d4acceac939f958199dae53c14bc1f6183`，EMU `ff840528eb1009e94906eefb3773ca321050f309553543ab26f0db23c410e30f`，正常NEMU `8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9`。原 `identity-02.json` SHA256为 `4a89872d0463163ea0be83f680843352e01354043f5709509d822353221258eb`。新运行前后用原T17来源门禁复核全部身份；不修改旧身份或正常参考模型。
- 第一阶段仅8×32、dataset0、endtoend-with-c-abi-call（shard3）；S1/firstdot各含basic/reuse × vdot/RVV，完整first、warmup、4个正式repeat与原AB/BA顺序保留。
- 新S1的完整BIN、kernel和public独立GNU对象必须逐字节等于对应T17基线；两个新变体所有ALLOC节布局和槽外BIN一致，4个8KiB槽、API PC不变，两RVV整槽不变，cases/plan相同，无REL/RELA/relax。
- 状态建立、加载、计算、完整输出写回、真实jal/ret与调用参数/观测指针恢复全部计入。保持最快合格同入口RVV，禁止引用旧周期作新分母。

## 3. 验证顺序及停止条件

1. 精确源码/生成物再生、GNU/AM编译、真实链接布局及编译后有限模型（3类输入、2类边界、4随机，带毒初值、全128位与边界读取）通过。
2. 使用原团队外置动态故障夹具，只污染正常NEMU返回的状态副本bit100；真实执行新firstdot，要求首条新机器字 `0x0388000b`、实际vd0/PC对应唯一差分mismatch、预期退出1。不能以历史vd20结果代替。
3. 同一BIN、新PID、负控结束后正常参考恢复，退出0、完整数学/CSR/退休/校准计数器/O2事务通过。禁止把ABORT事件PC强行等同指令PC。
4. S1与firstdot重新实跑，分别在新进程重放全部first/warmup/measured cycles及instret；性能串行，其他重任务结束后运行。
5. 最小实验每候选格只有4正式样本。若firstdot/reuse未同时胜过S1/reuse vdot和本轮最快RVV，保留稳定版、关闭无收益扩大；有具体新证据才另立修订。若通过，允许扩展三数据集及其他形状，保留K13的RVV默认，不预定所有尺寸必须采用。
6. 完整筛选仍不自动切换稳定库。若拟采用，另补普通C调用及新公共对象使用影响，保持可回退、精确身份和原文复算；不把局部窗口推广为LLM/完整应用性能。

所有输出必须新建且在源码目录外，不续跑、不覆盖失败；最多4核。最多4个独立编译任务，EMU串行；性能期间不并行重型审计、构建或其他EMU。不因120分钟目标重复有效实验。

## 4. 可复现命令

在原生Linux检出设置 `REPO`、T17原 `IDENTITY`、对应 `T17_BUILD`、新外部 `OUT`。

```bash
taskset -c 0-3 python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_experiment.py" \
  --repo "$REPO" --action build --identity "$IDENTITY" \
  --baseline-build "$T17_BUILD" --output "$OUT/build" --shards 3 --datasets 0 --jobs 2

taskset -c 0-3 python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_experiment.py" \
  --repo "$REPO" --action run --identity "$IDENTITY" --build "$OUT/build" \
  --output "$OUT/run" --operation-id unique-operation-id --negative --replay
```

运行 `state.json`/实际退出码和每进程原文是执行事实；`results.json`给出完整数据与资格边界。原静态PASS不转移，运行状态不确定时查询原回执。

## 5. 原文封存与离线复算

`firstdot_evidence.py` 使用原 `portable.py` 字节检查器、原 R4 构建命令/动态负控夹具验证和原 `merged_evidence.py` 正常运行复算；只通过私有模块绑定本合同、已核实T17身份和相同C ABI计数器适配。官方与旧团队门禁不改。

归档保留生成物、独立GNU对象、ELF/BIN、精确源码快照、构建命令/原文、运行命令/退出/原文、完整窗口和O2事务，以及T17构建元数据。EMU、正常NEMU、flash、AM/GNU工具和大型硬件树以物理运行已核实的哈希表示；离线PASS不声称重新验证缺席的物理输入。

离线复算逐条校验C ABI路径、数学/完整128位/CSR、退休指令、周期标定、O2排空、实际新rd的bit100负控与同BIN恢复，重算所有样本及最快合格RVV。跨批次要求相同源/工具/硬件身份、无重叠图清单、唯一负控、每图唯一正式执行、每个形状dataset0双变体全窗口重放；所有性能进程按真实时间串行。

完整矩阵复用第一批2图及其5次运行，再构建8×32/dataset1,2的4图和其余三形状/三数据集的18图；第二批22正式+6重放，总计33次EMU。不得把完整24图构建和旧2图同时纳入，以免重复计数。`probe`与`matrix`归档的精确覆盖分别为2图与24图，汇总中的`full_matrix`必须与原始执行相符。

```bash
python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_evidence.py" \
  --repo "$REPO" --action pack --identity "$IDENTITY" --scope probe \
  --run "$OUT/run" --archive "$OUT/probe-archive"

python3 -B "$REPO/team/optimizations/o2/r2-vector-accum/firstdot_evidence.py" \
  --repo "$REPO" --action audit --archive "$OUT/probe-archive" \
  --output "$OUT/probe-audit.json"
```

本合同使用原T17身份文件位置和本轮新建的原生绝对目录；输入目录不使用符号链接。路径检查用于防止工程误操作，不是执行任意不可信构建清单的安全边界。封存重算另按原始绝对路径验证目录身份。
