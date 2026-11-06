"""Small GNU/NEMU qualification; frozen scalar and official inputs stay read-only."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import resource
import shutil
import signal
import struct
import subprocess

HERE = Path(__file__).resolve().parent
CONTRACT = 'r2-s3-gs32-quantize-v1'
BASE = 0x80000000
PREFIX = 'quantize-gs32-check'
SOURCES = ('Makefile', 'main.c', 'probe.S', 'entry.S', 'linker.ld', 'quantize.S', 'CONTRACT.md', 'verify.py', 'oracle.json')
CORE_SHA = '6d50d5b613f6bdb7011f4fd148e668ca44e23bb59b11e2b9e6fcbaa69a7207bb'
LIBM_SHA = 'fab30dd1171318d09d987f7f84a9542e2b0504b27bca4170ddc22454c6b8041b'
RUNNER_SHA = '567ab9b91e7596c6bf682b56baeb42b36334e307fb54657dfe730eb2e1d98b9d'
REFERENCE_SHA = '8af118e5519db7ef6001010a2d547707c5d47630412e80abfc3f343bfef987c9'
ROWS, ROW_BYTES = 30, 17568
MAX_CALLS, WALL = 20000000, 120


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def need(ok, text):
    if not ok:
        raise ValueError(text)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def read(path):
    return json.loads(Path(path).read_text())


def command(argv, cwd, label, timeout=120, acceptable=(0,), env=None):
    argv = list(map(str, argv))
    rec = dict(command=argv, cwd=str(cwd), started=now(), cpu_affinity=sorted(os.sched_getaffinity(0)),
               pid=None, exit_code=None, timed_out=False, direct_child_reaped=False,
               process_group_absent_after_exit=False)
    p = None
    try:
        with (cwd / (label + '.stdout.log')).open('wb') as out, (cwd / (label + '.stderr.log')).open('wb') as err:
            p = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err, start_new_session=True, env=env)
            rec['pid'] = p.pid
            save(cwd / (label + '.receipt.json'), rec)
            try:
                rec['exit_code'] = p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                rec['timed_out'] = True
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    rec['exit_code'] = p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    rec['exit_code'] = p.wait(timeout=3)
            rec['direct_child_reaped'] = p.returncode is not None
    except BaseException:
        if p is not None:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait(timeout=3)
            rec['exit_code'] = p.returncode
            rec['direct_child_reaped'] = p.returncode is not None
        raise
    finally:
        if p is not None:
            try:
                os.killpg(p.pid, 0)
            except ProcessLookupError:
                rec['process_group_absent_after_exit'] = True
        rec['finished'] = now()
        save(cwd / (label + '.receipt.json'), rec)
    need(rec['direct_child_reaped'] and rec['process_group_absent_after_exit'] and not rec['timed_out'], label + ' terminal cleanup')
    need(rec['exit_code'] in acceptable, label + ' exit: ' + str(rec['exit_code']))
    return rec


def instructions(text):
    rows = [(int(m[1], 16), int(m[2], 16), len(m[2]) // 2)
            for m in re.finditer(r'^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F]{4,8})\s+', text, re.M)]
    need(bool(rows), 'nonempty actual instructions')
    return [(pc - rows[0][0], word, size) for pc, word, size in rows]


def original_code_equal(name, text, oracle):
    reference = instructions(oracle['actual_functions'][name])
    actual = instructions(text)
    offsets = {'quantize': {8, 12, 92, 96, 180, 184, 256, 260}, '__round': {14, 18}, '__fabs': set()}[name]
    need(len(reference) == len(actual), name + ' instruction count')
    differences = []
    for (offset, word, size), (off2, word2, size2) in zip(reference, actual):
        need((offset, size) == (off2, size2), name + ' instruction extent')
        if offset in offsets:
            need(size == 4, name + ' relocation width')
            mask = 0xfff if word & 0x7f == 0x17 else 0xfffff
            need(word & mask == word2 & mask, name + ' unchanged opcode/registers')
            if word != word2:
                differences.append(offset)
        else:
            need(word == word2, name + ' exact non-relocation instruction')
    return dict(instructions=len(actual), bytes=actual[-1][0] + actual[-1][2], relocation_offsets_changed=differences)


def whole_tree(root):
    return {str(p): digest(p) for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink() and '.git' not in p.parts}


def verify_pins(pins):
    for name, expected in pins.items():
        need(digest(name) == expected, 'input changed: ' + name)


def symbols(text):
    result = {}
    for line in text.splitlines():
        m = re.fullmatch(r'([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\S\s+(\S+)', line.strip())
        if m:
            result[m[3]] = (int(m[1], 16), int(m[2], 16))
        else:
            m = re.fullmatch(r'([0-9a-fA-F]+)\s+\S\s+(\S+)', line.strip())
            if m:
                result[m[2]] = (int(m[1], 16), 0)
    return result


def build(args, out, pins, oracle):
    source = out / 'source'
    source.mkdir()
    for name in SOURCES:
        shutil.copyfile(HERE / name, source / name)
    core = args.parent / 'consumer-core.o'
    shutil.copyfile(core, source / 'original-consumer-core.o')
    need(digest(source / 'original-consumer-core.o') == CORE_SHA, 'exact original object copy')
    text = (source / 'quantize.S').read_text()
    need(text.count('  fsrmi 4\n') == text.count('  fscsr t0\n') == 1, 'one bounded negative mutation site')
    variants = [('candidate', 'r2_quantize_gs32_rvv', text),
                ('bad-rne', 'r2_quantize_bad_rne', text.replace('  fsrmi 4\n', '  fsrmi 0\n')),
                ('bad-keep-flags', 'r2_quantize_bad_keep_flags', text.replace('  fscsr t0\n', '  nop\n')),
                ('bad-entry-flags', 'r2_quantize_bad_entry_flags', text.replace('  fscsr t0\n', '  fscsr t3\n'))]
    tools = read(args.parent / 'tools.json')
    need(tools == oracle['tools'], 'same observed GNU tool metadata')
    pins[str(args.parent / 'tools.json')] = digest(args.parent / 'tools.json')
    for tool in tools.values():
        need(digest(tool['path']) == tool['sha256'], 'fixed GNU tool: ' + tool['path'])
        pins[tool['path']] = tool['sha256']
    save(out / 'tools.json', tools)
    for label, symbol, content in variants:
        path = source / (label + '.S')
        path.write_text(content.replace('r2_quantize_gs32_rvv', symbol))
        command([tools['gcc']['path'], '-march=rv64gv', '-mabi=lp64d', '-mno-relax', '-c', path,
                 '-o', source / (label + '.o')], out, label + '-compile')
    env = dict(os.environ)
    for key in ('CFLAGS', 'CPPFLAGS', 'CXXFLAGS', 'ASFLAGS', 'LDFLAGS', 'CC_OPT', 'MAKEFLAGS', 'MFLAGS',
                'CC', 'AS', 'LD', 'OBJCOPY', 'OBJDUMP', 'ARCH', 'MARCH', 'LIBS', 'PREBUILD'):
        env.pop(key, None)
    env.update(AM_HOME=str(args.am_home), LINUX_GNU_TOOLCHAIN='1', LC_ALL='C', OMP_NUM_THREADS='1')
    command([tools['make']['path'], '--trace', '--output-sync=target', '-C', source,
             'CROSS_COMPILE=' + tools['gcc']['path'][:-3],
             'QUANT_OBJ_ROOT=' + str(out / 'objects'), 'BINARY=' + str(out / PREFIX),
             'MATH_ARCHIVE=/usr/riscv64-linux-gnu/lib/libm.a', '-j1', 'image'],
            out, 'target-build', 180, env=env)
    elf = out / (PREFIX + '.elf')
    command([tools['nm']['path'], '-S', '--defined-only', elf], out, 'symbols')
    command([tools['objdump']['path'], '-drwC', elf], out, 'disassembly')
    command([tools['readelf']['path'], '-Whlsr', elf], out, 'metadata')
    syms = symbols((out / 'symbols.stdout.log').read_text())
    raw = (out / (PREFIX + '.bin')).read_bytes()
    need(0 < len(raw) < 4 * 1024 * 1024, 'small standalone image')
    need(syms['_start'][0] == BASE, 'standalone entry at the unmodified boot target')
    need(syms['__quant_stack_top'][0] % 16 == 0 and
         syms['__quant_stack_top'][0] - syms['__quant_stack_bottom'][0] == 65536,
         'private aligned 64 KiB stack')
    need(syms['__quant_stack_bottom'][0] >= BASE + len(raw), 'stack excludes the loaded image')
    need(all(name not in syms for name in ('_trm_init', '__am_init_uartlite', '__errno_location')),
         'no device initialization or errno dependency in standalone scalar calls')
    proof = {}
    for name in ('quantize', '__round', '__fabs'):
        command([tools['objdump']['path'], '-dw', '--disassemble=' + name, elf], out, 'original-' + name)
        dis = (out / ('original-' + name + '.stdout.log')).read_text()
        proof[name] = original_code_equal(name, dis, oracle)
        if name == 'quantize':
            need(dis.count('<__fabs>') == dis.count('<__round>') == dis.count('<GS>') == 1, 'actual original targets')
            m = re.findall(r'flw\s+fs1,[^\n]+#\s+([0-9a-fA-F]+)', dis)
            need(len(m) == 1, 'one denominator address')
            offset = int(m[0], 16) - BASE
            need(raw[offset:offset + 4] == bytes.fromhex('0000fe42'), 'original denominator bytes')
        elif name == '__round':
            m = re.findall(r'fld\s+[^\n]+#\s+([0-9a-fA-F]+)', dis)
            need(len(m) == 1, 'one round threshold')
            offset = int(m[0], 16) - BASE
            need(raw[offset:offset + 8] == bytes.fromhex('0000000000004043'), 'original round threshold bytes')
    plans = []
    for symbol, name, size in (('quant_report', 'report.bin', 128), ('quant_cases', 'cases.bin', ROWS * ROW_BYTES),
                               ('quant_control', 'control.bin', 16)):
        address, length = syms[symbol]
        need(length == size and BASE <= address < BASE + len(raw), 'complete dumped symbol ' + symbol)
        plans.append((name, address, size))
    control = syms['quant_control'][0] - BASE
    need(raw[control:control + 16] == struct.pack('<2Q', 0x5154475333325631, 0), 'actual initial control')
    trap = syms['quant_finish_trap'][0]
    need(raw[trap - BASE:trap - BASE + 4] == bytes.fromhex('6b000500'), 'actual terminal instruction')
    (out / 'dump-plan.txt').write_text(''.join(f'{name} {addr:x} {size}\n' for name, addr, size in plans))
    record = dict(contract=CONTRACT, status='QUANTIZE_STATIC_PASS_NOT_RUNTIME', elf_sha256=digest(elf),
                  bin_sha256=digest(out / (PREFIX + '.bin')), control_offset=control, trap_pc=trap,
                  dump_plan=plans, original_identity=proof, source_pins={str(p.relative_to(source)): digest(p) for p in source.iterdir() if p.is_file()},
                  candidate_symbol=syms['r2_quantize_gs32_rvv'], parent=str(args.parent), performance_qualified=False)
    save(out / 'build.json', record)
    return raw, record


def validation(dest, mode, record):
    result, abi = read(dest / 'reference-result.json'), read(dest / 'abi.json')
    expected = 'bad_trap' if mode else 'good_trap'
    need(result['state'] == 2 and result['reason'] == expected and result['halt_ret'] == (94 if mode else 0), 'actual reference trap')
    need(result['halt_pc'] == record['trap_pc'] and result['pc'] == record['trap_pc'] + 4, 'actual complete terminal PC')
    need(0 < result['retired'] <= result['api_calls'] <= MAX_CALLS and not result['xiangshan_cycles_measured'], 'bounded reference only')
    need(all(result[n] == 0 for n in ('mcause', 'mepc', 'mtval')), 'no reference exception')
    need(abi['register_bytes'] == abi['header_span'] == 1400 and abi['initial_pc'] == 0x10000000 and abi['initial_mode'] == 3, 'actual original reference ABI')
    need(result['memory_dumps'] == 3, 'complete configured memory dump count')
    report = struct.unpack('<16Q', (dest / 'report.bin').read_bytes())
    need(report[:5] == (0x5154475333325631, 1, mode, ROWS, ROW_BYTES) and report[6] == 16, 'complete report identity')
    raw = (dest / 'cases.bin').read_bytes()
    need(len(raw) == ROWS * ROW_BYTES, 'complete case evidence')
    failures, cases = [], []
    for i in range(ROWS):
        row = raw[i * ROW_BYTES:(i + 1) * ROW_BYTES]
        cfg = struct.unpack_from('<9Q', row, 0)
        need(cfg[0] == i, 'case order')
        inp, after0, after1 = row[72:3176], row[3176:6280], row[6280:9384]
        out0, out1 = row[9384:13272], row[13272:17160]
        p0, p1 = struct.unpack_from('<13Q', row, 17352), struct.unpack_from('<13Q', row, 17456)
        fail = int(out0 != out1) | (int(inp != after0) << 1) | (int(inp != after1) << 2) | (int(p0[5] != p1[5]) << 3)
        for k, p in enumerate((p0, p1)):
            fail |= int(p[1:5] != p[6:10]) << 4
            fail |= int(p[10] != 0) << 5
            fail |= int(row[17160 + k * 48:17208 + k * 48] != row[17256 + k * 48:17304 + k * 48]) << 6
            fail |= int(p[:5] != (cfg[3] * 32 + cfg[4], cfg[5], cfg[6], cfg[7], cfg[8])) << 7
            need(0 < p[12] - p[11] < MAX_CALLS, 'bounded actual call interval')
        need(fail == struct.unpack_from('<Q', row, 17560)[0], 'independent host agrees with guest comparator')
        if fail:
            failures.append(i)
        cases.append(dict(case=i, failure=fail, scalar_fcsr=p0[5], candidate_fcsr=p1[5],
                          scalar_instret=p0[12] - p0[11], candidate_instret=p1[12] - p1[11],
                          scalar_q_first=list(out0[16:20]), candidate_q_first=list(out1[16:20])))
    need(report[7] == len(failures) and report[8] == sum(1 << x for x in failures) and report[9] == (94 if failures else 0), 'full failure inventory')
    need(not any(report[10:]), 'reserved report unchanged')
    need((mode == 0 and not failures) or (mode != 0 and bool(failures)), 'positive or effective negative')
    need(cases[0]['scalar_q_first'][1:3] == [1, 255] and cases[0]['scalar_fcsr'] == 0, 'halfway oracle witness')
    need(cases[1]['scalar_fcsr'] == 1, 'division NX oracle witness')
    need(cases[11]['scalar_fcsr'] == 3 and cases[11]['scalar_q_first'][:3] == [127, 0, 0], 'normal scale with UF and NX witness')
    if mode == 1:
        need(cases[0]['failure'] & 1 and cases[0]['candidate_q_first'][1:3] == [0, 0], 'RNE defect killed by halfway witness')
    if mode == 2:
        need(cases[0]['failure'] & 8 and cases[0]['candidate_fcsr'] & 1, 'conversion NX defect killed')
    if mode == 3:
        need(cases[1]['failure'] & 8 and cases[1]['candidate_fcsr'] == 0, 'entry restore defect killed by original division NX')
    need((dest / 'control.bin').read_bytes() == struct.pack('<2Q', 0x5154475333325631, mode), 'complete control unchanged')
    need(not (dest / 'reference.stderr.log').read_bytes(), 'no unexplained reference stderr')
    return dict(status='QUANTIZE_REFERENCE_PASS' if mode == 0 else 'EXPECTED_QUANTIZE_DEFECT_REJECTION', mode=mode,
                cases=cases, failure_cases=failures, reference=result,
                raw_sha256={p.name: digest(p) for p in sorted(dest.glob('*.bin'))}, performance_qualified=False)


def run(args):
    out = args.output
    need(sorted(os.sched_getaffinity(0)) == [1] and not out.exists(), 'fresh CPU1 experiment')
    need(out.is_absolute() and all(root != out and root not in out.parents for root in
         (args.parent, args.am_home, args.adapter, args.reference.parent, HERE)), 'isolated output')
    out.mkdir(parents=True)
    state = dict(contract=CONTRACT, status='RUNNING', started=now(), cpu_affinity=[1], reference_runs=0, target_emu_runs=0, performance_qualified=False)
    save(out / 'state.json', state)
    pins, am_before = {}, None
    try:
        pins = {str(HERE / name): digest(HERE / name) for name in SOURCES}
        fixed = {args.parent / 'consumer-core.o': CORE_SHA, Path('/usr/riscv64-linux-gnu/lib/libm.a'): LIBM_SHA,
                 args.adapter / 'reference-runner': RUNNER_SHA, args.reference: REFERENCE_SHA}
        pins.update({str(p): h for p, h in fixed.items()})
        am_before = whole_tree(args.am_home)
        pins.update(am_before)
        save(out / 'inputs.json', pins)
        verify_pins(pins)
        oracle = read(HERE / 'oracle.json')['readback']
        raw, record = build(args, out, pins, oracle)
        save(out / 'inputs.json', pins)
        verify_pins(pins)
        checks = []
        for mode, label in enumerate(('positive', 'bad-rne', 'bad-keep-flags', 'bad-entry-flags')):
            dest = out / label
            dest.mkdir()
            image = bytearray(raw)
            struct.pack_into('<Q', image, record['control_offset'] + 8, mode)
            (dest / 'image.bin').write_bytes(image)
            save(dest / 'control.json', dict(mode=mode, base_sha256=record['bin_sha256'], actual_sha256=digest(dest / 'image.bin')))
            state['reference_runs'] += 1
            save(out / 'state.json', state)
            command([args.adapter / 'reference-runner', args.reference, dest / 'image.bin', dest,
                     'builtin', str(MAX_CALLS), str(WALL), out / 'dump-plan.txt', '1'], dest, 'reference', WALL + 10,
                    acceptable=((2,) if mode else (0,)))
            checked = validation(dest, mode, record)
            save(dest / 'validation.json', checked)
            checks.append(checked)
            print(label, checked['status'], flush=True)
        verify_pins(pins)
        need(whole_tree(args.am_home) == am_before, 'whole official AM file inventory unchanged')
        state['status'] = 'GS32_QUANTIZE_BOUNDED_REFERENCE_PASS'
        state['finished'] = now()
        save(out / 'result.json', dict(**state, build=record, validations=checks, official_inputs_unchanged=True))
    except BaseException as error:
        state.update(status='FAILED', error=repr(error))
        raise
    finally:
        if state['status'] == 'FAILED' and am_before is not None:
            try:
                am_after = whole_tree(args.am_home)
                changed = sorted(k for k in set(am_before) | set(am_after) if am_before.get(k) != am_after.get(k))
                state['official_am_unchanged'] = not changed
                save(out / 'failure-input-audit.json', {'official_am_changed_paths': changed})
            except BaseException as error:
                state['failure_audit_error'] = repr(error)
        state['finished'] = now()
        save(out / 'state.json', state)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('owned quantize experiment stopped')))
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'am-home', 'adapter', 'reference', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    for name in ('parent', 'am_home', 'adapter', 'reference', 'output'):
        setattr(args, name, getattr(args, name).resolve())
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))
    run(args)
