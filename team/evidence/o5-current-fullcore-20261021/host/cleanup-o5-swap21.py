"""Remove only the verified temporary swap after build and campaign exit."""
from pathlib import Path
import json, subprocess, time
base = Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021').resolve()
if not (base/'build-launch-06.exit').is_file() or not (base/'g3-launch.exit').is_file():
    raise ValueError('build or campaign has not exited')
target = base/'temporary-build.swap'
if target.resolve().parent != base or target.is_symlink() or not target.is_file():
    raise ValueError('unexpected temporary swap target')
before = Path('/proc/swaps').read_text()
row = dict(time=time.time(), target=str(target), before=before, removed=False)
if str(target) in before:
    result = subprocess.run(['swapoff', str(target)], capture_output=True, text=True)
    row.update(command=result.args, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
    if result.returncode:
        (base/'temporary-swap-cleanup-failed.json').write_text(json.dumps(row, indent=2)+'\n')
        raise SystemExit(result.returncode)
after = Path('/proc/swaps').read_text()
if str(target) in after:raise ValueError('temporary swap still active')
target.unlink()
row.update(after=after, removed=True, status='TEMPORARY_SWAP_REMOVED')
with (base/'temporary-swap-cleanup.json').open('x') as stream:
    json.dump(row, stream, indent=2)
print(row['status'], flush=True)
