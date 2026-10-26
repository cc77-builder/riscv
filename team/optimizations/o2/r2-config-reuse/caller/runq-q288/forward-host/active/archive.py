"""Seal active-forward raw evidence and replay solely from archived source/ELF.

The fresh Python process is a reproducibility test, not an OS security sandbox.
It rebuilds the host library and repeats actual model-driven forward states.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,importlib.util,json,os,signal,subprocess,sys,tempfile,time,zipfile
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('active_archive_check',HERE/'check.py')
active=importlib.util.module_from_spec(spec);spec.loader.exec_module(active)
FORMAT='r2-s3-active-forward-raw-v1'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,why):
    if not ok:raise ValueError(why)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def relative(name):
    p=PurePosixPath(name)
    need(bool(p.parts) and not p.is_absolute() and '..' not in p.parts and
         str(p)==name and '\\' not in name and '\0' not in name,'canonical relative archive path')
    return p
def state_artifact(name):
    parts=PurePosixPath(name).parts
    return bool(parts) and parts[0] in ('normal','corrupt-k','corrupt-v','omit-output') and (
        name.endswith('.bin') or parts[-1] in ('callbacks.jsonl','certificate.json','result.json','events.txt'))

def pack(repo,run,out):
    need(not out.exists() and not out.is_relative_to(repo) and not out.is_relative_to(run),
         'new archive outside source and raw input')
    accepted=run/'check-03';result=json.loads((accepted/'result.json').read_text())
    need(result['status']=='ACTIVE_FORWARD_AND_PROPAGATION_CONTROLS_PASS' and
         result['source_files']==active.source_identity(repo),'accepted final active source')
    need(sha((accepted/'qualified-tail.elf').read_bytes())==active.ELF_SHA,'qualified actual ELF')
    out.mkdir(parents=True);selected=[]
    roots=('check-01','check-02','check-03')
    for label in roots:
        for p in sorted((run/label).rglob('*')):
            need(not p.is_symlink(),'no symlinks in active evidence')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.o':selected.append((p.relative_to(run).as_posix(),p.read_bytes()))
    for p in sorted(run.iterdir()):
        if p.is_file() and (p.name.startswith(('check-','receipt-','wrong-checkout.')) or p.name=='prepare.json'):
            selected.append((p.name,p.read_bytes()))
    # The default-archive-path failure happened before the normal snapshot was
    # written. Recover those exact source bytes and verify the contemporaneous pin.
    failed=json.loads((run/'check-02/source-pins.json').read_text())
    rel=(active.Q/'forward-host/active/check.py').as_posix()
    before=(accepted/'source-snapshot'/rel).read_text().replace('target-v1/archive/payload.zip','target-v1/payload.zip')
    need(sha(before.encode())==failed[rel],'hash-proven exact failed checker recovery')
    selected.append(('recovered-failure-source/check-02-check.py',before.encode()))
    recovery=dict(source='check-03/source-snapshot/'+rel,transformation='remove archive/ from fixed default payload path',
        verified_against='check-02/source-pins.json',sha256=failed[rel],original_failure_retained=True)
    selected.append(('recovered-failure-source/provenance.json',(json.dumps(recovery,indent=2)+'\n').encode()))
    auditors={'archive.py':Path(__file__).read_bytes(),'check.py':(HERE/'check.py').read_bytes()}
    selected.extend(('auditor/'+name,raw) for name,raw in auditors.items())
    rows=[];need(len({n for n,_ in selected})==len(selected),'unique archive member names')
    with zipfile.ZipFile(out/'raw.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,raw in sorted(selected):
            info=zipfile.ZipInfo(name,(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,raw);rows.append(dict(path=name,bytes=len(raw),sha256=sha(raw)))
    manifest=dict(format=FORMAT,contract=active.CONTRACT,accepted_run='check-03',files=rows,
        raw_bytes=sum(r['bytes'] for r in rows),stored_bytes=(out/'raw.zip').stat().st_size,
        payload_sha256=sha((out/'raw.zip').read_bytes()),source_files=result['source_files'],elf_sha256=active.ELF_SHA,
        auditor_sha256=sha(Path(__file__).read_bytes()),auditor_sources={n:sha(v) for n,v in auditors.items()},
        known_failures=['check-02 default archive path'],
        new_target_emu_runs=0)
    save(out/'manifest.json',manifest)
    # Reopen and hash every member; a written ZIP alone is not a completed seal.
    inspect(out)
    return dict(status='ACTIVE_FORWARD_RAW_ARCHIVE_PASS',files=len(rows),raw_bytes=manifest['raw_bytes'],
        stored_bytes=manifest['stored_bytes'],payload_sha256=manifest['payload_sha256'])

def inspect(archive):
    manifest=json.loads((archive/'manifest.json').read_text())
    need(manifest['format']==FORMAT and manifest['contract']==active.CONTRACT,'active archive format')
    need(manifest['accepted_run']=='check-03' and manifest['elf_sha256']==active.ELF_SHA,'fixed accepted run and ELF')
    for name in manifest['source_files']:relative(name)
    need(sha(Path(__file__).read_bytes())==manifest['auditor_sha256'],'same sealed active archive auditor')
    need(manifest['auditor_sources']=={n:sha((HERE/n).read_bytes()) for n in ('archive.py','check.py')},
         'matching standalone archive launcher sources')
    need(sha((archive/'raw.zip').read_bytes())==manifest['payload_sha256'],'raw ZIP identity')
    with zipfile.ZipFile(archive/'raw.zip') as z:
        need(len(z.namelist())==len(manifest['files']) and set(z.namelist())=={r['path'] for r in manifest['files']},'exact active archive inventory')
        for name,pin in manifest['auditor_sources'].items():
            need(sha(z.read('auditor/'+name))==pin,'sealed standalone launcher member '+name)
        for row in manifest['files']:
            relative(row['path'])
            raw=z.read(row['path']);need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'member identity '+row['path'])
    return manifest

def replay(archive,out):
    need(not out.exists() and not out.is_relative_to(archive),'fresh active replay outside archive')
    manifest=inspect(archive);out.mkdir(parents=True)
    needed=manifest['accepted_run']+'/';record={}
    with zipfile.ZipFile(archive/'raw.zip') as z:
        for row in manifest['files']:
            if row['path'].startswith(needed):record[row['path'][len(needed):]]=z.read(row['path'])
    before=json.loads(record['result.json']);need(before['source_files']==manifest['source_files'],'accepted source manifest')
    with tempfile.TemporaryDirectory(prefix='active-forward-source-replay-') as tmp:
        source=Path(tmp)/'source';source.mkdir();elf=Path(tmp)/'qualified-tail.elf';elf.write_bytes(record['qualified-tail.elf'])
        for name,pin in manifest['source_files'].items():
            raw=record['source-snapshot/'+name];need(sha(raw)==pin,'archived source '+name)
            dest=source/relative(name)
            need(dest.resolve().is_relative_to(source),'source extraction remains contained')
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        script=source/active.Q/'forward-host/active/check.py'
        env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
        argv=[sys.executable,'-I','-B',str(script),'--repo',str(source),'--output',str(out/'replay'),'--elf',str(elf)]
        receipt=dict(argv=argv,source_files=manifest['source_files'],elf_sha256=sha(elf.read_bytes()),
                     original_source_access_required=False,security_sandbox=False,status='STARTED',
                     started_unix=time.time(),timeout_seconds=1200)
        save(out/'launch.json',receipt)
        process=None
        try:
            with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
                process=subprocess.Popen(argv,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
                receipt.update(pid=process.pid,process_group=process.pid);save(out/'launch.json',receipt)
                process.wait(timeout=1200)
            receipt.update(status='EXITED',exit_code=process.returncode)
        except BaseException as error:
            receipt.update(status='TIMEOUT' if isinstance(error,subprocess.TimeoutExpired) else 'FAILED',error=repr(error))
            if process is not None:
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
                # The parent may exit before another member of its process group.
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                receipt.update(exit_code=process.returncode,process_group_cleanup_requested=True)
            raise
        finally:
            receipt['elapsed_seconds']=time.time()-receipt['started_unix'];save(out/'launch.json',receipt)
        need(process.returncode==0,'fresh source replay command; raw logs retained')
        after=json.loads((out/'replay/result.json').read_text())
        need(after['status']==before['status'] and after['source_files']==before['source_files'] and
             after['elf_sha256']==before['elf_sha256'] and after['results']==before['results'],
             'fresh source complete suite semantics')
        expected={name for name in record if state_artifact(name)}
        found={p.relative_to(out/'replay').as_posix() for p in (out/'replay').rglob('*')
               if p.is_file() and state_artifact(p.relative_to(out/'replay').as_posix())}
        need(expected==found,'complete archived and regenerated artifact inventories match')
        comparisons=[]
        for name in sorted(expected):
            raw=record[name]
            actual=(out/'replay'/name).read_bytes();need(raw==actual,'replayed complete state/callback identity '+name)
            comparisons.append(dict(path=name,bytes=len(raw),sha256=sha(raw)))
        need(sum(r['path'].endswith('-logits.bin') for r in comparisons)==22,
             '21 completed logits plus the omitted-output reference snapshot')
        need(all(sha((source/name).read_bytes())==pin for name,pin in manifest['source_files'].items()),'fresh sources unchanged')
    result=dict(status='ACTIVE_FORWARD_ARCHIVED_SOURCE_REPLAY_PASS',contract=active.CONTRACT,
        original_payload_sha256=manifest['payload_sha256'],comparisons=comparisons,files=len(comparisons),
        compared_bytes=sum(r['bytes'] for r in comparisons),new_model_calls=288,new_target_emu_runs=0,
        fresh_python_process=True,host_library_rebuilt=True,full_state_bytes_identical=True,
        original_source_checkout_required_by_child=False,os_security_sandbox=False)
    save(out/'result.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--action',choices=('pack','replay'),required=True)
    p.add_argument('--repo',type=Path);p.add_argument('--run',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    result=pack(a.repo.resolve(),a.run.resolve(),a.output.resolve()) if a.action=='pack' else replay(a.archive.resolve(),a.output.resolve())
    print(json.dumps({k:v for k,v in result.items() if k!='comparisons'},indent=2))
