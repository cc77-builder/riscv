"""Independent byte/schema checks only. Never import/run build, host, target or libraries."""
from pathlib import Path
import datetime, hashlib, json, struct
N=Path(__file__).resolve().parent.parent
P=N.parent
D=Path('/home/riscv/riscv-lab/speedup-first-20261103/sp1-ab/candidate')
def read(p): return json.loads(Path(p).read_text())
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def verify(q):
    assert pin(q['path'])==q, q['path']
    return q
m=read(N/'software/manifest.json'); b=N/'build-review/attempt-02'
checked=[verify(v) for v in m['sources']+list(m['images'].values())+[m['build_result']]]
build=read(b/'RESULT.json'); checked += [verify(v) for v in build['outputs']]
commands=read(b/'COMMANDS.json'); assert len(commands)==14 and all(v['exit_code']==0 for v in commands)
deps=read(b/'DEPENDENCIES_BEFORE.json'); assert deps==read(b/'DEPENDENCIES_AFTER.json')
checked += [verify(v) for v in deps]
assert build['status']=='PASS_GNU_BUILD_ONLY' and build['target_runs']==build['native_reference_loads']==0
for q in m['sources']: assert Path(q['path']).read_bytes()==(b/'source'/Path(q['path']).name).read_bytes(), q['path']
audit=read(b/'OBJECT_AUDIT.json'); verify(audit['manifest'])
assert audit['status']=='PASS_OBJECT_AND_LINK_AUDIT' and not audit['target_executed']
elf=Path(m['images']['elf']['path']).read_bytes()
assert elf[:6]==b'\x7fELF\x02\x01'
phoff=struct.unpack_from('<Q',elf,32)[0]
phsize,phnum=struct.unpack_from('<HH',elf,54)
segments=[struct.unpack_from('<IIQQQQQQ',elf,phoff+i*phsize) for i in range(phnum)]
def at(pc,size):
    matches=[elf[offset+pc-va:offset+pc-va+size] for typ,flags,offset,va,pa,sz,mem,align in segments if typ==1 and va<=pc and pc+size<=va+sz]
    assert len(matches)==1,(hex(pc),size)
    return matches[0]
roles={v['pc']:v for v in m['pc_roles']}; assert len(roles)==17
raw_custom=[]; raw_dependency=[]
for f in m['functions']:
    start,end=f['start_pc'],f['end_pc']; raw=at(start,end-start)
    assert hashlib.sha256(raw).hexdigest()==f['sha256']
    words=list(struct.unpack('<'+'I'*(len(raw)//4),raw)); assert len(words)==f['instruction_count']
    raw_custom += [start+4*i for i,w in enumerate(words) if w&127==11]
    if f['stage']=='S1':
        branch=f['branch_pc']; assert struct.unpack('<III',at(branch-8,12))==(0x01d282b3,0x0262d2b3,0x00729463)
        assert words.count(0x40af8eb3)==1
        assert start+4*words.index(0x40af8eb3)<branch-8
        raw_dependency.append(dict(name=f['name'],phase=f['phase'],branch_pc=branch,sub_word='40af8eb3',add_word='01d282b3',divu_word='0262d2b3'))
assert set(raw_custom)==set(roles) and len(raw_custom)==17
for pc,r in roles.items(): assert struct.unpack('<I',at(pc,4))[0]==r['word']
assert len(m['functions'])==9 and len(raw_dependency)==4
assert len(m['call_plan'])==41 and sum(len(c['expected_retired_pcs']) for c in m['call_plan'])==77
assert [pc for c in m['call_plan'] for pc in c['expected_retired_pcs']]==m['expected_retired_pc_sequence']
assert len([c for c in m['call_plan'] if c['probe']])==4
assert all(r['eligible_commit_ordinal']==8 for r in roles.values() if r['stage']=='S1' and r['packet']=='A')
x=bytes.fromhex(m['input_bytes']); signed=lambda v:v-256 if v>=128 else v
s=sum(signed(x[i])*signed(x[16+i]) for i in range(8))
assert ((s&0xffffffff).to_bytes(4,'little')+bytes(12)).hex()==m['expected_dot128']
c=read(N/'host/PC_CONTRACT.json');verify(c['software_manifest'])
assert c['pc_roles']=={str(r['pc']):r for r in m['pc_roles']}
assert c['expected_retired_pc_sequence']==m['expected_retired_pc_sequence'] and c['call_plan']==m['call_plan']
assert c['images']==m['images'] and c['expected_commits']==77
selector=read(N/'host/selector-check-02/RESULT.json');assert selector['exit_code']==0
for name,sha in selector['source_sha256'].items():assert pin(N/'host'/name)['sha256']==sha
judge=read(N/'host/judge-check-01/RESULT.json'); assert judge['status']=='PASS_HOST_C_JUDGE' and all(q['exit_code']==0 for q in judge['commands'])
for name,sha in judge['source_pins'].items(): assert pin(name)['sha256']==sha
old=read(P/'sp1-ab/build-inputs-final.json');by_path={v['path']:v for v in old['files']}
rtl=[]
for rel in ['src/main/scala/xiangshan/Parameters.scala','src/main/scala/xiangshan/backend/fu/FuConfig.scala','src/main/scala/xiangshan/backend/fu/wrapper/DivUnit.scala','src/main/scala/xiangshan/backend/fu/SRT16Divider.scala','src/main/scala/xiangshan/backend/fu/fpu/IntFPToVec.scala']:
    rtl.append(verify(by_path[str(D/rel)]))
result=dict(schema='o2-independent-readonly-object-review-v1',status='PASS_STATIC_BYTES_AND_EXISTING_RECEIPTS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Read bytes/JSON/ELF PT_LOAD only; no import of reviewed code, collector, test, GNU rebuild or target execution',software_manifest=pin(N/'software/manifest.json'),pc_contract=pin(N/'host/PC_CONTRACT.json'),elf=m['images']['elf'],binary=m['images']['bin'],gnu_commands=14,shared_dependencies_matched=len(deps),source_snapshot_files=len(m['sources']),leaf_functions=9,static_customs=17,calls=41,expected_custom_retirements=77,independent_signed_dot=s,complete_result128=m['expected_dot128'],branch_raw_dependencies=raw_dependency,max_critical_arch_instructions=max(f.get('critical_arch_instructions',0) for f in m['functions']),max_critical_two_uop_estimate=max(f.get('critical_f2v_two_uop_estimate',0) for f in m['functions']),rob_estimate_is_dynamic_proof=False,selected_build='attempt-02',attempt01_present=(N/'build-review/attempt-01/RESULT.json').is_file(),selector_existing_result=pin(N/'host/selector-check-02/RESULT.json'),judge_existing_result=pin(N/'host/judge-check-01/RESULT.json'),rtl_pins=rtl,checked_manifest_pins=checked,reviewer_tests=0,reviewer_target_launches=0,reviewer_native_reference_loads=0,target_qualified=False,full_core_reachability='NOT_TESTED')
(N/'independent-review/STATIC_OBJECT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','leaf_functions','static_customs','calls','expected_custom_retirements','independent_signed_dot','shared_dependencies_matched']}))
