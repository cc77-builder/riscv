"""Join published byte fragments without changing the frozen evidence ZIP.

This is transport verification only. Use archive.py verify for object/restore
checks, and recheck.py for numerical/protocol qualification from raw evidence.
"""
from pathlib import Path
import argparse
import hashlib
import json


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def restore(source,output):
    source,output=source.resolve(),output.resolve()
    need(source.is_dir() and not output.exists(),'existing archive and fresh output directory')
    need(not output.is_relative_to(source),'output outside archive source')
    encoded=(source/'parts.json').read_bytes();m=json.loads(encoded)
    need(m['format']=='forward-evidence-parts-v1' and m['artifact']=='payload.zip','known byte transport format')
    parts=m['parts'];need(parts and [p['path'] for p in parts]==[f'payload.zip.part-{i:04d}' for i in range(1,len(parts)+1)],'complete ordered fragment names')
    need(all(isinstance(p['bytes'],int) and p['bytes']>0 for p in parts) and sum(p['bytes'] for p in parts)==m['bytes'],'complete fragment sizes')
    metadata={}
    need(set(m['metadata']) in ({'manifest.json','verification.json'},{'manifest.json','verification.json','restore-verification.json'}),'exact original metadata set')
    for name,pin in m['metadata'].items():
        p=source/name;need(p.is_file() and not p.is_symlink(),'ordinary metadata file')
        raw=p.read_bytes();need(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'],'original metadata identity')
        metadata[name]=raw
    v=json.loads(metadata['verification.json'])
    need(v['status']=='ARCHIVE_BYTES_PASS' and (v['archive_sha256'],v['archive_bytes'])==(m['sha256'],m['bytes']),'original verified ZIP identity')
    for part in parts:
        p=source/part['path'];need(p.is_file() and not p.is_symlink() and p.stat().st_size==part['bytes'],'ordinary complete fragment')
    output.mkdir(parents=True);incomplete=output/'payload.zip.incomplete';whole=hashlib.sha256();total=0
    with incomplete.open('xb') as dest:
        for part in parts:
            local=hashlib.sha256();count=0
            with (source/part['path']).open('rb') as handle:
                for block in iter(lambda:handle.read(1024*1024),b''):
                    local.update(block);whole.update(block);count+=len(block);total+=len(block);dest.write(block)
            need(count==part['bytes'] and local.hexdigest()==part['sha256'],'complete original fragment identity')
    need(total==m['bytes'] and whole.hexdigest()==m['sha256'],'reassembled ZIP exactly equals frozen original')
    incomplete.rename(output/'payload.zip')
    (output/'parts.json').write_bytes(encoded)
    for name,raw in metadata.items():(output/name).write_bytes(raw)
    result=dict(status='ORIGINAL_FORWARD_ARCHIVE_REASSEMBLED',archive_sha256=whole.hexdigest(),archive_bytes=total,
        parts=len(parts),parts_manifest_sha256=sha(encoded),new_emu_runs=0,performance_qualified=False)
    (output/'transport-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(restore(a.archive,a.output),indent=2))
