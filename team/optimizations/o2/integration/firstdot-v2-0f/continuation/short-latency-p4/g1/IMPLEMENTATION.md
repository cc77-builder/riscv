# P4-G1 实现与局部验证合同

用户已授权本轮实现；修改生产RTL前已在会话列明两个文件和信号变化。沿用 ../g0/CONTRACT.md，不改变任何成本/性能门槛。

- 修改 src/.../wrapper/VDotO2.scala：默认关闭、仅0/1的编译期开关 VDOT_P4_ONE_CYCLE，要求O2/T14，不与O1/旧trace组合。
- 修改 src/.../wrapper/VDotElastic.scala：共享原乘法/17-18-19位归约；候选P存32位已完成结果，directR保存新data/ctrl/perf，旧P搬R优先；保留默认原分支。
- ExeUnit、DIV门控、FuConfig、共享后端、NEMU、原测试和build.sc不修改。既有全核EMU不重建。
- 两槽/反压/取消/非法/身份/高96位语义不变；最早响应1拍、理想II1，不强求排队请求固定时延。
- 独立fu/parent/sqrt测试目录保留旧两拍checker；父级schema2，观察direct_r/enqueue_p/MOVE和真实子FU/钟。SQRT仅给生成的测试顶层增加只读观测，不修改生产模块。
- 115 SQRT/双lane补充场景重新绑定当前候选；不引入C2门控RTL，不转授历史PASS。
- 无综合、STA、全核、NEMU目标或Git发布。本轮数值只属于局部RTL仿真；不得将一拍响应当作新的全核加速比。

运行入口：tools/run_local.py REPO fu|parent|sqrt off|p4 NEW_ABSOLUTE_OUTPUT；每次新目录、固定输入SHA、依赖和实际二进制，失败保留。配置拒绝：tools/check_configurations.py REPO NEW_ABSOLUTE_OUTPUT。关闭模式比较：tools/compare_default_off.py BEFORE_RTL AFTER_RTL NEW_RESULT_JSON。

候选/关闭模式分别运行独立FU和真实父级；候选另跑SQRT。先完成局部资格，下一轮才考虑G2成本。所有负控是观察值/日志破坏检测，不是DUT变异或形式证明。
