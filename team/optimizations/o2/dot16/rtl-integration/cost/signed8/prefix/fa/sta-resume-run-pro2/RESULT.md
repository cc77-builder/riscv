# FA 单次 STA 续接结果：30 秒超时，原证据保留

## 结论

本轮严格限定的唯一一次 STA 未完成。源输入、显式名称双射及完整终端图核验通过，但 OpenSTA 子命令触及 30 秒时限，被既定控制器回收。结果保持 FAILED；没有生成 setup-checks 或五类时序路径报告，因此本轮不能给出新的时序通过、频率改进或完整 PPA 结论。

没有重跑、增加预算、重新序列化、Yosys/ABC/remap、构建、EMU 或生产默认变更。原 local-01 与 serialization-01 两份 FAILED 仍按原 SHA 保留。首席负责整个 FA 目录的统一归档，本目录不另打重复 ZIP。

## 实际运行

- 真实 operation：0250d6044ba18f5fd71831ae3131d2ce.1c1e4dfba5c51505431803f9fd594a56。
- 宿主起止：2026-11-08T04:22:42.4202224Z 至 2026-11-08T04:23:16.0423656Z。
- 宿主 duration_ms=33580，exit_code=1，cleanup_complete=true；host timed_out=false、cancelled=false。失败原因是内部 STA 的 TimeoutExpired(30s)，不是宿主 120 秒超时。
- 启动前真实64项输入全匹配；CPU3、nice5、单次STA；MemAvailable=15187228 KiB，扫描到 other_heavy=[]。该扫描不作为 K288 是否运行的判断。
- 协调进程 PGID/SID32266；唯一 STA PID/PGID32267。
- 控制器记录 elapsed_seconds=30.98153338600241、total_budget_exceeded=false，STA回收标志 cleanup_complete/reaped/group_absent 均 true。上述耗时分别保留宿主与控制器的原测量值，不混用时钟。

运行保护：Issue #2 comment6717184006，已发布后原文回读：
https://github.com/cc77-builder/riscv/issues/2#issuecomment-6717184006
仅本次CPU3/新输出保护；WORK6670578319归属与root集成仍保留。

## 冻结源与输入

实际执行新版 input-sta-02：
- fa_sta_resume.py：16785 B，SHA256 258da7f1f301d1f70c51fee9f5d213f1ee8a833d3cadef197cf0ce4226c8a074。
- STA_RESUME_CONTRACT.md：4353 B，SHA256 f81ea953a7db24fe64d45925326359e9a0ae827eda018a8af3711ce4f282e3d5。
- PLAN_ONLY.json：16512 B，SHA256 cf80fbb5908e93b4faa8beece2774c84038f31bd0ad289da9227a42230fa7d3f。
- 本次 launch.py：4471 B，SHA256 7ef4e53e3c492adfd2daeeb43b0d6aa004c62aae51e54379cbd688240873581d。

旧 source01/plan 只做准备而未运行 STA；审查发现预算计时边界后，由首席改为 source02。总60秒从execute入口开始，STA截止在Popen前固定，最终输入核验及结果落盘后再判总时限。本专家未修改首席冻结的控制器，也未重新执行默认plan。

实际网表副本2177588 B，SHA256 b1557c027795810779995e60032c3493fcb53d3f194a2cce76e516bad01d8e23，与已有序列化结果逐字节相同。原Tcl仅七处输入/报告目录替换，完整逆还原成立；原库与所有数值约束不变。

## 最终证据与独立闭合审计

原生输出：
/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01

实际只有8个文件（含source-snapshot两件），完整库存见post-audit.json。关键文件：
- result.json：1376 B，SHA256 f3fbcfcfae5052860c263fbb2bc4e342de383d461163192bc27d33184bb31c7f。
- graph-audit.json：1366 B，SHA256 f96763edf3cd0ee45e9f55925366fbe7d43bd8d8110fcf949f548e077d284953。
- inputs.json：12883 B，SHA256 da20a77b5cafadf1761e97bdabd5fc473063db714beac408992deb7bbf370995。
- sta.log：351 B，SHA256 4a53db81c247e803698a9744e4bdc123f09d92f1f3c8c6da32cf61835e0f9e11。
- timing.tcl：2534 B，SHA256 4872d430f225382f4ea951a86e7b0668933c10012548b0b4d431721b72c1b859。

sta.log 只有OpenSTA 2.0.17启动banner，无完成标志。setup-checks.rpt、r2r.rpt、i2r.rpt、r2o.rpt、i2o.rpt、ready.rpt均不存在；本目录没有伪造空报告补齐它们。缺少阶段日志，不能进一步断言超时发生在读库、读网表、链接或时序传播的哪一步；也不能把没有Error文本当作成功解析证明。

闭合只读审计 operation 0250d6044ba18f5fd71831ae3131d2ce.f0da8b8935abe69992598376a23c7f39 于2026-11-08T04:25:41.0211576Z–04:25:41.6843411Z，617ms、exit0、cleanup_complete=true：
- 64原始输入及4个生成输入全部重新计算SHA匹配。
- 结果changed_inputs=[]、inputs_unchanged=true；审计读取的结果/日志再次核SHA未变。
- SIG0和独立/proc扫描均证32266、32267两个进程组不存在。
- 新mapped.v、实际source-snapshot与冻结身份一致。
- 未执行新EDA、测试或仿真；CPU3已释放。

完整原始结果、图审计、inputs、Tcl和STA日志在本目录逐字节复制；post-audit.json保存缺失报告状态及68项输入的逐项核验。host-receipts.json保留提案、首次执行回执、最终状态、完整durable stdout/stderr（包括base64原始数据）及闭合审计回执。launch.py/launch.ps1和原字节PLAN_ONLY.json已读回一致。

## 适用范围与后续

6150个cell在已验证的全量名称双射下，220端口、10729网和26529端点仍与冻结原图严格相同。该图证明只针对既有已映射JSON，不授予RTL到完整映射网表的等价资格。面积16542.806仅为固定映射网表按原库求和的计划值，本轮没有完整STA/cost PASS。应用/整核/PPA资格继续为false。

建议将本分支暂列为“单点映射已有图证据，但限定STA未完成”。若首席认为仍值得继续，应明确新诊断或预算合同；本次失败记录不改写，原operation不重放。本专家未自行提出或启动额外映射扫描。
