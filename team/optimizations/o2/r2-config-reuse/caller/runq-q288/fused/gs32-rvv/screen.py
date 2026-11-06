"""Check a real GS32 ELF using pinned FP/oracle support and bounded new RVV semantics.

This is a finite architectural value/address screen, never a cycle model or
target correctness claim. Existing model/checker source files remain unchanged.
"""
from collections import Counter
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import struct
import sys

import generate

need = generate.need


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, path, pin):
    need(sha(path.read_bytes()) == pin, 'unchanged support: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def support(repo):
    parent, _ = generate.load_parent(repo)
    path = repo / generate.REL
    model = load('gs32_pinned_fp_model', path / 'model.py',
                 '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82')
    # Resolve the old helper's ordinary imports to its own pinned dependencies.
    saved = {key: sys.modules.get(key) for key in ('generate', 'model')}
    sys.modules.update(generate=parent, model=model)
    try:
        helpers = load('gs32_pinned_oracle_helpers', path / 'screen.py',
                       '39bfbe63942d15ad5bee4e32e08153c2edf56cc8ce2058f74c199550f16cf5ae')
    finally:
        for key, value in saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value
    return model, helpers


def machine_class(repo, model):
    full = model.machine_class(repo / 'team/optimizations/o2/r2-safe-tail/machine_model.py')
    old_integer = full.__bases__[0]

    class WiderInteger(old_integer):
        def execute(self, code):
            need(len(code) > 0 and len(code) % 4 == 0, 'fixed-width instruction words')
            for word, in struct.iter_unpack('<I', code):
                op, f3, f6 = word & 127, (word >> 12) & 7, word >> 26
                rd, a, b = (word >> 7) & 31, (word >> 15) & 31, (word >> 20) & 31
                label = None
                if op == 0x57 and f3 == 7 and word >> 31 == 0:
                    vt = (word >> 20) & 2047
                    need(vt in (1, 10) and a != 0 and self.x[a] == 32,
                         'GS32 register-AVL and exact m2/m4 modes')
                    self.sew, self.lmul = (8, 2) if vt == 1 else (16, 4)
                    self.vl, self.ta, self.ma, self.vstart = 32, 0, 0, 0
                    self.write_x(rd, 32)
                    label = 'vsetvli'
                elif op == 7 and word & 0xfff0707f == 0x02000007 and self.lmul == 2:
                    self.mode(32, 8, 2)
                    need(rd % 2 == 0 and rd <= 30, 'aligned full-width m2 load')
                    self.put(rd, self.read(self.x[a], 32), 32)
                    label = 'vle8.v'
                elif op == 0x57 and (word >> 25) & 1 and (f6, f3) == (0x3b, 2) and self.lmul == 2:
                    self.mode(32, 8, 2)
                    need(rd % 4 == 0 and rd <= 28 and a % 2 == b % 2 == 0,
                         'aligned widening multiply groups')
                    need(not (set(range(rd, rd+4)) & (set(range(a, a+2)) | set(range(b, b+2)))),
                         'disjoint widening multiply source/destination groups')
                    products = [model.signed(x, 8) * model.signed(y, 8)
                                for x, y in zip(self.get(a, 32), self.get(b, 32))]
                    self.put(rd, struct.pack('<32h', *products), 64)
                    label = 'vwmul.vv'
                elif op == 0x57 and (word >> 25) & 1 and (f6, f3) == (0x31, 0) and self.lmul == 4:
                    self.mode(32, 16, 4)
                    need(b % 4 == 0 and b <= 28, 'aligned m4 reduction source')
                    seed = int.from_bytes(self.get(a, 4), 'little', signed=True)
                    values = struct.unpack('<32h', self.get(b, 64))
                    self.put(rd, struct.pack('<I', (seed + sum(values)) & 0xffffffff), 16)
                    label = 'vwredsum.vs'
                else:
                    super().execute(struct.pack('<I', word))
                if label:
                    self.counts[label] += 1
            return self

    # Cooperative MRO inserts the new integer semantics under the pinned full-Q
    # interpreter. No patching of modules/classes or copied FP interpreter.
    class GS32(full, WiderInteger):
        def execute_function(self, elf, name):
            self.elf = elf
            return super().execute_function(elf, name)

        def check_candidate(self, golden):
            elf = self.elf
            begin = elf.symbols[generate.NAME + '_core_begin'][0]
            end = elf.symbols[generate.NAME + '_core_end'][0]
            need(end-begin == generate.CORE_WORDS*4, 'actual shared-seed core word count')
            wanted = [(pc, self.function_words[pc]) for pc in range(begin, end, 4)]
            starts = [i for i, (pc, _) in enumerate(self.path) if pc == begin]
            need(len(starts) == 324 and all(self.path[i:i+generate.CORE_WORDS] == wanted for i in starts)
                 and sum(begin <= pc < end for pc, _ in self.path) == 324*generate.CORE_WORDS,
                 '324 complete GS32 integer blocks')
            need(self.regions['y'] == struct.pack('<288I', *golden), 'GS32 full-Q bitwise output')
            f, d = self.fixture, self.dataset
            dots = [sum(f['weight'][row*288+k]*f['inputs'][d][k] for k in range(256, 288))
                    for row in range(280, 288)]
            slots = b''.join(struct.pack('<I', v & 0xffffffff)+bytes(12) for v in dots)
            need(self.regions['slots'] == slots, 'GS32 complete final slots')
            need(all(bytes(self.regions[n]) == raw for n, raw in self.original.items()
                     if n not in ('y', 'slots')), 'GS32 readonly input/context')
            reads = Counter()
            for name, size, times in (('packed',82944,1),('x',288,36),('ws',10368,1),
                                      ('xs',36,36),('context',48,1)):
                reads.update({(name, i): times for i in range(size)})
            need(self.read_bytes_count == reads, 'GS32 exact input footprint')
            writes = Counter({(n, i):1 for n, size in (('y',1152),('slots',128)) for i in range(size)})
            need(self.write_bytes_count == writes, 'GS32 exact output footprint')
            need(all(self.x[i] == v for i, v in self.saved.items()) and
                 all(self.f[i] == v for i, v in self.saved_fp.items()), 'GS32 scalar/FP ABI')
            self.mode(8, 8, 1)
            need(self.vcsr == 7 and self.frm == 0, 'GS32 exit CSR/rounding mode')
            need(self.fp_counts == Counter(convert=2592,mul=5184,add=2592), 'GS32 unchanged FP operations')
            need(self.counts.get('vdot.vv', 0) == 0 and self.counts['vwmul.vv'] == 2592
                 and self.counts['vwredsum.vs'] == 2592, 'GS32 standard full-group arithmetic counts')
            need(self.counts['vs1r.v'] == 8 and self.counts['vse32.v'] == 36 and self.counts['ret'] == 1,
                 'GS32 final stores and return')
            return dict(function_instructions=len(self.path), counts=dict(self.counts),
                        output_sha256=sha(self.regions['y']), slots_sha256=sha(self.regions['slots']),
                        exact_footprints=True, abi_preserved=True, stack_used_bytes=0)

    return GS32, full


def numeric(repo, elf, model, helpers, out):
    q = repo / generate.REL.parent
    headers = {'q288.h':q/'q288.h','caller.h':q.parent/'caller.h','split.h':q.parent/'split/split.h'}
    lib = helpers.oracle_library(q/'oracle.c', headers, out/'oracle')
    primitives = helpers.fp_primitive_checks(lib)
    base = helpers.fixtures(q/'generate.py')
    cases = [('x'+str(d), base, d) for d in (0, 1, 0, 2)]
    for name, w, x in (('min-min',-128,-128),('max-max',127,127),('min-max',-128,127),('zero-weight',0,73)):
        f = copy.deepcopy(base)
        f['weight'] = [w]*82944
        f['inputs'][0] = [x]*288
        f['packed'] = [w]*82944
        cases.append((name, f, 0))
    candidate, baseline = machine_class(repo, model)
    methods = [('gs32', candidate, generate.NAME), ('fr', baseline, 'q288_fused_rvv4')]
    previous, records = {}, []
    for i, (label, fixture, d) in enumerate(cases):
        golden = helpers.native_golden(lib, fixture, d)
        need(golden == helpers.python_golden(fixture, d), 'C/Python independent FP32 golden')
        if i < 4:
            need(golden == fixture['golden'][d], 'unchanged frozen fixture golden')
        if i == 0:
            need(golden[0] == 0, 'strict FP32 FMA witness')
        record = dict(index=i,case=label,dataset=d,methods={})
        for kind, cls, symbol in methods:
            alignment = (0, 0) if i < 4 else ((i*3)%16, (i*7)%16)
            m = cls(fixture, d, poison=0x323200+i, alignment=alignment)
            if 0 < i < 4:
                m.regions['packed'] = previous[kind].regions['packed']
                m.v = [bytearray(v) for v in previous[kind].v]
            m.execute_function(elf, symbol)
            result = m.check_candidate(golden) if kind == 'gs32' else m.check_full('rvv4', golden)
            record['methods'][kind] = dict(result, byte_alignment=alignment)
            previous[kind] = m
        records.append(record)
    return dict(cases=records, fp_primitive_checks=primitives)


def controls(repo, elf, model, helpers):
    fixture = helpers.fixtures(repo/generate.REL.parent/'generate.py')
    cls, _ = machine_class(repo, model)
    begin, _, offset = elf.symbols[generate.NAME]
    words = [w for w, in struct.iter_unpack('<I', elf.symbol_data(generate.NAME))]
    find = lambda pred: next(i for i, w in enumerate(words) if pred(w))
    avl = find(lambda w: w == 0x02000e93)
    weight = find(lambda w: w & 0x000fffff == 0x00060f93 and w >> 20 == 32)
    widen = find(lambda w: w & 127 == 0x57 and w >> 26 == 0x3b)
    mul = find(lambda w: w & 127 == 0x57 and w >> 26 == 0x24 and (w >> 12) & 7 == 1)
    core_index = (elf.symbols[generate.NAME+'_core_begin'][0]-begin)//4
    seed_clear = core_index+1
    init_clear = find(lambda w: w & 0xfff0707f == 0x5e003057 and (w >> 7) & 31 == 2)
    mutants = [('short-vl', avl, 0x01000e93),
               ('wrong-row', weight, (words[weight] & 0xfffff) | (64 << 20)),
               ('misaligned-m4-destination', widen, (words[widen] & ~(31 << 7)) | (18 << 7)),
               ('missing-shared-seed-clear', seed_clear, 0x00000013),
               ('missing-entry-high96-clear', init_clear, 0x00000013)]
    records = []
    for name, at, word in mutants:
        raw = bytearray(elf.raw)
        struct.pack_into('<I', raw, offset+4*at, word)
        m = cls(fixture, 0, poison=0x500)
        try:
            m.execute_function(model.ELF(bytes(raw)), generate.NAME).check_candidate(fixture['golden'][0])
        except ValueError as error:
            records.append(dict(case=name,pc=hex(begin+4*at),mutant_sha256=sha(raw),rejection=str(error)))
        else:
            raise ValueError('actual ELF mutant accepted: ' + name)
    raw = bytearray(elf.raw)
    struct.pack_into('<3I', raw, offset+4*mul, words[mul+1], words[mul+2], words[mul])
    m = cls(fixture, 0, poison=0x501)
    try:
        m.execute_function(model.ELF(bytes(raw)), generate.NAME).check_candidate(fixture['golden'][0])
    except ValueError as error:
        need(str(error) == 'GS32 full-Q bitwise output', 'rounding-order numerical rejection')
        records.append(dict(case='wrong-fp-scale-order',pc=hex(begin+4*mul),mutant_sha256=sha(raw),rejection=str(error)))
    else:
        raise ValueError('actual ELF FP-order mutant accepted')
    return records


def run(repo, elf_path, out):
    need(not out.exists(), 'fresh screen result directory')
    out.mkdir(parents=True)
    model, helpers = support(repo)
    elf = model.ELF(elf_path.read_bytes())
    result = dict(contract=generate.CONTRACT, elf_sha256=sha(elf.raw),
                  numeric=numeric(repo, elf, model, helpers, out),
                  controls=controls(repo, elf, model, helpers),
                  status='GS32_ACTUAL_ELF_NUMERIC_PASS',
                  new_emu_runs=0, target_runtime_qualified=False, performance_qualified=False)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--elf', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    sys.dont_write_bytecode = True
    if hasattr(os, 'sched_getaffinity'):
        allowed = sorted(os.sched_getaffinity(0))
        os.sched_setaffinity(0, [allowed[0]])
    result = run(args.repo.resolve(), args.elf.resolve(), args.output.resolve())
    first = result['numeric']['cases'][0]['methods']
    print(json.dumps(dict(status=result['status'],elf_sha256=result['elf_sha256'],
                         cases=len(result['numeric']['cases']),controls=len(result['controls']),
                         instructions={key:value['function_instructions'] for key,value in first.items()},
                         target_runtime_qualified=False,performance_qualified=False), indent=2))
