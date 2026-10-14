import hashlib,json,re,sys
from pathlib import Path
p=Path(sys.argv[1]); core=Path(sys.argv[2]); log=(p/'emulator-output.log').read_text()
ids={'D03','D05','D07','L04-0-8-9','L04-10-0-9','L04-10-8-0','L04-0-0-9','L04-31-31-31','L05-3-ff','clean-vs',
     'X02-m2','X02-mf2','X03-vl0','X03-vl7','X04-vstart1','X05-vill','X06-VS-off','X07-vm0','X09-v0','X11-VS-1'}
rows=re.findall(r'^T10_CASE id=(\S+) result=(\S+) cause=(\d+) all32=(\d+) pre32=(\d+)$',log,re.M)
assert len(rows)==20 and {r[0] for r in rows}==ids,'Incomplete actual guest coverage'
assert all(r[1]=='PASS' and int(r[2])==(2 if r[0].startswith('X') else 0) and r[3:]==('1','1') for r in rows),'Guest state/trap judge failed'
assert log.count('T10_CORE_SMOKE_PASS legal=10 illegal=10 all32=20 pre32=20')==1
assert 'Difftest enabled' in log and 'HIT GOOD TRAP' in log and 'HIT BAD TRAP' not in log
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
record=dict(status='VDOT_T10_CORE_SMOKE_PASS',legal=10,illegal=10,all32_checked=20,pre32_checked=20,
            source_pack_sha256=json.loads((core/'source-binding.json').read_bytes())['source_pack_sha256'],
            source_manifest_sha256=sha(p/'source-before.json'),runtime_manifest_sha256=sha(p/'runtime.sha256'),
            workload_manifest_sha256=sha(p/'workload.sha256'),complete_t11=False,team_review_signed=False)
(p/'check.json').write_bytes((json.dumps(record,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(record,sort_keys=True))