import pathlib,json,gzip,hashlib,re,os,subprocess,importlib.util,collections
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:4]))
root=pathlib.Path('/home/lizufan/riscv-lab/r3-perf-20261025-0001')
repo=root/'source'
h1=repo/'team/optimizations/o2/result-width/h1/evidence/20261021-local'
o4=repo/'team/optimizations/o4/evidence/20261020-cost'
pins={}
def read_arch(arch,path):
 manifest=json.loads((arch/'manifest.json').read_text())
 entry=next(e for e in manifest['entries'] if e['path']==path)
 stored=(arch/'files'/entry['stored']).read_bytes()
 assert hashlib.sha256(stored).hexdigest()==entry['stored_sha256'] and len(stored)==entry['stored_bytes'],path
 raw=gzip.decompress(stored) if entry['gzip'] else stored
 assert hashlib.sha256(raw).hexdigest()==entry['sha256'] and len(raw)==entry['bytes'],path
 pins[str(arch.relative_to(repo))+'/'+path]=dict(manifest_sha256=hashlib.sha256((arch/'manifest.json').read_bytes()).hexdigest(),sha256=entry['sha256'],stored_sha256=entry['stored_sha256'],bytes=len(raw))
 return raw
results={}
for label,arch,prefix in [('o1-fu',o4,'o1-fu-map-02'),('o2-b0-fu',o4,'o2-fu-map-01'),('o2-h1-fu',h1,'fu-map-01'),('o2-h1-parent',h1,'parent-map-01')]:
 summary=json.loads(read_arch(arch,prefix+'/summary.json'))
 mapped=json.loads(read_arch(arch,prefix+'/mapped.json'))
 module=mapped['modules'][summary['top']]
 hist=collections.Counter(c['type'] for c in module['cells'].values())
 assert hist==summary['cell_histogram']
 qbits={b for c in module['cells'].values() if c['type'].startswith('DFF') for b in c['connections']['Q']}
 groups={}
 for group,pattern in [('P',r'(?:^|\.)pPerf_'),('R',r'(?:^|\.)rPacket_perfDebugInfo_')]:
  names={n:net['bits'] for n,net in module['netnames'].items() if re.search(pattern,n)}
  bits={b for v in names.values() for b in v}
  assert bits<=qbits,(label,group,'not registered')
  groups[group]=dict(bits=len(bits),fields={n:len(v) for n,v in names.items()},q_driver_verified=True)
 item=dict(cell_area_sum=summary['cell_area_sum'],dff_q_bits=len(qbits),perf_groups=groups,source='retained historical mapped JSON; no new synthesis',top=summary['top'])
 results[label]=item
 print(label,json.dumps(item,sort_keys=True))
 del mapped,module
legacy=read_arch(h1,'parent-01/result.log').decode()
sys_path=repo/'team/optimizations/o2/parent'
def mod(name):
 spec=importlib.util.spec_from_file_location(name,sys_path/(name+'.py'))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
legacy_trace=mod('check_trace').check_trace(legacy)
legacy_gate=mod('check_negative').check_positive(legacy)
report=dict(status='R3_HISTORICAL_SUBSET_REUSE_PASS',cost=results,legacy_trace=legacy_trace,legacy_gate=legacy_gate,inputs=pins,new_rtl=False,new_fullcore=False,new_ppa=False)
out=root/'historical-reuse-v1.json'
assert not out.exists()
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('LEGACY_REPLAY',legacy_trace['cycles'],legacy_trace['groups'],legacy_trace['perf_contract'])
print('T17_FILES')
for p in sorted(pathlib.Path('/home/lizufan/riscv-lab/t17-clean-20261024-0854').iterdir()): print(p.name)
