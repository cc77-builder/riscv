"""Bind the new target to screened code/data and audit its complete timed paths.

The mature counter, fatal-output and O2 protocol parsers stay unmodified. This
adapter supplies the three actual linked paths and the new bounded call plan.
"""
from pathlib import Path
import argparse
import json
import re
import struct
import sys
import tempfile

import generate
import screen
import target

need, sha, save = generate.need, target.sha, target.save
START, STOP = 0x51300013, 0x51400013
COUNTERS = (0xc0202773, 0xc0002873, 0xc00028f3, 0xc02027f3)
QGEN_PIN = 'e2862fb802754c473a0c9cb8a949b30ed55eaee647aae9ef7e1d566168122987'
SCREEN_ELF_PIN = '8316e32939385653c1c4f7e257443529c19dc71df8b5991552a2ab1453069daa'
TIMER_REFERENCE_PIN = '610c499f46f1fe73074f626d8990bdcbdbc5f78c30ce8fc4a835495b0e392faa'
HELPER_PINS = {
    'team/optimizations/o1/audit/runtime_gate.py':'80315b278f4dc0168edd33657a07ae648b20f0279fa57a69f35b0f983fa42ea1',
    'team/optimizations/o2/fullcore/recheck.py':'8cebe76129f86747cdddf87f93f54d4379a8606dd3c1a20d55008361f2f95140',
    'team/optimizations/o2/fullcore/analyze.py':'27d9fe451c035157848625e84c2a229ac1d83073eb56ba3ebc25131e5569d496',
    'team/workloads/unified-vdot/check.py':'084bebc22e2f4665e5c7a7797e5cd2a6c73220719b4cf228ce3075ae2446bc66',
}


def read(path):
    return json.loads(path.read_text())


def helper(repo, relative):
    return screen.load('gs32_' + Path(relative).stem, repo/relative, HELPER_PINS[relative])


def support(repo):
    model, helpers = screen.support(repo)
    qgen = screen.load('gs32_q_fixture', repo/generate.REL.parent/'generate.py', QGEN_PIN)
    phased_candidate = screen.load('gs32_phased_candidate', repo/generate.REL/'phased/candidate.py',
                                   target.BASE_PINS['phased/candidate.py'])
    previous = sys.modules.get('candidate')
    sys.modules['candidate'] = phased_candidate
    try:
        phased = screen.load('gs32_phased_checker', repo/generate.REL/'phased/screen.py',
                            '8537f85027ccc9164229c10a400a7d996d42c6711d30dc869835e5eb71a88fd9')
    finally:
        if previous is None:
            sys.modules.pop('candidate', None)
        else:
            sys.modules['candidate'] = previous
    candidate, baseline = screen.machine_class(repo, model)
    tail = phased.checker_class(model, repo/'team/optimizations/o2/r2-safe-tail/machine_model.py')
    return model, qgen, (candidate, tail, baseline)


