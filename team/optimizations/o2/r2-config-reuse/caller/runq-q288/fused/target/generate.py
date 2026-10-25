"""One-image, self-warmed complete-Q comparison with three strong RVV controls."""
from pathlib import Path
import importlib.util
import json
import re
import shutil

HERE=Path(__file__).resolve().parent
Q=HERE.parents[1]
REL=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/target')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
parent=load('fused_target_fixture',Q/'generate.py')
fusion=load('fused_target_assembly',HERE.parent/'generate.py')
CONTRACT='r2-s3-runq-q288-fused-target-v1'
MAX_CYCLES=12000000
FILES=parent.FILES+('fused.S',)
# AV, AR3, AR4, FV, FR. RVV3 is split_entries[4], RVV4 is [5].
METHODS=(0,4,5,0,5)
WRAPPERS=('q288_full','q288_full','q288_full','q288_fused_vdot','q288_fused_rvv4')
LABELS=('acc8-vdot','acc8-rvv3','acc8-rvv4','fused-vdot','fused-rvv4')
ORDER=(2,0,1,3,4,2,2,4,3,1,0,2)
FUNCTIONAL_ORDER=(3,4,3,4)
FUNCTIONAL_DATASETS=(1,1,2,2)
GUARD=0xd15ea5e5cafebabe


def generate(repo,out):
    candidate=Q/'acc8/q288.c'
    parent.split.need(parent.digest(candidate.read_bytes())=='f0c557cb837ac05ff713b0eaadb7949b3ba623ae54fe1c02aedcd4220f5bf8d1',
                      'unchanged acc8 source')
    out=Path(out);manifest=parent.generate(repo,out)
    shutil.copyfile(candidate,out/'q288.c');shutil.copyfile(HERE/'main.c',out/'main.c')
    public=(repo/fusion.PUBLIC).read_bytes()
    parent.split.need(parent.digest(public)==fusion.PUBLIC_SHA,'fixed integer public source')
    (out/'fused.S').write_text(fusion.generate_text(public.decode()))
    make=(out/'Makefile').read_text()
    parent.split.need(make.count('main.c q288.c oracle.c timers.S kernels.S')==1,'fixed generated translation units')
    (out/'Makefile').write_text(make.replace('main.c q288.c oracle.c timers.S kernels.S',
                                            'main.c q288.c oracle.c timers.S kernels.S fused.S'))
    rows=[dict(id=i,kind='Q',algorithm=METHODS[i],method='vdot' if METHODS[i]==0 else 'rvv',
               variant='acc8' if i<3 else 'fused',label=LABELS[i],scenario='self-warmed-prepacked-full-Q',
               n=1,dots=10368 if METHODS[i]==0 else 0,leaf=parent.NEW[METHODS[i]],wrapper=WRAPPERS[i]) for i in range(5)]
    plan=[dict(index=arm,phase='measured',repeat=i//6,dataset=0,block=i//6,
               role='anchor_start_method' if i%6==0 else 'anchor_end' if i%6==5 else 'method')
          for i,arm in enumerate(ORDER)]
    call_plan=[dict(stage=0,arm=a,dataset=d) for a,d in zip(FUNCTIONAL_ORDER,FUNCTIONAL_DATASETS)]
    for arm in ORDER:
        call_plan.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    header=(out/'data.h').read_text()
    header=header.replace('#define Q_CONTRACT "'+parent.CONTRACT+'"','#define Q_CONTRACT "'+CONTRACT+'"')
    parent.split.need(header.count('#define Q_WINDOWS 17')==1,'base window constant')
    header=header.replace('#define Q_WINDOWS 17','#define Q_WINDOWS 12\n#define Q_TOTAL_CALLS 28')
    header,count=re.subn(r'static const unsigned q_order\[16\].*?\n};',
        'static const unsigned q_order[12] __attribute__((aligned(16),used)) = {'+','.join(map(str,ORDER))+'};',header,flags=re.S)
    parent.split.need(count==1,'original order array')
    header,count=re.subn(r'static const int32_t q_group_dots\[2592\].*?\n};\n','',header,flags=re.S)
    parent.split.need(count==1,'unused integer sweep fixture')
    header+='extern void q288_fused_vdot(struct q288_context *);\nextern void q288_fused_rvv4(struct q288_context *);\n'
    header+='typedef void (*q_wrapper)(struct q288_context *);\nq_wrapper const q_wrappers[5] = {'+','.join(WRAPPERS)+'};\n'
    for name,values in (('q_methods',METHODS),('q_functional_order',FUNCTIONAL_ORDER),('q_functional_datasets',FUNCTIONAL_DATASETS)):
        header+='static const unsigned '+name+'['+str(len(values))+'] __attribute__((aligned(16),used)) = {'+','.join(map(str,values))+'};\n'
    data=parent.fixtures()
    header+='const struct guarded_packed q_packed __attribute__((aligned(16),used)) = {\n'
    header+='{UINT64_C(0xd15ea5e5cafebabe),UINT64_C(0xd15ea5e5cafebabe)}, {\n'
    header+=''.join(','.join(map(str,data['packed'][i:i+32]))+',\n' for i in range(0,82944,32))
    header+='}, {UINT64_C(0xd15ea5e5cafebabe),UINT64_C(0xd15ea5e5cafebabe)}};\n'
    (out/'data.h').write_text(header)
    manifest.update(contract=CONTRACT,rows=rows,plan=plan,call_plan=call_plan,functional_calls=28,explicit_functional_calls=4,
        timed_q_calls=12,warmup_calls=12,conditioning_calls=0,full_q_calls=28,integer_sweep_leaf_calls=0,
        all_leaf_calls=5184,integer_core_executions=9072,expected_dots=103681,formal_method_windows=12,
        formal_anchor_windows=4,method_anchor_overlap_windows=4,pack_windows=0,max_cycles=MAX_CYCLES,
        target_scalar_oracle_calls=0,prepacked_constant_input=True,pack_executed=False,
        functional_order=list(FUNCTIONAL_ORDER),functional_datasets=list(FUNCTIONAL_DATASETS),
        conditioning='one same-method full Q immediately before each window, common prepare before warm and timed call',
        primary_metric='complete prepacked 288-output Q projection after one same-method warm call',
        statistics='two reverse-order method observations; AR4 has four valid anchor observations; replay is not an extra sample',
        selection_scope='five named methods; RVV set acc8/RVV3, acc8/RVV4, fused/RVV4; not all existing RVV implementations',
        anchor_threshold_ratio=[101,100],separation_threshold_ratio=[199,200],
        count_expected_counter_enqueues=48,count_expected_csr_samples=48,
        fp_element_operations=dict(convert=72576,mul=145152,add=72576),selected_method=None,
        stable_default_changed=False,hardware_changed=False,includes_quantization=False,actual_model_checkpoint=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
