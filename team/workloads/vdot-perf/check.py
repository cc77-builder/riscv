"""Strict offline T13 evidence checking. Integer counters never pass through float."""
import argparse
import hashlib
import gzip
import io
import json
from pathlib import Path
import re
import struct
import tempfile
import types

START, STOP = 0x51300013, 0x51400013
COUNTERS = [0xc0202773, 0xc0002873, 0xc00028f3, 0xc02027f3]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(raw_bytes(path)).hexdigest()


def raw_bytes(path):
    path=Path(path)
    if path.exists():return path.read_bytes()
    compressed=Path(str(path)+'.gz')
    require(compressed.exists(),'missing artifact '+str(path))
    return gzip.decompress(compressed.read_bytes())


def read_text(path):
    # Preserve raw bytes for SHA; normalize UART CRLF only for parsing.
    return io.TextIOWrapper(io.BytesIO(raw_bytes(path)), encoding='utf-8', newline=None).read()


def signed(value, width):
    return value - (1 << width) if value & (1 << (width-1)) else value


def elf_data(path):
    data=Path(path).read_bytes()
    require(data[:6]==b'\x7fELF\x02\x01','ELF format')
    shoff=struct.unpack_from('<Q',data,40)[0];size,count=struct.unpack_from('<HH',data,58)
    sections=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+i*size) for i in range(count)]
    symbols={}
    for sec in sections:
        if sec[1]!=2:continue
        strings=sections[sec[6]];names=data[strings[4]:strings[4]+strings[5]]
        for at in range(sec[4],sec[4]+sec[5],sec[9]):
            name,_,_,section,address,length=struct.unpack_from('<IBBHQQ',data,at)
            name=names[name:names.find(b'\0',name)].decode()
            if name:symbols[name]=(address,length)
    def read(address,length):
        for sec in sections:
            if sec[2]&2 and sec[1]!=8 and sec[3]<=address and address+length<=sec[3]+sec[5]:
                offset=sec[4]+address-sec[3];return data[offset:offset+length]
        raise ValueError('ELF address outside allocated file data')
    return symbols,read


def check_compiled_cases(path,manifest):
    symbols,read=elf_data(path)
    address,length=symbols['cases']
    # rv64 LP64 ABI, with the explicit 16-byte aligned before[32][16] member.
    stride=1104
    require(length==stride*len(manifest['rows']),'compiled case ABI size')
    pointers=[]
    for i,row in enumerate(manifest['rows']):
        data=read(address+i*stride,stride)
        entry=struct.unpack_from('<Q',data,24)[0]
        require(entry==symbols[f't13_kernel_{i}'][0],'compiled entry pointer')
        expected=(row['iterations'],row['dots'],sum(1<<r for r in row['scratch']),row['vtype'],len(row['outputs']),row['operands'][0])
        require(struct.unpack_from('<6I',data,32)==expected,'compiled iteration/scratch/CSR constants')
        require(data[80:592]==b''.join(bytes.fromhex(x) for x in row['before']),'compiled input vector bytes')
        require(data[592:1104]==b''.join(bytes.fromhex(x) for x in row['expected']),'compiled full-register golden bytes')
        stream,outputs=struct.unpack_from('<QQ',data,56);pointers.append(stream)
        if row['stream']:
            wanted=b''.join(bytes.fromhex(x) for x in row['stream'])
            require(read(stream,len(wanted))==wanted,'compiled stream input')
        if row['outputs']:
            wanted=b''.join(bytes.fromhex(x) for x in row['outputs'])
            require(read(outputs,len(wanted))==wanted,'compiled stream golden')
    if manifest.get('shared_stream'):
        require(all(p%64==0 for p in pointers),'stream alignment')
        for i,row in enumerate(manifest['rows']):
            for j,other in enumerate(manifest['rows']):
                if row['stream']==other['stream']:require(pointers[i]==pointers[j],'paired input addresses differ')


