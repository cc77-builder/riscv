"""Archive exact prepared input bytes without changing absolute-path contracts."""
from pathlib import Path
import hashlib,json,zipfile
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
preflight=json.loads((base/'input-preflight-04.json').read_text())
files=dict(preflight['strict_current_preflight']['receipt']['input_files'])
contract=base/'inputs/input-contract-v1.json'
files[str(contract)]=hashlib.sha256(contract.read_bytes()).hexdigest()
files.update(preflight['strict_current_preflight']['receipt']['driver_files'])
for kind in ('supplement-diagnostic','supplement-control'):
    for path in (base/'inputs'/kind).rglob('*'):
        if path.is_file():files[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
manifest=dict(schema_version=1,scope='exact prepared O5 inputs; original absolute paths remain bound',
              portable_execution=False,files=dict(sorted(files.items())))
target=base/'prepared-inputs-v3.zip'
seen=set()
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    archive.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
    for path,digest in sorted(files.items()):
        content=Path(path).read_bytes()
        if hashlib.sha256(content).hexdigest()!=digest:raise ValueError('input drift: '+path)
        if digest not in seen:
            archive.writestr('blobs/'+digest,content);seen.add(digest)
with zipfile.ZipFile(target) as archive:
    if archive.testzip() is not None:raise ValueError('archive CRC failure')
    for digest in seen:
        if hashlib.sha256(archive.read('blobs/'+digest)).hexdigest()!=digest:raise ValueError('archive blob drift')
receipt=dict(status='PREPARED_INPUT_ARCHIVE_VERIFIED',paths=len(files),unique_blobs=len(seen),
             bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
             portable_execution=False)
(base/'prepared-inputs-v3.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
