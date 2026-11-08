"""Separate source/ELF review path; no tested target code, no target launch."""
from pathlib import Path
import ast,json,struct,hashlib
N=Path(__file__).resolve().parent.parent

def review():
 c=json.loads((N/'CONTRACT.json').read_text());m=json.loads(Path(c['software_manifest']['path']).read_text());b=Path(c['runtime']['bin']['path']).read_bytes();e=Path(c['runtime']['elf']['path']).read_bytes()
 assert hashlib.sha256(b).hexdigest()==c['runtime']['bin']['sha256']
 # GNU image starts at0x80000000 (checked against ELF entry and load segment).
 assert struct.unpack_from('<Q',e,24)[0]==0x80000000
 off=0x278;assert int.from_bytes(b[off:off+4],'little')==0x0294000b
 assert c['guard']=={'pc':0x80000278,'word':0x0294000b,'vd':0,'bit':100}
 assert len(m['call_plan'])==41 and len(m['expected_retired_pc_sequence'])==77
 src=(N/'runtime/runner.py').read_text();tree=ast.parse(src)
 assert sum(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='run_group' for x in ast.walk(tree))==1
 assert len(c['roles'])==2 and [x['wall_seconds'] for x in c['roles']]==[300,900]
 assert c['limits']['target_seconds']==1200 and c['limits']['host_seconds']==900 and c['limits']['outer_seconds']==2100
 assert src.index('measured=run_group')<src.index("rc=receipt(")<src.index('parsed=adapter.collect')
 assert "need(parsed['status']=='SUPPLEMENT_TRACE_HIT','NOT_HIT_COMPLETED_WITHOUT_REQUIRED_CHAIN')" in src
 assert 'except BaseException as e:' in src and "status='NOT_HIT'" in src
 assert "exclusive(N/'BATCH.used.json'" in src
 return {'status':'PASS_SEPARATE_SOURCE_REVIEW','method':'same Agent, separate static source/ELF reasoning; not teammate sign-off or a second-agent review','static_checks':10,'target_runs':0,'native_reference_loads':0,'new_coverage_proven':False,'long_DIV_hit_risk_retained':True}