def elf_kernels(path):
    data = Path(path).read_bytes()
    require(data[:6] == b'\x7fELF\x02\x01', 'ELF64 little endian required')
    shoff = struct.unpack_from('<Q', data, 40)[0]
    size, count = struct.unpack_from('<HH', data, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, shoff+i*size) for i in range(count)]
    result = {}
    for sec in sections:
        if sec[1] != 2:
            continue
        strings = sections[sec[6]]
        names = data[strings[4]:strings[4]+strings[5]]
        for at in range(sec[4], sec[4]+sec[5], sec[9]):
            name, _, _, section, address, length = struct.unpack_from('<IBBHQQ', data, at)
            name = names[name:names.find(b'\0', name)].decode()
            if not re.fullmatch(r't13_kernel_\d+', name):
                continue
            owner = sections[section]
            offset = owner[4]+address-owner[3]
            require(length % 4 == 0 and address % 64 == 0, 'kernel size/alignment')
            words = {address+i:struct.unpack_from('<I', data, offset+i)[0] for i in range(0,length,4)}
            require(all(w & 3 == 3 for w in words.values()), 'compressed kernel instruction')
            result[int(name.rsplit('_',1)[1])] = words
    require(result, 'no kernels')
    return result


def walk(words):
    """Bounded machine-code walk; only the generated t6 loop may branch."""
    starts = [pc for pc,w in words.items() if w == START]
    stops = [pc for pc,w in words.items() if w == STOP]
    require(len(starts) == len(stops) == 1, 'unique markers')
    pc, stop = starts[0], stops[0]
    result, t6 = [], None
    while True:
        require(pc in words and len(result) < 20000, 'escaped/unbounded kernel')
        word = words[pc]
        result.append((pc,word))
        if pc == stop:
            break
        op, rd, rs1, rs2 = word & 127, (word>>7)&31, (word>>15)&31, (word>>20)&31
        if rd == 31 and op == 0x13:
            require(((word>>12)&7) == 0 and rs1 in (0,31), 'unsupported loop write')
            t6 = (0 if rs1 == 0 else t6)+signed(word>>20,12)
        if op == 0x63:
            require((word>>12)&7 == 1 and rs1 == 31 and rs2 == 0 and t6 is not None, 'unexpected branch')
            imm = ((word>>31)<<12) | (((word>>7)&1)<<11) | (((word>>25)&63)<<5) | (((word>>8)&15)<<1)
            pc += signed(imm,13) if t6 != 0 else 4
        else:
            require(op not in (0x6f,0x67), 'call/jump inside window')
            pc += 4
    counters = [(pc,w) for pc,w in result if w in COUNTERS]
    require([w for _,w in counters] == COUNTERS, 'counter order')
    return result


FIELDS = {
 'COUNTER_ENQUEUE': r'cycle=\s*(\d+) rob=(\d+):\s*(\d+) pc=0x([0-9a-f]+) word=0x([0-9a-f]+) empty=(\d+) wait=(\d+) block=(\d+)',
 'CSR_SAMPLE': r'cycle=\s*(\d+) addr=0x([0-9a-f]+) data=0x([0-9a-f]+) wen=(\d+)',
 'RETIRE': r'cycle=\s*(\d+) slot=(\d+) rob=(\d+):\s*(\d+) pc=0x([0-9a-f]+) word=0x([0-9a-f]+) count=(\d+) data=0x([0-9a-f]+)',
}


