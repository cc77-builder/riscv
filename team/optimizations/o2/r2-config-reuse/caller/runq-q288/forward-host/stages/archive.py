"""Byte-preserving ZIP transport; equal files share one SHA256 object.

This verifies transport identity, not numerical correctness or performance.
Unpack recreates ordinary files in a fresh directory, with no symlinks.
"""
from pathlib import Path, PurePosixPath, PureWindowsPath
import argparse
import hashlib
import json
import re
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, why):
    if not ok: raise ValueError(why)


def safe(name):
    path=PurePosixPath(name)
    parts=name.split('/')
    need(name and not path.is_absolute() and not PureWindowsPath(name).drive and
         all(p not in ('','.','..') and p==p.rstrip(' .') and
             not PureWindowsPath(p).is_reserved() and
             not any(ord(c)<32 or c in '<>:"|?*\\' for c in p)
             for p in parts), 'safe portable relative member path')
    return path


def seal(inputs, output):
    need(not output.exists(), 'fresh archive directory')
    entries=[];objects={};names=set()
    for item in inputs:
        label,location=item.split('=',1);safe(label);need('/' not in label and label not in names,'unique root label')
        names.add(label);root=Path(location).resolve();need(root.is_dir(),'existing evidence root')
        for path in sorted(root.rglob('*')):
            need(not path.is_symlink(),'no evidence symlinks')
            if not path.is_file():continue
            raw=path.read_bytes();digest=sha(raw);name=label+'/'+path.relative_to(root).as_posix();safe(name)
            entries.append(dict(path=name,size=len(raw),sha256=digest))
            objects.setdefault(digest,path)
    manifest=dict(format='sha256-object-zip-v1',archiver_sha256=sha(Path(__file__).read_bytes()),
                  files=entries,file_count=len(entries),original_bytes=sum(r['size'] for r in entries),
                  unique_objects=len(objects),unique_bytes=sum(p.stat().st_size for p in objects.values()))
    output.mkdir(parents=True)
    encoded=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    with zipfile.ZipFile(output/'payload.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('manifest.json',encoded)
        for digest,path in sorted(objects.items()):
            raw=path.read_bytes();need(sha(raw)==digest,'source unchanged while sealing')
            z.writestr('objects/'+digest,raw)
    (output/'manifest.json').write_bytes(encoded)
    report=verify(output/'payload.zip')
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def verify(archive, output=None, expected=None):
    archive=Path(archive);digest=sha(archive.read_bytes())
    if expected:need(digest==expected,'published archive SHA256')
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();need(len(names)==len(set(names)),'unique ZIP member names')
        manifest=json.loads(z.read('manifest.json'))
        need(manifest['format']=='sha256-object-zip-v1','known transport format')
        files=manifest['files'];seen=set();sizes={}
        for record in files:
            path=record['path'];safe(path);folded=path.casefold()
            need(folded not in seen,'unique portable restored file path');seen.add(folded)
            key=record['sha256'];need(re.fullmatch('[0-9a-f]{64}',key) is not None,'SHA256 object name')
            need(isinstance(record['size'],int) and record['size']>=0,'bounded file length')
            need(key not in sizes or sizes[key]==record['size'],'same object has same length');sizes[key]=record['size']
        for path in seen:
            need(all('/'.join(path.split('/')[:i]) not in seen for i in range(1,len(path.split('/')))),
                 'no restored file is also a directory')
        need(set(names)=={'manifest.json'}|{'objects/'+key for key in sizes},'exact ZIP object membership')
        for key,size in sizes.items():
            raw=z.read('objects/'+key);need(len(raw)==size and sha(raw)==key,'every original object matches bytes')
        need(manifest['file_count']==len(files) and manifest['original_bytes']==sum(r['size'] for r in files)
             and manifest['unique_objects']==len(sizes) and manifest['unique_bytes']==sum(sizes.values()),'complete aggregate manifest')
        if output is not None:
            output=Path(output);need(not output.exists(),'fresh restore root');output.mkdir(parents=True)
            for record in files:
                path=output/record['path'];path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('xb') as handle:handle.write(z.read('objects/'+record['sha256']))
            for record in files:
                raw=(output/record['path']).read_bytes()
                need(len(raw)==record['size'] and sha(raw)==record['sha256'],
                     'final restored original byte identity')
    return dict(status='ARCHIVE_BYTES_PASS',archive_sha256=digest,archive_bytes=archive.stat().st_size,
                file_count=len(files),original_bytes=manifest['original_bytes'],unique_objects=len(sizes),
                restored=output is not None,performance_qualified=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    create=sub.add_parser('seal');create.add_argument('--input',action='append',required=True);create.add_argument('--output',type=Path,required=True)
    read=sub.add_parser('verify');read.add_argument('--archive',type=Path,required=True);read.add_argument('--output',type=Path);read.add_argument('--expected-sha256')
    args=parser.parse_args()
    result=seal(args.input,args.output) if args.action=='seal' else verify(args.archive,args.output,args.expected_sha256)
    print(json.dumps(result,indent=2))
