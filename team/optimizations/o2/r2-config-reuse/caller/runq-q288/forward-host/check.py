"""Observe a fixed complete upstream forward, then check captured Q calls.

No checkpoint download, target execution, host speed ranking or trained-model
quality claim. The observer never substitutes the upstream computation.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import time
import zipfile

HERE=Path(__file__).resolve().parent
Q=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288')
CONTRACT='r2-s3-runq-forward-host-v1'
ELF_SHA='6975d57aecd77f9ec6337cbf3aa5b031033e8a7b86dcad4bcd7e78b33b2dc97d'
PINS={
    Q/'acc8/q288.c':'f0c557cb837ac05ff713b0eaadb7949b3ba623ae54fe1c02aedcd4220f5bf8d1',
    Q/'q288.h':'f8e4df00dba860487c168f6990edbf2dc8814291b825d30762c7ecad61821cc2',
    Q.parent/'caller.h':'8f8ebbdfc64f506549b8fcb91700fc80dd91b1fd0a5be64aaed504ebcfa0c38e',
    Q.parent/'split/split.h':'94ccdc8e6212c0c0d7ef0e8795c8edcdc9a02e173802bea18965bbce5e01e222',
    Q/'fused/model.py':'703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82',
    Path('team/optimizations/o2/r2-safe-tail/machine_model.py'):'8fb2ac208d8db9083464fb839c06b46ec365234d72b819822563830dad90171e',
}
UPSTREAM_SHA='ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548'
UPSTREAM_BLOB='42360ae97c724d28e11ac4545e30f57b7a9c9a8e'

def need(ok,message):
    if not ok:raise ValueError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main_check(repo,out,elf_input):
    need(not out.exists() and not out.is_relative_to(repo),'fresh output outside input source')
    out.mkdir(parents=True)
    for path,pin in PINS.items():need(sha((repo/path).read_bytes())==pin,'frozen source '+str(path))
    upstream=(HERE/'upstream/runq.c').read_bytes()
    need(sha(upstream)==UPSTREAM_SHA and hashlib.sha1(b'blob '+str(len(upstream)).encode()+b'\0'+upstream).hexdigest()==UPSTREAM_BLOB,
         'exact unchanged upstream commit blob')
    paths=[repo/path for path in PINS]+[HERE/path for path in ('observe.c','check.py','CONTRACT.md','upstream/runq.c','upstream/LICENSE')]
    source_pins={str(path):sha(path.read_bytes()) for path in paths}
    if elf_input:
        image=elf_input.read_bytes()
    else:
        archive=repo/Q/'fused/evidence/screen-v1/raw.zip'
        need(sha(archive.read_bytes())=='201d0b2a01ab246338e6bdc80aaa486bed91254522bd8453c61e1d2de6d70df0','qualified fused archive')
        with zipfile.ZipFile(archive) as z:image=z.read('screen-03/fused.elf')
    need(sha(image)==ELF_SHA,'qualified actual GNU ELF')
    (out/'fused-reference.elf').write_bytes(image)
    build=out/'host-build';build.mkdir();commands=[]
    def command(argv):
        index=len(commands);started=time.time()
        proc=subprocess.run([str(v) for v in argv],cwd=build,capture_output=True,timeout=120)
        (build/f'{index:02}-stdout.log').write_bytes(proc.stdout);(build/f'{index:02}-stderr.log').write_bytes(proc.stderr)
        record=dict(argv=[str(v) for v in argv],exit_code=proc.returncode,elapsed_seconds=time.time()-started,
                    stdout_sha256=sha(proc.stdout),stderr_sha256=sha(proc.stderr))
        commands.append(record);save(build/'commands.json',commands)
        need(proc.returncode==0,'host command failed: '+str(argv[0]));return proc.stdout
    gcc=shutil.which('gcc');need(gcc is not None,'host GNU compiler')
    flags=['-std=gnu11','-O2','-ffp-contract=off','-fno-fast-math','-fexcess-precision=standard',
           '-fno-tree-vectorize','-fno-tree-slp-vectorize','-fno-inline','-fno-ipa-cp','-fno-ipa-sra','-fno-ipa-icf','-fno-lto',
           '-fno-pic','-fno-pie','-Wno-unknown-pragmas','-I'+str(repo/Q),'-I'+str(repo/Q.parent),'-I'+str(repo/Q.parent/'split')]
    command([gcc,*flags,'-finstrument-functions','-c',HERE/'observe.c','-o',build/'observe.o'])
    command([gcc,*flags,'-c',repo/Q/'acc8/q288.c','-o',build/'acc8.o'])
    command([gcc,'-no-pie','-Wl,--build-id=none',build/'observe.o',build/'acc8.o','-lm','-o',build/'observe'])
    libraries=command(['ldd',build/'observe']).decode()
    dynamic={}
    for name in re.findall(r'(/[^\s()]+)',libraries):
        path=Path(name)
        if path.is_file():dynamic[str(path.resolve())]=sha(path.read_bytes())
    need(any('libm.' in name for name in dynamic),'actual math library identity')
    captures=out/'captures';captures.mkdir();raw=command([build/'observe',captures]).decode()
    pattern=r'^FORWARD pass=(\d+) pos=(\d+) token=(\d+) matmuls=(\d+) quantizes=(\d+) rmsnorms=(\d+) softmaxes=(\d+) q_calls=(\d+) groups=(\d+) quantized_elements=(\d+)$'
    observed=[tuple(map(int,row)) for row in re.findall(pattern,raw,re.M)]
    wanted=[(p,i,token,43,25,13,36,24,315,10080) for p in range(2) for i,token in enumerate((1,7,19))]
    need(observed==wanted,'all six actual forward inventories')
    marker='HOST_FORWARD_PASS calls=6 q_observations=144 exported_q_cases=72 pack_calls=24 packed_bytes=1990656 weight_bytes=17101440 embedding_bytes=36864000 controls=3 model_trained=0 target_cycles=0'
    need(raw.splitlines()[-1]==marker,'exact whole-program acceptance marker')
    capture_manifest={path.name:dict(bytes=path.stat().st_size,sha256=sha(path.read_bytes())) for path in sorted(captures.iterdir())}
    wanted_names=set()
    for i in range(24):
        for tag in ('weight','scale','packed'):wanted_names.add(f'{tag}-{i:02}.bin')
    for pos in range(3):
        for tag in ('logits','key','value'):wanted_names.add(f'pos-{pos}-{tag}.bin')
        for i in range(24):
            for tag in ('input','output'):wanted_names.add(f'pos-{pos}-q-{i:02}-{tag}.bin')
    need(set(capture_manifest)==wanted_names,'exact complete capture inventory')
    for pos in range(3):
        for layer in range(6):
            values=[(captures/f'pos-{pos}-q-{4*layer+i:02}-input.bin').read_bytes() for i in range(3)]
            need(values[0]==values[1]==values[2],'actual Q/K/V share one quantized input')
    model=load('complete_forward_fused_model',repo/Q/'fused/model.py')
    elf=model.ELF(image);machine=model.machine_class(repo/'team/optimizations/o2/r2-safe-tail/machine_model.py')
    numeric=[]
    for pos in range(3):
        for index in range(24):
            weight=(captures/f'weight-{index:02}.bin').read_bytes();packed=(captures/f'packed-{index:02}.bin').read_bytes()
            scales=(captures/f'scale-{index:02}.bin').read_bytes();inputs=(captures/f'pos-{pos}-q-{index:02}-input.bin').read_bytes()
            golden=(captures/f'pos-{pos}-q-{index:02}-output.bin').read_bytes()
            need((len(weight),len(packed),len(scales),len(inputs),len(golden))==(82944,82944,10368,324,1152),'actual capture sizes')
            s8=lambda raw:list(struct.unpack('<'+'b'*len(raw),raw))
            u32=lambda raw:list(struct.unpack('<'+'I'*(len(raw)//4),raw))
            fixture=dict(weight=s8(weight),packed=s8(packed),weight_scale=u32(scales),
                         inputs=[s8(inputs[:288])],input_scale=[u32(inputs[288:])])
            expected=u32(golden);row=dict(position=pos,layer=index//4,kind=('Q','K','V','O')[index%4],methods={})
            for method in ('vdot','rvv4'):
                state=machine(fixture,0,poison=pos*24+index)
                state.execute_function(elf,'q288_fused_'+method)
                detail=state.check_full(method,expected)
                row['methods'][method]=dict(function_instructions=detail['function_instructions'],output_sha256=detail['output_sha256'],
                                             final_slots_sha256=detail['final_slots_sha256'],abi_preserved=detail['abi_preserved'],exact_footprints=detail['exact_footprints'])
            numeric.append(row)
    save(out/'captured-q-numeric.json',dict(status='CAPTURED_UPSTREAM_Q_BOTH_FUSED_ELF_MODELS_PASS',cases=numeric))
    need(all(sha(Path(path).read_bytes())==pin for path,pin in source_pins.items()),'all source bytes unchanged')
    need(all(sha(Path(path).read_bytes())==pin for path,pin in dynamic.items()),'host dynamic libraries unchanged')
    for path in paths:
        destination=out/'source-snapshot'/path.relative_to(repo);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
    save(out/'capture-manifest.json',capture_manifest)
    result=dict(status='COMPLETE_UPSTREAM_FORWARD_HOST_AND_CAPTURED_Q_PASS',contract=CONTRACT,
                upstream_commit='350e04fe35433e6d2941dce5a1f53308f87058eb',upstream_blob=UPSTREAM_BLOB,upstream_sha256=UPSTREAM_SHA,
                source_files=source_pins,host=dict(platform=platform.platform(),machine=platform.machine(),python=platform.python_version(),
                    compiler_path=gcc,compiler_sha256=sha(Path(gcc).read_bytes()),dynamic_libraries=dynamic,affinity=sorted(os.sched_getaffinity(0))),
                host_binary_sha256=sha((build/'observe').read_bytes()),fused_elf_sha256=ELF_SHA,
                actual_forward_calls=6,independent_run_states=2,positions=[0,1,2],token_ids=[1,7,19],
                matmuls_per_forward=43,quantizes_per_forward=25,quantized_groups_per_forward=315,quantized_elements_per_forward=10080,
                q_captures=72,distinct_quantized_input_byte_strings=len({capture_manifest[f'pos-{pos}-q-{index:02}-input.bin']['sha256'] for pos in range(3) for index in range(24)}),
                fused_methods=2,actual_elf_numeric_executions=len(numeric)*2,
                checked_outputs=72*2*288,persistent_packs=24,packed_bytes=1990656,
                capture_files=len(capture_manifest),capture_raw_bytes=sum(v['bytes'] for v in capture_manifest.values()),
                complete_logits_and_kv_replay_bit_equal=True,all_reference_weights_readonly=True,
                observer_replaces_reference_compute=False,trained_checkpoint_downloaded=False,
                target_emu_runs=0,cycle_performance_qualified=False,full_model_quality_qualified=False)
    save(out/'result.json',result);return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--fused-elf',type=Path)
    args=parser.parse_args();os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    print(json.dumps(main_check(args.repo.resolve(),args.output.resolve(),args.fused_elf.resolve() if args.fused_elf else None),indent=2))