def parse_events(text):
    events = {key:[] for key in FIELDS}
    for line in text.splitlines():
        if not line.startswith('T13_'):
            continue
        tag, _, body = line.partition(' ')
        key = tag[4:]
        require(key in FIELDS, 'unknown hardware event '+tag)
        m = re.fullmatch(FIELDS[key],body)
        require(m is not None, 'malformed hardware event '+line)
        values = m.groups()
        hexes = {'COUNTER_ENQUEUE':(3,4),'CSR_SAMPLE':(1,2),'RETIRE':(4,5,7)}[key]
        v = [int(x,16 if i in hexes else 10) for i,x in enumerate(values)]
        if key == 'COUNTER_ENQUEUE':
            row = dict(zip(('cycle','flag','rob','pc','word','empty','wait','block'),v))
        elif key == 'CSR_SAMPLE':
            row = dict(zip(('cycle','addr','data','wen'),v))
        else:
            row = dict(zip(('cycle','slot','flag','rob','pc','word','count','data'),v))
        require(all(x >= 0 for x in v) and row.get('data',0) < 1<<64, 'event overflow')
        events[key].append(row)
    for key, rows in events.items():
        require(all(a['cycle'] <= b['cycle'] for a,b in zip(rows,rows[1:])), 'event time reversal '+key)
    return events


def trace_windows(events, manifest, kernels):
    retires = events['RETIRE']
    windows, current = [], None
    for event in retires:
        if event['word'] == START:
            require(current is None, 'nested marker')
            current = []
        if current is not None:
            current.append(event)
        else:
            # The active flag can include later slots on the stop-marker cycle.
            require(windows and event['cycle'] == windows[-1][-1]['cycle'] and event['word'] not in COUNTERS, 'retire outside marker')
        if event['word'] == STOP:
            require(current is not None, 'stop without start')
            windows.append(current)
            current = None
    require(current is None and len(windows) == len(manifest['plan']), 'missing/extra windows')
    enq, samples = events['COUNTER_ENQUEUE'], events['CSR_SAMPLE']
    require(len(enq) == len(samples) == 4*len(windows), 'counter event count')
    output = []
    for index,(window,entry) in enumerate(zip(windows,manifest['plan'])):
        row = manifest['rows'][entry['index']]
        path = walk(kernels[entry['index']])
        pos = 0
        for event in window:
            require(pos < len(path), 'extra retired instruction')
            require((event['pc'],event['word']) == path[pos], f'retirement PC/word mismatch seq={index} position={pos}')
            require(1 <= event['count'] <= 8, 'retirement count range')
            # Compressed ROB entries must cover contiguous, non-control words.
            covered = path[pos:pos+event['count']]
            require(len(covered) == event['count'], 'retirement overrun')
            if len(covered)>1:
                require(all(pc == covered[0][0]+4*j for j,(pc,_) in enumerate(covered)), 'noncontiguous ROB compression')
                require(all(w not in COUNTERS and w not in (START,STOP) and w&127 != 0x63 for _,w in covered), 'control in compressed retirement')
            pos += event['count']
        require(pos == len(path), 'incomplete retirement')
        counters = [e for e in window if e['word'] in COUNTERS]
        require([e['word'] for e in counters] == COUNTERS, 'retired counter sequence')
        local_samples = samples[4*index:4*index+4]
        for j,(q,s,t) in enumerate(zip(enq[4*index:4*index+4],local_samples,counters)):
            require(all(q[k] == t[k] for k in ('flag','rob','pc','word')), 'counter identity mismatch')
            require(q['cycle'] <= s['cycle'] < t['cycle'] and s['addr'] == COUNTERS[j]>>20 and s['wen'] == 0, 'counter sampling bounds')
            require(s['data'] == t['data'], 'CSR sample/writeback mismatch')
            # Every counter is immediately preceded/followed by a retiring
            # fence in v2. No inference from rdcycle serialization is needed.
            k = window.index(t)
            require(k > 0 and window[k-1]['word'] == 0x0330000f, 'missing previous fence')
            require(window[k-1]['cycle'] < s['cycle'], 'counter overtook previous fence')
            require(k+1 < len(window) and window[k+1]['word'] == 0x0330000f, 'missing following fence')
            require(window[k+1]['cycle'] > t['cycle'], 'following fence did not drain counter')
        a,b,c,d = local_samples
        cycles, instructions = c['data']-b['data'], d['data']-a['data']
        require(0 < cycles < (1<<32) and instructions > 0, 'counter overflow/reversal')
        require(cycles == c['cycle']-b['cycle'], 'cycle CSR/global clock disagreement')
        retired_between = sum(e['count'] for e in window if a['cycle'] <= e['cycle'] < d['cycle'])
        static_between = next(i for i,(_,w) in enumerate(path) if w == COUNTERS[-1])-next(i for i,(_,w) in enumerate(path) if w == COUNTERS[0])
        require(instructions == retired_between == static_between, f'instret disagreement seq={index}: csr={instructions}, events={retired_between}, elf={static_between}')
        body = path[next(i for i,(_,w) in enumerate(path) if w == COUNTERS[1])+2:next(i for i,(_,w) in enumerate(path) if w == COUNTERS[2])-1]
        vdot_count = sum(w&0xfe00707f == 0x0200000b for _,w in body)
        require(vdot_count == (row['dots'] if row['method']=='vdot' else 0), 'wrong custom instruction count')
        output.append(dict(seq=index,id=row['id'],scenario=row['scenario'],method=row['method'],n=row['n'],dots=row['dots'],phase=entry['phase'],repeat=entry['repeat'],dataset=manifest['dataset'],cycles=cycles,instructions=instructions,counter_values=[s['data'] for s in local_samples],sample_ticks=[s['cycle'] for s in local_samples]))
    return output


