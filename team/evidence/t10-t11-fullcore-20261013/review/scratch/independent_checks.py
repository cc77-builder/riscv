"""Isolated host audits; SYNTHETIC logs below are NEVER real RTL receipts."""
import collections, copy, hashlib, importlib.util, json, pathlib, shutil, sys
ROOT=pathlib.Path(__file__).resolve().parents[1];REPO=ROOT/'review-repo';OUT=ROOT/'scratch'
sys.dont_write_bytecode=True;sys.path.insert(0,str(REPO/'team/tests'))
from generate_vdot_cases import generate
from test_vdot_log import fixture, checker
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
union=module('review_union',ROOT/'review-inputs/verify-union.py')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,text):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
def full_log(data):
    m,legal,exceptions=union.load_data(data)
    header=fixture().splitlines()[:-1]
    header[0]='VDOT_BEGIN contract=vdot-s8x8-r32-v0.1 mode=full'
    lines=['Difftest enabled',*header,'VDOT_EXTENSION_BEGIN']
    for c in legal+exceptions:
        cfg=c.get('config',c);cause=0 if 'config' in c else 2;off=cfg.get('vs_off',0)
        ty=(1<<63) if cfg['vtype']&0x100 else cfg['vtype'];vl=0 if cfg['vtype']&0x100 else cfg['vl']
        csrs='/'.join(hex(v) for v in (ty,vl,cfg['vstart'],cfg['vxrm'],cfg['vxsat'],cfg['vxrm']*2+cfg['vxsat']))
        before='0x'+'f'*32;after='0x'+c['expected_128'] if cause==0 else before
        row=dict(id=c['id'],result='PASS',instruction=c.get('instruction',hex(c.get('word',0))),
            trap_count=int(bool(cause)),expected_cause=hex(cause),actual_cause=hex(cause),fault_pc='0x80001000',
            actual_epc='0x80001000' if cause else '0x0',resume_pc='0x80001004',mtval='0x0',
            pre_mstatus=hex((0 if off else cfg['vs'])<<9),raw_mstatus=hex((0 if off else 3)<<9),
            capture_phase=2 if off else 1,protocol_errors='0x0',requested_vs=0 if off else cfg['vs'],
            pre_csr=csrs,post_csr=csrs,pre_vd128=before,expected_vd128=after,post_vd128=after,
            all32_checked=1,pre32_checked=1,guards_ok=1)
        lines.append('VDOT_CASE '+' '.join(f'{k}={v}' for k,v in row.items()))
    n=len(legal)+len(exceptions)
    lines.extend([f'VDOT_SUMMARY mode=full contract=vdot-s8x8-r32-v0.1 planned={n} executed={n} passed={n} failed=0 unreachable=0','HIT GOOD TRAP'])
    return '\n'.join(lines)+'\n'
