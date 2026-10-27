# 精确限定的 source-bound capacity 证明

本模块只读取已完成的 clean-02/fullcore-run-01。exact-case.json 锁住71份约1MiB的小型源码、14份result/runtime/exit、父级命令/完成stdout、身份、原v1审计失败与postprocess失败链。capacity_proof.py常量锁住case SHA，外层v2归档工具还必须锁住这两份实际源码的SHA。

接口：
- process_proof(run,e)：仅接受此次绝对run路径，前后核对71份实物原文SHA；继续调用未修改的e.spawn_binding，并核其源路径及字段集合；验证14记录/真实退出/必要因果关系/实际max3命令；精确重算唯一80,119us、peak4的原墙钟异常。
- source_inputs()：返回case固定的绝对路径→SHA，不读取实物源，供封存后的bytes核验使用。capacity_proof.py和exact-case.json另列auditor-source，避免重复角色。

返回source_bound_worker_capacity=PASS是被冻结同步线程池代码和实际回执的限定结论；wall_clock_capacity始终FAIL，recorded_peak=4，OS单调实测false，原因UNCONFIRMED。没有放宽epsilon、修改timestamp或调高jobs，也不授予semantic_raw_audit PASS。外部v2须另做完整fc.audit语义检查。

输出无当前时间等动态字段，physical/pack复算可按完整字典严格相等。工具执行不写原输入、不启动EMU/NEMU、不调用fc.audit。71份精确输入若改变即拒绝；其他运行、第二个异常、时间差变化、消除旧异常、抹除旧失败均拒绝。

25项主机测试通过，其中真实case只对小文件metadata进行两次确定性核验；其余用内存/临时小文件变异检查。实际绑定调用从冻结原函数AST单独加载，未加载或执行整套raw审计。capacity-real-readonly-proof.json仅是能力/元数据证明，不是最终干净复现资格。

这三份源码/合同现在冻结：capacity_proof.py、exact-case.json、test_capacity_proof.py。后续修改应另出版本和输出，不覆盖已执行证据。
