# C3-HF 协议与仪器最终复核

状态：C3_HF_PROTOCOL_INSTRUMENT_REVIEW_PASS。候选77d0a1228f0da7d584d5c7375b404dcda9763cf3，ExeUnit SHA256 150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7。

源码只有约定三处改动，精确逆变换后逐字节等于0f。O2浮点hold SET单独改变，uncertainLatency、reset、release、实际门控公式、整数、busy/ROB、dispatch和legacy/O1保持。见candidate-source-review.json。

测试工具位于主仓team/optimizations/o2/r3-div-gate/c3-hf/validation，四文件最终身份见validation-freeze-02.json。旧C2刺激与checker字节复用，新runner单独绑定候选ROOT/输出与443个源码pin，最终均现场一致。

新生成检查绑定实际浮点hold赋值的SET表达式，其不经过DIV ready/fire；双hold保留，两实际门控保留ready/fire路径。实际firtool把SET内联为多行，前两次解析严格拒绝的原始日志和脚本均保存，第三次完成正确语法适配。没有为解析修改生产RTL。

只读测试顶层仪器按parent posedge采样旧状态。初次reset&&TE有效边沿之后启用；以先前采样的reset/fire/hold/release计算本拍应有hold，分别比较FP与INT。P与实际FP fire每拍一致；日志与旧C++ O2_PARENT_CYCLE一一配对，没有以“无断言失败”代替覆盖。仪器仅向独立绝对输出日志写数据，未驱动任何生产网线，前后全部生产模块哈希一致。

supplement-02实际完成2959拍，其中2958拍通过bootstrap资格；FP接受143、INT接受34、FP保持1856拍、INT保持459拍、54个FP取消、89个FP完成释放、291拍FP输出反压、40拍TE0动态reset、15个normal SQRT接受。9项坏日志观察被拒绝。上述是实际观察计数，不与原115场景相加为“更多测试案例”。

supplement-01在仿真案例开始前，新增仪器文件句柄的逻辑取反引发Verilator WIDTHTRUNC。保留全部失败以及instrument_c3_parent-v1.py.txt；只将判断改为显式==0，未关闭warning、未改生产源和刺激；新输出supplement-02通过。

四层资格独立：
1. 新源码精确范围审查。
2. 复用此前C3-G0的hold-only两种复位控制抽象，未重新运行、不计入新RTL次数；gate+hold未采用。
3. 新生成RTL的SET/门控/保持位绑定。
4. 新真实父级逐拍P/fire/hold检查及观察负控。

instrument-review.json包含上述来源及哈希。该文档由本轮协议/仪器作者出具，不能代替另一Agent的独立总审计；本Agent没有执行新综合、STA、全核或周期测试，也没有生产RTL/Git/GitHub写入。最终成本门禁及采用决定由后续实际结果判定。
