import ast,collections,hashlib,json,os,pathlib,signal,time
signal.alarm(55);os.sched_setaffinity(0,{3});os.setpriority(os.PRIO_PROCESS,0,5)
t0=time.monotonic()
root=pathlib.Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main')
paths={'controller':root/'input-serial-01/fa_serialization.py','original':root/'local-01/mapped.json',
       'reparsed':root/'serialization-01/reparsed.json','failed_result':root/'serialization-01/result.json'}
expected={'controller':'82738e4ca6c0d84de04cb8a77e9143ab2d646bc025e087dddc3ff62a12109a8a',
 'original':'7117718b7d29be886b948d70d7a0486a472f341e1ffcf1bec827728b8cc8f53c',
 'reparsed':'dca75effeb69eccf2c406ba7436c607b82af36558465bfb491f2fa61fb416ce3',
 'failed_result':'861ccfa472deb1e08057fa57bec36fe245bd4ebfdcf51f13767fb7c06bc19d8f'}
raw={k:p.read_bytes() for k,p in paths.items()}
pins={k:dict(path=str(paths[k]),bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in raw.items()}
assert all(pins[k]['sha256']==v for k,v in expected.items())
tree=ast.parse(raw['controller']);defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('need','circuit')]
assert len(defs)==2
env=dict(defaultdict=collections.defaultdict,json=json)
exec(compile(ast.Module(body=defs,type_ignores=[]),'<existing-circuit-functions>','exec'),env)
o=json.loads(raw['original'])['modules']['CommonFuCostTop']
r=json.loads(raw['reparsed'])['modules']['CommonFuCostTop']
mapping={name:('\\'+name if name.startswith('$') else name) for name in o['cells']}
bijective=(len(set(mapping.values()))==len(mapping) and set(mapping.values())==set(r['cells']))
assert bijective,'one leading backslash for original dollar cell names is not a complete bijection'
inverse={v:k for k,v in mapping.items()}
back=dict(r);back['cells']={inverse[k]:v for k,v in r['cells'].items()}
og=env['circuit'](o);rg=env['circuit'](r);bg=env['circuit'](back)
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
changed=[[k,v] for k,v in sorted(mapping.items()) if k!=v]
assert og==bg,'renaming alone does not explain the complete graph mismatch'
after={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
report=dict(status='EXACT_GRAPH_MATCH_UNDER_EXPLICIT_CELL_NAME_BIJECTION',
 pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),
 input_files=pins,inputs_unchanged=all(after[k]==v for k,v in expected.items()),
 rule="Only each original cell identifier starting with dollar gets one literal leading backslash; all other identifiers unchanged.",
 complete_bijection=bijective,cell_names_original=len(mapping),cell_names_reparsed=len(r['cells']),
 changed_cell_names=len(changed),unchanged_cell_names=len(mapping)-len(changed),
 changed_prefix_histogram=dict(collections.Counter(k.split('$')[1] for k,v in changed)),
 mapping_sha256=digest(sorted(mapping.items())),mapping_examples=changed[:3]+changed[-3:],
 top_ports=len(og['ports']),cells=len(og['cells']),nets=len(og['nets']),
 terminal_count=sum(len(n['terminals']) for n in og['nets']),
 equal_ports=og['ports']==bg['ports'],equal_cells_all_fields=og['cells']==bg['cells'],
 equal_terminal_graph=og['nets']==bg['nets'],complete_graph_equal=og==bg,
 original_graph_sha256=digest(og),raw_reparsed_graph_sha256=digest(rg),inverse_renamed_graph_sha256=digest(bg),
 cell_type_histogram=dict(collections.Counter(c['type'] for c in og['cells'].values())),
 constant_nets=[dict(constant=n['constant'],terminal_count=len(n['terminals'])) for n in og['nets'] if n['constant'] is not None],
 no_eda_or_simulation_started=True,no_original_files_written=True,
 meaning="Readonly diagnostic of exact already-written mapped JSONs only. No old result edited, no gate bypass, no STA or RTL-to-mapped equivalence claim.",
 elapsed_seconds=time.monotonic()-t0)
assert report['inputs_unchanged'];print(json.dumps(report,indent=2))
