import os,sys,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/input-02")
pins=json.loads("[{\"path\":\"controller/BOOTH_CONTRACT.md\",\"bytes\":4823,\"sha256\":\"be1bb568849c8d431c9df82b6fac4885d55865cc7bd5a657b9c535211631960c\"},{\"path\":\"controller/booth3.py\",\"bytes\":51820,\"sha256\":\"9ced0b6414e37af9369e7ae5793f3dc8d1b6cb0f6a2f3e38c003c36f688e7bcd\"},{\"path\":\"controller/CONTROLLER_REVIEW.md\",\"bytes\":3992,\"sha256\":\"cbc6188f28778bf437bd7106cb1c82e5a4864513fe0f0d65cc721692cbd87261\"},{\"path\":\"controller/controller-derivation.json\",\"bytes\":6510,\"sha256\":\"ada7b1c636c9a2c8c8913a42a502ec40128af575eb944efea2ecb56252eaef71\"},{\"path\":\"controller/controller.diff\",\"bytes\":9932,\"sha256\":\"8d68d1aaeb45cc3fe5ef88f581fff233dece767eedccf12cf0040d84e9c2e8ea\"},{\"path\":\"controller/verifier-derivation.json\",\"bytes\":1333,\"sha256\":\"e085ca5d3b32b43012c3acc9d488dc9c3de64cdf397ad674b2e4388aee6d3958\"},{\"path\":\"controller/verify_booth.py\",\"bytes\":17469,\"sha256\":\"c0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587\"},{\"path\":\"decision-review-pro2.json\",\"bytes\":1757,\"sha256\":\"c28881d06968ff7d5b8a4d213cf959914d517d378886d668e001f1ccbd85a274\"},{\"path\":\"derive_controller.py\",\"bytes\":7644,\"sha256\":\"f42baf35445d32535f63063d09dd624cdde79e436c192db422c38cc63509d93e\"},{\"path\":\"source/source-derivation.json\",\"bytes\":18751,\"sha256\":\"202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876\"},{\"path\":\"source/source.diff\",\"bytes\":7118,\"sha256\":\"995befd1eaf229d3d0567daa8f0204cb4a3ab5007612922c3c8fa51c00f9ee6b\"},{\"path\":\"source/VDotDatapath.scala\",\"bytes\":10266,\"sha256\":\"880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680\"},{\"path\":\"source/VDotElastic.scala\",\"bytes\":9181,\"sha256\":\"1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238\"}]")
for item in pins:
 p=root/item['path'];b=p.read_bytes()
 assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],str(p)
stage=root/'SOURCE_STAGING.json';sb=stage.read_bytes()
assert len(sb)==2535 and hashlib.sha256(sb).hexdigest()=='bd153c5df2074a01f0ddfe88cda0f8b4c45d3ef1a4401f91a630b794c324a845','exact staging receipt'
s=json.loads(sb)
assert s['status']=='BOOTH3_BALANCED_INPUT_STAGING_VERIFIED' and s['files']==pins and s['source_unchanged'] and s['all_bytes_verified'] and s['new_runtime_commands']==0
args=json.loads("{\"repo\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source\",\"cost-root\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-production-cost-20261107-main\",\"fu-root\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-production-20261106-0014-pro2\",\"signed8-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-inline-signed8-20261107-main/local-03\",\"rwidth-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-rwidth-20261107-main/local-01\",\"csa-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-csa-20261107-main/local-03\",\"prefix-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/local-01\",\"output\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/local-02\",\"cpu\":\"2\",\"budget-seconds\":\"300\",\"previous-failed\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/local-01\"}")
out=Path(args['output']);assert not out.exists() and not out.is_symlink(),'output already exists'
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()}
assert mem['MemAvailable']>=6*1024*1024,'less than6GiB available; no controller launch'
assert shutil.disk_usage(root).free>=536870912,'less than512MiB free; no controller launch'
heavy=[]
for q in Path('/proc').iterdir():
 if not q.name.isdecimal():continue
 try:
  name=(q/'comm').read_text().strip()
  if name in ('java','emu','yosys','berkeley-abc','sta','verilator_bin','clang','clang++','clang++-19','make','cc1plus','ninja'):
   aff=sorted(os.sched_getaffinity(int(q.name)));heavy.append(dict(pid=int(q.name),name=name,affinity=aff))
   assert 2 not in aff,'CPU2 engineering conflict '+str(q)
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
used={2}
for x in heavy:used.update(x['affinity'])
assert len(used)<=4,'aggregate CPU budget'
assert datetime.now(timezone.utc)<datetime(2026,11,8,6,45,tzinfo=timezone.utc),'latest planned actual start passed'
if os.getpgrp()!=os.getpid():os.setsid()
argv=['/usr/bin/python3','-B',str(root/'controller/booth3.py')]
for key,value in args.items():argv.extend(['--'+key,value])
print(json.dumps(dict(status='BOOTH3_BALANCED_LAUNCH',started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,source_staging_sha256=hashlib.sha256(sb).hexdigest(),input_files=len(pins),argv=argv)),flush=True)
os.chdir(root)
os.execv(argv[0],argv)
