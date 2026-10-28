# 便携离线复算

audit_portable.py 只使用参数给定的解压证据目录，可在 Linux 或 Windows 的 Python 3.10+ 中运行。不需要 Git、WSL、Yosys、STA 或原始绝对路径存在。原文中的旧路径仅用于文本比较与归一化，不会执行。

调用参数（占位目录由打包者替换）：

    python -B audit_portable.py --baseline BASELINE_ROOT --work C2_COST_ROOT --screen C2_SCREEN_ROOT --library NangateOpenCellLibrary_typical.lib --exeunit-source ExeUnit.scala --local-manifest c2-local-manifest.json --baseline-manifest baseline-cost-manifest.json --output NEW_AUDIT_OUTPUT

必须提供以下原文件，按原目录相对布局解压；不要只复制汇总表：

1. BASELINE_ROOT：旧封存 cost/parent-cost-01、cost/parent-map-01、cost/parent-sta-01 三个目录的全部143个原文件。脚本以 baseline-cost-manifest.json 检查全量集合与逐个原SHA，缺失也拒绝。旧manifest本身固定SHA 9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77。
2. C2_COST_ROOT：parent-cost-01/result.json，以及 parent-map-01 和 parent-sta-01。实际使用 map 的 summary.json、mapped.json、mapped.v、map.ys、abc.constr；STA 的 summary.json、instance-binding.json、sta-canonical.v、canonical-binding.json 和每档 timing.tcl、六类原始rpt。
3. C2_SCREEN_ROOT：screen-01/result.json、before-state-registers.json、after-state-registers.json，以及 before/after × 五档子目录的 timing.tcl、queries.json 和全部 state*.rpt、icg*.rpt。保留其他原文件更便于查阅。
4. 原始 NangateOpenCellLibrary_typical.lib（SHA 8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1）、C2 ExeUnit.scala（SHA febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6）、C2原local manifest.json（SHA 5fe7ea1cd978cf14ef371380a51e64d942673e1c62c7ac3748698418237b1428）。
5. 对C2的新证据，外层封存manifest与解压校验器负责证明全部payload原SHA。便携脚本随后独立重算其数据和合同；不能用数据自洽检查取代封存哈希。

结果 status=C2_PORTABLE_COST_AUDIT_PASS 只表示复算可信；候选筛选需另看 screening_pass、45/45 和 failures=[]。它不核对当前机器 live Git HEAD，不自动允许新构建；全核控制器仍使用原严格 live audit_cost.py 的最终审计。
