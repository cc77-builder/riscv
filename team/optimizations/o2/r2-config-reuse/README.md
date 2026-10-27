# R2-S3：重复向量配置候选

本目录保留 firstdot 之后的重复配置删除候选及原主机证明，并提供独立 GNU/整核验证、普通 C 入口和可选静态库。**当前运行资格与四形状采用决定见 [RUNTIME_RESULT.md](RUNTIME_RESULT.md)，实际使用、复算及回退见 [RUNTIME_README.md](RUNTIME_README.md)。**

下面保留原主机阶段的生成与检查入口。该阶段的历史结论见 [RESULT.md](RESULT.md)，删除规则、初始状态和反例见 [CONTRACT.md](CONTRACT.md)；新增运行及C边界分别见 [运行合同](RUNTIME_CONTRACT.md) 和 [C合同](C_CONTRACT.md)。[R5稳定入口](../r2-select/STABLE.md) 与 [firstdot库](../r2-vector-accum/FIRSTDOT_README.md) 继续保留。

## 生成可比较源码

在含本目录的Linux原生团队检出中运行。`repo`是当前准确根目录；输出位于独立新目录，不覆盖历史产物。

```bash
repo="$(git rev-parse --show-toplevel)"
trial_root="$(mktemp -d /tmp/r2-config-reuse.XXXXXX)"
python3 "$repo/team/optimizations/o2/r2-config-reuse/candidate.py" \
  --repo "$repo" --output "$trial_root/firstdot" \
  --variant firstdot --dataset 0 --shard 3
python3 "$repo/team/optimizations/o2/r2-config-reuse/candidate.py" \
  --repo "$repo" --output "$trial_root/config-reuse" \
  --variant config-reuse --dataset 0 --shard 3
```

shard 1/3/5/7 分别对应4×8、8×32、16×64、4×13；仅生成原C ABI endtoend边界。vdot/RVV、basic/reuse均在每个图内。`kernels.S/cases.h/gemv.S/gemv.h`复用原wrapper与输入布局，manifest明确`runtime_qualified=false`，并逐项记录删除位置及其支配配置。

这些生成物仍使用原harness内部符号，供验证适配，不能直接充当合格公共库。普通C公共源由本轮独立运行适配导出，使用不同命名空间；不能把本生成器的新manifest传给冻结firstdot运行器后忽略身份拒绝。

## 重做本阶段主机验证

原主机阶段实际环境为Linux、Python3.12.14、LLVM20.1.2动态库。代码使用标准库，通过LLVM C API调用RISC-V汇编后端；不需要安装Python第三方包。该主机阶段没有安装或修改用户本机工具。

```bash
python3 "$repo/team/optimizations/o2/r2-config-reuse/check.py" \
  --repo "$repo" --output "$trial_root/host-check" \
  --llvm-library /usr/lib/x86_64-linux-gnu/libLLVM.so.20.1 --jobs 4
```

库路径必须指向当前环境真实可用且具备这些C API的LLVM；缺少时停止该构建步骤，不把此路径当作所有机器的安装标准。实际库SHA、版本、ABI、features、命令和退出码记录在产物中。原S1模型、ELF读取器及GNU锚对象从仓库按固定哈希只读载入。

轻量状态与输出保护检查可单独执行：

```bash
python3 -m unittest discover \
  -s "$repo/team/optimizations/o2/r2-config-reuse" \
  -p test_candidate.py -v
```

完整检查含24份串行与24份并行生成、12份原firstdot逐字节再生、48对象汇编、48对机器码删除核验、16函数/39输入/3入口状态的成对模型执行。既有输出和来源树重叠输出会拒绝，失败记录只写入本次成功创建的独立目录。

## 已封存证据

- [最终结果](evidence/host-v1/result.json)、[源清单](evidence/host-v1/source-identity.json)、[逐函数编译比较](evidence/host-v1/compiled-pairs.json)。
- [全部原始输出](evidence/host-v1/host-evidence.tar.gz)、[逐载荷清单](evidence/host-v1/archive-manifest.json)、[封存字节核验](evidence/host-v1/archive-check.json)。
- [独立只读审查与本机访问阻断](evidence/host-v1/review-and-runtime.json)。

归档包含`config-host-01`初轮输出、`config-host-02`最终输出、最终源快照及输出保护反例；最终资格只取`config-host-02`。两轮都不是EMU执行。解包到新目录后按清单核对载荷SHA；封存核验只证明字节完整性，不代替重新执行编译/模型或整核。

## 接续与回退

原主机阶段、GNU适配、固定布局性能矩阵和普通C交付的证据分开保存，不将历史主机PASS当作实跑资格。当前源码/工作区/真实进程与发布状态见 [运行定位](evidence/runtime-v1/runtime/locations.json) 和 [Issue #2](https://github.com/cc77-builder/riscv/issues/2)。

已完成的探针和矩阵不需要重复启动。新caller、布局、工具链或应用需要按变化影响验证；继续优化时先提出有数据依据的假设，以最快合格RVV走相同调用路径进行有界比较。不能把固定GEMV函数窗口的收益当作完整应用或硬件PPA收益。

本候选使用独立 `config_reuse_gemv_*` 入口，原R5默认和firstdot公共库保留。回退通过选择原入口并重新编译调用端完成，具体命令见 [使用与回退](RUNTIME_README.md#5-回退)。
