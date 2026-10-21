from pathlib import Path
import json, subprocess, time
base = Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021').resolve()
target = base/'temporary-build.swap'
if target.resolve().parent != base or not target.is_file() or target.stat().st_size != 8*1024**3:
    raise ValueError('unexpected temporary swap file')
before = Path('/proc/swaps').read_text()
if str(target) in before:raise ValueError('temporary swap is already active')
command = ['swapon', str(target)]
result = subprocess.run(command, capture_output=True, text=True)
with (base/'temporary-swap-reactivate.json').open('x') as stream:
    json.dump(dict(time=time.time(), command=command, exit_code=result.returncode,
        before=before, after=Path('/proc/swaps').read_text(), stdout=result.stdout, stderr=result.stderr,
        reason='WSL idle shutdown removed runtime swap activation; reuse the exact task-local file for fresh build06'), stream, indent=2)
raise SystemExit(result.returncode)
