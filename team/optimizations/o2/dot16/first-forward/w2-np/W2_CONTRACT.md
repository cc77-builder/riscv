# narrow Q288 + N/P K768 完整 consumer 实验合同 v1

本合同控制一个新的源码、GNU 构建和原参考运行实验。准备状态不授予 GNU、参考、目标机或性能资格。原四臂整核运行继续使用自己的 operation、旧镜像和资源；本实验不启动 EMU。

## 规格与修改边界

保持固定六层模型、dim=288、hidden_dim=768、token=1、position=0、原准备生命周期及原完整状态布局。复用已准备的 narrow Q288 controller，其 binding SHA 为 `f67ed9e3831ecd58748ec9bcb23565ff38ce95b566a88cc1d746836306a66364`。完整 Q288 N 函数仍为 312 字节、SHA `050bc3db3e2a70bd6e5409cbf9c139868008e8ccb18776b7e0e7104e6a554b75`。

仅四个新实验 consumer 的各一处 W2 调用改变：P/PQ 从 route_fr 变为 route_paired16，N/NQ 从 route_fr 变为 route_dot16。每个完整函数可逆恢复旧生成原件，七处 Q288 路由、五处量化调用的位置、层循环、矩阵地址、FP32 运算顺序与其余控制流保持。route_matmul 保留原 n=768/d=288 条件、六层 tensor 匹配、layer×221184 packed 偏移、56 字节 context 和其他形状回退；只新增类型声明并把 FR/TA 二选一扩为 FR→旧 FR、P→K768 P、N→K768 N、其余→旧 TA。

正式 C 方法枚举、main 的方法选择字、report magic、测量边界、四次 CSR 读取及 fences 均沿旧 ABI。新 ELF/BIN、合同标识、构建前缀和完整清单区分本实验，不把同一选择字误解为同一程序。

新 K768 汇编整文件固定为 8361 字节、SHA `fbe3a93f642ec3468da92ae776e1b547c29c527d4dffc30456191b437d1272c5`；N 函数 312 字节、SHA `b4a0e512feafd3ae8ea7e4531e13e1a23b12f97d80b3b007be6c52c3bdea56be`，P 函数 1096 字节、SHA `26f972751fb9882f92118ac30b98f2d0b4d1df9225be5d9cd136e7ed5c4629d3`。完整 P guard 和 -128 回退保留。旧 candidate.o、FR/TA、norm 与量化对象照原流程核对；新 K768 单独编译后加入组合对象。

## 既有证据与新验证

K768 GNU result SHA `55aeba703f9f2f95c1c706ede993a9779b2e7e8966b2ce6678100ce750bedfc5`；原 fixture、独立重放及末组 -128 边界参考 result SHA `7d46f70b4cb105bd468577815e21c97fe9fa249fb447eeec3c977d9236e3b8c1`。两者只提供完整内核身份和其局部资格。新最终 ELF 的两个函数必须分别与实际 GNU ELF 和实际参考 ELF 逐字节相等；不能将局部 PASS 转给完整 consumer。

GNU 检查保留原完整 ELF/BIN、RAM/BSS、TLS、模型和 gold、陷阱、norm、量化、组合对象以及每个函数完整机器码核对。四新 consumer 的八个静态调用点必须准备正确 a5 指针且实际调用 route_matmul。K768 selector 对同一最终 ELF 的 FR、P、N、合法旧 TA 四个输入作有界机器字解释，检查最终目标及同一 JALR ra。外层核对输入 a5 到 callee-saved 寄存器的支配关系和不覆写，关闭未解析间接出口并排除外部直跳到片段内部。函数调用采用普通 RV64 ABI；该静态检查不声称任意指针、动态次数或全程序形式证明。selector helper 只接受实际限定子集，未知控制依赖或不支持指令即拒绝，不能按结果放宽目标地址。

原 `reference.py` 保持逐字节相同，复用原 full-state 比较器、模型、gold、ABI1400 和固定 NEMU。新增镜像须实际完成 DQ/NQ 状态字节152476扰动负控（真实 BAD94）及 P/PQ/N/NQ 四个正常运行，核对全部3,691,424字节状态、两侧 guard、完整模型不变、TLS/errno12345、精确 FCSR flags=1、陷阱 PC 与进程闭合。reference identity 必须是已固定 dot16_hardware_result；旧 forward-norm 身份不是本次执行输入。

只有新 GNU 及上述五个原参考案例均实际完成，才授予相应构建/参考资格。目标运行、应用性能、整核时序与生产默认采用均为 false；真正的性能比较仍须在共同最终 ELF 上保留较快的合格 RVV 对照。

## 资源与复现

全部生成、对象、日志和状态写新的外部 runs 输出；不新建完整 checkout，不改官方代码、原检查器或冻结证据，不修改 resident/Windows 生产源码。CPU1、绝对 nice5、单 worker 与 make -j1；不占用第五核。准备、GNU 构建和参考分别使用新输出及独立有限 operation。构建最多1200秒；五案例参考总预算最多3600秒，每例沿原100M API调用、600秒内部/630秒外部上限；单文件上限128MiB。信号/超时必须回收本操作真实子进程组，失败输出保留，不自动重复或延长。

完整 controller 的 inherited/generated 输入清单前后核验。冻结 snapshot 的 Git 对象查询只在其检查范围内绑定既有 metadata，官方 AM 的 Git 查询仍使用 AM 自身元数据。准备器的精确编辑记录可恢复完整旧 build.py，旧 derive 前缀和 reference.py 保留；用户和其他 Agent 的工作区修改不参与此次提交。
