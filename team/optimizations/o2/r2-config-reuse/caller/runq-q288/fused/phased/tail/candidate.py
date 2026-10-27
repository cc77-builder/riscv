"""Two e8 phase configuration changes; preserve the qualified phased function."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,tempfile

PHASED=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused/phased')
PARENT_SHA='2b487c60b53e25dbc04eba4c2eac4bd175e1573837863194de463d6a27df2399'
CONTRACT='r2-s3-runq-q288-tail-agnostic-screen-v1'
NAME='q288_tail_vdot'

def need(ok,message):
    if not ok:raise ValueError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def generate(repo,out):
    path=repo/PHASED/'candidate.py';need(sha(path.read_bytes())==PARENT_SHA,'fixed phased generator')
    parent=load('tail_fixed_phased_generator',path)
    with tempfile.TemporaryDirectory(prefix='tail-generator-') as temp:
        folder=Path(temp)/'generated';parent.generate(repo,folder);original=(folder/'phased.S').read_text()
    start=original.index('.balign 64\n.global q288_phased_vdot\n')
    body=original[start:];core=parent.core()
    need(body.count(core)==1 and core.count('vsetivli zero, 8, e8, m1, tu, mu')==2,'two bounded e8 phases')
    changed=core.replace('vsetivli zero, 8, e8, m1, tu, mu','vsetivli zero, 8, e8, m1, ta, mu')
    body=body.replace(core,changed).replace('q288_phased_vdot',NAME)
    body=body.replace('.Ltile_phased','.Ltile_tail').replace('.Lgroup_phased','.Lgroup_tail')
    need(body.count('vsetivli zero, 8, e8, m1, ta, mu')==2 and
         body.count('vsetivli zero, 8, e8, m1, tu, mu')==1,'only core phases changed; final tu restored')
    assembly=original+body;out.mkdir(parents=True,exist_ok=False);(out/'tail.S').write_text(assembly)
    result=dict(contract=CONTRACT,assembly_sha256=sha(assembly.encode()),baseline='q288_phased_vdot',candidate=NAME,
        change='two e8 vsetivli vta bits only; e32 phases and final restore remain tu',new_emu_runs=0,
        target_runtime_qualified=False,performance_qualified=False)
    (out/'generation.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(generate(a.repo.resolve(),a.output.resolve()),indent=2))
