"""GNU ELF certificate and finite numeric screen for whole2 supply.

This is neither a target CPU nor a timing/exception model. The scalar dot16
oracle, strict FP arithmetic and ELF support are reused without changing their
sources; whole-two loading and the new complete function have separate checks.
"""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import argparse
import copy
import json
import os
import shutil
import struct
import sys

import generate

HERE = Path(__file__).resolve().parent
PARENT = generate.FUSED.parent
need, sha = generate.need, generate.sha


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def support(repo):
    old_generator = generate.old_generator(repo)
    previous = sys.modules.get('candidate')
    sys.modules['candidate'] = old_generator
    try:
        old = generate.load('whole2_fixed_dot16_screen', repo / generate.OLD / 'screen.py',
                            generate.OLD_SCREEN_SHA)
    finally:
        if previous is None:
            sys.modules.pop('candidate', None)
        else:
            sys.modules['candidate'] = previous
    model, helpers = old.support(repo)
    return model, helpers, old


def branch_target(word, pc):
    offset = ((word >> 31) << 12) | (((word >> 7) & 1) << 11)
    offset |= (((word >> 25) & 63) << 5) | (((word >> 8) & 15) << 1)
    return pc + (offset - 8192 if offset & 4096 else offset)


def certificate(elf):
    baseline = elf.symbol_data('q288_fused_vdot')
    body = elf.symbol_data(generate.NAME)
    need(sha(baseline) == '9a155c33b9f27ca04d68ab3e0d883d6819876db6dc1c5d6f55ba9a3faa435648',
         'unaltered original fused-vdot shell')
    need(len(baseline) == 800 and len(body) == 412 and body[:60] == baseline[:60],
         'exact original prefix and 412-byte complete function')
    targets, footer = [], []
    for index, (old, new) in enumerate(zip(struct.unpack('<45I', baseline[620:]),
                                          struct.unpack('<45I', body[232:]))):
        if old & 0x707f == 0x1063:
            need(new & 0x01fff07f == old & 0x01fff07f, 'same suffix branch condition')
            target = branch_target(new, 232 + 4 * index)
            need(target == branch_target(old, 620 + 4 * index), 'same logical loop target')
            targets.append(target)
        else:
            need(new == old, 'unchanged FP/ABI/stores and +32 X suffix')
            if old == 0x02058593:
                footer.append(index)
    need(len(footer) == 1 and targets == [60, 44], 'one X footer and both loop targets')
    pointers = {11: ('X', 0), 12: ('W', 0)}
    vectors, reads, counts, configs = {}, Counter(), Counter(), []
    mode = None

    def write(reg, value):
        need(0 <= reg < 32 and reg not in range(8, 14), 'v8..v13 FP state preserved')
        vectors[reg] = value

    for word, in struct.iter_unpack('<I', body[60:232]):
        op, f3 = word & 127, (word >> 12) & 7
        rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
        if word in (0xc4087057, 0xc1027057):
            mode = (16, 8, 1, 1, 0) if word == 0xc4087057 else (4, 32, 1, 0, 0)
            configs.append(mode)
            counts['vsetivli'] += 1
        elif op == 0x13 and f3 == 0:
            imm = word >> 20
            imm -= 4096 if imm & 2048 else 0
            need((rd, a) == (31, 12) and imm in range(0, 256, 32), 'bounded W row address')
            pointers[rd] = ('W', imm)
            counts['addi'] += 1
        elif word & 0xfff0707f == 0x22800007:
            need(mode == (16, 8, 1, 1, 0) and a in pointers, 'whole2 valid mode/address')
            need(rd in (14, 16, 18, 20, 22) and rd % 2 == 0, 'defined whole2 register group')
            region, offset = pointers[a]
            limit = 32 if region == 'X' else 256
            need(0 <= offset <= limit - 32, 'exact complete 32-byte allocation')
            values = tuple((region, offset + i) for i in range(32))
            reads.update(values)
            write(rd, ('bytes', values[:16]))
            write(rd + 1, ('bytes', values[16:]))
            counts['vl2re8.v'] += 1
        elif word & 0xfe00707f == 0x0e00000b:
            need(mode == (16, 8, 1, 1, 0), 'exact dot16 mode including TA/MU')
            need(a in vectors and b in vectors and vectors[a][0] == vectors[b][0] == 'bytes',
                 'defined dot16 source bytes')
            left, right = vectors[a][1], vectors[b][1]
            need(len(left) == len(right) == 16 and all(x[0] == 'W' and y[0] == 'X'
                 for x, y in zip(left, right)), 'sixteen W/X source roles')
            terms = Counter((x[1] // 32, x[1] % 32, y[1]) for x, y in zip(left, right))
            write(rd, ('lanes', (terms, Counter(), Counter(), Counter())))
            counts['vdot16.vv'] += 1
        elif op == 0x57 and word >> 26 == 0 and f3 == 0 and (word >> 25) & 1:
            need(mode == (4, 32, 1, 0, 0), 'four-lane TU/MU integer sum')
            need(a in vectors and b in vectors and vectors[a][0] == vectors[b][0] == 'lanes',
                 'defined partial sums')
            lanes = tuple(x + y for x, y in zip(vectors[a][1], vectors[b][1]))
            need(all(sum(lane.values()) <= 32 for lane in lanes), 'int32-safe product sum')
            write(rd, ('lanes', lanes))
            counts['vadd.vv'] += 1
        else:
            raise ValueError('unknown whole2 core word ' + hex(word))
    need(configs == [(16, 8, 1, 1, 0), (4, 32, 1, 0, 0)], 'exact two configurations')
    need(counts == Counter(vsetivli=2, addi=8, **{'vl2re8.v': 9, 'vdot16.vv': 16, 'vadd.vv': 8}),
         '43-word instruction multiset')
    need(pointers[11] == ('X', 0) and pointers[12] == ('W', 0), 'core base pointers unchanged')
    wanted = Counter({('W', i): 1 for i in range(256)})
    wanted.update({('X', i): 1 for i in range(32)})
    need(reads == wanted, 'all source bytes read exactly once per group')
    for row in range(8):
        expected = ('lanes', (Counter({(row, k, k): 1 for k in range(32)}), Counter(), Counter(), Counter()))
        need(vectors[row] == expected, 'each matching row product once and high96 zero')
    return dict(status='WHOLE2_ACTUAL_WORD_CERTIFICATE_PASS', core_words=43,
                core_sha256=sha(body[60:232]), function_bytes=len(body), function_sha256=sha(body),
                counts=dict(counts), modes=configs, prefix_bytes=60, suffix_words=45,
                logical_loop_targets=targets, x_core_advance=0, x_footer_advance=32,
                source_bytes_per_group=dict(W=256, X=32), high96_zero=True,
                gs32_sum_min=-520192, gs32_sum_max=524288, layout_unchanged=True)


def checker_class(repo, model, old):
    prior = old.checker_class(model, repo / 'team/optimizations/o2/r2-safe-tail/machine_model.py')
    full, dot16_hook, integer = prior.__mro__[1:4]

    class Whole2Hook(integer):
        def execute(self, code):
            need(code and len(code) % 4 == 0, 'complete machine words')
            for word, in struct.iter_unpack('<I', code):
                if word & 0xfff0707f != 0x22800007:
                    super().execute(struct.pack('<I', word))
                    continue
                need((self.vl, self.sew, self.lmul, self.ta, self.ma, self.vstart)
                     == (16, 8, 1, 1, 0, 0), 'whole2 VL16/e8/m1/TA/MU state')
                rd, address = (word >> 7) & 31, (word >> 15) & 31
                need(rd % 2 == 0 and rd <= 30, 'whole-two register alignment')
                self.put(rd, self.read(self.x[address], 32), 32)
                self.counts['vl2re8.v'] += 1
            return self

    class Whole2(prior, Whole2Hook):
        def check(self, golden):
            # Actual semantic output precedes path/count checks for the mutants.
            need(self.regions['y'] == struct.pack('<288I', *golden), 'whole2 actual full-Q bitwise output')
            f, d = self.fixture, self.dataset
            dots = [sum(f['weight'][r * 288 + k] * f['inputs'][d][k] for k in range(256, 288))
                    for r in range(280, 288)]
            slots = b''.join(struct.pack('<I', value & 0xffffffff) + bytes(12) for value in dots)
            need(self.regions['slots'] == slots, 'complete final eight 128-bit slots')
            need(all(bytes(self.regions[n]) == raw for n, raw in self.original.items()
                     if n not in ('y', 'slots')), 'all inputs and context unchanged')
            reads = Counter()
            for name, size, times in (('packed', 82944, 1), ('x', 288, 36), ('ws', 10368, 1),
                                      ('xs', 36, 36), ('context', 48, 1)):
                reads.update({(name, i): times for i in range(size)})
            need(self.read_bytes_count == reads, 'complete exact input footprint')
            writes = Counter({(name, i): 1 for name, size in (('y', 1152), ('slots', 128))
                              for i in range(size)})
            need(self.write_bytes_count == writes, 'complete exact output footprint')
            need(all(self.x[i] == v for i, v in self.saved.items()) and
                 all(self.f[i] == v for i, v in self.saved_fp.items()), 'scalar and FP ABI')
            self.mode(8, 8, 1)
            need(self.vcsr == 7 and self.frm == 0, 'final CSR and rounding mode')
            need(self.fp_counts == Counter(convert=2592, mul=5184, add=2592), 'unchanged strict FP operations')
            need(self.counts['vdot16.vv'] == 5184 and self.counts['vdot.vv'] == 0 and
                 self.counts['vadd.vv'] == 2592 and self.counts['vl2re8.v'] == 2916, 'whole2 arithmetic/load counts')
            need(self.counts['vs1r.v'] == 8 and self.counts['vse32.v'] == 36 and self.counts['ret'] == 1,
                 'complete stores and ordinary return')
            begin, length = self.function_begin + 60, 43
            expected = [(begin + 4 * i, self.function_words[begin + 4 * i]) for i in range(length)]
            starts = [i for i, (pc, _) in enumerate(self.path) if pc == begin]
            need(len(starts) == 324 and all(self.path[i:i + length] == expected for i in starts)
                 and sum(begin <= pc < begin + 4 * length for pc, _ in self.path) == 324 * length,
                 '324 complete dynamically executed whole2 cores')
            need(len(self.path) == 21090, 'actual complete function instruction count')
            return dict(instructions=len(self.path), counts=dict(self.counts),
                        fp_element_operations=dict(self.fp_counts), output_sha256=sha(self.regions['y']),
                        final_slots_sha256=sha(self.regions['slots']), core_executions=324, core_words=43,
                        exact_footprints=True, abi_preserved=True, stack_used_bytes=0)

    need(Whole2.__mro__[:6] == (Whole2, prior, full, dot16_hook, Whole2Hook, integer),
         'FullQ lexical super reaches scalar-dot16 oracle then whole2 hook')
    return Whole2


def numeric(repo, out, elf, model, helpers, old):
    out.mkdir()
    headers = {'q288.h': repo / PARENT / 'q288.h', 'caller.h': repo / PARENT.parent / 'caller.h',
               'split.h': repo / PARENT.parent / 'split/split.h'}
    library = helpers.oracle_library(repo / PARENT / 'oracle.c', headers, out / 'oracle')
    fixture = helpers.fixtures(repo / PARENT / 'generate.py')
    cases = [('x' + str(d), fixture, d) for d in (0, 1, 0, 2)]
    for name, w, x in (('min-min', -128, -128), ('max-max', 127, 127),
                       ('min-max', -128, 127), ('zero-weight', 0, None)):
        f = copy.deepcopy(fixture)
        f['weight'] = f['packed'] = [w] * 82944
        f['inputs'][0] = [x] * 288 if x is not None else list(fixture['inputs'][0])
        cases.append((name, f, 0))
    cls = checker_class(repo, model, old)
    results, previous = [], None
    for index, (name, f, dataset) in enumerate(cases):
        golden = helpers.native_golden(library, f, dataset)
        need(golden == helpers.python_golden(f, dataset), 'independent native C/Python golden agreement')
        if index < 4:
            need(golden == f['golden'][dataset], 'frozen fixture golden')
        if index == 0:
            need(golden[0] == 0, 'strict FMA rounding witness')
        alignment = (0, 0) if index < 4 else ((index * 3) % 16, (index * 7) % 16)
        machine = cls(f, dataset, poison=0x162000 + index, alignment=alignment)
        if index in (1, 2, 3):
            need(machine.regions['packed'] == previous.regions['packed'], 'same reusable packed W object')
            machine.regions['packed'] = previous.regions['packed']
            machine.v = [bytearray(v) for v in previous.v]
        machine.execute_function(elf, generate.NAME)
        results.append(dict(case=name, index=index, dataset=dataset, alignment=alignment,
                            **machine.check(golden)))
        previous = machine
    result = dict(status='WHOLE2_ACTUAL_ELF_NUMERIC_PASS', cases=results)
    save(out / 'result.json', result)
    return result


def controls(repo, out, elf, model, helpers, old):
    out.mkdir()
    body = elf.symbol_data(generate.NAME)
    _, _, offset = elf.symbols[generate.NAME]
    words = list(struct.unpack('<103I', body))
    core = words[15:58]
    changes = []
    high = next(i for i, w in enumerate(core) if w & 0xfe00707f == 0x0e00000b and (w >> 20) & 31 == 15)
    wrong_x = list(words)
    wrong_x[15 + high] = (wrong_x[15 + high] & ~(31 << 20)) | (14 << 20)
    changes.append(('wrong-x-high-half', wrong_x))
    need(all(w & 0xfe00707f == 0x0e00000b for w in core[14:18]) and
         sum(w & 0xfff0707f == 0x22800007 for w in core[18:26]) == 4, 'actual batch boundary for mutant')
    overwrite = list(words)
    overwrite[29:41] = core[18:26] + core[14:18]
    changes.append(('premature-second-w-batch', overwrite))
    wrong_stride = list(words)
    footer = [i for i in range(58, 103) if words[i] == 0x02058593]
    need(len(footer) == 1, 'unique +32 X footer mutation')
    wrong_stride[footer[0]] = 0x01058593
    changes.append(('old-plus16-x-footer', wrong_stride))
    fixture = helpers.fixtures(repo / PARENT / 'generate.py')
    golden = helpers.python_golden(fixture, 0)
    cls = checker_class(repo, model, old)
    results = []
    for name, mutated in changes:
        raw = bytearray(elf.raw)
        raw[offset:offset + len(body)] = struct.pack('<103I', *mutated)
        need(raw != elf.raw and len(raw) == len(elf.raw), 'nonempty same-size actual ELF mutation')
        (out / (name + '.elf')).write_bytes(raw)
        mutant, errors = model.ELF(raw), {}
        try:
            certificate(mutant)
        except ValueError as error:
            errors['symbolic'] = str(error)
        else:
            raise ValueError('symbolic mutant accepted ' + name)
        machine = cls(fixture)
        machine.execute_function(mutant, generate.NAME)
        need(machine.counts['ret'] == 1, 'mutant reaches ordinary return, not unsupported opcode')
        try:
            machine.check(golden)
        except ValueError as error:
            errors['numeric'] = str(error)
        else:
            raise ValueError('numeric mutant accepted ' + name)
        need(errors['numeric'] == 'whole2 actual full-Q bitwise output', 'semantic output rejection')
        results.append(dict(name=name, elf_sha256=sha(raw),
                            changed_word_indices=[i for i, (a, b) in enumerate(zip(words, mutated)) if a != b],
                            complete_return=True, instructions=len(machine.path),
                            output_sha256=sha(machine.regions['y']), rejections=errors))
    result = dict(status='WHOLE2_THREE_ACTUAL_ELF_MUTANTS_REJECTED', controls=results)
    save(out / 'result.json', result)
    return result


def screen(repo, out):
    need(not out.exists() and not out.is_relative_to(repo), 'fresh external output')
    out.mkdir(parents=True)
    result = dict(status='RUNNING', contract=generate.CONTRACT, started=now(),
                  target_runtime_qualified=False, performance_qualified=False, new_emu_runs=0,
                  cpu_affinity=sorted(os.sched_getaffinity(0)))
    sources = [repo / PARENT / n for n in ('generate.py', 'oracle.c', 'q288.h')]
    sources += [repo / PARENT.parent / 'caller.h', repo / PARENT.parent / 'split/split.h',
                repo / 'team/optimizations/o2/r2-config-reuse/public/gemv.S',
                repo / 'team/optimizations/o2/r2-safe-tail/machine_model.py']
    sources += [repo / generate.FUSED / n for n in
                ('generate.py', 'model.py', 'screen.py', 'phased/candidate.py', 'phased/tail/candidate.py')]
    sources += [repo / generate.OLD / n for n in ('candidate.py', 'screen.py', 'CONTRACT.md')]
    sources += [HERE / n for n in ('generate.py', 'screen.py', 'CONTRACT.md')]
    pins = {}
    try:
        for path in sources:
            raw = path.read_bytes()
            pins[str(path)] = sha(raw)
            destination = out / 'source-snapshot' / path.relative_to(repo)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        need(all(sha(Path(p).read_bytes()) == h for p, h in pins.items()), 'stable input snapshot')
        model, helpers, old = support(repo)
        generation = generate.generate(repo, out / 'generated')
        gcc = shutil.which('riscv64-linux-gnu-gcc')
        need(gcc, 'GNU RISC-V assembler and linker')
        prefix = [gcc, '-march=rv64gv', '-mabi=lp64d', '-mno-relax']
        commands = []
        for source, stem, entry in (('retained-dot16.S', 'retained', 'q288_dot16_vdot'),
                                     ('whole2.S', 'whole2', generate.NAME)):
            commands.append(helpers.command(prefix + ['-c', out / 'generated' / source,
                                                     '-o', out / (stem + '.o')], out, len(commands)))
            commands.append(helpers.command(prefix + ['-static', '-no-pie', '-nostdlib', '-nostartfiles',
                '-Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,' + entry,
                out / (stem + '.o'), '-o', out / (stem + '.elf')], out, len(commands)))
        elf = model.ELF((out / 'whole2.elf').read_bytes())
        retained = model.ELF((out / 'retained.elf').read_bytes())
        for name in generation['retained']:
            need(elf.symbol_data(name) == retained.symbol_data(name), 'unchanged retained function ' + name)
        prior_proof = old.certificate(elf)
        save(out / 'retained-dot16-certificate.json', prior_proof)
        proof = certificate(elf)
        save(out / 'certificate.json', proof)
        values = numeric(repo, out / 'numeric', elf, model, helpers, old)
        negative = controls(repo, out / 'controls', elf, model, helpers, old)
        need(all(sha(Path(p).read_bytes()) == h for p, h in pins.items()), 'all sources unchanged during screen')
        symbols = {name: dict(bytes=len(elf.symbol_data(name)), sha256=sha(elf.symbol_data(name)))
                   for name in generation['retained'] + [generate.NAME]}
        result.update(status='WHOLE2_ACTUAL_ELF_SCREEN_PASS', source_files=pins, generation=generation,
                      commands=commands, compiler_sha256=sha(Path(gcc).read_bytes()), elf_sha256=sha(elf.raw),
                      retained_elf_sha256=sha(retained.raw), retained_functions_identical=True,
                      symbols=symbols, certificate=proof, numeric_cases=len(values['cases']),
                      rejected_mutants=len(negative['controls']), instructions_per_function=21090)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), source_files=pins)
        raise
    finally:
        result['finished'] = now()
        save(out / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:1])
    print(json.dumps(screen(args.repo.resolve(), args.output.resolve()), indent=2))
