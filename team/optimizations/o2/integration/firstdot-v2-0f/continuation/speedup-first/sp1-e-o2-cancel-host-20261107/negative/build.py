#!/usr/bin/env python3
"""Compile the production interposer; never load it or run any reference."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'negative'
OLD=ROOT.parent/'sp1-e-g0/protection/negative'
REF=Path('/home/riscv/riscv-lab/t12-regression-20261013/nemu/reference/build/riscv64-nemu-interpreter-so')
REF_SHA='efbed0774addc27eac38af1a19ab5d9c9dd5f179b5015f25ae7b80b966185bd4'
SOURCE=HERE/'o2-cancel-bit100.c'
PRODUCT=HERE/'o2-cancel-negative-reference.so'

def pin(path):
    path=Path(path); data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def save(name,data):
    (HERE/name).write_text(json.dumps(data,indent=2)+'\n')
def protected():
    return [pin(p) for tree in ('software','build-review') for p in sorted((ROOT/tree).rglob('*')) if p.is_file()]
def require(condition,message):
    if not condition: raise RuntimeError(message)

require(not PRODUCT.exists(),'refuse to replace an existing compiled product')
before=protected()
save('PROTECTED_BEFORE.json',before)
original=(OLD/'o2-control-bit100.c').read_text()
replacements=[('0x80000300','0x80000278'),('0x0294080b','0x0294000b'),
              ('#define TARGET_VD 16u','#define TARGET_VD 0u'),('bit=100 vd=16','bit=100 vd=0')]
new=original
for a,b in replacements:
    require(a in new,'expected original binding absent: '+a)
    new=new.replace(a,b)
SOURCE.write_text(new)
normalized=new
for a,b in reversed(replacements): normalized=normalized.replace(b,a)
require(normalized==original,'nonbinding mechanism change')
manifest=json.loads((ROOT/'software/manifest.json').read_text())
guard=manifest['guard']
require((guard['pc'],guard['word'],guard['vd'])==(0x80000278,0x0294000b,0),'manifest guard mismatch')
require(pin(REF)['sha256']==REF_SHA,'reference library identity mismatch')
old_result=json.loads((OLD/'RESULT.json').read_text())
require(old_result['status']=='HOST_NEGATIVE_FIXTURES_PASS','old host-mechanism evidence not PASS')
require(old_result['normal_reference']==pin(REF),'old reference pin differs')
tools={name:Path(shutil.which(name)).resolve() for name in ('gcc','readelf','objdump','nm')}
inputs=[SOURCE,Path(__file__).resolve(),OLD/'o2-control-bit100.c',OLD/'SOURCE_FREEZE.json',OLD/'RESULT.json',
        ROOT/'software/manifest.json',REF,*tools.values()]
inputs_before=[pin(p) for p in inputs]
save('NORMALIZATION_AUDIT.json',{'status':'PASS_EXACT_TEXT_AFTER_BINDING_NORMALIZATION','replacements':replacements,
     'original':pin(OLD/'o2-control-bit100.c'),'new_source':pin(SOURCE),'normalized_sha256':hashlib.sha256(normalized.encode()).hexdigest(),
     'mechanism_unchanged':True,'same_env_guard':'SP1_CHAIN_BIT100=1','new_host_abi_tests':0,
     'reused_evidence':pin(OLD/'RESULT.json'),'target_rejection':'NOT_TESTED'})
save('SOURCE_FREEZE.json',{'scope':'COMPILE_AND_STATIC_INSPECTION_ONLY','inputs':inputs_before,'guard':guard,
     'vector_state_offset':800,'vd_stride':16,'bit':100,'byte_offset':800+0*16+12,'xor_mask':16,
     'normal_reference':pin(REF),'images':manifest['images'],'production_wrapper_load_permitted':False})
commands=[]
def run(argv,name):
    start=time.monotonic()
    p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,cwd=HERE)
    (HERE/(name+'.stdout')).write_bytes(p.stdout)
    (HERE/(name+'.stderr')).write_bytes(p.stderr)
    commands.append({'argv':argv,'cwd':str(HERE),'returncode':p.returncode,'elapsed_seconds':time.monotonic()-start,
                     'scope':'HOST_COMPILE_OR_STATIC_INSPECTION_NO_LIBRARY_LOAD'})
    save('COMMANDS.json',commands)
    require(p.returncode==0,name+' failed')
    return p.stdout
status='FAIL_BIT100_BUILD_PREPARATION'
try:
    argv=[str(tools['gcc']),'-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',f'-DREF_SO="{REF}"',str(SOURCE),
          '-Wl,--no-as-needed',str(REF),'-ldl','-o',str(PRODUCT)]
    run(argv,'compile')
    dynamic=run([str(tools['readelf']),'-h','-d','-Ws',str(PRODUCT)],'readelf').decode()
    assembly=run([str(tools['objdump']),'-d',str(PRODUCT)],'objdump').decode()
    symbols=run([str(tools['nm']),'-D',str(PRODUCT)],'nm').decode()
    require(str(REF) in dynamic,'reference DT_NEEDED binding absent')
    require(' T difftest_exec' in symbols and ' T difftest_regcpy' in symbols,'interposed exports absent')
    require('0x32c' in assembly,'compiled byte offset812 absent')
    require('0x80000278' in assembly and '0x294000b' in assembly,'compiled PC/word absent')
    require(b'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=0 pc=0x80000278 instruction=0x0294000b' in PRODUCT.read_bytes(),'compiled injection log absent')
    status='HOST_BIT100_BUILD_PREP_PASS'
finally:
    inputs_after=[pin(p) for p in inputs]
    after=protected()
    save('PROTECTED_AFTER.json',after)
    save('POST_BUILD_INPUTS.json',{'pins':inputs_after,'unchanged':inputs_before==inputs_after})
    if before!=after or inputs_before!=inputs_after: status='FAIL_INPUT_DRIFT'
    result={'status':status,'scope':'COMPILE_AND_STATIC_ONLY','source':pin(SOURCE),'product':pin(PRODUCT) if PRODUCT.exists() else None,
      'freeze':pin(HERE/'SOURCE_FREEZE.json'),'normalization':pin(HERE/'NORMALIZATION_AUDIT.json'),
      'commands':pin(HERE/'COMMANDS.json'),'normal_reference':pin(REF),'reference_identity_matches_old_host_evidence':True,
      'guard':{'pc':0x80000278,'word':0x0294000b,'vd':0},'bit':100,'state_byte_offset':812,'xor_mask':16,
      'software_build_review_unchanged':before==after,'frozen_inputs_unchanged':inputs_before==inputs_after,
      'production_wrapper_loads':0,'native_reference_loads':0,'target_executions':0,'new_host_abi_tests':0,
      'historical_host_evidence':pin(OLD/'RESULT.json'),'target_rejection':'NOT_TESTED',
      'next_runtime_and_strict_negative_parser':'NOT_PREPARED_IN_THIS_TASK','running_authorized':False}
    save('RESULT.json',result)
    print(status)
