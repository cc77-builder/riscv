import os,json,hashlib,stat
from pathlib import Path
os.sched_setaffinity(0,{2});os.setpriority(os.PRIO_PROCESS,0,5)
src=Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-booth3-20261108-main/cost-resume-01/source')
dst=Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-booth3-20261108-main/input-cost-01')
items=json.loads("[{\"path\":\"CONTRACT.md\",\"bytes\":4319,\"sha256\":\"fc6267cc664d900c143e21017f96b6adcab401c03aae642e00032a9a291fcfe0\"},{\"path\":\"FIXED_INPUTS.json\",\"bytes\":2878,\"sha256\":\"6766593ac8cf131c2326ac40f5236ec8c16968d4178eb5e27dedfbe51716bcde\"},{\"path\":\"REVIEW-controller.md\",\"bytes\":3901,\"sha256\":\"46f902acd4b1420a4a04023157b4bcabcf4661df0d9b8dd55f7086e7d784a3b6\"},{\"path\":\"REVIEW-graph.md\",\"bytes\":6518,\"sha256\":\"fc801be2f67e6534d2835c23d9f1cfc9ad00bb9164c03fcc7e816ab32e17d402\"},{\"path\":\"cost_resume.py\",\"bytes\":21597,\"sha256\":\"317f1919138e0c2e69c9d48514667fe82a871a0ec4caf8d6cc5fb206390f594a\"},{\"path\":\"review-pro2/REVIEW.md\",\"bytes\":6777,\"sha256\":\"b3895d3c46dc34a397f8badb027f786f7a1de36151c2098f1eb5f8cf44e5fa57\"},{\"path\":\"review-pro2/actual-read.json\",\"bytes\":8235,\"sha256\":\"25c447e1241baeb0408b806b494a4015300ae6cd4aaf00b25cee5e9c6608832c\"},{\"path\":\"review-pro2/read-receipts.json\",\"bytes\":25419,\"sha256\":\"3af967f8022249ab97ccfc8440ca318775223a99116f1072b2c51a264a24481e\"}]")
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
result=dict(status='BOOTH3_COST_INPUT_STAGING_VERIFIED',source=str(src),destination=str(dst),files=items,total_bytes=sum(i['bytes'] for i in items),source_unchanged=True,all_bytes_verified=True,new_runtime_commands=0)
doc=(json.dumps(result,indent=2)+'\n').encode()
with (dst/'SOURCE_STAGING.json').open('xb') as f:f.write(doc)
print(json.dumps(dict(**result,staging_file_bytes=len(doc),staging_file_sha256=hashlib.sha256(doc).hexdigest())))