def arrays(elf, manifest, qgen):
    fixture = qgen.fixtures()
    guard = struct.pack('<2Q', 0xd15ea5e5cafebabe, 0xd15ea5e5cafebabe)
    pack = lambda values, code: struct.pack('<'+str(len(values))+code, *values)
    wanted = {
        'q_weights':qgen.bytes8(fixture['weight']),
        'q_weight_scale':qgen.bytes32(fixture['weight_scale']),
        'q_inputs':b''.join(qgen.bytes8(v) for v in fixture['inputs']),
        'q_input_scale':b''.join(qgen.bytes32(v) for v in fixture['input_scale']),
        'q_golden':b''.join(qgen.bytes32(v) for v in fixture['golden']),
        'q_packed':guard+qgen.bytes8(fixture['packed'])+guard,
        'q_order':pack(target.ORDER, 'I'), 'q_methods':pack(target.METHODS, 'I'),
        'q_functional_order':pack((0,1,2,0,1,2), 'I'),
        'q_functional_datasets':pack((1,1,1,2,2,2), 'I'),
        'q_wrappers':pack([elf.symbols[n][0] for n in target.WRAPPERS], 'Q'),
        'split_entries':pack([elf.symbols[n][0] for n in qgen.NEW], 'Q'),
        'q_fault_probe':pack(qgen.PROBE_WORDS, 'I'),
    }
    for name, raw in wanted.items():
        need(elf.symbol_data(name) == raw, 'compiled array: '+name)
    calls = [dict(stage=0,arm=a,dataset=d) for a,d in zip((0,1,2,0,1,2),(1,1,1,2,2,2))]
    for arm in target.ORDER:
        calls.extend((dict(stage=1,arm=arm,dataset=0), dict(stage=2,arm=arm,dataset=0)))
    need(manifest['contract'] == target.CONTRACT and manifest['call_plan'] == calls,
         'exact new contract and 22-call plan')
    need(tuple(s['index'] for s in manifest['plan']) == target.ORDER,
         'all eight balanced windows, including four FR anchors')
    need(manifest['full_q_calls'] == 22 and manifest['expected_dots'] == 62209,
         'bounded complete-call/custom counts')
    for arm, row in enumerate(manifest['rows']):
        need(row['id'] == arm and row['wrapper'] == target.WRAPPERS[arm]
             and row['algorithm'] == target.METHODS[arm]
             and row['leaf'] == qgen.NEW[target.METHODS[arm]]
             and row['method'] == ('vdot' if arm == 1 else 'rvv')
             and row['dots'] == (10368 if arm == 1 else 0), 'exact arm metadata')
    return {n:sha(v) for n,v in wanted.items()}


def binary(elf):
    # This fixed AM image has one flat RAM LOAD segment; objcopy includes .bss.
    raw = elf.raw
    need(struct.unpack_from('<H', raw, 16)[0] == 2, 'linked executable ELF')
    phoff = struct.unpack_from('<Q', raw, 32)[0]
    size, count = struct.unpack_from('<HH', raw, 54)
    loads = [struct.unpack_from('<IIQQQQQQ', raw, phoff+i*size) for i in range(count)]
    loads = [p for p in loads if p[0] == 1]
    need(len(loads) == 1, 'single flat AM RAM LOAD')
    _, flags, offset, address, physical, filesz, memsz, _ = loads[0]
    need(flags & 1 and address == physical == 0x80000000
         and struct.unpack_from('<Q', raw, 24)[0] == address
         and 0 < filesz <= memsz < 128*1024*1024, 'AM executable entry and RAM bounds')
    return raw[offset:offset+filesz] + bytes(memsz-filesz)


def paths(repo, elf, manifest, qgen, classes):
    fixture = qgen.fixtures()
    body = elf.symbol_data('split_measure')
    begin = elf.symbols['split_measure'][0]
    timer = [(begin+4*i,w) for i,(w,) in enumerate(struct.iter_unpack('<I',body))]
    need([i for i,(_,w) in enumerate(timer) if w == START] == [11]
         and [i for i,(_,w) in enumerate(timer) if w == STOP] == [26]
         and timer[20][1] == 0x000a00e7, 'unchanged timer marker/call sites')
    streams, details = {}, {}
    addr = lambda name: elf.symbols[name][0]
    for arm, row in enumerate(manifest['rows']):
        for dataset in range(3):
            m = classes[arm](fixture, dataset, poison=0x3232288)
            m.addresses = dict(packed=addr('q_packed')+16, x=addr('q_inputs')+288*dataset,
                ws=addr('q_weight_scale'), xs=addr('q_input_scale')+36*dataset,
                y=addr('q_output')+16, slots=addr('q_slots')+16, context=addr('q_context'))
            m.regions['context'] = bytearray(struct.pack('<7Q',
                *(m.addresses[n] for n in ('packed','x','ws','xs','y','slots')), addr(row['leaf'])))
            m.original['context'] = bytes(m.regions['context'])
            m.halt = timer[21][0]
            m.x[1], m.x[2] = m.halt, 0x87fff000-48
            m.x[8] = m.x[10] = addr('q_context')
            m.x[9], m.x[20] = addr('q_measurement'), addr(row['wrapper'])
            m.saved = {i:m.x[i] for i in m.saved}
            m.execute_function(elf, row['wrapper'])
            check = (lambda:m.check_candidate(fixture['golden'][dataset])) if arm == 0 else (
                    lambda:m.check(fixture['golden'][dataset])) if arm == 1 else (
                    lambda:m.check_full('rvv4',fixture['golden'][dataset]))
            detail = check()
            stream = timer[11:21] + m.path + timer[21:27]
            need(len(stream) == len(m.path)+16, 'common complete timer overhead')
            positions = [i for i,(_,w) in enumerate(stream) if w in COUNTERS]
            need([stream[i][1] for i in positions] == list(COUNTERS), 'four counter sites in order')
            if arm in streams:
                need(streams[arm] == stream, 'dataset-independent exact PC/word path')
            else:
                streams[arm] = stream
            details[str(arm)+':'+str(dataset)] = dict(detail, dataset=dataset,
                function_instructions=len(m.path), marker_instructions=len(stream),
                expected_csr_instret=positions[3]-positions[0],
                path_sha256=sha(b''.join(struct.pack('<QI',pc,w) for pc,w in stream)),
                actual_elf_addresses=True)
    return streams, details


