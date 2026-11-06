"""Freeze the small complete source closure read by the original identity gate."""
from pathlib import Path
import argparse
import os
import subprocess

import build as b

MIGRATION_SOURCE = 'c95ece60883ee02be5992484246b5e930e998de0'


def snapshot(campaign, source, identity_path, adapter, output):
    b.need(not output.exists() and len(os.sched_getaffinity(0)) == 1,
           'fresh support snapshot on one coordinated CPU')
    r, _ = b.support(campaign)
    g, t = r.old.r.parent.g, r.old.r.parent.t17
    original = b.read(campaign / 'runtime-inputs.json')
    initial = campaign / 'runtime-source'
    identity = b.read(identity_path)
    b.need(b.digest(identity_path) == r.old.r.parent.PARENT_IDENTITY_SHA, 'original parent identity')
    modules = {str(Path(path).relative_to(source)) for path in original
               if Path(path).is_relative_to(source)}
    b.need(modules and str(b.STAGES / 'norm/consumer/run.py') in modules
           and {str(path.relative_to(initial)) for path in r.b.module_files()} <= modules,
           'complete original recorded source inventory, including runtime entry')
    names = modules | set(g.SOURCES) | set(g.FROZEN) | set(g.PINNED) | set(g.candidate.host.PINS)
    names.update(str(path) for path in t.a.frozen_f.CHECKER_PATHS)
    names.update(str(Path('team/optimizations/o2/repro') / name) for name in t.ADAPTERS)
    names.update(str(Path('team/optimizations/o2/r2-select') / name) for name in t.FROZEN)
    runner = str(b.STAGES / 'target/reference_runner.c')
    names.add(runner)
    metadata = subprocess.check_output(['git', '-C', str(source), 'rev-parse', '--absolute-git-dir'], text=True).strip()
    blob_pins = {**g.PINNED, **g.candidate.host.PINS}
    fixed_checkers = {str(path) for path in t.a.frozen_f.CHECKER_PATHS
                      if path != t.a.frozen_f.H1DIR / 'build_profile.py'}
    payload, origins = {}, {}
    for name in sorted(names):
        rel = Path(name)
        b.need(not rel.is_absolute() and '..' not in rel.parts, 'safe support source path')
        if (initial / rel).is_file():
            path = initial / rel
            raw, origin = path.read_bytes(), str(path)
        elif name in blob_pins:
            object_id = blob_pins[name]
            raw = subprocess.check_output(['git', '--git-dir=' + metadata, 'cat-file', 'blob', object_id])
            origin = 'git-blob:' + object_id
        elif name in fixed_checkers:
            object_name = g.BASE + ':' + name
            raw = subprocess.check_output(['git', '--git-dir=' + metadata, 'show', object_name])
            origin = 'git-tree:' + object_name
        elif rel == t.a.frozen_f.H1DIR / 'build_profile.py':
            object_name = MIGRATION_SOURCE + ':' + name
            raw = subprocess.check_output(['git', '--git-dir=' + metadata, 'show', object_name])
            origin = 'git-tree:' + object_name
        else:
            path = source / rel
            raw, origin = path.read_bytes(), str(path)
        if name in modules:
            b.need(b.derive.sha(raw) == original[str(source / rel)], 'original imported source bytes')
        payload[name] = raw
        origins[name] = origin
    for name, expected in g.FROZEN.items():
        b.need(b.derive.sha(payload[name]) == expected, 'original fixed dependency SHA: ' + name)
    for name, expected in g.PINNED.items():
        b.need(g.blob(payload[name]) == expected, 'original fixed source blob: ' + name)
    for name, expected in g.candidate.host.PINS.items():
        b.need(g.candidate.host.blob(payload[name]) == expected, 'original exact host source blob: ' + name)
    for name, expected in t.FROZEN.items():
        b.need(b.derive.sha(payload[str(Path('team/optimizations/o2/r2-select') / name)]) == expected,
               'original fixed software gate SHA: ' + name)
    for name, expected in identity['adapter_sources'].items():
        b.need(b.derive.sha(payload[name]) == expected, 'original T17 adapter SHA: ' + name)
    for path in t.a.frozen_f.CHECKER_PATHS:
        name = str(path)
        if path == t.a.frozen_f.H1DIR / 'build_profile.py':
            b.need(b.derive.sha(payload[name].replace(b'\r\n', b'\n')) ==
                   t.a.frozen_f.MIGRATED_PROFILE_SHA256, 'original normalized migration checker')
        else:
            raw = subprocess.check_output(['git', '--git-dir=' + metadata, 'show', g.BASE + ':' + name])
            b.need(raw == payload[name], 'original fixed BASE checker bytes: ' + name)
    b.need(payload[runner] == (adapter / 'reference_runner.c').read_bytes()
           and b.derive.sha(payload[runner]) == '6ea9a43ddfa4420f00c7e62f101035e1e7fbf85610e607c4d7762b96c803bd2b',
           'unchanged actual original reference caller source')
    output.mkdir(parents=True)
    for name, raw in payload.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        b.need(target.read_bytes() == raw, 'written complete support bytes')
    report = dict(status='GS32_REFERENCE_SUPPORT_SNAPSHOT_COMPLETE', parent_campaign=str(campaign),
        parent_manifest_sha256=b.digest(campaign / 'runtime-inputs.json'),
        identity_sha256=b.digest(identity_path), source=str(source), git_metadata_dir=metadata,
        fixed_git_base=g.BASE, files={name:b.derive.sha(raw) for name, raw in payload.items()}, origins=origins,
        original_runtime_source_files=sorted(modules), supplemented_files=sorted(names - modules),
        source_generator_sha256=b.digest(Path(__file__)), files_count=len(payload),
        total_bytes=sum(map(len, payload.values())), original_snapshot_unchanged=True, new_checkout=False)
    b.save(output / 'support-identity.json', report)
    return {key:report[key] for key in ('status', 'files_count', 'total_bytes', 'new_checkout')}


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('campaign', 'source', 'identity', 'adapter', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(snapshot(*(getattr(args, name).resolve() for name in
        ('campaign', 'source', 'identity', 'adapter', 'output')))), flush=True)
