# Q288 活动消费者完整状态接续 v1

合同 `r2-s3-runq-active-forward-v1`，2026-10-26。新增团队消费者与实际 ELF 有限模型桥接；保持原上游、旧观察器、所有历史验证器/实验和R5默认不变。

## 输入与实现边界

固定未训练确定性权重、D288/H768/L6/heads6/kvheads6/V32000/seq256/GS32，以及token `[1,7,19]` / pos `[0,1,2]`，沿用 `forward-host` 已声明的范围。上游 `runq.c` SHA256 `ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548`、43,357字节保持原样。新 `active.c` 只包含既有观察器以复用原样参考、确定性权重/pack及边界检查；原observer只在独立reference执行期间启用。

团队 `team_forward` 是有明确名称的独立消费者，逐字恢复检查证明：除函数名、四类Q/K/V/O回调，以及增加检查的quantize/matmul调用包装外，其余完整forward源文本与顺序等同固定上游；它不替换或改写原reference的forward。调用原样quantize、RMSNorm、softmax、FFN/classifier等助手，不声称算法独立oracle。

Reference、TA、FR各自分配清零RunState；全部可写buffer完整区间两两不重叠，权重只读共享。三位置持续使用各自KV，不在位置间重置。TA/FR每次真实量化输入来自自己的激活，不从reference或旧捕获喂入golden。

24份QKVO权重分别pack一次，共1,990,656字节，跨所有位置复用。每次完整forward后原序列化权重、embedding和packed权重逐字节不变。QKV三次投影共享同一次量化的324B输入；O使用attention后新量化。额外保存每次量化前真实FP32 QKV/O激活，供后续消费者边界工作使用；不是从量化值反构。

## 实际ELF与数值语义

使用已交付TA目标ELF SHA256 `610c499f46f1fe73074f626d8990bdcbdbc5f78c30ce8fc4a835495b0e392faa`，实际符号TA=`q288_tail_vdot`、FR=`q288_fused_rvv4`。原机器码/尾部代数证书和有限执行模型不改。每个callback从真实状态构建输入，执行完整机器函数，检查全部288输出、末槽完整128位、精确footprint、只读输入、ABI、CSR、FP顺序和指令计数，再把模型实际结果写回候选状态。独立Python算术golden仅作核对，不能成为写回来源。

保持RNE、严格binary32、不收缩FMA、不fast-math、不OpenMP、单CPU。每次量化检查有限值、组最大值非零、正且可表示scale、round后int8合法域；保留上游零组行为，不扩大输入域。宿主/libm/编译器身份全部记录；没有跨平台逐位相同承诺。

## 正常验收

- 原reference每位置完整观察43 matmul /25 quantize /24 QKVO，13 RMSNorm /36 softmax及315组/10,080元素。
- TA与FR各3次完整forward、72次真实ELF模型调用；总144次候选投影、41,472输出。
- 各候选每位置完整32,000 logits与各层完整256行KV，与原reference逐位相同；C内存比较后独立回读完整产物再次比较。
- 每次只有当前位置KV可变，历史/未来行逐字节不变；当前行有限且非退化。
- 每次callback前把所有288输出置NaN，必须完整覆盖；QKV路由、共享输入和调用序列准确。候选每位置24投影/19其余matmul/25量化。

## 消费前负控

正常与每个负控使用独立进程/输出/新状态，固定同一ELF和源。

1. K负控：TA第一层pos0的有效ELF结果返回后、RoPE/KV写入前，仅给K[0]加8。继续全部3位置；必须在pos0/1完整key cache发现差异，且pos1完整logits不同。它证明错误历史K实际参与后续attention；不要求pos0单元素softmax的logits改变。
2. V负控：同位置V[0]加8，必须pos0完整value cache与logits都不同，pos1 logits继续不同。
3. 漏写负控：首次callback返回成功但不写任何输出，必须以残留NaN的明确错误、exit2拒绝，不能接受为完成。

K/V负控在局部ELF正确性检查之后注入，不允许仅靠局部golden检查提前拒绝来冒充传播验证。原reference状态不受注入影响。两种传播负控各72次模型调用，共144次；漏写负控不执行模型。

## 交付与限制

保存原命令、stdout/stderr、全部源闭包、ELF/宿主库身份、callback日志、原始量化前输入及完整状态；失败不覆盖。可从发布包读取同SHA目标ELF或显式指定，独立输出目录运行 `check.py --repo ... --output ...`。

这只取得“宿主完整消费者＋实际RISC-V ELF有限模型的活动状态接续”资格。`target_emu_runs=0`；不授予目标token周期、吞吐、训练质量、完整应用加速或ASIC结论，不将既有局部百分比相乘，不改变R5或旧HOLD。后续目标边界需独立合同/最终ELF/公平强RVV；本合同不自动启动EMU矩阵。
