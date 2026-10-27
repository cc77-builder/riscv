"""Derive fixed M288/K768 kernels from immutable qualified team Q288 sources."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, tempfile

HERE=Path(__file__).resolve().parent
CONTRACT='r2-s3-real-w2-v1'
Q=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288')
PINS={Q/'fused/generate.py':'b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b',
      Q/'fused/phased/candidate.py':'2b487c60b53e25dbc04eba4c2eac4bd175e1573837863194de463d6a27df2399'}
CHANGES=(('  li t3, 36\n','  li t3, 96\n'),('  li t1, 9\n','  li t1, 24\n'),
         ('  addi a4, a4, 252\n','  addi a4, a4, 672\n'))

def need(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def functions(repo):
    repo=Path(repo)
    for rel,digest in PINS.items():need(sha((repo/rel).read_bytes())==digest,'frozen source '+str(rel))
    fused=load('w2_frozen_fused',repo/Q/'fused/generate.py')
    public=(repo/fused.PUBLIC).read_bytes();need(sha(public)==fused.PUBLIC_SHA,'frozen integer core')
    fr=fused.function(public.decode(),'rvv4')
    tail=load('w2_frozen_tail',repo/Q/'fused/phased/tail/candidate.py')
    with tempfile.TemporaryDirectory(prefix='w2-generator-') as folder:
        output=Path(folder)/'generated';tail.generate(repo,output);raw=(output/'tail.S').read_text()
    start=raw.index('.balign 64\n.global q288_tail_vdot\n');ta=raw[start:]
    return {'q768_fr':('q288_fused_rvv4',fr),'q768_ta':('q288_tail_vdot',ta)}

def generate(repo,output):
    output=Path(output);need(not output.exists(),'fresh generation directory');output.mkdir(parents=True)
    parents=functions(repo);code='.option norvc\n.option norelax\n.text\n';records={}
    parent_assembly='.option norvc\n.option norelax\n.text\n'
    for name,(old,before) in parents.items():
        after=before
        for source,target in CHANGES:
            need(after.count(source)==1,'one exact geometry site '+source.strip());after=after.replace(source,target)
        # Local label namespaces must remain distinct when both geometries link.
        labels=re.findall(r'^(\.L\w+):',after,re.M)
        after=after.replace(old,name)
        for label in labels:after=after.replace(label,label+'_k768')
        restored=after.replace(name,old)
        for label in labels:restored=restored.replace(label+'_k768',label)
        for source,target in CHANGES:restored=restored.replace(target,source)
        need(restored==before,'entire parent source restored exactly')
        code+=after;parent_assembly+=before
        records[name]=dict(parent=old,parent_sha256=sha(before.encode()),derived_sha256=sha(after.encode()),
                           whole_source_restored=True,geometry_changes=3)
    (output/'w2.S').write_text(code);(output/'parents.S').write_text(parent_assembly)
    result=dict(contract=CONTRACT,rows=288,k=768,groups=24,tiles=36,packed_bytes=221184,
                assembly_sha256=sha(code.encode()),functions=records,hardware_changed=False,performance_qualified=False)
    (output/'generation.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(generate(a.repo.resolve(),a.output.resolve()),indent=2))
