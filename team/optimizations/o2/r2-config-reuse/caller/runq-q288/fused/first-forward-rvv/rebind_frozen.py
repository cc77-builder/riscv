"""Bind the published first-token target closure in a fresh controller.

This changes host helper selection only. The existing guest build, reference
qualification, controller logic and all original input pins remain unchanged.
No helper discovery is performed against the current live-build repository.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys

MANIFEST_SHA = 'df00872b6b493d9a89c37ca72c226d96bf7d5ed2882afc232186e765d68475ef'
PREFIX = 'closures/target/repo/'
CHANGED = {
    'team/optimizations/o1/audit/runtime_gate.py',
    'team/optimizations/o2/fullcore/recheck.py',
    'team/optimizations/o2/fullcore/run_suite.py',
    'team/optimizations/o2/r2-safe-tail/merged_screen.py',
    'team/optimizations/o2/r2-select/entry_c_api.py',
    'team/optimizations/o2/r2-select/entry_experiment.py',
    'team/optimizations/o2/result-width/h1/performance/build_profile.py',
}
LIVE_ONLY = {
    'team/optimizations/o2/fullcore/input_contract.py',
    'team/optimizations/o2/fullcore/live_inputs.py',
    'team/optimizations/o1/build_recipe.py',
    'team/optimizations/o1/build_inputs.py',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    paths = list(root.rglob('*'))
    need(not any(p.is_symlink() for p in paths), 'plain controller and historical source files')
    return {str(p.relative_to(root)): digest(p) for p in paths if p.is_file()}


def bind(parent, source, manifest_path, output):
    need(sys.dont_write_bytecode and parent.is_dir() and source.is_dir(), 'explicit existing roots and -B')
    need(not output.exists() and all(not output.is_relative_to(p) and not p.is_relative_to(output)
                                   for p in (parent, source)), 'fresh sibling outside old inputs')
    need(digest(manifest_path) == MANIFEST_SHA, 'published historical manifest identity')
    manifest = json.loads(manifest_path.read_text())
    rows = {row['path'][len(PREFIX):]: row for row in manifest['files'] if row['path'].startswith(PREFIX)}
    expected = {name: row['sha256'] for name, row in rows.items()}
    mirror_prefix = 'target/runtime-source/'
    mirror = {row['path'][len(mirror_prefix):]: row['sha256'] for row in manifest['files'] if row['path'].startswith(mirror_prefix)}
    need(len(rows) == 92 and expected == mirror and sum(row['size'] for row in rows.values()) == 981710,
         'both published historical closures have the same complete identity')
    need(inventory(source) == expected, 'exact existing historical source membership and SHA')
    need(all((source / name).stat().st_size == row['size'] for name, row in rows.items()), 'all historical source sizes')
    original = inventory(parent)
    binding = json.loads((parent / 'binding.json').read_text())
    need(binding['contract'] == 'r2-s3-first-forward-rvv-v1' and
         binding['status'] == 'FIRST_FORWARD_RVV_CONTROLLER_BOUND_NOT_RUNTIME', 'parent controller identity')
    need(set(original) == set(binding['generated_files']) | {'binding.json'}, 'exact parent member set')
    need(all(original[name] == value for name, value in binding['generated_files'].items()), 'all parent generated files unchanged')
    need(all(digest(path) == value for path, value in binding['input_files'].items()), 'all parent input pins unchanged')
    repo = Path(binding['config']['repository']).resolve()
    need(not output.is_relative_to(repo) and not repo.is_relative_to(output), 'new controller is outside the repository')
    old_helpers = {name.removeprefix('target-support/'): value for name, value in original.items() if name.startswith('target-support/')}
    changed = {name: dict(old_sha256=old_helpers[name], frozen_sha256=value) for name, value in expected.items()
               if name in old_helpers and old_helpers[name] != value}
    excluded = {name: value for name, value in old_helpers.items() if name not in expected}
    added = {name: value for name, value in expected.items() if name not in old_helpers}
    need(set(changed) == CHANGED and set(excluded) == LIVE_ONLY and len(added) == 39,
         'reviewed seven version differences, four live-only exclusions and 39 full-closure additions')
    unchanged = {name: value for name, value in original.items() if name != 'binding.json' and not name.startswith('target-support/')}
    output.mkdir(parents=True)
    for name in unchanged:
        dest = output / name; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(parent / name, dest)
    for name in expected:
        dest = output / 'target-support' / name; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, dest)
    shutil.copyfile(manifest_path, output / 'historical-first-token-manifest.json')
    shutil.copyfile(Path(__file__).resolve(), output / 'rebind_frozen.py')
    need(inventory(output / 'target-support') == expected, 'new target support is exactly the original 92-file closure')
    need(all(digest(output / name) == value for name, value in unchanged.items()), 'all original controller logic and metadata copied unchanged')
    proof = dict(status='CONTROLLER_FROZEN_TARGET_CLOSURE_BOUND_NO_GUEST_CHANGE',
        parent_controller=str(parent), parent_binding_sha256=original['binding.json'],
        historical_source=str(source), historical_manifest=str(manifest_path), historical_manifest_sha256=MANIFEST_SHA,
        manifest_prefix=PREFIX, published_mirror_prefix=mirror_prefix, historical_files=expected,
        historical_file_count=92, historical_bytes=981710, changed_helpers=changed, excluded_helpers=excluded,
        exclusion_basis='absent from both exact published first-token closures; current live-build gates are not the frozen T17 contract',
        added_full_closure_members=added, unchanged_controller_files=unchanged,
        parent_input_pins_preserved=True, old_input_pins_are_provenance_not_executed_helper_selection=True,
        new_builds=0, new_reference_runs=0, new_target_emu_runs=0,
        reference_reaudit_required=True, physical_reaudit_required=True, performance_qualified=False)
    (output / 'frozen-target-closure.json').write_text(json.dumps(proof, indent=2) + '\n')
    for name, value in original.items():
        binding['input_files'][str(parent / name)] = value
    for name, value in expected.items():
        binding['input_files'][str(source / name)] = value
    binding['input_files'][str(manifest_path)] = MANIFEST_SHA
    binding['input_files'][str(Path(__file__).resolve())] = digest(__file__)
    binding['target_support_files'] = 92
    binding['target_support_source_identity'] = 'exact complete published original first-token target closure; no live-build helper discovery'
    binding['frozen_target_rebinding'] = dict(parent=str(parent), manifest_sha256=MANIFEST_SHA,
                                             source=str(source), unchanged_controller_logic=True)
    binding['generated_files'] = inventory(output)
    (output / 'binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    need(inventory(parent) == original and inventory(source) == expected, 'original controller and historical source unchanged')
    need(all(digest(path) == value for path, value in binding['input_files'].items()), 'all original and historical input pins unchanged')
    need(set(inventory(output)) == set(binding['generated_files']) | {'binding.json'}, 'complete new controller manifest')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    proof = bind(args.controller.resolve(), args.source.resolve(), args.manifest.resolve(), args.output.resolve())
    print(json.dumps({key: proof[key] for key in ('status', 'historical_file_count', 'historical_bytes',
                                                'new_builds', 'new_reference_runs', 'new_target_emu_runs')}), flush=True)
