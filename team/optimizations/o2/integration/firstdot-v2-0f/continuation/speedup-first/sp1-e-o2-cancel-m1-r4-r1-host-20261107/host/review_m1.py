"""Separate binary/ELF review and frozen-closure check, no native reference loading."""
from pathlib import Path
import json,hashlib,struct,ast
N=Path(__file__).resolve().parent.parent

def required_paths():
    c=json.loads((N/'CONTRACT.json').read_text());m=json.loads(Path(c['software_manifest']['path']).read_text())
    paths={str(N/x) for x in ['CONTRACT.json','USER_INSTRUCTION.txt','launch_target.py','target_campaign.py','host_admission.py','launch_host.py','runtime/PC_CONTRACT.json','runtime/BASE_REUSE.json','host/PC_CONTRACT.json','host/fixtures_local.py','host/test_m1.py','host/review_m1.py','host/offline_old.py','host/test_image_integration.py','build-review/audit.py']}
    paths|={str(p) for p in (N/'runtime').glob('*.py')}
    paths|={str(p) for p in (N/'host').glob('*.py')}
    paths.add(str(N/'host/BASE_REUSE.json'))
    paths|={x['path'] for x in c['runtime'].values()}
    paths|={c['software_manifest']['path']}
    paths|={x['path'] for x in m['sources']}
    reuse=json.loads((N/'runtime/BASE_REUSE.json').read_text());paths|={reuse[k]['path'] for k in ['analyzer','fixture']}
    return paths

def check_closure(f):
    allowed={x['path'] for x in f['files']}
    missing=required_paths()-allowed
    if missing:raise ValueError('missing execution companion '+str(sorted(missing)))
    return len(allowed)

def review():
    c=json.loads((N/'CONTRACT.json').read_text());m=json.loads(Path(c['software_manifest']['path']).read_text())
    elf=Path(c['runtime']['elf']['path']).read_bytes();binary=Path(c['runtime']['bin']['path']).read_bytes()
    assert struct.unpack_from('<Q',elf,24)[0]==0x80000000
    assert hashlib.sha256(binary).hexdigest()==c['runtime']['bin']['sha256']
    # Independent ELF program-segment -> BIN mapping for all custom sites.
    phoff=struct.unpack_from('<Q',elf,32)[0];size,count=struct.unpack_from('<HH',elf,54)
    seg=[struct.unpack_from('<IIQQQQQQ',elf,phoff+i*size) for i in range(count)]
    for role in m['pc_roles']:
        pc=role['pc'];parts=[elf[x[2]+pc-x[3]:x[2]+pc-x[3]+4] for x in seg if x[0]==1 and x[3]<=pc and pc+4<=x[3]+x[5]]
        assert len(parts)==1 and int.from_bytes(parts[0],'little')==role['word']
        assert binary[pc-0x80000000:pc-0x80000000+4]==parts[0]
    assert (c['guard']['pc'],c['guard']['word'],c['guard']['vd'],c['guard']['bit'])==(0x80000278,0x0294000b,0,100)
    assert len(m['call_plan'])==41 and len(m['expected_retired_pc_sequence'])==77
    old=json.loads((N.parent/'sp1-e-o2-cancel-host-20261107/software/manifest.json').read_text())
    for f,g in zip(m['functions'],old['functions']):
        assert f['instruction_count']-g['instruction_count']==(-2 if f['stage']=='S0' else 0)
    assert len(binary)==old['images']['bin']['bytes']-32
    assert c['roles']==json.loads((N.parent/'sp1-e-o2-cancel-calibration-r2-20261107/CONTRACT.json').read_text())['roles']
    assert c['limits']['target_seconds']==1200 and c['limits']['host_seconds']==900 and c['limits']['outer_seconds']==2100
    assert not c['user_authorized_if_host_passes']
    src=(N/'runtime/runner.py').read_text();tree=ast.parse(src)
    assert sum(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='run_group' for x in ast.walk(tree))==1
    assert "need(parsed['status']=='SUPPLEMENT_TRACE_HIT','NOT_HIT_COMPLETED_WITHOUT_REQUIRED_CHAIN')" in src
    for forbidden in ['RUN_AUTHORIZATION.json','EXECUTION_REQUEST.txt','LAUNCH.used.json','BATCH.used.json','target-01']:
        assert not (N/forbidden).exists()
    check_closure(json.loads((N/'EXECUTION_FREEZE.json').read_text()))
    return {'status':'PASS_SEPARATE_BINARY_AND_SOURCE_REVIEW','method':'same Agent independent program-header/BIN calculation and source review; not another teammate sign-off','custom_sites_checked':17,'new_targets':0,'native_reference_loads':0,'dynamic_S0_S1_proven':False}