def check_uart(text, manifest, results):
    lines = [line for line in text.splitlines() if line.startswith('T13_')]
    expected_begin = f"T13_BEGIN suite={manifest['suite']} dataset={manifest['dataset']} plan={len(manifest['plan'])} contract={manifest['contract']}"
    require(lines and lines[0] == expected_begin, 'UART begin')
    require(lines[-1] == f"T13_SUMMARY executed={len(manifest['plan'])} failures=0 scratch_control=1", 'UART summary')
    require(lines.count('T13_CONTROLS detected=6 expected=6') == 1, 'negative controls')
    require(lines.count('T13_SCRATCH_CONTROL allowed=1') == 1, 'scratch control')
    records = [line for line in lines if line.startswith(('T13_P ','T13_CASE '))]
    require(len(records) == len(results) and len(lines) == len(results)+4, 'UART record cardinality')
    for line,item,entry in zip(records,results,manifest['plan']):
        row = manifest['rows'][entry['index']]
        if manifest['compact']:
            require(line == f"T13_P seq={item['seq']} c={item['cycles']} i={item['instructions']}", 'UART/trace delta disagreement')
        else:
            a,b,c,d = item['counter_values']
            dest = bytes.fromhex(row['expected'][row['operands'][0]])[::-1].hex()
            wanted = f"T13_CASE seq={item['seq']} id={row['id']} phase={entry['phase']} repeat={entry['repeat']} result=PASS cycles={b},{c} instret={a},{d} iterations={row['iterations']} csr={row['vtype']}/8/0/3/1/7/0 dest={dest} checked_regs={32-len(row['scratch'])} stream_checked={len(row['outputs'])}"
            require(line == wanted, 'UART/trace/state disagreement')
    require('Difftest enabled.' in text and text.count('HIT GOOD TRAP') == 1, 'missing live DiffTest/GOOD TRAP')
    require(text.find('HIT GOOD TRAP') > text.find('T13_SUMMARY'), 'trap before summary')
    require(not re.search(r'T13_FAIL|HIT BAD TRAP|DIFFTEST FAIL|ABORT',text), 'failure in stdout')


