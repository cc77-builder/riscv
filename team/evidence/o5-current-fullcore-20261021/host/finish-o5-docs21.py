from pathlib import Path
import json
root=Path('/mnt/c/Code/RVInno/riscv')
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
r=json.loads((base/'runs/recheck-03/result.json').read_text())
if r['status']!='O2_G3_OFFLINE_RECHECK_INCOMPLETE' or r['suite_coverage']['missing']!=['PARTIAL_KILL']:
    raise ValueError('inspect unexpected final audit before writing docs')
if not all(r[k] for k in ('core_regression_pass','supplements_pass','original_evidence_unchanged','normal_reference_recovery')):
    raise ValueError('audit not clean apart from coverage')
brief='2026-10-21 本机 O2 基线：Linux LF、126个依赖、3430项输入及新全核构建通过。实际16次启动，选定14项作业；117个唯一矩阵用例/124次执行、5378条正常VDOT提交、bit100拒绝及恢复通过。严格重审为 INCOMPLETE，仅缺 PARTIAL_KILL；固定seed=1补测仍为0。原FAILED和两次INCOMPLETE均保留。该结果属于0484构建，不能用于随后H1整合源码的验收。O1/O2默认关闭，未推送，main不改；T17/人工ACK/新性能与PPA未完成。'
report=root/'team/docs/o5-current-fullcore-20261021.md'
text=report.read_text(encoding='utf-8')
text=text.replace('生成397个目标文件，包括先前GCC受阻的大编译单元；正在使用该EMU执行回归。','生成397个目标文件，包括先前GCC受阻的大编译单元；回归已完成，覆盖缺口见下方最终封存状态。')
text=text.replace('构建完成后应停用并移除。','已在全部EMU退出后停用并移除，cleanup回执随封存保存。')
text=text.replace('Linux HEAD、原门禁及11项运行检查器保持 `0484f1feb`','第一次修正审计时Linux HEAD、原门禁及11项运行检查器保持 `0484f1feb`')
section='''
## 最终基线封存状态

'''+brief+'''

证据：[完整清单](../evidence/o5-current-fullcore-20261021/manifest.json)、[选定审计](../evidence/o5-current-fullcore-20261021/native/runs/recheck-03/result.json)、[派生汇总](../evidence/o5-current-fullcore-20261021/native/current-g3-summary.json)。这是一份保留缺口的检查点，不是G3通过凭据。

`core-01` 的原 FAILED 来自旧负控PC门禁；`recheck-02` 使用已提交修复2b6严格重审，确认core与supplements通过，但PARTIAL_KILL缺失。随后仅按预先确定的seed=1执行两项supplements-02，未修改EMU、镜像、输入合同或覆盖阈值；仍未触发PARTIAL_KILL。`recheck-03` 重审core-01与supplements-02，结果仍INCOMPLETE。原core12项、supplements-01两项及supplements-02两项共16次启动；最终选定14项中包含1次预期bit100拒绝，其余13项正常通过，正常提交5378条。两个补测集合不能重复累计成更多唯一功能用例。

补测工具提交为 `afe589bffc1fe98785784100187d45e953b421e9`，已通过 `6ae8a9695` 合并至James_Hotten。原生HEAD切换至afe，但11项共享core驱动保持0484字节；独立审计器仍为2b6精确Git blob。explicit-seed-v1要求命令、runtime、preflight和最终Seed输出一致，旧隐式seed=0证据不重标。主机G3完整114项通过，随后仅终端周期格式兼容调整，6项seed测试重新通过；这些是主机合同检查，不补足硬件覆盖。

8GiB临时交换文件已清理，未改fstab。原构建01–05的失败/中断及build06的成功保持独立来源。v4输入包保留原0484检查器身份。归档包含原始日志、全部判决、启动器及输入包，复制前后核对审计绑定的SHA；不包含完整EMU、所有工具/依赖或可直接跨机器运行的环境。

后续H1整合另行记录。当前基线缺失PARTIAL_KILL需通过定向场景解决；不能借用上游不同源码/工具环境的H1覆盖声称此处完成，也不能依靠无界换seed筛选成功结果。
'''
report.write_text(text+section,encoding='utf-8',newline='\n')
for name, prefix in (
 ('AGENTS.md','# Current sealed baseline before H1 integration\n\n'+brief+' See team/docs/o5-current-fullcore-20261021.md. Earlier states below are historical.\n\n'),
 ('team/progress.md','# 基线封存（2026-10-21）\n\n'+brief+' 详见[复验记录](docs/o5-current-fullcore-20261021.md)。\n\n'),
 ('team/README.md','> '+brief+' [复验记录](docs/o5-current-fullcore-20261021.md)。下方为历史进展。\n\n'),
 ('OPTIMIZATION.md','> '+brief+' [复验记录](team/docs/o5-current-fullcore-20261021.md)。下方为历史进展。\n\n'),
 ('team/optimizations/o2/fullcore/README.md','> 当前基线已封存：G3 INCOMPLETE，仅缺PARTIAL_KILL。seed=1补测未改变该结论。见[最终记录](../../../docs/o5-current-fullcore-20261021.md)。下方执行中措辞为历史阶段。\n\n'),
 ('team/optimizations/o2/fullcore/REPRODUCE.md','> 2026-10-21封存：0484构建成功，03重审INCOMPLETE（PARTIAL_KILL缺失）。命令模板不代表验收通过；旧证据和后续H1源码分别绑定身份。\n\n')):
 p=root/name;p.write_text(prefix+p.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
print('O5_DOCS_UPDATED')
