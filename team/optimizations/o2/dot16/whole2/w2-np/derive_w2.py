#!/usr/bin/env python3
"""Derive and GNU-check fixed K768 N/P kernels; no reference or target guest."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = 'dot16-w2-np-geometry-v1'
N_SOURCE_SHA = '4df1d70ddc5efadc202f20817d43cbc70c1601a2261549820308ed3fe02a315e'
P_SOURCE_SHA = '452ecab3ae3122dd8ea3d5ae05140197a10bb14a9a5ab76437f7591b00b29caf'
N_ELF_SHA = '82281d6fab843190321cdb21189f2feae848e2c1220e6a1ad0ec8bd883011b91'
HEADER_SHA = '605a28aef27442e6ea15cae94f2350cdd7ac69ed40af7ea501f9650d6606544e'
MODEL_SHA = '703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82'
HELPER_SHA = 'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'
TOOLS = {
    'gcc-11': '0c54895c55568be5b5fee49e2426abcc8fb05ca2c121ca5685dea2cbc24a1c13',
    'as': '30ab46dce94fa2120f9465dd2965784af831363f75fac42ea9999819f6d15953',
    'ld.bfd': '59db886faf252e5e2fb2e5341fd57c24ddbd216197f69296321fef913e5b64ba',
    'nm': '3f6c21492177e99a2a6db48d530d5ec310ed058c679bc71a743f80c86cb87b56',
    'objdump': '07a28885534079b220a44c7f787c0eecdd240fbe95c525b85e88cc7b88b70e82',
}
FUNCTIONS = {
    'N': dict(old='q288_dot16_whole8_narrow', new='q768_dot16_whole8_narrow', size=312,
              machine_sha256='050bc3db3e2a70bd6e5409cbf9c139868008e8ccb18776b7e0e7104e6a554b75',
              sites=((9,28,0,36,96),(14,6,0,9,24),(56,14,14,252,672))),
    'P': dict(old='q288_paired16_rvv', new='q768_paired16_rvv', size=1096,
              machine_sha256='a06e377e88a230929cc971acf91b0adf3ac27e52fd17ec72956ae7890ed7e73c',
              sites=((3,6,0,9,24),(25,28,0,36,96),(34,6,0,9,24),
                     (104,14,14,252,672),(135,28,0,36,96),
                     (140,6,0,9,24),(252,14,14,252,672))),
}
CHANGES = (('  li t3, 36\n','  li t3, 96\n'),
           ('  li t1, 9\n','  li t1, 24\n'),
           ('  addi a4, a4, 252\n','  addi a4, a4, 672\n'))
TOKEN = re.compile(r'[A-Za-z_.$][A-Za-z0-9_.$]*')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2)+'\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def extract_n(raw):
    name = FUNCTIONS['N']['old']
    text = raw.decode()
    start = '.balign 64\n.global '+name+'\n'
    end = '.size '+name+', .-'+name+'\n'
    need(text.count(start) == 1 and text.count(end) == 1, 'unique complete N function')
    lo = text.index(start)
    hi = text.index(end, lo)+len(end)
    result = text[lo:hi].encode()
    need(sha(result) == '9e8ac1b23a3c83258f03620245e0eac4e090d7cd4e1b93330c7f788a88852031',
         'frozen extracted N function identity')
    return result


def derive(raw, arm):
    spec = FUNCTIONS[arm]
    text = raw.decode()
    counts = (1,1,1) if arm == 'N' else (2,3,2)
    changed = text
    for (before, after), count in zip(CHANGES, counts):
        need(changed.count(before) == count and after not in changed, 'exact geometry sites')
        changed = changed.replace(before, after)
    labels = re.findall(r'^(\.L[A-Za-z0-9_.$]+):', changed, re.M)
    need(len(labels) == len(set(labels)), 'unique local label definitions')
    mapping = {name: name+'_k768' for name in labels}
    for token in TOKEN.findall(changed):
        if token == spec['old'] or token.startswith(spec['old']+'_'):
            mapping[token] = spec['new']+token[len(spec['old']):]
    need(spec['old'] in mapping and len(set(mapping.values())) == len(mapping), 'bijective names')
    need(not (set(mapping.values()) & set(TOKEN.findall(changed))), 'fresh label namespace')
    changed = TOKEN.sub(lambda m: mapping.get(m.group(), m.group()), changed)
    inverse = {v:k for k,v in mapping.items()}
    restored = TOKEN.sub(lambda m: inverse.get(m.group(), m.group()), changed)
    for before, after in reversed(CHANGES):
        restored = restored.replace(after, before)
    need(restored.encode() == raw, 'entire parent source recovered byte exactly')
    return changed.encode(), dict(parent_sha256=sha(raw), candidate_sha256=sha(changed.encode()),
        exact_inverse=True, geometry_site_counts=counts, renamed_tokens=mapping)


def expected_machine(parent, spec):
    need(len(parent) == spec['size'] and sha(parent) == spec['machine_sha256'], 'complete parent machine identity')
    words = list(struct.unpack('<'+'I'*(len(parent)//4), parent))
    for index, rd, rs1, old_imm, new_imm in spec['sites']:
        # ADDI opcode/funct3/rd/rs1 and I immediate, independent of GNU assembly.
        old_word = ((old_imm & 4095)<<20) | (rs1<<15) | (rd<<7) | 0x13
        new_word = ((new_imm & 4095)<<20) | (rs1<<15) | (rd<<7) | 0x13
        need(words[index] == old_word, 'original exact ADDI word at '+str(index))
        need((old_word & 0xfffff) == (new_word & 0xfffff), 'only I immediate changes')
        words[index] = new_word
    return struct.pack('<'+'I'*len(words), *words)


def run(a):
    deadline = time.monotonic()+a.budget_seconds
    os.sched_setaffinity(0, {a.cpu})
    os.nice(5)
    out = a.output.resolve()
    need(not out.exists(), 'fresh output directory')
    inputs = {
        a.n_image/'source/fused.S': N_SOURCE_SHA,
        a.n_image/'paired16-target.elf': N_ELF_SHA,
        a.n_image/'inputs/model.py': MODEL_SHA,
        a.n_image/'inputs/process_helper.py': HELPER_SHA,
        a.p_source: P_SOURCE_SHA, a.w2_header: HEADER_SHA,
    }
    tool_paths = {name:Path('/usr/bin/riscv64-linux-gnu-'+name) for name in TOOLS}
    inputs.update({tool_paths[k]:v for k,v in TOOLS.items()})
    for p, digest in inputs.items():
        need(sha(p.read_bytes()) == digest, 'frozen input '+str(p))
        need(out != p.resolve() and out not in p.resolve().parents, 'output cannot contain input')
    frozen_dirs = (a.n_image.resolve(), a.p_source.parent.resolve())
    for d in frozen_dirs:
        need(out not in d.parents and d not in out.parents and out != d, 'output separate from frozen trees')
    need(30 <= a.budget_seconds <= 300, 'bounded total budget')
    out.mkdir(parents=True)
    (out/'inputs').mkdir()
    snapshots = {'n-fused.S':a.n_image/'source/fused.S', 'p-paired16.S':a.p_source,
        'w2.h':a.w2_header, 'model.py':a.n_image/'inputs/model.py',
        'process_helper.py':a.n_image/'inputs/process_helper.py'}
    for name,p in snapshots.items():
        (out/'inputs'/name).write_bytes(p.read_bytes())
        need(sha((out/'inputs'/name).read_bytes()) == inputs[p], 'exact executable/input snapshot '+name)
    (out/'inputs'/'derive_w2.py').write_bytes(Path(__file__).read_bytes())
    model = module(out/'inputs/model.py', 'w2_np_frozen_elf')
    helper = module(out/'inputs/process_helper.py', 'w2_np_process')
    old_elf = model.ELF((a.n_image/'paired16-target.elf').read_bytes())
    parents = {'N':extract_n((a.n_image/'source/fused.S').read_bytes()), 'P':a.p_source.read_bytes()}
    candidates, derivation = {}, {}
    for arm,raw in parents.items():
        candidates[arm],derivation[arm] = derive(raw, arm)
    prefix = b'.option norvc\n.option norelax\n.text\n'
    (out/'parents.S').write_bytes(prefix+parents['N']+parents['P'])
    (out/'w2_np.S').write_bytes(prefix+candidates['N']+candidates['P'])
    save(out/'derivation.json', derivation)
    result = dict(schema=1,contract=CONTRACT,status='BUILDING',started=stamp(),
        cpu=a.cpu,nice=5,commands=[],pins={str(p):v for p,v in inputs.items()},
        controller_sha256=sha(Path(__file__).read_bytes()),
        geometry=dict(m=288,k=768,group_size=32,groups=24,tiles=36,vlen_bits=128,
            packed_bytes=221184,x_bytes=768,weight_scales=6912,input_scales=24,
            scale_row_stride_bytes=96,scale_tile_step_bytes=768,output_bytes=1152,slot_bytes=128),
        source_inverse_byte_exact=True,gnu_built=False,reference_qualified=False,
        target_runtime_qualified=False,performance_qualified=False,new_emu_runs=0,
        production_routes_modified=False)
    save(out/'result.json',result)
    pending = [None]
    def interrupt(signum, frame):
        if pending[0] is None:
            pending[0] = signum
    def check():
        if pending[0] is not None:
            raise InterruptedError('received signal '+str(pending[0]))
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    env = {**os.environ,'LANG':'C','LC_ALL':'C','OMP_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1',
           'TMPDIR':str(out)}
    def command(label, argv):
        check()
        remaining = deadline-time.monotonic()
        need(remaining > 0, 'total deadline')
        rec = dict(label=label,argv=list(map(str,argv)),started=stamp(),budget_seconds=min(30,remaining))
        result['commands'].append(rec)
        proc = None
        try:
            with (out/(label+'.log')).open('wb') as log:
                proc = subprocess.Popen(rec['argv'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                rec['pid'] = proc.pid
                save(out/'result.json',result)
                end = time.monotonic()+rec['budget_seconds']
                while True:
                    check()
                    left = end-time.monotonic()
                    if left <= 0:
                        raise subprocess.TimeoutExpired(rec['argv'],rec['budget_seconds'])
                    try:
                        rec['exit_code'] = proc.wait(timeout=min(.25,left))
                        break
                    except subprocess.TimeoutExpired:
                        continue
            need(rec['exit_code'] == 0, label+' failed')
            need(not helper.group_exists(proc.pid), label+' left child processes')
        finally:
            if proc is not None:
                if helper.group_exists(proc.pid):
                    rec['cleanup_complete'] = helper.stop_group(proc)
                rec['reaped'] = proc.poll() is not None
                rec['group_absent'] = not helper.group_exists(proc.pid)
            rec['finished'] = stamp()
            save(out/'result.json',result)
        return (out/(label+'.log')).read_text(errors='replace')
    try:
        nm_logs = {}
        built = {}
        for name in ('parents','w2_np'):
            command(name+'-assemble',[tool_paths['gcc-11'],'-march=rv64gcv','-mabi=lp64d',
                '-mcmodel=medany','-mno-relax','-fno-pic','-ffreestanding','-c',out/(name+'.S'),'-o',out/(name+'.o')])
            entry = FUNCTIONS['N']['old' if name=='parents' else 'new']
            command(name+'-link',[tool_paths['ld.bfd'],'--no-relax','--build-id=none','-Ttext=0x80000000',
                '-e',entry,'-o',out/(name+'.elf'),out/(name+'.o')])
            nm_logs[name] = command(name+'-nm',[tool_paths['nm'],'--format=bsd','--print-size','--radix=x',
                '--defined-only',out/(name+'.elf')])
            command(name+'-disassembly',[tool_paths['objdump'],'-d','-M','no-aliases',out/(name+'.elf')])
            built[name] = model.ELF((out/(name+'.elf')).read_bytes())
        records = {}
        for arm,spec in FUNCTIONS.items():
            parent = built['parents'].symbol_data(spec['old'])
            frozen = old_elf.symbol_data(spec['old'])
            need(parent == frozen, 'rebuilt parent equals frozen qualified Q288 ELF '+arm)
            expected = expected_machine(parent,spec)
            actual = built['w2_np'].symbol_data(spec['new'])
            need(actual == expected, 'complete GNU candidate equals independent I-field derivation '+arm)
            for key,symbol in (('parents',spec['old']),('w2_np',spec['new'])):
                rows = [line.split() for line in nm_logs[key].splitlines() if line.split() and line.split()[-1]==symbol]
                need(len(rows)==1 and len(rows[0])==4, 'unique complete GNU nm symbol '+symbol)
                need(int(rows[0][0],16)==built[key].symbols[symbol][0] and int(rows[0][1],16)==spec['size'],
                     'GNU nm address/size agrees with full ELF symbol '+symbol)
            old_words = struct.unpack('<'+'I'*(len(parent)//4),parent)
            new_words = struct.unpack('<'+'I'*(len(actual)//4),actual)
            diffs = [i for i,(x,y) in enumerate(zip(old_words,new_words)) if x!=y]
            need(diffs == [s[0] for s in spec['sites']], 'exact change index set '+arm)
            (out/(arm+'-parent.bin')).write_bytes(parent)
            (out/(arm+'-candidate.bin')).write_bytes(actual)
            records[arm] = dict(parent=spec['old'],candidate=spec['new'],bytes=len(actual),
                parent_sha256=sha(parent),candidate_sha256=sha(actual),changed_word_indices=diffs,
                changed_words=[dict(index=i,old=f'{old_words[i]:08x}',new=f'{new_words[i]:08x}') for i in diffs],
                frozen_parent_elf_equal=True,all_other_words_equal=True,
                complete_fp_csr_branches_fallback_preserved=True)
        check()
        for p,digest in inputs.items():
            need(sha(p.read_bytes())==digest,'unchanged input '+str(p))
        need(time.monotonic()<deadline, 'total deadline after final audit')
        result.update(status='K768_N_P_GNU_GEOMETRY_VERIFIED',gnu_built=True,functions=records,
            all_pins_unchanged=True,all_children_reaped=all(r['reaped'] and r['group_absent'] for r in result['commands']))
    except BaseException as exc:
        result.update(status='FAILED',error=type(exc).__name__+': '+str(exc))
        raise
    finally:
        result['finished'] = stamp()
        save(out/'result.json',result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('n-image','p-source','w2-header','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,choices=range(4),default=1)
    p.add_argument('--budget-seconds',type=int,default=180)
    args = p.parse_args()
    for name in ('n_image','p_source','w2_header','output'):
        setattr(args,name,getattr(args,name).resolve())
    print(json.dumps(run(args),indent=2))