def verify_generation(build, manifest):
    """Regenerate from the exact generator stored with this image's receipt."""
    source=build/'source/generate.py'
    require(source.exists(),'missing source snapshot')
    receipt=json.loads((build/'build.json').read_text())
    recorded=receipt.get('software',receipt.get('software_files',{}))
    for name in ('generate.py','main.c','Makefile'):
        keys=[k for k in recorded if k.rsplit('/',1)[-1]==name]
        require(len(keys) == 1 and sha(build/'source'/name)==recorded[keys[0]],'build source hash missing/ambiguous/mismatch '+name)
    module=types.ModuleType('t13_archived_generator')
    module.__file__=str(Path(__file__).with_name('generate.py'))
    exec(compile(source.read_text(),str(source),'exec'),module.__dict__)
    with tempfile.TemporaryDirectory(prefix='t13-regenerate-') as temp:
        extra={'shared_stream':True} if manifest.get('shared_stream') else {}
        fresh=module.generate(Path(temp)/'data',manifest['suite'],manifest['dataset'],manifest.get('shard',0),manifest.get('shards',1),**extra)
        require(set(fresh) == set(manifest), 'generated manifest field inventory drift')
        for key in set(fresh) - {'files'}:
            require(fresh[key]==manifest[key],'generated manifest drift '+key)
        # The archived generator used platform text writes. Reproduce its Linux
        # LF output on Windows without altering the frozen source or artifacts.
        require(set(fresh['files'])=={'kernels.S','cases.h'},'unexpected generated files')
        lf_files={}
        for name,digest in fresh['files'].items():
            data=(Path(temp)/'data'/name).read_bytes()
            require(hashlib.sha256(data).hexdigest()==digest,'fresh generator hash mismatch')
            lf_files[name]=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
        require(lf_files==manifest['files'],'generated manifest drift files')


AM_REVISION = '086a238062fdfb3281b745a537b361983d0154b5'

# The first calibration predates complete receipts. Only these exact frozen
# bytes qualify; deleting fields from a newer receipt cannot enable this path.
CALIBRATION_BUILD = {
    'build.json': '93a5236d38ec76692fd685debe52dc816450422e8048edc40c85d0ac4354c8d4',
    'vdot-perf.bin': 'eaa629045d96327807fb967cf179549f07ba3c2e78dc8b013f6671386ea9318f',
    'vdot-perf.elf': '1f2f2afcd507d62eab242a5e1ab13dc239a2b420c0350bf6a266faa7dbe73e30',
    'data/manifest.json': 'c6233496ed88f9c5d6422343b7420633fd6f4b9085885d3e40b5d92351fe1753',
}
CALIBRATION_RUN = {
    'result.json': '0abb0046b89d498c7ee7953bae624f3ad0ba074a8daf06e734a4fd3ad206b4d4',
    'stdout.log': '8bdc3763ef0811c0d9307576755810cdf0616e882722fb79492a226a728e0355',
    'stderr.log': 'd8e4678dad27aa56def37cf2d553333ab86cc14791c01f2d9fbd27bf97baf6f4',
}


def runtime_roles(command, *, legacy_calibration=False):
    """Parse the supported EMU invocation without tolerating overriding flags."""
    require(isinstance(command, list) and all(isinstance(x, str) for x in command), 'runtime command missing')
    args = list(command)
    if args and args[0] == 'timeout':
        require(len(args) > 3 and re.fullmatch(r'[1-9][0-9]*[smh]?', args[1]), 'invalid timeout wrapper')
        args = args[2:]
    require(bool(args) and args[0].startswith('/'), 'absolute EMU path required')
    emu, options = args[0], {}
    i = 1
    allowed = {'-i', '--flash', '--ram-size', '--diff', '--max-cycles', '--seed'}
    while i < len(args):
        option, sep, value = args[i].partition('=')
        require(option in allowed and option not in options, 'unknown/duplicate runtime option '+option)
        if not sep:
            i += 1
            require(i < len(args), 'missing runtime argument')
            value = args[i]
        options[option] = value
        i += 1
    require({'-i', '--flash', '--ram-size', '--diff', '--max-cycles'} <= set(options), 'incomplete runtime roles')
    require(legacy_calibration or options.get('--seed') == '1', 'missing fixed replay seed')
    require(options['--ram-size'] == '128MB', 'wrong RAM configuration')
    require(options['--max-cycles'].isdigit() and int(options['--max-cycles']) > 0, 'invalid cycle bound')
    if '--seed' in options:
        require(options['--seed'] == '1', 'wrong deterministic seed')
    roles = {'emu': emu, 'image': options['-i'], 'reference': options['--diff'], 'flash': options['--flash']}
    require(len(set(roles.values())) == 4 and all(p.startswith('/') for p in roles.values()), 'runtime role paths overlap or are relative')
    return roles


