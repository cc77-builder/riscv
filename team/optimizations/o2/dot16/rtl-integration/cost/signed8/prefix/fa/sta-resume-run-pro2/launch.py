#!/usr/bin/env python3
"""Single-use preflight and exec wrapper for the chief's frozen STA continuation."""
import datetime, hashlib, json, os, pathlib, signal, sys, time
ROOT=pathlib.Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main')
SOURCE=ROOT/'input-sta-02'/'fa_sta_resume.py'
CONTRACT=SOURCE.with_name('STA_RESUME_CONTRACT.md')
PLAN=SOURCE.with_name('PLAN_ONLY.json')
OUT=ROOT/'sta-resume-01'
EXPECTED={
 'source':(16785,'258da7f1f301d1f70c51fee9f5d213f1ee8a833d3cadef197cf0ce4226c8a074'),
 'contract':(4353,'f81ea953a7db24fe64d45925326359e9a0ae827eda018a8af3711ce4f282e3d5'),
 'plan':(16512,'cf80fbb5908e93b4faa8beece2774c84038f31bd0ad289da9227a42230fa7d3f')
}
def need(ok,message):
    if not ok: raise RuntimeError(message)
def sha(b): return hashlib.sha256(b).hexdigest()
started=time.monotonic()
signal.alarm(25)
os.sched_setaffinity(0,{3});os.setpriority(os.PRIO_PROCESS,0,5)
need(sys.dont_write_bytecode,'-B is required')
need(os.getpid()==os.getpgrp()==os.getsid(0),'run under setsid --wait')
raw={}
for key,p in [('source',SOURCE),('contract',CONTRACT),('plan',PLAN)]:
    raw[key]=p.read_bytes()
    need((len(raw[key]),sha(raw[key]))==EXPECTED[key],'frozen '+key+' mismatch')
need(SOURCE.resolve()==SOURCE,'native source path must not be redirected')
plan=json.loads(raw['plan'])
need(plan['status']=='PLAN_ONLY' and plan['output']==str(OUT),'expected frozen plan/output')
need(plan['cpu_affinity']==[3] and plan['nice']==5 and plan['budget_seconds']==60 and plan['sta_seconds']==30,'fixed resource budget')
need(all(plan[k]==0 for k in ('new_yosys_runs','new_mapping_runs','new_fu_runs','new_core_runs')),'no additional toolchain runs')
pins=plan['original_pins']
need(len(pins)==64,'complete frozen input count')
need(pins[str(SOURCE)]==EXPECTED['source'][1] and pins[str(CONTRACT)]==EXPECTED['contract'][1],'source pins bound into plan')
for name,h in pins.items():
    need(sha(pathlib.Path(name).read_bytes())==h,'frozen input mismatch: '+name)
need(not OUT.exists() and not OUT.is_symlink(),'fresh output only; no restart')
heavy=[]
names={'emu','java','firtool','yosys','sta','abc','berkeley-abc','make','ninja','cc1','cc1plus','ld','ld.lld','verilator','verilator_bin'}
for p in pathlib.Path('/proc').iterdir():
    if not p.name.isdigit() or int(p.name)==os.getpid(): continue
    try:
        comm=(p/'comm').read_text().strip()
        if comm not in names and not comm.startswith(('clang','verilator','gcc','g++')): continue
        tids=[int(t.name) for t in (p/'task').iterdir() if t.name.isdigit()]
        cpus=set()
        for tid in tids:
            try: cpus.update(os.sched_getaffinity(tid))
            except ProcessLookupError: pass
        heavy.append(dict(pid=int(p.name),comm=comm,threads=len(tids),cpu_affinity=sorted(cpus)))
    except FileNotFoundError: continue
need(all(3 not in p['cpu_affinity'] for p in heavy),'CPU3 has another heavy process')
need(all(set(p['cpu_affinity']) <= {0,1,2,3} for p in heavy),'other heavy process outside the four-core budget')
used={3}
for p in heavy: used.update(p['cpu_affinity'])
need(len(used)<=4,'total engineering CPU budget')
mem={}
for line in pathlib.Path('/proc/meminfo').read_text().splitlines():
    parts=line.split()
    if parts: mem[parts[0].rstrip(':')]=int(parts[1])
need(mem['MemAvailable']>=2*1024*1024,'available memory below 2 GiB')
need(sha(PLAN.read_bytes())==EXPECTED['plan'][1],'plan changed during preflight')
need(time.monotonic()-started<25,'preflight budget')
record=dict(status='STA_LAUNCH_PREFLIGHT_PASS',
    at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    coordinator_pid=os.getpid(),coordinator_pgid=os.getpgrp(),coordinator_sid=os.getsid(0),
    cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),
    input_pins=len(pins),source=dict(path=str(SOURCE),bytes=EXPECTED['source'][0],sha256=EXPECTED['source'][1]),
    plan=dict(path=str(PLAN),bytes=EXPECTED['plan'][0],sha256=EXPECTED['plan'][1]),
    output=str(OUT),other_heavy=heavy,mem_available_kib=mem['MemAvailable'],
    preflight_seconds=time.monotonic()-started,exec_argv=['/usr/bin/python3','-B',str(SOURCE),'--execute'])
print(json.dumps(record,sort_keys=True),flush=True)
signal.alarm(0)
env=dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',TZ='UTC',
    OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
os.execve('/usr/bin/python3',record['exec_argv'],env)
