"""Finite actual-ELF value/address model for the two fused Q implementations.

Reuses the frozen integer instruction model. New FP operations use exact integer
binary32 rounding, independent of the generator and of the C oracle. This is
not NEMU, a target execution, an exception model, or a cycle predictor.
"""
from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import struct

MODEL_SHA = '8fb2ac208d8db9083464fb839c06b46ec365234d72b819822563830dad90171e'
MASK = (1 << 64)-1
SAVED = (2,3,4,8,9,18,19,20,21,22,23,24,25,26,27)
FP_SAVED = (8,9,18,19,20,21,22,23,24,25,26,27)


def need(ok, message):
    if not ok: raise ValueError(message)


def signed(value, bits):
    value &= (1 << bits)-1
    return value-(1 << bits) if value >> (bits-1) else value


def parts(word):
    exp, fraction = (word >> 23)&255, word&0x7fffff
    need(exp != 255, 'finite binary32 model domain')
    value = fraction | (0x800000 if exp else 0)
    return (-value if word >> 31 else value), (exp-150 if exp else -149)


def round_shift(value, shift):
    if shift <= 0: return value << -shift
    quotient, remainder = divmod(value, 1 << shift)
    half = 1 << (shift-1)
    return quotient + int(remainder > half or (remainder == half and quotient&1))


def round_binary32(value, exponent, zero_sign=0):
    if value == 0: return zero_sign << 31
    sign = int(value < 0); value = abs(value)
    power = value.bit_length()-1+exponent
    if power < -126:
        significand = round_shift(value, -149-exponent)
        need(significand <= 0x800000, 'subnormal rounding range')
        return (sign << 31) | significand
    significand = round_shift(value, value.bit_length()-24)
    if significand == 1 << 24:
        significand >>= 1; power += 1
    need(power <= 127, 'finite result model domain')
    return (sign << 31) | ((power+127) << 23) | (significand&0x7fffff)


def multiply(a, b):
    av, ae = parts(a); bv, be = parts(b)
    return round_binary32(av*bv, ae+be, ((a^b) >> 31)&1)


def add(a, b):
    av, ae = parts(a); bv, be = parts(b); exponent = min(ae, be)
    value = (av << (ae-exponent)) + (bv << (be-exponent))
    # Exact cancellation is +0 in RNE; only -0 + -0 retains a negative zero.
    zero_sign = int(av == bv == 0 and (a&b) >> 31 != 0)
    return round_binary32(value, exponent, zero_sign)


