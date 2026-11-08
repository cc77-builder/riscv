from pathlib import Path
import json,re
B=Path('/home/riscv/riscv-lab/item19-observer-20261107/build-03/source/build/emu-compile')
N=Path(__file__).resolve().parent.parent
records=[]
for q in B.glob('*.cpp'):
 t=q.read_text()
 for m in re.finditer(r'VL_FWRITEF_NX\(0x80000002U,"(SCHED_(?:[^"\\]|\\.)*)",(\d+)',t):
  end=t.find(';',m.end());body=t[m.end():end]
  tags=re.findall(r",\s*'([^']+)'\s*,\s*(\d+)\s*,",body)
  fmt=json.loads('"'+m.group(1)+'"');specs=list(re.finditer(r'%[dx]',fmt))
  assert len(tags)==int(m.group(2))==len(specs),(q,fmt,tags)
  # NX '#' is scalar transport; radix comes exclusively from format.
  widths=[int(w) for tag,w in tags]
  assert all(tag in ('#','w') for tag,w in tags),tags
  size=len(fmt.encode())-2*len(specs)
  for spec,bits in zip(specs,widths):
   size+=len(str((1<<bits)-1)) if spec[0]=='%d' else (bits+3)//4
  records.append(dict(kind=fmt.split()[0],format=fmt,widths=widths,max_bytes=size,source=str(q)))
by={k:[r['max_bytes']for r in records if r['kind']==k]for k in sorted(set(r['kind']for r in records))}
result=dict(status='PASS_ACTUAL_COMPILED_FORMAT_BOUND',records=records,by_kind=by,per_cycle_bytes=sum(r['max_bytes']for r in records if r['kind']!='SCHED_SCHEMA'),schema_bytes=sum(by['SCHED_SCHEMA']),note='Every compiled site allowed each cycle; decimal widths include padding, no event exclusivity assumed.')
(N/'FORMAT_BOUND.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items()if k not in ('records',)})
