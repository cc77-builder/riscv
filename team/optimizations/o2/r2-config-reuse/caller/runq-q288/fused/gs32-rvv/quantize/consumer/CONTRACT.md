# G 与 G＋GS32激活量化：首次完整消费者参考

合同：r2-s3-first-forward-gsq-v1。本轮只取得新组合固定p0参考资格，不启动目标EMU，不改变稳定默认。原型九文件、原G/P冻结输入与失败证据不改。

## 规格

RV64G＋RVV、VLEN128、FS/VS启用；固定D288/H768/L6/GS32模型，token=1、position=0。新同镜像保留原G，新增GQ。G标签0x47533332；GQ私有标签0x47535131，不改变旧公开枚举。正常参考镜像UART=0，仅方法word的4B可不同；共同prepare、模型和零初态一致。

GQ完整复制G cached clone，仅改变函数名、五个量化静态调用及薄入口，完整可逆恢复。动态结构19次n288＋6次n768，共315组是源码控制流计数，不是实测快路命中率。七K288 GEMV仍G、唯一W2矩阵乘仍q768_fr；W2的hq量化改为Q是预期变化。原consumer、quantize、官方upstream/runq.c、库、五模型缓冲及FP32顺序不改。

ABI为void(QuantizedTensor *,float *,int)，上下文两个指针；输入/输出/scale不别名，实际独立state数组满足。快路保存VL/VTYPE和FCSR行为；不满足域时恢复入口环境、整调用tail原quantize。无栈/无math调用只描述快路；fallback沿原quantize的112B栈、fabs/round和caller-saved规则，完整调用遵守原ABI。

## 实现身份

复用first-forward bind/build/first-token完整比较器与进程owner，在新controller记录精确替换及整文件逆向证明。只读关闭norm父输入、GS32支持/screen、已合法取得的源副本和量化attempt02，不读取受锁活动first-forward根，不新建checkout或重建官方程序。

实际重编共同consumer-core，把已有限参考合格的量化对象纳入新CORE，再沿原启动/TLS/fixture链接。核最终ELF的dispatcher→公开入口→GQ clone→五次新量化调用；原G五次仍到原quantize。核GS和fallback真实绑定、完整248B量化体除四个重定位word外相同、原quantize/fabs/round和常量身份。GQ误调G可能通过数值gold，故不能以输出相同代替候选真实执行。八GEMV路由、norm、独立gold及零初态仍核对，旧PASS不转移。

## 验证与预算

CPU1、GNU-j1；最多3个串行fresh原NEMU：GQ指定输出负控、G正常、GQ正常。每个100M API/600秒内部/630秒owner，全批2100秒含准备收尾；不自动延长。沿用原进程组清理与128MiB单文件上限。无新RTL、目标EMU或部署。

正常比较完整3691424B state、两侧guards、五模型/gold不变、TLS/errno12345、FCSR1、控制字和实际trap。GQ负控仅翻转末logit最低位，须在byte152476被原完整比较器拒绝，其他state完全相同。保留每个真实PID、退出、异常、输入前后SHA和清理，失败/未知不PASS。

沿原四CSR边界，method读取/dispatch及全部激活量化均在窗口；不加快路计数器。仅报原参考instret与固定输入终态，不称香山cycle/应用speedup。快路命中比例无直接证据则未知。后续目标比较由现有G/P实际结果、本次价值和排期决定。
