import os,json,hashlib,subprocess,stat,ast,datetime
from pathlib import Path
os.sched_setaffinity(0,{1});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-k288-20261108-main/source-02')
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k288-20261108-main')
dst=root/'input-02';out=root/'preflight-01'
items=json.loads("[{\"name\":\"run.py\",\"bytes\":25519,\"sha256\":\"d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3\"},{\"name\":\"TARGET_CONTRACT.md\",\"bytes\":4024,\"sha256\":\"18f5b8b22e5be4ccd98a8cc854662376f90210e1c4dbfa55fae4402f50c07447\"},{\"name\":\"source-derivation.json\",\"bytes\":8680,\"sha256\":\"1dabc73f6a113da24991870b08866af50a72039f9ad4f80bfb8d0a485a75749a\"}]")
assert not dst.exists() and not dst.is_symlink() and not out.exists()
original={}
for x in items:
 p=src/x['name'];assert stat.S_ISREG(p.lstat().st_mode);b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];original[x['name']]=b
j=json.loads(original['source-derivation.json']);derived=original['run.py'].decode()
assert hashlib.sha256(original['run.py']).hexdigest()==j['derived_sha256']
inverse=derived
for e in reversed(j['edits']):
 assert inverse.count(e['replace'])==e['expected_occurrences']
 inverse=inverse.replace(e['replace'],e['find'])
old=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-packed-ws-20261107-main/preflight-k288-01/inputs/run.py').read_bytes()
assert len(old)==21707 and hashlib.sha256(old).hexdigest()==j['original_sha256']=='df95f6a05dbf3ffdf4314de38ecd8bce13ff3a7b63ef2583bb99d00f77e29655'
assert inverse.encode()==old
for name in ('guest_check','run'):
 def part(s):return ast.get_source_segment(s,next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name==name))
 assert part(old.decode())==part(derived)
dst.mkdir(parents=True,exist_ok=False)
for x in items:
 p=dst/x['name'];p.write_bytes(original[x['name']]);assert p.read_bytes()==original[x['name']]
base=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs')
argv=['/usr/bin/python3','-B',str(dst/'run.py'),'preflight','--reference-build',str(base/'dot16-packed-ws-20261107-main/reference-02'),'--reference-result-sha256','65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0','--prefix-core-build',str(base/'dot16-prefix-20261107-main/core-build-02'),'--prefix-smoke-result',str(base/'dot16-prefix-20261107-main/core-smoke-02/result.json'),'--output',str(out),'--k','288','--cpu','1','--max-cycles','4000000','--budget-seconds','9000','--stream-limit','16777216']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(argv,cwd=dst,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150)
(dst/'PREFLIGHT.stdout').write_bytes(p.stdout);(dst/'PREFLIGHT.stderr').write_bytes(p.stderr)
for x in items:assert (src/x['name']).read_bytes()==(dst/x['name']).read_bytes()==original[x['name']]
audit=dict(status='PREFIX_K288_STAGED_PREFLIGHT',files=items,argv=argv,started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest(),sources_unchanged=True,original_runner_inverse=True,guest_check_and_run_bytes_unchanged=True,new_emu_runs=0,new_builds=0,cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0))
if p.returncode==0:
 audit['preflight']=json.loads((out/'result.json').read_bytes())
(dst/'SOURCE_STAGING.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit));print(p.stdout.decode(errors='strict'))
if p.returncode: print(p.stderr.decode(errors='replace'),file=__import__('sys').stderr)
assert p.returncode==0,'preflight failed; no EMU started'