def verify_build_record(build, legacy=False):
    record = json.loads((build/'build.json').read_text())
    require(record.get('exit_code') == 0, 'build failed or incomplete')
    require(not record.get('verification_error'), 'build verification failed')
    if legacy:
        require(all(sha(build/name) == digest for name, digest in CALIBRATION_BUILD.items()), 'legacy calibration build drift')
    else:
        require(re.fullmatch(r'[0-9a-f]{40}', record.get('source', '')), 'missing build source commit')
        require(record.get('am_revision') == AM_REVISION, 'wrong AM revision')
        artifacts = record.get('artifacts', {})
        require(set(artifacts) == {'vdot-perf.bin', 'vdot-perf.elf', 'manifest.json'}, 'incomplete build artifact binding')
        for name, digest in artifacts.items():
            require(sha(build/('data' if name == 'manifest.json' else '')/name) == digest, 'build artifact mismatch '+name)
    return record


def verify(build, run, external=None):
    build,run = Path(build),Path(run)
    receipt = json.loads((run/'result.json').read_text())
    require(receipt['exit_code'] == 0, 'EMU nonzero/incomplete')
    require(not receipt.get('verification_error'), 'runtime inputs changed')
    legacy = sha(run/'result.json') == CALIBRATION_RUN['result.json']
    if legacy:
        require(all(sha(run/name) == digest for name, digest in CALIBRATION_RUN.items()), 'legacy calibration log drift')
    else:
        require(receipt.get('single_core') is True and receipt.get('emu_threads') == 1, 'wrong core/thread configuration')
        require(set(receipt.get('raw_sha256', {})) == {'stdout.log', 'stderr.log'}, 'incomplete raw transcript binding')
    roles = runtime_roles(receipt.get('command'), legacy_calibration=legacy)
    require(set(receipt.get('files', {})) == set(roles.values()), 'incomplete runtime input binding')
    verify_build_record(build, legacy)
    for file,digest in receipt['files'].items():
        if file == roles['image']:
            require(sha(build/'vdot-perf.bin')==digest,'loaded image mismatch')
        elif external is not None:
            require(external.get(file)==digest,'external artifact pin mismatch '+file)
        else:
            require(sha(file) == digest, 'runtime input hash mismatch '+file)
    for file,digest in receipt.get('raw_sha256',{}).items():
        require(sha(run/file)==digest,'raw transcript hash mismatch')
    manifest = json.loads((build/'data/manifest.json').read_text())
    require(manifest['boundary'] == 'pinned-XiangShan-fence-serialized-v2','uncalibrated boundary')
    for file,digest in manifest['files'].items():
        require(Path(file).name == file, 'unsafe generated filename')
        require(sha(build/'data'/file) == digest, 'generated hash mismatch')
    verify_generation(build,manifest)
    check_compiled_cases(build/'vdot-perf.elf',manifest)
    stderr=read_text(run/'stderr.log')
    require(not re.search(r'Assertion.*failed|different at pc|DIFFTEST FAIL',stderr),'failure in stderr')
    results = trace_windows(parse_events(stderr),manifest,elf_kernels(build/'vdot-perf.elf'))
    check_uart(read_text(run/'stdout.log'),manifest,results)
    return dict(status='PASS',scope='full-core DiffTest, exact state and calibrated CSR windows',samples=results,raw_sha256={f:sha(run/f) for f in ('stdout.log','stderr.log')},image_sha256=sha(build/'vdot-perf.bin'),elf_sha256=sha(build/'vdot-perf.elf'),manifest_sha256=sha(build/'data/manifest.json'))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=verify(a.build,a.run)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=result['status'],samples=len(result['samples']))))
