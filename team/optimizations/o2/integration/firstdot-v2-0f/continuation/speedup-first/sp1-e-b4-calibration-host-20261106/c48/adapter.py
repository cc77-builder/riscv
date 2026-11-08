"""B4 C48 pure-host adapter. No target or native library is loaded or launched."""
from pathlib import Path
import hashlib, importlib.util, json, re
HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / 'CONTRACT.json').read_text())
CASE = CONTRACT['case']
CASE_ID = 'original-c8-c48'
ORIGINAL_CASE_ID = CASE['case_id']
SCOPES = ('HOST_FIXTURE', 'HISTORICAL_LOG', 'TARGET_LOG_REQUIRES_RUNTIME_RECEIPT')
FAKE_REFERENCE = '/FAKE_HOST_FIXTURE_NOT_A_LIBRARY'

def need(value, message):
    if not value:
        raise ValueError('B4_C48: ' + message)

def check_pin(pin):
    raw = Path(pin['path']).read_bytes()
    need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'frozen input changed ' + pin['path'])
    return raw

def load(name, pin):
    check_pin(pin)
    spec = importlib.util.spec_from_file_location(name, pin['path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

native = load('b4_frozen_c8_native', CONTRACT['native_adapter'])
group = load('b4_frozen_r7_negative_group', CONTRACT['negative_checker'])

# This module object is private to this leaf; the frozen R7 file is unchanged.
_r7_vector_destination = group.vector_destination

def c48_vector_destination(word):
    symbols, read = native.windows.elf_data(Path(CASE['artifacts']['elf']['path']))
    start, _ = symbols['config_reuse_gemv_8x32_reuse_vdot']
    stop = int(CASE['negative_binding']['pc'], 0)
    loads = {int.from_bytes(read(pc, 4), 'little') for pc in range(start, stop, 4)
             if int.from_bytes(read(pc, 4), 'little') & 0x7f == 0x07}
    need(len(loads) == 8 and {(w >> 7) & 31 for w in loads} == {16,17,18,19,24,25,26,27}, 'frozen eight C48 e8 load footprints')
    if word in loads:
        need(word >> 25 == 1 and (word >> 12) & 7 == 0 and (word >> 20) & 31 == 0, 'exact unmasked e8 unit-stride load')
        return (word >> 7) & 31
    return _r7_vector_destination(word)

group.vector_destination = c48_vector_destination

def descriptor():
    return dict(case_id=CASE_ID, kind='functional', bin=CASE['artifacts']['bin'],
                elf=CASE['artifacts']['elf'], manifest=CASE['artifacts']['manifest'],
                negative_reference=CASE['negative_reference'],
                normal_reference=CONTRACT['runtime']['normal_reference'], normal_ref=CONTRACT['runtime']['normal_reference'],
                negative_ref=CASE['negative_reference'], runtime={'bin':CASE['artifacts']['bin'], 'elf':CASE['artifacts']['elf'], 'normal_reference':CONTRACT['runtime']['normal_reference'], 'negative_reference':CASE['negative_reference']}, original_case_id=ORIGINAL_CASE_ID,
                bit100={k: int(v, 0) if isinstance(v, str) else v for k, v in CASE['negative_binding'].items()},
                negative_environment=CASE['negative_environment'], expected=CONTRACT['coverage'], coverage=CONTRACT['coverage'],
                guest_limits={'candidate-bit100':100000, 'normal':1500000}, wall_limits={'candidate-bit100':300, 'normal':2400}, budget_status='NEW_CALIBRATION_STOP_LIMIT_PROPOSAL_NOT_EXECUTION_AUTHORIZATION',
                guest_limits_source=CONTRACT['old_contract'],
                historical_complete_guest_cycles=871326,
                cwd={k: str(Path(CONTRACT['runtime'][k + '_emu']['path']).parent.parent) for k in ('candidate', 'baseline')},
                accepted_native_status={'normal': 'NORMAL_PASS', 'negative': 'C48_BIT100_LOG_PASS'}, normal_pass_status='NORMAL_PASS', negative_pass_status='C48_BIT100_LOG_PASS',
                comparison_fields=['accepted_sources_sha256', 'full128_packets_sha256', 'application_uart_sha256'],
                replay_extra_fields=['observer_events_sha256', 'guest_cycles'],
                absent_observations=['whole_ordinary_retirement', 'standalone_CSR_trace', 'performance_windows'],
                dependencies=json.loads((HERE / 'SOURCE_PINS.json').read_text())['files'], input_files=json.loads((HERE / 'SOURCE_PINS.json').read_text())['files'])

def header(text, case_id, mode, reference, exit_code, run_id, scope, negative):
    need(case_id == CASE_ID and mode in ('candidate', 'baseline'), 'exact case and hardware mode')
    need(scope in SCOPES and isinstance(run_id, str) and bool(run_id), 'supported explicit scope/run id')
    need(type(exit_code) is int and exit_code == (1 if negative else 0), 'exact role exit code')
    need(isinstance(reference, str) and isinstance(text, str), 'reference/text API types')
    plain = native.failure.normalize_console(text)
    need(plain.count('The first instruction of core 0 has commited. Difftest enabled.') == 1, 'exact live DiffTest marker')
    need(re.findall(r'The reference model is ([^\r\n]+)', plain) == [reference], 'exact reference banner')
    need(('O2_' not in plain) if mode == 'candidate' else ('SP1_' not in plain), 'hardware observer schema')
    need(not re.search(r'CRITICAL\s+ERROR|double\s+trap|PMA\s+check\s+failed|R4C_FAIL', plain, re.I), 'fatal diagnostic')
    if scope == 'HOST_FIXTURE':
        need(reference == FAKE_REFERENCE, 'explicit synthetic reference, never a library')
        image = CASE['artifacts']['bin']['path']
        context = 'SYNTHETIC_HOST_ONLY'
    elif scope == 'HISTORICAL_LOG':
        need(mode == 'baseline' and any(x['negative'] == negative and x['normal_reference_path'] == reference for x in CASE['history_budget_facts']), 'known historical runtime only')
        image = CONTRACT['historical_image']
        context = 'HISTORICAL_CONTEXT'
    else:
        expected = CASE['negative_reference'] if negative else CONTRACT['runtime']['normal_reference']
        check_pin(expected)
        need(reference == expected['path'], 'frozen current reference')
        need(not negative or mode == 'candidate', 'current negative uses candidate')
        image = CASE['artifacts']['bin']['path']
        context = 'CURRENT_CONTEXT'
    need(re.findall(r'The image is ([^\r\n]+)', plain) == [image], 'exact context image banner')
    guests = re.findall(r'Guest cycle spent:\s*(\d+)', plain)
    need(len(guests) == 1 and int(guests[0]) > 0, 'one complete positive guest count')
    return plain, context, int(guests[0])

def committed_elf(events):
    _, read = native.windows.elf_data(Path(CASE['artifacts']['elf']['path']))
    sources, packets = native.committed_vectors(events)
    for row in sources:
        need(int.from_bytes(read(row['pc'], 4), 'little') == row['word'], 'committed custom PC/word frozen ELF binding')
    return sources, packets

def collect(text, case_id, mode, reference, exit_code, run_id, scope='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT'):
    plain, context, guest = header(text, case_id, mode, reference, exit_code, run_id, scope, False)
    result = native.log_gate(CASE, '', plain, exit_code, reference, mode, context=context)
    observer = native.sp1 if mode == 'candidate' else native.o2
    events, _ = observer.extract_events_and_uart(plain)
    sources, packets = committed_elf(events)
    need(len(sources) == len(packets) == 1008 and result['calls'] == 48, 'full C48 coverage')
    result.update(case_id=CASE_ID, original_case_id=ORIGINAL_CASE_ID, scope=scope, run_id=run_id, guest_cycles=guest,
                  raw_sha256=hashlib.sha256(text.encode()).hexdigest(), target_run_qualified=False,
                  requires_runtime_receipt=True, ordinary_retirement_trace_observed=False,
                  independent_csr_trace_observed=False, performance_measured=False,
                  csr_evidence='frozen judge reads VL8/VTYPE0/VSTART0/VCSR7; execution+DiffTest required',
                  abi_evidence='frozen linked leaf static ABI and actual ordinary C path; no all-register dynamic sentinels')
    return result

def negative(text, case_id, mode, reference, exit_code, run_id, scope='TARGET_LOG_REQUIRES_RUNTIME_RECEIPT'):
    plain, context, guest = header(text, case_id, mode, reference, exit_code, run_id, scope, True)
    native.validate_static(CASE)
    observer = native.sp1 if mode == 'candidate' else native.o2
    observation = observer.analyze(plain, require_complete=False)
    events, uart = observer.extract_events_and_uart(plain)
    _, read = native.windows.elf_data(Path(CASE['artifacts']['elf']['path']))
    binding = {k: int(v, 0) if isinstance(v, str) else v for k, v in CASE['negative_binding'].items()}
    fault = group.validate_negative_group(plain, exit_code, binding, read, events)
    sources, _ = committed_elf(events)
    need(sources and sources[0]['pc'] == binding['pc'] and sources[0]['word'] == binding['word'], 'first actual custom injection')
    need(not re.search(r'R4C_END|R4C_CASE|R4C_CONTROLS', uart), 'reject before first successful ordinary call')
    return dict(status='C48_BIT100_LOG_PASS', case_id=CASE_ID, mode=mode, scope=scope,
                run_id=run_id, guest_cycles=guest, fault=fault, observation=observation,
                raw_sha256=hashlib.sha256(text.encode()).hexdigest(), target_run_qualified=False,
                requires_runtime_receipt=True, performance_measured=False,
                qualification='strict offline full128 current-group binding; real execution receipt mandatory')

def compare(left, right, replay=False):
    required = ('case_id', 'bin_sha256', 'manifest_sha256', 'custom_commits',
                'accepted_sources_sha256', 'full128_packets_sha256', 'application_uart_sha256')
    for row in (left, right):
        need(row.get('status') == 'NORMAL_PASS' and row.get('case_id') == CASE_ID, 'complete known functional result')
        need(row.get('calls') == 48 and row.get('custom_commits') == 1008, 'complete comparison coverage')
        need(row.get('bin_sha256') == CASE['artifacts']['bin']['sha256'] and row.get('manifest_sha256') == CASE['artifacts']['manifest']['sha256'], 'comparison frozen image identity')
        need(type(row.get('guest_cycles')) is int and row['guest_cycles'] > 0, 'comparison observed guest count')
        for key in required:
            need(key in row and row[key] is not None, 'missing actual comparison field ' + key)
    need(left['mode'] == right['mode'] if replay else (left['mode'], right['mode']) == ('baseline', 'candidate'), 'comparison hardware modes')
    for key in required:
        need(left[key] == right[key], 'architecture comparison ' + key)
    if replay:
        for key in ('observer_events_sha256', 'guest_cycles'):
            need(key in left and key in right and left[key] is not None and left[key] == right[key], 'exact observed replay ' + key)
    return dict(status='FUNCTIONAL_PAIR_PASS', replay=replay, performance_measured=False,
                target_run_qualified=False, requires_distinct_runtime_process_receipts=replay,
                ordinary_retirement_trace_observed=False, independent_csr_trace_observed=False)
