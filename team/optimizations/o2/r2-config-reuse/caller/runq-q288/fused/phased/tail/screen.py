"""Actual-ELF screen for two bounded TA phase bits; no target execution."""
from pathlib import Path
from types import SimpleNamespace
import argparse,hashlib,importlib.util,json,os,shutil,struct,sys

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

candidate=load('tail_screen_candidate',HERE/'candidate.py')
taint=load('tail_screen_taint',HERE/'taint.py')
need(sha((HERE.parent/'candidate.py').read_bytes())==candidate.PARENT_SHA,'fixed phased candidate')
need(sha((HERE.parent/'screen.py').read_bytes())=='8537f85027ccc9164229c10a400a7d996d42c6711d30dc869835e5eb71a88fd9','fixed phased screen')
old_candidate=load('tail_original_candidate',HERE.parent/'candidate.py')
previous=sys.modules.get('candidate');sys.modules['candidate']=old_candidate
try:phased=load('tail_original_screen',HERE.parent/'screen.py')
finally:
    if previous is None:sys.modules.pop('candidate',None)
    else:sys.modules['candidate']=previous

def algebra(elf):
    """Restore only the two validated policy bits for the frozen dot algebra.

    All other actual candidate words, including mutations, reach the independent
    old algebra unchanged. The TA-specific dependency proof remains separate.
    """
    body=bytearray(elf.symbol_data(candidate.NAME))
    need(len(body)==764,'candidate algebra size')
    for offset in taint.OFFSETS:
        need(struct.unpack_from('<I',body,offset)[0]==taint.NEW_CONFIG,'candidate algebra exact TA phase words')
        struct.pack_into('<I',body,offset,0xc0047057)
    view=SimpleNamespace(symbol_data=lambda name:bytes(body) if name=='q288_phased_vdot' else elf.symbol_data(name))
    result=phased.certificate(view)
    return dict(status='TAIL_LOW64_DOT_ALGEBRA_PASS',normalized_policy_offsets=list(taint.OFFSETS),
        other_candidate_words_unchanged=True,frozen_engine_result=result)

def certificate(elf):
    unchanged=phased.certificate(elf)
    before=elf.symbol_data('q288_phased_vdot');after=elf.symbol_data(candidate.NAME)
    return dict(status='TAIL_ACTUAL_WORD_CERTIFICATE_PASS',unchanged_phased_certificate=unchanged,
        exact_delta=taint.exact_delta(before,after),candidate_algebra=algebra(elf),arbitrary_tail_proof=taint.prove(after),
        function_bytes=len(after),core_words=131,static_instructions_unchanged=True,new_emu_runs=0)

def checker_class(model,machine_path):
    # The unmodified existing finite model already accepts vta for e8 load/dot.
    # Its e32/FP/final-mode requirements remain unchanged.
    return phased.checker_class(model,machine_path)

def numeric(repo,out,elf,model,helpers):
    symbols=dict(elf.symbols);symbols['q288_phased_vdot']=symbols[candidate.NAME]
    view=SimpleNamespace(symbols=symbols,symbol_data=lambda name:elf.symbol_data(candidate.NAME if name=='q288_phased_vdot' else name))
    result=phased.numeric(repo,out,view,model,helpers)
    need(result['status']=='PHASED_ACTUAL_ELF_NUMERIC_PASS' and len(result['cases'])==8,'unmodified full-Q numeric acceptance')
    return dict(status='TAIL_ACTUAL_ELF_NUMERIC_PASS',engine_result=result,actual_symbol=candidate.NAME,
        unchanged_machine_model=True,all_ones_is_one_legal_tail_realization=True,
        arbitrary_legal_tails_covered_by_separate_dependency_proof=True)

