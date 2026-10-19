"""Independent saved-log replay and corruption probes; no new EMU execution."""
import hashlib,json,re,sys
from pathlib import Path
root=Path('/mnt/c/Code/RVInno/riscv')
sys.path.insert(0,str(root/'team/optimizations/o1'))
import run_software_core as runner
cache=Path('/home/amesotten/.cache/codex-rvinno/o1-optimization-20261019')
campaign=cache/'software-01'
reference=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016/nemu/reference/build/riscv64-nemu-interpreter-so')
record=json.loads((campaign/'campaign.json').read_text())
assert record['status']=='O1_SOFTWARE_PLANS_PASS'
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in campaign.rglob('*') if p.is_file()}
replays=[]
for baseline in runner.PLANS:
    folder=campaign/baseline
    stdout=(folder/'stdout.log').read_text();stderr=(folder/'stderr.log').read_text()
    checked=runner.check_software(stdout,stderr,campaign/'images'/('software-'+baseline),baseline,0,reference)
    assert checked==json.loads((folder/'checked.json').read_text())
    replays.append(dict(baseline=baseline,executed=checked['architectural']['executed']))
folder=campaign/'original';image=campaign/'images/software-original'
stdout=(folder/'stdout.log').read_text();stderr=(folder/'stderr.log').read_text()
def one(pattern,replacement,text):
    changed,count=re.subn(pattern,replacement,text,count=1,flags=re.M)
    assert count==1,pattern
    return changed
cases=[('nonzero_exit',stdout,stderr,1),
       ('partial_plan',one(r'T12R_END executed=190', 'T12R_END executed=189', stdout),stderr,0),
       ('missing_perf_row',one(r'^T12R_PERF [^\n]*\n','',stdout),stderr,0),
       ('foreign_reference',stdout.replace(str(reference),'/wrong/reference.so'),
        stderr.replace(str(reference),'/wrong/reference.so'),0),
       ('absent_protocol',stdout,'\n'.join(x for x in stderr.splitlines() if not x.startswith(('O1_','O2_'))),0),
       ('wrong_csr_sample',stdout,one(r'^(O2_COUNTER_COMMIT [^\n]*\bdata=)\s*0x[0-9a-fA-F]+',
                                     r'\g<1>0xffffffffffffffff',stderr),0)]
results=[]
for name,out,err,rc in cases:
    assert (out,err,rc)!=(stdout,stderr,0),name
    try:
        runner.check_software(out,err,image,'original',rc,reference)
    except ValueError as exc:
        results.append(dict(name=name,status='REJECTED',reason=str(exc)))
    else:
        raise RuntimeError('corruption escaped: '+name)
after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in campaign.rglob('*') if p.is_file()}
assert after==before
output=cache/'software-recheck.json'
with output.open('x') as f:
    json.dump(dict(status='O1_SOFTWARE_REPLAY_AND_NEGATIVES_PASS',replays=replays,negative_probes=results,
                   raw_and_receipts_unchanged=True,new_emu_jobs=0,inputs=before),f,indent=2)
print('O1_SOFTWARE_REPLAY_AND_NEGATIVES_PASS',len(results))
