"""Actual-ELF value/address screen for dot16, with unchanged dot8/RVV symbols.

This finite host model is not NEMU, an exception model, RTL, or a cycle model.
The scalar dot16 oracle and symbolic address proof do not call the generator's
core construction. Frozen FP, ELF and memory support are reused by identity.
"""
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json
import os
import shutil
import struct
import sys

import candidate

HERE = Path(__file__).resolve().parent
PARENT = candidate.FUSED.parent
need = candidate.need
sha = candidate.sha
MODEL_SHA = '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82'
HELPERS_SHA = '39bfbe63942d15ad5bee4e32e08153c2edf56cc8ce2058f74c199550f16cf5ae'


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def support(repo):
    base = repo / candidate.FUSED
    generator = candidate.load('dot16_frozen_generator', base / 'generate.py', candidate.FUSED_GEN_SHA)
    model = candidate.load('dot16_frozen_model', base / 'model.py', MODEL_SHA)
    previous = {name: sys.modules.get(name) for name in ('generate', 'model')}
    sys.modules.update(generate=generator, model=model)
    try:
        helpers = candidate.load('dot16_frozen_helpers', base / 'screen.py', HELPERS_SHA)
    finally:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return model, helpers


def branch_target(word, pc):
    offset = ((word >> 31) << 12) | (((word >> 7) & 1) << 11)
    offset |= (((word >> 25) & 63) << 5) | (((word >> 8) & 15) << 1)
    return pc + (offset - 8192 if offset & 4096 else offset)


