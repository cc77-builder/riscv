from pathlib import Path
import ast,hashlib,json,re,datetime
O=Path('/home/riscv/riscv-lab/o2-c2-readyless-20261025/version-ledger')
R=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
p=O/'version-data-ledger.json'
d=json.loads(p.read_text())
md=(O/'version-data-ledger.md').read_text()
d['record_template']=json.loads(md.split('~~~json\n',1)[1].split('\n~~~',1)[0])
d['source_pins_file']='version-data-ledger-sources.json'
d['records'][7]['known_later_findings']=['Original H1 gates passed; later stricter DIV-cancel idle clock test rejected H1. Do not relabel original verification as new strict-gate PASS.']
d['identity_notes']=['O4 identity IDs refer to fixed production hardware inputs, not an assertion that the cost build used the identical full checkout/trace as G4 EMUs. Exact cost build identity remains in pinned O4 artifacts.',
 'H1 local cost run used base plus patch/snapshot; fullcore commit belongs to later fullcore build.',
 'The C2 reserved record is not an executed result and must be filled by main agent from new candidate evidence.']
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(O/'version-data-ledger-sources.json').write_bytes((O/'source-pins.json').read_bytes())
# Source consistency: only snapshot source identities, not full external artifact revalidation.
mismatches=[]
for rel,pin in d['source_pins'].items():
 b=(R/rel).read_bytes()
 if len(b)!=pin['bytes'] or hashlib.sha256(b).hexdigest()!=pin['sha256']:mismatches.append(rel)
assert not mismatches,mismatches
assert len({x['record_id'] for x in d['records']})==len(d['records'])
for ident,values in d['hardware_identities'].items():
 for key,val in values.items():
  if key in ('hardware_commit','resume_commit','production_src_tree') and val!='NOT_TESTED':assert re.fullmatch('[0-9a-f]{40}',val),(ident,key)
  if key in ('emu_sha256','new_emu_sha256') and val!='NOT_TESTED':assert re.fullmatch('[0-9a-f]{64}',val),(ident,key)
for rec in d['records']:
 assert all(i in d['hardware_identities'] for i in rec['identity_ids'])
 assert all(s in d['source_tables'] for s in rec['source_ids'])
 for v in rec['verification'].values():assert v in ('PASS','NOT_TESTED','PASS_REPORTS_TIMING_NOT_CLOSED','REJECT_THRESHOLD','PASS_ATTRIBUTION_ONLY')
# Read CSV directly copied from pinned files: selected summary points are exact.
c=d['extra_data']['team/optimizations/o1/evidence/20261018-performance-ab/files/work/results-01/comparison.csv']
assert next(x for x in c if x['scenario']=='batch')['t14_custom_mean_cycles']=='453.25'
assert next(x for x in c if x['scenario']=='batch')['o1_custom_mean_cycles']=='362.5'
c=d['extra_data']['team/workloads/o3-gemv/evidence/20261020-application/files/runs/results-03/comparison.csv']
expected={(4,8):(166.5,164),(8,32):(323.5,321.5),(16,64):(856.75,847.75),(4,13):(212,209.5)}
for x in c:
 if x['scope']=='endtoend' and x['software']=='reuse':
  assert (float(x['o1_vdot_mean_cycles']),float(x['o2_vdot_mean_cycles']))==expected[(int(x['m']),int(x['k']))]
pair=d['extra_data']['team/optimizations/o2/r3-div-gate/performance/results/paired-windows.csv']
assert len(pair)==96 and all(int(x['delta_cycles'])==0 for x in pair)
assert len(d['extra_data']['team/optimizations/o2/r3-div-gate/performance/results/samples.csv'])==478
# Markdown links are evaluated at intended integration destination team/docs/.
links=[]
for label,target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',md):
 if '://' in target or target.startswith('#'):continue
 target=target.split('#')[0]
 if target in ('version-data-ledger.json','version-data-ledger-sources.json'):
  candidate=O/target
 else:candidate=(R/'team/docs'/target).resolve()
 assert candidate.exists(),str(candidate)
 links.append(str(candidate))
for name in ('build_ledger.py','finalize_ledger.py'):
 q=O/name
 if q.exists():ast.parse(q.read_text())
report={'status':'VERSION_LEDGER_READONLY_DRAFT_AUDIT_PASS','at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
 'records':len(d['records']),'source_count':len(d['source_pins']),'source_hash_mismatches':mismatches,'expected_destination':'team/docs/',
 'markdown_links_checked':len(links),'extra_csv_rows':{k:len(v) for k,v in d['extra_data'].items() if k.endswith('.csv')},
 'checks':['source SHA and size recheck','unique IDs','full SHA format','reference integrity','T14/O1 batch exact CSV','O3 reuse e2e exact CSV','fix0f 96 delta0 CSV','478 raw CSV rows','Markdown destination links','Python AST'],
 'not_performed':['RTL edit','new simulation','EDA','historical full archive rerun','external binary verification','GitHub write'],
 'integration_notes':['Replace reserved C2 record from new actual result before user-facing final copy.','Files are drafted for team/docs; other paths resolve against repository after integration.','Full source pins record docs/instructions snapshot time; future route edits do not invalidate measured archive identity.'],
 'output_sha256':{q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in [O/'version-data-ledger.md',p,O/'version-data-ledger-sources.json']}}
(O/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
