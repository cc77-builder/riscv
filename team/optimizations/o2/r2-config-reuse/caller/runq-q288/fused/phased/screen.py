"""Bounded actual-ELF screen for one phased vdot schedule; no EMU."""
from collections import Counter
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import sys

import candidate

HERE=Path(__file__).resolve().parent
PARENT=candidate.FUSED.parent
CONTRACT='r2-s3-runq-q288-phased-screen-v1'
need=candidate.need

def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def support(repo):
    base=repo/candidate.FUSED
    pins={'generate.py':candidate.FUSED_GEN_SHA,
          'model.py':'703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82',
          'screen.py':'39bfbe63942d15ad5bee4e32e08153c2edf56cc8ce2058f74c199550f16cf5ae'}
    need(all(sha((base/n).read_bytes())==pin for n,pin in pins.items()),'frozen support sources')
    generator=load('phased_frozen_generator',base/'generate.py')
    model=load('phased_frozen_model',base/'model.py')
    previous={name:sys.modules.get(name) for name in ('generate','model')}
    sys.modules.update(generate=generator,model=model)
    try:screen=load('phased_frozen_screen',base/'screen.py')
    finally:
        for name,value in previous.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value
    return model,screen

def branch_target(word,pc):
    offset=((word>>31)<<12)|(((word>>7)&1)<<11)|(((word>>25)&63)<<5)|(((word>>8)&15)<<1)
    if offset&4096:offset-=8192
    return pc+offset

