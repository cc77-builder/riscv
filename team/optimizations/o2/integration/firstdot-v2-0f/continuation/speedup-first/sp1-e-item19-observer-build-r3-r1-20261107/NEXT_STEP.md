# 下一轮：R4 变换后FIR导出入口

开始第19项构建入口R4：在独立宿主工具中导出香山变换后的FIR及完整注解，复用原ArgParser、FileRegisters和Make后处理，不修改生产RTL。先完成小样闭包、参数和输出等价验证；全部准入后执行一次3600秒总预算、16GiB有界构建。保留原FAIL，失败即停、不重试、不加时；不运行EMU/NEMU、不改软件镜像、不做EDA、不切默认、不上传GitHub。

## 已知事实及最小修改范围

R3-R1已经修复小样配置；编译、原SystemVerilog生成、CHIRRTL生成均正常退出。失败点是真实PrintModuleName序列化差异，不再是夹具无法启动。五条内嵌注解和六个尾部文件在现有输出的离线比较中一致，但不能掩盖打印模块身份不一致。原FAIL和HOST.lock保留，不重复当前只改target的路径。

R4应保持“变换→完整序列化→JVM退出→独立firtool→原Make后处理”，只调整实验目录的构建驱动/导出工具。用XiangShanStage变换后的FirrtlCircuitAnnotation作为导出来源；核对CIRCT对CustomFileEmission及黑盒资源注解的处理，不能改用变换前的Chisel内部Circuit，也不能靠字符串替换对象标识伪造等价。

复用已正确的ArgParser初始化。小样保留现有XSLog、SyncReadMem、BlackBox、dontTouch和尾部文件，补充与导出变化直接相关的PrintControl/注解保留核查；不重跑既有FU/父级功能验证，不增加无关门禁。实际原Make入口与全核源码/依赖冻结必须在小样通过后完成；单次3600秒覆盖所有实际构建阶段，16GiB限制不变。

本轮没有授权也没有执行全核构建；不存在可恢复的R3-R1构建进程。正式19/20，第19项命中/重放仍待新观察EMU，默认0f＋firstdot V2＋原C8不变。
