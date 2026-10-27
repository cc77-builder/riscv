"""Read complete first-token raw logs without copying or retaining the event stream."""
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct

HERE = Path(__file__).resolve().parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

ref = load('first_token_audit_reference', HERE / 'reference.py')
b, c = ref.b, ref.c
norm = load('first_token_prior_raw_gates', HERE.parent / 'run.py')
stream, projection = norm.stream, norm.projection
need, read, save = b.need, b.read, b.save


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''): value.update(block)
    return value.hexdigest()


def gates():
    return tuple(load('first_token_' + name, b.REPO / path) for name, path in (
        ('banner', 'team/optimizations/o2/fullcore/run_suite.py'),
        ('gate', 'team/optimizations/o1/audit/runtime_gate.py'),
        ('fatal', 'team/optimizations/o2/fullcore/recheck.py'),
        ('observer', 'team/optimizations/o2/fullcore/analyze.py')))


def raw_gates(paths, negative, gate, fatal):
    """The unchanged per-line gates with allocation bounded before length check."""
    for path in paths:
        with path.open('r', encoding='utf-8') as source:
            tail = ''
            while True:
                line = source.readline(stream.MAX_LINE + 1)
                if not line: break
                need(len(line) <= stream.MAX_LINE, 'bounded raw physical line')
                plain = gate.normalize_console(line); fatal.reject_fatal_output(tail + plain)
                tail = (tail + plain)[-4096:]
                if negative and 'HIT BAD TRAP' in plain:
                    need(re.fullmatch(r'(?:Core 0: )?HIT BAD TRAP at pc = 0x[0-9a-f]+\n?', plain) is not None,
                         'canonical sole expected raw bad trap')
                else: gate.validate_failure_markers(plain)


def custom_sites(elf, build):
    sites = {}
    for name, wanted in build['kernel_identity']['functions'].items():
        start, size, *_ = elf.symbols[name]; raw = elf.read(start, size)
        need(size == wanted['bytes'] and hashlib.sha256(raw).hexdigest() == wanted['sha256'], 'actual complete qualified kernel')
        pc = start
        while pc < start + size:
            low = struct.unpack('<H', elf.read(pc, 2))[0]
            if low & 3 != 3:
                pc += 2; continue
            need(pc + 4 <= start + size, 'whole actual instruction extent')
            word = struct.unpack('<I', elf.read(pc, 4))[0]
            if word & 0xfe00707f == 0x0200000b:
                need(name in ('q288_tail_vdot', 'q768_ta'), 'custom site only in qualified TA kernels')
                sites[pc] = dict(word=word, function=name)
            pc += 4
    need(sites and {v['function'] for v in sites.values()} == {'q288_tail_vdot', 'q768_ta'}, 'both complete TA custom site maps')
    return sites


