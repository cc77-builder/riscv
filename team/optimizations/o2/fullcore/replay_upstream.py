"""Replay the six imported deliveries in their fixed LF source closure, no EMU.

The integration checkout retains newer generators and checks. Never rewrite
historical pins to make them accept current sources. This entry checks only
the MERGE raw evidence, qualified selection export, and R4 C/matrix closure.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REVISION = 'c9132b8d7f284ad7e76550315214b5b2ca431f79'
O2 = Path('team/optimizations/o2')


def run(repo, output, tool_bin):
    repo, output, tool_bin = map(lambda p: Path(p).resolve(), (repo, output, tool_bin))
    if sys.platform != 'linux':
        raise ValueError('use Linux/WSL with native Git and LF sources')
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (repo, tool_bin)):
        raise ValueError('output must be fresh and outside all inputs')
    if subprocess.check_output(['git','-C',str(repo),'rev-parse',REVISION+'^{commit}'],text=True).strip()!=REVISION:
        raise ValueError('fixed revision unavailable')
    env = dict(PATH=str(tool_bin)+':/usr/bin:/bin', LANG='C.UTF-8', LC_ALL='C.UTF-8', TZ='UTC')
    output.mkdir(parents=True)
    state = dict(status='RUNNING', revision=REVISION, environment=env, steps=[],
                 new_emu_runs=0, current_hardware_qualified=False,
                 historical_environment_fully_bound=False)
    def save():
        (output/'state.json').write_text(json.dumps(state,indent=2)+'\n')
    def command(name, argv, cwd=None):
        row = dict(name=name, command=list(map(str,argv)), cwd=str(cwd) if cwd else None,
                   started=datetime.now(timezone.utc).isoformat())
        state['steps'].append(row); save()
        with (output/(name+'.log')).open('xb') as stream:
            rc=subprocess.run(row['command'],cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT).returncode
        row.update(exit_code=rc, finished=datetime.now(timezone.utc).isoformat(),
                   log_sha256=hashlib.sha256((output/(name+'.log')).read_bytes()).hexdigest())
        save()
        if rc: raise ValueError('failed: '+name+'; original log preserved')
    context=output/'source'
    try:
        command('clone',['git','clone','--shared','--no-checkout','-c','core.autocrlf=false',repo,context])
        command('sparse',['git','-C',context,'sparse-checkout','set','--no-cone',
                         '/team/','!/team/evidence/','!/team/**/evidence/'])
        command('checkout',['git','-C',context,'checkout','--detach',REVISION])
        paths=[O2/p/'evidence' for p in ('fullcore','r2-select','r2-vector-accum')]
        paths += [Path('team/evidence/t10-t11-fullcore-20261013/matrix/negative-fixture.c')]
        command('evidence',['git','-C',context,'restore','--worktree','--ignore-skip-worktree-bits','--',*paths])
        full=context/O2/'fullcore'; select=context/O2/'r2-select'
        command('merge-audit',[sys.executable,'-B',full/'merged_regression_evidence.py','audit',
                '--archive',full/'evidence/merged-regression-v1/archive','--output',output/'merge-audit.json'],context)
        command('selection-export',[sys.executable,'-B',select/'selection.py','--repo',context,'--action','export',
                '--bundle',output/'selected-images','--report',output/'selection-export.json'],context)
        command('c-and-matrix-audit',[sys.executable,'-B',select/'entry_c_evidence.py','--repo',context,'--action','audit',
                '--archive',select/'evidence/c-api-v1','--matrix',select/'evidence/entry-v1',
                '--output',output/'c-and-matrix-audit.json'],context)
        state['status']='UPSTREAM_SIX_COMPATIBILITY_REPLAY_PASS'
    except BaseException as exc:
        state.update(status='FAILED',error=repr(exc)); raise
    finally:
        state['finished']=datetime.now(timezone.utc).isoformat(); save()
    return state


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--tool-bin',type=Path,default=Path('/usr/bin'))
    a=p.parse_args()
    print(json.dumps(run(a.repo,a.output,a.tool_bin)))
