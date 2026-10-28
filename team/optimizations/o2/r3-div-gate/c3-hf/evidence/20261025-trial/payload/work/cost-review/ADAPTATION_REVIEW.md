# C3-HF 成本流程最小适配与脚本说明

本轮只做脚本与主机拒错检查，没有执行新的生成、综合、STA 或 EMU。用户授权的一次候选为77d0a1228f0da7d584d5c7375b404dcda9763cf3，生产源码SHA 150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7。脚本可用不等于候选功能/成本通过，实际成本结论须等新数据。

## 直接复用与重新适配的边界

候选内O4的 elaborate.py、synthesize.py、timing.py、GenerateVDotCost.scala、canonical.py、compact.py原样使用。真实入口是 mill 的 vdotCost.runMain team.vdot.GenerateVDotCost parent；它实例化MinimalConfig(1)的CommonParentCostTop，实际VFEX4内含VFDivSqrt、VIDiv、VDot和三门控，暴露完整生产接口。不能换成ParentProbeTop或C2补充测试顶层。

新cost/run_ppa.py派生C2控制器，只更换本轮冻结身份与局部资格，保留126递归依赖、143基线文件、工具动态库/Liberty、源码前后哈希、单次生成/综合/五档执行。父级生成元数据必须为新commit、o2/parent和全部固定flags；SV文件集合须与0f生产边界一致。

新cost/screen.py保留五档45项与所有阈值。C2的两态查询及“旧hold必须消失”条件不可复用；新control_contract.py在两侧固定查询同三态，检查位宽、Q/QN驱动、DFF、标量D、canonical绑定、三个D端互异，owner不得出现。

新cost/audit_cost.py保留原文解析、Liberty面积重算和45项独立分类，独立实现三态绑定而非调用screen的bind_states。它从真实原始报告和mapped.json重算，不直接相信screen结果。实际运行由另一独立审计Agent负责；作者的主机测试不代替该审计。

## 3状态及ICG如何绑定

| 固定语义 | 含义 | 0f nominal既有arrival |
| --- | --- | ---: |
| dut.elasticDivOccupied_divBusy | 共用busy D | 0.870094ns |
| dut.uncer_en_reg | 浮点hold D | 1.930584ns |
| dut.uncer_en_reg_1 | 整数hold D | 1.506153ns |

旧canonical编号c197349/c197351/c197350仅用于识别旧档，绝不直接查询新网表。每侧从语义net的驱动DFF追到自身canonical映射，得到D端。两侧三态每档都查，nominal以三者最大值过≤1.737526ns，不能只看FP改善而漏掉INT或busy退化。

三个门控按本版mapping中的dut.ClockGate.impl、dut.ClockGate_1.impl、dut.ClockGate_2.impl分别映射到FP、INT、VDot的E。定向查询每版5档、每档3状态+3ICG，共60份rpt。45比较项为每档六条常规路径加三个ICG；状态报告不混计进45。

## 约束和门禁

固定工具/库和约束见cost/CONTRACT.md，完整复制旧口径：Nangate45 typical、ABC1000ps/BUF_X1/5fF、TE0、理想时钟、5K wire-load、0.05ns时钟uncertainty/transition、0.1ns IO；五档(1,5)/(.5,5)/(2,5)/(1,1)/(1,20)。

同档每条arrival≤基线101%；基线非负ICG slack须非负；控制最差≤1.737526ns；父级面积≤284899.560946。端口/库/规范化map.ys/ABC约束/STA约束前缀必须相同；3ICG、未知单元0，所有路径/数值/状态完整。两边原始最坏起点不同也保留真实报告，不加false path或人为固定较好起点。

baseline固定0f原manifest 9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77；新C3使用新局部资格，C2 manifest绝不冒充它。标准脚本工具exit0和C3_HF_SCREEN_PASS是不同概念；实质超线写C3_HF_SCREEN_REJECT且不进入后继。全父级1ns未收敛不是本轮新增阈值；没有整核频率/功耗/官方分数结论。

## qualification.json接口

文件由root在实际局部回执齐全后组装并一次冻结，建议WORK/cost-qualification.json：

- schema固定C3_HF_COST_QUALIFICATION_V1。
- candidate包含repo、head、exeunit_sha256、baseline，必须匹配写死的77d0/150baa/0f；当前Git HEAD/干净状态和实际ExeUnit同时校验。
- checks准确包含fu、parent、supplement、state、source_scope、replay、negative_controls、audit八类。每项path、sha256、assertions（keys数组与equals值）；回执必须显式passed=true或带独立PASS词的status，类型和值严格一致。audit还必须有candidate_head或candidate.head匹配新候选。
- source_manifests准确包含fu、parent、supplement三份实际source.json的path与sha256。parent/supplement必须绑定当前ExeUnit SHA；逐个源文件核对，不改原manifest。
- inputs为其余原始局部回执、脚本和源输入的绝对路径→SHA；不能为空。所有输入在阶段前后复核。
- source.json若包含真实外部验证源码，只允许固定MAIN的c2/parent目录、c3-hf/validation目录及唯一c2/check_generated_cone.py文件。每个外部文件必须同时在inputs用解析后的绝对路径显式声明同SHA；拒绝其他目录、未声明源和符号链接逃逸。

qualified后脚本自身、cost/CONTRACT.md和上级C3-HF合同也纳入输入冻结。不要在运行期间修改这些文件。

## 预定命令（这里只记录，未运行EDA）

在MAIN中用完整路径调用新控制器，repo参数必须指向独立候选：

    python3 -B team/optimizations/o2/r3-div-gate/c3-hf/cost/run_ppa.py \
      --repo /home/riscv/riscv-lab/o2-c3-hf-20261025/repo \
      --work /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-01 \
      --baseline /home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025 \
      --source-repo /home/riscv/riscv-lab/zjhwork2-review-20261018/repo \
      --qualification /home/riscv/riscv-lab/o2-c3-hf-20261025/cost-qualification.json

标准结果C3_HF_STANDARD_PPA_COMPLETE_AWAIT_SCREEN后，screen.py使用相同--work/--baseline/--source-repo/--qualification，再加--output WORK/cost-01/screen-01。它只做定向STA和筛选，不建全核。

独立audit_cost.py参数：--work WORK/cost-01 --baseline OLD_BASELINE --screen WORK/cost-01/screen-01 --output 新审计目录 --qualification WORK/cost-qualification.json。所有输出拒绝覆盖已有目录；基础设施失败保留原attempt，不把失败改写为PASS或重新综合挑好结果。

## 已完成主机检查与限制

host-tests-02实际23项unittest通过；其中一项调用原66个观察/门槛负控（不与23相加包装覆盖率）。同时用旧C1/C2真实screen.json重现15/45和25/45失败，确认未松动门槛。另覆盖缺hold、常量/非DFF/无D、错canonical、重复状态、owner、旧或错误候选、脏树、缺局部类别/源码清单、假PASS/类型错、audit错身份、原文SHA漂移、外部源未pin/越界/符号链接逃逸。

第一次host-tests-01因测试文件中换行转义导致SyntaxError，未导入测试也未执行任何EDA；源快照、日志、退出1保留。只修复测试夹具的字符串表达式后使用新02日志完成检查。没有以此修改RTL或门槛。

本目录sources.json固定最初查阅的旧工具来源与五份本轮实际选取的封存资料；脚本最终身份另见implementation-freeze.json。旧成本脚本、证据和生产基线都未改。最终结果、归档压缩和版本档案由root按真实运行另行维护。
