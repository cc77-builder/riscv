"""Compile/link ordinary C consumers and check exact qualified Q function bytes."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,shutil,struct,subprocess,sys

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def need(ok,message):
    if not ok:raise ValueError(message)
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def signed(value,bits):return value-(1<<bits) if value&(1<<(bits-1)) else value

def call_targets(elf,name):
    start=elf.symbols[name][0];raw=elf.symbol_data(name);need(len(raw)%4==0,'uncompressed C call boundary')
    words=[w for w, in struct.iter_unpack('<I',raw)];targets=[]
    for i,w in enumerate(words):
        if w&127==0x17 and i+1<len(words):
            j=words[i+1]
            if j&0x707f==0x67 and ((w>>7)&31)!=0 and ((j>>15)&31)==((w>>7)&31):
                targets.append((start+4*i+signed(w&0xfffff000,32)+signed(j>>20,12))&~1)
        elif w&127==0x6f:
            imm=((w>>31)<<20)|(((w>>12)&255)<<12)|(((w>>20)&1)<<11)|(((w>>21)&1023)<<1)
            targets.append(start+4*i+signed(imm,21))
    return targets

def decoder_controls():
    class Sample:
        symbols={'caller':(0x80000000,8)}
        def __init__(self,words):self.words=words
        def symbol_data(self,name):return struct.pack('<'+'I'*len(self.words),*self.words)
    cases=[('auipc_forward',(0x00001097,0x00408067),[0x80001004]),
           ('auipc_backward',(0xfffff097,0xffc08067),[0x7fffeffc]),
           ('jal_forward',(0x0080006f,),[0x80000008]),
           ('jal_backward',(0xffdff06f,),[0x7ffffffc]),
           ('auipc_x0_not_a_pc_relative_call',(0x00001017,0x00000067),[])]
    for name,words,expected in cases:need(call_targets(Sample(words),'caller')==expected,'call decoder control '+name)
    return dict(status='CALL_DECODER_CONTROLS_PASS',cases=[n for n,_,_ in cases])

def check(repo,build,out,variant):
    need(not out.exists() and not out.is_relative_to(repo) and not out.is_relative_to(build),'fresh API outputs outside inputs')
    out.mkdir(parents=True)
    target=HERE/('tail/target/run.py' if variant=='tail' else 'target/run.py');m=load('q288_api_target_identity',target)
    validated=m.verification(repo,build)
    representation_adapter=None
    if variant=='phased':
        adapter_path=HERE/'target/archive_json.py'
        need(sha(adapter_path)=='d1359825a72350f41718d382132f20ca2a4f68464df1a8d8d72a27878722660a','fixed exact-field phased JSON adapter')
        adapter=load('q288_api_phased_json_adapter',adapter_path)
        validated=adapter.json_certificate(validated)
        representation_adapter=dict(path=adapter_path.relative_to(repo).as_posix(),sha256=sha(adapter_path),
            field='phased_certificate.mode_phases',purpose='exact four frozen tuples to JSON arrays only')
    need(validated==json.loads((build/'elf-validation.json').read_text()),'original cached target verification equality')
    decoder=decoder_controls()
    original=m.g.ELF((build/'vdot-perf.elf').read_bytes());exporter=load('q288_api_exporter',HERE/'export.py')
    exported=exporter.export(repo,out/'exported',variant)
    gcc=shutil.which('riscv64-linux-gnu-gcc');nm=shutil.which('riscv64-linux-gnu-nm')
    need(gcc and nm,'native GNU RISC-V C and symbol tools')
    commands=[]
    def command(argv,label):
        directory=out/label;directory.mkdir();start=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (directory/'stdout.log').open('wb') as stdout,(directory/'stderr.log').open('wb') as stderr:
            p=subprocess.run([str(v) for v in argv],cwd=repo,stdout=stdout,stderr=stderr,timeout=60)
        receipt=dict(command=[str(v) for v in argv],cwd=str(repo),started=start,
            finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=p.returncode,
            stdout_sha256=sha(directory/'stdout.log'),stderr_sha256=sha(directory/'stderr.log'))
        save(directory/'command.json',receipt);commands.append(receipt);need(p.returncode==0,'GNU API command '+label)
        return (directory/'stdout.log').read_text()
    q=HERE.parent.parent;caller=q.parent
    base=[gcc,'-march=rv64gv','-mabi=lp64d','-mcmodel=medany','-mno-relax','-fno-pic','-fno-pie','-fno-lto']
    flags=['-std=c11','-O2','-ffreestanding','-fno-builtin','-fno-tree-vectorize','-fno-tree-slp-vectorize',
        '-fno-fast-math','-ffp-contract=off','-I'+str(HERE),'-I'+str(caller),'-I'+str(caller/'split')]
    if variant=='tail':flags.append('-DQ288_INCLUDE_TAIL=1')
    command(base+flags+['-c',HERE/'example.c','-o',out/'consumer.o'],'compile-consumer')
    command(base+flags+['-c',q/'q288.c','-o',out/'pack.o'],'compile-pack')
    command(base+['-c',out/'exported/q288-kernels.S','-o',out/'kernels.o'],'assemble-kernels')
    roots={'q288_api_pack':'q288_pack','q288_api_phased':'q288_phased_vdot',
        'q288_api_fused':'q288_fused_vdot','q288_api_rvv4':'q288_fused_rvv4'}
    if variant=='tail':roots['q288_api_tail']='q288_tail_vdot'
    link=base+['-static','-no-pie','-nostdlib','-nostartfiles','-Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,q288_api_phased']
    link+=['-Wl,--undefined='+n for n in roots]
    command(link+[out/'consumer.o',out/'pack.o',out/'kernels.o','-o',out/'consumer.elf'],'link-consumer')
    undefined=command([nm,'-u',out/'consumer.elf'],'undefined-symbols');need(undefined.strip()=='','no undefined symbol in deliverable ELF')
    defined=command([nm,'--defined-only','-P',out/'consumer.elf'],'defined-symbols')
    inventory=[line.split()[0] for line in defined.splitlines() if line.strip()]
    elf=m.g.ELF((out/'consumer.elf').read_bytes());function_hashes={}
    for name in exported['symbols']:
        need(inventory.count(name)==1,'one linked definition '+name)
        body=elf.symbol_data(name);need(body==original.symbol_data(name),'unchanged qualified full function '+name)
        function_hashes[name]=hashlib.sha256(body).hexdigest()
    calls={}
    for source,dest in roots.items():
        need(inventory.count(source)==1 and elf.symbols[source][1]>0,'retained ordinary C caller '+source)
        found=call_targets(elf,source);need(found==[elf.symbols[dest][0]],'actual direct C call target '+source)
        calls[source]=dict(target=dest,target_address=elf.symbols[dest][0],caller_sha256=hashlib.sha256(elf.symbol_data(source)).hexdigest())
    need(elf.symbols['q288_api_slots'][0]%16==0 and elf.symbols['q288_api_slots'][1]==128,'complete aligned C slot buffer')
    pins=json.loads((build/'build.json').read_text())['software_files']
    need(m.sources(repo)==pins and all(sha(repo/n)==v for n,v in pins.items()),'qualified input source identities remain unchanged')
    inputs=[HERE/n for n in ('phased.h','export.py','example.c','c_api_check.py')]
    if variant=='tail':inputs.append(HERE/'tail/tail.h')
    else:inputs += [HERE/'target/archive_json.py',HERE/'target/ARCHIVE-JSON-CONTRACT.md']
    inputs += [q/'q288.h',q/'q288.c',HERE.parent/'fused.h',caller/'caller.h',caller/'split/split.h']
    source_files={p.relative_to(repo).as_posix():sha(p) for p in inputs}
    for p in inputs:
        destination=out/'source'/p.relative_to(repo);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
    result=dict(status='Q288_ORDINARY_C_FINAL_LINK_AND_TARGET_BYTES_PASS',variant=variant,
        target_elf_sha256=sha(build/'vdot-perf.elf'),consumer_elf_sha256=sha(out/'consumer.elf'),
        cached_result_representation_adapter=representation_adapter,call_decoder_controls=decoder,
        qualified_runtime_sources_checked=len(pins),source_files=source_files,
        toolchain={n:dict(path=p,sha256=sha(p)) for n,p in (('gcc',gcc),('nm',nm))},commands=commands,
        exported_symbols=exported['symbols'],actual_C_calls=calls,function_sha256=function_hashes,
        slot_alignment=16,slot_bytes=128,unresolved_symbols=0,duplicate_exports=0,
        no_linker_garbage_collection=True,new_emu_runs=0,new_target_runtime_qualification=False,
        new_performance_qualification=False,stable_default_changed=False)
    save(out/'result.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','build','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--variant',choices=('phased','tail'),required=True);a=p.parse_args()
    if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    print(json.dumps(check(a.repo.resolve(),a.build.resolve(),a.output.resolve(),a.variant),indent=2))
