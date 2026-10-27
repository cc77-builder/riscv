# C3-HF 实施前协议与验证适配审查

基线0f12df675378556670afd0dd2153f47fcb330610，2026-10-25，只读审查。生产候选由主Agent实施；本Agent没有改RTL、运行EDA/仿真或Git/GitHub写入。本文件是实施前检查清单，不是候选通过证书。

## 实现范围

0f ExeUnit.scala 132行仅浮点O2 SET条件可替换。原uncerLat.asBool外层必须保留；100行RegInit、126–131 releaseUncertain、138–160所有clk_en表达式和ckAlwaysEn/ClockGate保持原样。不能从C1/C2复制owner或共享busy hold。

在clockgate循环前预先创建O2专用只读Wire解决Scala前向引用；在166–186行已有divBusy、divOutValid附近赋值：
NOT divBusy AND NOT divOutValid AND NOT elasticVDotOccupied AND NOT io.flush.valid AND NOT reset。
循环内只有vdotElastic && cfg.fuType==FuType.vfdiv时，用io.in.valid && cfg.fuSel(io.in.bits) &&该Wire作为SET；其他所有配置仍fu.io.in.fire。不复用elasticDivOccupied或dispatchedInputs.allowInput，它们含ready依赖。不要新增状态、ROB或输出接口。非EnableClockGate时辅助Wire允许被优化删除，不应新增行为。

FuConfig.scala：VidivCfg 566–581和VfdivCfg 674–691均为UncertainLatency；vfdiv对应整个VFDivSqrt，fuSel按功能单元而不是SQRT/DIV opcode，不能遗漏SQRT。O2自己的require限定VFEX4及三FU，legacy/O1的vdotElastic为false，必须留在原Scala分支。

## 可直接复用的真实测试

- team/optimizations/o2/run_rtl.py、fu/parent原生成器、原C++、4个FU负控和16个parent负控没有owner寄存器硬绑定。以新候选ROOT与全新输出执行，不能用旧绿灯转授。
- C2 parent/instrument_parent.py只增加test top的lane ready/finish与唯一divBusy观察；不读取owner，可原样用于新C3生成物。保存instrument前后hash，变化只能是测试顶层，生产模块不得改变。
- C2 c2_parent_test.cpp、check_c2_parent.py、negative_c2_parent.py依赖实际busy、实际子ready/fire/out、lane汇合及真实时钟，不依赖C2的owner编码。它们可以字节复用；C2字样应注明“沿用测试suite命名”，外层记录必须是C3源码身份。
- 仍要求13组原父级＋6组115案例补充，包含15 SQRT、48取消、14ROB、20 TE0 reset、18切换及既有观察负控；测试预期不可为了候选调整。新日志与固定旧同输入轨迹比较时核对脚本/镜像/配置身份后再声称逐拍一致。

## 必须新增或改造的检查

1. 新候选源码身份、最小diff、状态保持、调用ROOT及全程hash冻结。旧run_local只有开始记录HEAD与ExeSHA，不足以代替本轮全部输入冻结；外层应绑定新commit、全部相关源码/依赖和测试脚本。
2. C3专用只读P_F/实际FP fire相等检查，以及FP hold更新与原fire方程的逐拍关系。可在测试顶层作只读观察/断言；若在生产源增加assert，须明确只作诊断、不反馈控制，面积抽取时与原流程一样剔除simulation断言。不能以旧C2 clockStart断言名替代。
3. 新生成RTL结构审查：两个原hold寄存器仍在、owner不存在；FP SET/P输入锥不含ready/fire；其它SET和所有实际门控式保持0f。注意hold完整D锥允许经过原out.fire与cancel，因此不能要求完整D锥绝无任何ready信号。
4. C2 check_generated_cone.py默认检查两个DIV ICG.E去ready，本轮预期恰好相反（E原样保留）；必须新立查P/SET的目标，不能简单更改返回PASS。原解析器可以复用，但须确认生成名及真实寄存器更新分支，拒绝未解析符号。
5. C2 cost/screen.py和audit_portable.py硬编码C2 HEAD、owner保留及旧双hold消失。本轮必须改为新C3身份，查询FP hold、INT hold、divBusy三状态所有来源；冻结门槛不变。不得照搬C2结构资格。
6. C2 archive/final-audit/run_ppa的源码/manifest路径、C2状态字符串和候选SHA需要新外层身份，不覆盖旧封存。脚本复用与候选身份分离。

## 断言/边界不可改变

实际fire、parent.ready、child.valid和ROB捕获保持原路径；P只能用于FP hold SET。hold仍接受优先于release，RegInit reset优先。取消拍仍由旧hold开钟，不能用flush/kill提前断钟；完成只用out.fire，不用out.valid。保留匹配与无关redirect、SQRT双lane异步完成、response反压、完成/取消重叠、有效bootstrap后TE0动态reset。有效初始化前!B=>allReady不保证，不能把它当无条件组合恒等式。

所有功能/成本门槛失败应保留失败并关闭当前假设，不能自动增改gate或INT。下一步等待实际candidate diff独立审查；此时RTL功能、PPA、全核、cycle均NOT_TESTED。
