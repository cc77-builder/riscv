# O2可行性评估证据

当前主结果是 [带分配代次归属的轨迹分析](with-allocation-fate/trace-result.json)；[命令](with-allocation-fate/command.json)绑定分析器源码SHA。

- [18项主机测试](host-01/verification.json)，保留stdout/stderr及工具源快照。
- [设计合同自动审查](contract-audit/README.md)，320组合行抽象状态检查；非RTL或真实门控验证。
- [独立数据复核](final-audit/verification.json)，123份输入字节、96窗口汇总与生产源码身份检查。
- 根目录trace-result.json是初版等待总数分析，保留原样；增强版在新目录细分1266次有用请求WAIT与9次接受前取消WAIT，不覆盖旧结果。

本轮全部是源码/合同与旧证据离线处理，没有新EMU或O2性能。开始于2026-10-18，2026-10-19续接完成；原目录日期用于保留任务身份。
