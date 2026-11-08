$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]2
$py=@'
import os,json,hashlib,subprocess,stat,ast,datetime
from pathlib import Path
os.sched_setaffinity(0,{1});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-k768-20261108-main/source-01')
root=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k768-20261108-main')
dst=root/'input-01';out=root/'preflight-01'
items=json.loads("[{\"name\":\"run.py\",\"bytes\":25519,\"sha256\":\"984ff535756419240db26deaea96214b3ee98d65e30b0e10476abcd9cab06ac9\"},{\"name\":\"TARGET_CONTRACT.md\",\"bytes\":5429,\"sha256\":\"379fb985f0c403bea0245c7ffbebbc15a1177e1273a4ef34ba8519a3c3d655b3\"},{\"name\":\"source-derivation.json\",\"bytes\":2136,\"sha256\":\"b7ede00dad15845efb8f1079065af254537e001f436e1ea04b91107f1895e2dd\"}]")
assert not dst.exists() and not dst.is_symlink() and not out.exists()
original={}
for x in items:
 p=src/x['name'];assert stat.S_ISREG(p.lstat().st_mode);b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];original[x['name']]=b
j=json.loads(original['source-derivation.json']);derived=original['run.py'].decode()
assert hashlib.sha256(original['run.py']).hexdigest()==j['derived_sha256']
inverse=derived
for e in reversed(j['replacements']):
 assert inverse.count(e['replace'])==e['expected_occurrences']
 inverse=inverse.replace(e['replace'],e['find'])
old=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-k288-20261108-main/input-02/run.py').read_bytes()
assert len(old)==25519 and hashlib.sha256(old).hexdigest()==j['parent_sha256']=='d49d657f536d2cae77cbf14a01640799280e6fafb260529b8a22853fa7417ce3'
assert inverse.encode()==old
for name in ('prefix_hardware','guest_check','run'):
 def part(s):return ast.get_source_segment(s,next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name==name))
 assert part(old.decode())==part(derived)
dst.mkdir(parents=True,exist_ok=False)
for x in items:
 p=dst/x['name'];p.write_bytes(original[x['name']]);assert p.read_bytes()==original[x['name']]
base=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs')
argv=['/usr/bin/python3','-B',str(dst/'run.py'),'preflight','--reference-build',str(base/'dot16-packed-ws-20261107-main/reference-02'),'--reference-result-sha256','65de4aca20b86d7faaed7c11863297930d571ee2c97b2ad54bb15bdd4c72e4d0','--prefix-core-build',str(base/'dot16-prefix-20261107-main/core-build-02'),'--prefix-smoke-result',str(base/'dot16-prefix-20261107-main/core-smoke-02/result.json'),'--output',str(out),'--k','768','--cpu','1','--max-cycles','6000000','--budget-seconds','7200','--stream-limit','16777216']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(argv,cwd=dst,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150)
(dst/'PREFLIGHT.stdout').write_bytes(p.stdout);(dst/'PREFLIGHT.stderr').write_bytes(p.stderr)
for x in items:assert (src/x['name']).read_bytes()==(dst/x['name']).read_bytes()==original[x['name']]
audit=dict(status='PREFIX_K768_STAGED_PREFLIGHT',files=items,argv=argv,started=start,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest(),sources_unchanged=True,original_runner_inverse=True,prefix_hardware_guest_check_run_bytes_unchanged=True,new_emu_runs=0,new_builds=0,cpu_affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0))
if p.returncode==0:
 audit['preflight']=json.loads((out/'result.json').read_bytes())
(dst/'SOURCE_STAGING.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit));print(p.stdout.decode(errors='strict'))
if p.returncode: print(p.stderr.decode(errors='replace'),file=__import__('sys').stderr)
assert p.returncode==0,'preflight failed; no EMU started'

'@
$start=[Diagnostics.ProcessStartInfo]::new()
$start.FileName='C:\Windows\System32\wsl.exe'
$start.UseShellExecute=$false
$start.CreateNoWindow=$true
$start.RedirectStandardOutput=$true
$start.RedirectStandardError=$true
foreach($item in @('--distribution','Ubuntu-22.04','--exec','/usr/bin/python3','-B','-c',$py)){[void]$start.ArgumentList.Add($item)}
$p=[Diagnostics.Process]::new();$p.StartInfo=$start;[void]$p.Start()
$outTask=$p.StandardOutput.ReadToEndAsync();$errTask=$p.StandardError.ReadToEndAsync()
$p.WaitForExit()
$out=$outTask.GetAwaiter().GetResult();$err=$errTask.GetAwaiter().GetResult();$code=$p.ExitCode
$p.Dispose()
[Console]::Write($out)
if($err){[Console]::Error.Write($err)}
if($code -ne 0){throw ('WSL bounded operation exit '+$code)}
