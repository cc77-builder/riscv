import gzip,hashlib,json
from pathlib import Path
root=Path('C:/Code/RVInno/riscv')
base=root/'team/optimizations/o1/evidence'
results=[]
for name,leaf in [('20261018-parent-validation','manifest.json'),('20261018-fullcore-validation','archive-manifest.json'),('20261018-performance-ab','archive-manifest.json')]:
 p=base/name; manifest=json.loads((p/leaf).read_text()); files=manifest['files']; errors=[]
 rows=files if isinstance(files,list) else [{'path':k,'sha256':v} for k,v in files.items()]
 for row in rows:
  body=(p/row['path']).read_bytes()
  if hashlib.sha256(body).hexdigest()!=row['sha256'] or ('bytes' in row and len(body)!=row['bytes']): errors.append(row['path'])
 mapping=p/'file-map.json';mapped=0
 if mapping.exists():
  for row in json.loads(mapping.read_text()):
   body=(p/row['archive']).read_bytes()
   original=gzip.decompress(body) if row['storage']=='gzip' else body
   if hashlib.sha256(original).hexdigest()!=row['source_sha256'] or len(original)!=row['source_bytes']:errors.append(row['archive']+':raw')
   mapped+=1
 results.append({'archive':name,'sealed_files':len(rows),'mapped_original_bytes_verified':mapped,'errors':errors})
out=root/'team/out/latest-merge-standards/archive-hashes.json';out.write_text(json.dumps(results,indent=2));print(json.dumps(results))
