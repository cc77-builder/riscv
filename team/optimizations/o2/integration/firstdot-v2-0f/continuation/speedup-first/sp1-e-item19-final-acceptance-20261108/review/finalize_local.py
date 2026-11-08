# Local closeout only; no Git, target launch, RTL edit or default change.
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
F=Path(__file__).resolve().parent.parent;P=F.parent
R=next(x for x in P.parents if (x/'AGENTS.md').is_file() and (x/'team/docs/version-data-ledger.json').is_file())
def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
audit=read(F/'review/TERMINAL_AUDIT.json');assert audit['status']=='PASS_ITEM19_FULL_COVERAGE_AND_REPLAYS'
ledger_path=R/'team/docs/version-data-ledger.json';ledger=read(ledger_path);rid=F.name
assert not any(x.get('record_id')==rid for x in ledger['records']),'already archived'
number=len(ledger['records'])+1;now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
C=read(F/'CONTRACT.json');B=read(F/'target-01/batch.json');M=read(F/'review/HISTORICAL_METRICS.json');source=read(F/'review/PATCH_SOURCE_AUDIT.json')
assert source['status']=='PASS_FROZEN_FUNCTIONAL_SOURCE'
current_diff=subprocess.check_output(['git','diff','--','src/main/scala'],cwd=R,text=True)
assert current_diff==(F/'review/PREEXISTING_MAIN_RTL.diff').read_text(),'main RTL drift; preserve and review'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
matrix=read(F/'review/MATRIX_PENDING.json');matrix.update(status='PASS_20_OF_20',qualified_cases=20,record_number=number,terminal_audit=pin(F/'review/TERMINAL_AUDIT.json'))
row=next(x for x in matrix['cases']if x['case_id']=='o2-control');row.update(status='PASS_ORIGINAL_PLUS_M4_SUPPLEMENT_AND_REPLAYS',record_number=number,record_id=rid,original_coverage_contract_preserved=True)
save(F/'MATRIX.json',matrix)
lines=['# SP1 最终20项验收矩阵','','按原20项统计；其余19项复用已固定来源，第19项由原镜像完整检查与M4定点补测共同收口。','','|序号|用例|结果|依据记录|','|---|---|---|---|']
for i,x in enumerate(matrix['cases'],1):lines.append(f"|{i}|{x['case_id']}|PASS|{x['record_number']}|")
lines+=['','第19项原镜像16组、256次试验、1208次custom退休、131072字节寄存器检查保持；补测41调用、77次退休填补S0/S1。未借用0f槽位覆盖，未删除原检查。原1500秒合同HOLD保留，本轮使用执行前冻结的新独立预算。','','第16项C48以记录88新合同验收为准。CSR/ABI证明边界保持原合同：目标自检、DiffTest及静态叶函数审计，不能泛称每条普通指令或每个CSR均有独立观测。']
(F/'MATRIX.md').write_text('\n'.join(lines)+'\n')
M.update(status='QUALIFIED_CANDIDATE_HISTORICAL_METRICS_REUSED',record_number=number,current_progress='20/20',current_round_target_runs=5,qualification_scope='new functional acceptance; no new performance or EDA')
save(F/'METRICS.json',M)
metrics_text=(F/'review/HISTORICAL_METRICS.md').read_text().replace('最终采用状态待本轮验收闭合。','20/20验收已闭合，技术上可供采用；用户尚未切换默认。');(F/'METRICS.md').write_text(metrics_text)
result=dict(schema='sp1-final-acceptance-closeout-v1',record_number=number,record_id=rid,operation_id=C['operation_id'],operator='@cc77-builder / Agent',operator_basis='session identified account, not human signoff',started_utc=B['started_utc'],ended_utc=B['ended_utc'],recorded_at=now,status='GO_SP1_READY_FOR_USER_SELECTION_20_OF_20',source_commit=head,branch=branch,stable_default=C['stable_default'],default_changed=False,github_upload=False,candidate_source_root=source['source_root'],candidate_patch_sha256=source['patch_sha256'],runtime=C['runtime'],images=C['images'],coverage_qualified=20,coverage_required=20,item19_qualified=True,new_EMU_runs=5,new_NEMU_runs=0,new_DiffTest_reference_sessions=5,new_full_core_builds=0,new_EDA_runs=0,production_RTL_changed=False,software_image_changed_this_final_campaign=False,user_selection='PENDING_USER_SELECTION',recommendation='RECOMMEND_ORIGINAL_SP1_FOR_SPEEDUP_PRIORITY_WITH_LOCAL_TIMING_COST_DISCLOSED',new_three_metrics={k:'NOT_TESTED'for k in ['speedup','area','timing']},target_seconds_used=audit['target_seconds'],host_seconds_used=audit['host_seconds'],outer_seconds_used=audit['outer_seconds'],roles=audit['roles'],witnesses=audit['witnesses'],supplement_counts=audit['supplement_counts'],original_counts=audit['original_counts'],old_failures_preserved=True,old_1500_second_budget_status='HOLD_PRESERVED_NOT_REWRITTEN',current_contract_status='PASS_NEW_INDEPENDENT_FROZEN_BUDGET',qualification_boundary='frozen20 cases and reusable local tests, not universal proof or physical timing signoff',next_step='user may select original SP1; no automatic default or upload',evidence={k:pin(F/k)for k in ['review/TERMINAL_AUDIT.json','MATRIX.json','METRICS.json','CONTRACT.json','EXECUTION_FREEZE.json','RUN_AUTHORIZATION.json','review/OTHER19_EVIDENCE_RECHECK.json','review/COST_REUSE.json','review/PATCH_SOURCE_AUDIT.json','review/LOCAL_SOURCE_BOUNDARY.json']})
for k in ['historical_workload_metrics','historical_area','historical_five_profile_timing','timed_DIV_SQRT_qualified']:result[k]=M[k]
save(F/'RESULT.json',result)
rows=[f"|{x['role']}|{x['guest_cycles']}|{x['active_seconds']:.3f}|PASS|" for x in audit['roles']]
text=f"""# SP1 最后第19项验收收口：20/20，可供选用

记录{number}，{now}，@cc77-builder / Agent。结论：**GO，已达到本项目冻结的20/20验收条件，建议在加速比优先目标下选用原SP1候选。** 默认仍为0f＋firstdot V2＋原C8，没有自动切换，没有上传GitHub。

## 最后一个缺口如何补齐

M1/M2/M3均未命中所需重叠，全部失败/未命中记录和锁保留。依据真实侧带日志与父级仲裁源码，M4仅在测试程序scratch ft3中增加定点浮点依赖链，使F2v压力与VDOT响应重叠；没有修改RTL、VDOT输入/结果、分支、四个原相位或完整调用次数。

- S0：A seq1位于R，B seq2在17988周期进入P，17989周期双槽共存，双方完整响应与退休。
- S1：phase4指定第九次probe中，A seq76/ROB1:30存活；B seq77/ROB1:36在262616周期进入P，262617周期被ROB1:35的redirect取消；A在262624周期响应，B无响应/退休。
- 原SP1功能EMU完整复现同样覆盖，与额外观察EMU的2806条有效SP1事件逐项、逐周期相同（本镜像没有独立T13 CSR采样）；同硬件重放八类摘要完全一致。
- 补测41调用、78接受、77响应/退休、完整128位和目标端CSR/ABI判断、NEMU差分均通过。跨硬件有效输入、完整结果和CSR对照通过。
- 原镜像16组、256次试验、1208次custom退休、131072字节寄存器检查全部保留；R槽取消和256次DIV接收/响应仍由原镜像证明。两版原镜像重放分别与历史正常运行八类摘要一致。

## 最后五个角色

|角色|guest cycles|目标墙钟秒|结果|
|---|---:|---:|---|
{chr(10).join(rows)}

目标累计{audit['target_seconds']:.3f}秒，宿主{audit['host_seconds']:.3f}秒，外层{audit['outer_seconds']:.3f}秒，全部在事前7500/900/8400秒预算内。每角色900或2400秒、30万或150万guest上限满足。CPU4、进程组最多4线程、12GiB、2GiB原日志上限保持；清理通过。资源峰值是50ms采样值，不伪称内核瞬时上界。

bit100复用原镜像记录83与M4记录119的真实目标拒错；其余19项复用原已验收证据并核对选定清单哈希，没有重复无变化测试。实际C端自检＋DiffTest的CSR/ABI证据不等同独立逐指令CSR转储。

## 哪一版可以选用

独立目录 `{source['source_root']}` 中的**原P4/SP1一拍算术、两槽弹性**候选，补丁 `{source['patch_sha256']}`，功能EMU `{C['runtime']['candidate_emu']['sha256']}`。软件继续firstdot V2＋原C8。

主目录还含历史未采用P4-R1元数据Mux1H改动，不能据目录名认定它就是本次验收源码。已准备release-candidate四文件精确源码包、原补丁、构建开关和版本清单；不含P4-R1或临时侧带观察RTL。采用时按此包核对集成，保留原0f与未提交工作，不盲目reset覆盖。

## 三项指标和取舍

同镜像chain三数据集：加速比2.929725×→3.397658×，VDOT平均cycles1857→1601.25，减少13.7722%；相对VDOT吞吐约提高15.97%。batch保持3.067873×，原C8 reuse为1.095238×→1.099265×，basic仍慢于RVV。不能将微基准收益写成所有应用/LLM端到端提升。

Nangate45同约束FU面积17298.246→18322.878μm²（+5.9233%）；含DIV父级284614.946→285241.642μm²（+0.2202%）。nominal FU Q为1.268520→1.790381ns变差，父级Q为3.393998→3.337809ns略好；父级ready为0.247821→0.303064ns变差。Q=T−最差setup slack，不是全核实际时钟。负slack和旧成本合同失败保留；按事前SP0速度优先预算47/47通过。

完整负载、三数据集、原始cycles、五档STA与路径见[METRICS.md](METRICS.md)及JSON。本轮只新增功能验收，三项新测均NOT_TESTED。

## 资格边界与下一步

20/20指冻结工程矩阵全部通过，见[MATRIX.md](MATRIX.md)；不意味着所有程序/配置均被证明，不替代工艺后端签核或比赛报告、录屏、人工评审。原1500秒合同HOLD、历次FAIL/未命中保留；本轮以新独立冻结预算收口。

无需继续第19项探针。下一步属于用户选型后的默认集成与提交整理，本轮未自动执行。
"""
(F/'RESULT.md').write_text(text)
(F/'NEXT_STEP.md').write_text('# 第19项验证已结束\n\n20/20通过，本轮目标完成，不再自动追加探针。\n\n推荐加速比优先选用原SP1，保留面积和局部时序代价。默认和GitHub尚未改变。用户选型后，用release-candidate原四文件/补丁与冻结配置，隔离主目录未采用P4-R1，进行默认入口集成；软件保持firstdot V2＋原C8。诊断软件与额外侧带RTL不混入生产版本，未变验证可复用。\n')
package=read(F/'release-candidate/MANIFEST.json');package.update(status='QUALIFIED_READY_FOR_USER_SELECTION',acceptance=pin(F/'RESULT.json'),matrix=pin(F/'MATRIX.json'));save(F/'release-candidate/MANIFEST.json',package)
q=F/'release-candidate/README.md';q.write_text(q.read_text().replace('（等待最终验收）','（20/20验收通过）').replace('当前运行未结束，不能据本包提前认定20/20。','最终五角色和末尾审计通过，具备选用条件；默认尚未切换。'))
before=F/'review/before-closeout';before.mkdir(exist_ok=False)
for name in ['team/docs/version-data-ledger.json','team/docs/version-data-ledger.md','开发计分板.md','team/docs/development-route-current.md']:shutil.copyfile(R/name,before/Path(name).name)
ledger['records'].append(result);ledger['last_append_at']=now;ledger['last_append_note']=f'record {number}: item19 final acceptance,20/20,default unchanged';save(ledger_path,ledger)
relative=str(F.relative_to(R))
summary=f"""\n\n## 2026-11-08 记录{number}：SP1最后第19项通过，20/20，可供选用

@cc77-builder / Agent；操作ID `{C['operation_id']}`；执行UTC {B['started_utc']}～{B['ended_utc']}，留档北京时间{now}；基点 `{head}`，未提交。

五角色全部通过：原SP1补测与观察中性、同核重放、0f补测对照、原控制镜像SP1/0f重放。S0真实双槽和S1杀P保R在原功能EMU命中并精确复现；原16组/256试验/1208提交/131072字节覆盖保留。目标{audit['target_seconds']:.3f}秒，宿主{audit['host_seconds']:.3f}秒，外层{audit['outer_seconds']:.3f}秒，预算及清理通过。

原失败/未命中和旧预算HOLD保留，本轮新性能/面积/STA均NOT_TESTED。建议采用原SP1，最终默认选型由用户决定；没有切默认或上传。主目录历史P4-R1不等于候选，采用入口为独立原SP1源码与release-candidate。

[完整结果]({relative}/RESULT.md) · [20项矩阵]({relative}/MATRIX.md) · [候选包]({relative}/release-candidate/README.md) · [三项指标]({relative}/METRICS.md)。

路线接续：第19项验证关闭，不重复探针；用户选择后再集成默认入口和发布。
"""
with(R/'开发计分板.md').open('a')as out:out.write(summary+'\n'+metrics_text.replace('# SP1 与 0f 三项指标对照（历史实测复用）','### 本候选三项指标（历史同口径复用）',1))
with(R/'team/docs/version-data-ledger.md').open('a')as out:out.write(summary.replace(']('+relative,'](../../'+relative))
route=R/'team/docs/development-route-current.md';s=route.read_text();start=s.index('## 当前执行计划 SP0～SP6');end=s.index('## 历史路线与完成记录',start);old=s[start+len('## 当前执行计划 SP0～SP6'):end].strip()
new=f'## 当前执行计划 SP0～SP6\n\n**记录{number}：SP1-E最后第19项通过，冻结矩阵20/20，GO可供用户选用。** S0/S1实际覆盖、中性、完整数值和原镜像精确重放完成，无待补第19项探针。默认仍0f＋firstdot V2＋原C8，未上传。\n\n建议加速比优先选择原SP1一拍两槽版；四文件源码/补丁/配置已准备。主目录未采用P4-R1不能误当候选。用户选型后再集成默认及发布。chain3.397658×，FU面积+5.9233%、父级+0.2202%，FU局部时序退化保留；新SP0成本47/47通过，非全核时钟签核。\n\n[结果](../../{relative}/RESULT.md) · [矩阵](../../{relative}/MATRIX.md) · [三项指标](../../{relative}/METRICS.md) · [候选包](../../{relative}/release-candidate/README.md)\n\n'
route.write_text(s[:start]+new+'## 历史路线与完成记录\n\n### 记录115当时执行状态（历史原文保留）\n\n'+old+'\n\n'+s[end+len('## 历史路线与完成记录'):])
win=Path('/mnt/d/yanyi/riscv大赛/doc/SP1_E_最终20项验收收口_20261108');win.mkdir(exist_ok=True)
for name in ['RESULT.md','RESULT.json','MATRIX.md','MATRIX.json','METRICS.md','METRICS.json','NEXT_STEP.md']:shutil.copyfile(F/name,win/name)
shutil.copytree(F/'release-candidate',win/'release-candidate',dirs_exist_ok=True);shutil.copyfile(R/'开发计分板.md',win/'开发计分板_收口快照.md')
for name in ['TERMINAL_AUDIT.json','OTHER19_EVIDENCE_RECHECK.json','COST_REUSE.json','PATCH_SOURCE_AUDIT.json','LOCAL_SOURCE_BOUNDARY.json']:shutil.copyfile(F/'review'/name,win/name)
manifest=dict(schema='sp1-final-delivery-manifest-v1',status='PASS_LOCAL_DELIVERY',source=str(F),default_changed=False,github_upload=False,files=[pin(x)for x in sorted(win.rglob('*'))if x.is_file()and x.name!='DELIVERY_MANIFEST.json']);save(win/'DELIVERY_MANIFEST.json',manifest)
print(json.dumps(dict(status=result['status'],record_number=number,windows_delivery=str(win),default_changed=False,github_upload=False),ensure_ascii=False))
