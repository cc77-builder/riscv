import hashlib, json, sys
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv')
sys.path.insert(0,str(repo/'team/optimizations/o1'))
from check_trace import audit
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-trace-20261018')
old=Path('/home/amesotten/.cache/codex-rvinno/o1-parent-20261018/attempt-07')
out=cache/'final-parent-checks'
out.mkdir()
records=[]
for mode in range(3):
    before=(old/f'mode-{mode}/results.log').read_bytes()
    after=(cache/f'parent-02/mode-{mode}/results.log').read_bytes()
    selected=lambda b:[s for s in b.decode().splitlines() if s.startswith(('VFEX4_PARENT_PASS ', 'FU kind='))]
    if selected(before)!=selected(after) or len(selected(before))!=4:
        raise SystemExit('observation changed baseline behavior')
    result=audit(after.decode().splitlines(),mode,'parent')
    (out/f'mode-{mode}.json').write_text(json.dumps(result,indent=2)+'\n')
    records.append(dict(mode=mode,identical=True,baseline_sha256=hashlib.sha256(before).hexdigest(),trace_sha256=hashlib.sha256(after).hexdigest(),summary=selected(after)))
(out/'observation-invariance.json').write_text(json.dumps(records,indent=2)+'\n')
print('O1_FINAL_PARENT_AUDIT_AND_OBSERVATION_INVARIANCE_PASS')
