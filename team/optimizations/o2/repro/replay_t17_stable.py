"""Replay the published T17 archives in their fixed LF closure; never run EMU.

This deliberately keeps current hardened R4 generators separate from the
historical 34bae T17 locks. R5's optional GNU build has its own result.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

PUBLISHED = '137b44befb041439a018a1079577cc000df1ee03'
BASE = '34bae6d4acceac939f958199dae53c14bc1f6183'
REPRO = Path('team/optimizations/o2/repro')
SCRIPTS = ('clean_prepare.py', 'clean_build.py', 'clean_support.py', 'clean_profile.py',
           'clean_entry.py', 'clean_fullcore.py', 'clean_evidence.py', 'clean_fullcore_evidence.py',
           'test_clean_evidence.py', 'clean_portable_evidence.py')


def replay(repo, bundle, output, tool_bin, stable_build=False):
    if sys.platform != 'linux':
        raise ValueError('use native Linux Git and LF sources')
    if not output.is_absolute() or output.exists() or output.is_symlink():
        raise ValueError('output must be absolute and new')
    repo, bundle, output, tool_bin = [p.resolve() for p in (repo, bundle, output, tool_bin)]
    if any(output.is_relative_to(p) or p.is_relative_to(output) for p in (repo, bundle, tool_bin)):
        raise ValueError('output overlaps input')
    output.mkdir(parents=True)
    env = dict(PATH=str(tool_bin)+':/usr/bin:/bin', LANG='C.UTF-8', LC_ALL='C.UTF-8', TZ='UTC')
    state = dict(status='RUNNING', published=PUBLISHED, base=BASE, new_emu_runs=0,
                 performance_measured=False, current_hardware_qualified=False, steps=[], environment=env)

    def save():
        (output/'state.json').write_text(json.dumps(state, indent=2)+'\n')

    def command(name, argv, cwd=None, required=True):
        row = dict(name=name, command=list(map(str,argv)), cwd=str(cwd) if cwd else None,
                   started=datetime.now(timezone.utc).isoformat())
        state['steps'].append(row); save()
        with (output/(name+'.log')).open('xb') as stream:
            rc = subprocess.run(row['command'], cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT).returncode
        row.update(exit_code=rc, finished=datetime.now(timezone.utc).isoformat(),
                   log_sha256=hashlib.sha256((output/(name+'.log')).read_bytes()).hexdigest())
        save()
        if rc and required:
            raise ValueError('failed '+name+'; original log retained')
        return rc

    def clone(name, source, revision):
        target=output/name
        command(name+'-clone', ['git','clone','--shared','--no-checkout','-c','core.autocrlf=false',source,target])
        if name == 'published':
            command('fetch-bundle',['git','-C',target,'fetch',bundle,'refs/remotes/origin/zufan:refs/remotes/import/zufan'])
        command(name+'-sparse',['git','-C',target,'sparse-checkout','set','--no-cone',
                '/team/','!/team/evidence/','!/team/**/evidence/'])
        command(name+'-checkout',['git','-C',target,'checkout','--detach',revision])
        return target

    try:
        published=clone('published',repo,PUBLISHED)
        paths=[REPRO/'evidence/clean-reproduction-v1', Path('team/optimizations/o2/r2-select/evidence/stable-v1')]
        command('restore-evidence',['git','-C',published,'restore','--worktree','--ignore-skip-worktree-bits','--',*paths])
        source=clone('source',published,BASE)
        command('restore-frozen-inputs',['git','-C',source,'restore','--worktree','--ignore-skip-worktree-bits','--',
                'team/evidence/t10-t11-fullcore-20261013/matrix/negative-fixture.c',
                'team/evidence/t13-performance-20261015/images-v3/performance-d0-s06',
                'team/evidence/t14-optimization-20261016/control-sweep/build/build.json',
                'team/evidence/t10-t11-fullcore-20261013/parent/cases.jsonl',
                'team/evidence/t10-t11-fullcore-20261013/parent/exceptions.json'])
        snapshots={}
        for name in SCRIPTS:
            body=(published/REPRO/name).read_bytes()
            with (source/REPRO/name).open('xb') as stream:
                stream.write(body)
            snapshots[name]=hashlib.sha256(body).hexdigest()
        state['copied_new_tools']=snapshots; save()
        evidence=published/REPRO/'evidence/clean-reproduction-v1'
        identity=evidence/'reports/identity-02.json'
        guard=evidence/'analysis/detached-audit.py'
        deny=Path('/home/lizufan/riscv-lab/t17-clean-20261024-0854')
        for name, script, args in (
            ('fullcore','clean_fullcore_evidence.py',['--action','audit','--archive',evidence/'fullcore-archive']),
            ('matrix','clean_portable_evidence.py',['--action','audit-matrix','--identity',identity,'--archive',evidence/'matrix-archive']),
            ('c','clean_portable_evidence.py',['--action','audit-c','--identity',identity,'--archive',evidence/'c-archive',
                                            '--matrix',evidence/'matrix-archive'])):
            command(name,['python3','-B',guard,'--checkout',source,'--script',source/REPRO/script,
                    '--report',output/(name+'-guard.json'),'--deny-root',deny,'--','--repo',source,
                    *args,'--output',output/(name+'.json')],source)
        state['status']='T17_PUBLISHED_ARCHIVES_REPLAY_PASS'
        if stable_build:
            rc=command('stable-build',['python3','-B',published/'team/optimizations/o2/r2-select/verify_stable.py',
                       '--repo',published,'--output',output/'stable-build'],published,required=False)
            state['stable_build_pass']=rc==0
        state['scope']='Published T17 evidence replay only; R5 GNU build separate; no local hardware/performance/default adoption.'
    except BaseException as exc:
        state.update(status='FAILED', error=repr(exc))
        raise
    finally:
        state['finished']=datetime.now(timezone.utc).isoformat(); save()
    return state


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','bundle','output','tool-bin'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--stable-build', action='store_true')
    args=parser.parse_args()
    print(json.dumps(replay(args.repo,args.bundle,args.output,args.tool_bin,args.stable_build)))
