"""Seal fixed-weight raw evidence with the unchanged parent archive engine.

Both this adapter and the parent engine are bound in the manifest. Offline audit
recomputes all raw results; it does not claim current external-input revalidation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import run as e

g=e.g
engine=g.load('fixed_weight_archive_engine',e.PARENT_DIR/'archive.py')
BASE_AUDIT=engine.audit
GUARD=Path('team/optimizations/o2/repro/evidence/clean-reproduction-v1/analysis/detached-audit.py')
GUARD_SHA='57f31bb70dafa3154dc22e09c635dde1f4c140405717d98053d781dc2ca43cd4'
PARENT_ARCHIVE_SHA='85d9823ef722e72310293d20eb731bd167804b9bd8c69e0ba0062ea16ca93990'

def clean_environment():
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_') and k not in ('PYTHONPATH','PYTHONHOME')}
    env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_SYSTEM=os.devnull,
               GIT_NO_REPLACE_OBJECTS='1')
    return env

def historical_spec():
    frozen=e.parent.t17.a.frozen_f
    return frozen.g.BASE,[p.as_posix() for p in frozen.CHECKER_PATHS if p!=frozen.H1DIR/'build_profile.py']

def pack_history(repo,out):
    """Archive original objects needed by the six frozen git-show comparisons."""
    out.mkdir(parents=True,exist_ok=False);base,paths=historical_spec();commands=[]
    git=shutil.which('git');g.require(git is not None,'Git required for frozen checker provenance')
    def call(args,data=None):
        argv=[git,*args];start=e.now()
        p=subprocess.run(argv,cwd=repo,input=data,capture_output=True,timeout=30,env=clean_environment())
        commands.append(dict(command=argv,cwd=str(repo),started=start,finished=e.now(),exit_code=p.returncode,
            stdout_bytes=len(p.stdout),stdout_sha256=e.digest(p.stdout),stderr=p.stderr.decode(errors='replace')))
        g.save(out/'commands.json',commands);g.require(p.returncode==0,'historical Git export failed')
        return p.stdout
    specs={base:'commit',base+'^{tree}':'tree'}
    for name in paths:
        path=Path(name)
        for ancestor in path.parents:
            if ancestor!=Path('.'):specs[base+':'+ancestor.as_posix()]='tree'
        specs[base+':'+name]='blob'
    objects={};resolved={}
    for spec,kind in specs.items():
        oid=call(['rev-parse','--verify',spec]).decode().strip();resolved[spec]=oid
        g.require(len(oid)==40 and all(c in '0123456789abcdef' for c in oid),'original Git object identity')
        if oid in objects:
            g.require(objects[oid]['type']==kind,'inconsistent original Git type');continue
        raw=call(['cat-file',kind,oid])
        g.require(hashlib.sha1((kind+' '+str(len(raw))+'\0').encode()+raw).hexdigest()==oid,'Git content-address check')
        objects[oid]=dict(type=kind,bytes=len(raw),sha256=e.digest(raw))
    for name in paths:
        pin=objects[resolved[base+':'+name]]
        g.require(g.sha(repo/name)==pin['sha256'],'historical checker/current bytes differ: '+name)
    packed=call(['-c','pack.threads=1','pack-objects','--stdout'],('\n'.join(sorted(objects))+'\n').encode())
    (out/'objects.pack').write_bytes(packed)
    manifest=dict(format='fixed-weight-frozen-git-objects-v1',base=base,checker_paths=paths,objects=objects,
        resolved_specs=resolved,pack_sha256=e.digest(packed),pack_bytes=len(packed),
        command_sha256=g.sha(out/'commands.json'),source_root=str(repo),
        scope='original commit, ancestor trees and six checker blobs only; not a complete development repository')
    g.save(out/'manifest.json',manifest);return manifest

def history_manifest(archive):
    path=archive/'history';m=e.read(path/'manifest.json');base,paths=historical_spec()
    g.require(m['format']=='fixed-weight-frozen-git-objects-v1' and m['base']==base and m['checker_paths']==paths and
        g.sha(path/'objects.pack')==m['pack_sha256'] and (path/'objects.pack').stat().st_size==m['pack_bytes'] and
        g.sha(path/'commands.json')==m['command_sha256'],'frozen Git object transport identity')
    return m

def install_history(archive,source,out):
    """Initialize only archived original objects, without templates or alternates."""
    history=history_manifest(archive);setup=[];git=shutil.which('git')
    g.require(git is not None and not (source/'.git').exists(),'fresh Git provenance repository')
    for argv,data in (([git,'init','-q','--template=','--object-format=sha1',str(source)],None),
                     ([git,'-C',str(source),'index-pack','--stdin'],(archive/'history/objects.pack').read_bytes()),
                     ([git,'-C',str(source),'update-ref','--no-deref','HEAD',history['base']],None)):
        p=subprocess.run(argv,input=data,capture_output=True,timeout=30,env=clean_environment())
        setup.append(dict(command=argv,exit_code=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'),
            input_sha256=e.digest(data) if data is not None else None))
        g.save(out/'source-setup.json',setup);g.require(p.returncode==0,'source-only probe Git preparation')
    for name in ('alternates','http-alternates'):
        g.require(not (source/'.git/objects/info'/name).exists(),'no original Git object cache')
    return history

def tools():
    g.require(g.sha(e.ROOT/GUARD)==GUARD_SHA,'unchanged frozen dependency probe')
    g.require(g.sha(e.PARENT_DIR/'archive.py')==PARENT_ARCHIVE_SHA,'unchanged parent archive engine')
    return {p.relative_to(e.ROOT).as_posix():g.sha(p) for p in
        (Path(__file__).resolve(),e.PARENT_DIR/'archive.py',e.ROOT/GUARD)}

def audit(repo,build,run):
    with e.adapt(engine,e=e,g=g):result=BASE_AUDIT(repo,build,run)
    m=e.read(build/'source/manifest.json')
    result.update(status='FIXED_WEIGHT_RAW_EVIDENCE_AUDIT_PASS',
        windows_per_normal_run=len(m['plan']),replay_windows=len(m['plan']),
        formal_method_windows=m['formal_method_windows'],formal_anchor_windows=m['formal_anchor_windows'],
        functional_calls_per_normal_run=m['functional_calls'],judge_fault_controls=m['judge_fault_controls'],
        committed_vdot_per_normal_run=m['expected_dots'],audit_tool_sources=tools())
    return result

def pack(build,run,out):
    with e.adapt(engine,e=e,g=g,audit=audit):result=engine.pack(build,run,out)
    history=pack_history(e.ROOT,out/'history')
    m=e.read(out/'archive-manifest.json');m['adapter_sources']=tools()
    m['historical_git']=dict(manifest_sha256=g.sha(out/'history/manifest.json'),pack_sha256=history['pack_sha256'])
    g.save(out/'archive-manifest.json',m)
    return dict(result,status='FIXED_WEIGHT_EVIDENCE_PACKED',archive_manifest_sha256=g.sha(out/'archive-manifest.json'))

def unpack(archive,out):
    m=e.read(archive/'archive-manifest.json');history=history_manifest(archive)
    g.require(m.get('adapter_sources')==tools(),'fixed-weight archive adapter identity')
    g.require(m.get('historical_git')==dict(manifest_sha256=g.sha(archive/'history/manifest.json'),
        pack_sha256=history['pack_sha256']),'archive historical Git binding')
    with e.adapt(engine,e=e,g=g):return engine.unpack(archive,out)

def audit_archive(archive):
    with tempfile.TemporaryDirectory(prefix='fixed-weight-raw-audit-') as tmp:
        root=Path(tmp)/'restored';m=unpack(archive,root)
        result=audit(e.ROOT,root/'build',root/'run')
        g.require(result==e.read(archive/'original-audit.json'),'fixed-weight restored raw result differs')
    return dict(result,status='FIXED_WEIGHT_ARCHIVE_RAW_AUDIT_PASS',archive_manifest_sha256=g.sha(archive/'archive-manifest.json'),
        files=len(m['files']),raw_bytes=m['raw_bytes'],stored_bytes=m['stored_bytes'])

def audit_snapshot(archive,out):
    """Recompute in a fresh process with only archived source closure + auditors."""
    out.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='fixed-weight-closure-audit-') as tmp:
        root=Path(tmp)/'restored';m=unpack(archive,root)
        source=Path(tmp)/'source';shutil.copytree(root/'build/source/repo',source)
        for rel,pin in tools().items():
            dest=source/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(e.ROOT/rel,dest);g.require(g.sha(dest)==pin,'fresh auditor bytes')
        identity=source/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
        identity.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/'run/parent-identity.json',identity)
        g.require(g.sha(identity)==e.parent.PARENT_IDENTITY_SHA,'archived default parent identity')
        # Preserve the old git-show gate. Only its original commit/tree/blob
        # objects are imported, with no alternates or original object cache.
        history=install_history(archive,source,out)
        child=source/Path(__file__).resolve().relative_to(e.ROOT)
        report=Path(tmp)/'child-audit.json';guard_report=Path(tmp)/'guard.json'
        cfg=e.read(root/'run/configuration.json');br=e.read(root/'build/build.json')
        original_run=Path(e.read(root/'run/runs/recovery/result.json')['cwd']).parents[2]
        denied=[str(e.ROOT),str(Path(br['build_root']).parent),str(original_run),cfg['hardware_source'],cfg['build_record'],
            cfg['am_home'],str(Path(cfg['reference']).parent),str(Path(cfg['flash']).parent)]
        argv=[sys.executable,'-I','-B',str(source/GUARD),'--checkout',str(source),'--script',str(child),
            '--report',str(guard_report)]
        for path in denied:argv.extend(['--deny-root',path])
        argv.extend(['--','--action','audit','--build',str(root/'build'),
              '--run',str(root/'run'),'--output',str(report)])
        p=subprocess.run(argv,cwd=source,capture_output=True,timeout=180,env=clean_environment())
        for n,data in (('stdout.log',p.stdout),('stderr.log',p.stderr)):(out/n).write_bytes(data)
        receipt=dict(command=argv,cwd=str(source),exit_code=p.returncode,
            python=dict(path=sys.executable,sha256=g.sha(sys.executable)),
            raw_sha256={n:g.sha(out/n) for n in ('stdout.log','stderr.log')},
            archived_source_files=len(e.read(root/'build/build.json')['software_files']),
            supplementary_auditors=tools(),parent_identity_sha256=g.sha(identity),
            historical_git_manifest_sha256=g.sha(archive/'history/manifest.json'),new_emu_runs=0)
        g.save(out/'command.json',receipt)
        if guard_report.exists():shutil.copyfile(guard_report,out/'guard.json')
        g.require(p.returncode==0,'fresh source closure audit failed; original stdout/stderr retained')
        guard=e.read(guard_report)
        g.require(guard['status']=='T17_DETACHED_AUDIT_PASS' and guard['guard_self_test'] and
            not guard['rejected_runtime_accesses'] and guard['auditor_output']['sha256']==g.sha(report),
            'fresh source dependency probe')
        result=e.read(report)
        g.require(result==e.read(archive/'original-audit.json'),'fresh source closure result differs')
    result=dict(result,status='FIXED_WEIGHT_ARCHIVE_FRESH_SOURCE_AUDIT_PASS',
        archive_manifest_sha256=g.sha(archive/'archive-manifest.json'),command_sha256=g.sha(out/'command.json'),
        files=len(m['files']),raw_bytes=m['raw_bytes'],stored_bytes=m['stored_bytes'],
        fresh_python_process=True,full_git_history_required_by_child=False,source_checkout_required_by_launcher=True,
        archived_original_git_objects=len(history['objects']),dependency_probe_sha256=g.sha(out/'guard.json'),
        dependency_scope='Python filesystem/enumeration and explicit subprocess paths; not an OS sandbox')
    g.save(out/'result.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action',choices=('audit','pack','audit-archive','audit-snapshot','unpack'),required=True)
    for n in ('build','run','archive'):p.add_argument('--'+n,type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();g.require(not out.exists(),'fresh evidence output')
    roots=[e.ROOT]+[v.resolve() for v in (a.build,a.run,a.archive) if v]
    identity=e.ROOT/e.parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json'
    cfg=e.parent.parent_identity(e.ROOT,identity)['configuration']
    roots.extend([identity.parent]+[cfg[k] for k in ('am_home','hardware_source','build_record')])
    e.parent.outside_inputs(out,roots)
    if a.action in ('audit-archive','audit-snapshot','unpack'):
        g.require(a.archive is not None,'archive required')
        if a.action=='unpack':result=unpack(a.archive.resolve(),out)
        elif a.action=='audit-snapshot':result=audit_snapshot(a.archive.resolve(),out)
        else:result=audit_archive(a.archive.resolve());g.save(out,result)
    else:
        g.require(a.build and a.run,'build/run required')
        if a.action=='pack':result=pack(a.build.resolve(),a.run.resolve(),out)
        else:result=audit(e.ROOT,a.build.resolve(),a.run.resolve());g.save(out,result)
    print(json.dumps(result,indent=2))
