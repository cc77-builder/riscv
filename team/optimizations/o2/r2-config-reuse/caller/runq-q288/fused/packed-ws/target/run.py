"""Packed-scale target adapter over the unchanged build/runtime/audit engines."""
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import argparse
import importlib.util
import json
import os
import re
import shlex
import struct

HERE = Path(__file__).resolve().parent
Q = HERE.parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
tail = load('ws_target_frozen_tail_run', Q/'fused/phased/tail/target/run.py')
gen = load('ws_target_generator', HERE/'generate.py')
proof = load('ws_target_word_equivalence', HERE.parent/'verify.py')
fused = tail.previous
ROOT, g, parent, old, base = tail.ROOT, tail.g, tail.parent, tail.old, tail.base
PARENT_DIR = tail.PARENT_DIR
read, now, digest, adapt = tail.read, tail.now, tail.digest, tail.adapt
fixture_gen = gen.parent
CONTRACT, MAX_CYCLES, GENERATED = gen.CONTRACT, gen.MAX_CYCLES, gen.FILES
OWN = ('main.c', 'generate.py', 'run.py', 'archive.py', 'CONTRACT.md')
STATIC = ('q288_ws.h', 'pack.c', 'generate.py', 'verify.py', 'screen.py', 'CONTRACT.md')


def sources(repo):
    found = tail.sources(repo)
    paths = [HERE/n for n in OWN] + [HERE.parent/n for n in STATIC]
    found.update({p.relative_to(repo).as_posix(): g.sha(p) for p in paths})
    return found


def generate(repo, out):
    return gen.generate(repo, out)


