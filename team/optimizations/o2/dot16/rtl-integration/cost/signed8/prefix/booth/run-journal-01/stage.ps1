$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$self=[Diagnostics.Process]::GetCurrentProcess()
$self.PriorityClass='BelowNormal'
$self.ProcessorAffinity=[IntPtr]4
$py=@'
import os,json,hashlib,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-booth-20261108-main')
dst=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth-20261108-main/input-01')
items=json.loads("[{\"path\":\"controller/BOOTH_CONTRACT.md\",\"bytes\":7069,\"sha256\":\"85e449a5328e74a8894728e3d1c3816b081ded1ce4d39c79681ec2b45949300b\"},{\"path\":\"controller/booth9.py\",\"bytes\":46330,\"sha256\":\"6681fce5cc739206c5922e025d76ae0a75334d57502b089902b5a7a72f05ea60\"},{\"path\":\"controller/CONTROLLER_REVIEW.md\",\"bytes\":6783,\"sha256\":\"012b8f61af04157f4a5503a8f647008800ff690e5c24257c50f6dcbb2ef6843d\"},{\"path\":\"controller/controller-derivation.json\",\"bytes\":14468,\"sha256\":\"68ea0c414c37d4f7aedefd301bc078defef8067acc077009957ce671361068f3\"},{\"path\":\"controller/controller.diff\",\"bytes\":20783,\"sha256\":\"da0d6b641a0131b4c7ffe4f34e732e0a3b55c939d6433be1169eb734c7aef6a4\"},{\"path\":\"controller/verify_booth.py\",\"bytes\":17407,\"sha256\":\"b3044e637a5f312b71497de1eaa44503e27894cb7fd313ee389208a8fc351dc5\"},{\"path\":\"derive_controller.py\",\"bytes\":12392,\"sha256\":\"a46be79afdff960023d49899978fb37f00e50025d7134c4ead4ad77867f42427\"},{\"path\":\"derive_source.py\",\"bytes\":9267,\"sha256\":\"a6a28232c07ba54dd1a3390da584ef1cffcf158cba5e7090f26da76e9f025e02\"},{\"path\":\"derive_verifier.py\",\"bytes\":11325,\"sha256\":\"9579bbd6d605b9bd123da7930a6e0b09faeb0223d1de985d5ccf68197461da18\"},{\"path\":\"preparation-controller-01/controller/booth9.py\",\"bytes\":45888,\"sha256\":\"2ba914651f50a0b5557a2aeb8ba879a37f921452cc0899d012e5fa24d2f2da7f\"},{\"path\":\"preparation-controller-01/controller/controller-derivation.json\",\"bytes\":12287,\"sha256\":\"93744f3439ed5e5d083f762e149999ae375e250e2125576206ee91d1d1265eb0\"},{\"path\":\"preparation-controller-01/controller/controller.diff\",\"bytes\":18017,\"sha256\":\"5ce0aecd806429e1a5ca22b3fa05e242b66ab3ad64dbedccfc86a2d1e5049130\"},{\"path\":\"preparation-controller-01/derive_controller.py\",\"bytes\":10509,\"sha256\":\"f44ffa16ec72fa59f8c9d26741f50ab93e355c82b6ce949678fe2661c9352be2\"},{\"path\":\"preparation-controller-01/PREPARATION.json\",\"bytes\":890,\"sha256\":\"034d8e92fccadcfff3d7ffb6cb8dd03d822a602f6c395961fde0d88783312e48\"},{\"path\":\"review-pro2/BOOTH_DECISION_REVIEW.md\",\"bytes\":8093,\"sha256\":\"ac906dcb1e661f6166b33e1ddb8412bc8f69bf38becc2fc70ccc525784fbca18\"},{\"path\":\"review-pro2/booth_math_review_result.json\",\"bytes\":6456,\"sha256\":\"64677b4994192edd11c62b42a77a3e1dbfd10bbb73f9fe913b1ac3899b8ea9c8\"},{\"path\":\"review-pro2/booth_math_review.py\",\"bytes\":5570,\"sha256\":\"df1c4791ca6469ad56eba3563fb7778f6976a7a0ea6a8b7a5c8ce09e924b29e5\"},{\"path\":\"review/arithmetic/ARITHMETIC_REVIEW.md\",\"bytes\":4673,\"sha256\":\"9c128dfc84b162fede1209c2506a5a73f1c61a44fe3df190717175b7ae111f71\"},{\"path\":\"review/arithmetic/arithmetic-result.json\",\"bytes\":4091,\"sha256\":\"48430b16886e56284ef391617aabae24c8581f5c6addb5339753e004d77d4a9c\"},{\"path\":\"review/arithmetic/check_arithmetic.py\",\"bytes\":10317,\"sha256\":\"ccfa4dab5024659ffd9c57a79f84ddeb42a2a1ceeeb760312e6fd7ad57adc9aa\"},{\"path\":\"review/checker_fixture_review.py\",\"bytes\":8163,\"sha256\":\"583c50518c5368677f129514e58a6e7fe4140822b2216d2ffebbd3a27fa6206a\"},{\"path\":\"review/CHECKER_TEST_RESULT.json\",\"bytes\":7313,\"sha256\":\"cff768d85a5f658484aa16769a50efb51e9b0b5387b6376868f157268dbbb34b\"},{\"path\":\"review/checker-fixtures/extra-unknown-output-text.sv\",\"bytes\":77253,\"sha256\":\"4b7dd4eea0b69860f89f42b7517469e6675e594a41e7a087ba0c1641120acff8\"},{\"path\":\"review/checker-fixtures/missing-bias-bit18.sv\",\"bytes\":77228,\"sha256\":\"09c1077cb01928e053ad30c4d921d4660b4050e94b3aff7e977de6f880e06d88\"},{\"path\":\"review/checker-fixtures/missing-neg-correction.sv\",\"bytes\":76986,\"sha256\":\"c7dd51b489b6db03eab5a428e5f54bb18d9142f3c27083c8f7dac170412d601b\"},{\"path\":\"review/checker-fixtures/missing-sign-bit-inversion.sv\",\"bytes\":77225,\"sha256\":\"a827883f7b0399b9b77ac944ca2f82bae3a75f217cd78d41684a38728df7105e\"},{\"path\":\"review/checker-fixtures/synthetic-correct.sv\",\"bytes\":77228,\"sha256\":\"715b257a8bb84af07568436f2320737ba9cac40f2b24051c13419033049c37f6\"},{\"path\":\"review/checker-fixtures/wrong-input-lane.sv\",\"bytes\":77228,\"sha256\":\"2e99280f721d049c27fe4e2448c9389832982692f8cd4100ef3a4e7b9078a90a\"},{\"path\":\"review/checker-fixtures/wrong-neg-control.sv\",\"bytes\":77228,\"sha256\":\"e38b6b5e7b7d5f8dc31bc21bbc89f30612301a0ce60789bccc1f919fb1c192aa\"},{\"path\":\"review/checker-fixtures/wrong-neg-weight.sv\",\"bytes\":77131,\"sha256\":\"95b0eee9a6c9f47a4860cfba8466710c7361cc7b3917f9c3d9e90e58283e0c88\"},{\"path\":\"review/INDEPENDENT_REVIEW.md\",\"bytes\":6902,\"sha256\":\"d34a92c14bd04a5abd9ad14a7273d0af9dd8aedf77227b5ccb1593623e92bc14\"},{\"path\":\"source/source-derivation.json\",\"bytes\":11734,\"sha256\":\"72b19ecbc899c0175c86a31e1032607b65897999c17117e2de21f21fac7c7eae\"},{\"path\":\"source/source.diff\",\"bytes\":7264,\"sha256\":\"05aa4a4e2f04bd2b89b6830417f6fa709626e484112af585323354860a24d7e3\"},{\"path\":\"source/VDotDatapath.scala\",\"bytes\":9711,\"sha256\":\"f0a8bbe58440c6113aa56f848387c6b4e4a487d71ec2832a1e43fca55d3a8245\"},{\"path\":\"source/VDotElastic.scala\",\"bytes\":9049,\"sha256\":\"0fcc5df10355ee1e6382678ba40bc9d7ddf830b560dcc469c46e6a6888441556\"}]")
assert not dst.exists() and not dst.is_symlink(),'input staging destination already exists'
data={}
for item in items:
 p=src/item['path'];assert stat.S_ISREG(p.lstat().st_mode)
 b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],str(p)
 data[item['path']]=b
dst.mkdir(parents=True,exist_ok=False)
for item in items:
 p=dst/item['path'];p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data[item['path']])
 assert p.read_bytes()==data[item['path']]
for item in items:
 assert (src/item['path']).read_bytes()==data[item['path']],'source changed while staging'
assert {str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()}==set(data)
result=dict(status='BOOTH9_INPUT_STAGING_VERIFIED',source=str(src),destination=str(dst),files=items,total_bytes=sum(i['bytes'] for i in items),source_unchanged=True,all_bytes_verified=True,new_runtime_commands=0)
doc=(json.dumps(result,indent=2)+'\n').encode()
with (dst/'SOURCE_STAGING.json').open('xb') as f:f.write(doc)
print(json.dumps(dict(**result,staging_file_bytes=len(doc),staging_file_sha256=hashlib.sha256(doc).hexdigest())))

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
