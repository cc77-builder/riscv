"""Reference-test the guarded API linked to the exact new norm consumer object."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import signal
import types

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('norm_consumer_reference', HERE / 'run.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
b, a = r.b, r.b.a
need, read, save, digest = b.need, b.read, b.save, b.digest


def validator():
    # One historical identity literal is intrinsic to the W2 validator. Derive
    # its new acceptance identity explicitly; all numerical/process code stays
    # exact, and the one replacement has a complete inverse proof.
    original = inspect.getsource(a.validate)
    before, after = repr('PURE_W2_FORWARD_REFERENCE_CAMPAIGN_PASS'), repr(b.PASS)
    need(original.count(before) == 1 and after not in original, 'one old qualification identity literal')
    derived = original.replace(before, after)
    need(derived.replace(after, before) == original, 'exact complete API validator reversal')
    namespace = dict(a.validate.__globals__)
    namespace.update(CONTRACT=b.API_CONTRACT, PREFIX=b.API_PREFIX, PASS='NORM_W2_API_REFERENCE_PASS',
                     b=types.SimpleNamespace(CONTRACT=b.CONTRACT))
    exec(compile(derived, str(HERE / 'api.py') + ':derived-parent-validator', 'exec'), namespace)
    proof = dict(parent_source_sha256=digest(Path(a.__file__)),
                 parent_function_sha256=hashlib.sha256(original.encode()).hexdigest(),
                 derived_function_sha256=hashlib.sha256(derived.encode()).hexdigest(),
                 replacements=[dict(before=before, after=after, count=1)], exact_parent_reverse=True,
                 numerical_and_process_gates_unchanged=True)
    return namespace['validate'], proof


def inputs(build, adapter, identity_path):
    record, files, identity, checker = r.verify_inputs(build, adapter, identity_path)
    need(record['contract'] == b.API_CONTRACT and record['status'] == b.API_STATIC, 'new API build identity')
    parent = Path(record['qualified_build']); qualification = Path(record['qualified_campaign'])
    parent_record = read(parent / 'result.json'); results = read(qualification / 'results.json')
    need(parent_record['contract'] == b.CONTRACT and parent_record['status'] == b.STATIC and
         results['contract'] == b.CONTRACT and results['status'] == b.PASS, 'new forward qualification')
    need(record['qualified_consumer_object_sha256'] == parent_record['artifacts'][b.CORE], 'same new qualified object')
    for name, method, negative in r.CASES:
        dest = qualification / name
        checked = r.validate(parent, dest, method, negative, read(dest / 'result.json'))
        need(checked == results['validations'][name] == read(dest / 'validation.json'), 're-audited new parent case')
        for filename in ('result.json', 'validation.json', 'reference-result.json', 'abi.json',
                         'image-control.json', 'image.bin', 'stdout.log', 'stderr.log',
                         'initial-registers.bin', 'final-registers.bin', 'initial-csrs.bin', 'final-csrs.bin'):
            b.pin(files, dest / filename)
        for filename, value in checked['raw_sha256'].items():
            b.pin(files, dest / filename, value)
    for path in (qualification / 'results.json', qualification / 'state.json', HERE / 'api.py'):
        b.pin(files, path)
    checker.verify_files(files)
    return record, files, identity, checker


def validate(build, dest, record, receipt):
    check, _ = validator()
    return check(build, dest, record, receipt)


def run(build, adapter, identity_path, output):
    need(len(os.sched_getaffinity(0)) == 1, 'one API reference CPU')
    _, proof = validator()
    # Reuse the existing owned-process runner. Identity and file bindings point
    # to the distinct new build; the old module and results remain untouched.
    runner = b.bind(a.run, inputs=inputs, validate=validate, CONTRACT=b.API_CONTRACT,
                    PREFIX=b.API_PREFIX, PASS='NORM_W2_API_REFERENCE_PASS')
    state = runner(build, adapter, identity_path, output)
    need(state['status'] == 'SHARED_W2_API_REFERENCE_CAMPAIGN_PASS' and state['active_pid'] is None,
         'complete guarded API reference')
    results = read(output / 'results.json')
    need(results['contract'] == b.API_CONTRACT, 'new API identity throughout')
    state['status'] = results['status'] = b.API_PASS
    results['validator_derivation'] = proof
    save(output / 'validator-derivation.json', proof)
    save(output / 'results.json', results); save(output / 'state.json', state)
    return state


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('norm API reference signal')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'adapter', 'identity', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, [min(os.sched_getaffinity(0))])
    result = run(*(getattr(args, name).resolve() for name in ('build', 'adapter', 'identity', 'output')))
    print(json.dumps(dict(contract=b.API_CONTRACT, status=result['status']), indent=2))
