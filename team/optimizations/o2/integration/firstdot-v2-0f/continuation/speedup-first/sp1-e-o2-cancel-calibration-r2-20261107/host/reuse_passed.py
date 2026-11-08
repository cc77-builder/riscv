"""Reuse unaffected pass evidence by exact source and contract identity."""
from pathlib import Path
import ast
from common import read,sha,need
N=Path(__file__).resolve().parent.parent

def verify():
    c=read(N/'REUSED_UNCHANGED.json')
    for x in [c[k] for k in ('passed_method_log','passed_method_source','r1_passed_log','r1_result','r1_contract')]+list(c['same_files'].values()):
        p=Path(x['path']);need(p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],'reuse evidence drift')
    for rel,x in c['same_files'].items():need(sha(N/rel)==x['sha256'],'unaffected source changed '+rel)
    def methods(path):return {x.name:ast.dump(x,include_attributes=False) for x in ast.walk(ast.parse(Path(path).read_text())) if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')}
    a=methods(c['passed_method_source']['path']);b=methods(N/'host/test_delta.py');log=Path(c['passed_method_log']['path']).read_text()
    for name in c['reused_methods']:
        need(a[name]==b[name],'reused method AST '+name)
        need(name+' (test_delta.Delta) ... ok' in log,'old method PASS '+name)
    a=read(c['r1_contract']['path']);b=read(N/'CONTRACT.json');need(set(a)==set(b),'contract key drift')
    for k in a:
        if k not in ('operation_id','cwd'):need(a[k]==b[k],'frozen semantic contract '+k)
    return {'status':'PASS_UNCHANGED_EVIDENCE_REUSED','methods':c['reused_methods'],'source_files':len(c['same_files']),'scope':c['scope'],'old_FAIL_and_locks':'RETAINED','new_targets':0}