def certificate(elf):
    """Independent algebra over actual words; never imports the core generator."""
    baseline=elf.symbol_data('q288_fused_vdot');body=elf.symbol_data('q288_phased_vdot')
    need(sha(baseline)=='9a155c33b9f27ca04d68ab3e0d883d6819876db6dc1c5d6f55ba9a3faa435648',
         'unaltered original full-Q machine body')
    need(len(baseline)==800 and len(body)==764 and body[:60]==baseline[:60],'full prefix and function size')
    old_tail=list(struct.unpack('<45I',baseline[620:]))
    new_tail=list(struct.unpack('<45I',body[584:]))
    changes=[];targets=[]
    for index,(old,new) in enumerate(zip(old_tail,new_tail)):
        if old==0x02058593:
            need(new==0x00858593,'exact group X stride change');changes.append(index)
        elif old&0x707f==0x1063:
            need(new&0x01fff07f==old&0x01fff07f,'unchanged branch condition')
            old_target=branch_target(old,620+4*index);new_target=branch_target(new,584+4*index)
            need(old_target==new_target,'unchanged logical loop target');targets.append(new_target)
        else:need(new==old,'unchanged FP/store/control suffix')
    need(len(changes)==1 and targets==[60,44],'all and only suffix changes')
    words=list(struct.unpack('<131I',body[60:584]))
    pointers={11:('X',0),12:('W',0)};vectors={};reads=Counter();counts=Counter();configs=[];mode=None
    def write(reg,value):
        need(reg not in (8,9),'FP accumulators preserved by integer core')
        vectors[reg]=value
    for word in words:
        op=word&127;f3=(word>>12)&7
        rd,a,b=(word>>7)&31,(word>>15)&31,(word>>20)&31
        if word in (0xc0047057,0xc1027057):
            mode=(8,8) if word==0xc0047057 else (4,32)
            configs.append(mode);counts['vsetivli']+=1
        elif op==0x13 and f3==0:
            imm=word>>20;imm=imm-4096 if imm&2048 else imm
            need((rd,a,imm)==(11,11,8) or (rd,a)==(31,12),'only X advance or W address generation')
            need(a in pointers,'defined pointer source');region,offset=pointers[a]
            pointers[rd]=(region,offset+imm);counts['addi']+=1
        elif word&0xfff0707f==0x02000007:
            need(mode==(8,8) and a in pointers,'eight byte exact load mode/address')
            region,offset=pointers[a];limit=32 if region=='X' else 256
            need(0<=offset<=limit-8,'exact compact input bound')
            values=tuple((region,offset+i) for i in range(8))
            reads.update(values);write(rd,('bytes',values));counts['vle8.v']+=1
        elif word&0xfe00707f==0x0200000b:
            need(mode==(8,8),'exact dot mode')
            need(a in vectors and b in vectors and vectors[a][0]==vectors[b][0]=='bytes','defined quantized operands')
            left,right=vectors[a][1],vectors[b][1]
            need(all(x[0]=='W' and y[0]=='X' for x,y in zip(left,right)),'W/X dot source roles')
            terms=Counter((x[1]//32,x[1]%32,y[1]) for x,y in zip(left,right))
            write(rd,('lanes',(terms,Counter(),Counter(),Counter())));counts['vdot.vv']+=1
        elif op==0x57 and word>>26==0 and f3==0 and (word>>25)&1:
            need(mode==(4,32),'full four-lane integer addition')
            need(a in vectors and b in vectors and vectors[a][0]==vectors[b][0]=='lanes','defined full-width partial sums')
            lanes=tuple(x+y for x,y in zip(vectors[a][1],vectors[b][1]))
            need(all(sum(lane.values())<=32 for lane in lanes),'at most 32 int8 products per sum')
            write(rd,('lanes',lanes));counts['vadd.vv']+=1
        else:raise ValueError('unknown phased core encoding '+hex(word))
    need(configs==[(8,8),(4,32),(8,8),(4,32)],'four exact mode phases')
    need(counts==Counter(vsetivli=4,addi=35,**{'vle8.v':36,'vdot.vv':32,'vadd.vv':24}),'core opcode counts')
    need(pointers[11]==('X',24) and pointers[12]==('W',0),'exact core pointer postconditions')
    wanted=Counter({('W',i):1 for i in range(256)});wanted.update({('X',i):1 for i in range(32)})
    need(reads==wanted,'complete exact W/X byte footprint')
    for row in range(8):
        need(vectors[row]==('lanes',(Counter({(row,k,k):1 for k in range(32)}),Counter(),Counter(),Counter())),
             'each row has every matching W/X product once and all high bits zero')
    return dict(status='PHASED_ACTUAL_WORD_SYMBOLIC_CERTIFICATE_PASS',core_words=len(words),core_sha256=sha(body[60:584]),
                counts=dict(counts),mode_phases=configs,exact_products_per_row=32,high96_zero=True,
                fp_accumulators_preserved=True,maximum_absolute_sum_bound=524288,
                prefix_bytes=60,suffix_words=45,logical_loop_targets=targets,x_core_advance=24,x_suffix_advance=8)

def checker_class(model,machine_path):
    base=model.machine_class(machine_path)
    class Phased(base):
        def check(self,golden):
            begin=self.function_begin+60;length=131
            expected=[(begin+4*i,self.function_words[begin+4*i]) for i in range(length)]
            starts=[i for i,(pc,_) in enumerate(self.path) if pc==begin]
            need(len(starts)==324 and all(self.path[i:i+length]==expected for i in starts) and
                 sum(begin<=pc<begin+4*length for pc,_ in self.path)==324*length,'324 actual 131-word core executions')
            need(self.regions['y']==struct.pack('<288I',*golden),'actual phased full-Q bitwise output')
            f,d=self.fixture,self.dataset
            dots=[sum(f['weight'][r*288+k]*f['inputs'][d][k] for k in range(256,288)) for r in range(280,288)]
            need(self.regions['slots']==b''.join(struct.pack('<I',v&0xffffffff)+bytes(12) for v in dots),'complete final slots')
            need(all(bytes(self.regions[n])==raw for n,raw in self.original.items() if n not in ('y','slots')),'all inputs/context readonly')
            reads=Counter()
            for name,size,times in (('packed',82944,1),('x',288,36),('ws',10368,1),('xs',36,36),('context',48,1)):
                reads.update({(name,i):times for i in range(size)})
            need(self.read_bytes_count==reads,'exact complete source footprint')
            writes=Counter({(name,i):1 for name,size in (('y',1152),('slots',128)) for i in range(size)})
            need(self.write_bytes_count==writes,'exact complete output footprint')
            need(all(self.x[i]==v for i,v in self.saved.items()) and all(self.f[i]==v for i,v in self.saved_fp.items()),'full-width ordinary ABI')
            self.mode(8,8,1);need(self.vcsr==7 and self.frm==0,'final CSR and RNE')
            need(self.fp_counts==Counter(convert=2592,mul=5184,add=2592),'strict FP operation counts')
            need(self.counts['vdot.vv']==10368 and self.counts['vadd.vv']==7776 and
                 self.counts['vs1r.v']==8 and self.counts['vse32.v']==36 and self.counts['ret']==1,'full instruction/slot/output count')
            need(len(self.path)==49602,'actual complete function instruction count')
            return dict(instructions=len(self.path),counts=dict(self.counts),output_sha256=sha(self.regions['y']),
                        final_slots_sha256=sha(self.regions['slots']),core_executions=324,core_words=131,
                        inputs_readonly=True,exact_footprints=True,abi_preserved=True,stack_used_bytes=0)
    return Phased

def numeric(repo,out,elf,model,helpers):
    out.mkdir();headers={'q288.h':repo/PARENT/'q288.h','caller.h':repo/PARENT.parent/'caller.h',
                       'split.h':repo/PARENT.parent/'split/split.h'}
    library=helpers.oracle_library(repo/PARENT/'oracle.c',headers,out/'oracle')
    fixture=helpers.fixtures(repo/PARENT/'generate.py');cases=[('x'+str(d),fixture,d) for d in (0,1,0,2)]
    for name,w,x in (('min-min',[-128]*82944,[-128]*288),('max-max',[127]*82944,[127]*288),
                     ('min-max',[-128]*82944,[127]*288),('zero-weight',[0]*82944,fixture['inputs'][0])):
        f=copy.deepcopy(fixture);f['weight']=w;f['inputs'][0]=x
        f['packed']=[w[(8*t+r)*288+g*32+k] for t in range(36) for g in range(9) for r in range(8) for k in range(32)]
        cases.append((name,f,0))
    machine=checker_class(model,repo/'team/optimizations/o2/r2-safe-tail/machine_model.py')
    results=[];previous=None
    for index,(name,f,d) in enumerate(cases):
        golden=helpers.native_golden(library,f,d)
        need(golden==helpers.python_golden(f,d),'independent native C/Python reference agreement')
        if index<4:need(golden==f['golden'][d],'frozen fixture golden')
        alignment=(0,0) if index<4 else ((index*3)%16,(index*7)%16)
        m=machine(f,d,poison=0x28840+index,alignment=alignment)
        if index in (1,2,3):
            need(m.regions['packed']==previous.regions['packed'],'same packed object content')
            m.regions['packed']=previous.regions['packed'];m.v=[bytearray(v) for v in previous.v]
        m.execute_function(elf,'q288_phased_vdot')
        results.append(dict(case=name,dataset=d,alignment=alignment,**m.check(golden)));previous=m
    result=dict(status='PHASED_ACTUAL_ELF_NUMERIC_PASS',cases=results)
    save(out/'result.json',result);return result

def controls(repo,out,elf,model,helpers):
    out.mkdir();body=elf.symbol_data('q288_phased_vdot');_,_,offset=elf.symbols['q288_phased_vdot']
    words=list(struct.unpack('<191I',body));core=list(enumerate(words[15:146],15));changes=[]
    i,w=next((i,w) for i,w in core if w&0xfe00707f==0x0200000b)
    changes.append(('wrong-x-chunk',i,(w&~(31<<20))|(17<<20)))
    i,w=next((i,w) for i,w in core if w&0xfffff==0x60f93)
    changes.append(('wrong-weight-row',i,w+(32<<20)))
    i,w=next((i,w) for i,w in core if w&127==0x57 and w>>26==0 and (w>>12)&7==0)
    source=(w>>15)&31;changes.append(('wrong-reduction',i,(w&~(31<<15))|(((source+1)%8)<<15)))
    fixture=helpers.fixtures(repo/PARENT/'generate.py');golden=helpers.python_golden(fixture,0)
    machine=checker_class(model,repo/'team/optimizations/o2/r2-safe-tail/machine_model.py');results=[]
    for name,index,word in changes:
        raw=bytearray(elf.raw);struct.pack_into('<I',raw,offset+4*index,word);need(raw!=elf.raw,'nonempty actual ELF mutation')
        (out/(name+'.elf')).write_bytes(raw);mutant=model.ELF(raw);errors={}
        try:certificate(mutant)
        except ValueError as error:errors['symbolic']=str(error)
        else:raise ValueError('symbolic mutant accepted '+name)
        try:
            m=machine(fixture);m.execute_function(mutant,'q288_phased_vdot');m.check(golden)
        except ValueError as error:errors['numeric']=str(error)
        else:raise ValueError('numeric mutant accepted '+name)
        results.append(dict(name=name,word_index=index,elf_sha256=sha(raw),rejections=errors))
    result=dict(status='PHASED_ACTUAL_ELF_CONTROLS_PASS',controls=results);save(out/'result.json',result);return result

def screen(repo,out):
    need(not out.exists() and not out.is_relative_to(repo),'fresh output outside checkout');out.mkdir(parents=True)
    model,helpers=support(repo)
    sources=[repo/PARENT/n for n in ('generate.py','oracle.c','q288.h')]
    sources += [repo/PARENT.parent/'caller.h',repo/PARENT.parent/'split/split.h',repo/candidate.PUBLIC,
                repo/'team/optimizations/o2/r2-safe-tail/machine_model.py']
    sources += [repo/candidate.FUSED/n for n in ('generate.py','model.py','screen.py')]
    sources += [HERE/n for n in ('candidate.py','screen.py','CONTRACT.md')]
    pins={str(p):sha(p.read_bytes()) for p in sources}
    generation=candidate.generate(repo,out/'generated');gcc=shutil.which('riscv64-linux-gnu-gcc');need(gcc,'native GNU RISC-V compiler')
    prefix=[gcc,'-march=rv64gv','-mabi=lp64d','-mno-relax'];commands=[]
    commands.append(helpers.command(prefix+['-c',out/'generated/phased.S','-o',out/'phased.o'],out,0))
    commands.append(helpers.command(prefix+['-static','-no-pie','-nostdlib','-nostartfiles',
        '-Wl,--build-id=none,--no-relax,-Ttext=0x80000000,-e,q288_phased_vdot',out/'phased.o','-o',out/'phased.elf'],out,1))
    elf=model.ELF((out/'phased.elf').read_bytes());proof=certificate(elf);save(out/'certificate.json',proof)
    values=numeric(repo,out/'numeric',elf,model,helpers);negative=controls(repo,out/'controls',elf,model,helpers)
    need(all(sha(Path(path).read_bytes())==pin for path,pin in pins.items()),'all screen sources unchanged')
    for path in sources:
        destination=out/'source-snapshot'/path.relative_to(repo)
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
    result=dict(status='PHASED_STATIC_SCREEN_PASS',contract=CONTRACT,source_files=pins,commands=commands,
                generation=generation,elf_sha256=sha(elf.raw),compiler_sha256=sha(Path(gcc).read_bytes()),
                certificate=proof,numeric_status=values['status'],cases=len(values['cases']),controls=len(negative['controls']),
                baseline_instructions=52518,candidate_instructions=49602,instruction_reduction=2916,
                new_emu_runs=0,target_runtime_qualified=False,performance_qualified=False)
    save(out/'result.json',result);return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if os.name=='posix':os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    print(json.dumps(screen(args.repo.resolve(),args.output.resolve()),indent=2))
