# P 与 P＋GS32激活量化：首次完整消费者参考

合同：r2-s3-first-forward-psq-v1。本次仅验证新组合在固定合成模型、规定prepare后的首次完整forward；不启动目标EMU，不改变稳定默认。原P、GQ、量化原型及失败证据保留。

## 规格与比较范围

RV64G＋RVV、VLEN128、FS/VS启用；固定合成D288/H768/L6/GS32模型，token=1、position=0。新同镜像保留原P，新增PQ。P标签0x50313631；PQ私有标签0x50535131，报告MAGIC为0x5232505351563031；旧公开枚举不变。正常参考镜像UART=0，仅方法word的4B可不同；共同prepare、模型、gold与零初态相同。计时窗口包含方法读取、dispatch、全部激活量化和完整forward，排除模型生成、打包、启动和初始化。

PQ完整克隆原P cached函数，仅改函数名、五个量化静态调用及薄入口；全函数可逆恢复。七K288 GEMV仍为P，唯一W2矩阵乘仍q768_fr；W2的hq量化改为Q是预期变化。源码控制流对应19次n288＋6次n768，共315组；该数目不代表实测快路命中率。原consumer、quantize、官方upstream/runq.c、库、五模型缓冲与FP32累加顺序保持原样；既有P的HOLD_CONTEXT_VARIATION不因本次结果解除。

量化ABI为void(QuantizedTensor *,float *,int)，上下文两个指针；输入/输出/scale不别名，实际独立state数组满足。快路保持约定的VL/VTYPE和FCSR行为；不满足域时恢复入口环境，整调用tail原quantize。无栈/无math调用只描述快路；fallback沿原quantize的112B栈、fabs/round和caller-saved规则，完整调用遵守原ABI。

## 实现身份

复用已关闭GQ的prepare/derive/inspect机制及原first-forward bind/build/first-token完整比较器和进程owner，使用新的隔离source/controller/build/reference目录。原五份base源、八份量化输入和原参考SO逐一核SHA；不新建checkout或重建官方程序。prepare、build、reference在三个独立Python进程执行，避免同一解释器缓存造成实时根与冻结支持根混用。

实际重编共同consumer-core，把已有限参考合格的量化对象纳入新CORE，再沿原启动/TLS/fixture链接。最终ELF核dispatcher→公开入口→PQ clone→五次新量化调用，原P五次仍到原quantize；核七P＋一W2-FR、norm、GS和fallback实际目标地址，完整248B量化体除四个重定位word外一致，原quantize/fabs/round和常量身份。生成代码保留原C可逆与include原前缀；main为可逆扩展，不宣称字节未变。PQ误调P也可能通过数值gold，故不能以输出相同替代真实调用绑定证据。

## 验证与预算

CPU1、GNU-j1；最多3个串行fresh原NEMU：PQ指定输出负控、P正常、PQ正常。每个100M API/600秒内部/630秒owner，全批2100秒含准备收尾；不自动延长。沿用原进程组清理与128MiB单文件上限。无新RTL、目标EMU或部署，GQ或旧P PASS不转移到本次组合。

正常比较完整3691424B state、两侧guards、五模型/gold不变、TLS/errno12345、FCSR1、控制字和实际trap。PQ负控仅翻转末logit最低位，须在byte152476被原完整比较器拒绝，其他state完全相同。保留每个真实PID、退出、异常、输入前后SHA及清理，失败/未知不PASS。

沿用四CSR边界，不加快路计数器。仅报告原参考instret和固定输入终态；NEMU cycle不是香山cycle，退休指令变化不能称完整应用speedup。快路比例无直接证据则未知。此次比较只对上述合成模型与首次forward成立，不能代表全部输入、持续生成或含打包的端到端性能。是否执行后续目标周期比较，由新参考结果、合格更快基线与独立资源预算决定。
