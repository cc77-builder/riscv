import argparse,gzip,hashlib,json,subprocess
from pathlib import Path
if not __debug__:
 raise RuntimeError('Optimized Python (-O/-OO/PYTHONOPTIMIZE) is forbidden: verification requires assertions.')
BASE_COMMIT='4669c487f3024ee5fce514c37270297f99066b2a'
JAMES_COMMIT='b806ce9c9c5228f6512474c7f2c3ab917349d7a6'
H1_MANIFEST_SHA256='73fe5f79d3209937a3278a16f8bfc70f90333fc46657de161810bcf9c2d8974a'
parser=argparse.ArgumentParser(description='Read-only pinned R3 source and archived gate trace analysis; no hardware execution.')
parser.add_argument('--repo',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path,help='New output directory; existing path is refused.')
args=parser.parse_args()
R=args.repo.resolve(strict=True)
OUT=args.output.resolve()
if args.output.exists() or args.output.is_symlink():
 raise FileExistsError('Refusing to overwrite existing evidence: '+str(args.output))
for commit in [BASE_COMMIT,JAMES_COMMIT]:
 actual=subprocess.check_output(['git','rev-parse','--verify',commit+'^{commit}'],cwd=R,text=True).strip()
 if actual!=commit:raise RuntimeError('Pinned commit is unavailable or mismatched: '+commit)
def sha(b):return hashlib.sha256(b).hexdigest()
def git(path,ref=JAMES_COMMIT):return subprocess.check_output(['git','show',ref+':'+path],cwd=R)
H='team/optimizations/o2/result-width/h1/evidence/20261021-local'
J='team/evidence/o2-o3-integration-20261020'
manifest_raw=(R/H/'manifest.json').read_bytes()
if sha(manifest_raw)!=H1_MANIFEST_SHA256:raise RuntimeError('H1 manifest SHA256 mismatch')
manifest=json.loads(manifest_raw)
OUT.mkdir(parents=True,exist_ok=False)
hm={x['path']:x for x in manifest['entries']}
jm=json.loads(git(J+'/files.json'))['files']
checked=[]
def hread(path):
 e=hm[path]; data=(R/H/'files'/e['stored']).read_bytes()
 assert len(data)==e['stored_bytes'] and sha(data)==e['stored_sha256']
 raw=gzip.decompress(data) if e['gzip'] else data
 assert len(raw)==e['bytes'] and sha(raw)==e['sha256']
 checked.append({'source':'H1','path':path,'raw_sha256':sha(raw),'stored_sha256':sha(data)})
 return raw
def jread(path):
 data=git(J+'/'+path);e=jm[path]
 assert len(data)==e['bytes'] and sha(data)==e['sha256']
 raw=gzip.decompress(data) if path.endswith('.gz') else data
 checked.append({'source':'James-O2','path':path,'raw_sha256':sha(raw),'stored_sha256':sha(data)})
 return raw
def parse(raw):
 lines=raw.decode().splitlines()
 cycles=[dict(t.split('=',1) for t in l.split()[1:]) for l in lines if l.startswith('O2_PARENT_CYCLE ')]
 assert [int(x['cycle']) for x in cycles]==list(range(len(cycles)))
 summary=next((dict(t.split('=',1) for t in l.split()[1:]) for l in lines if l.startswith('O2_PARENT_PASS ')),None)
 fu=[dict(t.split('=',1) for t in l.split()[1:]) for l in lines if l.startswith('O2_PARENT_FU ')]
 return cycles,summary,fu
hr=hread('parent-01/result.log')
jr=jread('parent-green-01/result.log.gz')
red=jread('parent-red-01/result.log.gz')
h,hs,hfu=parse(hr);j,js,jfu=parse(jr)
assert len(h)==len(j)==34356
diff=[]
for x,y in zip(h,j):
 k=[k for k in sorted(set(x)|set(y)) if k!='clocks' and x.get(k)!=y.get(k)]
 if k:diff.append({'cycle':x['cycle'],'fields':k})
assert not diff, 'Non-clock event fields differ; no PASS allowed'
def dedicated(c):
 kinds={x['accept_seq']:int(x['kind']) for x in c if x['accept']=='1'}
 post=[]
 for i,x in enumerate(c):
  if x['case'].startswith('DIV-cancel-') and x['kill_div']=='1':
   k=kinds[x['divseq']];rows=c[i+1:i+4]
   assert len(rows)==3 and all(y['case']==x['case'] and y['accept']=='0' and y['reset']=='0' and y['divseq']=='0' and y['p']=='0' and y['r']=='0' for y in rows)
   post.append({'case':x['case'],'kill_cycle':int(x['cycle']),'kind':k,'idle_cycles':[int(y['cycle']) for y in rows],'idle_clock_pulses':sum(bool(int(y['clocks'])&(1<<k)) for y in rows)})
 return post
