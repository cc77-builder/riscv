from pathlib import Path
import json,hashlib,re,datetime
R=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
W=Path('/home/riscv/riscv-lab/o2-c2-readyless-20261025')
O=W/'version-ledger'
D=R/'team/docs'
def read(rel):return json.loads((W/rel).read_text())
candidate=read('candidate.json'); parent=read('parent-replay.json')
supp=read('supplement-01/supplement-replay.json'); neg=read('supplement-01/supplement-negative.json')
review=read('rtl-review/final-review.json')
assert candidate['head']==review['candidate_head']=='6704ce3502a7235cdb81697638c01ed23f6914f6'
assert parent['status']=='O2_PARENT_OFFLINE_TRACE_PASS'
assert supp['status']=='C2_PARENT_SUPPLEMENT_PASS'
assert neg['status']=='C2_PARENT_SUPPLEMENT_NEGATIVE_PASS'
assert all(x['detected'] for x in neg['records']) and len(neg['records'])==7
assert read('fu-02/runner.status.json')['passed']
assert read('parent-01/runner.status.json')['passed']
assert read('supplement-01/runner.status.json')['passed']
fu=(W/'fu-02/result.log').read_text().strip()
assert fu.startswith('O2_FU_PASS vectors=10022 cycles=31499 ')
fudata={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',fu)}
manifest='team/optimizations/o2/r3-div-gate/c2/evidence/20261025-local/manifest.json'
report='team/optimizations/o2/r3-div-gate/c2/RESULT.md'
d=json.loads((O/'version-data-ledger.json').read_text())
pins=json.loads((O/'version-data-ledger-sources.json').read_text())
for x in pins['files']:
 b=(R/x['path']).read_bytes()
 assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['path']
assert len(pins['files'])==58
newrels=['candidate.json','parent-replay.json','rtl-review/final-review.json','fu-02/runner.status.json','fu-02/result.log','fu-02/run.env.json','parent-01/runner.status.json','parent-01/result.log','supplement-01/runner.status.json','supplement-01/supplement-replay.json','supplement-01/supplement-negative.json','supplement-01/result.log']
newrels += ['fu-02/'+x for x in ['check-identity.log','check-cancel.log','check-wen.log','check-high.log']]
newrels += [str(x.relative_to(W)) for x in sorted((W/'parent-01').glob('check-*.log'))]
for rel in newrels:
 if '/check-' in rel:assert 'PASS' in (W/rel).read_text()
newpins=[]
for rel in newrels:
 b=(W/rel).read_bytes()
 newpins.append({'origin':str(W/rel),'work_relative_path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'future_archive_manifest':manifest})
pins['c2_local_sources']=newpins
pins['c2_archive_manifest_sha256']='PENDING_SEAL'
pins['c2_archive_manifest_path']=manifest
pins['note']='Original 58 files remain an unchanged historical snapshot. Additional C2 sources bind actual current local results; archive manifest SHA to be added after sealing.'
d['hardware_identities']['C2']={'hardware_commit':candidate['head'],'baseline_commit':candidate['baseline'],'candidate_parent_commit':candidate['parent'],'exeunit_sha256':candidate['exeunit_sha256'],'emu_sha256':'NOT_TESTED','kind':'local C2 combined busy/owner plus ready-independent gate-start; not adopted'}
rec=next(x for x in d['records'] if x['record_id']=='C2-local-RESERVED')
rec.update({
 'record_id':'C2-local-20261025-01',
 'label':'C2 去除门控启动 ready 依赖：真实 FU/父级局部资格',
 'source_ids':['c2_local'],
 'contract_refs':['team/optimizations/o2/r3-div-gate/c2/CONTRACT.md'],
 'configuration':'MinimalConfig / VLEN128 / O2_ELASTIC=1 / FUSED_INPUT=1 / O1_HANDOFF=0; T12/T13/O1/O2 traces=0; independent FU + real VFEX4; parent bootstrap and supplemental TE0 runtime resets',
 'summary':'FU 10022 vectors/full128 and 4 observed-fault negatives PASS; original parent 35075 cycles/13 groups/16 negatives PASS; supplement 2959 cycles/6 groups incl exact directed SQRT, actual lane skew and reset/cancel PASS; 7 offline observation mutations rejected.',
 'decision':'LOCAL_VALIDATION_PASS_NOT_ADOPTED; next same-constraint area/STA screen against DIV-fix0f; fullcore/cycles/PPA NOT_TESTED',
 'verification':dict(rec['verification'],numeric_rtl='PASS',fu='PASS',real_parent='PASS',fullcore_difftest='NOT_TESTED',cycles='NOT_TESTED',area_sta='NOT_TESTED'),
 'metrics':{'fu':fudata,'parent_cycles':parent['cycles'],'parent_groups':parent['groups'],'parent_accepted':parent['recomputed']['accepted'],'parent_responses':parent['recomputed']['responses'],'parent_cancellations':parent['recomputed']['cancelled'],'parent_reset_dropped':parent['recomputed']['reset_dropped'],'parent_idle_cancel_windows':sum(parent['cancel_idle_cases'].values()),'parent_idle_cancel_samples':sum(parent['cancel_idle_samples'].values()),'parent_extra_idle_clock_pulses':parent['recomputed']['cancel_idle_clock_on'],'supplement_cycles':supp['replay']['cycles'],'supplement_groups':supp['replay']['groups'],'normal_sqrt_cases':supp['normal_sqrt_cases'],'sqrt_cancel_cases':supp['sqrt_cancel_cases'],'te0_reset_cases':supp['te0_reset_cases'],'sqrt_rob_cases':supp['sqrt_rob_cases'],'sqrt_switch_cases':supp['sqrt_switch_cases'],'real_lane_skew_cycles':supp['real_lane_skew_cycles'],'real_lane_skew_cancel_cases':supp['real_lane_skew_cancel_cases'],'idle_ready_checks':supp['counts']['idle_ready_checks'],'supplement_immediate_cancel_idle_samples':supp['immediate_cancel_idle_samples'],'supplement_offline_mutations_rejected':neg['count']},
 'execution':{'fu':read('fu-02/runner.status.json'),'parent':read('parent-01/runner.status.json'),'supplement':read('supplement-01/runner.status.json')},
 'limitations':['No new fullcore/NEMU or fair-cycle comparison or synthesis/STA.','Counters across groups overlap; do not sum as unique coverage.','Supplement negative tests mutate observations offline, not RTL.','Exact directed SQRT is not exhaustive FP arithmetic qualification.','C1 structural state coding is combined in C2 but its rejected PPA result is not adopted.'],
 'raw_evidence_location':manifest,'evidence_manifest_sha256':'PENDING_SEAL','result_path':report,'source_pin_refs':[x['work_relative_path'] for x in newpins]
})
d['source_tables']['c2_local']={'source':report,'tables':[],'note':'Actual local raw receipts bound separately; report generated by main agent after sealing.'}
d['c2_local_source_pins']=newpins
d['generated_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
d['identity_notes']=[x for x in d['identity_notes'] if 'reserved' not in x.lower()]
assert len(d['records'])==18
md=(O/'version-data-ledger.md').read_text()
md=md.replace('本轮 C2 实现结果由对应新记录填写，不能套用旧成绩。','C2 已完成本轮 FU/真实父级局部验证，尚未采用；全核、周期和面积/STA 均 NOT_TESTED。')
md=md.replace('| C2 本轮 | 门控启动路径去 ready 依赖 | **待本轮真实结果填写** | NOT_TESTED | NOT_TESTED | NOT_TESTED | 不提前记采用 |','| C2 本轮 | busy/owner＋门控启动去 ready 依赖，真实接收协议保留 | PASS（含 SQRT/双 lane 增补） | NOT_TESTED | NOT_TESTED | NOT_TESTED | 局部通过，未采用；下一步成本筛选 |')
md=md.replace('| C2 | 待本轮实际候选身份 | NOT_TESTED |','| C2 | 6704ce3502a7235cdb81697638c01ed23f6914f6 | NOT_TESTED |')
insert='''### 3.5 四项目统一测试：同一旧合同，单独存档

[完整比较与限制](unified-vdot-comparison-20261017.md)；[固定条件与公开源码身份](../workloads/unified-vdot/README.md)。本机实际运行64个全核镜像，384个正式窗口。每格为“自定义窗口平均 cycles / 该实现实测 RVV÷自定义”。这里只比较当时的 T14、Jade、试水、Redoop dot8 适配，不把后来 O2/C2 插入此表作为当前排名。

| 实现 | single1 | chain256 | batch128（四路×32） | stream64 |
| --- | ---: | ---: | ---: | ---: |
| 本项目 T14 | 71 / 1.201× | 1857 / 2.930× | 453.25 / 1.496× | 1127.5 / 1.005× |
| Jade | 70 / 1.218× | 1601.25 / 3.398× | 260.25 / 2.605× | 1126.25 / 1.006× |
| 试水 | 71 / 1.201× | 1857 / 2.930× | 292 / 2.322× | 1127.5 / 1.005× |
| Redoop（dot8 适配） | 90.25 / 0.953× | 3673 / 1.481× | 744.75 / 0.929× | 1155.5 / 0.981× |

Redoop 原生工作不同，表中已计入完成共同 dot8/full128 的软件适配；窗口外辅助代码并非逐字节相同。这里没有统一 PPA、真实频率或官方排名结论。

'''
md=md.replace('## 4. 应用数据按合同保存',insert+'## 4. 应用数据按合同保存')
insert2='''### 6.1 C2-local-20261025-01：本轮真实局部验证

候选提交 **6704ce3502a7235cdb81697638c01ed23f6914f6**，生产修改仅 ExeUnit.scala，文件 SHA256 为 febbce48c4865ac5e1c7909f8494599a01ae2fee643ee53396635a0f403323a6。候选在独立检出中组合 busy/owner 保持与不依赖 ready 的门控启动；对照仍为获保留的 fix0f。真实 parent.ready、child.valid、实际接收、ROB 捕获和响应协议保留。

| 本轮层级 | 实际数据/状态 |
| --- | --- |
| FU 完整结果与控制 | PASS；10022 向量、31499 拍；23311 接受、22460 响应、739 取消、112 复位丢弃；4 项观测故障负控全部检出 |
| 原真实父级矩阵 | PASS；35075 拍、13 组；13611 接受、13122 响应、426 取消、63 复位丢弃；16 项观测故障负控检出 |
| 原严格取消关钟 | 48 空闲窗口/144 采样，额外时钟脉冲 0；原父级日志与 fix0f/C1 固定日志 SHA 相同 |
| 新真实父级增补 | PASS；2959 拍、6 组，实际 SQRT、取消、ROB、切换、TE=0 动态复位 |
| SQRT 定向与控制 | 15 正常 SQRT、48 取消、14 ROB 定向、18 切换；这些覆盖标签有交集，不求和成唯一 case |
| 双 lane 实际不同步 | 两种方向分别 56/27 拍；不同步时取消各 6 例，均来自真实内部观测 |
| 空闲/复位增补 | 620 次空闲 ready 检查；20 个 TE=0 复位场景；162 次取消后即时空闲采样 |
| 增补负控 | 7 项离线观测变异全部检出；不是 RTL 故障注入 |
| 源码及生成控制结构 | 独立审查 PASS；两处 DIV 门控启动的生成控制锥去除 ready 依赖；旧 C1 被同检查器按预期拒绝 |
| 新全核/NEMU、同镜像 cycles、面积/STA、功耗、Fmax | NOT_TESTED |

本轮只能作 **LOCAL_VALIDATION_PASS_NOT_ADOPTED**：尚未采用 C2，也没有新的加速比或时序改善结论。下一步相对 fix0f 做同约束父级面积与五档 STA 筛选，通过后再进入新全核回归。完整结果见 [C2 结果](../optimizations/o2/r3-div-gate/c2/RESULT.md)，不可变证据入口为 [C2 manifest](../optimizations/o2/r3-div-gate/c2/evidence/20261025-local/manifest.json)。manifest 的最终 SHA 由本轮封存后补入配套 JSON；实际本地来源已逐项固定。

'''
md=md.replace('## 7. 完整身份索引',insert2+'## 7. 完整身份索引')
# Preserve original drafts; integrate only the three authorized main files.
outputs={'version-data-ledger.md':md,'version-data-ledger.json':json.dumps(d,ensure_ascii=False,indent=2)+'\n','version-data-ledger-sources.json':json.dumps(pins,ensure_ascii=False,indent=2)+'\n'}
for name,contents in outputs.items():
 p=D/name
 assert not p.exists(),f'Refusing unexpected overwrite {p}'
 p.write_text(contents)
audit={'status':'VERSION_LEDGER_C2_INTEGRATION_PASS','at':d['generated_at'],'old_source_count':58,'old_source_hash_mismatches':[],'new_source_count':len(newpins),'records':len(d['records']),'c2_commit':candidate['head'],'main_files':[str(D/x) for x in outputs],'main_sha256':{x:hashlib.sha256((D/x).read_bytes()).hexdigest() for x in outputs},'manifest_sha_state':'PENDING_SEAL','source_drafts_preserved':True}
(O/'integration-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(audit,ensure_ascii=False,indent=2))
