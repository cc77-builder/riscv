"""Read-only closeout audit for C2-G0; no simulation, EDA or Git writes."""
import argparse,ast,datetime,hashlib,json,re,subprocess
from pathlib import Path
R=Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
W=Path('/home/riscv/riscv-lab/o2-c2-g0-20261025')
M=R/'team/optimizations/o2/r3-div-gate/c2-g0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def need(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    need(not a.output.exists(),'new receipt required')
    pins={}
    def add(path,h):
        need(path not in pins or pins[path]==h,'inconsistent identity '+path);pins[path]=h
    for name,key in [('review-fp/fp-control-result.json','inputs'),('composition-check.json','inputs')]:
        for p,h in read(W/name)[key].items():add(p,h)
    for name,key in [('review-int/inputs.json',None),('review-int/generated-inputs.json',None),
                     ('review-reset/inputs.json','files'),('review-int/system-review-audit.json','inputs')]:
        obj=read(W/name);obj=obj[key] if key else obj
        for ent in obj:add(ent['path'],ent['sha256'])
    for name in ['system_model.py','check_composition.py','CONTRACT.md']:
        p=M/name;add(str(p),sha(p))
    for p,h in pins.items():need(sha(Path(p))==h,'input changed '+p)
    need(sha(M/'system_model.py')==read(W/'system-proof-02-command.json')['source_sha256'],'final model identity')
    need(sha(M/'CONTRACT.md')==read(W/'started.json')['contract_sha256'],'contract altered')
    for file,h in read(W/'review-fp/review-manifest.json')['files'].items():
        need(sha(W/'review-fp'/file)==h,'FP sealed review altered')
    proof=read(W/'system-proof-02.json')
    metrics={}
    for key,trans in [('production_async',33600),('fixture_sync_te1_reset',31680),
                      ('sync_warm_reset_te_unrestricted',33600)]:
        x=proof[key];need(x['passed'] and x['states']==48 and x['transitions']==trans,'system result')
        metrics[key]=dict(states=x['states'],transitions=x['transitions'])
    need(proof['reset_establishment']['arbitrary_control_initializations']==1944,'bootstrap scope')
    negatives={}
    for name,x in proof['negative_controls'].items():
        need(not x['passed'] and 'idle_implies_all_ready' in x['counterexample'][-1]['violation'],'negative misses target')
        negatives[name]=len(x['counterexample'])
    need(len(negatives)==5,'negative scope')
    composition=read(W/'composition-check.json')
    need((composition['fp_rows'],composition['fp_edges'],composition['integer_top_rows'])==(640,660,384),'inclusion scope')
    fp=read(W/'review-fp/fp-control-result.json')
    for mode in ['sync','async']:
        x=fp['models'][mode];need(x['reached']==38 and x['transitions']==11184,'FP fine proof')
    integer=read(W/'review-int/proof.json')
    need(integer['status']=='INTEGER_SOURCE_LINKED_CONTROL_PROOF_PASS_CONDITIONAL_BOOTSTRAP','integer proof')
    reset=read(W/'review-reset/summary.json')
    need(reset['frozen_generated_files_verified']==11 and reset['ROB_comparisons']==65536,'reset source binding')
    need(read(W/'review-int/system-review-audit.json')['status']=='NO_CIRCULAR_STATE_FILTER_FOUND','independent review')
    commands=[]
    for p in W.rglob('*command*.json'):
        x=read(p)
        # Agent command schemas use exit_code or returncode.
        rc=x.get('exit_code',x.get('returncode'))
        need(rc==0,'command failure or unknown schema '+str(p))
        commands.append(str(p.relative_to(W)))
    syntax=[]
    for p in list(M.glob('*.py'))+list(W.rglob('*.py')):
        ast.parse(p.read_text(),filename=str(p));syntax.append(str(p))
    seals={}
    for rel,h in [
      ('evidence/20261025-performance-cost/manifest.json','9bda2d8c8ee254786ac8928588d3372b2b269bca89d6ec720eb1abf2c936be77'),
      ('c1/evidence/20261025-screen/manifest.json','ced265304d08b2ee3c7eb9a894eb009869bb494adb7c48e1ff72493ce4cb252e')]:
        p=M.parent/rel;need(sha(p)==h,'old cost seal changed');seals[str(p)]=h
    git=lambda *args: subprocess.check_output(['git','-C',str(R),*args],text=True).strip()
    need(git('rev-parse','HEAD')=='0f12df675378556670afd0dd2153f47fcb330610','source HEAD changed')
    need(not git('diff','HEAD','--','src'),'production source dirty')
    deps={}
    for sub in ['yunsuan','utility']:
        p=R/sub
        need(not subprocess.check_output(['git','-C',str(p),'diff','HEAD','--','src'],text=True),'dependency source dirty')
        deps[sub]=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
    manifest=read(M/'evidence/manifest.json')
    for ent in manifest['files']:
        p=M/'evidence'/ent['path'];src=W/ent['path']
        need(p.stat().st_size==ent['bytes'] and sha(p)==ent['sha256']==sha(src),'archive byte mismatch '+ent['path'])
    a.output.parent.mkdir(exist_ok=True)
    x=dict(status='C2_G0_SOURCE_LINKED_CONTROL_PROOF_AUDIT_PASS',
           time=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
           inputs=pins,input_count=len(pins),old_seals=seals,source_head=git('rev-parse','HEAD'),
           dependency_heads=deps,production_src_diff_empty=True,system_metrics=metrics,
           negative_controls_target_failures=negatives,checked_command_records=commands,
           syntax_files=syntax,archive_files=len(manifest['files']),
           archive_bytes=sum(x['bytes'] for x in manifest['files']),
           archive_manifest_sha256=sha(M/'evidence/manifest.json'),
           interpretation='Scoped G0 PASS: fixed-source reviewed control abstractions and actual-reset identity, not full RTL formal equivalence or implemented-C2 acceptance.',
           rtl_changes=False,hardware_runs=False,eda_runs=False,github_write=False)
    a.output.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:x[k] for k in ['status','input_count','system_metrics','archive_files','archive_bytes']},indent=2))
if __name__=='__main__':main()
