"""Cold-process tests for new collector glue; existing full analyzers are pinned and reused."""
from pathlib import Path
import argparse,importlib.util,json,sys,re
p=argparse.ArgumentParser();p.add_argument('stage');p.add_argument('out');args=p.parse_args();S=Path(args.stage)
spec=importlib.util.spec_from_file_location('closeout_collector',Path(__file__).with_name('collect.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
sys.path.insert(0,str(S/'runtime'));import fixtures_local
text=fixtures_local.normal();conf=json.loads((S/'CONTRACT.json').read_text());ref=conf['runtime']['normal_reference']['path']
a=c.supplement(text,'candidate',S,ref,0);rows=[]
for label,pattern,new in [('full128',r'data=0x[0-9a-f]*fffffdec','data=0x000000100000000000000000fffffdec'),('calls',r'OC19_PASS seq=40','OC19_PASS seq=39'),('config',r'vl=\s*8\b','vl=7'),('image',re.escape(conf['runtime']['bin']['path']),'/wrong/image.bin')]:
 m=re.search(pattern,text);assert m,label
 bad=text[:m.start()]+new+text[m.end():]
 try:c.supplement(bad,'candidate',S,ref,0)
 except (ValueError,AssertionError)as e:rows.append(dict(label=label,rejected=True,reason=str(e)))
 else:raise AssertionError('mutation accepted: '+label)
Path(args.out).write_text(json.dumps(dict(status='PASS_SUPPLEMENT_COLLECTOR_GLUE',positive=a['status'],negatives=rows,target_runs=0),indent=2)+'\n')
print('PASS_SUPPLEMENT_COLLECTOR_GLUE')
