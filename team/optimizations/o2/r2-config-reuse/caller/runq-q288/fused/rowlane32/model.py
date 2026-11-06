"""Bounded actual-ELF row32 value/address screen, not NEMU or a cycle model.

Reuse the pinned independent full-Q exact binary32 arithmetic and buffer/ABI
state. This extension decodes only the actual candidate's standard RVV subset;
unknown instructions and unsupported vector modes fail closed. No fflags model.
"""
from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import struct

FUSED = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused')
MODEL_SHA = '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82'
INTEGER = Path('team/optimizations/o2/r2-safe-tail/machine_model.py')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def pinned_model(repo):
    path = Path(repo) / FUSED / 'model.py'
    need(hashlib.sha256(path.read_bytes()).hexdigest() == MODEL_SHA,
         'unchanged exact full-Q FP/address/ABI model')
    spec = importlib.util.spec_from_file_location('rowlane32_fused_model', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def machine_class(repo):
    fp = pinned_model(repo)
    parent = fp.machine_class(Path(repo) / INTEGER)
    signed = fp.signed

    class Row32(parent):
        def mode(self, vl, sew, lmul, ta=0):
            need((self.vl, self.sew, self.lmul, self.ta, self.ma, self.vstart) ==
                 (vl, sew, lmul, ta, 0, 0), 'exact row32 vector mode')

        def group(self, reg, emul):
            need(emul in (1, 2, 4, 8) and reg % emul == 0 and reg + emul <= 32,
                 'aligned bounded vector register group')

        def execute_function(self, elf, name):
            begin, size, _ = elf.symbols[name]
            body = elf.symbol_data(name)
            need(size == len(body) and size % 4 == 0, 'bounded complete ELF function')
            words = {begin + 4*i: w for i, (w,) in enumerate(struct.iter_unpack('<I', body))}
            need(all(w & 3 == 3 for w in words.values()), 'uncompressed actual instructions')
            self.function_begin, self.function_words, self.function_name = begin, words, name
            self.core_begin = elf.symbols[name + '_core_begin'][0]
            self.core_end = elf.symbols[name + '_core_end'][0]
            pc = begin
            for _ in range(200000):
                need(pc in words, 'control escaped actual row32 function')
                w = words[pc]
                self.path.append((pc, w))
                next_pc = pc + 4
                op, f3, f6 = w & 127, (w >> 12) & 7, w >> 26
                rd, a, b = (w >> 7) & 31, (w >> 15) & 31, (w >> 20) & 31
                imm = signed(w >> 20, 12)
                label = None
                if op == 0x13 and f3 == 0:
                    self.write_x(rd, self.x[a] + imm)
                    label = 'addi'
                elif op == 3 and f3 in (0, 3):
                    raw = self.read(self.x[a] + imm, 1 if f3 == 0 else 8)
                    value = signed(raw[0], 8) if f3 == 0 else int.from_bytes(raw, 'little')
                    self.write_x(rd, value)
                    label = 'lb' if f3 == 0 else 'ld'
                elif op == 0x63 and f3 == 1:
                    offset = ((w >> 31) << 12) | (((w >> 7) & 1) << 11) | (((w >> 25) & 63) << 5) | (((w >> 8) & 15) << 1)
                    if self.x[a] != self.x[b]:
                        next_pc = pc + signed(offset, 13)
                    label = 'bne'
                elif w == 0x00008067:
                    need(self.x[1] == self.halt, 'ordinary preserved return address')
                    self.counts['ret'] += 1
                    return self
                elif op == 0x73 and f3 == 5 and rd == 0 and w >> 20 in (8, 15):
                    if w >> 20 == 8:
                        self.vstart = a
                    else:
                        self.vcsr = a & 7
                    label = 'csrwi'
                elif op == 7 and f3 == 2:
                    self.f[rd] = 0xffffffff00000000 | int.from_bytes(self.read(self.x[a] + imm, 4), 'little')
                    label = 'flw'
                elif op == 0x57 and f3 == 7 and (w >> 30 == 3 or w >> 31 == 0):
                    immediate = w >> 30 == 3
                    vt = (w >> 20) & (1023 if immediate else 2047)
                    need(vt & ~0xff == 0 and vt & 7 in (0, 1, 2, 3), 'finite supported VTYPE')
                    sew, lmul = 8 << ((vt >> 3) & 7), 1 << (vt & 7)
                    avl = a if immediate else self.x[a]
                    need(sew in (8, 16, 32) and (immediate or a != 0) and 0 < avl <= 128*lmul//sew,
                         'explicit bounded nonzero AVL')
                    self.vl, self.sew, self.lmul = avl, sew, lmul
                    self.ta, self.ma, self.vstart = (vt >> 6) & 1, (vt >> 7) & 1, 0
                    self.write_x(rd, avl)
                    label = 'vsetivli' if immediate else 'vsetvli'
                elif op == 7 and w & 0xfff0707f == 0x02000007:
                    self.mode(32, 16, 4, ta=1)
                    self.group(rd, 2)
                    self.put(rd, self.read(self.x[a], 32), 32)
                    label = 'vle8.v'
                elif op == 7 and f3 == 6 and (w >> 25) & 1 and (w >> 26) & 3 == 2 and w >> 28 == 0:
                    self.mode(32, 32, 8)
                    self.group(rd, 8)
                    values = [int.from_bytes(self.read(self.x[a] + i*signed(self.x[b], 64), 4), 'little') for i in range(32)]
                    self.put32(rd, values, 128)
                    label = 'vlse32.v'
                elif op == 0x27 and f3 == 6 and w >> 20 == 0x20:
                    self.mode(32, 32, 8)
                    self.group(rd, 8)
                    self.write(self.x[a], self.get(rd, 128))
                    label = 'vse32.v'
                elif op == 0x27 and f3 == 6 and (w >> 25) & 1 and (w >> 26) & 3 == 2 and w >> 28 == 0:
                    self.mode(8, 32, 2)
                    self.group(rd, 2)
                    values = self.v32(rd, 8)
                    for i, value in enumerate(values):
                        self.write(self.x[a] + i*signed(self.x[b], 64), struct.pack('<I', value))
                    label = 'vsse32.v'
                elif op == 0x57 and (w >> 25) & 1:
                    need(self.vstart == 0, 'zero vstart for vector arithmetic')
                    if (f6, f3) == (0x17, 3) and b == 0:
                        need((self.vl, self.sew, self.lmul) in ((32, 32, 8), (8, 32, 2)),
                             'supported accumulator/slot immediate move')
                        self.mode(self.vl, self.sew, self.lmul)
                        self.group(rd, self.lmul)
                        self.put32(rd, [signed(a, 5)]*self.vl, 16*self.lmul)
                        label = 'vmv.v.i'
                    elif (f6, f3) == (0x12, 2) and a == 7:
                        self.mode(32, 16, 4, ta=1)
                        self.group(rd, 4)
                        self.group(b, 2)
                        need(set(range(rd, rd+4)).isdisjoint(range(b, b+2)), 'nonoverlapping sign-extension groups')
                        values = [signed(value, 8) for value in self.get(b, 32)]
                        self.put(rd, struct.pack('<32h', *values), 64)
                        label = 'vsext.vf2'
                    elif (f6, f3) == (0x3d, 6):
                        self.mode(32, 16, 4, ta=1)
                        self.group(rd, 8)
                        self.group(b, 4)
                        need(set(range(rd, rd+8)).isdisjoint(range(b, b+4)), 'nonoverlapping widening MAC groups')
                        weights = [value for value, in struct.iter_unpack('<h', self.get(b, 64))]
                        scalar = signed(self.x[a], 16)
                        self.put32(rd, [old + scalar*weight for old, weight in zip(self.v32(rd, 32), weights)], 128)
                        label = 'vwmacc.vx'
                    elif (f6, f3) == (0, 0):
                        self.mode(32, 32, 8)
                        for reg in (rd, a, b):
                            self.group(reg, 8)
                        self.put32(rd, [x+y for x, y in zip(self.v32(a, 32), self.v32(b, 32))], 128)
                        label = 'vadd.vv'
                    elif (f6, f3) == (0x12, 1) and a == 3:
                        self.mode(32, 32, 8)
                        self.group(rd, 8)
                        self.group(b, 8)
                        self.put32(rd, [fp.round_binary32(signed(value, 32), 0) for value in self.v32(b, 32)], 128)
                        self.fp_counts['convert'] += 32
                        label = 'vfcvt.f.x.v'
                    elif (f6, f3) in ((0x24, 1), (0x24, 5), (0, 1)):
                        self.mode(32, 32, 8)
                        self.group(rd, 8)
                        self.group(b, 8)
                        need(self.frm == 0, 'RNE vector FP model')
                        if f3 == 5:
                            need(self.f[a] >> 32 == 0xffffffff, 'NaN-boxed scalar FP')
                            left = [self.f[a] & 0xffffffff]*32
                        else:
                            self.group(a, 8)
                            left = self.v32(a, 32)
                        arithmetic = fp.add if f6 == 0 else fp.multiply
                        self.put32(rd, [arithmetic(x, y) for x, y in zip(left, self.v32(b, 32))], 128)
                        self.fp_counts['add' if f6 == 0 else 'mul'] += 32
                        label = 'vfadd.vv' if f6 == 0 else 'vfmul.vf' if f3 == 5 else 'vfmul.vv'
                need(label is not None, 'unsupported row32 instruction 0x%08x' % w)
                self.counts[label] += 1
                need(self.x[0] == 0, 'constant x0')
                pc = next_pc
            raise ValueError('row32 function exceeded finite execution budget')

        def check_full(self, golden):
            need(self.core_end - self.core_begin == 165*4, 'complete 165-word integer core')
            core = [(pc, self.function_words[pc]) for pc in range(self.core_begin, self.core_end, 4)]
            starts = [i for i, (pc, _) in enumerate(self.path) if pc == self.core_begin]
            need(len(starts) == 81 and all(self.path[i:i+165] == core for i in starts) and
                 sum(self.core_begin <= pc < self.core_end for pc, _ in self.path) == 81*165,
                 '81 complete executed integer blocks')
            need(self.regions['y'] == struct.pack('<288I', *golden), 'actual ELF full-Q bitwise output')
            f, d = self.fixture, self.dataset
            dots = [sum(f['weight'][r*288+k]*f['inputs'][d][k] for k in range(256, 288)) for r in range(280, 288)]
            slots = b''.join(struct.pack('<I', value & 0xffffffff) + bytes(12) for value in dots)
            need(self.regions['slots'] == slots, 'actual ELF final complete slots')
            need(all(bytes(self.regions[name]) == raw for name, raw in self.original.items() if name not in ('y', 'slots')),
                 'all input/context bytes unchanged')
            wanted_read = Counter()
            for name, size, count in (('packed', 82944, 1), ('x', 288, 9), ('ws', 10368, 1), ('xs', 36, 9), ('context', 48, 1)):
                wanted_read.update({(name, i): count for i in range(size)})
            need(self.read_bytes_count == wanted_read, 'complete exact source-byte footprint')
            wanted_write = Counter({(name, i): 1 for name, size in (('y', 1152), ('slots', 128)) for i in range(size)})
            need(self.write_bytes_count == wanted_write, 'complete exact output-byte footprint')
            need(all(self.x[i] == value for i, value in self.saved.items()) and
                 all(self.f[i] == value for i, value in self.saved_fp.items()), 'full-width scalar/FP ABI preservation')
            self.mode(8, 8, 1)
            need(self.vcsr == 7 and self.frm == 0, 'final CSR/FRM state')
            need(self.fp_counts == Counter(convert=2592, mul=5184, add=2592), 'strict FP element operation counts')
            need(all(self.counts[name] == 2592 for name in ('lb', 'vle8.v', 'vsext.vf2', 'vwmacc.vx')) and
                 self.counts['vadd.vv'] == 81 and self.counts['vse32.v'] == 9 and self.counts['vsse32.v'] == 4 and self.counts['ret'] == 1,
                 'complete standard-RVV integer and output inventory')
            return dict(function_instructions=len(self.path), counts=dict(self.counts), fp_element_operations=dict(self.fp_counts),
                        output_sha256=hashlib.sha256(self.regions['y']).hexdigest(), final_slots_sha256=hashlib.sha256(self.regions['slots']).hexdigest(),
                        path_sha256=hashlib.sha256(b''.join(struct.pack('<QI', pc, w) for pc, w in self.path)).hexdigest(),
                        full_inputs_readonly=True, exact_footprints=True, abi_preserved=True, stack_used_bytes=0)

    return Row32
