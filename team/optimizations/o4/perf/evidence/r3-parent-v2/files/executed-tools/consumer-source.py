import pathlib,json,hashlib,re,subprocess,os
os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:4]))
root=pathlib.Path('/home/lizufan/riscv-lab/r3-perf-20261025-0001')
repo=root/'source'
specs={
'src/main/scala/xiangshan/Bundle.scala':[(237,249)],
'src/main/scala/xiangshan/backend/BackendParams.scala':[(35,44)],
'src/main/scala/xiangshan/backend/CtrlBlock.scala':[(120,139)],
'src/main/scala/xiangshan/backend/datapath/WbArbiter.scala':[(157,175),(203,212),(351,388)],
'src/main/scala/xiangshan/backend/rob/Rob.scala':[(408,423),(522,535),(1374,1398),(1418,1454),(1569,1599)],
'src/main/scala/xiangshan/backend/exu/ExeUnit.scala':[(433,439),(513,529),(724,727)],
'src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala':[(38,51),(67,74),(94,107)],
'src/main/scala/top/ArgParser.scala':[(216,229)],
'src/main/scala/xiangshan/Parameters.scala':[(553,569)],
'utility/src/main/scala/utility/ChiselDB.scala':[(145,155),(224,239)]}
sources={}
for name,ranges in specs.items():
 p=repo/name;raw=p.read_bytes();lines=raw.decode().splitlines()
 sources[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),excerpts=[dict(first=a,last=b,text='\n'.join(lines[a-1:b])) for a,b in ranges])
utility_head=subprocess.check_output(['git','-C',str(repo/'utility'),'rev-parse','HEAD'],text=True).strip()
assert utility_head=='a8ca0c6564865ee69b564d431ecbc52074ba8060'
result=dict(base='5640b7fda828109a875bc4e2dfb9d9a1da0266da',utility_head=utility_head,sources=sources)
out=root/'consumer-source-v1.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print('CONSUMER_SOURCE_SNAPSHOT',len(sources))
base=pathlib.Path('/home/lizufan/riscv-lab/t17-clean-20261024-0854')
print('BUILD_RECORDS', [p.name for p in (base/'build-01').iterdir()])
for name in ['identity-02.json','acceptance.json','build-01/state.json','build-01/build-state.json','build-01/commands.json']:
 p=base/name
 if p.is_file():
  data=json.loads(p.read_text())
  print(name,'KEYS',list(data)[:25] if isinstance(data,dict) else len(data))
  if isinstance(data,dict):
   for k,v in data.items():
    if any(s in k.lower() for s in ['command','config','flags','environment','generated','status']):
     print(k,str(v)[:4000])
print('PERF_UTIL_FILES')
for name in subprocess.check_output(['git','-C',str(repo/'utility'),'ls-files'],text=True).splitlines():
 if 'PerfCounter' in name:print(name)
