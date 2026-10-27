"""One same-ELF, shared-scalar-quantizer, actual-activation QKV experiment."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,struct,zipfile
HERE=Path(__file__).resolve().parent
Q=HERE.parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
previous=load('qkv_generator_previous',Q/'fused/phased/tail/target/generate.py')
parent=previous.parent
CONTRACT='r2-s3-runq-active-qkv-target-v1'
MAX_CYCLES=18000000
FILES=previous.FILES+('boundary.h','boundary.S')
ORDER=(1,0,1,1,0,1)
WRAPPERS=('q288_tail_vdot','q288_fused_rvv4')
FIXTURE=HERE/'evidence/input-v1/fixture.zip'
FIXTURE_SHA='4b926d3c459e52ad3e9c8ec78c2dd22f090498b06a1b11b5188d7f1e75353913'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,why):
    if not ok:raise ValueError(why)
def fixtures():
    need(sha(FIXTURE.read_bytes())==FIXTURE_SHA,'frozen active capture and oracle archive')
    with zipfile.ZipFile(FIXTURE) as z:
        meta=json.loads(z.read('metadata.json'));raw={n:z.read(n) for n in meta['members']}
        need(set(z.namelist())==set(raw)|{'metadata.json'},'exact input archive members')
    need(meta['status']=='ACTUAL_CONSUMER_QKV_INPUT_AND_QUANTIZER_ORACLE_PASS' and
         meta['layer']==0 and meta['measured_position']==0 and meta['functional_position']==1 and
         meta['host_subnormal_scale_verified'],'fixed consumer provenance')
    for n,value in raw.items():need(len(value)==meta['members'][n]['bytes'] and sha(value)==meta['members'][n]['sha256'],'input '+n)
    s8=lambda value:list(struct.unpack('<'+str(len(value))+'b',value))
    u32=lambda value:list(struct.unpack('<'+str(len(value)//4)+'I',value))
    inputs=[s8(raw[f'quant-{d}.bin'][:288]) for d in range(3)]
    scales=[u32(raw[f'quant-{d}.bin'][288:]) for d in range(3)]
    projections=[]
    for m in range(3):projections.append(dict(weight=s8(raw[f'weight-{m}.bin']),packed=s8(raw[f'packed-{m}.bin']),
        weight_scale=u32(raw[f'scale-{m}.bin']),inputs=inputs[:2],input_scale=scales[:2],
        golden=[u32(raw[f'y-{d}-{m}.bin']) for d in range(2)]))
    return dict(raw=raw,metadata=meta,projections=projections,fp=[u32(raw[f'fp-{d}.bin']) for d in range(3)],
                inputs=inputs,scales=scales)

def generate(repo,out):
    previous.generate(repo,out);out=Path(out);f=fixtures()
    for name in ('main.c','boundary.h','boundary.S'):shutil.copyfile(HERE/name,out/name)
    make=(out/'Makefile').read_text();needle='kernels.S fused.S'
    need(make.count(needle)==1,'existing generated units')
    make=make.replace(needle,needle+' boundary.S')
    include='include $(AM_HOME)/Makefile.app'
    need(make.count(include)==1,'one authoritative AM include')
    (out/'Makefile').write_text(make.replace(include,'ASFLAGS += -mno-relax -mabi=lp64d\n'+include))
    h=['#include "boundary.h"',f'#define QKV_CONTRACT "{CONTRACT}"']
    def array(ctype,name,shape,values,fmt=str):
        h.append('static const '+ctype+' '+name+shape+' __attribute__((aligned(16),used)) = {')
        def render(v):
            if isinstance(v,list):return '{'+','.join(render(x) for x in v)+'}'
            return fmt(v)
        if isinstance(values[0],list):h.extend(render(row)+',' for row in values)
        else:h.extend(','.join(render(v) for v in values[i:i+32])+',' for i in range(0,len(values),32))
        h.append('};')
    float_text=lambda b:struct.unpack('<f',struct.pack('<I',b))[0].hex()+'f'
    array('int8_t','qkv_weights','[3][82944]',[p['weight'] for p in f['projections']])
    array('int8_t','qkv_packed','[3][82944]',[p['packed'] for p in f['projections']])
    array('float','qkv_weight_scale','[3][2592]',[p['weight_scale'] for p in f['projections']],float_text)
    array('float','qkv_fp','[3][288]',f['fp'],float_text)
    array('int8_t','qkv_expected_x','[3][288]',f['inputs'])
    array('uint32_t','qkv_expected_xs','[3][9]',f['scales'],lambda v:hex(v)+'u')
    array('uint32_t','qkv_expected_y','[2][3][288]',[[p['golden'][d] for p in f['projections']] for d in range(2)],lambda v:hex(v)+'u')
    array('unsigned','qkv_order','[6]',list(ORDER))
    h.append('split_leaf const split_entries[6] = {'+','.join(parent.NEW)+'};')
    h.append('qkv_kernel const qkv_kernels[2] = {'+','.join(WRAPPERS)+'};')
    (out/'data.h').write_text('\n'.join(h)+'\n')
    rows=[dict(id=i,kind='QKV',method='vdot' if i==0 else 'rvv',variant='tail' if i==0 else 'fused-rvv4',
        label='TA-QKV' if i==0 else 'FR-QKV',wrapper='qkv_boundary',kernel=WRAPPERS[i],leaf=parent.NEW[0 if i==0 else 5],
        scenario='actual-fp32-shared-quantization-qkv',n=1,dots=31104 if i==0 else 0) for i in range(2)]
    plan=[dict(index=arm,phase='measured',repeat=i//3,dataset=0,block=i//3,
        role='anchor_start' if i%3==0 else 'anchor_end' if i%3==2 else 'candidate') for i,arm in enumerate(ORDER)]
    calls=[dict(stage=0,arm=arm,dataset=1) for arm in range(2)]
    for arm in ORDER:calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    manifest=dict(contract=CONTRACT,rows=rows,plan=plan,call_plan=calls,dataset=0,custom_mask=0xfe00707f,custom_match=0x0200000b,
        expected_dots=155521,timed_dots=62208,max_cycles=MAX_CYCLES,full_q_calls=42,boundary_calls=14,
        quantize_calls_in_boundaries=14,standalone_quantize_probes=3,quantize_groups_total=153,quantize_elements_total=4896,
        projection_outputs=12096,windows=6,csr_samples=24,counter_enqueues=24,
        fixture_sha256=FIXTURE_SHA,layer=0,measured_position=0,functional_position=1,
        input_scope='actual untrained active-forward capture; persistent packed weights',
        primary_metric='FP32 input through one shared scalar quantization and three complete Q/K/V projections',
        conditioning='same-method whole-boundary selfwarm followed by identical prepare',
        anchor_threshold_ratio=[101,100],separation_threshold_ratio=[199,200],
        performance_qualified=False,hardware_changed=False,stable_default_changed=False,
        includes_quantization=True,pack_included=False,full_forward_included=False,trained_model_quality=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
