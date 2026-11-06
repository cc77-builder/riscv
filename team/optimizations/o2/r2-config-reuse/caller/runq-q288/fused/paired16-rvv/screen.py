"""Actual-ELF paired16 numeric/address screen; not a CPU or cycle model."""
from collections import Counter
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import struct
import sys

import generate

need = generate.need
sha = generate.sha


def load(name, path, pin):
    need(sha(path.read_bytes()) == pin, 'unchanged support: '+str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def support(repo):
    parent, _ = generate.load_parent(repo)
    path = repo/generate.REL
    model = load('paired16_fixed_fp_model', path/'model.py',
                 '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82')
    saved = {name:sys.modules.get(name) for name in ('generate', 'model')}
    sys.modules.update(generate=parent, model=model)
    try:
        helpers = load('paired16_fixed_oracle_helpers', path/'screen.py',
                       '39bfbe63942d15ad5bee4e32e08153c2edf56cc8ce2058f74c199550f16cf5ae')
    finally:
        for name, value in saved.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return model, helpers


def certificate(elf):
    def interval(first, last):
        a, _, offset = elf.symbols[first]
        b = elf.symbols[last][0]
        need(b >= a, 'ordered ELF interval')
        return elf.raw[offset:offset+b-a]
    fallback = interval(generate.NAME+'_fallback_begin', generate.NAME+'_fallback_end')
    original = elf.symbol_data('q288_fused_rvv4')
    need(fallback == original, 'fallback actual machine body equals retained FR')
    core = interval(generate.NAME+'_core_begin', generate.NAME+'_core_end')
    need(len(core) == generate.CORE_WORDS*4, 'actual 45-word fast core')
    fallback_core = interval(generate.NAME+'_fallback_core_begin', generate.NAME+'_fallback_core_end')
    need(len(fallback_core) == 87*4 and fallback_core == original[60:60+87*4],
         'actual unchanged 87-word fallback core')
    after = interval(generate.NAME+'_core_end', generate.NAME+'_fast_end')
    def normalized(raw):
        # BNE immediate offsets change with the replaced integer core.
        return [w & 0x01fff07f if w & 127 == 0x63 else w
                for w, in struct.iter_unpack('<I', raw)]
    need(normalized(after) == normalized(original[60+87*4:]),
         'unchanged FP consumer/footer except relative loop displacements')
    return dict(fallback_bytes=len(fallback), fallback_sha256=sha(fallback),
                core_bytes=len(core), core_sha256=sha(core), fp_footer_sha256=sha(after))


def machine_class(repo, model):
    full = model.machine_class(repo/'team/optimizations/o2/r2-safe-tail/machine_model.py')
    old_integer = full.__bases__[0]

    class PairedInteger(old_integer):
        def execute(self, code):
            need(code and len(code) % 4 == 0, 'fixed-width instruction words')
            for word, in struct.iter_unpack('<I', code):
                op, f3, f6 = word & 127, (word >> 12) & 7, word >> 26
                rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
                label = None
                if op == 0x57 and f3 == 7 and word >> 31 == 0:
                    vt = (word >> 20) & 2047
                    need(vt == 1 and a != 0 and self.x[a] == 32,
                         'guard exact e8m2 register-AVL32')
                    self.vl, self.sew, self.lmul, self.ta, self.ma, self.vstart = 32, 8, 2, 0, 0, 0
                    self.write_x(rd, 32)
                    label = 'vsetvli'
                elif op == 7 and word & 0xfff0707f == 0x02000007 and self.lmul == 2:
                    self.mode(32, 8, 2)
                    need(rd % 2 == 0 and rd <= 30, 'guard aligned m2 load group')
                    self.put(rd, self.read(self.x[a], 32), 32)
                    label = 'vle8.v'
                elif op == 7 and word & 0xfff0707f == 0x22800007:
                    self.mode(16, 8, 1)
                    need(rd % 2 == 0 and rd <= 30, 'whole-two aligned register group')
                    self.put(rd, self.read(self.x[a], 32), 32)
                    label = 'vl2re8.v'
                elif op == 0x57 and (word >> 25) & 1 and (f6, f3) == (0x1b, 4):
                    self.mode(32, 8, 2)
                    need(b % 2 == 0 and b <= 30 and rd not in (b, b+1),
                         'guard compare source and mask groups')
                    scalar = model.signed(self.x[a], 8)
                    mask = sum((model.signed(v, 8) < scalar) << i
                               for i, v in enumerate(self.get(b, 32)))
                    # Mask destinations have agnostic tails: choose legal all ones.
                    self.v[rd][:] = mask.to_bytes(4, 'little')+bytes([255])*12
                    label = 'vmslt.vx'
                elif op == 0x57 and (word >> 25) & 1 and (f6, f3, a) == (0x10, 2, 16):
                    self.mode(32, 8, 2)
                    mask = int.from_bytes(self.get(b, 16), 'little') & ((1 << 32)-1)
                    self.write_x(rd, mask.bit_count())
                    label = 'vcpop.m'
                elif op == 0x57 and (word >> 25) & 1 and (f6, f3) == (0x3d, 2):
                    self.mode(16, 8, 1)
                    need(rd % 2 == 0 and rd <= 30 and a not in (rd, rd+1) and b not in (rd, rd+1),
                         'paired widening MAC groups do not overlap')
                    old = struct.unpack('<16h', self.get(rd, 32))
                    exact = [z+model.signed(x, 8)*model.signed(y, 8)
                             for z, x, y in zip(old, self.get(a, 16), self.get(b, 16))]
                    self.wrapped_lanes += sum(not -32768 <= value <= 32767 for value in exact)
                    self.put(rd, struct.pack('<16H', *(value & 65535 for value in exact)), 32)
                    label = 'vwmacc.vv'
                else:
                    super().execute(struct.pack('<I', word))
                if label:
                    self.counts[label] += 1
            return self

    class Paired(full, PairedInteger):
        def execute_function(self, elf, name):
            self.elf, self.wrapped_lanes = elf, 0
            return super().execute_function(elf, name)

        def check_candidate(self, golden):
            # Numeric checks precede dispatch/path assertions intentionally:
            # a disabled guard must execute wraparound and fail the oracle.
            need(self.regions['y'] == struct.pack('<288I', *golden), 'paired16 full-Q bitwise output')
            f, d = self.fixture, self.dataset
            dots = [sum(f['weight'][row*288+k]*f['inputs'][d][k] for k in range(256, 288))
                    for row in range(280, 288)]
            slots = b''.join(struct.pack('<I', value & 0xffffffff)+bytes(12) for value in dots)
            need(self.regions['slots'] == slots, 'paired16 complete final slots')
            fallback = -128 in f['inputs'][d]
            selected = '_fallback_core_' if fallback else '_core_'
            other = '_core_' if fallback else '_fallback_core_'
            begin = self.elf.symbols[generate.NAME+selected+'begin'][0]
            end = self.elf.symbols[generate.NAME+selected+'end'][0]
            other_begin = self.elf.symbols[generate.NAME+other+'begin'][0]
            other_end = self.elf.symbols[generate.NAME+other+'end'][0]
            count = 87 if fallback else generate.CORE_WORDS
            expected = [(pc, self.function_words[pc]) for pc in range(begin, end, 4)]
            starts = [i for i, (pc, _) in enumerate(self.path) if pc == begin]
            need(len(expected) == count and len(starts) == 324
                 and all(self.path[i:i+count] == expected for i in starts)
                 and sum(begin <= pc < end for pc, _ in self.path) == 324*count
                 and not any(other_begin <= pc < other_end for pc, _ in self.path), 'paired16 complete selected path')
            guard = self.elf.symbols[generate.NAME+'_guard_loop'][0]
            dispatch = self.elf.symbols[generate.NAME+'_guard_dispatch'][0]
            need(sum(pc == guard for pc, _ in self.path) == 9, 'paired16 nine complete guard chunks')
            need(sum(pc == dispatch for pc, _ in self.path) == 1, 'paired16 single guarded dispatch')
            need(all(bytes(self.regions[n]) == raw for n, raw in self.original.items()
                     if n not in ('y', 'slots')), 'paired16 readonly input/context')
            reads = Counter()
            for name, size, times in (('packed',82944,1), ('x',288,37), ('ws',10368,1),
                                      ('xs',36,36), ('context',48,1)):
                reads.update({(name, i):times for i in range(size)})
            reads.update({('context', i):1 for i in range(8, 16)})
            need(self.read_bytes_count == reads, 'paired16 exact guarded input footprint')
            writes = Counter({(n, i):1 for n, size in (('y',1152), ('slots',128)) for i in range(size)})
            need(self.write_bytes_count == writes, 'paired16 exact output footprint')
            need(all(self.x[i] == value for i, value in self.saved.items())
                 and all(self.f[i] == value for i, value in self.saved_fp.items()), 'paired16 scalar/FP ABI')
            self.mode(8, 8, 1)
            need(self.vcsr == 7 and self.frm == 0, 'paired16 exit CSR/rounding')
            need(self.fp_counts == Counter(convert=2592,mul=5184,add=2592), 'paired16 strict FP operation counts')
            need(self.counts.get('vdot.vv', 0) == 0
                 and self.counts['vwmul.vv'] == (5184 if fallback else 2592)
                 and self.counts['vwredsum.vs'] == (5184 if fallback else 2592)
                 and self.counts.get('vwmacc.vv', 0) == (0 if fallback else 2592)
                 and self.counts.get('vl2re8.v', 0) == (0 if fallback else 2916), 'paired16 exact arithmetic counts')
            need(self.counts['vmslt.vx'] == self.counts['vcpop.m'] == self.counts['addw'] == 9,
                 'paired16 guard opcode counts')
            need(self.wrapped_lanes == 0, 'accepted paired path has no wrapped product sums')
            need(self.counts['vs1r.v'] == 8 and self.counts['vse32.v'] == 36 and self.counts['ret'] == 1,
                 'paired16 complete stores and ordinary return')
            return dict(function_instructions=len(self.path), path='fallback' if fallback else 'fast',
                        counts=dict(self.counts), output_sha256=sha(self.regions['y']),
                        slots_sha256=sha(self.regions['slots']), exact_footprints=True,
                        abi_preserved=True, stack_used_bytes=0, wrapped_lanes=self.wrapped_lanes)

    return Paired, full


def constant_case(base, w, x):
    fixture = copy.deepcopy(base)
    fixture['weight'] = [w]*82944
    fixture['packed'] = [w]*82944
    fixture['inputs'][0] = [x]*288
    return fixture


def numeric(repo, elf, model, helpers, out):
    q = repo/generate.REL.parent
    headers = {'q288.h':q/'q288.h', 'caller.h':q.parent/'caller.h', 'split.h':q.parent/'split/split.h'}
    lib = helpers.oracle_library(q/'oracle.c', headers, out/'oracle')
    primitives = helpers.fp_primitive_checks(lib)
    base = helpers.fixtures(q/'generate.py')
    cases = [('x'+str(d), base, d) for d in (0, 1, 0, 2)]
    for name, w, x in (('min-min',-128,-128), ('max-max',127,127), ('min-max',-128,127),
                       ('max-min',127,-128), ('min-neg127',-128,-127), ('zero-weight',0,73)):
        cases.append((name, constant_case(base, w, x), 0))
    for position in (0, 15, 16, 31, 32, 255, 256, 287):
        fixture = constant_case(base, -128, 127)
        fixture['inputs'][0][position] = -128
        cases.append(('guard-at-'+str(position), fixture, 0))
    last_pair = constant_case(base, -128, 127)
    last_pair['inputs'][0][271] = last_pair['inputs'][0][287] = -128
    cases.append(('guard-last-overflow-pair', last_pair, 0))
    candidate, baseline = machine_class(repo, model)
    previous, records = {}, []
    for i, (label, fixture, dataset) in enumerate(cases):
        golden = helpers.native_golden(lib, fixture, dataset)
        need(golden == helpers.python_golden(fixture, dataset), 'independent C/Python full-Q golden')
        if i < 4:
            need(golden == fixture['golden'][dataset], 'unchanged frozen fixture golden')
        if i == 0:
            need(golden[0] == 0, 'strict FP FMA witness')
        row = dict(index=i, case=label, dataset=dataset, methods={})
        for kind, cls, symbol in (('paired16',candidate,generate.NAME), ('fr',baseline,'q288_fused_rvv4')):
            alignment = (0, 0) if i < 4 else ((i*3) % 16, (i*7) % 16)
            machine = cls(fixture, dataset, poison=0x161600+i, alignment=alignment)
            if 0 < i < 4:
                machine.regions['packed'] = previous[kind].regions['packed']
                machine.v = [bytearray(v) for v in previous[kind].v]
            machine.execute_function(elf, symbol)
            result = machine.check_candidate(golden) if kind == 'paired16' else machine.check_full('rvv4', golden)
            row['methods'][kind] = dict(result, byte_alignment=alignment)
            previous[kind] = machine
        records.append(row)
    return dict(cases=records, fp_primitive_checks=primitives)


def controls(repo, elf, model, helpers, out):
    out.mkdir()
    base = helpers.fixtures(repo/generate.REL.parent/'generate.py')
    cls, _ = machine_class(repo, model)
    begin, _, offset = elf.symbols[generate.NAME]
    words = [w for w, in struct.iter_unpack('<I', elf.symbol_data(generate.NAME))]
    at_symbol = lambda suffix:(elf.symbols[generate.NAME+suffix][0]-begin)//4
    core = at_symbol('_core_begin')
    dispatch = at_symbol('_guard_dispatch')
    last_pair = constant_case(base, -128, 127)
    last_pair['inputs'][0][271] = last_pair['inputs'][0][287] = -128
    # These mutants must reach RET and fail output, rather than be rejected
    # by a convenient domain/path assertion before doing the bad arithmetic.
    mutants = [
        ('guard-disabled-overflow', [(dispatch,0x00000013)], constant_case(base,-128,-128), 'paired16 full-Q bitwise output'),
        ('guard-misses-last-group', [(3,0x00800313)], last_pair, 'paired16 full-Q bitwise output'),
        ('missing-shared-seed-clear', [(core+1,0x00000013)], base, 'paired16 full-Q bitwise output'),
    ]
    macc = next(i for i in range(core, core+generate.CORE_WORDS)
                if words[i] & 127 == 0x57 and words[i] >> 26 == 0x3d)
    mutants.append(('wrong-second-half-x', [(macc,(words[macc] & ~(31 << 20)) | (14 << 20))],
                    base, 'paired16 full-Q bitwise output'))
    init = next(i for i in range(at_symbol('_fast_begin'), core)
                if words[i] & 0xfff0707f == 0x5e003057 and (words[i] >> 7) & 31 == 2)
    mutants.append(('missing-entry-high96-clear', [(init,0x00000013)], base, 'paired16 complete final slots'))
    mul = next(i for i in range(at_symbol('_core_end'), at_symbol('_fast_end'))
               if words[i] & 127 == 0x57 and words[i] >> 26 == 0x24 and (words[i] >> 12) & 7 == 1)
    mutants.append(('wrong-fp-scale-order', [(mul,words[mul+1]),(mul+1,words[mul+2]),(mul+2,words[mul])],
                    base, 'paired16 full-Q bitwise output'))
    records = []
    for index, (name, changes, fixture, expected_error) in enumerate(mutants):
        raw = bytearray(elf.raw)
        for at, word in changes:
            struct.pack_into('<I', raw, offset+4*at, word)
        (out/(name+'.elf')).write_bytes(raw)
        golden = helpers.python_golden(fixture, 0)
        machine = cls(fixture, 0, poison=0x1616f0+index)
        try:
            machine.execute_function(model.ELF(bytes(raw)), generate.NAME).check_candidate(golden)
        except ValueError as error:
            need(str(error) == expected_error and machine.counts['ret'] == 1,
                 'mutant must return then fail the intended numeric/slot oracle: '+name+': '+str(error))
            if 'overflow' in name or 'last-group' in name:
                need(machine.wrapped_lanes > 0, 'overflow mutant actually wrapped s16 lanes')
            actual = struct.unpack('<288I', machine.regions['y'])
            mismatch = next((dict(row=i, expected=f'0x{want:08x}', actual=f'0x{got:08x}')
                             for i, (want, got) in enumerate(zip(golden, actual)) if want != got), None)
            records.append(dict(case=name, mutant_sha256=sha(raw), rejection=str(error),
                                returned=True, wrapped_lanes=machine.wrapped_lanes,
                                instructions=len(machine.path), first_output_mismatch=mismatch,
                                actual_output_sha256=sha(machine.regions['y']),
                                expected_output_sha256=sha(struct.pack('<288I', *golden))))
        else:
            raise ValueError('actual ELF mutant accepted: '+name)
    return records


def run(repo, elf_path, out):
    need(not out.exists(), 'fresh independent screen output')
    out.mkdir(parents=True)
    model, helpers = support(repo)
    elf = model.ELF(elf_path.read_bytes())
    result = dict(contract=generate.CONTRACT, elf_sha256=sha(elf.raw),
                  certificate=certificate(elf), numeric=numeric(repo, elf, model, helpers, out),
                  controls=controls(repo, elf, model, helpers, out/'negative-controls'),
                  status='PAIRED16_ACTUAL_ELF_NUMERIC_PASS', new_emu_runs=0,
                  target_runtime_qualified=False, performance_qualified=False)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--elf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    result = run(args.repo.resolve(), args.elf.resolve(), args.output.resolve())
    first = result['numeric']['cases'][0]['methods']
    print(json.dumps(dict(status=result['status'], elf_sha256=result['elf_sha256'],
                         cases=len(result['numeric']['cases']), controls=len(result['controls']),
                         instructions={key:value['function_instructions'] for key,value in first.items()},
                         target_runtime_qualified=False, performance_qualified=False), indent=2))