def certificate(elf):
    baseline = elf.symbol_data('q288_fused_vdot')
    body = elf.symbol_data('q288_dot16_vdot')
    need(sha(baseline) == '9a155c33b9f27ca04d68ab3e0d883d6819876db6dc1c5d6f55ba9a3faa435648',
         'unaltered original full-Q function body')
    need(len(baseline) == 800 and len(body) == 484 and body[:60] == baseline[:60],
         'exact original prefix and new function size')
    changes, targets = [], []
    old_tail = struct.unpack('<45I', baseline[620:])
    new_tail = struct.unpack('<45I', body[304:])
    for index, (old, new) in enumerate(zip(old_tail, new_tail)):
        if old == 0x02058593:
            need(new == 0x01058593, 'exact group X footer advance')
            changes.append(index)
        elif old & 0x707f == 0x1063:
            need(new & 0x01fff07f == old & 0x01fff07f, 'same branch condition')
            target = branch_target(new, 304 + 4 * index)
            need(target == branch_target(old, 620 + 4 * index), 'same logical loop target')
            targets.append(target)
        else:
            need(old == new, 'unchanged FP, ABI, stores and control suffix')
    need(len(changes) == 1 and targets == [60, 44], 'all and only suffix changes')
    pointers = {11: ('X', 0), 12: ('W', 0)}
    vectors, reads, counts, configs = {}, Counter(), Counter(), []
    mode = None

    def write(reg, value):
        need(reg not in range(8, 16), 'FP accumulator and scratch registers preserved')
        vectors[reg] = value

    for word, in struct.iter_unpack('<I', body[60:304]):
        op, f3 = word & 127, (word >> 12) & 7
        rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
        if word in (0xc4087057, 0xc1027057):
            mode = (16, 8) if word == 0xc4087057 else (4, 32)
            configs.append(mode)
            counts['vsetivli'] += 1
        elif op == 0x13 and f3 == 0:
            imm = word >> 20
            imm -= 4096 if imm & 2048 else 0
            need((rd, a, imm) == (11, 11, 16) or (rd, a) == (31, 12), 'only specified address updates')
            need(a in pointers, 'defined address source')
            region, offset = pointers[a]
            pointers[rd] = (region, offset + imm)
            counts['addi'] += 1
        elif word & 0xfff0707f == 0x02000007:
            need(mode == (16, 8) and a in pointers, 'exact 16-byte load mode/address')
            region, offset = pointers[a]
            limit = 32 if region == 'X' else 256
            need(0 <= offset <= limit - 16, 'compact input bounds')
            values = tuple((region, offset + i) for i in range(16))
            reads.update(values)
            write(rd, ('bytes', values))
            counts['vle8.v'] += 1
        elif word & 0xfe00707f == 0x0e00000b:
            need(mode == (16, 8), 'exact dot16 mode')
            need(a in vectors and b in vectors and vectors[a][0] == vectors[b][0] == 'bytes', 'defined dot16 operands')
            left, right = vectors[a][1], vectors[b][1]
            need(len(left) == len(right) == 16 and all(x[0] == 'W' and y[0] == 'X' for x, y in zip(left, right)),
                 'sixteen matching W/X source roles')
            terms = Counter((x[1] // 32, x[1] % 32, y[1]) for x, y in zip(left, right))
            write(rd, ('lanes', (terms, Counter(), Counter(), Counter())))
            counts['vdot16.vv'] += 1
        elif op == 0x57 and word >> 26 == 0 and f3 == 0 and (word >> 25) & 1:
            need(mode == (4, 32), 'four-lane exact integer sum')
            need(a in vectors and b in vectors and vectors[a][0] == vectors[b][0] == 'lanes', 'defined partial sums')
            lanes = tuple(x + y for x, y in zip(vectors[a][1], vectors[b][1]))
            need(all(sum(lane.values()) <= 32 for lane in lanes), 'int32-safe sum of at most 32 int8 products')
            write(rd, ('lanes', lanes))
            counts['vadd.vv'] += 1
        else:
            raise ValueError('unknown dot16 core encoding ' + hex(word))
    need(configs == [(16, 8), (4, 32)], 'two exact configurations')
    need(counts == Counter(vsetivli=2, addi=17, **{'vle8.v': 18, 'vdot16.vv': 16, 'vadd.vv': 8}), 'exact core instruction counts')
    need(pointers[11] == ('X', 16) and pointers[12] == ('W', 0), 'core pointer postconditions')
    wanted = Counter({('W', i): 1 for i in range(256)})
    wanted.update({('X', i): 1 for i in range(32)})
    need(reads == wanted, 'all source bytes read exactly once per group')
    for row in range(8):
        need(vectors[row] == ('lanes', (Counter({(row, k, k): 1 for k in range(32)}), Counter(), Counter(), Counter())),
             'every matching row product exactly once and high96 zero')
    return dict(status='DOT16_ACTUAL_WORD_CERTIFICATE_PASS', core_words=61, core_sha256=sha(body[60:304]),
                counts=dict(counts), modes=configs, gs32_sum_min=-520192, gs32_sum_max=524288,
                prefix_bytes=60, suffix_words=45, logical_loop_targets=targets,
                x_core_advance=16, x_footer_advance=16, high96_zero=True, layout_unchanged=True)


def checker_class(model, machine_path):
    full = model.machine_class(machine_path)
    integer = full.__mro__[1]

    class Dot16Hook(integer):
        def execute(self, code):
            need(len(code) > 0 and len(code) % 4 == 0, 'whole machine words')
            for word, in struct.iter_unpack('<I', code):
                if word & 0xfe00707f != 0x0e00000b:
                    super().execute(struct.pack('<I', word))
                    continue
                need((self.vl, self.sew, self.lmul, self.vstart) == (16, 8, 1, 0), 'illegal modeled dot16 configuration')
                rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
                left, right = self.get(a, 16), self.get(b, 16)
                value = sum((x - 256 if x >= 128 else x) * (y - 256 if y >= 128 else y) for x, y in zip(left, right))
                self.v[rd][:] = struct.pack('<I', value & 0xffffffff) + bytes(12)
                self.counts['vdot16.vv'] += 1
            return self

    class Dot16(full, Dot16Hook):
        def check(self, golden):
            begin, length = self.function_begin + 60, 61
            expected = [(begin + 4 * i, self.function_words[begin + 4 * i]) for i in range(length)]
            starts = [i for i, (pc, _) in enumerate(self.path) if pc == begin]
            need(len(starts) == 324 and all(self.path[i:i + length] == expected for i in starts)
                 and sum(begin <= pc < begin + 4 * length for pc, _ in self.path) == 324 * length,
                 '324 complete dynamically executed dot16 cores')
            need(self.regions['y'] == struct.pack('<288I', *golden), 'actual dot16 full-Q bitwise output')
            f, d = self.fixture, self.dataset
            dots = [sum(f['weight'][r * 288 + k] * f['inputs'][d][k] for k in range(256, 288)) for r in range(280, 288)]
            slots = b''.join(struct.pack('<I', value & 0xffffffff) + bytes(12) for value in dots)
            need(self.regions['slots'] == slots, 'complete final eight slots')
            need(all(bytes(self.regions[n]) == raw for n, raw in self.original.items() if n not in ('y', 'slots')), 'all inputs and context unchanged')
            reads = Counter()
            for name, size, times in (('packed', 82944, 1), ('x', 288, 36), ('ws', 10368, 1), ('xs', 36, 36), ('context', 48, 1)):
                reads.update({(name, i): times for i in range(size)})
            need(self.read_bytes_count == reads, 'complete exact input footprint')
            writes = Counter({(name, i): 1 for name, size in (('y', 1152), ('slots', 128)) for i in range(size)})
            need(self.write_bytes_count == writes, 'complete exact output footprint')
            need(all(self.x[i] == v for i, v in self.saved.items()) and all(self.f[i] == v for i, v in self.saved_fp.items()), 'scalar and FP ABI')
            self.mode(8, 8, 1)
            need(self.vcsr == 7 and self.frm == 0, 'final CSR and rounding mode')
            need(self.fp_counts == Counter(convert=2592, mul=5184, add=2592), 'unchanged strict FP operations')
            need(self.counts['vdot16.vv'] == 5184 and self.counts['vdot.vv'] == 0 and self.counts['vadd.vv'] == 2592,
                 'distinct dot16/dot8 and add counts')
            need(self.counts['vs1r.v'] == 8 and self.counts['vse32.v'] == 36 and self.counts['ret'] == 1, 'complete output and return counts')
            need(len(self.path) == 26922, 'actual complete function instruction count')
            return dict(instructions=len(self.path), counts=dict(self.counts), fp_element_operations=dict(self.fp_counts),
                        output_sha256=sha(self.regions['y']), final_slots_sha256=sha(self.regions['slots']),
                        core_executions=324, core_words=61, exact_footprints=True, abi_preserved=True, stack_used_bytes=0)

    need(Dot16.__mro__[:4] == (Dot16, full, Dot16Hook, integer), 'lexical FullQ super dispatch reaches the new hook')
    return Dot16


def numeric(repo, out, elf, model, helpers):
    out.mkdir()
    headers = {'q288.h': repo / PARENT / 'q288.h', 'caller.h': repo / PARENT.parent / 'caller.h',
               'split.h': repo / PARENT.parent / 'split/split.h'}
    library = helpers.oracle_library(repo / PARENT / 'oracle.c', headers, out / 'oracle')
    fixture = helpers.fixtures(repo / PARENT / 'generate.py')
    cases = [('x' + str(d), fixture, d) for d in (0, 1, 0, 2)]
    for name, w, x in (('min-min', [-128] * 82944, [-128] * 288), ('max-max', [127] * 82944, [127] * 288),
                       ('min-max', [-128] * 82944, [127] * 288), ('zero-weight', [0] * 82944, fixture['inputs'][0])):
        f = copy.deepcopy(fixture)
        f['weight'], f['inputs'][0] = w, x
        f['packed'] = [w[(8 * t + r) * 288 + g * 32 + k] for t in range(36) for g in range(9) for r in range(8) for k in range(32)]
        cases.append((name, f, 0))
    cls = checker_class(model, repo / 'team/optimizations/o2/r2-safe-tail/machine_model.py')
    results, previous = [], None
    for index, (name, f, d) in enumerate(cases):
        golden = helpers.native_golden(library, f, d)
        need(golden == helpers.python_golden(f, d), 'independent native C and Python FP reference agreement')
        if index < 4:
            need(golden == f['golden'][d], 'frozen fixture golden')
        if index == 0:
            need(golden[0] == 0, 'strict FMA rounding witness')
        align = (0, 0) if index < 4 else ((index * 3) % 16, (index * 7) % 16)
        machine = cls(f, d, poison=0xd1600 + index, alignment=align)
        if index in (1, 2, 3):
            need(machine.regions['packed'] == previous.regions['packed'], 'same reusable packed weight object')
            machine.regions['packed'] = previous.regions['packed']
            machine.v = [bytearray(v) for v in previous.v]
        machine.execute_function(elf, 'q288_dot16_vdot')
        results.append(dict(case=name, dataset=d, alignment=align, **machine.check(golden)))
        previous = machine
    result = dict(status='DOT16_ACTUAL_ELF_NUMERIC_PASS', cases=results)
    save(out / 'result.json', result)
    return result


def controls(repo, out, elf, model, helpers):
    out.mkdir()
    body = elf.symbol_data('q288_dot16_vdot')
    _, _, offset = elf.symbols['q288_dot16_vdot']
    words = list(struct.unpack('<121I', body))
    core = list(enumerate(words[15:76], 15))
    changes = []
    i, w = next((i, w) for i, w in core if w & 0xfe00707f == 0x0e00000b)
    changes.append(('wrong-x-half', i, (w & ~(31 << 20)) | (17 << 20)))
    changes.append(('old-dot8-opcode', i, w ^ 0x0c000000))
    i, w = next((i, w) for i, w in core if w & 0xfffff == 0x60f93)
    changes.append(('wrong-weight-row', i, w + (32 << 20)))
    i, w = next((i, w) for i, w in core if w & 127 == 0x57 and w >> 26 == 0 and (w >> 12) & 7 == 0)
    changes.append(('wrong-partial-reduction', i, (w & ~(31 << 15)) | (1 << 15)))
    i, w = next((i, w) for i, w in core if w == 0xc1027057)
    changes.append(('vl1-breaks-full-slot-packing', i, (w & ~(31 << 15)) | (1 << 15)))
    fixture = helpers.fixtures(repo / PARENT / 'generate.py')
    golden = helpers.python_golden(fixture, 0)
    cls = checker_class(model, repo / 'team/optimizations/o2/r2-safe-tail/machine_model.py')
    results = []
    for name, index, word in changes:
        raw = bytearray(elf.raw)
        struct.pack_into('<I', raw, offset + 4 * index, word)
        need(raw != elf.raw, 'nonempty actual ELF mutation')
        (out / (name + '.elf')).write_bytes(raw)
        mutant, errors = model.ELF(raw), {}
        try:
            certificate(mutant)
        except ValueError as error:
            errors['symbolic'] = str(error)
        else:
            raise ValueError('symbolic mutant accepted ' + name)
        try:
            machine = cls(fixture)
            machine.execute_function(mutant, 'q288_dot16_vdot')
            machine.check(golden)
        except ValueError as error:
            errors['numeric'] = str(error)
        else:
            raise ValueError('numeric mutant accepted ' + name)
        results.append(dict(name=name, word_index=index, elf_sha256=sha(raw), rejections=errors))
    result = dict(status='DOT16_ACTUAL_ELF_MUTANTS_REJECTED', controls=results)
    save(out / 'result.json', result)
    return result


def screen(repo, out):
    need(not out.exists() and not out.is_relative_to(repo), 'fresh external output')
    out.mkdir(parents=True)
    result = dict(status='RUNNING', contract=candidate.CONTRACT, started=now(),
                  target_runtime_qualified=False, performance_qualified=False, new_emu_runs=0)
    sources = [repo / PARENT / n for n in ('generate.py', 'oracle.c', 'q288.h')]
    sources += [repo / PARENT.parent / 'caller.h', repo / PARENT.parent / 'split/split.h', repo / candidate.PUBLIC,
                repo / 'team/optimizations/o2/r2-safe-tail/machine_model.py']
    sources += [repo / candidate.FUSED / n for n in ('generate.py', 'model.py', 'screen.py', 'phased/candidate.py', 'phased/tail/candidate.py')]
    sources += [HERE / n for n in ('candidate.py', 'screen.py', 'CONTRACT.md')]
    pins = {}
    try:
        for path in sources:
            raw = path.read_bytes()
            pins[str(path)] = sha(raw)
            target = out / 'source-snapshot' / path.relative_to(repo)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        need(all(sha(Path(p).read_bytes()) == h for p, h in pins.items()), 'stable source snapshot')
        model, helpers = support(repo)
        generation = candidate.generate(repo, out / 'generated')
        gcc = shutil.which('riscv64-linux-gnu-gcc')
        need(gcc, 'GNU RISC-V assembler and linker')
        prefix = [gcc, '-march=rv64gv', '-mabi=lp64d', '-mno-relax']
        commands = [helpers.command(prefix + ['-c', out / 'generated/dot16.S', '-o', out / 'dot16.o'], out, 0)]
        commands.append(helpers.command(prefix + ['-static', '-no-pie', '-nostdlib', '-nostartfiles',
            '-Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,q288_dot16_vdot', out / 'dot16.o', '-o', out / 'dot16.elf'], out, 1))
        elf = model.ELF((out / 'dot16.elf').read_bytes())
        proof = certificate(elf)
        save(out / 'certificate.json', proof)
        values = numeric(repo, out / 'numeric', elf, model, helpers)
        negative = controls(repo, out / 'controls', elf, model, helpers)
        need(all(sha(Path(p).read_bytes()) == h for p, h in pins.items()), 'all sources unchanged during screen')
        symbols = {n: dict(bytes=len(elf.symbol_data(n)), sha256=sha(elf.symbol_data(n)))
                   for n in generation['retained'] + [candidate.NAME]}
        result.update(status='DOT16_ACTUAL_ELF_SCREEN_PASS', source_files=pins, generation=generation,
                      commands=commands, compiler_sha256=sha(Path(gcc).read_bytes()), elf_sha256=sha(elf.raw),
                      symbols=symbols, certificate=proof, numeric_cases=len(values['cases']),
                      rejected_mutants=len(negative['controls']), instructions_per_function=26922)
    except BaseException as error:
        result.update(status='FAILED', error=repr(error), source_files=pins)
        raise
    finally:
        result['finished'] = now()
        save(out / 'result.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:1])
    print(json.dumps(screen(a.repo.resolve(), a.output.resolve()), indent=2))
