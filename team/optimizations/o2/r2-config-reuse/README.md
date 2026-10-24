# R2-S3：重复向量配置候选

本目录交付 firstdot 之后的独立软件候选。**当前只完成状态证明、真实LLVM汇编及编译后主机模型检查；尚不能作为新的稳定库或性能获选版本。**

结论和实测边界见 [RESULT.md](RESULT.md)，删除规则、初始状态、反例及整核进入条件见 [CONTRACT.md](CONTRACT.md)。稳定使用继续从 [R5入口](../r2-select/STABLE.md) 或已合格的 [firstdot库](../r2-vector-accum/FIRSTDOT_README.md) 进入。

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

这些生成物仍使用原harness内部符号，供验证适配。它们不是新增的合格公共库，没有安装、默认切换或稳定ABI发布入口。不能把新manifest传给冻结firstdot运行器后忽略身份拒绝。

## 重做本阶段主机验证

本轮实际环境为Linux、Python3.12.14、LLVM20.1.2动态库。代码使用标准库，通过LLVM C API调用RISC-V汇编后端；不需要安装Python第三方包。本轮没有安装或修改用户本机工具。

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

下一执行者先读协作Issue，核实实际工作区和运行，再认领R2-S3。本轮没有访问Windows来源树，不能凭本结果推断其HEAD或空闲状态。

整核阶段还需独立身份的GNU/nexus-AM构建及验证适配、固定完整加载布局、真实负控/同BIN恢复、同入口强RVV与重放。先做8×32/dataset0的有界筛选，有明确周期收益再扩大，详见合同第4节。

本候选没有接入任何默认入口，因此保留现有R5和firstdot版本即可继续正常使用；不需要撤销硬件或回滚稳定库。
