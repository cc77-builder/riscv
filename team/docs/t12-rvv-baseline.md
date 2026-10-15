# T12 等价 RVV 与计时边界

完整有符号8项和为 `[-130048,131072]`。19位是最低有符号宽度；结果为低32位补码、高96位零。这里的等价指固定合法入口下、允许明示 scratch 的函数序列等价，并非单条 vdot 的全部无副作用合同。

当前生产 RTL 和黄金 NEMU 未改。原 RVV 基线和全部 AB/BA 样本保留；新基线单独生成 `baseline=lean` 的清单及镜像。两套清单各自绑定生成器、源、binary、实际 DiffTest 和完成位图。各分片唯一身份是 `(seq,id,repeat)`，跨基线记录还带独立清单 hash，不能混拼两套计划。

新完整序列以 v8/v9 为源、v10 为目的、v2/v3 为 scratch：

```asm
csrr t3, vl
csrr t4, vtype
vwmul.vv v2, v8, v9
vsetivli zero, 8, e16, m1, tu, mu
vmv.v.i v10, 0
vwredsum.vs v10, v2, v10
vsetvl zero, t3, t4
```

vwmul 首先消费原源（允许目的与源别名，只要不和固定 scratch 冲突），再清目的；不能先清目的再乘，否则别名失效。八个16位乘积完全位于 v2；v3 按最初 EMUL2 明示为 scratch。e16/m1/vl8 的清零覆盖目的128位，作为32位归约初值的低32位也为0。`vwredsum` 正确扩宽为32位，tu 保留已清零的高96位；无需先切 e32 或经标量搬回。完整版本保存/恢复真实 vl/vtype，六CSR均校验。

| 场景 | 原 RVV / 新 RVV 每次计算序列条数 | 边界 |
| --- | --- | --- |
| complete | 13 / 7 | 完整合法配置与策略恢复；t3/t4 也属 scalar scratch |
| known-config | 11 / 5 | 入口固定 e8/m1/vl8/tu/mu/vstart0；退出恢复同一已知配置，不声称任意策略透明 |
| independent-batch | 26 / 14（每次四个结果） | 入口固定e8/m1/VL8/tu/mu；源v8/v9，目的v10..v13；新 scratch v16..v23；共享一次e16配置和固定配置恢复 |
| dependency-chain（新增） | 新 RVV5 / vdot1 | 64次 v10→v10 真 RAW 依赖，与独立四路 batch 单独报告 |

生成器拒绝固定 scratch 与源/目的冲突；没有冒充可任意分配全部32寄存器的通用 ABI。完整双路比较覆盖所有非 scratch 终态寄存器、全部32初态寄存器、完整128位目的、六CSR、VS及存储读回；RVV 的 scalar scratch 不计入严格单指令无副作用声明。

所有窗口保留原始 `cycle_begin/end`、`instret_begin/end`，起点在共同 fence 后，终点包含完整结果存储和 fence；没有打印在被测核内。每场景按4次 AB/BA交替，空窗口一并保存，**不减空窗口、不挑最快样本、不拿host秒数作周期**。读计数器的序列化、流水位置尚未做硬件校准，因此数值只能称该具体程序窗口的原始计数，不能称 FU latency、Fmax 或官方性能验收。独立 batch 与依赖链也不能混为同一吞吐指标。

新简化序列在固定NEMU参考层完成16,800双路组（75输入×7别名模式×4策略×4 vxrm×2 vxsat），另75 known与75 batch；完整199计划也已真实全核DiffTest通过，其中11组边界和64组固定随机均有vdot/RVV双路记录。精确提交、各层范围及所有原始窗口见[本轮交付](t12-r2-delivery-20261014.md)和[版本化证据](../evidence/t12-r2-20261014/README.md)。参考层数量不加进全核覆盖；旧序列和超时日志保留。
