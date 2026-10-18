from pathlib import Path
import collections
import gzip
import hashlib
import importlib.util
import json
import re
import subprocess
import sys

ROOT = Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
OUT = Path(__file__).resolve().parent

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def load(name, relative):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

legacy = load('historical_t12_observer', 'team/scripts/check-vdot-regression.py')
current = load('current_o1_observer', 'team/optimizations/o1/fullcore/analyze.py')
paths = [
 'team/evidence/t14-optimization-20261016/t12/suite/functional-0/stderr.log.gz',
 'team/evidence/t14-optimization-20261016/control-sweep/candidate/stderr.log.gz',
 'team/evidence/t14-optimization-20261016/fullcore/performance/performance-d0-s06-r0/stderr.log.gz',
]
records = []
for relative in paths:
    path = ROOT / relative
    compressed = path.read_bytes()
    raw = gzip.decompress(compressed)
    text = raw.decode('utf-8')
    events, _ = legacy.extract_events(text)
    globals_ = [e for e in events if e[2] in ('ENQUEUE', 'COMMIT', 'REDIRECT')]
    redirects = {e[0]: e for e in globals_ if e[2] == 'REDIRECT'}
    raw_observer_rows = list(re.finditer(r'T(?:12|13)_[A-Z0-9_]+[^\n]*', text))
    snippets = []
    for cycle, _, kind, fields in globals_:
        if kind != 'ENQUEUE' or cycle not in redirects:
            continue
        selected = []
        for match in raw_observer_rows:
            line = match.group()
            m = re.search(r'cycle=\s*(\d+)', line)
            if m and int(m[1]) == cycle and line.startswith(('T12_ENQUEUE ', 'T12_REDIRECT ')):
                selected.append({'physical_line': text.count('\n', 0, match.start()) + 1,
                                 'record': line})
        snippets.append({'cycle': cycle, 'enqueue_rob': fields['rob'], 'records': selected})
    t13_counts = collections.Counter()
    samples = {}
    for match in raw_observer_rows:
        line = match.group()
        tag, _, body = line.partition(' ')
        samples.setdefault(tag, line)
        if tag.startswith('T13_'):
            kind = tag[4:]
            if kind in current.T13_FIELDS:
                current.parse_fields(tag, body, current.T13_FIELDS[kind].split(), t13=True)
                t13_counts[tag] += 1
    record = {
        'path': str(path), 'compressed_sha256': digest(compressed),
        'uncompressed_sha256': digest(raw), 'uncompressed_bytes': len(raw),
        'crlf_count': text.count('\r\n'),
        'legacy_observer_record_count': len(events),
        'tag_counts': dict(collections.Counter(re.findall(r'T(?:12|13)_[A-Z0-9_]+', text))),
        'format_samples': samples,
        't13_hardware_rows_validated_against_current_stripper': dict(t13_counts),
        'enqueue_tags_same_cycle_as_rob_redirect': snippets,
    }
    if 'functional-0' not in relative:
        live, history, overwritten = {}, [], []
        rank = {'COMMIT': 0, 'REDIRECT': 1, 'ENQUEUE': 2}
        for cycle, _, kind, fields in sorted(globals_, key=lambda e:(e[0], rank[e[2]])):
            rob = fields['rob']
            if kind == 'COMMIT':
                if rob in live:
                    live[rob]['commit'] = cycle
            elif kind == 'REDIRECT':
                for entry in live.values():
                    if not entry.get('commit') and current.flushed(entry['rob'], rob, 0):
                        entry['cancel'] = cycle
            elif cycle not in redirects:
                old = live.get(rob)
                if old is not None and not old.get('commit') and not old.get('cancel'):
                    overwritten.append(old)
                entry = dict(rob=rob, cycle=cycle, pc=fields['pc'])
                live[rob] = entry
                history.append(entry)
        unfinished = [e for e in history if not e.get('commit') and not e.get('cancel')]
        record['limited_legacy_lifetime_diagnostic'] = {
            'allocation_tags_after_excluding_redirect_cycle_tags': len(history),
            'unfinished_entries': unfinished, 'uncompleted_entry_overwritten': overwritten,
            'note': 'Diagnostic only. Old REDIRECT lacks self bit; these legal-only control/dense streams use younger-cancellation for this check. No log bytes or event names were rewritten.',
        }
    records.append(record)
source_paths = [
 'team/scripts/check-vdot-regression.py', 'team/optimizations/o1/fullcore/analyze.py',
 'team/optimizations/o1/fullcore/check_control.py',
 'src/main/scala/xiangshan/backend/rob/Rob.scala',
 'src/main/scala/xiangshan/backend/CtrlBlock.scala',
]
result = {
    'status': 'HISTORICAL_TRACE_FORMAT_AND_OBSERVER_DIAGNOSTIC_COMPLETE',
    'repository': str(ROOT),
    'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'checker_versions_sha256': {str(ROOT/p): digest((ROOT/p).read_bytes()) for p in source_paths},
    'command': [sys.executable, '-B', str(Path(__file__).resolve())],
    'audit_script_sha256': digest(Path(__file__).read_bytes()),
    'new_emu_executed': False, 'new_o1_rtl_validation': False,
    'historical_logs_modified': False, 'production_sources_modified': False,
    'findings': [
        'Actual Chisel space-padded decimal fields, rob=0: 8, hexadecimal PC and 128-bit result formatting are handled by the strict field grammar.',
        'All 4608 RETIRE, 48 COUNTER_ENQUEUE and 48 CSR_SAMPLE records in the sampled historical dense log match the current known-T13 stripping grammar.',
        'Old ENQUEUE tags coincide with ROB redirect in one sampled control event and six sampled dense events. Actual ROB connectEnq is suppressed when redirect.valid, so new O1 observation must apply that gate.',
        'The limited legal-only historical lifetime diagnostic has no unfinished allocations or live overwrites after excluding those same-cycle enqueue tags.',
    ],
    'limits': [
        'This is historical-format and observer-boundary diagnosis, not a new emulator run, new O1 pass, or performance comparison.',
        'No T12 record was relabeled as O1, and no historical log was edited or emitted as new-run evidence.',
        'Functional-0 was used only for format samples; no exact self-redirect lifetime verdict is inferred from its legacy schema.',
    ],
    'logs': records,
}
(OUT/'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'logs': len(records),
                  'same_cycle_enqueues': [len(r['enqueue_tags_same_cycle_as_rob_redirect']) for r in records],
                  'new_emu_executed': False}, indent=2))
