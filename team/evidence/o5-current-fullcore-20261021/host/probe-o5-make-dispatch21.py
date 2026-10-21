from pathlib import Path
import json,os,runpy,shlex,subprocess,tempfile
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
env=json.loads((base/'native-environment.json').read_text())
os.environ.clear(); os.environ.update(env)
recipe=runpy.run_path('/mnt/c/Code/RVInno/riscv/team/optimizations/o1/build_recipe.py')
contract=json.loads((base/'native-probe-03.json').read_text())
with tempfile.TemporaryDirectory(prefix='native-dispatch-',dir=base) as tmp:
    root=Path(tmp);timing=root/'timing output.log'
    (root/'Makefile').write_text('TIMELOG := '+str(timing)+'\nemu:\n\t$(TIME_CMD) mill --version\n')
    command=shlex.split(recipe['make_command'](contract))
    result=subprocess.run(command,cwd=root,env=recipe['environment'](),text=True,capture_output=True)
    record=dict(command=command,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,
                timing=timing.read_text() if timing.exists() else None,
                scope='Actual bound GNU time/Make/POSIX fallback launches installed Mill payload; no RTL build')
    with (base/'native-dispatch-probe-03.json').open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(result.stdout,result.stderr)
    if result.returncode or 'Mill Build Tool version 0.12.3' not in result.stdout:raise SystemExit(1)
    print('ACTUAL_MAKE_TIME_MILL_DISPATCH_PASS')
