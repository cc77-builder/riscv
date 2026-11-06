"""Complete the frozen NEMU provenance data input in a new controller.

Only one non-code manifest is added. All 92 historical target helpers and all
existing controller code retain their exact bytes. No patch is applied and no
NEMU, guest or hardware build is executed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

MANIFEST = 'team/patches/nemu/manifest.json'
MANIFEST_SHA = '1fee8f48616d7d09f46fd5924fb677f4a042ab7a6e2098a4af93e5e4e6a495a1'
MANIFEST_BLOB = '8c5e48287e81d4e1dbe90ce52fec45542cf06f3d'
HARDWARE_COMMIT = '34bae6d4acceac939f958199dae53c14bc1f6183'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    paths = list(root.rglob('*'))
    need(not any(path.is_symlink() for path in paths), 'plain frozen controller members')
    return {str(path.relative_to(root)): sha(path) for path in paths if path.is_file()}


def complete(parent, output):
    need(sys.dont_write_bytecode and parent.is_dir() and not output.exists(), 'existing parent and fresh -B output')
    need(not parent.is_relative_to(output) and not output.is_relative_to(parent), 'outside original controller')
    original = inventory(parent)
    binding = json.loads((parent / 'binding.json').read_text())
    need(binding['contract'] == 'r2-s3-first-forward-rvv-v1' and
         binding['status'] == 'FIRST_FORWARD_RVV_CONTROLLER_BOUND_NOT_RUNTIME', 'exact parent experiment')
    need(set(original) == set(binding['generated_files']) | {'binding.json'} and
         all(original[name] == digest for name, digest in binding['generated_files'].items()), 'all original controller bytes')
    need(all(sha(path) == digest for path, digest in binding['input_files'].items()), 'all original input pins')
    proof = json.loads((parent / 'frozen-target-closure.json').read_text())
    historical = proof['historical_files']
    need(len(historical) == 92 and inventory(parent / 'target-support') == historical, 'exact frozen 92-source closure')
    identity_path = Path(binding['config']['identity'])
    identity = json.loads(identity_path.read_text())
    hardware = Path(identity['configuration']['hardware_source']).resolve()
    repo = Path(binding['config']['repository']).resolve()
    need(all(not output.is_relative_to(root) and not root.is_relative_to(output) for root in (hardware, repo)),
         'new data closure is outside hardware and repository')
    source = hardware / MANIFEST
    need(not source.is_symlink() and source.stat().st_size == 1062 and sha(source) == MANIFEST_SHA,
         'exact physical original manifest bytes')
    need(not any(os.environ.get(key) for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')), 'own hardware Git discovery')
    head = subprocess.check_output(['git', '--no-optional-locks', '-C', str(hardware), 'rev-parse', 'HEAD'], text=True).strip()
    need(head == HARDWARE_COMMIT, 'original hardware HEAD')
    blob = subprocess.check_output(['git', '--no-optional-locks', '-C', str(hardware), 'rev-parse', 'HEAD:' + MANIFEST], text=True).strip()
    raw = subprocess.check_output(['git', '--no-optional-locks', '-C', str(hardware), 'show', 'HEAD:' + MANIFEST])
    need(blob == MANIFEST_BLOB and raw == source.read_bytes(), 'physical manifest equals immutable original Git blob')
    manifest = json.loads(raw)
    provenance_path = Path(identity['configuration']['reference']).resolve().parents[1] / 'build/vdot-provenance.json'
    provenance = json.loads(provenance_path.read_text())
    need(provenance == identity['hardware_profile']['reference_provenance'], 'actual original reference provenance equals parent identity')
    need(set(manifest) == {'base_rev', 'contract_id', 'patch_sha256', 'patch_version', 'patched_source_sha256', 'platform_profile'} and
         all(provenance.get(key) == value for key, value in manifest.items()), 'all six original manifest fields agree')
    fixed = {str(source): MANIFEST_SHA, str(identity_path): sha(identity_path), str(provenance_path): sha(provenance_path)}
    shutil.copytree(parent, output)
    destination = output / 'target-support' / MANIFEST
    need(not destination.exists(), 'only a missing non-code data input is added')
    destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, destination)
    shutil.copyfile(Path(__file__).resolve(), output / 'complete_data.py')
    unchanged = {name: digest for name, digest in original.items() if name != 'binding.json'}
    data_proof = dict(status='FROZEN_TARGET_NEMU_DATA_COMPLETED_NO_CODE_CHANGE', parent_controller=str(parent),
        parent_binding_sha256=original['binding.json'], unchanged_files=unchanged,
        added_data={MANIFEST: dict(source=str(source), bytes=1062, sha256=MANIFEST_SHA,
            git_commit=head, git_blob=blob, all_manifest_fields_equal_original_provenance=True)},
        historical_source_members=92, target_support_members=93,
        dependency_scope='verify_nemu(reference) and nemu_snapshot read only this manifest relative to the helper ROOT; actual NEMU/config/dependencies/system inputs remain physically checked',
        patch_file_read_or_applied=False, old_t17_tree_modified=False,
        new_builds=0, new_reference_runs=0, new_target_emu_runs=0,
        physical_reaudit_required=True, performance_qualified=False)
    (output / 'frozen-target-data.json').write_text(json.dumps(data_proof, indent=2) + '\n')
    binding['input_files'].update(fixed)
    binding['input_files'].update({str(parent / name): digest for name, digest in original.items()})
    binding['input_files'][str(Path(__file__).resolve())] = sha(__file__)
    binding['target_support_files'] = 93
    binding['target_support_source_identity'] = 'exact 92 published original helper/source files plus one original NEMU provenance manifest data file'
    binding['frozen_target_data_completion'] = dict(parent=str(parent), added=MANIFEST, sha256=MANIFEST_SHA)
    binding['generated_files'] = {name: digest for name, digest in inventory(output).items() if name != 'binding.json'}
    (output / 'binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    need(inventory(output / 'target-support') == {**historical, MANIFEST: MANIFEST_SHA}, 'exact 92-source plus one-data closure')
    need(inventory(parent) == original and all(sha(output / name) == digest for name, digest in unchanged.items()),
         'all original inputs and copied code remain byte identical')
    need(all(sha(path) == digest for path, digest in binding['input_files'].items()), 'all input pins still match')
    return data_proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    proof = complete(args.controller.resolve(), args.output.resolve())
    print(json.dumps({key: proof[key] for key in ('status', 'historical_source_members', 'target_support_members',
                                                'new_builds', 'new_reference_runs', 'new_target_emu_runs')}), flush=True)
