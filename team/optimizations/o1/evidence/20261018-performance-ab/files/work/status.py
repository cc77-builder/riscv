from pathlib import Path
import json,os,subprocess,datetime,re
w=Path('/home/riscv/riscv-lab/o1-performance-20261018')
b=w/('t14-build-resume-01' if (w/'t14-build-resume-01/build-state.json').exists() else 't14-build-01')
state=json.loads((b/'build-state.json').read_text())
products=Path(state.get('build_products',str(b/'products')))
if not (w/'campaign-01/state.json').exists(): print('T14 build',(json.loads((w/'t14-build-final-01/build-state.json').read_text())['status'] if (w/'t14-build-final-01/build-state.json').exists() else state['status']),'SV',len(list((products/'rtl').glob('*.sv'))),'objects',len(list((products/'emu-compile').glob('*.o'))))
s=(b/'emu-build.log').read_text(errors='replace')
complete=s.splitlines()
if not (w/'campaign-01/state.json').exists(): print('build tail:', next((x[:220] for x in reversed(complete) if x.strip()),''))
compiler=b/'actual-compiler.json'
if not compiler.exists():
 matches=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   cmd=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x]
   if cmd and 'clang++' in cmd[0] and any(str(products) in x for x in cmd):
    exe=(p/'exe').resolve()
    matches.append({'pid':int(p.name),'exe':str(exe),'command':cmd,'version':subprocess.check_output([str(exe),'--version'],text=True)})
  except (OSError,UnicodeError,subprocess.CalledProcessError):pass
 if matches:
  compiler.write_text(json.dumps({'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'actual live compiler processes','invocations':matches[:2]},indent=2)+'\n')
  print('captured actual compiler',matches[0]['exe'])
for root in ([w/'campaign-01'] if (w/'campaign-01').exists() else [w/'o1-calibration-probe-01']):
 if not root.exists():continue
 final=root/'result.json'
 if final.exists():
  d=json.loads(final.read_text()); print(root.name,d.get('status'),d.get('error',''))
  if d.get('status') not in ('RUNNING','PREFLIGHT'):continue
 if (root/'state.json').exists():
  d=json.loads((root/'state.json').read_text());print('campaign',d.get('status'),d.get('stage',''))
 progress=root/'progress.json'
 done=json.loads(progress.read_text()) if progress.exists() else []
 if progress.exists():print('completed',len(done),'failed',sum(x.get('status')=='FAILED' for x in done))
 runtimes=[root/'runtime.json'] if (root/'runtime.json').exists() else sorted(root.glob('*/*/*/runtime.json'))
 for rp in runtimes:
  d=rp.parent
  if (d/'result.json').exists() and json.loads((d/'result.json').read_text()).get('status')!='RUNNING':continue
  log=d/'stderr.log'
  if log.exists():
   text=log.read_text(errors='replace')
   text=text.rsplit('\n',1)[0]
   cycles=re.findall(r'(?:cycle|tick)=\s*(\d+)',text)
   uart=(d/'stdout.log').read_text(errors='replace') if (d/'stdout.log').exists() else ''
   markers=re.findall(r'T13_(?:P|CASE) seq=(\d+)',uart)
   print('active',d.relative_to(w), 'cycle',cycles[-1:] if cycles else [],'window',markers[-1:],'bytes',log.stat().st_size)
