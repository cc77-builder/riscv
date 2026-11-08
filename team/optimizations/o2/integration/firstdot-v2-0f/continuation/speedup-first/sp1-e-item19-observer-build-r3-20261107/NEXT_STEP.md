# 下一轮：R3-R1 小样参数修复与闭包准入

开始第19项构建入口R3-R1：修复闭包小样的参数初始化，使用原ArgParser路径，复用已通过的参数和缓存证据，集中核查FIR、注解、尾部附属文件及小样生成结果。存在真实序列化差异就HOLD，不绕过变换或弱化比较；全部准入后接入完整冻结与原Make后处理，同轮执行一次独立3600秒总预算构建，保持16GiB上限。保留原FAIL与锁，失败即停、不重试、不加时；不运行EMU/NEMU、不改RTL或镜像、不做EDA、不切默认、不上传GitHub。

## 接续边界

本轮 full-core build=0，3600秒预算使用0秒；宿主原入口失败后未继续，正式19/20。默认0f＋firstdot V2＋原C8。HOST.lock、HOST_EXECUTION_FREEZE.json、host-systemverilog/stderr.log及R1/R2原现场全部保留。不得直接再次运行本轮 host_gate.py 或把 ADMISSION 手改成 PASS。

最小修正点在 ClosureFixture.scala：原 top.SimTop 通过 ArgParser.parse 派生日志/性能选项，小样漏掉了这一步。参数正确之后仍须证明 chirrtl 序列化保留香山阶段变换；静态风险见 DESIGN_REVIEW.md。本轮没有测出 FIR 等价或不等价。

若原生 CHIRRTL 确实不能保留变换，应停止在宿主，并设计外部导出入口；不重复全核内存试错。新全核入口须覆盖全部构建阶段、环境与依赖，不可直接调用复用监督器里仍指向 R2 的 run()。
