"""One bounded vdot schedule candidate; the existing fusion is unchanged."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

PUBLIC=Path('team/optimizations/o2/r2-config-reuse/public/gemv.S')
PUBLIC_SHA='9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2'
FUSED=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/fused')
FUSED_GEN_SHA='b1d127cfc60d9b3fe942b90fd8a1faa0800726d56b081ebd183ca4e611c9a77b'


def need(ok,message):
    if not ok:raise ValueError(message)


def core():
    text='  vsetivli zero, 8, e8, m1, tu, mu\n'
    for chunk in range(4):
        if chunk:text+='  addi a1, a1, 8\n'
        text+=f'  vle8.v v{16+chunk}, (a1)\n'
    tables=(((0,4,24,28),(1,5,25,29),(2,6,26,30),(3,7,27,31)),
            ((4,10,14,26),(5,11,15,27),(6,12,24,28),(7,13,25,29)))
    for half,table in enumerate(tables):
        if half:text+='  vsetivli zero, 8, e8, m1, tu, mu\n'
        for chunk in range(4):
            for row in range(4):
                text+=f'  addi t6, a2, {(half*4+row)*32+chunk*8}\n  vle8.v v{20+row}, (t6)\n'
            for row in range(4):
                word=0x0200000b | (table[row][chunk]<<7) | ((20+row)<<15) | ((16+chunk)<<20)
                text+=f'  .word 0x{word:08x}\n'
        text+='  vsetivli zero, 4, e32, m1, tu, mu\n'
        for row in range(4):
            destination=half*4+row
            for chunk in (1,2,3):text+=f'  vadd.vv v{destination}, v{destination}, v{table[row][chunk]}\n'
    return text


def generate(repo,out):
    source=repo/FUSED/'generate.py';raw=source.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==FUSED_GEN_SHA,'frozen fusion generator')
    spec=importlib.util.spec_from_file_location('phased_original_generator',source)
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    public=(repo/PUBLIC).read_bytes();need(hashlib.sha256(public).hexdigest()==PUBLIC_SHA,'fixed team public source')
    before=original.function(public.decode(),'vdot');old_core=original.integer_core(public.decode(),'vdot')
    need(before.count(old_core)==1 and before.count('  addi a1, a1, 32\n')==1,'unique replacement boundaries')
    after=before.replace(old_core,core()).replace('  addi a1, a1, 32\n','  addi a1, a1, 8\n')
    after=after.replace('q288_fused_vdot','q288_phased_vdot').replace('.Ltile_vdot','.Ltile_phased').replace('.Lgroup_vdot','.Lgroup_phased')
    assembly='.option norvc\n.option norelax\n.text\n'+before+after
    out.mkdir(parents=True,exist_ok=False);(out/'phased.S').write_text(assembly)
    result=dict(contract='r2-s3-runq-q288-phased-screen-v1',assembly_sha256=hashlib.sha256(assembly.encode()).hexdigest(),
                baseline='q288_fused_vdot',candidate='q288_phased_vdot',integer_core_words_expected=131,
                new_emu_runs=0,target_runtime_qualified=False,performance_qualified=False)
    (out/'generation.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(generate(a.repo.resolve(),a.output.resolve()),indent=2))
