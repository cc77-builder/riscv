"""Copy this round's verified evidence into its new Git-backed module."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path('/home/lizufan/riscv-lab/r2s3-split-20261025-0716')
MONITOR = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/monitor-r2s3-split-20261025-0716')
WORK = Path('/mnt/d/Projects/competitions/2026-10-CIE-RISCV-XiangShan/working-r2s3-split-20261025-0716')
REL = Path('team/optimizations/o2/r2-config-reuse/caller/split')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    post = read(ROOT / 'postverify-v2-01.json')
    campaign = read(ROOT / 'run-02/state.json')
    library = read(ROOT / 'library-v2-01/library.json')
    archive = read(ROOT / 'archive-audit-v2-01.json')
    mutations = read(ROOT / 'mutations-v2-01.json')
    harness = read(ROOT / 'harness-check-01/result.json')
    assert post['status'] == 'POSTVERIFY_PASS'
    assert campaign['status'] == 'SPLIT_CAMPAIGN_PASS' and campaign['active_pid'] is None
    assert library['status'] == 'SPLIT_GNU_LIBRARY_AND_CONSUMER_LINK_PASS'
    assert archive['status'] == 'SPLIT_ARCHIVE_RAW_AUDIT_PASS'
    assert mutations['status'] == 'SPLIT_TARGETED_NEGATIVE_CHECKS_PASS'
    assert harness['status'] == 'SPLIT_C_HARNESS_BYTE_FAULTS_PASS'
    image = '2f94ede51e1c555aa7eceb777b4d2ab859418828d56705783ab72b4bcdb57aed'
    assert library['qualified_image_sha256'] == archive['image_sha256'] == mutations['image_sha256'] == image
    destination = WORK / REL / 'evidence'
    assert not destination.exists()
    build = read(ROOT / 'build-04/build.json')
    own = {name: pin for name, pin in build['software_files'].items() if name.startswith(REL.as_posix() + '/')}
    assert len(own) == 8 and all(sha(WORK / name) == pin for name, pin in own.items())
    destination.mkdir()
    mappings = [
        (ROOT / 'archive-v2-01', destination / 'split-input-v2'),
        (ROOT / 'failed-v1-archive-01', destination / 'failed-v1'),
        (ROOT / 'library-v2-01', destination / 'library-v2'),
        (ROOT / 'harness-check-01', destination / 'harness-v2'),
        (MONITOR / 'statistics-v2', destination / 'statistics-v2'),
    ]
    for source, target in mappings:
        assert not any(p.is_symlink() for p in source.rglob('*'))
        shutil.copytree(source, target)
        before = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
        after = {p.relative_to(target).as_posix(): sha(p) for p in target.rglob('*') if p.is_file()}
        assert before == after
    reports = destination / 'reports'
    reports.mkdir()
    names = ['archive-audit-v2-01.json', 'mutations-v2-01.json', 'postverify-v2-01.json',
             'setup.json', 'setup-v2.json', 'dependency-closure.json', 'run-02-driver.json']
    names += [p.name for p in sorted(ROOT.glob('*-driver.*'))
              if p.name.startswith(('build-04-', 'harness-check-01-', 'mutations-v2-01-',
                                    'library-v2-01-', 'failed-v1-archive-01-', 'archive-v2-01-',
                                    'archive-audit-v2-01-'))]
    for name in sorted(set(names)):
        source = ROOT / name
        assert source.is_file() and not source.is_symlink(), name
        shutil.copyfile(source, reports / name)
        assert sha(source) == sha(reports / name)
    for name in ['preserve_failed_v1.py', 'postverify_v2.py', 'assemble_evidence_v2.py', 'host-operations.json']:
        source = MONITOR / name
        shutil.copyfile(source, reports / name)
        assert sha(source) == sha(reports / name)
    locations = {
        'operation_id': '20261025-LiZufan001-r2s3-split-0716',
        'claim': 'https://github.com/cc77-builder/riscv/issues/2#issuecomment-6390798028',
        'source_base': '71b24fc43a7111abae1012d0c4bcaf89f249300f',
        'native_root': str(ROOT), 'v1_source': str(ROOT / 'source'), 'v2_source': str(ROOT / 'source-v2'),
        'windows_worktree': r'D:\Projects\competitions\2026-10-CIE-RISCV-XiangShan\working-r2s3-split-20261025-0716',
        'branch': 'work/r2s3-split-20261025-0716',
        'v1_host_operation': '1bcd341bbd2162e3d9e297ccd2678ca0.0d85897dcad608d2a638ef32a901bab2',
        'v2_host_operation': '1bcd341bbd2162e3d9e297ccd2678ca0.17c12b10369d5af794226c1cd427b15d',
        'frozen_outputs': ['build-01', 'build-02', 'build-03', 'build-04', 'run-01', 'run-02'],
        'campaign': campaign, 'runtime_source_sha256': own,
        'new_emu_runs_this_round': campaign['new_emu_runs'] + read(ROOT / 'run-01/state.json')['new_emu_runs'],
        'native_git_dependency': 'source-v2 borrows source objects; source borrows the hoisted donor chain; keep all donors until separately verified retention',
        'prior_r3_protection': 'Prior unknown R3 receipt/lock remains protected under its existing Issue/handoff; this round does not release it',
        'originals_removed': 0, 'deployment': False,
    }
    (destination / 'locations.json').write_text(json.dumps(locations, indent=2) + '\n')
    files = [{'path': p.relative_to(destination).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(destination.rglob('*')) if p.is_file()]
    result = {'status': 'SPLIT_V2_EVIDENCE_COPIED_AND_HASHED',
              'created': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'image_sha256': image, 'files': files, 'file_count': len(files),
              'total_bytes': sum(row['bytes'] for row in files),
              'manifest_excludes': ['manifest.json'], 'originals_removed': 0}
    (destination / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))


if __name__ == '__main__':
    main()
