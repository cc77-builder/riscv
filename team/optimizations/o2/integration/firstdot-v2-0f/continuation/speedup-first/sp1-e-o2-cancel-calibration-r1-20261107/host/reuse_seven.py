"""Read-only reuse verification, no rerun of the seven old methods."""
from pathlib import Path
import json,ast
from common import read,sha,need
N=Path(__file__).resolve().parent.parent

def verify():
    c=read(N/'REUSED_SEVEN.json');old=Path(c['old_root'])
    for x in [c['old_log'],c['old_result'],c['old_freeze'],c['old_test'],c['old_contract']]+c['old_locks']:
        p=Path(x['path']);need(p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],'old evidence drift')
    def methods(path):return {x.name:ast.dump(x,include_attributes=False) for x in ast.walk(ast.parse(path.read_text())) if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')}
    a,b=methods(old/'host/test_delta.py'),methods(N/'host/test_delta.py');log=(old/'host/tests.log').read_text()
    for name in c['reused_methods']:
        need(a[name]==b[name],'unmodified passed method '+name)
        need(name+' (test_delta.Delta) ... ok' in log,'actual old method PASS '+name)
    for rel,x in c['same_files'].items():need(sha(N/rel)==x['sha256'] and sha(Path(x['path']))==x['sha256'],'reused source changed '+rel)
    a=read(old/'CONTRACT.json');b=read(N/'CONTRACT.json')
    for k in a:
        if k not in c['contract_allowed_changes']:need(a[k]==b[k],'contract gate changed '+k)
    need(set(a)==set(b),'contract field set')
    return {'status':'PASS_SEVEN_METHODS_REUSED','methods':c['reused_methods'],'source_files':len(c['same_files']),'scope':'prior method results with identical AST/mechanisms; new path cold-import rerun separately; old third-method FAIL retained','old_whole_suite_status':'FAIL_RETAINED','new_targets':0}
