# 第19项构建入口R2（记录107）

**宿主准入GO；唯一一次构建因RSS_LIMIT停止，结论HOLD。** 正式进度19/20，默认0f＋firstdot V2＋原C8不变。没有新EMU，也没有目标、EDA、默认切换或GitHub上传。

## 本轮完成与实际失败

- 复用冻结编译缓存，新增3项入口测试PASS：实际Make参数映射、错目标/参数/目录拒绝、原后处理保留。R1监督函数逐字节复用，不重跑未变局部RTL回归。
- 新独立build-02源码与旧副本完全相同，原Makefile未修改。入口只把原Mill的单次top.SimTop任务替换为同classpath/JVM参数的直接exec，保留存储宏、版本注释、断言转换及native构建步骤。
- 启动前及失败后，24595源码、18061外部、456保护输入无漂移；缺省资源目录未出现，HEAD和暂存条目一致。Git索引按逻辑身份核验，原R1字节FAIL未删除。
- 全核Chisel展开完成并产出约1.038GB FIR，但在firtool阶段352.629秒触发RSS_LIMIT，353.065秒完成回收；remaining=[]。峰值17232977920字节，约16.049GiB，高于16GiB上限约50.65MiB。峰值线程31，日志250327字节。
- 确认没有Mill父进程，但约10GiB生成JVM仍在等待约6.04GiB firtool。没有重试、加时或临时放宽上限。运行正常停止后未再启动任何编译/生成命令。

## 资格边界

没有build/emu及SimTop.sv，ChiselDB/Constantin尾部文件尚未生成。已有FIR和DiffTest生成文件不是完整可交付构建。R1/R2 FIR长度相同但哈希不同，不能据长度相同声称等价。新加速比/面积/时序全部NOT_TESTED；历史18格窗口与五档STA仅复用，见METRICS.md/json。

## 下一步

R3方向有静态依据：本地Chisel6.6.0的CIRCT CHIRRTL目标分支直接返回，可评审“只生成FIR及附属文件→JVM退出→独立firtool→原后处理”的串行流程。先核清XiangShan自定义phase及FileRegisters闭包，再通过必要宿主门；不简单拷贝旧不完整FIR或制造占位产物。这个方案本轮没有实施或运行。

[下一轮指令](NEXT_STEP.md) · [资源归因](RESOURCE_ANALYSIS.md) · [原始失败](build-run-01/STATE.json) · [身份复核](POST_INPUT_CHECK.json) · [历史三指标](METRICS.md)。
