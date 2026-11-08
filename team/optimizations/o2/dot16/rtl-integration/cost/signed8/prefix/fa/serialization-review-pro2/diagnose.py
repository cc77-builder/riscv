import ast,collections,hashlib,json,os,pathlib,signal,time
signal.alarm(55)
os.sched_setaffinity(0,{3})
os.setpriority(os.PRIO_PROCESS,0,5)
t0=time.monotonic()
root=pathlib.Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main')
paths={
 'controller':root/'input-serial-01/fa_serialization.py',
 'original':root/'local-01/mapped.json',
 'split':root/'serialization-01/split.json',
 'reparsed':root/'serialization-01/reparsed.json',
 'result':root/'serialization-01/result.json',
 'serialize_script':root/'serialization-01/serialize.ys',
 'reparse_script':root/'serialization-01/reparse.ys',
 'reparse_log':root/'serialization-01/reparse.log'
}
raw={k:p.read_bytes() for k,p in paths.items()}
before={k:dict(path=str(paths[k]),size=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in raw.items()}
assert before['controller']['sha256']=='82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a'
assert before['original']['sha256']=='7117718b7d29be886b948d70d7a0486a472f341e1ffcf1bec827728b8cc8f53c'
tree=ast.parse(raw['controller'])
defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('need','circuit')]
assert len(defs)==2
env=dict(defaultdict=collections.defaultdict,json=json)
exec(compile(ast.Module(body=defs,type_ignores=[]),'<read-only-circuit-extraction>','exec'),env)
docs={k:json.loads(raw[k]) for k in ('original','split','reparsed')}
mods={k:v['modules']['CommonFuCostTop'] for k,v in docs.items()}
graphs={k:env['circuit'](v) for k,v in mods.items()}
def summary(g):
 return dict(ports=len(g['ports']),cells=len(g['cells']),nets=len(g['nets']),
             cell_types=dict(collections.Counter(c['type'] for c in g['cells'].values())),
             graph_sha256=hashlib.sha256(json.dumps(g,sort_keys=True).encode()).hexdigest())
def diffdict(a,b,limit=30):
 common=sorted(set(a)&set(b));changed=[k for k in common if a[k]!=b[k]]
 return dict(only_before_count=len(set(a)-set(b)),only_after_count=len(set(b)-set(a)),
             only_before=sorted(set(a)-set(b))[:limit],only_after=sorted(set(b)-set(a))[:limit],
             changed_count=len(changed),changed=[dict(key=k,before=a[k],after=b[k]) for k in changed[:limit]])
def netsig(g):
 out={}
 for n in g['nets']:
  ts=tuple(tuple(t) for t in n['terminals']);v=(n['constant'],ts)
  for t in ts: assert t not in out;out[t]=v
 return out
o=graphs['original'];r=graphs['reparsed'];a=netsig(o);b=netsig(r)
common=set(a)&set(b)
changed=sorted(t for t in common if a[t]!=b[t])
groups={};kindcounts=collections.Counter()
for t in changed:
 x,y=a[t],b[t];key=(x,y)
 if x[0]!=y[0]:kind='constant_binding'
 elif set(x[1])!=set(y[1]):kind='terminal_membership'
 else:kind='ordering_only'
 kindcounts[kind]+=1
 if key not in groups and len(groups)<30:
  groups[key]=dict(example_terminal=t,kind=kind,
                  before_constant=x[0],after_constant=y[0],
                  before_terminal_count=len(x[1]),after_terminal_count=len(y[1]),
                  removed=sorted(set(x[1])-set(y[1]))[:20],
                  added=sorted(set(y[1])-set(x[1]))[:20],
                  before_terminals=list(x[1])[:20],after_terminals=list(y[1])[:20])
res=json.loads(raw['result'])
after={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
report=dict(status='READONLY_FA_SERIALIZATION_DIAGNOSTIC',pid=os.getpid(),pgid=os.getpgrp(),
 cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),
 input_files=before,inputs_unchanged=all(after[k]==v['sha256'] for k,v in before.items()),
 original_result=dict(status=res.get('status'),error=res.get('error'),
                      started=res.get('started'),finished=res.get('finished'),
                      commands=[{k:c.get(k) for k in ('label','pid','exit_code','reaped','group_absent')} for c in res.get('commands',[])]),
 module_names={k:sorted(v['modules']) for k,v in docs.items()},
 summary={k:summary(v) for k,v in graphs.items()},
 original_split_graph_equal=graphs['original']==graphs['split'],
 original_reparsed_graph_equal=graphs['original']==graphs['reparsed'],
 ports_diff=diffdict(o['ports'],r['ports']),
 cells_diff=diffdict(o['cells'],r['cells']),
 net_diff=dict(only_before_terminals=len(set(a)-set(b)),only_after_terminals=len(set(b)-set(a)),
               only_before_samples=sorted(set(a)-set(b))[:20],only_after_samples=sorted(set(b)-set(a))[:20],
               changed_common_terminals=len(changed),kinds=dict(kindcounts),sample_groups=list(groups.values())),
 serialize_script=raw['serialize_script'].decode(),reparse_script=raw['reparse_script'].decode(),
 reparse_log_tail=raw['reparse_log'].decode(errors='replace')[-6000:],
 elapsed_seconds=time.monotonic()-t0,no_eda_or_simulation_started=True,no_original_files_written=True)
assert report['inputs_unchanged']
print(json.dumps(report,indent=2))
