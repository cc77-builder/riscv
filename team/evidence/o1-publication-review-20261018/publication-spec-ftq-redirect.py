from pathlib import Path
import sys,re,json,hashlib
root=Path('/mnt/c/Code/RVInno/riscv')
sys.path.insert(0,str(root/'team/optimizations/o1'))
from check_extended import extended_audit, record
run=Path('/home/amesotten/.cache/codex-rvinno/o1-complete-20261018/runs-01')
results=[]
for name in ['control']+['matrix-'+str(i) for i in range(8)]:
    log=run/name/'stderr.log'; lines=log.read_text().splitlines()
    base=extended_audit(lines)[0]
    # Check whether a redirect is to the same VDot allocation, whose FTQ ID is available.
    live={}; selected=None
    for index,line in enumerate(lines):
        if not line.startswith(('O2_FTQ_ENQ ','O2_FTQ_COMMIT ','O2_FTQ_REDIRECT ')): continue
        tag,row=record(line); ptr=(row['rf'],row['rv'])
        if tag=='O2_FTQ_ENQ': live[ptr]=row
        elif tag=='O2_FTQ_COMMIT': live.pop(ptr,None)
        elif ptr in live:
            selected=(index,row,live[ptr]);break
    if selected:
        index,row,enq=selected
        corrupted=list(lines)
        corrupted[index]=re.sub(r'ftv=\s*\d+', 'ftv='+str((row['ftv']+1)%8), corrupted[index])
        result=extended_audit(corrupted)[0]
        results.append(dict(run=name,original=lines[index],enq=enq,corrupted=corrupted[index],passed=result==base,status=result['status']))
print(json.dumps(results,indent=2))
(root/'team/out/publication-spec-ftq-redirect.json').write_text(json.dumps(results,indent=2)+'\n')