def verify(repo, build, screened_elf, numeric_result, timer_reference):
    record = read(build/'build.json')
    model, qgen, classes = support(repo)
    elf = model.ELF((build/'gs32-target.elf').read_bytes())
    need(record['elf_sha256'] == sha(elf.raw) and
         record['bin_sha256'] == sha((build/'gs32-target.bin').read_bytes()), 'recorded build bytes')
    need(binary(elf) == (build/'gs32-target.bin').read_bytes(), 'complete ELF/BIN correspondence')
    for path, pin in record['immutable_am_inputs'].items():
        need(sha(Path(path).read_bytes()) == pin, 'immutable AM input '+path)
    producer_files = {}
    for path,pin in read(build/'source/producer-inputs.json').items():
        source = Path(path)
        relative = source.relative_to(repo).as_posix()
        # The unchanged parent INPUT_PINS hashes decoded gzip payloads. Its
        # raw() function is the authority for that explicitly named subset;
        # ordinary imported source entries describe physical file bytes.
        payload = qgen.raw(repo,relative) if relative in qgen.INPUT_PINS else source.read_bytes()
        if relative in qgen.INPUT_PINS:
            need(pin == qgen.INPUT_PINS[relative], 'unchanged parent payload pin '+relative)
        need(sha(payload) == pin, 'frozen producer input '+path)
        producer_files[relative] = dict(physical_sha256=sha(source.read_bytes()),payload_sha256=pin)
    result = read(numeric_result)
    need(sha(screened_elf.read_bytes()) == SCREEN_ELF_PIN == result['elf_sha256']
         and result['status'] == 'GS32_ACTUAL_ELF_NUMERIC_PASS'
         and len(result['numeric']['cases']) == 8 and len(result['controls']) == 6,
         'v2 screened ELF and bounded result identity')
    reference = model.ELF(screened_elf.read_bytes())
    need(elf.symbol_data(generate.NAME) == reference.symbol_data(generate.NAME),
         'complete new body equals screened actual ELF')
    bodies = {generate.NAME:sha(elf.symbol_data(generate.NAME))}
    for name,pin in target.FUNCTION_PINS.items():
        need(sha(elf.symbol_data(name)) == pin, 'unchanged qualified body '+name)
        bodies[name] = pin
    need(sha(timer_reference.read_bytes()) == TIMER_REFERENCE_PIN, 'previous fixed timer ELF')
    timer_elf = model.ELF(timer_reference.read_bytes())
    need(elf.symbol_data('split_measure') == timer_elf.symbol_data('split_measure'), 'unchanged entire timer')
    bodies['split_measure'] = sha(elf.symbol_data('split_measure'))
    with tempfile.TemporaryDirectory(prefix='gs32-target-verify-') as temporary:
        fresh = Path(temporary)/'source'
        target.produce(repo, fresh)
        for path in fresh.iterdir():
            # This inventory also records the invoking Python modules; it is
            # verified above, not treated as generated executable source.
            if path.name == 'producer-inputs.json':
                continue
            need(path.read_bytes() == (build/'source'/path.name).read_bytes(), 'source regeneration '+path.name)
    manifest = read(build/'source/manifest.json')
    bound_arrays = arrays(elf, manifest, qgen)
    streams, details = paths(repo, elf, manifest, qgen, classes)
    controls = []
    for name in ('q_wrappers','q_order','q_golden','q_packed'):
        raw = bytearray(elf.raw)
        offset = elf.symbols[name][2]+(16 if name == 'q_packed' else 0)
        raw[offset] ^= 1
        try:
            arrays(model.ELF(raw), manifest, qgen)
        except ValueError as error:
            need(str(error) == 'compiled array: '+name, 'specific bound-array rejection')
            controls.append(dict(name=name,offset=offset,error=str(error),mutant_sha256=sha(raw)))
        else:
            raise ValueError('target array mutation accepted: '+name)
    return dict(status='GS32_TARGET_ELF_DATASET_TIMER_PATH_PASS', contract=target.CONTRACT,
        elf_sha256=sha(elf.raw),bin_sha256=sha(binary(elf)), function_sha256=bodies,
        compiled_array_sha256=bound_arrays,paths=details,array_controls=controls,
        producer_files=producer_files,producer_inventory_sha256=sha((build/'source/producer-inputs.json').read_bytes()),
        screened_elf_sha256=SCREEN_ELF_PIN,numeric_result_sha256=sha(numeric_result.read_bytes()),
        windows=8,full_q_calls=22,target_runtime_qualified=False,performance_qualified=False)


