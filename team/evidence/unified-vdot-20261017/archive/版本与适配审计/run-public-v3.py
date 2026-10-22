from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,time
w=Path(__file__).resolve().parent
refs={'shishui':w/'variants/shishui/.benchmark/nemu/build/riscv64-nemu-interpreter-so','redoop':w/'variants/redoop/benchmark-nemu/build/riscv64-nemu-interpreter-so'}
def run(variant):
    status=w/'runs'/(variant+'-build/build.json')
    while not status.exists() or json.loads(status.read_text())['status']=='RUNNING':time.sleep(5)
    record=json.loads(status.read_text())
    if record['status']!='PASS':return (variant,'BUILD_FAILED')
    repo=Path(record['cwd'])
    cmd=['python3','-B',str(w/'repo/team/workloads/unified-vdot/run-suite.py'),'--variant',variant,'--images',str(w/'runs'/(variant+'-images-02')),'--output',str(w/'runs'/(variant+'-suite-02')),'--emu',str(repo/'build/emu'),'--reference',str(refs[variant]),'--flash','/home/riscv/riscv-lab/t12-regression-20261013/repo/team/workloads/hello-vadd/build/boot-flash.bin','--jobs','8']
    with (w/'runs'/(variant+'-suite-driver.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    print(variant+' SUITE_EXIT '+str(r.returncode),flush=True)
    return variant,r.returncode
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(run,('shishui','redoop')))
print(results,flush=True)
if any(code!=0 for variant,code in results):raise SystemExit(1)
