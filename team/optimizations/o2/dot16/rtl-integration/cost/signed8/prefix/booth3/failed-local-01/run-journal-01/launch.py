import os,sys,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
root=Path("/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/input-01")
pins=json.loads("[{\"path\":\"controller/BOOTH_CONTRACT.md\",\"bytes\":5814,\"sha256\":\"805b354eb7001c1c2c5bf36ca00bf3e54138b37b6eff4f427068a278d9f2b8ca\"},{\"path\":\"controller/booth3.py\",\"bytes\":49573,\"sha256\":\"bcde44c580003a0a99e18cc30a2795a9c7a9af08ed56ef38a8f740987ec8241f\"},{\"path\":\"controller/CONTROLLER_REVIEW.md\",\"bytes\":5626,\"sha256\":\"910ee18f7617aa13b115f621c7b337303f15dd51ae6eec7c0fb8a309815606d0\"},{\"path\":\"controller/controller-derivation.json\",\"bytes\":10984,\"sha256\":\"265632793b2b1f74df2f78994ba375241db5a99173df6cf7601478ded0df1bf1\"},{\"path\":\"controller/controller.diff\",\"bytes\":17093,\"sha256\":\"adff88376e7f97d9205de4e25b0a71cf73e413e958a8903fc96c478bbb254a34\"},{\"path\":\"controller/verifier-derivation.json\",\"bytes\":1333,\"sha256\":\"e085ca5d3b32b43012c3acc9d488dc9c3de64cdf397ad674b2e4388aee6d3958\"},{\"path\":\"controller/verify_booth.py\",\"bytes\":17469,\"sha256\":\"c0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587\"},{\"path\":\"derive_controller.py\",\"bytes\":7750,\"sha256\":\"960d1824fa90b531b2bfae35b95927f948bb8045e664e25b9f5891c1d731d572\"},{\"path\":\"derive_source.py\",\"bytes\":9653,\"sha256\":\"37f42bc92375810f046bcb12730c98cec8c4f8318cd46087811fcb6e47f1f37e\"},{\"path\":\"review-pro2/actual-inputs.json\",\"bytes\":30977,\"sha256\":\"28b8832a1e55796e8d5dac748ff82e2b84d019aaab8c3f0206c8fe2b61570b53\"},{\"path\":\"review-pro2/mapping-and-library.json\",\"bytes\":3724,\"sha256\":\"ab22757c7377f172bec3d929ea5893bfe4aeac77251498f145b5c3335ec43be7\"},{\"path\":\"review-pro2/receipts.json\",\"bytes\":93057,\"sha256\":\"3a9da33ee39e8a6f230a10a3221321fd590aea3e40e2b6aacd7086bd95bec6fe\"},{\"path\":\"review-pro2/REVIEW.md\",\"bytes\":8145,\"sha256\":\"b887f94ea00b9b2ab9710f7a23a7cb6f2c3c59e7bedfe3d3a5cec646687c55f7\"},{\"path\":\"review/arithmetic/ARITHMETIC_REVIEW.md\",\"bytes\":3835,\"sha256\":\"0a855934f6b862751b87c07f6c37afdf2309d233e0afc51789d7b3f8decb4585\"},{\"path\":\"review/arithmetic/arithmetic-result.json\",\"bytes\":3084,\"sha256\":\"c85996c5ed6324af6a08264cad4542abe80a0b7f1c7be3943e9b5eff4762683d\"},{\"path\":\"review/arithmetic/check_arithmetic.py\",\"bytes\":9029,\"sha256\":\"b8d4d43789fdd6dceec1b6e8050addc65e5b6f0b6723f319fef9b1bfb87cedad\"},{\"path\":\"review/check_row2.py\",\"bytes\":4478,\"sha256\":\"668e826e4926a83faa5c0ca8fcd94176070d12f8d1ea6151d0856cfcbb7bc8db\"},{\"path\":\"review/INDEPENDENT_REVIEW.md\",\"bytes\":5849,\"sha256\":\"9efce8e444a01c3b3e05562094a5831a63266b570f2c1ad33c1b4b96397c3f49\"},{\"path\":\"review/row2-result.json\",\"bytes\":10718,\"sha256\":\"c1bc3518c3d6fa2a94e4372f98d10275b39400496e56ba864c63fc2caf327e8c\"},{\"path\":\"source/source-derivation.json\",\"bytes\":18751,\"sha256\":\"202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876\"},{\"path\":\"source/source.diff\",\"bytes\":7118,\"sha256\":\"995befd1eaf229d3d0567daa8f0204cb4a3ab5007612922c3c8fa51c00f9ee6b\"},{\"path\":\"source/VDotDatapath.scala\",\"bytes\":10266,\"sha256\":\"880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680\"},{\"path\":\"source/VDotElastic.scala\",\"bytes\":9181,\"sha256\":\"1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238\"}]")
for item in pins:
 p=root/item['path'];b=p.read_bytes()
 assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],str(p)
stage=root/'SOURCE_STAGING.json';sb=stage.read_bytes()
assert len(sb)==4153 and hashlib.sha256(sb).hexdigest()=='85b716d1851f26097838abdb274af7085cfa8ced6b467765d304e6cf99f208b1','exact staging receipt'
s=json.loads(sb)
assert s['status']=='BOOTH3_INPUT_STAGING_VERIFIED' and s['files']==pins and s['source_unchanged'] and s['all_bytes_verified'] and s['new_runtime_commands']==0
args=json.loads("{\"repo\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/checkout/source\",\"cost-root\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-production-cost-20261107-main\",\"fu-root\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-production-20261106-0014-pro2\",\"signed8-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-inline-signed8-20261107-main/local-03\",\"rwidth-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-rwidth-20261107-main/local-01\",\"csa-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-csa-20261107-main/local-03\",\"prefix-local\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main/local-01\",\"output\":\"/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/local-01\",\"cpu\":\"2\",\"budget-seconds\":\"1200\"}")
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
assert datetime.now(timezone.utc)<datetime(2026,11,8,7,0,tzinfo=timezone.utc),'latest planned actual start passed'
if os.getpgrp()!=os.getpid():os.setsid()
argv=['/usr/bin/python3','-B',str(root/'controller/booth3.py')]
for key,value in args.items():argv.extend(['--'+key,value])
print(json.dumps(dict(status='BOOTH3_LAUNCH',started=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),pgid=os.getpgrp(),cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),mem_available_kib=mem['MemAvailable'],other_heavy=heavy,source_staging_sha256=hashlib.sha256(sb).hexdigest(),input_files=len(pins),argv=argv)),flush=True)
os.chdir(root)
os.execv(argv[0],argv)