def selection(samples, manifest):
    methods = []
    for arm,row in enumerate(manifest['rows']):
        observations = [s for s in samples if s['id'] == arm]
        need(len(observations) == (4 if arm == 2 else 2)
             and all(s['cycles'] > 0 for s in observations), 'all method observations retained')
        cycles = [s['cycles'] for s in observations]
        methods.append(dict(id=arm,wrapper=row['wrapper'],cycles=cycles,
            instructions=[s['instructions'] for s in observations],mean_cycles=sum(cycles)/len(cycles)))
    anchors = methods[2]['cycles']
    context = 100*max(anchors) <= 101*min(anchors)
    comparisons = []
    for baseline in (1,2):
        candidate, before = methods[0]['cycles'], methods[baseline]['cycles']
        gate = 200*max(candidate) <= 199*min(before)
        comparisons.append(dict(candidate=0,baseline=baseline,worst_candidate=max(candidate),
            best_baseline=min(before),reduction=1-max(candidate)/min(before),
            separation_gate=gate,qualified=context and gate))
    promote = context and all(c['qualified'] for c in comparisons)
    return dict(decision='HOLD_CONTEXT_VARIATION' if not context else
                'GS32_PREFERRED_IN_FIXED_PLAN' if promote else 'KEEP_EXISTING_ENTRY',
        methods=methods,anchors=anchors,anchor_gate=context,comparisons=comparisons,
        candidate_qualified=promote,stable_default_changed=False,hardware_changed=False,
        statistical_scope='two reversed GS32/TA observations, all four FR anchors; replay is not an extra sample',
        application_scope='synthetic prepacked complete Q288 with same-method selfwarm; no token or full-model claim')


