"""Fail-closed source and runtime attribution shared by vdot/baseline drivers."""
import argparse
import hashlib
import json
import shlex
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DEPENDENCIES = {
    'resource/nanopb': '26e4b21317f88a66fb351f5aa3d8cc0083622b25',
    'resource/LibCheckpoint': '1d8905cc2803c242ef257569128c2e68bf4272aa',
    'resource/LibCheckpoint/resource/nanopb': '671672b4d7994a9b07a307ae654885c7202ae886',
    'resource/gcpt_restore': '5169da768d18f4682a489eaabe7c071df6d6ef88',
    'resource/softfloat/repo': 'a0c6494cdc11865811dec815d5c0049fba9d82a8',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def audit_repo(repo, revision, allowed=None, source_roots=('src','include','lib-include','source','generator'), generated=()):
    """Check tracked bytes and ALL files in input directories, without Git ignores.

    Generated config directories are recorded in the snapshot, not asserted to
    come from Git; their exact bytes are bound to the resulting binary later.
    Build outputs outside compiler input directories are not source inputs.
    """
    repo = Path(repo).resolve()
    allowed = allowed or {}
    require(git(repo,'rev-parse','HEAD').decode().strip()==revision, f'Revision mismatch: {repo}')
    tracked = {}
    snapshot = {}
    for entry in git(repo,'ls-tree','-rz','HEAD').split(b'\0'):
        if not entry:
            continue
        info, raw_name = entry.split(b'\t',1)
        mode, kind, oid = info.decode().split()
        name = raw_name.decode()
        if kind == 'commit':
            continue
        tracked[name] = oid
        path = repo/name
        require(path.exists(), f'Missing tracked input: {path}')
        data = path.readlink().as_posix().encode() if mode=='120000' else path.read_bytes()
        if name in allowed:
            require(digest(path)==allowed[name], f'Patched source digest mismatch: {name}')
        else:
            require(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==oid,
                    f'Tracked source differs: {path}')
        if path.is_symlink():
            require(path.resolve().is_relative_to(repo), f'External source symlink: {path}')
        snapshot[name] = digest(path)
    for name, wanted in allowed.items():
        require(digest(repo/name)==wanted, f'Patched source digest mismatch: {name}')
        snapshot[name] = wanted
    for directory in source_roots:
        base = repo/directory
        if not base.exists():
            continue
        for path in base.rglob('*'):
            name = path.relative_to(repo).as_posix()
            generated_input = any(name==g or name.startswith(g+'/') for g in generated)
            if path.is_symlink():
                require(name in tracked and path.resolve().is_relative_to(repo), f'Unknown source symlink: {path}')
            if not path.is_file():
                continue
            require(name in tracked or name in allowed or generated_input,
                    f'Unknown compiler input (including ignored paths): {path}')
            snapshot[name] = digest(path)
    return snapshot


def nemu_snapshot(repo):
    manifest = json.loads((ROOT/'team/patches/nemu/manifest.json').read_text())
    sources = audit_repo(repo,manifest['base_rev'],manifest['patched_source_sha256'],
                         generated=('include/config','include/generated/autoconf.h'))
    for relative,revision in DEPENDENCIES.items():
        child = Path(repo)/relative
        subset = audit_repo(child,revision)
        sources.update({relative+'/'+name:value for name,value in subset.items()})
        if (child/'CONFIG.mk').exists():
            sources[relative+'/CONFIG.mk'] = digest(child/'CONFIG.mk')
    # GCC/Clang dependency files bind headers actually consumed, including
    # ignored generated headers. Unknown project inputs fail instead of being
    # accepted simply because Git hides them.
    repo = Path(repo).resolve()
    for dependency in (repo/'build').rglob('*.d'):
        logical = dependency.read_text(errors='strict').replace('\\\n','')
        if ':=' in logical:
            # fixdep keeps the original GCC record as *.o.d; the replacement
            # file contains Make variables rather than file dependencies.
            continue
        for line in logical.splitlines():
            if ':' not in line:
                continue
            for name in shlex.split(line.split(':',1)[1]):
                path = (repo/name).resolve()
                if not path.is_relative_to(repo):
                    require(path.is_relative_to(Path('/usr')), f'External compiled input: {path}')
                    sources['@system/'+str(path)] = digest(path)
                    continue
                relative = path.relative_to(repo).as_posix()
                require(relative in sources, f'Unknown compiled header/source: {path}')
                require(digest(path)==sources[relative],f'Compiled input changed: {path}')
    return sources


def verify_sums(path):
    records = {}
    for line in Path(path).read_text().splitlines():
        expected,name = line.split('  ',1)
        require(digest(name)==expected, f'Build input/source digest mismatch: {name}')
        require(name not in records, f'Duplicate digest record: {name}')
        records[name] = expected
    require(records, f'Empty digest list: {path}')
    return records


def capture_build(evidence, data, kind, arch, mode, am=None):
    evidence, data = Path(evidence), Path(data).resolve()
    inputs = verify_sums(evidence/'inputs.sha256')
    require(str(data/'cases.jsonl') in inputs, 'Selected data is not a compiled input')
    result = dict(schema_version=1,kind=kind,arch=arch,mode=mode,data_dir=str(data),
                  source_sha256=verify_sums(evidence/'source.sha256'),
                  inputs_sha256=inputs,images_sha256=verify_sums(evidence/'workload.sha256'),
                  compiler_version=subprocess.check_output(['riscv64-linux-gnu-gcc','--version'],text=True))
    if am:
        am = Path(am).resolve()
        result['am_home'] = str(am)
        result['am_rev'] = '086a238062fdfb3281b745a537b361983d0154b5'
        result['am_source_sha256'] = audit_repo(am,result['am_rev'],source_roots=('am/src','am/include','libs/klib/src','libs/klib/include'))
        result['am_libraries_sha256'] = {str(p):digest(p) for p in
            (am/'am/build/am-riscv64-xs.a',am/'libs/klib/build/klib-riscv64-xs.a')}
    (evidence/'workload-provenance.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')


def verify_build(evidence, image, data, kind, mode):
    evidence = Path(evidence)
    record = json.loads((evidence/'workload-provenance.json').read_text())
    require(record['schema_version']==1 and record['kind']==kind and record['mode']==mode,'Wrong workload build type/mode')
    require(record.get('arch')=='riscv64-xs' and Path(image).suffix=='.bin','Runtime requires a riscv64-xs raw image')
    require(record['data_dir']==str(Path(data).resolve()),'Data directory differs from build')
    for group in ('source_sha256','inputs_sha256','images_sha256','am_libraries_sha256'):
        for name,expected in record.get(group,{}).items():
            require(digest(name)==expected,f'Build input/source digest mismatch: {name}')
    require(str(Path(image).resolve()) in record['images_sha256'],'Selected image is not a compiled artifact')
    if 'am_home' in record:
        actual = audit_repo(record['am_home'],record['am_rev'],source_roots=('am/src','am/include','libs/klib/src','libs/klib/include'))
        require(actual==record['am_source_sha256'],'AM source changed after build')
    return record


def check_xiangshan_reset_config(config):
    """Reject references whose trap reset policy differs from pinned XS RTL."""
    for key, expected in {
        'NMIE_INIT': 'CONFIG_NMIE_INIT=y',
        'MDT_INIT': '# CONFIG_MDT_INIT is not set',
    }.items():
        entries = [line for line in config
                   if line.startswith(f'CONFIG_{key}=') or line == f'# CONFIG_{key} is not set']
        require(entries == [expected],
                f'XiangShan reference requires exactly {expected}; rebuild against the target reset policy')


def verify_nemu(repo, binary, mode):
    repo = Path(repo).resolve()
    binary = Path(binary).resolve()
    name = 'riscv64-nemu-interpreter' if mode=='standalone' else 'riscv64-nemu-interpreter-so'
    require(binary==(repo/'build'/name).resolve(),'NEMU executable and source checkout mismatch')
    provenance = json.loads((repo/'build/vdot-provenance.json').read_text())
    manifest = json.loads((ROOT/'team/patches/nemu/manifest.json').read_text())
    require(provenance.get('schema_version')==2 and provenance['build_mode']==mode,'NEMU provenance type/version mismatch; rebuild')
    for name,value in manifest.items():
        require(provenance.get(name)==value,f'NEMU patch manifest differs: {name}')
    require(digest(binary)==provenance['binary_sha256'],'NEMU binary changed after build')
    require(digest(repo/'.config')==provenance['config_sha256'],'NEMU config changed after build')
    config=(repo/'.config').read_text().splitlines()
    require('CONFIG_RVV=y' in config and 'CONFIG_CUSTOM_VDOT=y' in config,'Candidate extension is not enabled')
    require(('CONFIG_SHARE=y' in config)==(mode=='reference'),'NEMU configuration does not match binary role')
    check_xiangshan_reset_config(config)
    require(nemu_snapshot(repo)==provenance['source_sha256'],'NEMU source/generated inputs changed after build')
    return provenance


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('repo','nemu-snapshot','nemu-runtime','capture-build','verify-build'))
    parser.add_argument('--repo',type=Path)
    parser.add_argument('--revision')
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--binary',type=Path)
    parser.add_argument('--mode',default='full')
    parser.add_argument('--kind')
    parser.add_argument('--arch')
    parser.add_argument('--am',type=Path)
    parser.add_argument('--data',type=Path)
    parser.add_argument('--evidence',type=Path)
    parser.add_argument('--image',type=Path)
    args = parser.parse_args()
    try:
        if args.action=='repo':
            m=json.loads(args.manifest.read_text()) if args.manifest else None
            result=audit_repo(args.repo,args.revision,m['patched_source_sha256'] if m else None,
                              generated=('include/config','include/generated/autoconf.h') if m else ())
        elif args.action=='nemu-snapshot': result=nemu_snapshot(args.repo)
        elif args.action=='nemu-runtime': result=verify_nemu(args.repo,args.binary,args.mode)
        elif args.action=='capture-build':
            capture_build(args.evidence,args.data,args.kind,args.arch,args.mode,args.am)
            result={'status':'BUILD_PROVENANCE_CAPTURED'}
        else: result=verify_build(args.evidence,args.image,args.data,args.kind,args.mode)
        print(json.dumps(result,sort_keys=True))
    except (ValueError,OSError,KeyError,TypeError) as error:
        raise SystemExit(f'ARTIFACT_REJECTED: {error}')
