import hashlib,importlib.util,json
from pathlib import Path
repo=Path('/mnt/c/Code/RVInno/riscv');cache=Path('/home/amesotten/.cache/codex-rvinno/fullcore-20261016')
spec=importlib.util.spec_from_file_location('negative',repo/'team/scripts/check-vdot-negative.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
folder=cache/'runs/negative-vdot-retry';record=json.loads((folder/'result.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if not all(sha(Path(p))==h for p,h in record['files'].items()):raise ValueError('runtime changed')
if not all(sha(folder/n)==h for n,h in record['raw_logs_sha256'].items()):raise ValueError('logs changed')
result=m.check((folder/'run.log').read_text(),record['exit_code'])
result.update(original_result_sha256=sha(folder/'result.json'),checker_sha256=sha(repo/'team/scripts/check-vdot-negative.py'),scope='recheck same execution; original failure receipt preserved')
(folder/'recheck.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
