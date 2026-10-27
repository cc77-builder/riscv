"""Generate the six exact address-relocated leaves and fixed single-image plan."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil
import struct

HERE = Path(__file__).resolve().parent
REL = Path('team/optimizations/o2/r2-config-reuse/caller/split')
CONTRACT = 'r2-s3-split-input-8x32-v2'
BASE = '71b24fc43a7111abae1012d0c4bcaf89f249300f'
CONFIG = REL.parent.parent
S0 = Path('team/optimizations/o2/r2-select/evidence/entry-v1/files/builds/build-probe-01/images/performance-s0-d0-s03')
FIRST = Path('team/optimizations/o2/r2-vector-accum')
INPUT_PINS = {
    str(CONFIG/'public/gemv.S'): '9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2',
    str(CONFIG/'caller/hoisted/caller.c'): '141d1789e5cf8e55ba5463e1ed246868bc94bdeee3daf9006f6f0e134fb6e75b',
    str(S0/'data/gemv.S.gz'): 'dce2a2e16e2051c140c82c661cfd392d9a1a32941e043b75821aaf3436d554c3',
    str(S0/'gemv-reference.o.gz'): '2a034f57cce082566bccf0d7f07d0950370af8a59b1f186bcaeefb95908e16a5',
    str(FIRST/'firstdot/public/gemv.S'): '1e1aa8ca665559efa6acab2648f4614c6121422aaf400d78c192e6accad5da47',
    str(FIRST/'evidence/firstdot-v1/library/member-extract/stdout.log'): 'b65d4ca4faf3550ad2e95d3fb7d1d452923b71ae50776420bfcd679d098238af',
}
# symbol, size, SHA256, x-address count, bytes read by each vector load
LEAVES = (
    ('config_reuse_gemv_8x32_reuse_vdot',656,'3bca83077ccd7529ff6f80c9002441c99d27d3113aa8b10769ad26f3c4e9c64d',4,8),
    ('r4_gemv_8x32_basic_rvv',1060,'6f7c75562128eecc42c54ef840d0a6d04bd9446a4703e595ee61ffa432b5ecbe',16,16),
    ('r4_gemv_8x32_reuse_rvv',740,'20ee57db9abe4bf501608dc6680ff9ccc39c7ccd5fcadb637026da20edc2afc4',2,16),
    ('config_reuse_gemv_8x32_basic_rvv',676,'c33e1fb01a939cf68d4a867a5daf6b5fe4dc7bf9536d644808949ef555052def',16,16),
    ('firstdot_gemv_8x32_reuse_rvv',452,'f304ee128fbac736755d1fe7d03b6d8e8f6ea30e625dc1937f379445e6c23137',2,16),
    ('config_reuse_gemv_8x32_reuse_rvv',448,'ea86a50cd67113246dae98ef7ce8db4e0d1383f453d889c6aad6cf2579857513',2,16),
)
NEW = tuple('split_gemv_8x32_'+('vdot' if i==0 else 'rvv'+str(i-1)) for i in range(6))
FILES = ('caller.h','caller.c','split.h','split.c','main.c','data.h','timers.S','gemv.S','strong.S','kernels.S','Makefile','manifest.json')

def need(ok,msg):
    if not ok: raise ValueError(msg)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def raw(repo,name):
    value=(repo/name).read_bytes()
    return gzip.decompress(value) if str(name).endswith('.gz') else value
def function(text,name):
    found=re.findall(r'(?m)^\.global '+re.escape(name)+r'\n.*?^\.size '+re.escape(name)+r',[^\n]*\n',text,re.S|re.M)
    need(len(found)==1,'unique source function: '+name)
    return found[0]
def relocate(text,old,new,count):
    need(text.count('  mv a2, a0\n  mv a3, a1\n')==1,'old prologue')
    body=text.split(old+':\n',1)[1].split('.size ',1)[0]
    need(sum(bool(re.search(r'\ba1\b',line)) for line in body.splitlines())==1,'a1 is not reserved for new x')
    body=body.replace('  mv a2, a0\n  mv a3, a1\n','  mv a3, a2\n  mv a2, a0\n')
    hits=[]
    def replace(m):
        offset=int(m[1]); need(offset in (256,264,272,280),'x immediate')
        hits.append(offset)
        return '  addi t6, a1, '+str(offset-256)
    body=re.sub(r'  addi t6, a2, (2[5-8][0-9])(?=\n)',replace,body)
    need(len(hits)==count,'x source count')
    return '.balign 16\n.global '+new+'\n.type '+new+', @function\n'+new+':\n'+body+'.size '+new+', .-'+new+'\n'

def machine_certificate(before,after,kind):
    """An independent allow-list over *all* final machine words, not text diff."""
    name,size,pin,count,load_bytes=LEAVES[kind]
    need(len(before)==len(after)==size and (pin is None or digest(before)==pin),'qualified old length/hash')
    left=list(struct.unpack('<'+'I'*(size//4),before));right=list(struct.unpack('<'+'I'*(size//4),after))
    need(all(w&3==3 for w in left+right),'compressed instruction')
    def addi(rd,rs,imm): return ((imm&4095)<<20)|(rs<<15)|(rd<<7)|0x13
    need(left[:2]==[addi(12,10,0),addi(13,11,0)] and right[:2]==[addi(13,12,0),addi(12,10,0)],'three-argument prologue')
    expected=list(left);expected[:2]=right[:2];positions=[]
    for i,w in enumerate(left[2:],2):
        if w&0x000fffff==addi(31,12,0)&0x000fffff and (w>>20) in (256,264,272,280):
            expected[i]=addi(31,11,(w>>20)-256);positions.append(i)
    need(len(positions)==count and expected==right,'unapproved split machine word change')
    need(sum(w&0xfe00707f==0x0200000b for w in right)==(32 if kind==0 else 0),'custom count')
    return dict(old=name,new=NEW[kind],bytes=size,old_sha256=digest(before),new_sha256=digest(after),
                changed_words=[0,1]+positions,x_address_words=count,vector_load_bytes=load_bytes,
                arithmetic_csr_and_stores_exact=True)

def timer():
    # Same fence/counter protocol and saved-register frame as the existing timer.
    return '''.option norvc
.option norelax
.text
.balign 64
.global split_measure
.type split_measure, @function
split_measure:
  addi sp, sp, -48
  sd ra, 0(sp)
  sd s0, 8(sp)
  sd s1, 16(sp)
  sd s2, 24(sp)
  sd s3, 32(sp)
  sd s4, 40(sp)
  mv s0, a0
  mv s1, a1
  mv s4, a2
  fence rw,rw
  .word 0x51300013
  fence rw,rw
  csrr a4, instret
  fence rw,rw
  csrr a6, cycle
  fence rw,rw
  mv s2, a4
  mv s3, a6
  mv a0, s0
  jalr ra, 0(s4)
  fence rw,rw
  csrr a7, cycle
  fence rw,rw
  csrr a5, instret
  fence rw,rw
  .word 0x51400013
  fence rw,rw
  sub a7, a7, s3
  sub a5, a5, s2
  sd a7, 0(s1)
  sd a5, 8(s1)
  ld ra, 0(sp)
  ld s0, 8(sp)
  ld s1, 16(sp)
  ld s2, 24(sp)
  ld s3, 32(sp)
  ld s4, 40(sp)
  addi sp, sp, 48
  ret
.size split_measure, .-split_measure
'''

MAKEFILE='''NAME = vdot-perf
SRCS = main.c caller.c split.c timers.S gemv.S strong.S kernels.S
INC_DIR += $(CURDIR)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
CFLAGS += -fno-ipa-cp -fno-ipa-icf -fno-optimize-sibling-calls -fno-lto -mno-relax -mabi=lp64d
ifneq ($(CALLER_OBJ_ROOT),)
DST_DIR := $(CALLER_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
'''

def generate(repo,out,base_inputs):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    for name,pin in INPUT_PINS.items(): need(digest(raw(repo,name))==pin,'input identity: '+name)
    config=raw(repo,str(CONFIG/'public/gemv.S')).decode()
    s0=raw(repo,str(S0/'data/gemv.S.gz')).decode();first=raw(repo,str(FIRST/'firstdot/public/gemv.S')).decode()
    texts=[function(s0 if i in (1,2) else first if i==4 else config,row[0]) for i,row in enumerate(LEAVES)]
    split='.option norvc\n.option norelax\n.text\n'+''.join(relocate(t,row[0],NEW[i],row[3]) for i,(t,row) in enumerate(zip(texts,LEAVES)))
    strong='.option norvc\n.option norelax\n.text\n'+''.join('.balign 16\n'+texts[i] for i in (1,2,4))
    for name in ('split.h','split.c','main.c'): shutil.copyfile(HERE/name,out/name)
    shutil.copyfile(repo/CONFIG/'caller/caller.h',out/'caller.h')
    shutil.copyfile(repo/CONFIG/'caller/hoisted/caller.c',out/'caller.c')
    (out/'gemv.S').write_text(config);(out/'strong.S').write_text(strong);(out/'kernels.S').write_text(split)
    (out/'timers.S').write_text(timer());(out/'Makefile').write_text(MAKEFILE)
    inputs=[]
    for d in range(3):
        a,x=base_inputs(8,32,d);inputs.append([int(v) for row in a for v in row]+[int(v) for v in x])
    inputs += [[-128]*288,[127]*288,[-128]*256+[127]*32,[0]*288]
    rows=[]
    for mode in ('packed','split'):
        for i,old in enumerate(LEAVES):
            rows.append(dict(id=len(rows),mode=mode,algorithm=i,method='vdot' if i==0 else 'rvv',
                scope='full',scenario='split-input',n=1,dots=32 if i==0 else 0,
                leaf=NEW[i] if mode=='split' else old[0],wrapper='split_full' if mode=='split' else 'caller_full',anchor=False))
    rows.append(dict(rows[6],id=12,anchor=True))
    plan=[]
    for d in range(3):
        for rep in range(6):
            order=list(range(12))[::1 if rep%2==0 else -1]
            for j,row in enumerate([12]+order+[12]):
                plan.append(dict(index=row,dataset=d,repeat=rep,phase='first' if rep==0 else 'warmup' if rep==1 else 'measured',
                                 order_group=rep%2,anchor_position=('start' if j==0 else 'end') if row==12 else None))
    header=['#include "split.h"',f'#define SPLIT_CONTRACT "{CONTRACT}"',f'#define SPLIT_WINDOWS {len(plan)}',
            'static const int8_t split_inputs[7][288] __attribute__((aligned(16),used)) = {']
    header += ['{'+','.join(map(str,values))+'},' for values in inputs];header += ['};']
    header += ['extern void '+row[0]+'(const int8_t *, void *);' for row in LEAVES]
    header += ['caller_leaf const packed_entries[6] = {'+','.join(row[0] for row in LEAVES)+'};',
               'split_leaf const split_entries[6] = {'+','.join(NEW)+'};']
    (out/'data.h').write_text('\n'.join(header)+'\n')
    manifest=dict(contract=CONTRACT,source_base=BASE,dataset=-1,datasets=[0,1,2],shape=[8,32],inputs=inputs,
                  rows=rows,plan=plan,custom_mask=0xfe00707f,custom_match=0x0200000b,
                  functional_calls=84,expected_dots=2752,formal_method_windows=144,formal_anchor_windows=24,
                  max_cycles=3000000,hardware_changed=False,stable_default_changed=False,
                  conditioning='one unmeasured split/firstdot-RVV full call before every measurement, then uniform initialize',
                  primary_metric='complete call including extraction, excluding setup/conditioning',
                  normal_uart_deferred=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
