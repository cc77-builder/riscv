# O2 致命运行错误标记隔离补丁

状态：只在本目录准备；尚未集成源码检出目录，未运行 EMU。

修改清单：

1. workloads/check.py：两个补充程序校验入口先拒绝 CRITICAL ERROR、double trap、PMA check failed。
2. recheck.py：原 core 作业及补充作业原始流增加独立致命标记门禁。
3. portable.py：archive audit_job 同样显式拒绝致命标记。它不重做全部工作负载验证，不能只依赖旧 runtime_gate。
4. test_fatal_output.py：独立新增测试，避免修改 test_workloads.py。

所有新门禁先去除完整 ANSI CSI，再做大小写不敏感匹配。普通 bit100 负控仍交由未修改的旧 runtime_gate 精确验证，不把预期 ABORT 当作新增致命类别。

验证：
- 39 项主机测试通过，包括新增致命标记、原 recheck、portable 与 workloads 测试。
- 完整真实失败原流 5,352,066 字节：三处新增门禁均明确拒绝。
- 完整真实 bit100 原流 1,054,538 字节：新增门禁放行到原负控校验；原负控仍验证 pc/vd/bit100/ABORT 链成功。
- 伪造完整 CASE_PASS/SUMMARY/GOOD TRAP 后夹入致命标记的反例均被拒绝。
- ANSI 插入关键词中、不同大小写、空白变体，以及原流读取到检查器前的集成入口均有检查。

复现日志：host-results.json、host-01.log 至 host-04.log、real-raw-results.json。
补丁：proposed.patch；基准和目标 SHA：patch-manifest.json；base/ 保留原始三文件，proposed/ 保存候选文件及主机测试依赖。

集成时仅应用 proposed.patch 的四个文件。不要整目录复制 proposed/，其中的旧 runtime_gate 及其他辅助文件仅为隔离测试依赖。先核对 patch-manifest 的 base SHA。当前运行中的 supplements-01、core-02 及原离线审计必须保留原身份；候选工具使用新提交和新证据目录。