def validate(dest, build_dir, build, receipt, cfg, profile, output):
    need(not output.exists(), 'fresh separate audit output')
    method, negative = receipt['method'], receipt['negative']
    need(build.get('exact_flags_guard') == 1 and all(v == 1 for v in build['expected_flags'].values()) and
         read(build_dir / 'derivation.json')['exact_flags_guard'] == 1, 'new image enforces precise flags before either transcript')
    need(method in (3, 4) and type(negative) is bool and (not negative or method == 4), 'exact method and negative controls')
    need(receipt['contract'] == b.CONTRACT and receipt['operation_id'] == profile['operation_id'] and
         receipt['profile_sha256'] == sha(dest.parent / 'resource-contract.json') and
         read(dest.parent / 'resource-contract.json') == profile and
         receipt['environment_overrides'] == profile['environment_overrides'] ==
         {'XS_NEGATIVE_VECTOR_TARGET': None, 'OMP_NUM_THREADS': '1', 'EMU_THREADS': '1'} and
         receipt['log_profile'] == profile['log_profile'], 'exact runtime resource/source and environment binding')
    need(receipt.get('process_started') is True and receipt.get('direct_child_reaped') is True and
         receipt.get('process_group_absent_after_exit') is True and not receipt.get('residual_process_group') and
         not receipt.get('timed_out') and receipt.get('exit_code') == (1 if negative else 0), 'complete owned expected EMU exit')
    raw, control = ref.image(build_dir, build, method, negative, 1)
    need(sha(dest / 'image.bin') == hashlib.sha256(raw).hexdigest() == receipt['image_sha256'] and
         read(dest / 'image-control.json') == control, 'actual loaded image and explicit controls')
    del raw
    max_cycles, timeout, limit = (profile[k] for k in ('max_cycles', 'external_timeout_seconds', 'max_output_file_bytes'))
    need(all(receipt[k] == profile[k] for k in ('max_cycles', 'external_timeout_seconds', 'max_output_file_bytes')),
         'actual resource contract unchanged')
    need(receipt['command'] == [str(Path(cfg['hardware_source']) / 'build/emu'), '-i', str(dest / 'image.bin'),
         '--flash=' + cfg['flash'], '--ram-size=128MB', '--diff=' + cfg['reference'], '--max-cycles=' + str(max_cycles),
         '--seed=1', '--log-end=0'], 'exact actual frozen EMU invocation')
    logs = [dest / 'stderr.log', dest / 'stdout.log']
    need(receipt['raw_sha256'] == {p.name: sha(p) for p in logs} and
         receipt['raw_bytes'] == {p.name: p.stat().st_size for p in logs} and
         all(p.stat().st_size < limit for p in logs), 'complete original raw bytes and hashes within resource bound')
    banner, gate, fatal, observer = gates()
    raw_gates(logs, negative, gate, fatal)
    elf = c.base.f.g.ELF((build_dir / (b.PREFIX + '.elf')).read_bytes())
    sites = custom_sites(elf, build); commit_hash = hashlib.sha256(); per_site = Counter(); enqueued = Counter()
    class CheckedReader(stream.Reader):
        def events(self):
            for cycle, index, kind, fields in super().events():
                if kind != 'SCHEMA': need(0 <= cycle < max_cycles, 'all actual observer events within guest bound')
                if kind == 'ENQUEUE':
                    pc = fields['pc']
                    need(pc in sites and fields['word'] == sites[pc]['word'], 'every custom enqueue PC/word equals final ELF')
                    enqueued[hex(pc)] += 1
                yield cycle, index, kind, fields
    def commit(fields):
        pc = fields['pc']
        need(method == 4 and pc in sites, 'only selected TA path may retire qualified custom sites')
        commit_hash.update(struct.pack('<Q', pc)); per_site[hex(pc)] += 1
    with ExitStack() as stack:
        reader = CheckedReader([stack.enter_context(p.open('r', encoding='utf-8')) for p in logs])
        protocol = stream.analyze_reader(reader, require_complete=True, commit_sink=commit)
        uart, counters = reader.uart, ''.join(reader.counter_rows)
    count = sum(per_site.values())
    need(protocol['status'] == 'O2_TRACE_PASS' and protocol['schema']['slots'] == 2 and
         all(protocol[k] == 0 for k in ('pending_count', 'pending_div_count', 'unfinished_rob_count')) and
         protocol['counts']['COMMIT'] == count and (count > 0 if method == 4 else count == 0), 'complete exact custom protocol')
    banner.validate_runtime(uart, cfg['reference']); fatal.reject_fatal_output(uart)
    plain = gate.normalize_console(uart)
    lines = [line for line in plain.splitlines() if line.startswith('CONSUMER_')]
    begin = f'CONSUMER_BEGIN method={method} token=1 position=0 negative={int(negative)}'
    need(len(lines) == 3 and lines[0] == begin, 'exact first-token application transcript')
    match = re.fullmatch(r'CONSUMER_COUNTERS ([34]) ([0-9a-f]{16}) ([0-9a-f]{16}) ([0-9a-f]{16}) ([0-9a-f]{16})', lines[1])
    need(match is not None and int(match[1]) == method, 'one canonical full-width counter row')
    values = [int(value, 16) for value in match.groups()[1:]]
    c0, i0, i1, c1 = values
    need(0 < c1 - c0 < max_cycles and 0 < i1 - i0 < 2**32, 'bounded actual UART deltas')
    expected_end = 'CONSUMER_REJECT code=94 byte=152476' if negative else f'CONSUMER_PASS bytes={b.S} flags={build["expected_flags"][str(method)]}'
    need(lines[2] == expected_end, 'entire state compared or precise actual last-logit rejection')
    trap_lines = [line for line in plain.splitlines() if 'HIT ' in line and ' TRAP' in line]
    trap_kind = 'BAD' if negative else 'GOOD'
    need(len(trap_lines) == 1 and plain.count('HIT ' + trap_kind + ' TRAP') == 1, 'one expected terminal trap')
    trap = re.fullmatch(r'(?:Core 0: )?HIT ' + trap_kind + r' TRAP at pc = (0x[0-9a-f]+)', trap_lines[0])
    need(trap is not None, 'canonical terminal trap')
    trap_pc = int(trap[1], 16)
    expected_pcs = [int(x, 16) for x in build['failure_traps']] if negative else [int(build['success_trap'], 16)]
    need(trap_pc in expected_pcs and elf.read(trap_pc, 4) == struct.pack('<I', 0x0005006b), 'actual expected a0-consuming trap PC/word')
    gate.validate_failure_markers('\n'.join(line for line in plain.splitlines() if not (negative and line == trap_lines[0])))
    spent = re.findall(r'Guest cycle spent: (\d+)', plain)
    need(len(spent) == 1 and 0 < int(spent[0]) <= max_cycles, 'complete bounded guest terminal count')
    samples = [dict(cycles=c1 - c0, instret=i1 - i0)]
    # Reuse the exact numerical gate with the declared new total cycle bound.
    timing = c.bind(projection.counter_audit, MAX_CYCLES=max_cycles)(counters, elf, build['counter_sites'], 1, samples, observer)
    need([row['sample']['data'] for row in timing['records']] == values and
         all(row['retire']['cycle'] < max_cycles for row in timing['records']), 'all four exact UART raw values bound to actual CSR retirement')
    custom = dict(count=count, per_site=dict(sorted(per_site.items())), enqueue_per_site=dict(sorted(enqueued.items())),
        pc_sha256=commit_hash.hexdigest(), digest_encoding='ordered architectural custom COMMIT PCs, each unsigned little-endian u64',
        sites={hex(pc): dict(word=hex(info['word']), function=info['function']) for pc, info in sorted(sites.items())},
        exact_dynamic_count_claimed=False)
    output.mkdir(parents=True)
    save(output / 'protocol.json', protocol); save(output / 'counter-audit.json', timing); save(output / 'custom.json', custom)
    (output / 'uart.txt').write_text(uart); (output / 'counter-source.txt').write_text(counters)
    return dict(contract=b.CONTRACT, status='EXPECTED_FIRST_TOKEN_TARGET_REJECTION' if negative else 'FIRST_TOKEN_TARGET_DIFFTEST_PASS',
        method=method, negative=negative, transcript=lines, flags=build['expected_flags'][str(method)],
        flags_evidence='fixed-program flags==1 gate before COUNTERS/REJECT' if negative else 'exact PASS flags plus fixed-program flags==1 gate',
        guest_cycles=int(spent[0]), counter_values=values, samples=samples, trap_pc=hex(trap_pc), custom=custom,
        protocol={k: v for k, v in protocol.items() if k != 'input_sha256'}, counter_audit=timing,
        target_correctness_qualified=not negative, performance_qualified=False, full_retirement_window_audited=False,
        scope='one cold p0 token1 complete state comparison, original DiffTest, full custom protocol and four CSR chains')