def path(elf, row, fixture, dataset=0):
    """Actual path with a proven layout normalization for new load semantics.

    The old numeric interpreter never sees a new opcode. For a packed entry,
    first certify its exact three-word relation to the qualified baseline;
    execute that baseline at the new entry/context addresses with a real 48B
    object and the original logical scale values; then substitute the actual
    candidate words at the identical PC offsets. The independent address proof
    establishes the value correspondence. Actual NEMU/EMU remains mandatory.
    """
    timer_body = elf.symbol_data('split_measure')
    g.require(timer_body == base.reference_images()[1].symbol_data('split_measure'), 'complete common timer body')
    begin = elf.symbols['split_measure'][0]
    timer = [(begin+4*i, w) for i,(w,) in enumerate(struct.iter_unpack('<I',timer_body))]
    starts = [i for i,(_,w) in enumerate(timer) if w == base.base.traced.START]
    stops = [i for i,(_,w) in enumerate(timer) if w == base.base.traced.STOP]
    g.require(starts == [11] and stops == [26] and timer[20][1] == 0x000a00e7, 'fixed marker/call/return interval')
    name = row['wrapper']; packed = row['id'] in (2,3)
    before_name = 'q288_tail_vdot' if row['method'] == 'vdot' else 'q288_fused_rvv4'
    actual_body = elf.symbol_data(name)
    model_body = elf.symbol_data(before_name) if packed else actual_body
    certificate = proof.pair_certificate(model_body, actual_body, name) if packed else None
    machine_path = ROOT/'team/optimizations/o2/r2-safe-tail/machine_model.py'
    cls = (tail.phased.checker_class(fused.value_model, machine_path) if row['method'] == 'vdot'
           else fused.value_model.machine_class(machine_path))
    m = cls(fixture, dataset, poison=0x5753288)
    addr = lambda n: elf.symbols[n][0]
    m.addresses = dict(packed=addr('q_packed')+16, x=addr('q_inputs')+288*dataset,
        ws=addr('q_packed_scale')+16 if packed else addr('q_weight_scale'),
        xs=addr('q_input_scale')+36*dataset, y=addr('q_output')+16, slots=addr('q_slots')+16,
        context=addr('q_ws_guarded')+16 if packed else addr('q_context'))
    pointers = [m.addresses[n] for n in ('packed','x','ws','xs','y','slots')]
    if not packed: pointers.append(addr(row['leaf']))
    context = struct.pack('<'+str(len(pointers))+'Q', *pointers)
    g.require(len(context) == (48 if packed else 56) == row['context_bytes'], 'actual context ABI extent')
    m.regions['context'] = bytearray(context); m.original['context'] = context
    m.halt = timer[21][0]; m.x[1] = m.halt; m.x[2] = 0x87fff000-48
    m.x[8] = m.x[10] = m.addresses['context']; m.x[9] = addr('q_measurement'); m.x[20] = addr(name)
    m.saved = {i:m.x[i] for i in m.saved}
    view = SimpleNamespace(symbols={name:(addr(name),len(model_body),0)},
                           symbol_data=lambda requested: model_body if requested == name else elf.symbol_data(requested))
    m.execute_function(view, name)
    detail = m.check(fixture['golden'][dataset]) if row['method'] == 'vdot' else m.check_full('rvv4', fixture['golden'][dataset])
    if packed:
        detail['normalized_model_counts'] = detail['counts']
        actual_counts = dict(detail['counts'])
        g.require(actual_counts.pop('vlse32.v') == 324, 'one scale load in every logical group')
        actual_counts['vle32.v'] = 324
        detail['counts'] = actual_counts
    actual_words = list(struct.unpack('<'+'I'*(len(actual_body)//4), actual_body))
    original_words = list(struct.unpack('<'+'I'*(len(model_body)//4), model_body))
    body_path = []
    for pc, word in m.path:
        delta = pc-addr(name)
        g.require(0 <= delta < len(actual_body) and delta%4 == 0 and original_words[delta//4] == word,
                  'complete normalized path within its certified function')
        body_path.append((pc, actual_words[delta//4]))
    stream = timer[11:21] + body_path + timer[21:27]
    g.require(len(stream) == len(m.path)+16, 'unchanged common timer overhead')
    detail.update(instructions=len(stream),vdot=10368 if row['method']=='vdot' else 0,
        leaf_calls=0,integer_core_executions=324,actual_elf_addresses=True,
        common_timer_bytes_sha256=digest(timer_body),context_bytes=len(context),context_address=hex(m.addresses['context']),
        context_image_sha256=digest(context),scale_address=hex(m.addresses['ws']),scale_alignment_mod16=m.addresses['ws']%16,
        value_model_mode='certified layout-normalized baseline' if packed else 'unchanged actual baseline words',
        candidate_load_executed_by_old_numeric_model=False,layout_equivalence=certificate,
        fp_values='same logical scale bits and unchanged finite-RNE operation order; target execution required')
    return stream, detail


def paths_for_plan(elf, manifest):
    fixture = fixture_gen.fixtures(); paths = {}; details = {}
    for call in manifest['call_plan']:
        row = manifest['rows'][call['arm']]; dataset = call['dataset']; key = str(row['id'])+':'+str(dataset)
        if key in details: continue
        stream, detail = path(elf, row, fixture, dataset)
        if row['id'] in paths: g.require(paths[row['id']] == stream, 'all datasets have identical actual PC/word paths')
        else: paths[row['id']] = stream
        counters = [i for i,(_,w) in enumerate(stream) if w in base.base.traced.COUNTERS]
        g.require(len(counters) == 4, 'four actual counter sites')
        details[key] = dict(detail,dataset=dataset,expected_csr_instret=counters[3]-counters[0],
            path_sha256=digest(b''.join(struct.pack('<QI',pc,w) for pc,w in stream)))
    g.require(len(paths) == 4 and len(details) == 12, 'all four methods and three datasets modeled')
    return paths, details


def compiled_arrays(elf, manifest):
    f = fixture_gen.fixtures(); guard = struct.pack('<2Q',gen.GUARD,gen.GUARD)
    packed = lambda values,size: struct.pack('<'+str(len(values))+size,*values)
    arrays = {
        'q_weights':fixture_gen.bytes8(f['weight']), 'q_weight_scale':fixture_gen.bytes32(f['weight_scale']),
        'q_inputs':b''.join(fixture_gen.bytes8(x) for x in f['inputs']),
        'q_input_scale':b''.join(fixture_gen.bytes32(x) for x in f['input_scale']),
        'q_golden':b''.join(fixture_gen.bytes32(x) for x in f['golden']),
        'q_packed':guard+fixture_gen.bytes8(f['packed'])+guard,
        'q_order':packed(gen.ORDER,'I'), 'q_methods':packed(gen.METHODS,'I'),
        'q_functional_order':packed(gen.FUNCTIONAL_ORDER,'I'),
        'q_functional_datasets':packed(gen.FUNCTIONAL_DATASETS,'I'),
        'q_entry_addresses':packed([elf.symbols[n][0] for n in gen.WRAPPERS],'Q'),
        'split_entries':packed([elf.symbols[n][0] for n in fixture_gen.NEW],'Q')}
    for name, raw in arrays.items(): g.require(elf.symbol_data(name) == raw, 'compiled array: '+name)
    for name,size,alignment in (('q_context',56,8),('q_ws_guarded',80,16),('q_pack_context',16,8),
                                ('q_packed_scale',10400,16),('q_output',1184,16),('q_slots',160,16)):
        address,length = elf.symbols[name][:2]
        g.require(length == size and address%alignment == 0, 'compiled object extent/alignment: '+name)
    calls = [dict(stage=0,arm=a,dataset=d) for a,d in zip(gen.FUNCTIONAL_ORDER,gen.FUNCTIONAL_DATASETS)]
    for arm in gen.ORDER: calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    g.require(manifest['call_plan'] == calls and tuple(s['index'] for s in manifest['plan']) == gen.ORDER,
              'exact complete functional/warm/measured plan')
    g.require(len(calls) == 32 and manifest['full_q_calls'] == 32 and manifest['expected_dots'] == 124417,
              'new complete-call/custom inventory')
    return {n:digest(raw) for n,raw in arrays.items()}


def compiler_commands(log, record):
    result = tail.compiler_commands(log, record)
    root = PurePosixPath(record['build_root']); gcc = record['toolchain']['gcc']['path']
    src, obj = str(root/'source/pack.c'), str(root/'objects/pack.o')
    lines = [shlex.split(s) for s in log.splitlines() if s.startswith(gcc+' ')]
    found = [line for line in lines if src in line]
    expected = [src if v == str(root/'source/q288.c') else obj if v == str(root/'objects/q288.o') else v
                for v in result['q288']]
    g.require(len(found) == 1 and found[0] == expected, 'actual separate scale pack compilation with the same C flags')
    result['pack'] = found[0]
    return result


def verification(repo, build_dir):
    with adapt(fused,CONTRACT=CONTRACT,GENERATED=GENERATED,gen=gen,sources=sources,generate=generate,
               compiled_arrays=compiled_arrays,paths_for_plan=paths_for_plan,compiler_commands=compiler_commands):
        result = tail._OLD_VERIFY(repo, build_dir)
    elf = g.ELF((build_dir/'vdot-perf.elf').read_bytes())
    baseline = tail.phased.certificate(elf)
    g.require(digest(elf.symbol_data('q288_tail_vdot')) ==
              'b318b99344d0ceabb2a5cab6ce671ab2bfcb189e4aacc9ffccb18488165971f3', 'unchanged qualified TA body')
    changed = proof.certificate(elf)
    result.update(status='PACKED_WS_TARGET_ELF_DATASET_AND_TIMER_PATH_PASS',windows=12,full_q_calls=32,
        original_tail_certificate=json.loads(json.dumps(baseline)),packed_scale_certificate=changed,
        target_scale_pack_body_sha256=digest(elf.symbol_data('q288_ws_pack')),
        new_candidate_numeric_interpreter=False,performance_qualified=False)
    return result


def selection(samples, manifest):
    methods = []
    for i,row in enumerate(manifest['rows']):
        ss = [s for s in samples if s['id'] == i]; wanted = 4 if i in (0,2) else 2
        g.require(len(ss) == wanted and all(s['cycles'] > 0 for s in ss), 'every planned positive observation retained')
        methods.append(dict(id=i,label=row['label'],wrapper=row['wrapper'],leaf=row['leaf'],
            cycles=[s['cycles'] for s in ss],instructions=[s['instructions'] for s in ss],
            mean_cycles=sum(s['cycles'] for s in ss)/wanted))
    values = [m['cycles'] for m in methods]
    anchors = {gen.LABELS[i]:dict(cycles=values[i],stable=100*max(values[i])<=101*min(values[i])) for i in (0,2)}
    context = all(a['stable'] for a in anchors.values())
    def compare(candidate, baseline, label):
        after, before = values[candidate], values[baseline]
        gate = 200*max(after) <= 199*min(before)
        return dict(comparison=label,candidate=candidate,baseline=baseline,worst_candidate=max(after),
            best_baseline=min(before),reduction=1-max(after)/min(before),separation_gate=gate,qualified=context and gate)
    comparisons = [compare(3,1,'PTA-vs-TA'),compare(2,0,'PFR-vs-FR'),compare(3,0,'PTA-vs-FR'),
                   compare(3,2,'PTA-vs-PFR'),compare(1,0,'TA-vs-FR'),compare(1,2,'TA-vs-PFR')]
    promote = context and all(comparisons[i]['separation_gate'] for i in (0,2,3))
    retain_ta = context and all(comparisons[i]['separation_gate'] for i in (4,5))
    rvv = 2 if comparisons[1]['separation_gate'] else 0
    selected = 3 if promote else 1 if retain_ta else rvv
    return dict(decision='HOLD_CONTEXT_VARIATION' if not context else 'PACKED_WS_VDOT_PREFERRED_IN_FIXED_PLAN' if promote
        else 'KEEP_QUALIFIED_TA' if retain_ta else 'PACKED_WS_RVV_PREFERRED_IN_FIXED_PLAN' if rvv==2 else 'KEEP_ORIGINAL_FR',
        methods=methods,anchors=anchors,anchor_gate=context,software_comparisons=comparisons[:2],
        comparisons=comparisons,packed_vdot_promoted=promote,ta_eligible_against_both_rvv=retain_ta,
        selected_id=selected if context else None,selected_method=methods[selected]['wrapper'] if context else None,
        selected_label=methods[selected]['label'] if context else None,selected_leaf=methods[selected]['leaf'] if context else None,
        rvv_fallback_id=rvv if context else None,comparison_gate_pass=context,stable_default_changed=False,
        pack_included=False,hardware_changed=False,
        statistical_scope='fixed reverse-order twelve-window plan; FR/PFR separately stable; replay adds no sample',
        application_scope='synthetic prepacked Q, same-method selfwarm; no preparation/token/full-model/ASIC claim')


def normal(repo, build_dir, run_dir, receipt):
    g.require(receipt.get('process_started') is True and receipt.get('exit_code') == 0 and
              not receipt.get('timed_out'), 'complete execution required')
    manifest = read(build_dir/'source/manifest.json')
    stdout, stderr = ((run_dir/n).read_text() for n in ('stdout.log','stderr.log'))
    gate = g.load('ws_target_failure', repo/'team/optimizations/o1/audit/runtime_gate.py')
    fatal = g.load('ws_target_fatal', repo/'team/optimizations/o2/fullcore/recheck.py')
    observer = g.load('ws_target_protocol', repo/'team/optimizations/o2/fullcore/analyze.py')
    for stream in (stdout,stderr): gate.validate_failure_markers(stream); fatal.reject_fatal_output(stream)
    _, uart = observer.extract_events_and_uart(stderr+stdout)
    gate.validate_failure_markers(uart); fatal.reject_fatal_output(uart)
    plain = gate.normalize_console(uart)
    counter = g.load('ws_target_counter', repo/'team/workloads/unified-vdot/check.py')
    elf = g.ELF((build_dir/'vdot-perf.elf').read_bytes()); paths, details = paths_for_plan(elf,manifest)
    counter.walk = lambda stream: stream
    events = counter.parse_events(stderr); samples = counter.trace_windows(events,manifest,paths)
    windows = []; current = None
    for event in events['RETIRE']:
        if event['word'] == base.base.traced.START:
            g.require(current is None, 'no nested measured marker'); current = []
        if current is not None: current.append(event)
        if event['word'] == base.base.traced.STOP:
            g.require(current is not None, 'stop marker has an open window'); windows.append(current); current = None
    g.require(current is None and len(windows) == len(samples) == len(manifest['plan']) == 12,
              'exact new measured window inventory')
    for records, step in zip(windows,manifest['plan']):
        stream = paths[step['index']]; pos = 0
        for event in records:
            covered = stream[pos:pos+event['count']]
            if event['count'] > 1:
                g.require(not any(w&127 in (0x63,0x6f,0x67) for _,w in covered), 'control hidden by ROB compression')
            pos += event['count']
        g.require(pos == len(stream), 'complete marker path')
    for sample, step in zip(samples,manifest['plan']):
        sample.update({k:step[k] for k in ('dataset','block','role')}); row = manifest['rows'][step['index']]
        sample.update(kind='Q',variant=row['variant'],label=row['label'],leaf=row['leaf'])
        g.require(sample['instructions'] == details[str(row['id'])+':0']['expected_csr_instret'],
                  'actual CSR instret vs exact complete path')
    expected = [f'Q_BEGIN contract={CONTRACT} windows=12','Q_PACK words=2592 controls=3 failures=0',
                'Q_FUNCTIONAL calls=32 controls=10 outputs=9216 warm=12 extra=8']
    expected += [f"Q_CALL {i} {c['stage']} {c['arm']} {c['dataset']}" for i,c in enumerate(manifest['call_plan'])]
    expected += [f"QW {s['seq']} {s['cycles']} {s['instructions']}" for s in samples]
    expected += ['Q_END windows=12 full_calls=32 leaf_calls=0 inline_calls=32 probe_dots=1 failures=0']
    actual = [line for line in plain.splitlines() if line.startswith(('Q_','QW '))]
    g.require(actual == expected and plain.count('HIT GOOD TRAP') == 1, 'complete UART/call-plan/counter/oracle evidence')
    analysis = observer.analyze(stderr+stdout)
    g.require(analysis['status'] == 'O2_TRACE_PASS' and analysis['schema']['slots'] == 2 and
        all(analysis.get(k) == 0 for k in ('pending_count','pending_div_count','unfinished_rob_count')) and
        analysis['counts'].get('COMMIT') == 124417, 'complete O2 protocol and all-stage custom total')
    probe_pc = elf.symbols['q_fault_probe'][0]+5*4; expected_pcs = [probe_pc]; phases = []
    for i,call in enumerate(manifest['call_plan']):
        pcs = [pc for pc,w in paths[call['arm']] if w&0xfe00707f == 0x0200000b]
        phases.append(dict(seq=i,**call,vdot_count=len(pcs),first_commit_index=len(expected_pcs)))
        expected_pcs.extend(pcs)
    actual_pcs = [int(v,16) for v in re.findall(r'^O2_COMMIT [^\n]*pc=0x([0-9a-fA-F]+)',stderr,re.M)]
    g.require(actual_pcs == expected_pcs and len(actual_pcs) == 124417,
              'entire functional/warm/timed custom PC sequence')
    g.require(len(events['COUNTER_ENQUEUE']) == len(events['CSR_SAMPLE']) == 48, 'exact new counter totals')
    return dict(status='PACKED_WS_TARGET_DIFFTEST_AND_PLAN_PASS',contract=CONTRACT,windows=12,
        full_q_calls=32,functional_calls=32,explicit_functional_calls=8,timed_q_calls=12,selfwarm_calls=12,
        extra_functional_calls=8,judge_fault_controls=10,scale_pack_calls=1,scale_pack_controls=3,
        committed_vdot=124417,timed_vdot=41472,custom_phases=phases,
        all_stage_custom_pc_sha256=digest(b''.join(struct.pack('<Q',p) for p in actual_pcs)),
        counter_enqueues=48,csr_samples=48,samples=samples,selection=selection(samples,manifest),
        hardware_changed=False,stable_default_changed=False,replay_and_archive_required_for_completion=True)


def build(repo, identity, out):
    with adapt(old,CONTRACT=CONTRACT,sources=sources,generate=generate,verification=verification):
        return old.build(repo,identity,out)


def run(repo, identity, build_dir, out, operation):
    with adapt(base.base.up,CONTRACT=CONTRACT,MAX_CYCLES=MAX_CYCLES,GENERATED=GENERATED,
               sources=sources,verification=verification,gen=SimpleNamespace(NEW=('q_fault_probe',)),normal=normal):
        return base.base.up.run(repo,identity,build_dir,out,operation)


def selector_controls(manifest):
    def data(fr,ta,pfr,pta):
        observations = (fr,ta,pfr,pta); used = [0]*4; result = []
        for i,step in enumerate(manifest['plan']):
            arm = step['index']; value = observations[arm]
            if isinstance(value,list): value = value[used[arm]]
            used[arm] += 1
            result.append(dict(seq=i,id=arm,cycles=value,instructions=1,block=step['block'],role=step['role']))
        return result
    positive = selection(data(100000,90000,99000,88000),manifest)
    g.require(positive['packed_vdot_promoted'] and positive['selected_id'] == 3, 'positive bounded promotion')
    # An end anchor is deliberately the fastest FR observation; discarding it
    # would falsely qualify PFR as a software improvement.
    fast_end = selection(data([100000,99100,100000,99100],110000,99400,109000),manifest)
    g.require(fast_end['anchor_gate'] and not fast_end['software_comparisons'][1]['qualified'] and
              fast_end['selected_id'] == 0, 'fast original RVV end anchors remain in the denominator')
    holds = []
    for fr,pfr in (([100000,97000,100000,100000],99000),(100000,[99000,96000,99000,99000])):
        held = selection(data(fr,90000,pfr,88000),manifest)
        g.require(held['decision'] == 'HOLD_CONTEXT_VARIATION' and held['selected_id'] is None and
                  not any(c['qualified'] for c in held['comparisons']), 'each RVV series independently blocks on instability')
        holds.append(held)
    incumbent = selection(data(100000,90000,99000,91000),manifest)
    g.require(not incumbent['packed_vdot_promoted'] and incumbent['selected_id'] == 1,
              'beating both RVV controls cannot displace a faster TA')
    weak_rvv = selection(data(100000,110000,99600,109000),manifest)
    strong_rvv = selection(data(100000,110000,99400,109000),manifest)
    g.require(weak_rvv['selected_id'] == 0 and strong_rvv['selected_id'] == 2,
              'RVV fallback changes only after conservative separation')
    noisy = selection(data(100000,90000,99000,[85000,90500]),manifest)
    g.require(not noisy['packed_vdot_promoted'] and noisy['selected_id'] == 1,
              'candidate mean cannot hide a worst-observation loss')
    return dict(status='PACKED_WS_BOTH_RVV_AND_INCUMBENT_SELECTOR_CONTROLS_PASS',positive=positive,
        fast_end_anchor=fast_end,independently_unstable_rvv=holds,incumbent=incumbent,
        weak_rvv_fallback=weak_rvv,strong_rvv_fallback=strong_rvv,noisy_candidate=noisy)


def elf_controls(build_dir, out):
    positive = verification(ROOT,build_dir); out.mkdir(parents=True,exist_ok=False)
    raw = (build_dir/'vdot-perf.elf').read_bytes(); elf = g.ELF(raw)
    manifest = read(build_dir/'source/manifest.json'); controls = []
    for name,at,size in (('q_entry_addresses',16,8),('q_order',4,4),('q_functional_datasets',0,4),
                         ('q_golden',0,4),('q_packed',16,1),('q_weight_scale',0,4)):
        body = elf.symbol_data(name); offset = raw.find(body)
        g.require(offset >= 0 and raw.find(body,offset+1) < 0, 'unique array mutation region')
        value = elf.symbols['q288_fused_rvv4'][0] if name == 'q_entry_addresses' else int.from_bytes(body[at:at+size],'little')^1
        changed = bytearray(raw); changed[offset+at:offset+at+size] = value.to_bytes(size,'little')
        g.require(bytes(changed) != raw, 'nonempty actual target array mutation')
        (out/(name+'.elf')).write_bytes(changed)
        try: compiled_arrays(g.ELF(bytes(changed)),manifest)
        except ValueError as error:
            g.require(str(error) == 'compiled array: '+name, 'specific target array rejection')
            controls.append(dict(name=name,file_offset=offset+at,mutated_elf_sha256=digest(changed),error=str(error)))
        else: raise ValueError('actual target array mutant accepted: '+name)
    result = dict(status='PACKED_WS_TARGET_ACTUAL_ELF_CONTROLS_PASS',contract=CONTRACT,positive=positive,
        controls=controls,actual_function_controls=proof.negative_controls(elf),
        selector_regression=selector_controls(manifest),new_emu_runs=0)
    g.save(out/'result.json',result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True); parser.add_argument('--identity',type=Path)
    parser.add_argument('--action',choices=('build','verify','run','elf'),required=True)
    parser.add_argument('--build',type=Path); parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--operation-id'); parser.add_argument('--cpus',default='0,1,2,3')
    args = parser.parse_args(); repo = args.repo.resolve(); out = args.output.resolve()
    g.require(repo == ROOT and not out.exists(), 'selected checkout and fresh output required')
    identity = (args.identity or repo/parent.REPRO/'evidence/clean-reproduction-v1/reports/identity-02.json').resolve()
    cfg = parent.parent_identity(repo,identity)['configuration']
    roots = [repo,identity.parent] + [cfg[k] for k in ('am_home','hardware_source','build_record')]
    if args.build: roots.append(args.build.resolve())
    parent.outside_inputs(out,roots)
    cpus = {int(v) for v in args.cpus.split(',')}
    if os.name == 'posix':
        g.require(0 < len(cpus) <= 4 and cpus <= os.sched_getaffinity(0), 'authorized CPU affinity')
        os.sched_setaffinity(0,cpus)
    if args.action == 'build': result = build(repo,identity,out)
    elif args.action == 'verify':
        g.require(args.build is not None, 'build required'); result = verification(repo,args.build.resolve()); g.save(out,result)
    elif args.action == 'elf':
        g.require(args.build is not None, 'build required'); result = elf_controls(args.build.resolve(),out)
    else:
        g.require(args.build is not None and args.operation_id, 'build and operation required')
        result = run(repo,identity,args.build.resolve(),out,args.operation_id)
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
