from pathlib import Path
from datetime import datetime, timezone
import json, os, signal
base = Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
pid = 3748
cmd = Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0', b' ').decode()
if not cmd.startswith('/usr/bin/verilator_bin ') or str(base/'repo/build') not in cmd:
    raise ValueError('target no longer belongs to this build')
receipt = base/'build-05/operator-stop.json'
with receipt.open('x') as stream:
    json.dump(dict(status='STOP_REQUESTED_TOOL_CONTRACT_GAP', utc=datetime.now(timezone.utc).isoformat(),
        pid=pid, command=cmd, signal='SIGTERM', reason='Verilator make independently selects LINK=g++ and AR=ar; split-clang-v1 binds only CXX/CC. Preserve this attempt; fresh explicit v2 required.'), stream, indent=2)
os.kill(pid, signal.SIGTERM)
print('SIGTERM sent to verified build05 Verilator process')
