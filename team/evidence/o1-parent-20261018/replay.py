"""Replay this fixed, reviewed Linux/Verilator artifact in a fresh directory."""
import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = 'fb309f5421c9f24b68350ecf6cfd53fc2d8368102f9a948bef2f8ca68fb084ec'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
archive_path = HERE/'validation.tar.gz'
if hashlib.sha256(archive_path.read_bytes()).hexdigest() != EXPECTED:
    raise RuntimeError('Artifact differs from the independently pinned reviewed archive')
args.output.mkdir(parents=True, exist_ok=False)
results = []
with tarfile.open(archive_path) as archive:
    def copy(name, dest, executable=False):
        member = archive.getmember(name)
        if not member.isfile():
            raise RuntimeError('Expected a regular file: '+name)
        dest.write_bytes(archive.extractfile(member).read())
        if executable:
            dest.chmod(0o755)
        return dest

    vectors = copy('attempt-07/vectors.tsv', args.output/'vectors.tsv')
    for mode in range(3):
        binary = copy(f'attempt-07/mode-{mode}/obj/VVDotExuTestTop', args.output/f'parent-{mode}', True)
        run = subprocess.run([str(binary),str(vectors),str(mode),'-','strict-idle'],
                             capture_output=True, timeout=30)
        (args.output/f'mode-{mode}.log').write_bytes(run.stdout+run.stderr)
        expected = archive.extractfile(f'attempt-07/mode-{mode}/results.log').read()
        if run.returncode or run.stderr or run.stdout != expected:
            raise RuntimeError('Parent replay differs: '+str(mode))
        results.append(dict(mode=mode, exit_code=run.returncode, identical_to_original=True))
    old = copy('harness-01/parent_test', args.output/'parent-before-fix', True)
    run = subprocess.run([str(old),str(vectors),'0','-','strict-idle'], capture_output=True, timeout=30)
    (args.output/'before-fix.log').write_bytes(run.stdout+run.stderr)
    if run.returncode != 1 or b'canceled FU clock stayed enabled during idle' not in run.stderr:
        raise RuntimeError('Old clock defect was not reproduced')
    for fault in ('identity','wen','high','cancel'):
        run = subprocess.run([str(args.output/'parent-2'),str(vectors),'2',fault],
                             capture_output=True, timeout=30)
        (args.output/f'inject-{fault}.log').write_bytes(run.stdout+run.stderr)
        if run.returncode != 1 or ('PARENT_INJECT '+fault).encode() not in run.stderr or b'VFEX4_PARENT_FAIL' not in run.stderr:
            raise RuntimeError('Fault was not detected: '+fault)
summary = dict(status='VFEX4_ARCHIVE_REPLAY_PASS', modes=results, old_clock_defect_detected=True,
               negative_controls=4, scope='Archived binaries; not independent RTL synthesis/full-core execution')
(args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
