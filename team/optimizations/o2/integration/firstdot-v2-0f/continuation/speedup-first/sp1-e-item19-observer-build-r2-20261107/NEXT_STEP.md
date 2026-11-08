# 下一轮：R3拆开JVM展开与firtool转换

本轮唯一一次构建RSS_LIMIT，原锁/日志/生成物保留，不续跑或借用剩余时间。正式19/20，默认0f＋firstdot V2＋原C8。

开始第19项构建入口R3：保留R1/R2失败，评审并实现CHIRRTL生成、JVM退出、独立firtool、原Make后处理的串行入口。复用冻结编译缓存，先验证FIR与附属文件闭包及参数一致性；全部宿主准入后，同轮接受新的独立3600秒总预算执行一次构建，保持16GiB上限。失败即停、不重试、不加时；不运行EMU/NEMU、不改RTL或镜像、不做EDA、不切默认、不上传GitHub。

## 证据与范围

R2已消除Mill父进程，现有峰值仍由约10GiB展开JVM与约6.04GiB firtool并存造成。需要分离这两个阶段，不能仅重复当前入口。静态查看本地Chisel6.6.0字节码发现CIRCTTarget.CHIRRTL分支直接返回；这支持“只展开、随后退出JVM”的方向，但不代表完整生成闭包已验证。

R3先核对 `top.XiangShanStage` 的PrintControl/AddDedup/序列化及 `top.SimTop` 在Generator返回后的FileRegisters输出，评审 `--target chirrtl` 与原注解/配置的关系；使用独立小样闭环或必要宿主门验证，不能以文件存在代替一致性。仅构建入口适配，不改RTL源码。

R2现场完整firtool命令已存FIRTOOL_LIVE.json：输入为完整SimTop.fir，含内嵌annotations，保留原warn/output-annotation、repl-seq-mem、release lowering、split-verilog等选项。后续应在第一阶段JVM完全退出并回收后，才独立执行相同转换；转换成功后才进入原存储宏/版本注释/assert处理/C++编译。保留原make后处理，不生成假占位输出骗过依赖检查。

R2完整FIR已留档，但ChiselDB/Constantin/FileRegisters的尾部输出尚未执行完；不可单独复制此FIR就称闭包完整，也不能未核对便混用其他轮附属文件。R1/R2的FIR长度相同但原始哈希不同，本轮不声称其语义等价；未来固定新完整生成身份，必要时区分日志字符串/排序差异与功能差异。

复用R1监督机制、R2输入/索引逻辑核验和冻结classpath，原始index字节继续留档；不重复已通过的未变RTL局部验证。新的单次3600秒上限覆盖整轮真实生成/转换/编译，不是每阶段各3600秒。CPU4–5、make-j2、RSS16GiB、线程128、日志2GiB保持，失败即停并回收。首次准入若不能确认完整闭包，HOLD而不启动构建。

本轮未授权目标，两角色诊断仍须待新EMU成功后单独冻结和授权；完整S0/S1及必要重放保持。
