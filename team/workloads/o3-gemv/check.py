"""O3 exact straight-line ELF windows; original counter checks remain unchanged."""
import argparse
import importlib.util
import json
import hashlib
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("o3_frozen_counter_checker",ROOT/"team/workloads/unified-vdot/check.py")
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def walk(words):
    start=[pc for pc,w in words.items() if w==base.START]
    stop=[pc for pc,w in words.items() if w==base.STOP]
    base.require(len(start)==len(stop)==1,"unique O3 markers")
    a,b=start[0],stop[0]
    base.require(a<b and (b-a)//4<20000,"invalid O3 straight-line window")
    result=[]
    for pc in range(a,b+4,4):
        base.require(pc in words,"O3 code hole")
        word=words[pc]
        base.require(word&127 not in (0x63,0x6f,0x67),"branch/call/jump in unrolled O3 kernel")
        result.append((pc,word))
    base.require([w for _,w in result if w in base.COUNTERS]==base.COUNTERS,"O3 counter order")
    return result

base.walk=walk


def verify_generation(build, manifest):
    """Validate O3 snapshots, then regenerate with reviewed active code only.

    Never execute the generator supplied by an image receipt. Historical O3
    generators are accepted only by this fixed reviewed digest; active source
    may also match itself. Both paths must reproduce the complete image data.
    """
    build=Path(build)
    receipt=json.loads((build/'build.json').read_text())
    software=receipt.get('software',{})
    for name in ('generate.py','model.py','main.c','Makefile','fixed-layout.ld'):
        key='team/workloads/o3-gemv/'+name
        base.require(key in software and base.sha(build/'source'/name)==software[key],
                     'O3 source hash missing/mismatch '+name)
    renderer=build/'source/renderer/generate.py'
    base.require(software.get('team/workloads/unified-vdot/generate.py')==base.sha(renderer),
                 'O3 renderer source hash mismatch')
    base._provenance.trusted_generator_source(renderer,'unified-vdot')
    here=Path(__file__).resolve().parent
    canonical=lambda p: p.read_bytes().replace(b'\r\n',b'\n')
    source=canonical(build/'source/generate.py')
    base.require(len(source)<=128*1024 and hashlib.sha256(source).hexdigest() in {
        'b0500ec98a3db471f4ed4a9d927fa1854a9a1c2f4c0cbec495fc89918ddf5a57',
        hashlib.sha256(canonical(here/'generate.py')).hexdigest()},
        'unreviewed O3 generator source')
    base.require(canonical(build/'source/model.py')==canonical(here/'model.py'),
                 'unreviewed O3 mathematical model')
    base.require(manifest.get('model_sha256')==software['team/workloads/o3-gemv/model.py'],
                 'O3 manifest/model mismatch')
    spec=importlib.util.spec_from_file_location('o3_reviewed_generator',here/'generate.py')
    generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
    with tempfile.TemporaryDirectory(prefix='o3-regenerate-') as temp:
        output=Path(temp)/'data'
        fresh=generator.generate(output,manifest['suite'],manifest['dataset'],manifest['shard'],manifest['shards'],
                                 manifest['shared_stream'],manifest['variant'])
        base.require(set(fresh)==set(manifest),'O3 manifest field inventory')
        for key in fresh:
            if key not in ('files','model_sha256'):
                base.require(fresh[key]==manifest[key],'O3 generated manifest drift '+key)
        base.require(set(fresh['files'])=={'kernels.S','cases.h'},'O3 generated file inventory')
        generated={}
        for name,digest in fresh['files'].items():
            data=(output/name).read_bytes()
            base.require(hashlib.sha256(data).hexdigest()==digest,'O3 regenerated hash mismatch')
            generated[name]=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
        base.require(generated==manifest['files'],'O3 generated file drift')


_shared_runtime_roles=base.runtime_roles

def runtime_roles(command):
    # O3 emits this exact buffering wrapper; every EMU option still passes the
    # shared strict parser, including duplicate and overriding flag rejection.
    if isinstance(command,list) and len(command)>5 and command[:5]==['timeout','120m','stdbuf','-o0','-e0']:
        command=command[:2]+command[5:]
    return _shared_runtime_roles(command)


base.verify_generation=verify_generation
base.runtime_roles=runtime_roles

def verify(build,run,external=None):
    result=base.verify(Path(build),Path(run),external)
    result["scope"]="O3 full GEMV math/state, live DiffTest, original calibrated counters and exact straight-line ELF retirement"
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build",type=Path,required=True);p.add_argument("--run",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();value=verify(a.build,a.run)
    with a.output.open("x",encoding="utf-8") as f:json.dump(value,f,indent=2);f.write("\n")
    print(json.dumps({"status":value["status"],"windows":len(value["samples"])}))