def main():
    output={'scope':'HOST/SYNTHETIC AUDIT ONLY; NO RTL EXECUTION','input_hashes':{},'partitions':[],'negative_tests':[],'accepted_counterexamples':[]}
    for p in (ROOT/'review-inputs').iterdir():
        if p.is_file():output['input_hashes'][p.name]=digest(p)
    parent=OUT/'parent';generate(parent,32,0x20261011)
    for n in (4,8):
        runs=OUT/f'partition-{n}';runs.mkdir(exist_ok=True)
        for i in range(n):generate(runs/f'data-{i}',32,0x20261011,32,'legacy',i,n)
        result=union.validate(parent,runs,REPO,True);output['partitions'].append(result)
        assert result['unique_cases']==117 and result['unique_legal']==80 and result['unique_exceptions']==37
    runs=OUT/'partition-8'
    for kind in ('missing-shard','mixed-parent','corrupt-input','wrong-index','wrong-source','incomplete-real-evidence'):
        target=OUT/'union-negative'/kind;target.mkdir(parents=True,exist_ok=True)
        for i in range(8):shutil.copytree(runs/f'data-{i}',target/f'data-{i}',dirs_exist_ok=True)
        if kind=='missing-shard':shutil.rmtree(target/'data-7')
        elif kind=='corrupt-input':
            p=target/'data-1/cases.jsonl';p.write_bytes(p.read_bytes()+b'\n')
        elif kind!='incomplete-real-evidence':
            p=target/'data-2/manifest.json';d=json.loads(p.read_text())
            if kind=='mixed-parent':d['shard']['parent_plan_sha256']='0'*64
            elif kind=='wrong-index':d['shard']['index']=1
            else:d['source_sha256']['vdot_model.py']='0'*64
            put(p,json.dumps(d))
        try:union.validate(parent,target,REPO,kind!='incomplete-real-evidence')
        except (ValueError,FileNotFoundError,KeyError) as e:output['negative_tests'].append(dict(case=kind,status='EXPECTED_REJECTION',message=str(e)))
        else:raise AssertionError(kind+' was accepted')
    # A complete SYNTHETIC fixture lets individual missing evidence checks be tested.
    syn=OUT/'SYNTHETIC-aggregate';syn.mkdir(exist_ok=True)
    runtime='a'*64+'  emu\n'+'b'*64+'  riscv64-nemu-interpreter-so\n'+'c'*64+'  boot-flash.bin\n'
    for i in range(8):
        shutil.copytree(runs/f'data-{i}',syn/f'data-{i}',dirs_exist_ok=True)
        ev=syn/f'run-{i}/evidence'
        put(ev/'run.log',full_log(syn/f'data-{i}'));put(ev/'exit-code.txt','0\n');put(ev/'runtime.sha256',runtime)
        put(ev/'team.sha','1bd6f1d9c9485695876ff37a77fbb175a5125983\n');put(syn/f'run-{i}/status','exit_code=0\n')
    put(syn/'build-0/workload.sha256','d'*64+'  vdot-exceptions.bin\n')
    put(syn/'negative-0/inputs.sha256',runtime+'d'*64+'  vdot-exceptions.bin\n')
    put(syn/'negative-0/status','exit_code=1\n')
    nr=dict(status='EXPECTED_DIFFERENTIAL_REJECTION',bit=100,negative_exit=1,instruction='0x0294050b')
    put(syn/'negative-0/result.json',json.dumps(nr))
    nlog='Difftest enabled\nDIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=10 pc=0x80001000 instruction=0x0294050b\nv10_high different at pc = 0x80001000, right= 0x0000000000000000, wrong = 0x0000001000000000\nABORT\n'
    put(syn/'negative-0/run.log',nlog)
    baseline=union.validate(parent,syn,REPO)
    assert baseline['extension_pass'];output['synthetic_baseline_accepted']=True
    def counter(name,change,restore):
        change()
        for rel in ('run-0/evidence/run.log','negative-0/run.log','run-0/status','run-0/evidence/team.sha','data-0/manifest.json'):
            put(OUT/'counterexamples'/name/rel,(syn/rel).read_text())
        try:verdict=union.validate(parent,syn,REPO)
        except (ValueError,FileNotFoundError,KeyError) as e:output['negative_tests'].append(dict(case=name,status='EXPECTED_REJECTION',message=str(e)))
        else:output['accepted_counterexamples'].append(dict(case=name,status='UNEXPECTED_ACCEPTANCE',checker_status=verdict['status']))
        finally:restore()
    counter('all_receipts_bound_to_wrong_candidate',
        lambda:[put(syn/f'run-{i}/evidence/team.sha','5ff189b8a44e58ee6a37d824e74c801c466c25d3\n') for i in range(8)],
        lambda:[put(syn/f'run-{i}/evidence/team.sha','1bd6f1d9c9485695876ff37a77fbb175a5125983\n') for i in range(8)])
    logpath=syn/'run-0/evidence/run.log';original=logpath.read_text()
    counter('missing_all_seven_selftest_records',lambda:put(logpath,'\n'.join(x for x in original.splitlines() if not x.startswith('VDOT_CASE id=H'))),lambda:put(logpath,original))
    scope=original.split('VDOT_EXTENSION_BEGIN\n');ext=scope[1].splitlines();records=[x for x in ext if x.startswith('VDOT_CASE')];other=[x for x in ext if not x.startswith('VDOT_CASE')]
    counter('exceptions_executed_before_D00',lambda:put(logpath,scope[0]+'VDOT_EXTENSION_BEGIN\n'+'\n'.join(list(reversed(records))+other)),lambda:put(logpath,original))
    counter('good_trap_before_extension_without_terminal_event',lambda:put(logpath,'HIT GOOD TRAP\n'+original.replace('HIT GOOD TRAP\n','')),lambda:put(logpath,original))
    counter('contradictory_driver_status',lambda:put(syn/'run-0/status','exit_code=0\nexit_code=124\n'),lambda:put(syn/'run-0/status','exit_code=0\n'))
    counter('negative_mismatch_at_different_pc',lambda:put(syn/'negative-0/run.log',nlog.replace('different at pc = 0x80001000','different at pc = 0x80009000')),lambda:put(syn/'negative-0/run.log',nlog))
    counter('summary_truncated_despite_exit_zero',lambda:put(logpath,original.split('VDOT_SUMMARY')[0]),lambda:put(logpath,original))
    # Generation source claims are equal across shards, but parent is not compared.
    original_manifests={i:(syn/f'data-{i}/manifest.json').read_text() for i in range(8)}
    def corrupt_sources():
        for i in range(8):
            p=syn/f'data-{i}/manifest.json';d=json.loads(p.read_text());d['source_sha256']['vdot_model.py']='0'*64;put(p,json.dumps(d))
    counter('all_shards_claim_wrong_model_source',corrupt_sources,lambda:[put(syn/f'data-{i}/manifest.json',original_manifests[i]) for i in range(8)])
    # Import original digests are deliberately preserved; current ones must match.
    imports=json.loads((REPO/'team/docs/t10-t11-imports.json').read_text());output['stale_current_hashes']=[]
    for item in imports['files']:
        actual=digest(REPO/item['path'])
        if actual!=item['current_sha256']:output['stale_current_hashes'].append(dict(path=item['path'],recorded=item['current_sha256'],actual=actual))
    nm=REPO/'team/patches/nemu';manifest=json.loads((nm/'manifest.json').read_text());hist=json.loads((nm/'history/manifest-1.0.0.json').read_text())
    assert digest(nm/'vdot-s8x8-r32-v0.1.patch')==manifest['patch_sha256']
    assert digest(nm/'history/vdot-1.0.0.patch')==hist['patch_sha256']
    patch=(nm/'vdot-s8x8-r32-v0.1.patch').read_text();history=(nm/'history/vdot-1.0.0.patch').read_text()
    output['new_nemu_headers_sha256']={}
    for name in ('src/isa/riscv64/instr/rvv/vdot.h','src/isa/riscv64/local-include/vdot_tval.h'):
        section=patch.split('+++ b/'+name+'\n',1)[1].split('\ndiff --git',1)[0]
        header='\n'.join(x[1:] for x in section.splitlines() if x.startswith('+'))+'\n'
        actual=hashlib.sha256(header.encode()).hexdigest()
        assert actual==manifest['patched_source_sha256'][name]
        output['new_nemu_headers_sha256'][name]=actual
    tail=lambda x:x.split('+++ b/src/isa/riscv64/instr/rvv/vdot.h\n',1)[1].split('\ndiff --git',1)[0]
    assert tail(patch).splitlines()==tail(history).splitlines();output['nemu_arithmetic_unchanged']=True
    output['patch_and_history_digests_verified']=True
    put(OUT/'independent-checks.json',json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
