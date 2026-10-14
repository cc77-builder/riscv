"""Freeze the current workspace into a native Linux build copy, without commits."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def git(repo, *args, input=None):
    return subprocess.check_output(['git', '-C', str(repo), *args], input=input)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def names(repo, *options):
    return [x.decode('utf-8') for x in git(repo, 'ls-files', '-z', *options).split(b'\0') if x]


def is_input(name):
    return (name.startswith(('src/', 'macros/', 'scripts/', 'team/workloads/hello-vadd/')) or
            name in ('build.sc', 'Makefile', '.mill-version', '.gitmodules', '.gitattributes',
                     'team/scripts/prepare-core-baseline.py', 'team/scripts/core-baseline.sh'))


def root_inputs(repo):
    selected = sorted({name for name in names(repo, '--cached', '--others', '--exclude-standard')
                       if is_input(name) and (repo/name).is_file()})
    # Git's clean filter gives the canonical bytes for Windows CRLF checkouts.
    paths = ''.join(json.dumps(name, ensure_ascii=False)+'\n' for name in selected).encode('utf-8')
    hashes = git(repo, '-c', 'core.autocrlf=true', 'hash-object', '--stdin-paths', input=paths).decode().splitlines()
    require(len(hashes) == len(selected), 'Incomplete canonical source inventory')
    for folder in ('src/main/scala', 'src/test/scala', 'macros/src'):
        for path in (repo/folder).rglob('*.scala'):
            require(path.relative_to(repo).as_posix() in selected, 'Ignored compiler input: '+str(path))
    return dict(zip(selected, hashes))


def modules(repo):
    result = {}
    for line in git(repo, 'submodule', 'status', '--recursive').decode('utf-8').splitlines():
        require(line.startswith(' '), 'Uninitialized or different submodule: '+line)
        revision, name = line[1:].split()[:2]
        result[name] = revision
    return result


def pack(repo, output):
    require(not output.exists(), 'Use a fresh source pack directory: '+str(output))
    output.mkdir(parents=True)
    revision = git(repo, 'rev-parse', 'HEAD').decode().strip()
    patch = git(repo, 'diff', '--binary', '--ignore-submodules=dirty', 'HEAD')
    (output/'changes.patch').write_bytes(patch)
    untracked = {}
    for name in names(repo, '--others', '--exclude-standard'):
        source = repo/name
        require(source.is_file() and not source.is_symlink(), 'Unsupported untracked path: '+name)
        target = output/'untracked'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        untracked[name] = digest(target)
    dependencies = modules(repo)
    # Snapshot clones use the pinned dependency trees, so reject local changes.
    for name in dependencies:
        child = repo/name
        subprocess.run(['git','-C',str(child),'diff','--exit-code','--quiet',
                        '--ignore-submodules=all','HEAD'], check=True)
        unknown = names(child, '--others', '--exclude-standard')
        require(not unknown, 'Untracked dependency inputs: '+name+' '+str(unknown[:3]))
    record = dict(schema=1, revision=revision, canonical_root_inputs=root_inputs(repo),
                  modules=dependencies, patch_sha256=digest(output/'changes.patch'), untracked_sha256=untracked)
    encoded = (json.dumps(record, sort_keys=True, indent=2)+'\n').encode('utf-8')
    (output/'source-pack.json').write_bytes(encoded)
    print(json.dumps(dict(status='CORE_SOURCE_PACK_READY', source_pack_sha256=hashlib.sha256(encoded).hexdigest(),
                          root_inputs=len(record['canonical_root_inputs']), modules=len(dependencies)), sort_keys=True))


def materialize(source, packed, cache):
    record = json.loads((packed/'source-pack.json').read_bytes())
    require(digest(packed/'changes.patch') == record['patch_sha256'], 'Changed source patch')
    identity = digest(packed/'source-pack.json')
    target = cache/('source-'+identity[:16])
    require(not target.exists(), 'Build copy already exists; verify it before reuse: '+str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git','clone','--shared','--no-checkout',str(source),str(target)], check=True)
    subprocess.run(['git','-C',str(target),'checkout','--detach',record['revision']], check=True)
    # Native Git checkouts restore LF scripts and executable modes. Only shared
    # object storage references Windows; all compiler inputs/build outputs are Linux.
    for name, revision in sorted(record['modules'].items(), key=lambda item:(item[0].count('/'),item[0])):
        child = target/name
        if child.is_dir():
            require(not any(child.iterdir()), 'Unexpected populated module: '+str(child))
        child.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git','clone','--shared','--no-checkout',str(source/name),str(child)], check=True)
        subprocess.run(['git','-C',str(child),'checkout','--detach',revision], check=True)
    for repo in (target, *(target/name for name in record['modules'])):
        if (repo/'.gitmodules').exists():
            subprocess.run(['git','-C',str(repo),'submodule','init'],check=True,stdout=subprocess.DEVNULL)
    if (packed/'changes.patch').stat().st_size:
        subprocess.run(['git','-C',str(target),'apply',str(packed/'changes.patch')], check=True)
    for name, expected in record['untracked_sha256'].items():
        origin = packed/'untracked'/name
        require(digest(origin) == expected, 'Changed new source: '+name)
        destination = target/name
        require(not destination.exists(), 'New source would overwrite a tracked path: '+name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, destination)
    require(root_inputs(target) == record['canonical_root_inputs'], 'Build copy source differs from current workspace')
    # Record physical Linux compiler inputs after canonical workspace comparison.
    physical = {name:digest(target/name) for name in record['canonical_root_inputs']}
    binding = dict(source_pack_sha256=identity, revision=record['revision'],
                   source=str(source), build_copy=str(target), modules=record['modules'], physical_root_sha256=physical)
    (target/'build').mkdir()
    (target/'build/source-binding.json').write_bytes((json.dumps(binding,sort_keys=True,indent=2)+'\n').encode())
    (packed/'build-copy.txt').write_bytes((str(target)+'\n').encode())
    print(json.dumps(dict(status='CORE_BUILD_COPY_READY',build_copy=str(target),root_inputs=len(physical)),sort_keys=True))


def verify(source, packed, target):
    record = json.loads((packed/'source-pack.json').read_bytes())
    binding = json.loads((target/'build/source-binding.json').read_bytes())
    require(digest(packed/'source-pack.json') == binding['source_pack_sha256'], 'Changed source pack')
    require(git(source,'rev-parse','HEAD').decode().strip() == record['revision'], 'Workspace revision changed')
    require(root_inputs(source) == record['canonical_root_inputs'], 'Workspace compiler inputs changed')
    require(root_inputs(target) == record['canonical_root_inputs'], 'Build copy compiler inputs changed')
    for name, expected in binding['physical_root_sha256'].items():
        require(digest(target/name) == expected, 'Build copy bytes changed: '+name)
    for name, expected in record['modules'].items():
        require(git(target/name,'rev-parse','HEAD').decode().strip() == expected, 'Build dependency changed: '+name)
        subprocess.run(['git','-C',str(target/name),'diff','--exit-code','--quiet','--ignore-submodules=all','HEAD'],check=True)
    print(json.dumps(dict(status='CORE_SOURCE_BINDING_PASS',root_inputs=len(binding['physical_root_sha256']),
                          modules=len(record['modules']),source_pack_sha256=binding['source_pack_sha256']),sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('pack','materialize','verify'))
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--pack',type=Path,required=True)
    parser.add_argument('--cache',type=Path)
    parser.add_argument('--target',type=Path)
    args=parser.parse_args()
    if args.action == 'pack': pack(args.source.resolve(), args.pack.resolve())
    elif args.action == 'materialize':
        require(args.cache is not None, 'Set --cache')
        materialize(args.source.resolve(),args.pack.resolve(),args.cache.resolve())
    else:
        require(args.target is not None, 'Set --target')
        verify(args.source.resolve(),args.pack.resolve(),args.target.resolve())
