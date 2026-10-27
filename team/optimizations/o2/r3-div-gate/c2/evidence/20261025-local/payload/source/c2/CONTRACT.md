# C2：DIV 门控启动去 ready 依赖的实现与验证合同

2026-10-25。用户授权本轮先说明改法和合同，再实现并做 FU／真实父级验证；不上传 GitHub。主生产基线为 0f12df675378556670afd0dd2153f47fcb330610（O2＋H1＋DIV取消关钟修复），原检出／EMU／证据保持不变。

## 1. 候选组成与改动范围

在独立 WSL 检出中以 C1 的 3be0e3d9e500bd1aa772bcc8d4f8b023a2877c66 为结构起点，组成新的 C2，而非恢复采用 C1。C1 的两份 hold 替换为已有 divBusy 与一位 divOwnerIsFp；此组合仍须相对0f验证。

唯一生产源码改动文件：src/main/scala/xiangshan/backend/exu/ExeUnit.scala。仅 O2/VFEX4 的 VIDiv 和 VFDivSqrt 使用：

~~~text
P_j = input.valid && cfg.fuSel(input)
      && !divBusy && !divOutValid && !VDotOccupied
      && !flush.valid && !reset

E_j = P_j || (divBusy && ownerIsThisFu)
~~~

启动项不引用 DIV ready、实际 fire、dispatchedInputs.allowInput 或 elasticDivOccupied。busy／owner／outvalid 的前向连接使用预先创建的 Wire，避免 Scala 前向 val 引用。两 DIV 最终 clk_en 使用上述完整表达式；原 ckAlwaysEn 覆盖优先级保留。

实际 parent.ready、child.valid、divAccept、divRobIdx 捕获、divBusy 接收／完成／取消优先级、DIV out.fire 和 VDot 门控保持原协议。保持项不加 flush/reset/cancel 遮罩，旧 busy 仍供应释放边沿。legacy/O1 分支不改变。

G0证明只适用于已固定、正确初始化的子状态机；实际全核是共享异步reset，父级同步夹具先用有效TE=1 bootstrap。生产中的断言可检查P_j==child.fire及!B=>RI&&RF，但不得用断言反馈控制或用断言代替外部门禁。

## 2. 本轮顺序与完成门槛

1. 保存本合同和变更说明，固定源码/依赖/工具；只创建独立可写候选，旧运行不复用可写目录。
2. 实现最小生产diff；独立审查生产范围、实际接受代码和取消边沿。核对G0与C1状态关系如何组合，不把旧PASS转授。
3. 运行原独立FU验证：22定向＋10000随机，完整128位、身份、异常、反压/取消，4种观察负控必须被正确拒绝。
4. 运行原真实VFEX4父级13组campaign、16种负控和严格逐拍离线复算；与已封存0f/C1旧同输入轨迹比较，要求可比字段/时钟逐拍一致。只有比较输入完全相同才作字节等价声明。
5. 新增独立父级C2补充campaign：真实SQRT、双lane独立finish可见证据、反压、匹配/无关取消、完成取消交叠；有效bootstrap后TE=0动态reset，含取消重叠与后续重启。核查完整结果及必要身份，不能仅以无assert失败作为覆盖通过。
6. 新增观测只在测试顶层/bench；若修改生成测试顶层SV，需保存pre/post及逐模块hash，生产生成模块不得被改。保留原13组和16负控语义；新checker必须用受控坏观察验证可拒绝。
7. 生成RTL结构审查：两个DIV ICG.E当前周期组合锥不包含ready、allowInput、elasticDivOccupied；寄存器D端的历史依赖不计为当前周期门控路径。不得靠伪造波形/改名隐藏路径。
8. 固定候选身份、原始命令/日志/失败、全部实际覆盖、局限与版本数据档案。本轮到局部功能关卡止，不启动综合/STA、全核/NEMU或性能测试。

任何功能／时钟／身份／取消或覆盖门禁失败必须修正并保留原失败；不能放宽严格空闲关钟或忽略SQRT/lane证据。模型反例若暴露G0环境不成立，则停止门控改写。

## 3. 后续筛选合同（本轮不执行）

如本轮通过，再相对0f进行同约束父级综合和五档STA：控制状态D端nominal最差≤1.737526ns；父级r2r/i2r、VDot相关、ready、各ICG到达≤基线101%，基线正slack门控保持非负；面积≤284614.946×1.001、未知单元0。继承旧内部筛选线，不宣称官方门槛。通过才进入新身份全核/NEMU与同镜像周期比较。

C2局部PASS不代表面积时序收益、整核验收、加速比提高或最终采用。C1既有否决事实、原1ns未收敛结果均保留。

## 4. 版本数据档案

建立单一实验数据索引，按可比较合同/镜像/边界分组，记录各版完整身份、功能资格、cycles/加速比、面积/时序、取舍和证据链接；未测记NOT_TESTED，失败和弃用保留。今后每一轮实测追加，不覆盖历史，不把不同镜像/窗口或FU/父级/全核结果拼成一条排名。此索引不替代当前路线、计分板或各实验原文。
