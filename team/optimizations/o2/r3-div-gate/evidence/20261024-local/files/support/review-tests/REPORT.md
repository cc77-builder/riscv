# DIV 取消门控：局部测试合同与修改记录

源码基线：4669c487f3024ee5fce514c37270297f99066b2a。
本子任务只改父级测试与检查器；没有修改生产 RTL、生成器、build.sc、run_rtl.py，没有执行硬件仿真。
5 项测试输入已经冻结，SHA256 见 frozen-tests.json，补丁见 strict-tests.patch。
主机验证 49 项 PASS，原始输出见 host-tests.log / host-tests.json。

## 已有覆盖与新增内容

- 保留 22 定向＋10,000 随机完整 128 位数据、三写回数据总线、完整 VPU/perf、ROB/pdest身份、例外和写使能验证。
- 保留 VDot 的 II=1、无反压初响应2拍、满两槽反压、部分取消、R完成但P幸存、真实门控下TE=0复位。
- 保留原36组DIV取消：两种DIV × 下一FU三种 × 计算/可见/背压 × ready两值。
- 新增28组DIV ROB关系：两种DIV × 7关系 × 计算/背压。关系包含同ROB非self、普通older/younger、47/48跨flag杀/不杀、95/0完整环绕杀/不杀。
- 新增关系中12组杀DIV，因此总48次定向DIV取消；每次紧邻下一个父时钟上升沿开始，连续3拍要求该DIV时钟为零，共144采样（VIDiv/VFDiv各72）。
- 原6组DIV TE=1复位扩为12组，包含匹配取消与reset重合；必须只记一次reset终止，不得又记cancel，随后恢复VDot请求。未把旧DIV复位合同扩成TE=0。
- 总完成组数由12变13。20,000步固定随机控制仍保留，但新增定向消耗了serial，因此不能声称新旧全迹线逐帧刺激相同。
- kind2使用原op=0，动态覆盖是VFDiv，不含平方根；不要把同一wrapper的sqrt也写为动态验证通过。

## 严格门禁

C++仍要求取消当拍旧DIV收到真实清理时钟。只有后续没有旧事务、没有新accept、不是reset或TE的真空闲边沿才要求所有FU clock为零。没有延迟宽限，也不会靠随后正常DIV完成来掩盖残留开钟。

每次定向取消后3拍另有显式关闭检查；最终cancel_idle_clock_on必须为零。旧硬件红测预计先被step内部通用规则截获，返回O2_PARENT_FAIL clock，详情包含idle FU retained clock after cancellation/completion。

check_trace从原始逐帧事件独立重算ROB kill、窗口边界、每拍真实clock位和cancel_idle_clock_on；最终摘要改零不能绕过失败。idle_clock_samples也重算，不再列为未复算side counter。check_negative的positive入口同时调用strict checker，保留其原事务交叉复核。

原16个读回负控的名字、类别、exit=1与两行精确输出合同保持不变。新主机负控额外验证：在修改clock时同步修改汇总计数仍被门禁拒绝；第1、2、3拍分别出现clock都被拒绝；reset不能截短采样窗口；伪造summary、错误DIV ROB关系标签也被拒绝。

## 验证与冻结

主机命令：
python3 -B -m unittest discover -s /home/riscv/riscv-lab/zjhwork2-review-20261018/repo/team/optimizations/o2/parent -p test_*.py -v
49 tests OK；git diff --check通过。

开发中新增手写取消窗口fixture把case从fixture改为DIV-cancel-fixture时，首次漏同步redirects=1；该主机测试报错后补齐独立fixture计数，未放松任何门禁。最终记录位于host-tests.json。

后续由根代理使用冻结输入执行旧硬件红测、新硬件FU与真实父级正测以及原16父级读回负控。本记录不能替代那些硬件运行，也不构成全核、NEMU、性能、面积或功耗结论。

归档注意：现有run_rtl.py source列表未包含check_trace.py/test_trace.py；本轮driver或最终manifest需额外保存这两个文件，frozen-tests.json已经含其SHA。
