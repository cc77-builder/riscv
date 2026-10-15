> 本文件是独立审查的只读展示副本。正文相对路径指向同目录审查包解压后的 `independent-review/`，原始正文保存在归档中，不代表所有源码副本直接铺在 GitHub 目录。参见 [README](README.md)。

# RVV baseline independent review

**结论：现有基线在已使用的合法输入域内可等价，但并非最强基线。** 已在真实 GNU RISC-V 汇编器和固定 NEMU 参考库中验证更短候选，不依赖字符串包含测试。完整序列静态指令数为 **13→8**，已知 tu/mu 配置为 **11→6**，四路 batch 为 **26→15**。这些只是指令数；本审查没有全核周期或加速比。

固定源码为 b8272f2（完整 SHA/逐文件 blob 在 [manifest](evidence/source_manifest.json)）；`generate_baseline.py` 也存在于团队 6bf3c2c，`generate_t12.py` 只在 b8272f2。原生成器位于 [generate_t12.py](sources/baseline/team/tests/generate_t12.py) 28–48、[generate_baseline.py](sources/baseline/team/tests/generate_baseline.py) 13–17、39–49。没有读主实现的并发工作文件作为基线。

可直接复核的例子，vd=v10、vs1=v8、vs2=v9，入口 VLEN128、VL8、e8/m1、vstart0、VS 可用、vm=1；scratch v2/v3、t3/t4：

```asm
csrr      t3, vl
csrr      t4, vtype
vwmul.vv  v2, v8, v9
vsetivli  zero, 4, e32, m1, tu, mu
vmv.v.i   v10, 0
vsetivli  zero, 8, e16, m1, tu, mu
vwredsum.vs v10, v2, v10
vsetvl    zero, t3, t4
```

若入口/出口明确固定为 e8/m1/VL8/tu/mu，省略两个 CSR 读取，并将最后一条换成 `vsetivli zero,8,e8,m1,tu,mu`，共6条。任意原 vta/vma 的通用合同必须保存/恢复实际 vtype；不能拿已知配置版本声称保持四种策略。已提供的 [short()、batch_short()](scripts/rvv_reference.py) 可生成正确分配 scratch 的序列；[真实汇编及反汇编](validation/rvv/directed-candidates.S)、[反汇编日志](logs/directed-candidates-objdump.log) 包括旧序列、短序列和负控。

证明依赖以下逐条事实，而不是把候选当成先验结论：

1. e8/m1 的 `vwmul.vv` 产生 signed16、EMUL2 的对齐寄存器组。VL8 只写八个16位有效乘积，恰好填满低编号物理向量寄存器的128位。高组寄存器在 ta 下允许改变，因此必须把 **p 和 p+1 都声明为 scratch**；不能因为 VL8 就把它从可观察状态排除规则里漏掉。
2. 分配偶数 p∈[2,30]，使 `{p,p+1}` 与 `{vd,vs1,vs2,v0}` 不交叠。最多三操作数加 v0，不会耗尽15个候选偶数组。先完成乘法，随后清 vd，所以 vd=vs1、vd=vs2、三者同号、v0/v31 都不提前破坏源。
3. e32/m1/VL4 的 `vmv.v.i vd,0` 清全部128位，包括未来归约 seed 的低32位与高96位。不允许只在 e8/VL8 清零：那只清低64位。
4. 切 e16/m1/VL8 后，读取 p 的全部八个 signed16 乘积。`vwredsum.vs` 的 scalar seed/dest 是**单个向量寄存器中的2×SEW=32位元素0**，不因 LMUL 而要求偶数目的；其 source group 在这里 LMUL1 已足够。m2 也能读前八元素，但没有必要继续把上一步的 EMUL2 机械当作当前 LMUL。
5. seed 与 destination 相同合法：先读取已清零的 vd[0]，完成 signed16→signed32 归约，写元素0；tu 保留目的其余96位零。和在 −130048…131072，32位不溢出。`vredsum.vs` 的16位归约不等价。
6. 恢复保存的 VL/vtype；合法输入下 vstart 始终为0，vxrm/vxsat/vcsr 不变，VS 置 Dirty。单条 VDot 与多指令 RVV 的中间状态、GPR/scratch 破坏、可中断点、非法状态的 trap 行为并不完全等同；性能比较必须限定共同的合法入口/出口合同。

