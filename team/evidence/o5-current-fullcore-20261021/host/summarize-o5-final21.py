"""Produce a readable derivative of the completed, separately bound G3 audit."""
from pathlib import Path
import hashlib,json
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
audit=base/'runs/recheck-03'
result=json.loads((audit/'result.json').read_text())
if result['status'] not in ('O2_G3_OFFLINE_RECHECK_PASS','O2_G3_OFFLINE_RECHECK_INCOMPLETE') or result.get('error'):
    raise ValueError('audit failed unexpectedly')
if not (result['core_regression_pass'] and result['supplements_pass'] and result['original_evidence_unchanged']):
    raise ValueError('audit inputs or jobs failed')
core=result['runs']; supplemental=result['supplement_audit']['runs']
rows=core+supplemental
attempts=[json.loads((base/'runs'/name/'result.json').read_text()) for name in ('core-01','supplements-01','supplements-02')]
actual_launches=sum(len(attempt['runs']) for attempt in attempts)
normal=[r for r in rows if r['name']!='negative-vdot']
matrix=[json.loads((audit/f'functional-{i}/functional-result.json').read_text()) for i in range(8)]
summary=dict(status=result['status'],source=str(audit/'result.json'),
    source_sha256=hashlib.sha256((audit/'result.json').read_bytes()).hexdigest(),
    build_source_commit=result['build_source_commit'],runtime_gate_audit=result['runtime_gate_audit'],
    emu_sha256=result['emu_sha256'],selected_jobs=len(rows),actual_launches=actual_launches,normal_jobs=len(normal),
    g3_complete=result['g3_complete'],
    matrix_executed=sum(r['executed'] for r in matrix),
    normal_vdot_commits=sum(r['observation_counts']['COMMIT'] for r in normal),
    normal_reference_recovery=result['normal_reference_recovery'],
    original_evidence_unchanged=result['original_evidence_unchanged'],
    coverage=result['suite_coverage'],
    verdicts=[dict(name=r['name'],status=r['status'],exit_code=r['exit_code'],
                  original_status=r.get('original_status'),
                  commits=r.get('observation_counts',{}).get('COMMIT')) for r in rows],
    scope='Derivative summary only; no additional emulator execution or performance measurement')
with (base/'current-g3-summary.json').open('x') as stream:json.dump(summary,stream,indent=2)
print(json.dumps(summary,indent=2),flush=True)
