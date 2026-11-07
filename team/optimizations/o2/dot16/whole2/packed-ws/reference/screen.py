#!/usr/bin/env python3
"""Eight-window K288/K768 packed-Ws reference screen; scalar crossing is a fixed prerequisite."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = "r3-packed-ws-eight-window-reference-v2"
BASE = 0x80000000
ORDER = [1,2,3,4,4,3,2,1]
ABI = {'bytes': 1400, 'regs_int': 0, 'regs_fp': 256, 'csr': 512, 'pc': 656, 'hcsr': 664, 'regs_vec': 800, 'vcsr': 1312, 'fcsr': 1368, 'triggercsr': 1376}


def need(ok, message):
    if not ok: raise ValueError(message)


def read(path): return json.loads(Path(path).read_bytes())


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha(raw): return hashlib.sha256(raw).hexdigest()


def stamp(): return datetime.now(timezone.utc).isoformat()


def save(path, value): Path(path).write_text(json.dumps(value,indent=2)+'\n')


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj)
    return obj


def fnv(raw):
    h=14695981039346656037
    for b in raw:h=((h^b)*1099511628211)&((1<<64)-1)
    return h


def replace_exact(text,before,after,count=1):
    need(text.count(before)==count and after not in text,'unique derivation '+before[:50])
    return text.replace(before,after)


def inspect(elf, raw, kernels, scalar):
    data=elf.raw
    kind,entry=struct.unpack_from('<H',data,16)[0],struct.unpack_from('<Q',data,24)[0]
    need(kind==2 and entry==BASE,'static RV64 original AM entry')
    phoff=struct.unpack_from('<Q',data,32)[0];phsize,phnum=struct.unpack_from('<HH',data,54)
    segments=[struct.unpack_from('<IIQQQQQQ',data,phoff+i*phsize) for i in range(phnum)]
    need(not any(x[0] in (2,3,7) for x in segments),'no dynamic interpreter or TLS segment')
    alloc=sorted((s for s in elf.sections if s[2]&2 and s[5]),key=lambda s:s[3])
    need(alloc and alloc[0][3]==BASE,'RAM base')
    need(all(BASE<=s[3]<s[3]+s[5]<=0x88000000 for s in alloc),'whole allocation in RAM')
    need(all(a[3]+a[5]<=b[3] for a,b in zip(alloc,alloc[1:])),'disjoint sections')
    need(not any(s[1] in (4,9) and s[2]&2 and any(data[s[4]:s[4]+s[5]]) for s in elf.sections),'no live allocated relocations')
    image=bytearray(max(s[3]+s[5] for s in alloc)-BASE)
    for s in alloc:
        if s[1]!=8:image[s[3]-BASE:s[3]-BASE+s[5]]=data[s[4]:s[4]+s[5]]
    need(bytes(image)==raw,'complete actual ELF/BIN identity including BSS')
    for name in ('_start','team_forward_main','_putc',scalar,'full_success_trap','reject',*kernels):
        need(name in elf.symbols,'actual required symbol '+name)
    need('_trm_init' not in elf.symbols and 'q768_fr' not in elf.symbols and 'q768_ta' not in elf.symbols,'exact new executable routes')
    for name,(length,pin) in kernels.items():
        addr,size,_=elf.symbols[name];body=elf.symbol_data(name)
        need(size==length and sha(body)==pin,'complete linked GNU kernel identity '+name)
        need(any(s[0]==1 and s[1]&5==5 and s[3]<=addr<addr+size<=s[3]+s[5] for s in segments),'whole kernel in RX PT_LOAD')
    top=elf.symbols['_stack_top'][0];stack=elf.symbols['_stack_pointer'][0];heap=elf.symbols['_heap_start'][0]
    need(stack%16==0 and len(image)+BASE<=top<=stack<heap<0x88000000,'data/stack/heap bounds')
    failure=elf.symbol_data('reject');addr=elf.symbols['reject'][0]
    need(len(failure)%4==0,'uncompressed exact reject extent')
    traps=[i for i in range(0,len(failure),4) if struct.unpack_from('<I',failure,i)[0]&127==0x6b]
    need(len(traps) in (1,2) and all(i>=4 and failure[i-4:i+4]==struct.pack('<2I',0x05b00513,0x0005006b) for i in traps),'all complete rs1=a0 code91 failure traps')
    success=elf.symbols['full_success_trap'][0]
    need(raw[success-BASE:success-BASE+4]==struct.pack('<I',0x0000006b),'actual good trap')
    main=elf.symbol_data('team_forward_main');counters=[]
    for at in range(0,len(main)-3,4):
        w=struct.unpack_from('<I',main,at)[0]
        if w&0x707f==0x2073 and (w>>15)&31==0 and w>>20 in (0xc00,0xc02):
            need(at>=4 and main[at-4:at]==main[at+4:at+8]==struct.pack('<I',0x0ff0000f),'actual fenced counter sites')
            counters.append(w>>20)
    need(counters==[0xc00,0xc02,0xc02,0xc00],'ordered whole-kernel counter window')
    return dict(image_bytes=len(raw),failure_pcs=[addr+i for i in traps],success_pc=success,kernels={n:dict(address=elf.symbols[n][0],bytes=l,sha256=h) for n,(l,h) in kernels.items()})


def derive_validator(raw):
    text=raw.decode();tree=ast.parse(text)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate']
    need(len(nodes)==1,'one complete original validator')
    original=ast.get_source_segment(text,nodes[0])+'\n';changed=original
    edits=[("('input','input-scales','weight','packed','scales','gold','slot-gold')",
            "('input','input-scales','weight','packed','scales','gold','slot-gold','expected-flags','packed-scales')"),
           ('flags==1 and fnv==',"flags==record['expected_flags'] and fnv=="),
           ('1 if negative else 9,0 if negative else 9','1 if negative else 8,0 if negative else 8')]
    for before,after in edits:changed=replace_exact(changed,before,after)
    restored=changed
    for before,after in reversed(edits):restored=restored.replace(after,before,1)
    need(restored==original,'complete original validator inverse')
    namespace=dict(Path=Path,struct=struct,need=need,read=read,digest=digest,ORDER=ORDER)
    exec(compile(changed,'derived-original-w2-validator.py','exec'),namespace)
    return namespace['validate'],changed,edits


def pack_scale_bytes(raw,k):
    groups=k//32;need(len(raw)==288*groups*4,'complete source scale bytes')
    indices=[(8*t+r)*groups+g for t in range(36) for g in range(groups) for r in range(8)]
    need(sorted(indices)==list(range(288*groups)),'complete scale permutation')
    return b''.join(raw[4*i:4*i+4] for i in indices)


def run(a):
    deadline=time.monotonic()+a.budget_seconds
    os.sched_setaffinity(0,{a.cpu});os.setpriority(os.PRIO_PROCESS,0,5)
    need(os.sched_getaffinity(0)=={1} and os.getpriority(os.PRIO_PROCESS,0)==5,'actual CPU1/absolute nice5')
    here=Path(__file__).resolve().parent
    narrow,w2,gnu,fixtures,adapter,hwpath,template,support,prior,out=(getattr(a,n).resolve() for n in
        ('narrow_build','w2_reference','gnu','q288_fixtures','adapter','hardware','reference_template','support_adapter_source','prior_reference','output'))
    need(not out.exists() and 300<=a.budget_seconds<=1800,'fresh output and finite budget')
    for p in (here,narrow,w2,gnu,fixtures,adapter,hwpath.parent,template.parent,support.parent,prior):
        need(out!=p and not out.is_relative_to(p) and not p.is_relative_to(out),'separate source/output scopes')
    pins={}
    def pin(path,expected=None):
        p=Path(path).absolute();h=digest(p)
        need(expected is None or h==expected,'fixed input '+str(p))
        need(str(p) not in pins or pins[str(p)]==h,'consistent input pin')
        pins[str(p)]=h;return p
    manifest=read(here/'source-manifest.json');pin(here/'source-manifest.json')
    need(set(manifest['files'])=={'screen.py','main.c','flags_host.c','REFERENCE_CONTRACT.md','source-derivation.json'},'exact controller source inventory')
    for name,h in manifest['files'].items():pin(here/name,h)
    need(manifest['files']['screen.py']==digest(Path(__file__)),'actual controller source')
    pin(prior/'result.json','cec287cff44cdda1070539515a3d426fd81e6a4025e0a84ac6bcb632ef7f1f5a')
    previous=read(prior/'result.json')
    need(previous['contract']=='r3-packed-ws-two-geometry-reference-v1'
         and previous['status']=='PACKED_WS_BOTH_GEOMETRIES_REFERENCE_PASS'
         and previous['reference_qualified'] and previous['all_inputs_unchanged'] and previous['all_children_reaped']
         and previous['reference_runs']==10 and previous['target_emu_runs']==0,'closed full scalar/four-arm reference')
    for path,h in {**previous['snapshots'],**previous['generated_inputs']}.items():pin(path,h)
    for k,case in (('288','normal-0'),('768','normal')):
        v=previous['campaigns'][k]['validations'][case]
        need(v['samples'][0][0]==0 and len(v['samples'])==9 and v['prepared_all_bytes']
             and v['packed_slots_all_bytes'] and v['final_fcsr']==1,'prior complete scalar crossing')

    pin(gnu/'result.json','369307b6a392df26e1e34f5a643feb2cadb96f84ada8006214625ba6e27ebb8e')
    gr=read(gnu/'result.json')
    need(gr['status']=='PACKED_WS_FOUR_KERNEL_GNU_IDENTITY_PASS' and gr['all_pins_unchanged'] and gr['all_children_reaped'],
         'closed complete GNU identity stage')
    for name,h in {'packed.S':'445ff9a47f182e8f876caf1dcd89eac2d13a25ebccd3ceb91d21a194d31edb15',
        'packed_ws.h':'0c2bf40d4339f59a973595435838486e0cb536a07b395a8bc9ac664a2da97bfd',
        'pack.c':'7cca44cca9766762b46af4afbbab82a89fafaa4b329c6954558defeb93a55237',
        'model.py':'703667b537c652b22a7dd82f8e3d3a7a42e965d7b5df7d4627b78e0d7358cc82',
        'process_helper.py':'db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3',
        'parent-dot16.S':'40d263b68ead735b84cb626086674463fbb81154ed9898eb8a340f95f102d671',
        'parent-paired16.S':'452ecab3ae3122dd8ea3d5ae05140197a10bb14a9a5ab76437f7591b00b29caf',
        'parent-w2_np.S':'fbe3a93f642ec3468da92ae776e1b547c29c527d4dffc30456191b437d1272c5'}.items():pin(gnu/'inputs'/name,h)
    pin(w2/'result.json','7d46f70b4cb105bd468577815e21c97fe9fa249fb447eeec3c977d9236e3b8c1')
    pin(w2/'static.json','b498a43984c64707d28861505275fb0aff0e23e64778ba68d92350873e5bc448')
    wr=read(w2/'result.json');ws=read(w2/'static.json')
    need(wr['status']=='K768_N_P_REAL_FIXTURE_AND_EDGE_REFERENCE_PASS' and wr['all_inputs_unchanged'] and wr['all_children_reaped'],
         'closed K768 real and edge reference evidence')
    original=wr['original_inputs']
    for name,h in {'Makefile':'f9677131b47cf2ff8da112bdf97fcd4aa1fec0716792fb8c2e46e60ec4f8454c',
        'entry.S':'7db6047a7dfea8a4a1cd98ba95b2845c03405d4fc8aee638463e241da6290531',
        'scalar.c':'a1ca625fbd564d844ef905aa794a33cb5cf01864ba6c55cbd593f2eedf03b719',
        'w2.h':'605a28aef27442e6ea15cae94f2350cdd7ac69ed40af7ea501f9650d6606544e',
        'upstream/runq.c':'ba9cc681afca79f994f815dfeffc4a61c5b3ca8c5d4d4dcb75c8d375856ba548'}.items():pin(w2/'source'/name,h)
    for name,h in {'q288.h':'f8e4df00dba860487c168f6990edbf2dc8814291b825d30762c7ecad61821cc2',
        'split.h':'94ccdc8e6212c0c0d7ef0e8795c8edcdc9a02e173802bea18965bbce5e01e222',
        'caller.h':'8f8ebbdfc64f506549b8fcb91700fc80dd91b1fd0a5be64aaed504ebcfa0c38e',
        'oracle.c':'6e72ed5b4e6b4ea804d34212e9e84d9001207eea076a26a8a835f2a1c29f9dec'}.items():pin(narrow/'source'/name,h)
    pin(fixtures/'manifest.json','13d05882e6f1876993a6e6b63c8d5041c1067bdfb73ba061adf41f91d66f2bd1')
    pin(fixtures/'result.json');fm=read(fixtures/'manifest.json');fr=read(fixtures/'result.json')
    need(fr['status']=='K288_FIXED_FIXTURES_EXTRACTED_AND_VALUE_CHECKED' and fr['inputs_unchanged'] and fr['outputs_readback_verified']
         and fr['manifest']['sha256']==digest(fixtures/'manifest.json') and fm['exact_flags_resolved'] is False,'actual closed K288 extraction')
    need(set(fm['cases'])=={'normal-0','normal-1','normal-2','fullmin'},'four fixed K288 cases')
    for case,record in fm['cases'].items():
        need(record['expected_flags'] is None and record['binary32_value_check_passed'],'exact flags intentionally unresolved')
        for name,meta in record['files'].items():
            p=pin(fixtures/'cases'/case/'fixture'/name,meta['sha256']);need(p.stat().st_size==meta['bytes'],'full fixture span')
    for kind in ('normal','edge'):
        for name,h in ws['records'][kind]['fixtures'].items():pin(w2/'images'/kind/'fixture'/name,h)
    appfiles=[Path(p) for p in original if p.endswith('/Makefile.app')]
    need(len(appfiles)==1,'one existing AM build root');am=appfiles[0].parent
    for p,h in original.items():
        if Path(p).is_relative_to(am):pin(p,h)
    need(not out.is_relative_to(am) and not am.is_relative_to(out),'output outside immutable AM')
    toolfiles=[Path(p) for p in original if p.endswith('/tools.json')]
    need(len(toolfiles)==1,'one frozen GNU tool record');pin(toolfiles[0],original[str(toolfiles[0])])
    toolrec=read(toolfiles[0]);tools={name:record['path'] for name,record in toolrec.items()}
    for name in ('gcc','ld','ar','objcopy','objdump','readelf','nm','make'):pin(tools[name],toolrec[name]['sha256'])
    pin('/usr/bin/riscv64-linux-gnu-as','30ab46dce94fa2120f9465dd2965784af831363f75fac42ea9999819f6d15953')
    hostcc=pin('/usr/bin/x86_64-linux-gnu-gcc-11','821af3c74506283c179ca413bb33e6b528805a4dd8a5c09df125e5ad560a9e89')
    pin(hwpath,'e825fff45feb5afa9952140d9832ec8afe9393c02ebd1ab1558ddcfb4a63ae8f');hw=read(hwpath)
    flags=dict(VDOT_DOT16='1',VDOT_O2_ELASTIC='1',VDOT_T14_FUSED_INPUT='1',VDOT_O1_HANDOFF='0',
               VDOT_O1_TRACE='0',VDOT_O2_TRACE='0',VDOT_T12_TRACE='0',VDOT_T13_TRACE='0')
    need(hw['status']=='DOT16_FULLCORE_SMOKE_PASS' and hw['qualification']['fixed_six_legal_case_fullcore_difftest'] is True
         and hw['abi']['actual_dynamic_difftest_passed'] is True and hw['abi']['layout']==ABI and hw['source_identity']['flags']==flags,
         'fixed actual dot16 runtime/ABI identity')
    for p,h in hw['runtime_inputs'].items():pin(p,h)
    refs=[p for p,h in hw['runtime_inputs'].items() if h=='cc768488944941d59442727a96e0a19206e24872dcefed0052cf6cb3694a3fae']
    need(len(refs)==1,'one exact dot16 reference');reference=refs[0]
    pin(adapter/'build.json','afc535c9b4eaf64ca6c7ba3dafd5b7f93ac8b56d2f280060e892f2816a56669f')
    ar=read(adapter/'build.json');pin(adapter/'inputs.json',ar['inputs_sha256'])
    need(ar['status']=='REFERENCE_ADAPTER_BUILD_PASS','existing qualified reference adapter')
    for p,h in read(adapter/'inputs.json')['files'].items():pin(p,h)
    for name,h in ar['artifacts'].items():pin(adapter/name,h)
    pin(support,'6ea9a43ddfa4420f00c7e62f101035e1e7fbf85610e607c4d7762b96c803bd2b')
    need((adapter/'reference_runner.c').read_bytes()==support.read_bytes(),'unchanged complete reference adapter')
    compile_record=read(adapter/'compile.command.json')
    need(compile_record.get('exit_code')==0 and compile_record.get('status')=='exited' and compile_record.get('process_group_absent_after_exit') is True,
         'closed original adapter compile')
    pin(template,'9bc23d73550f0de16b2816fc732031f53dd81f6c9a483ce233ac2d2c4a7f41fa')
    out.mkdir(parents=True);snap=out/'inputs';snap.mkdir();snapshots={};generated={}
    def copy(path,dest):
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        need(digest(dest)==pins[str(path.absolute())],'exact source snapshot '+str(path));snapshots[str(dest)]=digest(dest)
    for name in manifest['files']:copy(here/name,snap/name)
    copy(here/'source-manifest.json',snap/'source-manifest.json')
    for name in ('model.py','process_helper.py'):copy(gnu/'inputs'/name,snap/name)
    copy(template,snap/'original-reference.py')
    model=module(snap/'model.py','packed_screen_elf');helper=module(snap/'process_helper.py','packed_screen_process')
    validate,checktext,checkedits=derive_validator((snap/'original-reference.py').read_bytes())
    (out/'derived-validator.py').write_text(checktext);generated[str(out/'derived-validator.py')]=digest(out/'derived-validator.py')
    result=dict(contract=CONTRACT,status='RUNNING',started=stamp(),commands=[],reference_runs=0,target_emu_runs=0,
        reference_qualified=False,target_runtime_qualified=False,performance_qualified=False,application_performance_qualified=False,
        production_routes_modified=False,cpu_affinity=[1],nice=5,budget_seconds=a.budget_seconds,original_inputs=pins,snapshots=snapshots)
    save(out/'inputs.json',dict(originals=pins,snapshots=snapshots));save(out/'result.json',result)
    pending=[None]
    def interrupt(s,f):
        if pending[0] is None:pending[0]=s
    def check():
        if pending[0] is not None:raise InterruptedError('received signal '+str(pending[0]))
    signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
    env={**os.environ,'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
         'MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(out),'GIT_OPTIONAL_LOCKS':'0'}
    for k in ('CFLAGS','CPPFLAGS','CXXFLAGS','ASFLAGS','LDFLAGS','CC_OPT','MAKEFLAGS','MFLAGS','MAKEFILES','MAKEOVERRIDES',
              'CC','AS','LD','OBJCOPY','OBJDUMP','ARCH','MARCH','LIBS','PREBUILD','GIT_DIR','GIT_WORK_TREE',
              'GCC_EXEC_PREFIX','COMPILER_PATH','LIBRARY_PATH'):env.pop(k,None)
    env.update(AM_HOME=str(am),LINUX_GNU_TOOLCHAIN='1',MAKEFLAGS='-j1')
    soft,hard=resource.getrlimit(resource.RLIMIT_FSIZE);limit=32*1024*1024
    need(hard==resource.RLIM_INFINITY or hard>=limit,'32MiB output file cap');resource.setrlimit(resource.RLIMIT_FSIZE,(limit,hard))
    def command(label,argv,cwd=out,budget=120,expected=0,guest=False):
        check();remaining=deadline-time.monotonic();need(remaining>0,'total deadline before '+label)
        rec=dict(label=label,command=list(map(str,argv)),cwd=str(cwd),started=stamp(),budget_seconds=min(budget,remaining),
                 process_started=False,exit_code=None,cpu_affinity=sorted(os.sched_getaffinity(0)))
        result['commands'].append(rec);proc=None
        try:
            with (cwd/(('stdout' if guest else label)+'.log')).open('wb') as stdout,(cwd/(('stderr' if guest else label+'.stderr')+'.log')).open('wb') as stderr:
                proc=subprocess.Popen(rec['command'],cwd=cwd,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
                rec.update(pid=proc.pid,process_started=True)
                if guest:result['reference_runs']+=1
                save(out/'result.json',result);until=time.monotonic()+rec['budget_seconds']
                while True:
                    check();left=until-time.monotonic()
                    if left<=0:rec['timed_out']=True;raise subprocess.TimeoutExpired(rec['command'],rec['budget_seconds'])
                    try:rec['exit_code']=proc.wait(timeout=min(.25,left));break
                    except subprocess.TimeoutExpired:continue
            need(rec['exit_code']==expected,label+' exit mismatch')
            need(not helper.group_exists(proc.pid),label+' residual process group')
        finally:
            if proc is not None:
                if helper.group_exists(proc.pid):rec['cleanup_complete']=helper.stop_group(proc)
                rec['direct_child_reaped']=proc.poll() is not None
                rec['process_group_absent_after_exit']=not helper.group_exists(proc.pid)
                rec['residual_process_group']=not rec['process_group_absent_after_exit']
            rec['finished']=stamp();save(out/'result.json',result)
            if guest:save(cwd/'result.json',rec)
        return rec
    try:
        host=out/'host-flags';host.mkdir()
        for name in ('q288.h','split.h','caller.h','oracle.c'):copy(narrow/'source'/name,host/name)
        copy(here/'flags_host.c',host/'flags_host.c')
        command('host-flags-build',[hostcc,'-std=gnu11','-O2','-Wall','-Wextra','-Werror','-Wno-error=unknown-pragmas',
            '-fno-fast-math','-ffp-contract=off','-frounding-math','-fno-tree-vectorize','-fno-tree-slp-vectorize',
            '-fexcess-precision=standard','-I',host,host/'flags_host.c',host/'oracle.c','-lm','-o',host/'flags-host'],budget=30)
        generated[str(host/'flags-host')]=digest(host/'flags-host');host_flags={}
        for case in ('normal-0','normal-1','normal-2','fullmin'):
            path=host/(case+'.bin')
            command('host-flags-'+case,[host/'flags-host',fixtures/'cases'/case/'fixture',path],budget=15)
            raw=path.read_bytes();need(len(raw)==4,'complete host flags word');value=struct.unpack('<I',raw)[0]
            need(value<=31,'valid accrued RISC-V flags')
            text=(out/('host-flags-'+case+'.log')).read_text()
            need(re.fullmatch(r'K288_HOST_ORACLE_FLAGS_PASS bytes=1152 riscv_flags='+str(value)+r' host_exceptions=\d+\n',text) is not None,
                 'host exact gold and fenv receipt')
            host_flags[case]=value;generated[str(path)]=digest(path)
        need(host_flags==previous['host_oracle_expected_flags'],'same independently crossed host flags')
        result['host_oracle_expected_flags']=host_flags;result['prior_reference_result_sha256']=digest(prior/'result.json');save(out/'result.json',result)
        campaigns={};makefile_edits={}
        for k in (288,768):
            check();work=out/('k'+str(k));work.mkdir();source=work/'source';source.mkdir()
            for name in ('entry.S','w2.h'):copy(w2/'source'/name,source/name)
            for name in ('q288.h','split.h','caller.h'):copy(narrow/'source'/name,source/name)
            if k==288:copy(narrow/'source/oracle.c',source/'scalar.c')
            else:
                copy(w2/'source/scalar.c',source/'scalar.c');copy(w2/'source/upstream/runq.c',source/'upstream/runq.c')
            for name in ('packed.S','packed_ws.h','pack.c'):copy(gnu/'inputs'/name,source/name)
            for name in ('dot16.S','paired16.S','w2_np.S'):copy(gnu/'inputs'/('parent-'+name),source/name)
            copy(here/'main.c',source/'main.c')
            rawmake=(w2/'source/Makefile').read_text();newmake=rawmake
            edits=[('SRCS = main.c entry.S scalar.c w2.S fixture.S',
                    'SRCS = main.c entry.S scalar.c dot16.S paired16.S w2_np.S packed.S pack.c fixture.S'),
                   'PLACEHOLDER']
            edits[1]=('CFLAGS += -ffreestanding -fno-builtin -fno-fast-math -ffp-contract=off',
                      'CFLAGS += -ffreestanding -fno-builtin -fno-fast-math -ffp-contract=off -DSCREEN_K='+str(k))
            for before,after in edits:newmake=replace_exact(newmake,before,after)
            restored=newmake
            for before,after in reversed(edits):restored=restored.replace(after,before,1)
            need(restored==rawmake,'complete original Makefile inverse');(source/'Makefile').write_text(newmake);makefile_edits[k]=edits
            groups=k//32;sizes={'input':k,'input-scales':groups*4,'weight':288*k,'packed':288*k,
                'scales':288*groups*4,'gold':1152,'slot-gold':128,'expected-flags':4,'packed-scales':288*groups*4}
            kinds=('normal-0','normal-1','normal-2','fullmin') if k==288 else ('normal','edge')
            views={};casefixtures={}
            for kind in kinds:
                view=work/'images'/kind;folder=view/'fixture';folder.mkdir(parents=True);views[kind]=view
                oldfolder=fixtures/'cases'/kind/'fixture' if k==288 else w2/'images'/kind/'fixture'
                values={name:(oldfolder/(name+'.bin')).read_bytes() for name in sizes if name not in ('expected-flags','packed-scales')}
                values['expected-flags']=struct.pack('<I',host_flags[kind]) if k==288 else (oldfolder/'expected-flags.bin').read_bytes()
                values['packed-scales']=pack_scale_bytes(values['scales'],k)
                if k==288:need(values['packed-scales']==(oldfolder/'packed-scales.bin').read_bytes(),'independent exact extracted scale permutation')
                casefixtures[kind]={}
                for name,size in sizes.items():
                    need(len(values[name])==size,'complete selected fixture '+str(k)+'/'+kind+'/'+name)
                    path=folder/(name+'.bin');path.write_bytes(values[name]);casefixtures[kind][name+'.bin']=digest(path);generated[str(path)]=digest(path)
            default=kinds[0];asm=['.section .rodata.w2_fixture,"a"','.balign 64']
            for name in sizes:
                symbol='w2_'+name.replace('-','_');path=views[default]/'fixture'/(name+'.bin')
                asm += [f'.global {symbol}',f'{symbol}:',f'.incbin "{path}"',f'.global {symbol}_end',f'{symbol}_end:','.balign 64']
            (source/'fixture.S').write_text('\n'.join(asm)+'\n')
            for path in source.rglob('*'):
                if path.is_file():generated[str(path)]=digest(path)
            binary=work/'packed-screen'
            command('k'+str(k)+'-build',[tools['make'],'--trace','--output-sync=target','-C',source,'ARCH=riscv64-xs','MARCH=rv64gv',
                'CROSS_COMPILE='+tools['gcc'][:-3],'W2_OBJ_ROOT='+str(work/'objects'),'BINARY='+str(binary),'-o','am','-o','klib','-j1','image'],budget=180)
            command('k'+str(k)+'-metadata',[tools['readelf'],'-W','-h','-A','-l','-s','-r',str(binary)+'.elf'],budget=30)
            command('k'+str(k)+'-disassembly',[tools['objdump'],'-drwC',str(binary)+'.elf'],budget=30)
            kernels={}
            for name,record in gr['functions'].items():
                if name.startswith('q'+str(k)+'_'):
                    kernels[name]=(record['bytes'],record['sha256']);kernels[record['parent']]=(record['bytes'],record['parent_sha256'])
            need(len(kernels)==4,'four selected frozen whole function bodies')
            elf=model.ELF(Path(str(binary)+'.elf').read_bytes());raw=Path(str(binary)+'.bin').read_bytes()
            inspection=inspect(elf,raw,kernels,'q288_oracle' if k==288 else 'w2_scalar')
            offset,extent,_=elf.symbols['w2_control'];offset-=BASE
            need(extent==8 and raw[offset:offset+8]==struct.pack('<2I',0,1),'exact control ABI')
            dumps=[]
            for name,size,file in (('w2_report',512,'report.bin'),('w2_samples',512,'samples.bin'),('output',1184,'output.bin'),
                    ('slots',160,'slots.bin'),('packed_slots',160,'packed-slots.bin'),('prepared',sizes['packed-scales']+128,'prepared.bin')):
                address,length,_=elf.symbols[name];need(length==size,'whole guarded object '+name)
                need(address%64==0 if name=='prepared' else True,'prepared object alignment');dumps.append((file,address,size))
            ranges=[]
            for name,size in sizes.items():
                symbol='w2_'+name.replace('-','_');address=elf.symbols[symbol][0]
                need(elf.symbols[symbol+'_end'][0]-address==size and raw[address-BASE:address-BASE+size]==(views[default]/'fixture'/(name+'.bin')).read_bytes(),
                     'complete actual linked fixture '+name)
                dumps.append((name+'-after.bin',address,size));ranges.append((name,address-BASE,size))
            ordered=sorted((lo,lo+n) for _,lo,n in ranges)
            need(all(x[1]<=y[0] for x,y in zip(ordered,ordered[1:])) and all(not(lo<offset+8 and offset<hi) for lo,hi in ordered),
                 'disjoint exact fixture/control ranges')
            plan=work/'dump-plan.txt';plan.write_text(''.join(f'{name} {addr:x} {size}\n' for name,addr,size in dumps))
            records={}
            for kind,view in views.items():
                image=bytearray(raw)
                for name,lo,n in ranges:image[lo:lo+n]=(view/'fixture'/(name+'.bin')).read_bytes()
                (view/'real-w2.bin').write_bytes(image)
                record=dict(contract=CONTRACT,k=k,fixture_kind=kind,fixtures=casefixtures[kind],dump_plan=dumps,control_offset=offset,
                    golden_fnv=f"{fnv((view/'fixture/gold.bin').read_bytes()):016x}",
                    expected_flags=struct.unpack('<I',(view/'fixture/expected-flags.bin').read_bytes())[0])
                records[kind]=record;save(view/'record.json',record)
                for path in (view/'real-w2.bin',view/'record.json'):generated[str(path)]=digest(path)
            for path in (Path(str(binary)+'.elf'),Path(str(binary)+'.bin'),plan):generated[str(path)]=digest(path)
            static=dict(contract=CONTRACT,k=k,status='PACKED_WS_FOUR_ARM_STATIC_PASS_NOT_RUNTIME',inspection=inspection,
                records=records,fixture_ranges=ranges,source_identity={p:h for p,h in generated.items() if Path(p).is_relative_to(work)},
                reference=reference,reference_sha256=pins[reference],abi=ABI,target_emu_runs=0,performance_qualified=False)
            save(work/'static.json',static);generated[str(work/'static.json')]=digest(work/'static.json')
            validations={};caseplan=[('negative',default,True),(default,default,False),('replay',default,False)]+[(kind,kind,False) for kind in kinds[1:]]
            for label,kind,negative in caseplan:
                check();dest=work/'reference'/label;dest.mkdir(parents=True);view=views[kind];record=records[kind]
                image=bytearray((view/'real-w2.bin').read_bytes());image[offset:offset+8]=struct.pack('<2I',int(negative),0)
                (dest/'image.bin').write_bytes(image);image_sha=digest(dest/'image.bin')
                rec=command('k'+str(k)+'-'+label,[adapter/'reference-runner',reference,dest/'image.bin',dest,'builtin','100000000','180',plan,'1'],
                            cwd=dest,budget=210,expected=2 if negative else 0,guest=True)
                need(digest(dest/'image.bin')==image_sha,'selected image unchanged')
                actual=read(dest/'reference-result.json')
                need(actual['halt_pc'] in (inspection['failure_pcs'] if negative else [inspection['success_pc']])
                     and actual['pc']==actual['halt_pc']+4 and all(actual[x]==0 for x in ('mcause','mepc','mtval')),'actual intended trap without exception')
                checked=validate(view,dest,record,rec,negative)
                guard=struct.pack('<2Q',*[0x5a1d8c2976e340bf]*2);bigguard=guard*4
                need((dest/'packed-slots.bin').read_bytes()==guard+bytes([0xa5])*128+guard,'inactive final packed slots and all guards')
                need((dest/'prepared.bin').read_bytes()==bigguard+(view/'fixture/packed-scales.bin').read_bytes()+bigguard,
                     'all prepared scale bytes and 64-byte guards')
                final_regs=(dest/'final-registers.bin').read_bytes()
                need(struct.unpack_from('<Q',final_regs,ABI['fcsr'])[0]==record['expected_flags'],'complete final accrued FCSR')
                checked.update(contract=CONTRACT,k=k,fixture_kind=kind,
                    status='EXPECTED_PACKED_WS_REFERENCE_REJECTION' if negative else 'PACKED_WS_REFERENCE_PASS',
                    prepared_all_bytes=True,packed_slots_all_bytes=True,final_fcsr=record['expected_flags'])
                save(dest/'validation.json',checked);validations[label]=checked
                for path,h in {**pins,**snapshots,**generated}.items():need(digest(path)==h,'stable campaign input '+path)
                print(k,label,checked['status'],flush=True)
            need(validations[default]==validations['replay'],'exact independent full reference replay')
            campaigns[str(k)]=dict(inspection=inspection,static_sha256=digest(work/'static.json'),validations=validations)
        save(out/'derivation.json',dict(checker_edits=checkedits,makefile_edits=makefile_edits,complete_originals_reconstructed=True,
            core_main='New team-only fixed-geometry harness; original scalar files and frozen kernels copied byte-for-byte.'))
        check();need(time.monotonic()<deadline,'budget includes final audit')
        need(result['reference_runs']==10 and all(x['direct_child_reaped'] and x['process_group_absent_after_exit'] for x in result['commands']),
             'exact ten reference cases and all children reaped')
        result.update(status='PACKED_WS_EIGHT_WINDOWS_REFERENCE_PASS',reference_qualified=True,campaigns=campaigns,
            all_inputs_unchanged=True,all_children_reaped=True,generated_inputs=generated)
    except BaseException as exc:
        result.update(status='FAILED',error=repr(exc));raise
    finally:
        result['finished']=stamp();save(out/'result.json',result)
    print(json.dumps({k:result[k] for k in ('status','reference_runs','reference_qualified','target_emu_runs','performance_qualified','started','finished')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('narrow-build','w2-reference','gnu','q288-fixtures','adapter','hardware','reference-template','support-adapter-source','prior-reference','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,choices=[1],default=1)
    p.add_argument('--budget-seconds',type=int,default=1200)
    run(p.parse_args())
