# 普通 C 中断续跑

合同：current-firstdot-c-continuation-v1。

当前旧 campaign 为 c-run-01：negative 已真实完成并按原文复算通过，recovery 在中断时停在 case 44，进程已不在。
不补造原 exit/finished，不改旧 state，不把未完成恢复测试算作通过。旧原始目录所有文件、原启动命令及实际 WORK/run_c_independent.py 的固定 SHA 绑定保存。

resume_c.py 仅新增两个正常进程：recovery → replay。保留先前 negative 的原记录、实际 cwd、命令、时间与路径。
计数明确区分：本轮 new_emu_runs=2；累计 total_launched_processes=4（含1中断）；
合格 logical_completed_processes=3，48 distinct cases、96 完成的正常调用。旧半截输出不进入96次数。

实际执行入口（所有路径应为绝对路径，输出目录须不存在）：

    python3 -B resume_c.py --action run --repo MAIN --identity IDENTITY \
      --matrix WORK/combination-build-02 --build WORK/c-build-01 \
      --prior WORK/c-run-01 --output WORK/c-run-02

脚本固定上游 entry_c_api.py 的 SHA，私有改编原 run 函数，仅替换序列、来源和计数，沿用原 spawn、normal_check、
NEMU 与 O2 检查；每个替换片段必须唯一。固有 C/固件合同不改，外层续跑合同独立。
程序固定单CPU（可用列表第二个）；不会修改 RTL、原checker、冻结组合四文件或旧证据。

运行前/后核对实际硬件、原完整输入闭包、C构建与48个leaf锚定。运行后 continuation-proof.json 为输入仍一致的封存；
它不是最终组合资格。后续必须按 record_locations 对旧negative与新normal逐条原文复算，
并与完整矩阵续跑资格联合验收。旧 matrix_qualification 或旧 C audit 不接受本合同，不伪造其新启动数。

只读API：

- inspect_prior(repo, identity, matrix, build, prior, physical=True)：验证原中断、已完成negative原文、固定源与输入，返回7项，其中末项为proof。
- qualify(repo, identity, matrix, build, run_path)：检查完成状态、计数、原目录不漂移、C重放、时间与source-lock，返回 metadata_only=true 和 record_locations；不能替代raw audit。

已实际完成：inspect-01.log / prior-inspection-01.json；5项主机测试见 tests-01.log，0 skips。
主机集成测试以真实adapter走到 spawn 前注入 StopBeforeEmu，未启动任何 EMU，
确认第一个待执行任务是正常recovery、没有重建或重跑negative，旧目录hash不变。
真实两个新EMU进程及联合raw audit尚未执行（由根任务接续启动）。
