"""Record targeted host gates after the real compiler-chain repair."""
from pathlib import Path
import hashlib, json, subprocess
root = Path('/mnt/c/Code/RVInno/riscv')
checks = [
    ('native-v2', 'team/optimizations/o1', 'test_build_recipe.py'),
    ('split-v2', 'team/optimizations/o1', 'test_split_recipe.py'),
    ('g3-v2', 'team/optimizations/o2/fullcore', 'test_*.py'),
]
rows = []
for name, directory, pattern in checks:
    command = ['python3', '-OO', '-B', '-m', 'unittest', 'discover', '-s', directory, '-p', pattern, '-v']
    path = root/'team/out'/('o5-'+name+'-final.log')
    with path.open('xb') as log:
        rc = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT).returncode
    rows.append(dict(name=name, command=command, exit_code=rc, log=str(path),
                     sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    print(name, rc, flush=True)
    if rc:break
(root/'team/out/o5-native-v2-host.json').write_text(json.dumps(rows, indent=2)+'\n')
raise SystemExit(1 if any(row['exit_code'] for row in rows) else 0)