没有联网；依据是固定本地实现、独立整数数学和真实指令执行。NEMU 基础源码 `a48a11f208ff81ad765591d83271d1b339fb3861` 的 [vcompute_impl.c](sources/nemu_base/src/isa/riscv64/instr/rvv/vcompute_impl.c) 464–473、1522–1572 行明确标出 reduction scalar single-register、先读 seed、widened source extension、tu/ta 和元素0写回。它是实现交叉验证，不能替代官方比赛规格确认或新的硬件验证。

| 实际执行的验证 | 结果 | 限制 |
|---|---|---|
| 32,768 个 vd/vs1/vs2 编号组合，真实汇编与参考执行 | PASS | 每组合一个确定寄存器输入；不称数据域穷举 |
| 边界×7组别名×4种 vta/vma×4种 vxrm×2种 vxsat，共2,016组 | PASS | 含 max/min、尾部污染、v0/v31 |
| 固定种子1,000组全寄存器随机输入 | PASS | 独立 Python 大整数 oracle |
| 原通用序列75组×4策略，T09 scratch allocator 7别名×4策略，共328组 | PASS | T12 fixed scratch 版本不扩展为任意操作数合同 |
| 原/短四路 batch | PASS | 配置固定 tu/mu；未测全核吞吐 |
| 完整目的128位、所有非scratch向量/GPR、VL/vtype/vstart/vlenb/vxrm/vxsat/vcsr、dirty VS | PASS | GPR scratch 通用短版 t3/t4；旧版另含 t2 |

[结果 JSON](validation/rvv/results.json) 与 [完整执行日志](logs/rvv-reference.log)；参考库 SHA256 `e5f04192ad782581eef8cd17648933aa6da0fd0543944cb6e59eb931efc60cae`，ABI size1400、VR offset800、512字节已核查。所有命令、退出码、工具 SHA 在 logs/*.command.json 和 [工具清单](evidence/tool_inventory.json)。驱动先前的 ABI/cache/out-of-domain 探测失败单独保留；最终执行 exit0。独立 PC 放置防止固定 NEMU 的指令解码缓存让不同序列意外复用旧指令。

已执行的最小反例（表中的数值是数值表示，JSON 的 byte hex 为小端）：

| 错误候选/前提 | 输入 | 实际反例 |
|---|---|---|
| 乘法前清 vd | vd=vs1=v8，A=−128×8，B=127×8 | 输出0，期望低32 `fffe0400` |
| 用16位 `vredsum` | 同上，vd=v10 | 输出 `00000400`，负和被截断 |
| reduction 使用 ta | 同上 | 高96被置1，不满足清零合同 |
| T12 `general(10,4,9)` 的固定 scratch | 源A放v4 | 开头清 v4 破坏输入，输出0。当前 corpus 只用8/9，故是**接口泛化漏洞，不是已使用 corpus 的失败**；T09 allocator 没有这个问题 |
| `known=True` 当作任意策略恢复 | 入 vtype=192（ta,ma） | 出 vtype=0；当前性能用例确实固定0，不能把适用域扩大 |
| 非零 vstart | vstart=1 | 固定参考在首条 vwmul trap；不把该实现的限制泛化成 RVV restart 规则。候选合同显式排除此输入 |

会夸大 VDot 加速比的具体冗余：旧 general 用单独 v4 清 seed、先切 e32 再切回 e8 才乘法、归约到临时 v5 后再切 e32 做 `vmv.x.s t2,v5`、清 vd、`vmv.s.x vd,t2`。短版省掉1次独立 seed 清零、2次 scalar 跨域搬运、2次配置切换，合计5条；batch 省掉1次 seed 清零、8次 scalar 搬运和2次配置切换，合计11条。它们还引入真实依赖和资源占用，不能把旧序列称作最优 RVV。

当前 T12 性能循环仍是固定源、重复写目的，主要覆盖完整序列吞吐/开销窗口，**不是 RAW 依赖延迟测量**；`raw-long` 不在性能计数场景中。`generate_t12.py:136–141` 两侧都计入 store/fence/counter 窗口，有空循环但未扣除，原 checker 已称 raw uncalibrated。四次 AB/BA 仅提供很少配对样本；不应把模拟器主机秒数、ISA 指令数或局部 II 代替比赛周期。下一步先把短基线纳入独立同硬件配对测量，再决定是否值得改 VDot 时序。
