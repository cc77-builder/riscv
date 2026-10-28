# 当前0f干净全核归档适配草稿

状态：接口与35项临时夹具测试通过；实际新clean全核归档与运行原文复查尚未执行。新EMU执行数为0。归档工具不修改生产RTL。当前私有fullcore适配器已补新NEMU负例身份绑定，并同步runtime-source-lock.json；实际干净构建尚未开始。

## 方案和边界

采用独立manifest封存 + 原物理目录严格原文复查。原T17 clean_fullcore_evidence 对旧support-proof/identity/controller耦合较深，本版不改其源码或旧锁，不宣称独立无原路径语义复算。

新合同：zjh-current-clean-fullcore-archive-v1。

- physical：调用固定 current_clean_fullcore 的私有 configure/fc.audit，从原始完整轨迹重新解析14个进程；复用原clean_fullcore_evidence的私有spawn_binding/process_proof；再检查真实exit文件、stdout/stderr/run.log精确拼接、回执SHA、14进程完整集合、同镜像负控与正常恢复。
- pack：封存全部campaign原文、审计原文、直接输入、支持库构建来源、控制器/检查器源码；EMU二进制仅保留显式external SHA。此动作只形成字节包，不额外授予语义PASS。
- bytes：无需原运行目录，核对全部raw/stored hash、文件集合、source/controller源码闭包及原始路径映射。只返回BYTES_ONLY，不计作14进程语义复查。
- audit：要求原source/build/run及直接输入仍在；先确认封存包与原物理输入逐项一致，再调用固定fc.audit重新解析14进程；前后再次核对输入不变。返回LIVE_RAW_AUDIT，明确original_physical_inputs_required=true、detached_archive_semantic_recheck=false。

源码默认source-scope=hardware：另封存429硬件文件与21236递归依赖源码。合法源码symlink按其固定目标字节保存为普通payload，并记录原始link text、resolved target及内容SHA；不会在归档目录创建symlink。实际195个源码symlink已只读核对，目标全部位于硬件源码根内且内容与0f pins相同。运行日志/回执、一般输入仍禁止symlink。可显式选择direct，只封存直接输入/检查器源码，但此时完整硬件/依赖源树属于外部范围。

Git对象库、安装工具、完整generated build树仍为外部物理来源；本归档不证明新机器从零重建。单独字节PASS不能替代全核语义通过或可离线重放资格。

## 安装

将以下三文件复制到主项目：
team/optimizations/o2/integration/firstdot-v2-0f/clean-audit/

- current_clean_archive.py
- runtime-source-lock.json
- test_current_clean_archive.py

runtime-source-lock固定已copy稳定clean的五份执行脚本SHA；测试文件不影响runtime identity。新目录不改变clean identity的四份运行适配器，也不改变combination的叶级冻结输入。

## 使用命令

仅在新的14进程clean fullcore完成后使用；性能运行结束后再做重型hash/压缩与原文审计。路径必须替换为本轮真实source/run，所有output和archive必须是新的独立目录/文件。

~~~bash
CLEAN_REPO=/absolute/current/clean/source
CLEAN_RUN=/absolute/current/clean/fullcore-run
AUDITOR="$CLEAN_REPO/team/optimizations/o2/integration/firstdot-v2-0f/clean-audit/current_clean_archive.py"
AUDIT_OUT=/absolute/new/fullcore-physical-audit
ARCHIVE_OUT=/absolute/new/fullcore-archive

taskset -c 0-3 python3 -B "$AUDITOR" --repo "$CLEAN_REPO" --action physical \
 --run "$CLEAN_RUN" --output "$AUDIT_OUT"

taskset -c 0-3 python3 -B "$AUDITOR" --repo "$CLEAN_REPO" --action pack \
 --run "$CLEAN_RUN" --audit "$AUDIT_OUT" --archive "$ARCHIVE_OUT" \
 --source-scope hardware --output /absolute/new/fullcore-pack.json

python3 -B "$AUDITOR" --repo "$CLEAN_REPO" --action bytes \
 --archive "$ARCHIVE_OUT" --output /absolute/new/fullcore-bytes.json

taskset -c 0-3 python3 -B "$AUDITOR" --repo "$CLEAN_REPO" --action audit \
 --archive "$ARCHIVE_OUT" --output /absolute/new/fullcore-archive-live-recheck
~~~

脚本默认在repo的clean子目录找到已固定适配器；若工具repo与硬件source使用不同已核验路径，可显式给--clean-adapter。原始运行路径记录保持原样，audit不会改路径或改写旧结果来适配新位置。

## 检查范围

实际14进程功能、异常、全128位、DiffTest、117唯一case/124执行、六类O2覆盖、负控与恢复由稳定fc.audit原文重新解析并核对；本工具补足严格spawn/实际exit/日志原文和封存链接。以下门禁不是只读缓存PASS：完整raw日志SHA、run.log=stderr+stdout、真实exit-code与runtime/result一致、timeout/terminated拒绝、负控exit1正常exit0、negative及functional-0同镜像且PID不同且时间有序、completed-runs精确集合。

物理目录缺失或变化时，audit直接失败，不悄悄降级为BYTES_ONLY。bytes动作可单独核验归档拷贝，但报告明确无新运行且没有原文语义复查。

35项单测只在临时目录内创建合成非运行夹具，包括畸形exit、PID、timeout、缺进程、错误拼接、身份/源闭包篡改、缺载荷/额外载荷、哈希错误、symlink路径逃逸、内容漂移和字节/语义范围区分；临时数据已清理。没有把合成数据写成实际比赛运行证据。

本轮集成验证回执：/home/riscv/riscv-lab/software-import-20261026/reviews/t17/integrated-tests-02/；源码链接预检：原review目录source-link-readiness.json。运行源码锁见runtime-source-lock.json。实际新clean pack/physical/live audit全部为NOT_TESTED，需要根任务在真实campaign完成后执行。
