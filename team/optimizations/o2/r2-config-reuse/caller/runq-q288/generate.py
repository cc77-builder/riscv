"""Fixed public runq Q-boundary fixture, strict binary32 goldens and plan."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import struct

HERE = Path(__file__).resolve().parent
REL = Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288')
spec = importlib.util.spec_from_file_location('runq_split_generate', HERE.parent/'split/generate.py')
split = importlib.util.module_from_spec(spec); spec.loader.exec_module(split)
CONFIG, S0, FIRST = split.CONFIG, split.S0, split.FIRST
INPUT_PINS, LEAVES, NEW = split.INPUT_PINS, split.LEAVES, split.NEW
raw, function, relocate, machine_certificate = split.raw, split.function, split.relocate, split.machine_certificate
CONTRACT = 'r2-s3-runq-q288-v1'
BASE = '3182e945df59dd5183b22e06103556496c6b1695'
CONSUMER = '350e04fe35433e6d2941dce5a1f53308f87058eb'
MAX_CYCLES = 30000000
FILES = ('q288.h','q288.c','oracle.c','main.c','caller.h','split.h','data.h',
         'timers.S','gemv.S','kernels.S','Makefile','manifest.json')

def digest(value): return hashlib.sha256(value).hexdigest()
def f32(value): return struct.unpack('<f', struct.pack('<f', value))[0]
def from_bits(value): return struct.unpack('<f', struct.pack('<I', value))[0]
def bits(value): return struct.unpack('<I', struct.pack('<f', value))[0]
def bytes8(values): return bytes(v & 255 for v in values)
def bytes32(values): return struct.pack('<'+'I'*len(values), *values)

def fixtures():
    w = [((r*17+k*29+(r^k)*7) % 255)-127 for r in range(288) for k in range(288)]
    w[:288] = [0]*288; w[0] = -1; w[32] = 1
    ws = [0x3c800000 + ((r*7213+g*104729+17) % 0x800000) for r in range(288) for g in range(9)]
    xs = [[0x3d000000+((d*34933+g*23419+31) % 0x800000) for g in range(9)] for d in range(3)]
    x = [[((k*43+(k*k)*3+11) % 255)-127 for k in range(288)],
         [127 if k%2 else -127 for k in range(288)], [0]*288]
    x[0][0] = x[0][32] = 1
    ws[0], xs[0][0], ws[1], xs[0][1] = 0x3d000000, 0x3d000000, 0x3d000001, 0x3cfffffe
    packed = [w[(8*t+r)*288+32*g+k] for t in range(36) for g in range(9) for r in range(8) for k in range(32)]
    gold, groups = [], []
    for d in range(3):
        y, dots = [], []
        for r in range(288):
            acc = 0.0
            for g in range(9):
                dot = sum(w[r*288+32*g+k]*x[d][32*g+k] for k in range(32))
                dots.append(dot)
                term = f32(f32(float(dot)*from_bits(ws[r*9+g]))*from_bits(xs[d][g]))
                acc = f32(acc+term)
            y.append(bits(acc))
        gold.append(y); groups.append(dots)
    assert gold[0][0] == 0 and all(v == 0 for v in gold[2])
    return dict(weight=w, weight_scale=ws, inputs=x, input_scale=xs,
                packed=packed, golden=gold, group_dots=groups)

MAKEFILE = '''NAME = vdot-perf
SRCS = main.c q288.c oracle.c timers.S kernels.S
INC_DIR += $(CURDIR)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
CFLAGS += -fno-ipa-cp -fno-ipa-icf -fno-optimize-sibling-calls -fno-lto -mno-relax -mabi=lp64d
CFLAGS += -ffp-contract=off -fno-fast-math
ifneq ($(CALLER_OBJ_ROOT),)
DST_DIR := $(CALLER_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
'''

def generate(repo, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    for name,pin in INPUT_PINS.items(): split.need(digest(raw(repo,name)) == pin, 'qualified input '+name)
    config = raw(repo,CONFIG/'public/gemv.S').decode()
    s0 = raw(repo,S0/'data/gemv.S.gz').decode()
    first = raw(repo,FIRST/'firstdot/public/gemv.S').decode()
    texts = [function(s0 if i in (1,2) else first if i == 4 else config, row[0]) for i,row in enumerate(LEAVES)]
    (out/'gemv.S').write_text(config)
    (out/'kernels.S').write_text('.option norvc\n.option norelax\n.text\n'+''.join(relocate(text,row[0],NEW[i],row[3]) for i,(text,row) in enumerate(zip(texts,LEAVES))))
    for name in ('q288.h','q288.c','oracle.c','main.c'): shutil.copyfile(HERE/name,out/name)
    shutil.copyfile(repo/CONFIG/'caller/caller.h',out/'caller.h')
    shutil.copyfile(HERE.parent/'split/split.h',out/'split.h')
    (out/'timers.S').write_text(split.timer())
    (out/'Makefile').write_text(MAKEFILE)
    data = fixtures()
    rows = [dict(id=i,kind='Q',algorithm=i,method='vdot' if i == 0 else 'rvv',
                 scenario='runq-q288',n=1,dots=10368 if i == 0 else 0,
                 leaf=NEW[i],wrapper='q288_full') for i in range(6)]
    rows.append(dict(id=6,kind='pack',algorithm=-1,method='pack',scenario='runq-q288-pack',n=1,dots=0,leaf=None,wrapper='q288_pack'))
    plan = [dict(index=6,phase='setup',repeat=0,dataset=0,block=-1,role='pack')]
    order = []
    for block in range(2):
        methods = list(range(6))[::1 if block == 0 else -1]
        for pos,method in enumerate([5]+methods+[5]):
            role = 'anchor_start' if pos == 0 else 'anchor_end' if pos == 7 else 'method'
            plan.append(dict(index=method,phase='measured',repeat=block,dataset=0,block=block,role=role))
            order.append(method)
    h = ['#include "q288.h"',f'#define Q_CONTRACT "{CONTRACT}"','#define Q_WINDOWS 17']
    def array(ctype,name,shape,values,fmt=str):
        h.append('static const '+ctype+' '+name+shape+' __attribute__((aligned(16),used)) = {')
        if values and isinstance(values[0],list): h.extend('{'+','.join(fmt(v) for v in row)+'},' for row in values)
        else:
            h.extend(','.join(fmt(v) for v in values[i:i+32])+',' for i in range(0,len(values),32))
        h.append('};')
    array('int8_t','q_weights','[82944]',data['weight'])
    array('float','q_weight_scale','[2592]',data['weight_scale'],lambda b:from_bits(b).hex()+'f')
    array('int8_t','q_inputs','[3][288]',data['inputs'])
    array('float','q_input_scale','[3][9]',data['input_scale'],lambda b:from_bits(b).hex()+'f')
    array('uint32_t','q_golden','[3][288]',data['golden'],lambda b:hex(b)+'u')
    array('int32_t','q_group_dots','[2592]',data['group_dots'][0])
    array('unsigned','q_order','[16]',order)
    h.append('split_leaf const split_entries[6] = {'+','.join(NEW)+'};')
    (out/'data.h').write_text('\n'.join(h)+'\n')
    hashes = dict(weight=digest(bytes8(data['weight'])),packed=digest(bytes8(data['packed'])),
                  weight_scale=digest(bytes32(data['weight_scale'])),
                  inputs=[digest(bytes8(v)) for v in data['inputs']],
                  input_scale=[digest(bytes32(v)) for v in data['input_scale']])
    manifest = dict(contract=CONTRACT,source_base=BASE,consumer_commit=CONSUMER,
        consumer='karpathy/llama2.c runq.c matmul, prequantized full Q boundary',
        shape=[288,288],group_size=32,tiles=36,groups=9,dataset=0,rows=rows,plan=plan,
        golden_y_bits=data['golden'],fixture_sha256=hashes,fp_contract='off',rounding='RNE',
        fma_witness=dict(row=0,strict_bits=0,fused_bits=0xa3800000),
        functional_calls=8,warmup_calls=6,conditioning_calls=16,full_q_calls=46,
        integer_sweep_leaf_calls=324,early_probe_leaf_calls=1,all_leaf_calls=15229,
        expected_dots=82976,custom_mask=0xfe00707f,custom_match=0x0200000b,
        formal_method_windows=12,formal_anchor_windows=4,pack_windows=1,
        max_cycles=MAX_CYCLES,extra_weight_storage_bytes=82944,
        synthetic_inputs=True,actual_model_checkpoint=False,includes_quantization=False,
        primary_metric='complete 288-output quantized Q projection including float consumption; pack separately',
        conditioning='one full RVV4 call then uniform output/slot/vector/floating state preparation',
        hardware_changed=False,stable_default_changed=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
