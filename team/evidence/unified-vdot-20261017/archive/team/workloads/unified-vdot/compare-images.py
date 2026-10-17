"""Audit equal workload, baseline machine code, and addresses across variants."""
import argparse,json
from pathlib import Path
import check


def main(root):
    variants=('ours','jade','shishui','redoop')
    inventories={v:json.loads((root/(v+'-images-02/images.json')).read_text())['images'] for v in variants}
    names=[x['name'] for x in inventories['ours']]
    for v in variants:check.require(names==[x['name'] for x in inventories[v]],'image plans differ')
    checked=0
    for name in names:
        folders={v:root/(v+'-images-02')/name for v in variants}
        manifests={v:json.loads((f/'data/manifest.json').read_text()) for v,f in folders.items()}
        kernels={v:check.elf_kernels(f/'vdot-perf.elf') for v,f in folders.items()}
        base=manifests['ours']
        for v in variants:
            m=manifests[v]
            match={'ours':0x0200000b,'jade':0xe6000057,'shishui':0xfa000057,'redoop':0xe6002057}
            check.require(m['variant']==v and m['custom_match']==match[v] and m['custom_mask']==0xfe00707f,'variant/code binding differs')
            check.check_compiled_cases(folders[v]/'vdot-perf.elf',m)
            check.require(base['plan']==m['plan'],'run order differs')
            for i,(a,b) in enumerate(zip(base['rows'],m['rows'])):
                for key in ('id','scenario','method','n','iterations','dots','operands','vtype','before','expected','stream','outputs'):
                    check.require(a[key]==b[key],f'{name} {v} workload differs: {key}')
                check.require(min(kernels['ours'][i])==min(kernels[v][i]),'function address differs')
                if a['method']!='vdot':check.require(kernels['ours'][i]==kernels[v][i],'RVV/control compiled code differs')
                check.walk(kernels[v][i])
            sa,ra=check.elf_data(folders['ours']/'vdot-perf.elf');sb,rb=check.elf_data(folders[v]/'vdot-perf.elf')
            check.require(sa['cases']==sb['cases'],'case array address differs')
            for symbol,address in [('cases',0x80120000),('observed',0x80130000),('sink',0x80131000)]:
                check.require(sb[symbol][0]==address,'fixed symbol address differs '+symbol)
            # Data pointer members: stream and expected outputs, excluding scratch masks.
            for i in range(len(base['rows'])):
                off=i*1104+56
                check.require(ra(sa['cases'][0]+off,16)==rb(sb['cases'][0]+off,16),'input/output data addresses differ')
        checked+=len(base['rows'])*len(variants)
    return {'status':'UNIFIED_INPUT_AND_BASELINE_IDENTITY_PASS','images_per_variant':len(names),'compiled_rows_checked':checked,'same_function_addresses':True,'same_input_addresses':True,'same_baseline_machine_code':True}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=main(a.runs);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
