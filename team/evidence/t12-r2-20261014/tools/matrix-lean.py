import datetime,importlib.util,json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];repo=root/'repo';out=root/'runs/matrix-199-lean';out.mkdir(exist_ok=False)
source='8af7b21857ba2c65dbc4d835f7b2152cd6684875';old=Path('/home/lizufan/xiangshan-t10-t11-supervisor-20261013');script=repo/'team/scripts/t12-tests.py'
now=lambda:datetime.datetime.now().astimezone().isoformat()
records=[]
for start,count in ((0,13),(13,50),(63,50),(113,50),(163,36)):
 for mode in ('build','run'):
  target=out/f'{mode}-{start:03d}';cmd=[sys.executable,'-B',str(script),mode,'--expected-source',source,'--output',str(target)]
  if mode=='build':cmd+=['--am',str(root/'deps/nexus-am'),'--toolchain',str(old/'tools/ubuntu-root'),'--start',str(start),'--count',str(count),'--baseline','lean','--include-chain']
  else:cmd+=['--build',str(out/f'build-{start:03d}'),'--emu',str(old/'repo/build/emu'),'--reference',str(old/'nemu-xs-tval/reference/build/riscv64-nemu-interpreter-so'),'--nemu',str(old/'nemu-xs-tval/reference'),'--flash',str(old/'runs/final-acceptance-20261013-2155/run-0/evidence/boot-flash.bin'),'--cycles','600000','--timeout','600']
  rec=dict(argv=cmd,started_at=now());p=subprocess.Popen(cmd,cwd=root);rec['pid']=p.pid;records.append(rec);(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
  rc=p.wait();rec.update(exit_code=rc,finished_at=now());(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
  if rc:raise SystemExit(rc)
 spec=importlib.util.spec_from_file_location('c',repo/'team/scripts/check_t12_compact.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
 completed=[json.loads(p.read_text()) for p in sorted(out.glob('run-*/checked.json'))]
 print('MATRIX_PROGRESS',sum(x['executed'] for x in completed),flush=True)
result=c.aggregate(completed,out/'build-000/data');(out/'aggregate.json').write_text(json.dumps(result,indent=2)+'\n');print('MATRIX_COMPLETE',result['executed'],flush=True)