dh,dj=dedicated(h),dedicated(j)
assert len(dh)==len(dj)==36
partial=[]
for x in h:
 if x['kill_p']!=x['kill_r'] and x['p']=='1' and x['r']=='1':
  partial.append(int(x['cycle']))
clock_h=[sum(bool(int(x['clocks'])&(1<<k)) for x in h) for k in range(3)]
clock_j=[sum(bool(int(x['clocks'])&(1<<k)) for x in j) for k in range(3)]
source=json.loads(hread('parent-01/source.json'))
source_bind={}
for p in ['src/main/scala/xiangshan/backend/exu/ExeUnit.scala','src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala','src/main/scala/xiangshan/backend/fu/wrapper/VIDiv.scala','src/main/scala/xiangshan/backend/fu/wrapper/VFDivSqrt.scala','team/optimizations/o2/parent/parent_test.cpp','team/optimizations/o2/parent/GenerateVDotElasticParent.scala']:
 digest=sha((R/p).read_bytes())
 pinned_digest=sha(git(p,BASE_COMMIT))
 assert digest==pinned_digest, 'Current audited input differs from pinned baseline: '+p
 source_bind[p]={'current_sha256':digest,'pinned_commit_sha256':pinned_digest,'archived_sha256':source.get(p),'same_as_h1_parent':digest==source.get(p)}
assert all(x['same_as_h1_parent'] for x in source_bind.values())
hold=[x for x in h if int(x['occupancy'])>0 and all(x[k]=='0' for k in ['accept','p_to_r','response','kill_p','kill_r','reset'])]
res={'hold_cycle_diagnostic':{'total':len(hold),'both_slots':sum(x['occupancy']=='2' for x in hold),'r_only':sum(x['p']=='0' and x['r']=='1' for x in hold),'clock_edges':sum(bool(int(x['clocks'])&1) for x in hold),'scope':'Activity upper-bound screening only; no assertion-state or candidate clock validation'},'status':'R3_READONLY_GATE_TRACE_AUDIT_PASS','base_commit':BASE_COMMIT,'james_commit':JAMES_COMMIT,'h1_manifest_sha256':H1_MANIFEST_SHA256,'observed_repo_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'scope':'Read-only source and archived trace analysis; no new RTL/synthesis/full-core/power execution.',
 'checked_payloads':checked,'current_source_binding':source_bind,
 'h1_summary':hs,'james_summary':js,'h1_per_fu':hfu,'james_per_fu':jfu,
 'trace_cycles':len(h),'nonclock_cycle_field_differences':diff,
 'h1_clock_edges':clock_h,'james_clock_edges':clock_j,
 'recorded_edge_difference':[a-b for a,b in zip(clock_h,clock_j)],
 'dedicated_div_kill_cases':36,'postkill_idle_samples':108,
 'h1_idle_pulses_by_kind':{k:sum(x['idle_clock_pulses'] for x in dh if x['kind']==k) for k in (1,2)},
 'james_idle_pulses_by_kind':{k:sum(x['idle_clock_pulses'] for x in dj if x['kind']==k) for k in (1,2)},
 'h1_postkill_idle_cases':dh,'james_postkill_idle_cases':dj,
 'red_tail':red.decode().splitlines()[-3:],
 'partial_kill_with_both_slots_count':len(partial),'partial_kill_sample_cycles':partial[:6],
 'warnings':['Historical O2 James green uses pre-H1 128-bit R packet; numerical comparison is archived activity only, not fresh current H1 plus gate acceptance.','All per-cycle fields apart from clocks compared, payload/metadata absent from this event schema not newly validated.','No watt/Fmax/area/CPU cycle improvement can be inferred from clock-edge reduction.']}
(OUT/'gate-trace-audit.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
(OUT/'h1-parent-tail.txt').write_text('\n'.join(hr.decode().splitlines()[-7:])+'\n')
(OUT/'james-parent-tail.txt').write_text('\n'.join(jr.decode().splitlines()[-7:])+'\n')
(OUT/'james-red-tail.txt').write_text('\n'.join(red.decode().splitlines()[-6:])+'\n')
(OUT/'james-exeunit.patch').write_bytes(subprocess.check_output(['git','diff',BASE_COMMIT,JAMES_COMMIT,'--','src/main/scala/xiangshan/backend/exu/ExeUnit.scala'],cwd=R))
print(json.dumps({k:v for k,v in res.items() if k in ['status','trace_cycles','nonclock_cycle_field_differences','h1_clock_edges','james_clock_edges','recorded_edge_difference','h1_idle_pulses_by_kind','james_idle_pulses_by_kind','partial_kill_with_both_slots_count']},ensure_ascii=False,indent=2))
