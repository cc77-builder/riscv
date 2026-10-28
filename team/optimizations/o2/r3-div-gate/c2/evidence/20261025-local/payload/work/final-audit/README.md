# C2 最终只读审计

结论：C2_FINAL_READONLY_AUDIT_PASS。生产候选为6704ce3502a7235cdb81697638c01ed23f6914f6，保留基线为0f12df675378556670afd0dd2153f47fcb330610。

- 实际命令回执：FU、原父级、补充父级均完成；仅预期观察故障注入返回1，对应严格拒错检查器返回0。
- 核验1119份去重输入、1298次源码哈希比较、118份生成物清单条目与6份向量/可执行文件清单条目；126个依赖HEAD及当前已跟踪文件清洁状态通过。
- 原父级35075周期原文与C1及原关钟修复运行三方逐字节一致。原修复运行时HEAD是4669c4且有未提交修复，398份生产源码快照逐项匹配后续0f；不把该原运行冒称在0f提交上执行。
- 原父级和补充2959周期分别重放身份/控制，38034个周期独立核对前缀计数守恒，结束时无悬挂事务。
- 补充顶层只增加3个输出和3条只读层级assign；56份生产生成模块逐字节相同。
- 27项负控=FU4项与原父级16项运行时观察值破坏+7项离线日志变异。此次审计重新执行的是离线检查；没有新RTL变异或硬件仿真。

详细数字以audit.json为准；audit.py拒绝覆盖既有audit.json。复现选择新输出目录：

```bash
python3 -B /home/riscv/riscv-lab/o2-c2-readyless-20261025/final-audit/audit.py \
  --work /home/riscv/riscv-lab/o2-c2-readyless-20261025 \
  --baseline-repo /home/riscv/riscv-lab/zjhwork2-review-20261018/repo \
  --output-dir /tmp/c2-audit-new
```

检查器的输入仍需保持固定，输出目录必须新鲜。检查脚本只调用只读Git/Python离线检查，不调用编译、仿真、综合、STA或GitHub。

审计前几次运行遇到历史source.json未包含check_trace.py、PowerShell修补命令引号错误及JSON整数字典键比较差异。已分别保留原因和修正回执；补用原封存source-candidate中的checker哈希及真实replay的checker_sha256，未修改任何输入/原日志/验收标准。最终完整运行退出码0，见audit-command.json。

当前结论只覆盖固定源码、FU/父级测试及证据一致性。完整128位和定向SQRT数值由原C++仿真检查，离线轨迹复核侧重控制/身份；本轮不构成C2全核/NEMU、面积、时序、功耗、性能或最终采用结论。
