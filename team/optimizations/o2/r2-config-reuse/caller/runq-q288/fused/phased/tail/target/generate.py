"""One new same-ELF PV/TV/FR comparison; retain every prior source unchanged."""
from pathlib import Path
import importlib.util,json,re,shutil,tempfile

HERE=Path(__file__).resolve().parent
Q=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
previous=load('tail_target_previous_generator',Q/'fused/phased/target/generate.py')
candidate=load('tail_target_candidate',HERE.parent/'candidate.py')
parent=previous.parent
CONTRACT='r2-s3-runq-q288-tail-agnostic-target-v1'
MAX_CYCLES=12000000
FILES=previous.FILES
METHODS=(0,0,5)
WRAPPERS=('q288_phased_vdot','q288_tail_vdot','q288_fused_rvv4')
LABELS=('phased-vdot','tail-vdot','fused-rvv4')
ORDER=(2,0,1,2,2,1,0,2)
FUNCTIONAL_ORDER=(0,1,2,0,1,2)
FUNCTIONAL_DATASETS=(1,1,1,2,2,2)
GUARD=previous.GUARD
need=parent.split.need

def generate(repo,out):
    out=Path(out);manifest=previous.generate(repo,out)
    shutil.copyfile(HERE/'main.c',out/'main.c')
    with tempfile.TemporaryDirectory(prefix='tail-target-producer-') as temp:
        generated=Path(temp)/'generated';candidate.generate(repo,generated)
        assembly=(generated/'tail.S').read_text()
    marker='.balign 64\n.global q288_tail_vdot\n'
    need(assembly.count(marker)==1,'one bounded new function')
    tail=assembly[assembly.index(marker):]
    need(tail.count('q288_tail_vdot:')==1 and 'q288_phased_vdot' not in tail and 'q288_fused_vdot' not in tail,
         'append only the TA function')
    (out/'fused.S').write_text((out/'fused.S').read_text()+tail)
    header=(out/'data.h').read_text();old='#define Q_CONTRACT "'+previous.CONTRACT+'"'
    need(header.count(old)==1,'unique previous contract macro')
    header=header.replace(old,'#define Q_CONTRACT "'+CONTRACT+'"')
    header,count=re.subn(r'q_wrapper const q_wrappers\[3\][^;]*;',
        lambda _:'q_wrapper const q_wrappers[3] = {'+','.join(WRAPPERS)+'};',header)
    need(count==1,'exact three-entry wrapper table')
    marker='typedef void (*q_wrapper)(struct q288_context *);'
    need(header.count(marker)==1,'wrapper declaration')
    header=header.replace(marker,'extern void q288_tail_vdot(struct q288_context *);\n'+marker)
    (out/'data.h').write_text(header)
    rows=[dict(id=i,kind='Q',algorithm=METHODS[i],method='vdot' if i<2 else 'rvv',
               variant=('phased','tail-agnostic','fused')[i],label=LABELS[i],scenario='self-warmed-prepacked-full-Q',
               n=1,dots=10368 if i<2 else 0,leaf=parent.NEW[METHODS[i]],wrapper=WRAPPERS[i]) for i in range(3)]
    need([s['index'] for s in manifest['plan']]==list(ORDER) and manifest['full_q_calls']==22 and
         manifest['expected_dots']==124417,'unchanged bounded three-method plan cardinality')
    manifest.update(contract=CONTRACT,rows=rows,
        statistics='two reverse-order PV/TV observations; all four FR anchors; replay is not an extra sample',
        selection_scope='two-vta-bit candidate versus qualified phased incumbent and named FR; no renewed global RVV claim',
        changed_candidate_function_words=2,candidate_instruction_count_change=0,
        structural_hypothesis='ordinary TA vector loads can remove old-vd readiness/read demand; custom already removes old-vd',
        hardware_changed=False,stable_default_changed=False,selected_method=None)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest
