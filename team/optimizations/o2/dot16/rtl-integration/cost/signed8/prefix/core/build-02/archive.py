#!/usr/bin/env python3
"""One bounded, read-only-source archive; no restore, build, EDA, or guest run.

Keep the actual core02 EMU, final RTL except SimTop.fir, small generated
support, all top-level controller records, source-snapshot, and all core01
failure files. Omitted generated files retain individual original manifest
identities. This is a selected artifact archive, not a standalone rebuild.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib
import json
import os
import signal
import stat
import sys
import time
import zipfile
import zlib

BASE = Path('/home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-20261107-main')
WIN = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/runs/dot16-prefix-20261107-main')
CORE = BASE / 'core-build-02'
FAILED = BASE / 'core-build-01'
REVIEW = WIN / 'core-build-02-review'
OUT = WIN / 'core-build-02-archive-01'
MANIFEST_SHA = '2bf579a661d390d7c8d734580487c0ccb352e63b684471aa622498bddb102bc3'
REVIEW_NAMES = ('audit.json', 'host-receipts.json', 'review.ps1', 'review.py')
REVIEW_PINS = {
    'audit.json': '8b7b960ab269cd72c9e14bd47515be36f3a13961809d34a0c5ffcba4c54eb792',
    'host-receipts.json': '2cd9f885a075a04c766dd4ab54bc1164d133dc07bc36df0d17f7f8ae551907fa',
    'review.ps1': '5e3312d809139b106c250db2120deefad7c948176c4f4e03a8b0841c79b3340d',
    'review.py': '8a331871131ad4559e7f438cd76727617707f63ac51006f7eeef89aed909158e',
}
CORE_PINS = {
    'result.json': '06b38d232feda7ea93e3b34d806888163a5abf89de916e63af185d383773a5e2',
    'plan.json': '488be2506d8027b93aaa7d3954347b754207170eced5353c8ba1fa050587ff37',
    'input-lock.json': '01ebfe385c649d14e02f0f1a880dd60f5971cbb92c8219bc4a3a211b198d8ce4',
    'generated-files.json': MANIFEST_SHA,
    'source-snapshot/prefix_core_build.py': '77f0d609f732a54c6376759ea2db1ed4b988945c93d8255bf1221774b8c81081',
    'source-snapshot/CORE_BUILD_CONTRACT.md': 'e7e86da82eead7092fe5a9d5da6939fc88372821b38c195a5e18b00828d2bec3',
    'generate-core.log': '0381b86077928c33eddda3542b21c49c926dc372601f736aba9c5a3e06a325d9',
    'build-native.log': '2ff63d69cbb4e6145754d8009f4b3b315db007c8628874436b6b52c72948bc9c',
    'check-inputs-before.log': '854634defc0078ab033ae23905240d3a030bd7f1a770a3aa691e3707e1830157',
    'check-inputs-after.log': '854634defc0078ab033ae23905240d3a030bd7f1a770a3aa691e3707e1830157',
}
FAILED_PINS = {
    'result.json': '7b3bad1abc032a3d6a02c4013e0ac64fbc0e5e45346f3c61b765c49d9c48ca7c',
    'plan.json': 'e8325ed20f9a8a86158f58b8f7a9feb8d09cdf670728e3158db00cd590fa72fd',
    'input-lock.json': '78d09a66fa1b7d16dce3f45e0670d8a5c160305ef3f4385d91011820b01e399a',
    'source-snapshot/prefix_core_build.py': 'ac6a2ffcf527d7a2eb61452597d63e8e147d7563f6ecaf79450f838460f1a3ae',
    'source-snapshot/CORE_BUILD_CONTRACT.md': '7cf9509780519917638aaa8fd444a43fd25885fc16562287b6feb6a3c8515025',
    'generate-core.log': '0260943c4026ada6549a2725a2e2fe0f543987ab78b43f3a6b0f85811aaea22c',
    'check-inputs-before.log': '854634defc0078ab033ae23905240d3a030bd7f1a770a3aa691e3707e1830157',
}
START = time.monotonic()
DEADLINE = START + 210


def now():
    return datetime.now(timezone.utc).isoformat()


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def check():
    need(time.monotonic() < DEADLINE, 'archive internal 210-second budget exhausted')


def interrupted(sig, frame):
    raise TimeoutError('archive interrupted by signal ' + str(sig))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def file_stat(path):
    s = path.lstat()
    need(stat.S_ISREG(s.st_mode), 'non-regular input: ' + str(path))
    return dict(bytes=s.st_size, mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns,
                mode=s.st_mode, inode=s.st_ino, device=s.st_dev, links=s.st_nlink)


def inventory(root):
    check()
    need(root.is_dir() and not root.is_symlink() and root.resolve() == root,
         'root missing or symbolic path: ' + str(root))
    files = {}
    for directory, dirs, names in os.walk(root, followlinks=False):
        check()
        dirs.sort()
        for name in dirs:
            need(not (Path(directory) / name).is_symlink(), 'directory symlink is not allowed')
        for name in sorted(names):
            path = Path(directory) / name
            files[path.relative_to(root).as_posix()] = file_stat(path)
    return files


def read_hash(path, sink=None):
    check()
    h = hashlib.sha256()
    crc = 0
    count = 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'not a regular opened file')
        while True:
            check()
            data = stream.read(1 << 20)
            if not data:
                break
            h.update(data)
            crc = zlib.crc32(data, crc)
            count += len(data)
            if sink is not None:
                sink.write(data)
    return dict(bytes=count, sha256=h.hexdigest(), crc32=crc & 0xffffffff)


def fresh_write(name, data):
    check()
    with (OUT / name).open('xb') as stream:
        stream.write(data)
    return dict(path=str(OUT / name), bytes=len(data), sha256=sha_bytes(data))


def cpu_list(value):
    answer = set()
    for part in value.split(','):
        ends = part.split('-')
        answer.update(range(int(ends[0]), int(ends[-1]) + 1))
    return answer


def runtime_snapshot():
    watched = {'emu', 'java', 'firtool', 'verilator_bin', 'verilator', 'clang',
               'clang++', 'clang++-19', 'clang-19', 'cc1plus', 'g++', 'yosys',
               'berkeley-abc', 'yosys-abc', 'sta', 'make', 'ninja', 'iverilog', 'vvp'}
    processes = []
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit() or int(directory.name) == os.getpid():
            continue
        try:
            rows = {line.split(':', 1)[0]: line.split(':', 1)[1].strip()
                    for line in (directory / 'status').read_text().splitlines() if ':' in line}
            if rows['Name'] in watched and not rows['State'].startswith('Z'):
                processes.append(dict(pid=int(directory.name), name=rows['Name'],
                                      affinity=sorted(cpu_list(rows['Cpus_allowed_list'])),
                                      rss=rows.get('VmRSS'), state=rows['State']))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    need(all(3 not in p['affinity'] for p in processes), 'CPU3 already has a heavy process')
    need(all(set(p['affinity']) <= {0, 1, 2, 3} for p in processes), 'observed task exceeds four-core domain')
    return dict(at=now(), pid=os.getpid(), pgid=os.getpgid(0),
                cpu_affinity=sorted(os.sched_getaffinity(0)), nice=os.getpriority(os.PRIO_PROCESS, 0),
                observed_heavy=processes, observation_scope='WSL process metadata; no command lines')


def main():
    need(len(sys.argv) == 2 and len(sys.argv[1]) == 64, 'explicit archive source SHA required')
    need(Path(__file__).resolve() == OUT / 'archive.py', 'archive script must be in the one authorized output')
    need(read_hash(Path(__file__))['sha256'] == sys.argv[1], 'archive source changed')
    need({p.name for p in OUT.iterdir()} == {'archive.py', 'PREPARATION.json'}, 'output is not preparation-only')
    os.sched_setaffinity(0, {3})
    os.setpriority(os.PRIO_PROCESS, 0, 5)
    launch = runtime_snapshot()
    print(json.dumps(dict(event='PREFIX_CORE02_ARCHIVE_LAUNCH', **launch)), flush=True)
    signal.signal(signal.SIGALRM, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    signal.alarm(215)
    report = dict(status='RUNNING', started=now(), source_sha256=sys.argv[1], launch=launch,
                  internal_budget_seconds=210, external_budget_seconds=240,
                  independent_rebuild_verified=False, original_sources_deleted=False,
                  omitted_file_contents_rehashed=False, new_eda_runs=0, new_guest_runs=0)
    try:
        before = {'core-build-02': inventory(CORE), 'core-build-01': inventory(FAILED),
                  'core-build-02-review': inventory(REVIEW)}
        manifest_raw = (CORE / 'generated-files.json').read_bytes()
        need(sha_bytes(manifest_raw) == MANIFEST_SHA, 'frozen generated manifest changed')
        generated = json.loads(manifest_raw)
        need(len(generated) == 2722 and sum(r['bytes'] for r in generated) == 2622947810,
             'original generated manifest count/size changed')
        names = [r['path'] for r in generated]
        need(len(set(names)) == len(names), 'duplicate generated entry')
        for row in generated:
            p = PurePosixPath(row['path'])
            need(not p.is_absolute() and '..' not in p.parts and str(p) == row['path'] and
                 row['path'].startswith('cwd/build/'), 'invalid manifest path')
            need(row['path'] in before['core-build-02'] and
                 before['core-build-02'][row['path']]['bytes'] == row['bytes'], 'manifest inventory mismatch')
        selected, omitted = [], []
        for row in generated:
            if row['path'].startswith('cwd/build/emu-compile/'):
                omitted.append(dict(**row, reason='Verilator/native intermediate; source retained in place'))
            elif row['path'] == 'cwd/build/rtl/SimTop.fir':
                omitted.append(dict(**row, reason='FIR intermediate; source retained in place'))
            else:
                selected.append(row)
        need(len(selected) == 1687 and sum(r['bytes'] for r in selected) == 207136616,
             'authorized selected count/size mismatch')
        need(len(omitted) == 1035 and sum(r['bytes'] for r in omitted) == 2415811194,
             'omitted count/size mismatch')
        expected = {r['path']: r['sha256'] for r in selected}
        expected.update(CORE_PINS)
        controls = [p for p in before['core-build-02'] if '/' not in p or p.startswith('source-snapshot/')]
        need(set(CORE_PINS) <= set(controls), 'required control evidence missing')
        generated_set = set(names)
        other_unselected = [dict(path=p, metadata=v, reason='outside selected generated/control scope; not read')
                            for p, v in before['core-build-02'].items() if p not in generated_set and p not in controls]
        need(set(FAILED_PINS) <= set(before['core-build-01']), 'original failed evidence missing')
        need(sum(r['bytes'] for r in before['core-build-01'].values()) <= 16 * 1024 * 1024,
             'unexpected failure evidence size; stop before broadening archive')
        need(set(REVIEW_NAMES) <= set(before['core-build-02-review']), 'review evidence missing')
        jobs = [(CORE, 'core-build-02', r['path'], expected.get(r['path'])) for r in selected]
        jobs += [(CORE, 'core-build-02', p, expected.get(p)) for p in controls]
        jobs += [(FAILED, 'core-build-01', p, FAILED_PINS.get(p)) for p in before['core-build-01']]
        jobs += [(REVIEW, 'core-build-02-review', p, REVIEW_PINS[p]) for p in REVIEW_NAMES]
        jobs.sort(key=lambda r: (r[1], r[2]))
        archive_names = [label + '/' + rel for _, label, rel, _ in jobs]
        need(len(archive_names) == len(set(archive_names)), 'duplicate archive source name')
        selection = dict(status='SELECTED_ARTIFACTS_ONLY', original_manifest_sha256=MANIFEST_SHA,
                         selected_generated=selected, omitted_generated=omitted,
                         other_unselected=other_unselected,
                         scope='Not all rows of the original generated-files.json are included. No original removed.',
                         standalone_rebuild=False, dependency_policy='External frozen dependencies remain original path/SHA references')
        selection_data = encoded(selection)
        selection_record = fresh_write('archive-selection.json', selection_data)
        inventory_data = encoded(before)
        inventory_record = fresh_write('source-inventory-before.json', inventory_data)
        source_members = []
        zip_path = OUT / 'raw.zip'
        with zipfile.ZipFile(zip_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            for root, label, rel, pinned in jobs:
                check()
                path = root / rel
                need(file_stat(path) == before[label][rel], 'input changed before copy: ' + str(path))
                zi = zipfile.ZipInfo(label + '/' + rel,
                      datetime.fromtimestamp(before[label][rel]['mtime_ns'] / 1e9, timezone.utc).timetuple()[:6])
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = before[label][rel]['mode'] << 16
                with archive.open(zi, 'w', force_zip64=True) as writer:
                    actual = read_hash(path, writer)
                need(actual['bytes'] == before[label][rel]['bytes'], 'source size changed during copy')
                if pinned is not None:
                    need(actual['sha256'] == pinned, 'original pinned content mismatch: ' + str(path))
                source_members.append(dict(name=zi.filename, source=str(path), **actual))
            source_data = encoded(dict(source_members=source_members,
                              note='Source SHA/CRC measured while writing; every archived source member is rehashed after archive verification.'))
            archive.writestr('ARCHIVE_SELECTION.json', selection_data)
            archive.writestr('SOURCE_MEMBERS.json', source_data)
        metadata = [dict(name=n, bytes=len(b), sha256=sha_bytes(b), crc32=zlib.crc32(b) & 0xffffffff)
                    for n, b in [('ARCHIVE_SELECTION.json', selection_data), ('SOURCE_MEMBERS.json', source_data)]]
        all_members = {r['name']: r for r in source_members + metadata}
        with zipfile.ZipFile(zip_path, 'r') as archive:
            infos = archive.infolist()
            need(len(infos) == len(all_members) and {i.filename for i in infos} == set(all_members),
                 'ZIP membership mismatch or duplicate')
            for info in infos:
                check()
                wanted = all_members[info.filename]
                h = hashlib.sha256(); crc = 0; count = 0
                with archive.open(info, 'r') as reader:
                    while True:
                        check()
                        data = reader.read(1 << 20)
                        if not data:
                            break
                        h.update(data); crc = zlib.crc32(data, crc); count += len(data)
                need(count == info.file_size == wanted['bytes'] and h.hexdigest() == wanted['sha256'] and
                     (crc & 0xffffffff) == info.CRC == wanted['crc32'], 'ZIP member SHA/CRC mismatch: ' + info.filename)
        for row in source_members:
            need(read_hash(Path(row['source'])) == {k: row[k] for k in ('bytes', 'sha256', 'crc32')},
                 'source content changed after archive: ' + row['source'])
        after = {'core-build-02': inventory(CORE), 'core-build-01': inventory(FAILED),
                 'core-build-02-review': inventory(REVIEW)}
        need(before == after, 'source inventory metadata changed during archive')
        member_record = fresh_write('archive-members.json', encoded(list(all_members.values())))
        zip_record = dict(path=str(zip_path), **read_hash(zip_path))
        report.update(status='PREFIX_CORE02_SELECTED_ARCHIVE_PASS',
                      selected_generated_files=len(selected), selected_generated_bytes=sum(r['bytes'] for r in selected),
                      omitted_generated_files=len(omitted), omitted_generated_bytes=sum(r['bytes'] for r in omitted),
                      controller_files=len(controls), failed_files=len(before['core-build-01']),
                      review_files=len(REVIEW_NAMES), source_files=len(source_members),
                      source_bytes=sum(r['bytes'] for r in source_members), archive_members=len(all_members),
                      zip=zip_record, within_95_decimal_mb=zip_record['bytes'] <= 95000000,
                      all_member_sha_crc_verified=True, selected_original_contents_unchanged=True,
                      complete_source_inventory_metadata_unchanged=True,
                      original_inventory=inventory_record, selection=selection_record, members=member_record,
                      output_files_before_host_receipts=sorted(p.name for p in OUT.iterdir()) + ['audit.json'])
    except BaseException as error:
        report.update(status='FAILED', error=repr(error))
        raise
    finally:
        signal.alarm(0)
        report['finished'] = now()
        report['elapsed_seconds'] = time.monotonic() - START
        with (OUT / 'audit.json').open('xb') as stream:
            stream.write(encoded(report))
        print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
