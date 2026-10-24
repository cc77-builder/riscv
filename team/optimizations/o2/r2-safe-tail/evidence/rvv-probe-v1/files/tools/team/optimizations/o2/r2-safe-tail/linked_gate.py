#!/usr/bin/env python3
"""Strict linked ELF/bin gate. This validates artifacts, NOT CPU execution.

Only the original nexus-am build path is eligible for the full-core runner.
Relocatable objects and the explicit unit-test fixtures are rejected there.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile

BASE = "24cb8b2e0fa0b17cad65c82246c572347a351d43"
REL = Path("team/optimizations/o2/r2-safe-tail")
O3 = Path("team/workloads/o3-gemv")
PINNED = {
    str(O3/'generate.py'): '9cb0c6b755daa9b05d346b4b48cb80246852d4a8',
    str(O3/'model.py'): '0be812d0fc112af863fe5adf3be3794e16c7bdf4',
    'team/workloads/unified-vdot/generate.py': '90cc41079c27ebfe146321d4bf01e2ee0426dae9',
    str(REL/'candidate.py'): 'e8b0a80f05151442fec29fd309e632e6d32a93ed',
    str(O3/'main.c'): '8f760dfa263be49a00c52ef3932006b52f218d2d',
    str(O3/'Makefile'): '1f7e330f204be58b68cc1a3094623ad57b7a3889',
    str(O3/'fixed-layout.ld'): '9502a16fa1342a9fa7b9b9f63bb8636ee8050e7a',
}
RAM, RAM_END = 0x80000000, 0x88000000
FIXED = {'.benchmark_inputs':0x80100000, '.benchmark_expected':0x80110000,
         '.benchmark_cases':0x80120000, '.benchmark_result':0x80130000,
         '.benchmark_sink':0x80131000}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blob(data):
    data = data.replace(b'\r\n', b'\n')
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, Path(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


class ELF:
    """Small bounds-checked ELF64 reader, for RISC-V ET_EXEC/ET_REL only."""
    def __init__(self, raw):
        self.raw = raw
        require(len(raw) >= 64, 'truncated ELF')
        h = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
        require(h[0][:7] == b'\x7fELF\x02\x01\x01' and h[2] == 243, 'not ELF64 LE RISC-V')
        require(h[1] in (1,2) and h[3] == 1, 'not static executable/relocatable ELF')
        self.kind, self.entry = h[1], h[4]
        require(h[11] == 64 and 0 < h[12] < 8192 and h[13] < h[12], 'section table')
        self.range(h[6], h[11]*h[12])
        self.sections = [struct.unpack_from('<IIQQQQIIQQ',raw,h[6]+i*64) for i in range(h[12])]
        names = self.section(self.sections[h[13]])
        self.named = {}
        for s in self.sections:
            name = self.string(names, s[0])
            if name:
                require(name not in self.named, 'duplicate section')
                self.named[name] = s
            if s[1] != 8:
                self.range(s[4], s[5])
        self.segments = []
        if h[10]:
            require(h[9] == 56 and h[10] < 4096, 'program table')
            self.range(h[5], h[9]*h[10])
            self.segments = [struct.unpack_from('<IIQQQQQQ',raw,h[5]+i*56) for i in range(h[10])]
        self.symbols = {}
        for s in self.sections:
            if s[1] != 2:
                continue
            require(s[9] == 24 and s[5] % 24 == 0 and s[6] < len(self.sections), 'symbol table')
            strings = self.section(self.sections[s[6]])
            for pos in range(s[4],s[4]+s[5],24):
                name,info,other,index,address,length=struct.unpack_from('<IBBHQQ',raw,pos)
                name=self.string(strings,name)
                if not name or (info & 15) in (3,4):
                    continue
                # RISC-V mapping/assembler-local labels may repeat after linking.
                if info >> 4 == 0 and info & 15 == 0 and name.startswith(('$x', '$d', '.L')):
                    continue
                if index == 0:
                    require(info >> 4 == 2, 'undefined strong symbol: '+name)
                    continue
                if name in self.symbols:
                    require(self.symbols[name] == (address,length,index,info), 'ambiguous symbol: '+name)
                self.symbols[name]=(address,length,index,info)

    def range(self, offset, length):
        require(0 <= offset <= len(self.raw) and 0 <= length <= len(self.raw)-offset, 'ELF range overflow')

    @staticmethod
    def string(data, offset):
        require(0 <= offset < len(data), 'ELF string offset')
        end=data.find(b'\0',offset)
        require(end >= offset, 'unterminated ELF string')
        return data[offset:end].decode('utf-8')

    def section(self, sec):
        require(sec[1] != 8, 'NOBITS has no file contents')
        self.range(sec[4],sec[5])
        return self.raw[sec[4]:sec[4]+sec[5]]

    def read(self, address, length):
        for s in self.sections:
            if s[2]&2 and s[1]!=8 and s[3] <= address and address+length <= s[3]+s[5]:
                start=s[4]+address-s[3]
                self.range(start,length)
                return self.raw[start:start+length]
        raise ValueError('ELF address outside loaded file data')

    def symbol_data(self, name):
        address,length,index,_=self.symbols[name]
        require(index < len(self.sections), 'non-section symbol')
        s=self.sections[index]
        offset=address-s[3]
        require(0 <= offset and offset+length <= s[5], 'symbol outside section')
        return self.section(s)[offset:offset+length]

    def cstring(self, address):
        for s in self.sections:
            if s[2]&2 and s[1]!=8 and s[3] <= address < s[3]+s[5]:
                return self.string(self.section(s),address-s[3])
        raise ValueError('string outside file-backed memory')

    def binary(self):
        ranges=[]
        for s in self.sections:
            if s[2]&2 and s[5]:
                require(RAM <= s[3] < s[3]+s[5] <= RAM_END, 'loaded section outside RAM')
                ranges.append((s[3],s[3]+s[5],s))
        require(ranges and min(a for a,_,_ in ranges)==RAM, 'binary load base')
        ranges.sort()
        for prev,nxt in zip(ranges,ranges[1:]):
            require(prev[1] <= nxt[0], 'overlapping allocated sections')
        result=bytearray(max(b for _,b,_ in ranges)-RAM)
        for a,b,s in ranges:
            if s[1]!=8:
                result[a-RAM:b-RAM]=self.section(s)
        return bytes(result)

    def executable(self, allow_test_fixture=False):
        require(self.kind == 2, 'ET_REL is not a runnable ELF')
        require(allow_test_fixture or 'r2_unit_test_fixture' not in self.symbols, 'unit-test fixture cannot enter runtime gate')
        require(self.entry==RAM and self.symbols['_start'][0]==RAM, 'wrong boot entry')
        require(all(name in self.symbols for name in ('main','_trm_init','_halt','_putc')), 'incomplete runtime/harness')
        require(not any(p[0] in (2,3) for p in self.segments), 'dynamic/interpreter ELF')
        loads=[p for p in self.segments if p[0]==1 and p[6]]
        require(loads, 'no load segments')
        for _,flags,offset,vaddr,paddr,filesz,memsz,align in loads:
            require(filesz <= memsz and vaddr==paddr, 'invalid load sizes or LMA')
            require(RAM <= vaddr < vaddr+memsz <= RAM_END, 'segment outside memory')
            self.range(offset,filesz)
            require(align in (0,1) or (align&(align-1)==0 and (vaddr-offset)%align==0), 'segment alignment')
        require(any(p[1]&1 and p[3] <= self.entry < p[3]+p[5] for p in loads), 'entry is not loaded executable data')
        for name,address in FIXED.items():
            require(name in self.named and self.named[name][3]==address, 'fixed section drift: '+name)
        for s in self.sections:
            if s[2]&2 and s[5]:
                require(any(p[3]<=s[3] and s[3]+s[5]<=p[3]+p[6] and
                            (s[1]==8 or (s[3]+s[5]<=p[3]+p[5] and s[4]-p[2]==s[3]-p[3]))
                            for p in loads), 'allocated section not consistently loadable')
        return True


def compiled_cases(elf, manifest):
    rows=manifest['rows']; address,length,_,_=elf.symbols['cases']
    require(len(rows)==4 and length==1104*4, 'case ABI size')
    inputs=[]
    for i,row in enumerate(rows):
        data=elf.read(address+i*1104,1104)
        for n,field in enumerate(('id','scenario','method')):
            require(elf.cstring(struct.unpack_from('<Q',data,n*8)[0])==row[field], 'case text pointer mismatch')
        require(struct.unpack_from('<Q',data,24)[0]==elf.symbols[f't13_kernel_{i}'][0], 'wrong function dispatch')
        expected=(row['iterations'],row['dots'],sum(1<<r for r in row['scratch']),row['vtype'],len(row['outputs']),row['operands'][0])
        require(struct.unpack_from('<6I',data,32)==expected, 'case constants/dot count mismatch')
        require(data[80:592]==b''.join(bytes.fromhex(v) for v in row['before']), 'input registers mismatch')
        require(data[592:1104]==b''.join(bytes.fromhex(v) for v in row['expected']), 'full golden registers mismatch')
        stream,output=struct.unpack_from('<QQ',data,56); inputs.append(stream)
        for pointer,key in ((stream,'stream'),(output,'outputs')):
            wanted=b''.join(bytes.fromhex(v) for v in row[key])
            require(elf.read(pointer,len(wanted))==wanted, 'compiled '+key+' mismatch')
    require(all(x==inputs[0] and x%64==0 for x in inputs), 'inputs must use identical aligned addresses')
    address,length,_,_=elf.symbols['plan']
    require(length==16*len(manifest['plan']), 'plan ABI/cardinality')
    for i,item in enumerate(manifest['plan']):
        index,repeat,phase=struct.unpack('<IIQ',elf.read(address+16*i,16))
        require((index,repeat,elf.cstring(phase))==(item['index'],item['repeat'],item['phase']), 'compiled plan/order mismatch')


def inspect(elf_path, binary_path, reference_object, manifest, audit, *, allow_test_fixture=False):
    elf=ELF(Path(elf_path).read_bytes()); elf.executable(allow_test_fixture)
    require(Path(binary_path).read_bytes()==elf.binary(), 'ELF/bin load-image mismatch')
    compiled_cases(elf,manifest)
    obj=ELF(Path(reference_object).read_bytes())
    require(obj.kind==1, 'expected independently assembled relocatable reference')
    counts=[]
    for i,row in enumerate(manifest['rows']):
        name=f't13_kernel_{i}'
        code=elf.symbol_data(name)
        require(code==obj.symbol_data(name), 'linked kernel differs from independent assembly')
        address=elf.symbols[name][0]
        require(address%4096==0, 'kernel fixed alignment')
        report=audit.audit_kernel(code,address)
        require(report['counts']==audit.source_counts(row['body']), 'machine/source instruction mismatch')
        require(report['counts'].get('vdot.vv',0)==(row['dots'] if row['method']=='vdot' else 0), 'custom instruction identity/count')
        counts.append({k:v for k,v in report.items() if k!='instructions'})
    return dict(status='LINKED_ELF_STATIC_CHECK_PASS_NOT_DIFFTEST',elf_sha256=sha(elf_path),
                binary_sha256=sha(binary_path),kernels=counts,runtime_executed=False)


def verify_sources(repo):
    for name,wanted in PINNED.items():
        require(blob((Path(repo)/name).read_bytes())==wanted, 'pinned source drift: '+name)


def regenerate(build):
    build=Path(build); manifest=json.loads((build/'data/manifest.json').read_text())
    snapshot=build/'source/repo'
    verify_sources(snapshot)
    candidate=load('r2_pinned_candidate_regenerate',snapshot/REL/'candidate.py')
    with tempfile.TemporaryDirectory(prefix='r2-regenerate-') as tmp:
        directory=Path(tmp)/'data'
        fresh=candidate.generate(snapshot,directory,manifest['r2_variant'],manifest['dataset'],manifest['shard'],manifest['suite'])
        require(fresh==manifest, 'candidate manifest differs from exact regeneration')
        for name in ('kernels.S','cases.h'):
            require((directory/name).read_bytes()==(build/'data'/name).read_bytes(), 'generated source drift: '+name)
    for name in ('main.c','Makefile','fixed-layout.ld'):
        require((build/'source'/name).read_bytes()==(snapshot/O3/name).read_bytes(), 'harness/build source drift')
    return manifest


def verify_build(build, repo):
    build=Path(build); receipt=json.loads((build/'build.json').read_text())
    require(receipt.get('kind')=='nexus-am-riscv64-xs' and receipt.get('exit_code')==0, 'no successful real nexus-am build')
    require(set(receipt['artifacts'])=={'vdot-perf.elf','vdot-perf.bin','kernels-reference.o','data/manifest.json'}, 'artifact inventory')
    for path,digest in receipt['artifacts'].items():
        require(sha(build/path)==digest,'build artifact changed: '+path)
    manifest=regenerate(build)
    audit=load('r2_original_instruction_auditor',Path(repo)/'team/optimizations/o2/r2-kernel-audit/audit.py')
    result=inspect(build/'vdot-perf.elf',build/'vdot-perf.bin',build/'kernels-reference.o',manifest,audit)
    result['manifest_sha256']=sha(build/'data/manifest.json')
    return result
