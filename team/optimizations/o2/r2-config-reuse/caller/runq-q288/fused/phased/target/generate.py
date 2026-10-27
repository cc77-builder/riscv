"""One bounded target comparison of the existing phased schedule, FV and FR."""
from pathlib import Path
import importlib.util,json,re,shutil,tempfile

HERE=Path(__file__).resolve().parent
Q=HERE.parents[2]
REL=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased/target')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
previous=load('phased_target_previous_generator',Q/'fused/target/generate.py')
candidate=load('phased_target_fixed_candidate',HERE.parent/'candidate.py')
parent=previous.parent
CONTRACT='r2-s3-runq-q288-phased-target-v1'
MAX_CYCLES=12000000
FILES=previous.FILES
METHODS=(0,0,5)
WRAPPERS=('q288_fused_vdot','q288_phased_vdot','q288_fused_rvv4')
LABELS=('fused-vdot','phased-vdot','fused-rvv4')
ORDER=(2,0,1,2,2,1,0,2)
FUNCTIONAL_ORDER=(0,1,2,0,1,2)
FUNCTIONAL_DATASETS=(1,1,1,2,2,2)
GUARD=previous.GUARD
need=parent.split.need

def generate(repo,out):
    out=Path(out);manifest=previous.generate(repo,out)
    shutil.copyfile(HERE/'main.c',out/'main.c')
    # Retain the unchanged legacy wrapper as a byte-checkable link root only.
    make=(out/'Makefile').read_text()
    need('--undefined=q288_full' not in make,'no preexisting legacy link root')
    (out/'Makefile').write_text(make+'LDFLAGS += --undefined=q288_full\n')
    public=(repo/candidate.PUBLIC).read_text()
    prefix='.option norvc\n.option norelax\n.text\n'+previous.fusion.function(public,'vdot')
    with tempfile.TemporaryDirectory(prefix='phased-target-producer-') as temp:
        generated=Path(temp)/'generated';candidate.generate(repo,generated)
        assembly=(generated/'phased.S').read_text()
    need(assembly.startswith(prefix),'exact existing candidate baseline prefix')
    phased=assembly[len(prefix):]
    need(phased.count('q288_phased_vdot:')==1 and 'q288_fused_vdot' not in phased,'one existing phased function')
    (out/'fused.S').write_text((out/'fused.S').read_text()+phased)
    header=(out/'data.h').read_text()
    for old,new in (('#define Q_CONTRACT "'+previous.CONTRACT+'"','#define Q_CONTRACT "'+CONTRACT+'"'),
                    ('#define Q_WINDOWS 12','#define Q_WINDOWS 8'),
                    ('#define Q_TOTAL_CALLS 28','#define Q_TOTAL_CALLS 22')):
        need(header.count(old)==1,'unique header contract field');header=header.replace(old,new)
    for name,old_size,values in (('q_order',12,ORDER),('q_methods',5,METHODS),
                                ('q_functional_order',4,FUNCTIONAL_ORDER),('q_functional_datasets',4,FUNCTIONAL_DATASETS)):
        pattern=r'static const unsigned '+name+r'\['+str(old_size)+r'\][^;]*;'
        replacement='static const unsigned '+name+'['+str(len(values))+'] __attribute__((aligned(16),used)) = {'+','.join(map(str,values))+'};'
        header,count=re.subn(pattern,lambda _:replacement,header)
        need(count==1,'unique old array '+name)
    header,count=re.subn(r'q_wrapper const q_wrappers\[5\][^;]*;',
        lambda _:'q_wrapper const q_wrappers[3] = {'+','.join(WRAPPERS)+'};',header)
    need(count==1,'unique original wrapper table')
    marker='typedef void (*q_wrapper)(struct q288_context *);'
    need(header.count(marker)==1,'wrapper declaration')
    header=header.replace(marker,'extern void q288_phased_vdot(struct q288_context *);\n'+marker)
    (out/'data.h').write_text(header)
    rows=[dict(id=i,kind='Q',algorithm=METHODS[i],method='vdot' if i<2 else 'rvv',
               variant='phased' if i==1 else 'fused',label=LABELS[i],scenario='self-warmed-prepacked-full-Q',
               n=1,dots=10368 if i<2 else 0,leaf=parent.NEW[METHODS[i]],wrapper=WRAPPERS[i]) for i in range(3)]
    plan=[dict(index=arm,phase='measured',repeat=i//4,dataset=0,block=i//4,
               role='anchor_start_method' if i%4==0 else 'anchor_end' if i%4==3 else 'method')
          for i,arm in enumerate(ORDER)]
    calls=[dict(stage=0,arm=a,dataset=d) for a,d in zip(FUNCTIONAL_ORDER,FUNCTIONAL_DATASETS)]
    for arm in ORDER:calls.extend((dict(stage=1,arm=arm,dataset=0),dict(stage=2,arm=arm,dataset=0)))
    need(len(calls)==22 and sum(rows[c['arm']]['dots'] for c in calls)+1==124417,'derived normal-run counts')
    manifest.update(contract=CONTRACT,rows=rows,plan=plan,call_plan=calls,functional_calls=22,
        functional_calls_legacy_field_means='all complete Q calls including selfwarm and timed',
        explicit_functional_calls=6,timed_q_calls=8,warmup_calls=8,conditioning_calls=0,full_q_calls=22,
        integer_sweep_leaf_calls=0,all_leaf_calls=0,integer_core_executions=7128,expected_dots=124417,
        formal_method_windows=8,formal_anchor_windows=4,method_anchor_overlap_windows=4,
        pack_windows=0,max_cycles=MAX_CYCLES,target_scalar_oracle_calls=0,prepacked_constant_input=True,pack_executed=False,
        functional_order=list(FUNCTIONAL_ORDER),functional_datasets=list(FUNCTIONAL_DATASETS),
        conditioning='one same-method full Q immediately before each window; identical prepare before both',
        primary_metric='complete prepacked 288-output Q in the new common ELF',
        statistics='two reverse-order FV/PV observations; all four FR anchors; replay is not an extra sample',
        selection_scope='existing phased candidate versus FV and named FR; no renewed claim over every RVV implementation',
        anchor_threshold_ratio=[101,100],separation_threshold_ratio=[199,200],
        count_expected_counter_enqueues=32,count_expected_csr_samples=32,
        fp_element_operations=dict(convert=57024,mul=114048,add=57024),selected_method=None,
        stable_default_changed=False,hardware_changed=False,includes_quantization=False,actual_model_checkpoint=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
