"""Controlled untracked-source injection; restores only files created by this check."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

def require(condition,message):
    if not condition: raise RuntimeError(message)


def check(cache, base, evidence):
    root = Path(__file__).resolve().parents[2]
    evidence.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root/'team/patches/nemu/manifest.json').read_text())
    target = cache/'standalone'
    before = {p:hashlib.sha256((target/p).read_bytes()).hexdigest() for p in manifest['patched_source_sha256']}
    results = []
    for kind, path in (
        ('nemu', target/'src/utils'/f'team-guard-{uuid.uuid4().hex}.c'),
        ('nemu-optimized', target/'src/utils'/f'team-guard-{uuid.uuid4().hex}.c'),
        ('nemu-ignored', target/'src/utils/build'/f'team-guard-{uuid.uuid4().hex}.c'),
        ('nemu-ignored-header', target/'src/utils/.idea'/f'team-guard-{uuid.uuid4().hex}.h'),
        ('dependency', base/'resource/LibCheckpoint/src'/f'team-guard-{uuid.uuid4().hex}.c'),
        ('dependency-ignored', base/'resource/LibCheckpoint/src/build'/f'team-guard-{uuid.uuid4().hex}.c')):
        env = dict(os.environ, TEAM_NEMU_VDOT_ROOT=str(cache), TEAM_NEMU_BASE_ROOT=str(base),
                   TEAM_EVIDENCE_DIR=str(evidence/kind))
        if kind == 'nemu-optimized':
            env['PYTHONOPTIMIZE']='1'
        created=not path.parent.exists()
        path.parent.mkdir(exist_ok=True)
        with path.open('x') as out:
            out.write('/* Controlled test: must never be compiled. */\n')
        try:
            result = subprocess.run(['bash',str(root/'team/scripts/prepare-nemu-vdot.sh'),'standalone'],
                                    env=env, capture_output=True, text=True, timeout=60)
            (evidence/f'{kind}.log').write_text(result.stdout+result.stderr)
            require(result.returncode != 0,f'{kind}: unknown source was accepted')
            if kind.startswith('nemu'):
                require('Unknown compiler input' in result.stderr and path.name in result.stderr,result.stderr)
            else:
                dependency_log = (evidence/kind/'dependencies.txt').read_text()
                require('Dependency has tracked or untracked edits' in dependency_log or
                        ('Unknown compiler input' in dependency_log and path.name in dependency_log),dependency_log)
            results.append(dict(kind=kind,rejected=True,exit_code=result.returncode))
        finally:
            path.unlink()
            if created: path.parent.rmdir()
    after = {p:hashlib.sha256((target/p).read_bytes()).hexdigest() for p in manifest['patched_source_sha256']}
    require(before == after == manifest['patched_source_sha256'],'Patched source changed during test')
    output = dict(tests=results, patched_sources_unchanged=True, injected_files_removed=True)
    (evidence/'summary.json').write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
    print(json.dumps(output,sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args = parser.parse_args()
    check(args.cache,args.base,args.evidence)