class ELF:
    def __init__(self, raw):
        self.raw = raw
        need(raw[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', raw, 18)[0] == 243,
             'actual RV64 little-endian ELF')
        shoff = struct.unpack_from('<Q', raw, 40)[0]
        size, count = struct.unpack_from('<HH', raw, 58)
        self.sections = [struct.unpack_from('<IIQQQQIIQQ', raw, shoff+i*size) for i in range(count)]
        self.symbols = {}
        for sec in self.sections:
            if sec[1] != 2: continue
            strings = self.sections[sec[6]]
            names = raw[strings[4]:strings[4]+strings[5]]
            for at in range(sec[4], sec[4]+sec[5], sec[9]):
                name, _, _, section, address, length = struct.unpack_from('<IBBHQQ', raw, at)
                name = names[name:names.find(b'\0', name)].decode()
                if not name or not 0 < section < len(self.sections): continue
                owner = self.sections[section]
                self.symbols[name] = (address, length, owner[4]+address-owner[3])

    def symbol_data(self, name):
        _, length, offset = self.symbols[name]
        return self.raw[offset:offset+length]


def core_certificate(elf, reference_words, kind):
    old_name = 'config_reuse_gemv_8x32_reuse_'+('vdot' if kind == 'vdot' else 'rvv')
    pin, count, length = (
        ('3bca83077ccd7529ff6f80c9002441c99d27d3113aa8b10769ad26f3c4e9c64d',4,164)
        if kind == 'vdot' else
        ('ea86a50cd67113246dae98ef7ce8db4e0d1383f453d889c6aad6cf2579857513',2,112))
    before = bytes.fromhex(reference_words[old_name])
    need(hashlib.sha256(before).hexdigest() == pin, 'qualified original integer machine body')
    words = list(struct.unpack('<'+'I'*length, before))
    need(words[:4] == [0x00050613,0x00058693,0x00805073,0x00f3d073] and
         words[-20:-17] == [0xc0047057,0x10000f13,0x00068f93] and words[-1] == 0x00008067,
         'exact removed integer entry and store tail')
    core = words[4:-20]
    if kind == 'rvv4':
        need(core[:2] == [0xc0047057,0xc0087057], 'redundant RVV setup word')
        core = core[1:]
    changed = []
    for i, word in enumerate(core):
        if word&0x000fffff == 0x00060f93 and word >> 20 in (256,264,272,280):
            core[i] = (((word >> 20)-256) << 20) | 0x00058f93
            changed.append(i)
    need(len(changed) == count, 'all and only x-address machine changes')
    expected = struct.pack('<'+'I'*len(core), *core)
    name = 'q288_fused_'+kind; body = elf.symbol_data(name)
    need(body[60:60+len(expected)] == expected and body.count(expected) == 1,
         'exact contiguous integer arithmetic/reset/loads within fused function')
    return dict(original_sha256=pin, core_words=len(core), x_relocations=changed,
                actual_core_sha256=hashlib.sha256(expected).hexdigest())


def machine_class(model_path):
    model_path = Path(model_path)
    need(hashlib.sha256(model_path.read_bytes()).hexdigest() == MODEL_SHA, 'frozen integer model')
    spec = importlib.util.spec_from_file_location('fused_integer_model', model_path)
    base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

    class FullQ(base.Machine):
        def __init__(self, fixture, dataset=0, poison=0, alignment=(0,0)):
            super().__init__([[0]*32 for _ in range(8)], [0]*32, poison)
            # Entry state must not pre-satisfy the candidate's reset obligations.
            self.vl,self.sew,self.lmul,self.ta,self.ma,self.vstart,self.vcsr = 3,16,2,1,1,2,0
            self.fixture, self.dataset = fixture, dataset
            self.x = [(0x9345678900000000+i*257)&MASK for i in range(32)]; self.x[0] = 0
            self.halt = 0x1234567812345678; self.x[1] = self.halt
            self.f = [0x3ff1234500000000+i*257 for i in range(32)]
            addresses = dict(packed=0x10000000+alignment[0], x=0x10020000+alignment[1],
                             ws=0x10030004, xs=0x10040004, y=0x10050004, slots=0x10060000, context=0x10070000)
            raw8 = lambda seq: bytes(v&255 for v in seq)
            raw32 = lambda seq: struct.pack('<'+'I'*len(seq), *seq)
            self.regions = {
                'packed': bytearray(raw8(fixture['packed'])),
                'x': bytearray(raw8(fixture['inputs'][dataset])),
                'ws': bytearray(raw32(fixture['weight_scale'])),
                'xs': bytearray(raw32(fixture['input_scale'][dataset])),
                'y': bytearray(b'\xa6'*1152), 'slots': bytearray(b'\xa6'*128),
                'context': bytearray(struct.pack('<7Q', *(addresses[n] for n in ('packed','x','ws','xs','y','slots')), 0x81234560)),
            }
            self.addresses = addresses; self.x[10] = addresses['context']
            self.original = {n:bytes(raw) for n,raw in self.regions.items()}
            self.saved = {i:self.x[i] for i in (1,*SAVED)}
            self.saved_fp = {i:self.f[i] for i in FP_SAVED}
            self.read_bytes_count, self.write_bytes_count, self.fp_counts = Counter(), Counter(), Counter()
            self.path = []; self.frm = 0

        def write_x(self, rd, value):
            if rd: self.x[rd] = value&MASK

        def locate(self, address, size):
            for name, begin in self.addresses.items():
                if begin <= address and address+size <= begin+len(self.regions[name]):
                    return name, address-begin
            raise ValueError('actual memory access outside exact caller buffers')

        def read(self, address, size):
            name, offset = self.locate(address, size)
            need(name not in ('y','slots'), 'no output/slot readback in fused body')
            self.read_bytes_count.update((name,i) for i in range(offset, offset+size))
            return bytes(self.regions[name][offset:offset+size])

        def write(self, address, raw):
            name, offset = self.locate(address, len(raw))
            need(name in ('y','slots'), 'read-only input/context write rejected')
            self.write_bytes_count.update((name,i) for i in range(offset, offset+len(raw)))
            self.regions[name][offset:offset+len(raw)] = raw

        def v32(self, reg, lanes):
            return list(struct.unpack('<'+'I'*lanes, self.get(reg, 4*lanes)))

        def put32(self, reg, values, capacity):
            self.put(reg, struct.pack('<'+'I'*len(values), *(v&0xffffffff for v in values)), capacity)

        def mode(self, vl, sew, lmul):
            need((self.vl,self.sew,self.lmul,self.ta,self.ma,self.vstart) == (vl,sew,lmul,0,0,0),
                 'exact vector mode at fused operation')

        def execute_function(self, elf, name):
            begin, size, _ = elf.symbols[name]; pc = begin
            words = {begin+4*i:w for i,(w,) in enumerate(struct.iter_unpack('<I', elf.symbol_data(name)))}
            self.function_begin,self.function_words = begin,words
            need(all(w&3 == 3 for w in words.values()), 'uncompressed fused instructions')
            for _ in range(200000):
                need(pc in words, 'fused control escaped function')
                w = words[pc]; self.path.append((pc,w)); next_pc = pc+4
                op, f3, f6 = w&127, (w>>12)&7, w>>26
                rd, a, b = (w>>7)&31, (w>>15)&31, (w>>20)&31
                imm = signed(w>>20,12); label = None
                if op == 0x13 and f3 == 0:
                    self.write_x(rd, self.x[a]+imm); label = 'addi'
                elif op == 3 and f3 == 3:
                    self.write_x(rd, int.from_bytes(self.read(self.x[a]+imm,8),'little')); label = 'ld'
                elif op == 0x63 and f3 == 1:
                    offset = ((w>>31)<<12) | (((w>>7)&1)<<11) | (((w>>25)&63)<<5) | (((w>>8)&15)<<1)
                    if self.x[a] != self.x[b]: next_pc = pc+signed(offset,13)
                    label = 'bne'
                elif w == 0x00008067:
                    need(self.x[1] == self.halt, 'ordinary preserved return address')
                    self.counts['ret'] += 1
                    return self
                elif op == 7 and f3 == 2:
                    self.f[rd] = 0xffffffff00000000 | int.from_bytes(self.read(self.x[a]+imm,4),'little')
                    label = 'flw'
                elif op == 0x27 and w&0xfff0707f == 0x02800027:
                    self.write(self.x[a], self.get(rd,16)); label = 'vs1r.v'
                elif op == 7 and f3 == 6 and (w>>25)&1 and (w>>26)&3 == 2 and w>>28 == 0:
                    self.mode(8,32,2); need(rd%2 == 0, 'aligned strided-load LMUL2 group')
                    values = [int.from_bytes(self.read(self.x[a]+i*signed(self.x[b],64),4),'little') for i in range(8)]
                    self.put32(rd,values,32); label = 'vlse32.v'
                elif op == 0x27 and f3 == 6 and w>>20 == 0x20:
                    self.mode(8,32,2); need(rd%2 == 0, 'aligned output LMUL2 group')
                    self.write(self.x[a],self.get(rd,32)); label = 'vse32.v'
                elif op == 0x57 and (w>>25)&1 and (f6,f3) == (0,0):
                    self.mode(4,32,1)
                    self.put32(rd,[x+y for x,y in zip(self.v32(a,4),self.v32(b,4))],16); label = 'vadd.vv'
                elif op == 0x57 and (w>>25)&1 and (f6,f3) == (0x17,0) and b == 0:
                    self.mode(4,32,1); self.put(rd,self.get(a,16),16); label = 'vmv.v.v'
                elif op == 0x57 and (w>>25)&1 and (f6,f3) == (0x0e,3):
                    self.mode(4,32,1); need(rd != b and 0 <= a < 4, 'nonoverlapping finite gather slide')
                    values = self.v32(rd,4); values[a:4] = self.v32(b,4)[:4-a]
                    self.put32(rd,values,16); label = 'vslideup.vi'
                elif op == 0x57 and (w>>25)&1 and (f6,f3) == (0x17,3) and b == 0:
                    need(rd % self.lmul == 0, 'aligned immediate vector move destination')
                    super().execute(struct.pack('<I',w))
                elif op == 0x57 and (w>>25)&1 and (f6,f3) == (0x12,1):
                    self.mode(8,32,2); need(a == 3 and rd%2 == b%2 == 0, 'exact signed vfcvt.f.x.v')
                    self.put32(rd,[round_binary32(signed(v,32),0) for v in self.v32(b,8)],32)
                    self.fp_counts['convert'] += 8; label = 'vfcvt.f.x.v'
                elif op == 0x57 and (w>>25)&1 and (f6,f3) in ((0x24,1),(0x24,5),(0,1)):
                    self.mode(8,32,2); need(rd%2 == b%2 == 0, 'aligned FP LMUL2 groups')
                    if f3 == 5:
                        need(self.f[a] >> 32 == 0xffffffff, 'NaN-boxed scalar FP input')
                        left = [self.f[a]&0xffffffff]*8
                    else:
                        need(a%2 == 0, 'aligned second FP LMUL2 source'); left = self.v32(a,8)
                    arithmetic = add if f6 == 0 else multiply
                    self.put32(rd,[arithmetic(x,y) for x,y in zip(left,self.v32(b,8))],32)
                    self.fp_counts['add' if f6 == 0 else 'mul'] += 8
                    label = 'vfadd.vv' if f6 == 0 else 'vfmul.vf' if f3 == 5 else 'vfmul.vv'
                else:
                    super().execute(struct.pack('<I',w))
                if label: self.counts[label] += 1
                need(self.x[0] == 0, 'constant x0')
                pc = next_pc
            raise ValueError('fused function exceeded finite execution budget')

        def check_full(self, kind, golden):
            core_begin=self.function_begin+60
            core_length=140 if kind=='vdot' else 87
            expected=[(core_begin+4*i,self.function_words[core_begin+4*i]) for i in range(core_length)]
            starts=[i for i,(pc,_) in enumerate(self.path) if pc==core_begin]
            need(len(starts)==324 and all(self.path[i:i+core_length]==expected for i in starts) and
                 sum(core_begin<=pc<core_begin+4*core_length for pc,_ in self.path)==324*core_length,
                 '324 complete dynamically executed integer core blocks')
            need(self.regions['y'] == struct.pack('<288I',*golden), 'actual ELF full-Q bitwise output')
            f, d = self.fixture, self.dataset
            dots = [sum(f['weight'][r*288+k]*f['inputs'][d][k] for k in range(256,288)) for r in range(280,288)]
            expected = b''.join(struct.pack('<I',v&0xffffffff)+bytes(12) for v in dots)
            need(self.regions['slots'] == expected, 'actual ELF final complete slots')
            need(all(bytes(self.regions[n]) == raw for n,raw in self.original.items() if n not in ('y','slots')),
                 'all input/context bytes unchanged')
            wanted_read = Counter()
            for name, size, times in (('packed',82944,1),('x',288,36),('ws',10368,1),('xs',36,36),('context',48,1)):
                wanted_read.update({(name,i):times for i in range(size)})
            need(self.read_bytes_count == wanted_read, 'complete exact source-byte footprint')
            wanted_write = Counter({(name,i):1 for name,size in (('y',1152),('slots',128)) for i in range(size)})
            need(self.write_bytes_count == wanted_write, 'complete exact output-byte footprint')
            need(all(self.x[i] == value for i,value in self.saved.items()) and
                 all(self.f[i] == value for i,value in self.saved_fp.items()), 'full-width scalar/FP ABI preservation')
            self.mode(8,8,1); need(self.vcsr == 7 and self.frm == 0, 'final CSR/FRM state')
            need(self.fp_counts == Counter(convert=2592,mul=5184,add=2592), 'strict FP element operation counts')
            need(self.counts.get('vdot.vv',0) == (10368 if kind == 'vdot' else 0), 'complete custom count')
            need(self.counts['vs1r.v'] == 8 and self.counts['vse32.v'] == 36 and self.counts['ret'] == 1,
                 'only final slots, all tile outputs and one ordinary return')
            return dict(function_instructions=len(self.path), counts=dict(self.counts), fp_element_operations=dict(self.fp_counts),
                output_sha256=hashlib.sha256(self.regions['y']).hexdigest(), final_slots_sha256=hashlib.sha256(self.regions['slots']).hexdigest(),
                path_sha256=hashlib.sha256(b''.join(struct.pack('<QI',pc,w) for pc,w in self.path)).hexdigest(),
                full_inputs_readonly=True, exact_footprints=True, abi_preserved=True, stack_used_bytes=0)

    return FullQ
