# 当前0f硬件：8×32配置复用普通C调用验证

外层合同：zjhwork-config-reuse-8x32-c-qualification-v1。

沿用第25条已完成矩阵：24新镜像、33目标进程、独立原文审计、完整重放、当前clean identity；8×32必须为PERFORMANCE_CANDIDATE。4×8、16×64、4×13的INCONCLUSIVE保持。本轮不改变任何性能门禁，不新测加速比。

## 保留冻结夹具与限定结论

复用未修改的entry_c_api.py主程序、Makefile、GNU/ELF验证、标量参考、逐字节128位结果、输入不变性、越界canary、CSR及O2观察器。使用已冻结config-reuse c_api.py生成器，仅通过外部适配器绑定当前0f/clean硬件。内层r2-s3-config-reuse-c-application-v1与R4标签保持，不把它们冒称为旧硬件资格。

为了保留原有严格门禁，实际运行整个16函数/48不同用例夹具，三个新EMU依次为bit100故障负控、同BIN正常恢复、正常独立重放；两个正常进程合计96调用。8×32占4公共函数（basic/reuse×vdot/RVV）、12用例、24正常调用；其他形状仅获功能旁证，不增加性能或默认采用资格。

负控必须位于本次普通C ELF实际8×32 reuse vdot函数中，vd0、word 0x0388000b、bit100。外层生成器将48个调用表条目稳定排序为8×32组在前且其dataset0/reuse/vdot为首例，其余相对顺序保留；仅重排cases.h表及manifest cases，增加外层合同/原始case摘要，输入数组、gemv.S/h、main.c和Makefile不变。主机检查证明48个完整case字典的多重集合相同、目标12例在前、无遗漏重复；实际首个vdot编码由ELF解码确认。8×32全部输出另由正常用例、标量参考和NEMU全宽差分验证。

## 固定输入、来源与时序

新公共16个leaf必须逐字节等于本轮矩阵12个config-reuse单元中的对应函数，共48次比较；8×32为12次比较。输入/函数指针表/独立对象/ELF/BIN和生成源码均用原门禁精确验证。

外层完整闭包包含新适配器/合同/parent-pins、当前矩阵build/run/audit/identity与其文件闭包、当前物理输入。内层冻结C common-inputs不加入对照BIN或外部脚本，避免把对照BIN误当实际加载BIN或破坏源码相对路径假定；外层在每阶段及每次spawn前后严格核验，最终原文审计同时验证两层。

不修改冻结C的UTC顺序检查。额外采集每次spawn/wait同boot单调包络和真实PID，验证三次串行顺序与运行身份；UTC仅有异常时保留失败，不补时间戳或放宽旧门禁。新进程最多使用4个允许CPU、实际串行、EMU_THREADS=1，原guest2M cycles及7200秒上限保持。初始负控为共用链路，其他范围扩展须独立合同。

## 通过与交付

构建、原文、物理身份、源文件快照、正常输出重放均通过后，保存独立的public/gemv.S、gemv.h、实际C调用源码与完整版本数据。只认可8×32配置复用的当前普通C调用功能；上轮1.095238×来自旧完整调用测量窗口，不转成此普通C程序的新性能数据。静态库包装、dispatcher、默认入口、额外矩阵、RTL、PPA及GitHub上传不在本轮。

所有输出使用新目录，保留失败。复用合格旧矩阵，无新矩阵EMU。每项新结果追加版本档案第26条及计分板。