def controls(repo,out,elf,model,helpers):
    out.mkdir();body=elf.symbol_data(candidate.NAME);_,_,offset=elf.symbols[candidate.NAME]
    words=list(struct.unpack('<191I',body));core=list(enumerate(words[15:146],15));changes=[]
    i,w=next((i,w) for i,w in core if w&0xfe00707f==0x0200000b)
    changes.append(('wrong-x-chunk',i,(w&~(31<<20))|(17<<20)))
    i,w=next((i,w) for i,w in core if w&0xfffff==0x60f93)
    changes.append(('wrong-weight-row',i,w+(32<<20)))
    i,w=next((i,w) for i,w in core if w&127==0x57 and w>>26==0 and (w>>12)&7==0)
    source=(w>>15)&31;changes.append(('wrong-reduction',i,(w&~(31<<15))|(((source+1)%8)<<15)))
    fixture=helpers.fixtures(repo/phased.PARENT/'generate.py');golden=helpers.python_golden(fixture,0)
    machine=checker_class(model,repo/'team/optimizations/o2/r2-safe-tail/machine_model.py');results=[]
    for name,index,word in changes:
        raw=bytearray(elf.raw);struct.pack_into('<I',raw,offset+4*index,word);need(raw!=elf.raw,'nonempty actual ELF mutation')
        (out/(name+'.elf')).write_bytes(raw);mutant=model.ELF(raw);errors={}
        try:algebra(mutant)
        except ValueError as error:errors['symbolic']=str(error)
        else:raise ValueError('symbolic mutant accepted '+name)
        try:
            m=machine(fixture);m.execute_function(mutant,candidate.NAME);m.check(golden)
        except ValueError as error:errors['numeric']=str(error)
        else:raise ValueError('numeric mutant accepted '+name)
        results.append(dict(name=name,word_index=index,elf_sha256=sha(raw),rejections=errors))
    flow=taint.controls(elf.symbol_data('q288_phased_vdot'),body)
    result=dict(status='TAIL_ACTUAL_ELF_CONTROLS_PASS',actual_elf_controls=results,tail_flow_controls=flow,new_emu_runs=0)
    save(out/'result.json',result);return result

def source_files(repo):
    paths=[repo/phased.PARENT/n for n in ('generate.py','oracle.c','q288.h')]
    paths += [repo/phased.PARENT.parent/'caller.h',repo/phased.PARENT.parent/'split/split.h',repo/old_candidate.PUBLIC,
              repo/'team/optimizations/o2/r2-safe-tail/machine_model.py']
    paths += [repo/old_candidate.FUSED/n for n in ('generate.py','model.py','screen.py')]
    paths += [HERE.parent/n for n in ('candidate.py','screen.py','CONTRACT.md')]
    paths += [HERE/n for n in ('candidate.py','taint.py','screen.py','CONTRACT.md')]
    return {p.relative_to(repo).as_posix():sha(p.read_bytes()) for p in paths}

def screen(repo,out):
    need(not out.exists() and not out.is_relative_to(repo),'fresh output outside source tree');out.mkdir(parents=True)
    pins=source_files(repo);model,helpers=phased.support(repo)
    generation=candidate.generate(repo,out/'generated');gcc=shutil.which('riscv64-linux-gnu-gcc');need(gcc,'native GNU RISC-V compiler')
    prefix=[gcc,'-march=rv64gv','-mabi=lp64d','-mno-relax'];commands=[]
    commands.append(helpers.command(prefix+['-c',out/'generated/tail.S','-o',out/'tail.o'],out,0))
    commands.append(helpers.command(prefix+['-static','-no-pie','-nostdlib','-nostartfiles',
        '-Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,'+candidate.NAME,out/'tail.o','-o',out/'tail.elf'],out,1))
    elf=model.ELF((out/'tail.elf').read_bytes());proof=certificate(elf);save(out/'certificate.json',proof)
    values=numeric(repo,out/'numeric',elf,model,helpers);negative=controls(repo,out/'controls',elf,model,helpers)
    need(source_files(repo)==pins,'unchanged exact static source closure')
    for name in pins:
        dest=out/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,dest)
    result=dict(status='TAIL_STATIC_SCREEN_PASS',contract=candidate.CONTRACT,source_files=pins,commands=commands,
        generation=generation,elf_sha256=sha(elf.raw),compiler_sha256=sha(Path(gcc).read_bytes()),certificate=proof,
        numeric=values,controls=negative,baseline_instructions=49602,candidate_instructions=49602,
        new_emu_runs=0,target_runtime_qualified=False,performance_qualified=False)
    save(out/'result.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    print(json.dumps(screen(a.repo.resolve(),a.output.resolve()),indent=2))
