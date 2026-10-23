from pathlib import Path
import copy,hashlib,json,sys
from types import SimpleNamespace
base=Path('/home/amesotten/.cache/codex-rvinno/merge-reg-20261023');root=base/'repo';assets=base/'inputs'
out=base/'input-negatives-01';out.mkdir(exist_ok=False)
sys.path.insert(0,str(root/'team/optimizations/o2/fullcore'))
import run_suite as suite
import run_supplements as supplements
guard=suite.load_module('input_audit_guard',root/'team/scripts/artifact_guard.py')
perf=suite.load_module('input_audit_perf',root/'team/workloads/vdot-perf/check.py')
original=json.loads((assets/'input-contract-v1.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def execute(value,name):
    path=out/(name+'.json');save(path,value)
    args=SimpleNamespace(preflight_only=True,input_contract=path,t12_root=assets/'t12',t14_root=assets/'t14',dense_build=assets/'dense')
    return suite.preflight(args,guard,perf)[2]
rows=[]
for name in ('missing-nemu-source','missing-matrix-source','wrong-shard','missing-am-library','negative-wrong-reference','wrong-hello-command'):
    value=copy.deepcopy(original)
    if name=='missing-nemu-source':
        key=next(k for k in value['files'] if '/nemu/reference/src/' in k);value['files'].pop(key)
    elif name=='missing-matrix-source':value['files'].pop(str(root/'team/workloads/vdot-exceptions/judge.c'))
    elif name=='wrong-shard':value['sha256']['matrix'][0]=value['sha256']['matrix'][1]
    elif name=='missing-am-library':value['files'].pop(str(assets/'nexus-am/am/build/am-riscv64-xs.a'))
    else:
        role='negative' if name.startswith('negative') else 'hello'
        receipt=json.loads(Path(value['receipts'][role]).read_text())
        if role=='negative':receipt['command'][7]='-DREF_SO="/wrong.so"'
        else:receipt['commands'][0][-2]='BINARY=/wrong'
        replacement=out/(name+'-receipt.json');save(replacement,receipt)
        value['receipts'][role]=str(replacement);value['files'][str(replacement)]=sha(replacement)
    try:
        execute(value,name)
    except Exception as error:
        rows.append(dict(probe=name,status='EXPECTED_REJECTION',error=str(error)))
    else:raise AssertionError('accepted '+name)
paths,contract,files,reference=supplements.current_inputs(assets/'input-contract-v1.json')
_,workload=supplements.modules()
supplement_rows=[]
for kind,spec in contract['supplements'].items():
    manifest,receipt,image=supplements.validate_build(kind,Path(spec['build']),workload,contract)
    supplement_rows.append(dict(kind=kind,status='SOURCE_AND_BUILD_VERIFIED',image_sha256=sha(image),expected_vdot_commits=manifest['expected_vdot_commits']))
save(out/'result.json',dict(status='INPUT_CONTRACT_NEGATIVES_AND_SUPPLEMENT_BUILDS_PASS',negative_probes=rows,supplements=supplement_rows,emulators_executed=0))
print('INPUT_NEGATIVES_PASS',len(rows),'SUPPLEMENT_BUILDS_PASS',len(supplement_rows),flush=True)
