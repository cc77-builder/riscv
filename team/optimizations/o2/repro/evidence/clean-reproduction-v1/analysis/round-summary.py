"""Bind this completed T17 attempt's independent audits into a result summary.

This is a derived report, not another simulator or a replacement for raw-log
auditing. Publication, Git index checks and cross-machine installation remain
separate. The existing audit reports must already describe these exact bytes.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve()
require(not args.output.exists(), 'summary output must be new')
inputs = {}


def read(relative):
    raw = (root / relative).read_bytes()
    inputs[relative] = sha(raw)
    return json.loads(raw)


def moment(value):
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, 'timestamp must include timezone')
    return result


def archive(name, proof):
    relative = name + '/archive-manifest.json'
    manifest = read(relative)
    records = manifest['files']
    expected = dict(files=len(records), raw_bytes=sum(r['raw_bytes'] for r in records),
                    stored_bytes=sum(r['stored_bytes'] for r in records),
                    archive_manifest_sha256=inputs[relative])
    require(proof['archive'] == expected, name + ': audit/manifest identity')
    by_logical = {}
    for row in records:
        path = PurePosixPath(row['stored'])
        require(not path.is_absolute() and '..' not in path.parts and path.parts[0] == 'files',
                name + ': unsafe manifest path')
        logical = str(PurePosixPath(*path.parts[1:]))
        if row['encoding'] == 'gzip':
            require(logical.endswith('.gz'), name + ': gzip path')
            logical = logical[:-3]
        else:
            require(row['encoding'] == 'identity', name + ': encoding')
        require(logical not in by_logical, name + ': duplicate logical record')
        by_logical[logical] = row

    def exact(logical, relative):
        row = by_logical[logical]
        stored = (root / name / row['stored']).read_bytes()
        require(sha(stored) == row['stored_sha256'] and len(stored) == row['stored_bytes'],
                name + ': selected stored payload')
        raw = gzip.decompress(stored) if row['encoding'] == 'gzip' else stored
        current = (root / relative).read_bytes()
        inputs[relative] = sha(current)
        require(sha(raw) == row['raw_sha256'] and len(raw) == row['raw_bytes'] and raw == current,
                name + ': selected report/identity payload differs: ' + logical)
    return manifest, exact


identity = read('identity-02.json')
identity_sha = inputs['identity-02.json']
emu_sha = identity['hardware_profile']['emu_sha256']
fc = read('fullcore-run-01/results.json')
fc_state = read('fullcore-run-01/state.json')
fc_physical = read('fullcore-audit-01/results.json')
fc_proof = read('fullcore-detached-audit-01.json')
c_outer = read('c-run-01/t17-result.json')
matrix_outer = read('matrix-run-01/t17-result.json')
c_physical = read('c-audit-01.json')
c_outer_proof = read('c-archive-audit-02.json')
matrix_outer_proof = read('matrix-archive-audit-03.json')
for label, outer in [('C', c_outer), ('matrix', matrix_outer),
                     ('C archive', c_outer_proof), ('matrix archive', matrix_outer_proof)]:
    require(outer['identity_sha256'] == identity_sha and outer['emu_sha256'] == emu_sha and
            outer['hardware_contract'] == 't17-clean-build-v1' and
            outer['historical_fixed_hardware_acceptance'] is False, label + ': T17 identity')
c, matrix = c_outer['software_gate_result'], matrix_outer['software_gate_result']
c_proof, matrix_proof = c_outer_proof['software_gate_result'], matrix_outer_proof['software_gate_result']
require(read('c-run-01/state.json') == c and read('matrix-run-01/state.json') == matrix,
        'T17 wrapper differs from independently audited runtime state')
require(c_outer_proof['audit_source_sha256'] == matrix_outer_proof['audit_source_sha256'],
        'C/matrix audit sources differ')

require(fc['status'] == fc_state['status'] == 'T17_FRESH_FULLCORE_PASS' and
        fc['identity_sha256'] == identity_sha and fc['emu_sha256'] == emu_sha and
        fc['reference_sha256'] == identity['reference_sha256'] and
        fc['new_emu_runs'] == 14 and fc['reused_execution_verdicts'] == 0 and
        fc['normal_reference_recovery'] is True, 'fullcore completion')
require(fc_physical['status'] == 'T17_FRESH_FULLCORE_RAW_AUDIT_PASS' and
        fc_physical['source_result_sha256'] == inputs['fullcore-run-01/results.json'] and
        fc_proof['status'] == 'T17_FULLCORE_ARCHIVE_RAW_AUDIT_PASS' and
        fc_proof['source_new_emu_runs'] == 14 and fc_proof['new_emu_runs'] == 0 and
        fc_proof['complete_normal_traces'] == 13 and fc_proof['expected_negative_traces'] == 1 and
        fc_proof['matrix_unique'] == 117 and fc_proof['matrix_executed'] == 124 and
        fc_proof['suite_coverage'] == fc['suite_coverage'] and
        fc_proof['suite_coverage']['complete'] is True, 'fullcore audit binding')
require(c['status'] == 'R4_C_APPLICATION_CALLS_PASS' and c['new_emu_runs'] == 3 and
        c['normal_runs'] == 2 and c['expected_negative_runs'] == 1 and
        c['public_functions'] == 16 and c['distinct_cases'] == 48 and c['normal_case_executions'] == 96,
        'ordinary C completion')
require(c_physical['identity_sha256'] == identity_sha and
        c_physical['proof']['status'] == 'R4_C_APPLICATION_RAW_AUDIT_PASS' and
        c_physical['proof']['physical_external_inputs_revalidated'] is True and
        c_proof['status'] == 'R4_C_APPLICATION_ARCHIVE_RAW_AUDIT_PASS' and
        c_proof['public_functions'] == 16 and c_proof['distinct_cases'] == 48 and
        c_proof['normal_case_executions'] == 96 and c_proof['original_emu_processes'] == 3 and
        c_proof['new_emu_runs'] == c_proof['new_nemu_runs'] == 0, 'ordinary C audit binding')
require(matrix['status'] == 'R4_CALLABLE_ENTRY_SCREEN_PASS' and matrix['new_emu_runs'] == 33 and
        matrix['normal_runs'] == 32 and matrix['negative_runs'] == 1 and matrix['measured_windows'] == 384 and
        matrix['qualification']['real_negative_and_same_image_recovery'] is True and
        matrix['qualification']['all_shape_replay_complete'] is True and
        matrix['qualification']['historical_performance_reused'] is False, 'matrix completion')
require(matrix_proof['status'] == 'R4_ENTRY_ARCHIVE_ARCHITECTURE_COUNTER_TRACE_PASS' and
        matrix_proof['qualification_scope'] == 'matrix' and matrix_proof['formal_normal_images'] == 24 and
        matrix_proof['replay_images'] == 8 and matrix_proof['expected_negative_runs'] == 1 and
        matrix_proof['original_emu_processes'] == 33 and matrix_proof['formal_windows'] == 384 and
        matrix_proof['all_window_replay_comparisons'] == 192 and
        matrix_proof['new_emu_runs'] == matrix_proof['new_nemu_runs'] == 0, 'matrix audit binding')
require(fc_state['active'] == {} and fc_state['new_emu_runs'] ==
        fc_state['new_emu_launch_attempts'] == 14 and
        moment(fc_state['started']) <= moment(fc_state['finished']), 'fullcore: pending execution')
for label, state in [('C', c), ('matrix', matrix)]:
    require(state['active_pid'] is None and state['active_result'] is None and
            moment(state['started']) <= moment(state['finished']), label + ': pending execution')
require(moment(matrix['started']) > max(moment(fc['finished']), moment(c['finished'])),
        'performance overlaps correctness execution')

fc_manifest, fc_exact = archive('fullcore-archive-01', fc_proof)
matrix_manifest, matrix_exact = archive('matrix-archive-03', matrix_proof)
c_manifest, c_exact = archive('c-archive-02', c_proof)
fc_exact('campaign/identity.json', 'identity-02.json')
fc_exact('campaign/state.json', 'fullcore-run-01/state.json')
fc_exact('campaign/results.json', 'fullcore-run-01/results.json')
fc_exact('physical-audit/results.json', 'fullcore-audit-01/results.json')
fc_exact('support/support-proof.json', 'support-proof.json')
matrix_exact('support/identity-02.json', 'identity-02.json')
matrix_exact('support/support-proof.json', 'support-proof.json')
matrix_exact('campaigns/matrix-run-01/t17-result.json', 'matrix-run-01/t17-result.json')
matrix_exact('campaigns/matrix-run-01/state.json', 'matrix-run-01/state.json')
c_exact('run/t17-result.json', 'c-run-01/t17-result.json')
c_exact('run/state.json', 'c-run-01/state.json')
require(c_manifest['matrix_manifest_sha256'] == c_proof['matrix_manifest_sha256'] ==
        inputs['matrix-archive-03/archive-manifest.json'], 'C/matrix archive anchor')
for kind, outer, manifest, count in [('matrix', matrix_outer_proof, matrix_manifest, 1),
                                   ('c', c_outer_proof, c_manifest, 3)]:
    transport, declared = outer['transport'], manifest['transport']
    require(outer['transport_contract'] == transport['contract'] == declared['contract'] == 't17-portable-entry-v2' and
            outer['transport_source_sha256'] == declared['source_tool_sha256'] and declared['kind'] == kind and
            transport['status'] == 'T17_PORTABLE_NAMESPACE_PASS' and
            transport['runtime_input_hashes_changed'] is False and transport['raw_auditor_sources_changed'] is False and
            all(transport[k] == declared[k] for k in ('source_manifest_sha256', 'source_archive', 'relocations')) and
            len(transport['relocations']) == count and
            all(v['before']['sha256'] == v['after']['sha256'] for v in transport['relocations'].values()),
            kind + ': transport contract/identity')
require(c_outer_proof['transport_source_sha256'] == matrix_outer_proof['transport_source_sha256'],
        'C/matrix transport sources differ')
detached = {}
for label, guard_name, audit_name, archive_name, action, script_name, script_sha in [
    ('fullcore', 'fullcore-detached-guard-01.json', 'fullcore-detached-audit-01.json', 'fullcore-archive-01',
     'audit', 'clean_fullcore_evidence.py', '20bebd4f5526a3522a09c2324e683d34b55997930c5078e89c3e5d04a6733412'),
    ('matrix', 'matrix-detached-guard-03.json', 'matrix-archive-audit-03.json', 'matrix-archive-03',
     'audit-matrix', 'clean_portable_evidence.py', matrix_outer_proof['transport_source_sha256']),
    ('ordinary_c', 'c-detached-guard-02.json', 'c-archive-audit-02.json', 'c-archive-02',
     'audit-c', 'clean_portable_evidence.py', c_outer_proof['transport_source_sha256'])]:
    guard = read(guard_name)
    arguments = guard['arguments']
    def option(name):
        require(arguments.count(name) == 1, label + ': detached option inventory')
        return arguments[arguments.index(name) + 1]
    checkout = root / 'portable-audit/source'
    require(guard['status'] == 'T17_DETACHED_AUDIT_PASS' and guard['auditor_succeeded'] is True and
            guard['guard_self_test'] is True and guard['rejected_runtime_accesses'] == [] and
            guard['build_present'] is False and guard['out_present'] is False and
            guard['new_emu_runs'] == guard['new_nemu_runs'] == 0 and
            guard['checkout'] == guard['execution_cwd'] == str(checkout) and guard['revision'] == identity['source_commit'] and
            guard['script'] == str(checkout / 'team/optimizations/o2/repro' / script_name) and
            guard['script_sha256'] == script_sha and
            guard['launcher_sha256'] == sha((root / 'analysis/detached-audit.py').read_bytes()) and
            guard['auditor_output'] == dict(path=str(root / audit_name), sha256=inputs[audit_name]) and
            option('--repo') == str(checkout) and option('--archive') == str(root / archive_name) and
            option('--action') == action and option('--output') == str(root / audit_name) and
            moment(matrix['finished']) < moment(guard['started']) <= moment(guard['finished']),
            label + ': detached raw-audit binding')
    required_denied = [root / n for n in ('clean-02', 'build-01', 'support-01', 'matrix-build-01', 'matrix-run-01',
                                         'c-build-01', 'c-run-01', 'fullcore-run-01', 'fullcore-audit-01')]
    require(all(str(path) in guard['denied_roots'] for path in required_denied), label + ': detached denied roots')
    if label != 'fullcore':
        require(option('--identity') == str(root / 'identity-02.json'), label + ': detached identity')
    if label == 'ordinary_c':
        require(option('--matrix') == str(root / 'matrix-archive-03'), 'detached C matrix anchor')
    detached[label] = dict(report_sha256=inputs[guard_name], auditor_output=guard['auditor_output'],
                           script_sha256=script_sha, launcher_sha256=guard['launcher_sha256'],
                           scope=guard['scope'])
comparison = read('reproduction-comparison.json')
require(comparison['status'] == 'T17_AUDITED_CROSS_BUILD_COMPARISON_COMPLETE' and
        comparison['candidate_manifest_sha256'] == inputs['matrix-archive-03/archive-manifest.json'] and
        comparison['candidate_audit_sha256'] == inputs['matrix-archive-audit-03.json'] and
        comparison['candidate_rows'] == matrix_proof['rows'] and comparison['new_emu_runs'] == 0,
        'derived comparison binding')
before, after = (read('performance-resource-' + label + '.json') for label in ('before', 'after'))
require(before['matching_processes'] == after['matching_processes'] == [] and
        before['performance_processes_serial'] is True and
        moment(before['observed_utc']) <= moment(matrix['started']) <= moment(matrix['finished']) <= moment(after['observed_utc']),
        'performance boundary process snapshot')

result = dict(status='T17_CLEAN_REPRODUCTION_PASS', contract='t17-clean-build-v1',
              scope='Same-host Agent clean-source rebuild and new-identity execution under CLEAN_CONTRACT.md; derived binding of completed independent audits.',
              created_utc=datetime.now(timezone.utc).isoformat(),
              summary_source_sha256=sha(Path(__file__).read_bytes()),
              identity_sha256=identity_sha, emu_sha256=emu_sha, reference_sha256=identity['reference_sha256'],
              source_commit=fc['source_commit'], new_execution_counts=dict(fullcore=14, ordinary_c=3, matrix=33,
              total=50, complete_normal=47, expected_negative=3), audit_new_emu_runs=0,
              fullcore=dict(unique_cases=117, case_executions=124, o2_coverage=fc_proof['suite_coverage']),
              ordinary_c=dict(public_functions=16, distinct_cases=48, normal_case_executions=96),
              performance=dict(formal_windows=384, all_window_replay_comparisons=192,
              scope='Fixed GEMV benchmark invocation endtoend windows', rows=matrix_proof['rows'],
              resource_snapshot_scope=before['scope']),
              archives={label: proof['archive'] for label, proof in
                        [('fullcore', fc_proof), ('matrix', matrix_proof), ('ordinary_c', c_proof)]},
              detached_raw_audits=detached, transport_contract='t17-portable-entry-v2',
              transport_source_sha256=matrix_outer_proof['transport_source_sha256'],
              input_sha256=inputs, human_ack=False, new_machine_installation_qualified=False,
              historical_runtime_pass_inherited=False, all_contest_requirements_accepted=False,
              publication_and_git_index_verification='separate required delivery checks')
args.output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
print(json.dumps({k: v for k, v in result.items() if k not in ('input_sha256', 'performance', 'fullcore')},
                 ensure_ascii=False, indent=2))