def analyze(repo, build, run, receipt):
    need(receipt['process_started'] and receipt['exit_code'] == 0 and not receipt['timed_out'], 'complete target run')
    stdout,stderr = ((run/n).read_text() for n in ('stdout.log','stderr.log'))
    gate = helper(repo, 'team/optimizations/o1/audit/runtime_gate.py')
    fatal = helper(repo, 'team/optimizations/o2/fullcore/recheck.py')
    observer = helper(repo, 'team/optimizations/o2/fullcore/analyze.py')
    for text in (stdout,stderr):
        gate.validate_failure_markers(text)
        fatal.reject_fatal_output(text)
    _,uart = observer.extract_events_and_uart(stderr+stdout)
    gate.validate_failure_markers(uart)
    fatal.reject_fatal_output(uart)
    plain = gate.normalize_console(uart)
    model,qgen,classes = support(repo)
    elf = model.ELF((build/'gs32-target.elf').read_bytes())
    manifest = read(build/'source/manifest.json')
    arrays(elf,manifest,qgen)
    streams,details = paths(repo,elf,manifest,qgen,classes)
    counter = helper(repo, 'team/workloads/unified-vdot/check.py')
    counter.walk = lambda path:path  # already expanded exact actual-ELF paths
    events = counter.parse_events(stderr)
    samples = counter.trace_windows(events,manifest,streams)
    windows,current = [],None
    for event in events['RETIRE']:
        if event['word'] == START:
            current = []
        if current is not None:
            current.append(event)
        if event['word'] == STOP:
            windows.append(current)
            current = None
    need(current is None and len(windows) == len(samples) == 8, 'eight complete measured windows')
    for records,step,sample in zip(windows,manifest['plan'],samples):
        stream,pos = streams[step['index']],0
        for event in records:
            covered = stream[pos:pos+event['count']]
            if event['count'] > 1:
                need(not any(w & 127 in (0x63,0x6f,0x67) for _,w in covered), 'no hidden compressed control flow')
            pos += event['count']
        need(pos == len(stream), 'complete exact marker path')
        sample.update({k:step[k] for k in ('dataset','block','role')})
        need(sample['instructions'] == details[str(step['index'])+':0']['expected_csr_instret'],
             'CSR/event/ELF complete instruction count')
    expected = [f'Q_BEGIN contract={target.CONTRACT} windows=8',
                'Q_FUNCTIONAL calls=22 controls=5 outputs=6336 warm=8 extra=6']
    expected += [f"Q_CALL {i} {c['stage']} {c['arm']} {c['dataset']}" for i,c in enumerate(manifest['call_plan'])]
    expected += [f"QW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['Q_END windows=8 full_calls=22 leaf_calls=0 inline_calls=22 probe_dots=1 failures=0']
    need([line for line in plain.splitlines() if line.startswith(('Q_','QW '))] == expected
         and plain.count('HIT GOOD TRAP') == 1, 'complete UART/call/oracle/guard/CSR evidence')
    protocol = observer.analyze(stderr+stdout)
    need(protocol['status'] == 'O2_TRACE_PASS' and protocol['schema']['slots'] == 2
         and all(protocol.get(k) == 0 for k in ('pending_count','pending_div_count','unfinished_rob_count'))
         and protocol['counts'].get('COMMIT') == 62209, 'complete custom protocol and count')
    expected_pcs = [elf.symbols['q_fault_probe'][0]+20]
    for call in manifest['call_plan']:
        expected_pcs += [pc for pc,w in streams[call['arm']] if w & 0xfe00707f == 0x0200000b]
    actual_pcs = [int(v,16) for v in re.findall(r'^O2_COMMIT [^\n]*pc=0x([0-9a-fA-F]+)',stderr,re.M)]
    need(actual_pcs == expected_pcs and len(actual_pcs) == 62209, 'entire functional/warm/timed custom PC sequence')
    return dict(status='GS32_TARGET_DIFFTEST_COUNTER_PATH_PASS',contract=target.CONTRACT,
        windows=8,full_q_calls=22,judge_fault_controls=5,outputs_checked=6336,
        committed_vdot=62209,all_stage_custom_pc_sha256=sha(b''.join(struct.pack('<Q',pc) for pc in actual_pcs)),
        samples=samples,selection=selection(samples,manifest),protocol=protocol,
        runtime_qualified=True,full_application_performance_qualified=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--screened-elf', type=Path, required=True)
    p.add_argument('--numeric-result', type=Path, required=True)
    p.add_argument('--timer-reference', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    sys.dont_write_bytecode = True
    need(not a.output.exists(), 'fresh verification report')
    result = verify(a.repo.resolve(),a.build.resolve(),a.screened_elf.resolve(),
                    a.numeric_result.resolve(),a.timer_reference.resolve())
    save(a.output,result)
    print(json.dumps(dict(status=result['status'],elf_sha256=result['elf_sha256'],
        instructions={key:value['expected_csr_instret'] for key,value in result['paths'].items()})))


if __name__ == '__main__':
    main()
