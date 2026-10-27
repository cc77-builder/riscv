"""Preserve this round's failed v1 without editing any original input/output."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(root, out):
    assert not out.exists()
    assert not any(out.is_relative_to(root / name) for name in
                   ('build-01', 'build-02', 'build-03', 'run-01', 'source', 'source-v2'))
    run = root / 'run-01'
    state = json.loads((run / 'state.json').read_text())
    recovery = json.loads((run / 'runs/recovery/result.json').read_text())
    negative = json.loads((run / 'runs/negative/result.json').read_text())
    stdout = (run / 'runs/recovery/stdout.log').read_text()
    stderr = (run / 'runs/recovery/stderr.log').read_text()
    assert state['status'] == recovery['status'] == 'FAILED'
    assert state['new_emu_runs'] == 2 and state['active_pid'] is None and state['finished']
    assert recovery['exit_code'] == 0 and recovery['finished']
    assert negative['status'] == 'EXPECTED_VDOT_HIGHBIT_REJECTION'
    assert 'EXCEEDING CYCLE/INSTR LIMIT' in stdout and 'cycleCnt = 3000000' in stdout
    assert 'SPLIT_FUNCTIONAL calls=84 controls=6' in stdout
    assert 'HIT GOOD TRAP' not in stdout and not (run / 'runs/replay').exists()
    stops = re.findall(r'(?m)^T13_RETIRE cycle=\s*(\d+)[^\n]*word=0x51400013', stderr)
    assert 0 < len(stops) < 252
    builds = {name: json.loads((root / name / 'build.json').read_text())
              for name in ('build-01', 'build-02', 'build-03')}
    assert builds['build-01']['exit_code'] != 0
    assert builds['build-02']['exit_code'] == builds['build-03']['exit_code'] == 0
    selected = []
    for name in ('build-01', 'build-02', 'build-03', 'run-01'):
        for path in sorted((root / name).rglob('*')):
            assert not path.is_symlink(), path
            if path.is_dir():
                continue
            assert stat.S_ISREG(path.stat().st_mode) and path.resolve().is_relative_to(root)
            selected.append((path, path.relative_to(root).as_posix()))
    module = root / 'source/team/optimizations/o2/r2-config-reuse/caller/split'
    for path in sorted(module.iterdir()):
        assert path.is_file() and not path.is_symlink(), path
        selected.append((path, 'source-v1-module/' + path.name))
    for name in ('setup.json', 'dependency-closure.json'):
        if (root / name).is_file():
            selected.append((root / name, 'preparation/' + name))
    selected.append((Path(__file__).resolve(), 'preserve_failed_v1.py'))
    assert len({name for _, name in selected}) == len(selected)
    out.mkdir(parents=True)
    rows = []
    with zipfile.ZipFile(out / 'payload.zip', 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path, name in selected:
            data = path.read_bytes()
            row = {'path': name, 'raw_bytes': len(data), 'sha256': sha(data)}
            rows.append(row)
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(out / 'payload.zip') as z:
        assert z.namelist() == [row['path'] for row in rows]
        for (path, name), row in zip(selected, rows):
            data = z.read(name)
            assert len(data) == row['raw_bytes'] and sha(data) == row['sha256']
            assert data == path.read_bytes(), 'source changed while archiving: ' + name
    result = {
        'status': 'FAILED_V1_BYTES_PRESERVED',
        'scope': 'failed diagnostics; no campaign or performance qualification',
        'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_root': str(root), 'source_base': '71b24fc43a7111abae1012d0c4bcaf89f249300f',
        'v1_contract': state['contract'], 'state': state,
        'v1_failure': '3,000,000-cycle budget exhausted; runtime gate rejected; no replay',
        'functional_uart': {'calls': 84, 'controls': 6},
        'negative_status': negative['status'],
        'completed_measurement_windows': len(stops), 'planned_windows': 252,
        'last_completed_window_cycle': int(stops[-1]),
        'build_01_failure': 'split.c and split.S generated the same split.o target; undefined split leaves',
        'builds': {n: {'exit_code': b['exit_code'], 'artifacts': b.get('artifacts', {})}
                   for n, b in builds.items()},
        'originals_removed': 0, 'new_emu_runs': 0,
        'files': rows, 'raw_bytes': sum(row['raw_bytes'] for row in rows),
        'payload_bytes': (out / 'payload.zip').stat().st_size,
        'payload_sha256': sha((out / 'payload.zip').read_bytes()),
    }
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('files', 'state', 'builds')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.root.resolve(), args.output.resolve())
