# 完整公开 forward 的宿主观察与实际 Q 数值接续 v1

合同`r2-s3-runq-forward-host-v1`。限定一个固定公开消费者版本、一个确定性未训练权重、三个连续位置及两个独立RunState。不下载checkpoint，不启动EMU，不测宿主或目标加速，不授予模型质量或实际token性能资格。

上游为karpathy/llama2.c `350e04fe35433e6d2941dce5a1f53308f87058eb`。`upstream/runq.c`须与原始Git blob`42360ae97c724d28e11ac4545e30f57b7a9c9a8e`、SHA256`ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548`完整字节一致。使用其已有TESTING宏排除CLI main，其他代码保持；不重写原matmul、quantizer、forward或判定。MIT许可随原源保存。

配置D288/H768/L6/heads6/kvheads6/V32000/seq256/GS32，来自固定README与默认训练配置及hidden_dim/export公式；未声称核验过模型文件头。权重由固定xorshift32种子生成signed[-8,8]字节和正的二进制精确尺度，按原memory_map_weights布局初始化，共17,101,440字节；共享embedding/classifier，原加载函数实际反量化36,864,000字节embedding。它不是训练好的模型。所有参考权重与embedding在每个forward后全字节比对原快照。

原forward在宿主实际执行token1/7/19、pos0/1/2；然后用新分配并清零的第二RunState重复。全部32,000个logits与完整KV cache逐位相同。每次只允许当前pos的各层KV行变化，当前行须有限且非全零。比较器还以真实一位logit破坏验证能拒错，再恢复。

只对观察器TU启用GCC函数进入／退出观察，全部观察回调禁用自递归instrumentation；acc8 C对象与普通signed int8 host leaf独立编译，不被观察。禁止OpenMP并行、LTO、FP contraction、fast math及相关跨过程优化，限定一CPU。宿主CABI/float/libm身份须记录；没有跨平台bit相同或宿主时间转移到香山的承诺。

观察每次真实forward有43 matmul、25 quantize、13 RMSNorm和36 softmax；每次量化前从已固定调用顺序对应的真实state数组检查所有值有限、每组最大绝对值>0、实际float尺度正且有限，以及round后位于int8可表示域，完整315组/10,080元素；退出后再检查原quantizer实际写出的尺度。未修改上游对全零组的处理；若实际触发该输入域边界则失败并保留。Q/K/V三个捕获输入必须逐字相同，O使用真实attention输出重新量化。72为位置／权重组合观察案例，不称72种独立量化输入，实际输入字节去重数量另记。

24个Q/K/V/O权重只pack一次，新增1,990,656字节，在全部调用间复用。原matmul退出后，以同一实际量化输入/尺度、固定acc8 C及普通host leaf被动计算完整Q并逐位比较，但不将候选结果写回原forward。第一RunState导出72个实际Q输入和原始golden，以及24份原W、Ws及packed W；不存在仅凭人工统计的替代样本。

再以固定GNU融合ELF SHA`6975d57aecd77f9ec6337cbf3aa5b031033e8a7b86dcad4bcd7e78b33b2dc97d`和固定有限模型，对72个捕获分别运行vdot与RVV4的完整实际机器路径；检查288输出、末组全部槽、只读输入、精确footprint、ABI、CSR及324整数核。共144次机器路径、41,472个输出比较。它是静态有限机器码模型，不能称真实RISC-V目标执行或NEMU验证。

本合同的价值为实际消费者调用、量化复用、持久pack、状态生命周期和数值接续的有界证据。上游forward仍消耗其原matmul结果；当前输出不是候选已替换整模型的证明。不得与另一BIN的pack/Q成本拼接，不增加目标性能样本，不解除任何旧HOLD或改变R5默认。
