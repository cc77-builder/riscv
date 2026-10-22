# O2 G3 观察器与检查链审阅

本记录针对固定 SHA 的源码快照，检查器与运行链为交叉审阅；观察器由本审阅代理实现，因此不把其自查当作另一名成员的人类复核。

状态：INDEPENDENT_STATIC_AND_HOST_REVIEW_PASS
硬件 HEAD：b218cbc6e6b135e4ff219a902a9284a59d3c82c9

生产功能检查：移除新增 O2 观察块后，ExeUnit、ROB 与 901687a 原代码逐字节相同；VDotElastic 观察接口之前和之后的功能实现逐字节相同。新增 kill 观察节点只供 tap 读取。

已纠正的具体问题：覆盖键大小写接口不匹配、取消 DIV 输出未绑定真实占用、DIV ready 未绑定共享 ready、补充 UART 与观察前缀区分、子级派生 tap 的 elaboration 作用域、复位 printf 隐式屏蔽。详见 JSON 每项反例和修复。

编译证据：observer-elaboration-01 为真实 VFEX4 + DIV + ClockGate，在 O2_TRACE=1 下完成 Chisel/firtool elaboration（56 SV，rc=0，四生产文件哈希前后一致）。这不代替全核回归。

本目录保留 sources/、source-before/after 哈希清单、两份主机测试日志和 JSON 审阅结果。没有新增 EMU 运行，没有性能加速结论，也没有代替两位团队成员的核心接口确认。
