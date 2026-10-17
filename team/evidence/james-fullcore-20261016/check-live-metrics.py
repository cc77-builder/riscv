"""Early diagnostics only; cannot certify incomplete software plans."""
import importlib.util,json,re
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv');cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
spec=importlib.util.spec_from_file_location('compact',repo/'team/scripts/check_t12_compact.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for baseline in ('original','lean'):
    manifest,byid=m.load(cache/'workloads'/('software-'+baseline)/'data')
    text=(cache/'runs'/('software-'+baseline)/'stdout.log').read_text();checked=0
    for match in re.finditer(r'^T12R_PERF seq=(\d+) cy=(\d+),(\d+) ir=(\d+),(\d+)\n',text,re.MULTILINE):
        seq,cb,ce,ib,ie=map(int,match.groups());m.check_counters(byid[manifest['schedule'][seq]['id']],cb,ce,ib,ie);checked+=1
    print(baseline,'complete counter rows checked',checked,'INCOMPLETE_PLAN_DIAGNOSTIC')
