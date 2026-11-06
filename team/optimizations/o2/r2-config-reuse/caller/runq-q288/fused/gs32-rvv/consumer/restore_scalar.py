"""Restore only the archived original scalar case into a new audit directory.

Uses the existing team's object-ZIP verifier. No output is reconstructed from
a golden, no original run is changed, and no reference process is started.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import zipfile

import build as b

ARCHIVE_SHA = 'c10b8332590abeb7c2597e6cd051b81ba86b1de5b9b3070bbebeec3ca0b588c2'
MANIFEST_SHA = 'a72b1088cd52787fcba5cae1295fff2bace87c0f3a0f68fe897a60f08a7a9641'
ARCHIVER_SHA = '76c0ebc50b4e288883cf565bdf014dfdf9f344066992de3c6380c044a3df73c7'


def restore(archive, archiver, original, output):
    b.need(len(os.sched_getaffinity(0)) == 1 and not output.exists(), 'one CPU and fresh scalar audit view')
    b.need(b.digest(archive) == ARCHIVE_SHA and b.digest(archiver) == ARCHIVER_SHA,
           'published original archive and unchanged mature transport verifier')
    spec = importlib.util.spec_from_file_location('gs32_original_archive_verifier', archiver)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    checked = helper.verify(archive, expected=ARCHIVE_SHA)
    with zipfile.ZipFile(archive) as z:
        manifest_raw = z.read('manifest.json')
        b.need(b.derive.sha(manifest_raw) == MANIFEST_SHA, 'published original whole manifest')
        manifest = json.loads(manifest_raw)
        rows = [row for row in manifest['files'] if row['path'].startswith('consumer-reference/scalar/')]
        b.need(rows and all(len(Path(row['path']).parts) == 3 for row in rows), 'bounded original scalar case only')
        names = {Path(row['path']).name for row in rows}
        b.need({'image.bin', 'snapshots.bin', 'live-state.bin', 'flags.bin', 'result.json', 'validation.json'} <= names,
               'actual archived input and complete original output evidence')
        b.need({p.name for p in original.iterdir() if p.is_file()} <= names, 'every resident scalar file is archived')
        for row in rows:
            resident = original / Path(row['path']).name
            if resident.exists():
                b.need(resident.is_file() and b.digest(resident) == row['sha256'], 'resident original agrees with archive')
        output.mkdir(parents=True)
        for row in rows:
            name = Path(row['path']).name
            raw = z.read('objects/' + row['sha256'])
            b.need(len(raw) == row['size'] and b.derive.sha(raw) == row['sha256'], 'original archived scalar bytes')
            with (output / name).open('xb') as stream:
                stream.write(raw)
            b.need(b.digest(output / name) == row['sha256'], 'exact ordinary restored file')
    report = dict(status='GS32_ORIGINAL_SCALAR_SUBSET_RESTORED', archive=str(archive),
        archive_sha256=ARCHIVE_SHA, manifest_sha256=MANIFEST_SHA, original_scalar=str(original),
        archiver=str(archiver), archiver_sha256=ARCHIVER_SHA, whole_transport_verification=checked,
        files={Path(row['path']).name: dict(sha256=row['sha256'], size=row['size']) for row in rows},
        restored_bytes=sum(row['size'] for row in rows), new_reference_runs=0, new_emu_runs=0)
    b.save(output / 'restoration.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'archiver', 'original', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = restore(*(getattr(args, name).resolve() for name in ('archive', 'archiver', 'original', 'output')))
    print(json.dumps({key: result[key] for key in ('status', 'restored_bytes', 'new_reference_runs')}), flush=True)
