# P1-R1：8×32 准备调用隔离结果

**P1_R1_PROBE_HOLD**。本轮仅修改软件窗外准备调用位置，稳定版本仍为 **0f＋firstdot V2＋显式 C8**。

执行者：@cc77-builder / Agent；操作ID：20261028-cc77-builder-p1-r1-condition-isolation。开始 2026-10-28T10:02:57.482181+00:00，记录 2026-10-28T20:57:21.546706+08:00。
新候选正确性：**PASS_STEADY_D0_ONLY**；steady-d0性能门槛：**HOLD**；采用：**未采用**。
实际启动EMU 4 个；找到 4 份进程记录，预算4。后处理新启动目标进程0。

## 同条件周期结果

正式统计只使用各实现4个普通计时窗；重放不重复计样本。

| 实现 | control平均cycles | candidate平均cycles | 变化 |
| --- | ---: | ---: | ---: |
| P-V | 408.75 | 409.25 | -0.1223% |
| P-R0 | 646.25 | 646.75 | -0.0774% |
| P-R1 | 487.50 | 487.25 | 0.0513% |
| P-R2 | 511.25 | 511.75 | -0.0978% |
| P-R3 | 448.75 | 447.00 | 0.3900% |
| P-R4 | 434.25 | 433.75 | 0.1151% |
| S-V | 308.50 | 310.00 | -0.4862% |
| S-R0 | 528.25 | 528.75 | -0.0947% |
| S-R1 | 386.00 | 386.50 | -0.1295% |
| S-R2 | 399.00 | 400.00 | -0.2506% |
| S-R3 | 343.00 | 344.00 | -0.2915% |
| S-R4 | 340.50 | 340.75 | -0.0734% |

| 指标 | control | candidate |
| --- | ---: | ---: |
| 同场最快RVV/S-V观测比 | 1.1037277147487845 | 1.0991935483870967 |
| 1%锚点门槛 | False | False |
| 两顺序3%收益门槛 | True | True |
| 具备后续扩围条件 | False | False |

control 锚点两窗和：{"before_forward": 605, "before_reverse": 605, "after_forward": 626, "after_reverse": 606}。

candidate 锚点两窗和：{"before_forward": 606, "before_reverse": 606, "after_forward": 631, "after_reverse": 608}。

即使本探针门槛通过，也未自动测试其他镜像或切换默认。旧273/299 cycles不作为本窗口分母。

## 面积与时序

下表是**继承的0f历史数据**，本软件轮未重新综合或STA。FU包含在父级中，面积不能相加。

| 指标 | 继承数值 |
| --- | ---: |
| FU面积 | 17298.246 μm² |
| VFEX4父级面积 | 284614.946 μm² |
| FU i2r / r2r | 1.190323 / 1.163404 ns |
| 父级全局 / vdot r2r | 3.261218 / 1.356106 ns |
| FU / 父级已报告最差slack | -0.26852 / -2.393998 ns |

Nangate45 typical/25C/1.1V; nominal 1ns, 5fF; pre-layout reference；1ns时序未收敛，这不是全核Fmax。

## 镜像、身份与覆盖

源码基点 10b71ad4bff25cd2070e775c74a4717b01602f75；生产硬件 0f12df675378556670afd0dd2153f47fcb330610。当前成果尚未提交。

| 镜像 | BIN SHA256 | ELF SHA256 |
| --- | --- | --- |
| control | 4d162f4e21a298af371c050b1b5f755161d0649d652ac67b36ff5f1f1f4e62ed | 352c927659c6c8f6c8a5ab19f8586c21955edf79ca7cfa78eae66264a2fada3d |
| candidate | 494495db689f489e33c0f14b55936c75b3ac3f0d94a28c46a2264213568a9b73 | e6e11f6e1cccf7ffd0d73a35a132f80114a48756e07988204e2cf5552c110079 |

完整工具链、GNU命令、两份源码/manifest、EMU/NEMU/flash、冻结pin和原始日志身份见配套RESULT.json及归档。
原4692 pins分为4690实物与2份历史ledger gzip内容；旧false资格不修改。当前追加ledger不作为旧运行实物输入。
其余8张镜像（steady-d1/d2、first-d0/d1/d2、native-d0/d1/d2）本候选运行均NOT_TESTED。

## 失败、修订与限制

- HOST_BUILD_FAILURE_RETAINED：首次静态构建拒绝 old symbol changed: $x；修正检查器mapping-symbol处理后用fresh build-02，不启动失败镜像。；证据 build-01/status.json
- HOST_VERIFIER_FAILURE_RETAINED：初次验证器测试失败保留；后续verify-03/04为独立fresh输出。；证据 verify-02/tests.record.json
- HOST_DISCOVERY_FAILURE_RETAINED：通用unittest发现缺少builder专用--build/--out参数；改用正确入口，旧returncode=1保留。；证据 all-host-tests-01.json
- HOST_COMPATIBILITY_FAILURE_RETAINED：新路径证书status与旧bind_retirement不兼容；启动前保留失败并补适配/真实旧trace检查。；证据 verify-04/pre-fix-bind-retirement.failure.txt

- 仅steady-d0软件准备调用隔离；不是新RTL优化，不是全应用或全数据集升级。
- 完整正确性、性能门槛、采用/扩围三项分别判断。HOLD可以正确性通过但不能获选。
- 4个正式普通样本/实现；replay不增加统计样本。partial记录不产新性能资格。
- PPA仅继承0f历史测量，无新综合/STA/功耗/布局布线/Fmax。1ns负slack仍保留。
- 旧P1运行资格false标记未修改；新的归档历史视图不冒称旧live-ledger身份检查直接通过。
- 没有成员人工验收，也没有独立机器的新干净复现；未Git提交或上传。

## 下一步

保留0f＋firstdot V2＋显式C8稳定版；停止该候选扩大，先复核本轮完整失败/未过门槛原因，不自动重试。

全部原失败和未测项保留；本轮未Git提交、未推送GitHub。

## 归档

Manifest：team/optimizations/o2/integration/firstdot-v2-0f/continuation/split-input-r1/evidence/20261028-p1-r1/manifest.json
SHA256：4604a8c369617fe3ac0d55bd4bf3d78deba568fb0777a5213ff2d21768796a32。
归档包含manifest创建前的T/final结果；带manifest身份的仓库结果与第32条记录在封存后生成，避免自引用哈希。
