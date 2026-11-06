"""Complete a copied controller's Python helper snapshot without changing code.

The qualified controller, guest build, reference results and their input files
remain untouched. This adds actual imported helper modules missed by a traversal
of module-valued attributes (notably `from module import function`).
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import types

HERE = Path(__file__).resolve().parent
STAGES = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages')


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def seal(parent, output):
    need(sys.dont_write_bytecode and parent.is_dir() and not output.exists(), 'read-only original and fresh -B output')
    need(not output.is_relative_to(parent) and not parent.is_relative_to(output), 'new controller is outside the frozen original')
    binding = json.loads((parent / 'binding.json').read_text())
    need(binding['contract'] == 'r2-s3-first-forward-rvv-v1' and
         binding['status'] == 'FIRST_FORWARD_RVV_CONTROLLER_BOUND_NOT_RUNTIME', 'original controller identity')
    original = {str(p.relative_to(parent)): sha(p) for p in parent.rglob('*') if p.is_file()}
    need(set(original) == set(binding['generated_files']) | {'binding.json'}, 'exact original controller inventory')
    need(all(original[n] == v for n, v in binding['generated_files'].items()), 'all original controller bytes')
    need(all(sha(p) == value for p, value in binding['input_files'].items()), 'original controller inputs still frozen')
    need(not any(p.is_symlink() for p in parent.rglob('*')), 'plain immutable controller files')
    repo = Path(binding['config']['repository']).resolve()
    need(not output.is_relative_to(repo) and not repo.is_relative_to(output), 'new helper snapshot is outside the repository')
    audit = load('first_forward_support_completion_audit', repo / STAGES / 'norm/target/audit.py')
    roots = [audit, *audit.gates()]
    for index, rel in enumerate(('team/optimizations/o2/fullcore/run_suite.py',
            'team/optimizations/o2/result-width/h1/performance/build_profile.py', 'team/scripts/artifact_guard.py')):
        roots.append(load('first_forward_support_completion_physical_' + str(index), repo / rel))
    pending, seen, closure = [*roots, *list(sys.modules.values())], set(), {}
    while pending:
        module = pending.pop()
        if not isinstance(module, types.ModuleType) or id(module) in seen:
            continue
        seen.add(id(module))
        pending.extend(value for value in vars(module).values() if isinstance(value, types.ModuleType))
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_file() and path.is_relative_to(repo) and path != Path(__file__).resolve():
                closure[str(path.relative_to(repo))] = (path, sha(path))
    need(any(Path(name).name == 'build_inputs.py' for name in closure), 'actual from-import dependency discovered')
    # Refuse conflicting helper versions before creating the new controller.
    added = {}
    for name, (path, value) in closure.items():
        relative = 'target-support/' + name
        if relative in original:
            need(original[relative] == value, 'existing helper version remains exact: ' + name)
        else:
            added[relative] = value
    need(added, 'a concrete missing-helper closure is completed')
    shutil.copytree(parent, output)
    for name, (path, value) in closure.items():
        dest = output / 'target-support' / name
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        need(sha(dest) == value, 'complete byte-identical helper copy')
        binding['input_files'][str(path)] = value
    for name, value in original.items():
        binding['input_files'][str(parent / name)] = value
    shutil.copyfile(HERE / 'seal.py', output / 'seal.py')
    binding['input_files'][str(HERE / 'seal.py')] = sha(HERE / 'seal.py')
    proof = dict(status='CONTROLLER_HELPER_CLOSURE_COMPLETED_NO_GUEST_CHANGE', parent_controller=str(parent),
                 parent_binding_sha256=original['binding.json'], added_helpers=added,
                 unchanged_files={n: v for n, v in original.items() if n != 'binding.json'},
                 discovery='actual module graph plus sys.modules, including from-import dependencies',
                 new_builds=0, new_reference_runs=0, new_target_emu_runs=0,
                 reference_reaudit_required=True, performance_qualified=False)
    (output / 'support-completion.json').write_text(json.dumps(proof, indent=2) + '\n')
    binding['target_support_files'] = len(list((output / 'target-support').rglob('*.py')))
    binding['target_support_source_identity'] = 'unchanged original helper bytes; actual from-import closure added'
    binding['support_completion'] = dict(parent=str(parent), parent_binding_sha256=original['binding.json'])
    binding['generated_files'] = {str(p.relative_to(output)): sha(p) for p in output.rglob('*')
                                  if p.is_file() and p != output / 'binding.json'}
    (output / 'binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    need(all(sha(parent / n) == value for n, value in original.items()), 'original controller unchanged')
    need(all(sha(output / n) == value for n, value in proof['unchanged_files'].items()), 'all copied original code unchanged')
    need(all(sha(p) == value for p, value in binding['input_files'].items()), 'all original and added source inputs unchanged')
    return proof


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = seal(args.controller.resolve(), args.output.resolve())
    print(json.dumps({key: result[key] for key in ('status', 'new_builds', 'new_reference_runs', 'new_target_emu_runs')}), flush=True)
