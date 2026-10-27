"""Prepare closed W2 evidence and reuse the existing byte-preserving transport.

All ordinary files are copied exactly; no image/dump reconstruction recipes and
no numerical decisions are introduced here. Frozen project-source snapshots
are completed from the original runtime pins before invoking archive.py.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil, sys

HERE = Path(__file__).resolve().parent
REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/w2')
REPO = HERE.parents[8]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


archive = load('original_w2_byte_archive', HERE.parent / 'archive.py')
restore = load('original_w2_byte_restore', HERE.parent / 'restore.py')
need = archive.need


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare(inputs, output, snapshot_roots=()):
    need(not output.exists(), 'fresh isolated transport workspace')
    snapshot_roots = [Path(path).resolve() for path in snapshot_roots]
    need(all(path.is_dir() for path in snapshot_roots), 'existing explicitly supplied older source snapshots')
    helpers = {name: path.read_bytes() for name, path in (
        ('evidence.py', HERE / 'evidence.py'), ('archive.py', HERE.parent / 'archive.py'),
        ('restore.py', HERE.parent / 'restore.py'))}
    roots = {}
    for item in inputs:
        label, path = item.split('=', 1)
        archive.safe(label)
        need('/' not in label and label not in roots and label != 'transport', 'unique ordinary root label')
        root = Path(path).resolve()
        need(root.is_dir() and not output.is_relative_to(root), 'existing source and external output')
        state_path = root / 'state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            need(state.get('finished') and not state.get('active') and state.get('active_pid') is None and
                 not state.get('cleanup_unknown'), 'closed source evidence, no active owner')
        roots[label] = root
    output.mkdir(parents=True)
    staging = output / 'staging'
    staging.mkdir()
    copies, sources, original_roots = {}, {}, {}
    for label, root in roots.items():
        dest = staging / label
        dest.mkdir()
        inventory = {}
        for path in sorted(root.rglob('*')):
            need(not path.is_symlink(), 'ordinary immutable source evidence')
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            # Python bytecode is neither a runtime input nor a raw artifact.
            need('__pycache__' not in rel.parts and path.suffix != '.pyc', 'no unrecorded bytecode cache in archive input')
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            value = sha(path)
            shutil.copyfile(path, target)
            need(sha(path) == sha(target) == value, 'source unchanged during exact staging copy')
            inventory[rel.as_posix()] = value
        copies[label] = inventory
        pins_path = root / 'runtime-inputs.json'
        if not pins_path.exists():
            continue
        pins = json.loads(pins_path.read_text())
        # The current checkout is the known source owner. Build snapshots also
        # contain */source/repo/<entry>; suffix matching is therefore ambiguous.
        original = REPO
        need(any(str(original / REL / name) in pins for name in ('reference.py', 'consumer_run.py', 'api.py', 'run.py')),
             'known original project root is explicitly pinned by this campaign')
        original_roots[label] = str(original)
        captured = {}
        for name, value in pins.items():
            path = Path(name)
            if not path.is_relative_to(original):
                continue
            rel = path.relative_to(original)
            # Existing frozen campaign snapshots take precedence over the live
            # checkout. A newer source cannot replace an old runtime identity.
            choices = (root / 'runtime-source' / rel, root / 'source' / rel,
                       *(folder / rel for folder in snapshot_roots), path)
            candidates = [p for p in choices if p.is_file() and sha(p) == value]
            need(candidates, 'original pinned project source is available: ' + str(rel))
            target = dest / 'runtime-source' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                need(sha(target) == value, 'existing snapshot is exact')
            else:
                shutil.copyfile(candidates[0], target)
            need(sha(target) == value, 'complete frozen project-source identity')
            captured[rel.as_posix()] = value
        sources[label] = captured
        print('staged', label, len(inventory), 'files; source closure', len(captured), flush=True)
    for label, root in roots.items():
        need({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} == set(copies[label]),
             'source file membership unchanged during preparation')
        need(all(sha(root / name) == value for name, value in copies[label].items()), 'all original source bytes remain frozen')
    metadata = staging / 'transport'
    metadata.mkdir()
    for name, raw in helpers.items():
        (metadata / name).write_bytes(raw)
    need(sha(HERE / 'evidence.py') == hashlib.sha256(helpers['evidence.py']).hexdigest() and
         sha(HERE.parent / 'archive.py') == hashlib.sha256(helpers['archive.py']).hexdigest() and
         sha(HERE.parent / 'restore.py') == hashlib.sha256(helpers['restore.py']).hexdigest(),
         'executed transport helpers unchanged')
    save(metadata / 'preparation.json', dict(format='w2-exact-staging-v1',
        source_roots={k: str(v) for k, v in roots.items()}, original_files=copies,
        captured_runtime_project_sources=sources, runtime_original_project_roots=original_roots,
        older_snapshot_search_roots=[str(path) for path in snapshot_roots],
        preparer_sha256=sha(HERE / 'evidence.py'),
        original_archiver_sha256=sha(HERE.parent / 'archive.py'),
        original_restorer_sha256=sha(HERE.parent / 'restore.py')))
    report = archive.seal([name + '=' + str(staging / name) for name in (*roots, 'transport')], output / 'archive')
    save(output / 'archive/restore-verification.json', archive.verify(output / 'archive/payload.zip', output / 'restored', report['archive_sha256']))
    publish = output / 'published'
    publish.mkdir()
    metadata_names = ('manifest.json', 'verification.json', 'restore-verification.json')
    metadata_pins = {}
    for name in metadata_names:
        shutil.copyfile(output / 'archive' / name, publish / name)
        metadata_pins[name] = dict(bytes=(publish / name).stat().st_size, sha256=sha(publish / name))
    parts = []
    with (output / 'archive/payload.zip').open('rb') as source:
        while True:
            block = source.read(20 * 1024 * 1024)
            if not block:
                break
            name = f'payload.zip.part-{len(parts) + 1:04d}'
            (publish / name).write_bytes(block)
            parts.append(dict(path=name, bytes=len(block), sha256=hashlib.sha256(block).hexdigest()))
    save(publish / 'parts.json', dict(format='forward-evidence-parts-v1', artifact='payload.zip',
        bytes=report['archive_bytes'], sha256=report['archive_sha256'], parts=parts, metadata=metadata_pins))
    joined = restore.restore(publish, output / 'reassembled')
    need(joined['archive_sha256'] == report['archive_sha256'], 'actual published fragment reassembly')
    result = dict(status='W2_ORIGINAL_BYTES_PACKAGED', archive=report, fragment_transport=joined,
        manifest_sha256=sha(publish / 'manifest.json'), parts_manifest_sha256=sha(publish / 'parts.json'),
        roots=list(roots), source_snapshot_counts={name: len(values) for name, values in sources.items()},
        new_reference_runs=0, new_emu_runs=0, performance_qualified=False)
    save(output / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', action='append', required=True)
    parser.add_argument('--snapshot-root', action='append', type=Path, default=[],
        help='read-only older repository-shaped source closure; every selected file must match its runtime SHA')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.output.resolve(), args.snapshot_root), indent=2))
