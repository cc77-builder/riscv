import pathlib, subprocess, hashlib, json, re, os
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:4]))
root=pathlib.Path('/home/lizufan/riscv-lab/r3-perf-20261025-0001')
source=root/'source'
old=pathlib.Path('/home/lizufan/riscv-lab/t17-clean-20261024-0854/clean-02/source')
result=dict(base='5640b7fda828109a875bc4e2dfb9d9a1da0266da',t17_source='34bae6d4acceac939f958199dae53c14bc1f6183',trees={},generated={})
for path in ['src','build.sc','team/models/vdot/data']:
 pins={ref:subprocess.check_output(['git','-C',str(source),'rev-parse',ref+':'+path],text=True).strip() for ref in [result['base'],result['t17_source']]}
 assert len(set(pins.values()))==1,path
 result['trees'][path]=pins
subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src','build.sc','.gitmodules','team/rtl/vdot','team/models/vdot'],check=True,stdout=subprocess.PIPE)
result['production_diff_exit']=0
rtl=old/'build/rtl'
targets=[rtl/'VDotElastic.sv',rtl/'WbDataPath.sv',rtl/'CtrlBlock.sv',rtl/'Rob.sv']
for p in sorted(rtl.glob('ExeUnit*.sv')):
 if re.search(r'\bVDotElastic\s+',p.read_text()): targets.append(p)
for p in targets:
 raw=p.read_bytes(); lines=raw.decode().splitlines()
 hits=[dict(line=i+1,text=line) for i,line in enumerate(lines) if ('perfDebugInfo' in line or 'debugInfo' in line) and ('pPerf' in line or 'rPacket' in line or 'output' in line or 'assign io_out_bits_debugInfo' in line)]
 result['generated'][p.name]=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),perf_excerpts=hits)
 print('RTL',p.name,len(raw),hashlib.sha256(raw).hexdigest())
 if p.name=='VDotElastic.sv':
  for i,line in enumerate(lines,1):
   if ('pPerf_' in line or 'rPacket_perfDebugInfo_' in line) and ('reg ' in line or '<=' in line or 'assign io_out_bits_perfDebugInfo' in line):print(i,line)
 if p.name.startswith('ExeUnit'):
  for i,line in enumerate(lines,1):
   if 'VDotElastic ' in line or ('out_bits_debugInfo_' in line and ('assign ' in line or 'output' in line)):print(i,line)
out=root/'consumer-generated-v1.json'
assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n')
print('TREE_IDENTITIES',json.dumps(result['trees']))
print('T17_BUILD_RECORDS',[p.name for p in old.parent.iterdir()])
paths=subprocess.check_output(['git','-C',str(source),'ls-files','team/optimizations/o2/result-width/h1/evidence','team/optimizations/o4/evidence'],text=True).splitlines()
print('COST_EVIDENCE')
for p in paths:
 if any(x in p for x in ['summary.json','structure','mapped.json','register','manifest.json']): print(p)
