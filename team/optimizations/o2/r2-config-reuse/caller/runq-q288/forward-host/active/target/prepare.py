"""Freeze two actual active-consumer captures and independent quantizer probes."""
from pathlib import Path
import argparse,ctypes,hashlib,importlib.util,json,shutil,struct,sys,zipfile
HERE=Path(__file__).resolve().parent
Q=HERE.parents[2]
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
active=load('qkv_prepare_active',HERE.parent/'check.py')
def words(values):return struct.pack('<'+str(len(values))+'I',*values)

def crafted():
    half=[]
    for middle in (0x3f000000,0x3fc00000,0x40200000,0x42fd0000):
        for value in (middle-1,middle,middle+1):half.extend((value,value|0x80000000))
    half += [0x42fe0000,0xc2fe0000,0,0x80000000,1,0x80000001,0x3f800000,0xbf800000]
    small=[(i*8+1)|(0x80000000 if i%2 else 0) for i in range(30)]+[127,0x8000007f]
    small=[(v&0x80000000)|min(v&0x7fffffff,127) for v in small]
    under=[0x437e0000,0xc37e0000,1,0x80000001]+[0]*28
    edge=[0x00800000,0x80800000,0x007fffff,0x807fffff,1,0x80000001]+[0]*26
    unit=[0x3f800000,0xbf800000,0x3dcccccd,0xbdcccccd,0x3effffff,0xbeffffff]+[0]*26
    large=[0x7f7fffff,0xff7fffff,0x3f800000,0xbf800000,1,0x80000001]+[0]*26
    second=[254,0x800000fe,128,0x80000080,2,0x80000002]+[0]*26
    groups=[half,small,under,edge,unit,large,second,list(reversed(half)),list(reversed(unit))]
    need(all(len(g)==32 for g in groups),'nine exact crafted groups')
    return words([v for group in groups for v in group])

def prepare(repo,capture,out):
    need(HERE==(repo/active.Q/'forward-host/active/target').resolve(),'matching target source checkout')
    need(not out.exists() and not out.is_relative_to(repo),'new output outside source')
    out.mkdir(parents=True)
    parent=json.loads((capture/'result.json').read_text())
    need(parent['status']=='ACTIVE_FORWARD_AND_PROPAGATION_CONTROLS_PASS' and
         parent['source_files']==active.source_identity(repo),'closed active source and run identity')
    normal=capture/'normal';files={};origins={}
    journal_raw=(normal/'callbacks.jsonl').read_bytes()
    journal=[json.loads(line) for line in journal_raw.splitlines()]
    callbacks={(r['method'],r['position'],r['matrix']):r for r in journal}
    need(len(callbacks)==len(journal)==144,'complete unique positive callback journal')
    def get(name):
        raw=(normal/name).read_bytes()
        size=(82944 if name.startswith(('weight-','packed-')) else 10368 if name.startswith('scale-')
              else 324 if name.endswith('-input.bin') else 1152)
        need(len(raw)==size,'complete captured buffer '+name)
        origins[name]=sha(raw);return raw
    for m in range(3):
        for stem in ('weight','scale','packed'):files[f'{stem}-{m}.bin']=get(f'{stem}-{m:02}.bin')
    for d in range(2):
        fp=get(f'm0-p{d}-l0-qkv-fp32.bin')
        need(fp==get(f'm1-p{d}-l0-qkv-fp32.bin'),'TA and FR own FP32 input identity')
        files[f'fp-{d}.bin']=fp
        quant=get(f'm0-p{d}-q00-input.bin')
        for m in range(3):
            for method in range(2):
                need(quant==get(f'm{method}-p{d}-q{m:02}-input.bin'),'shared complete actual QKV quantization')
                record=callbacks[method,d,m]
                actual=dict(weight=sha(files[f'weight-{m}.bin']),packed=sha(files[f'packed-{m}.bin']),
                    weight_scale=sha(files[f'scale-{m}.bin']),x=sha(quant[:288]),xs=sha(quant[288:]))
                need(record['input_sha256']==actual,'selected capture matches actual ELF callback input journal')
                need(record['output_sha256']==sha(get(f'm{method}-p{d}-q{m:02}-output.bin')),
                     'selected capture matches actual ELF callback output journal')
            result=get(f'm0-p{d}-q{m:02}-output.bin')
            need(result==get(f'm1-p{d}-q{m:02}-output.bin'),
                 'TA/FR complete projection identity within accepted active forward')
            files[f'y-{d}-{m}.bin']=result
        files[f'quant-{d}.bin']=quant
    files['fp-2.bin']=crafted()
    compiler=shutil.which('gcc');need(compiler,'host compiler')
    library=out/'quantize-oracle.so'
    flags=['-std=gnu11','-O2','-fPIC','-shared','-ffp-contract=off','-fno-fast-math',
           '-fexcess-precision=standard','-fno-tree-vectorize','-fno-tree-slp-vectorize',
           '-fno-inline','-fno-lto','-Wl,--build-id=none,-Bsymbolic']
    command=active.command([compiler,*flags,HERE/'oracle.c','-lm','-o',library],out,'compile-oracle',timeout=120)
    c=ctypes.CDLL(str(library));c.qkv_reference_quantize.argtypes=[ctypes.c_void_p]*3;c.qkv_reference_quantize.restype=ctypes.c_int
    def quantize(raw):
        need(len(raw)==1152,'exact FP32 input extent before native oracle')
        input=ctypes.create_string_buffer(raw);x=ctypes.create_string_buffer(288);xs=ctypes.create_string_buffer(36)
        status=c.qkv_reference_quantize(input,x,xs)
        need(input.raw[:1152]==raw,'host oracle input readonly')
        return status,x.raw+xs.raw
    for d in range(3):
        status,quant=quantize(files[f'fp-{d}.bin']);need(status==0,'defined complete quantizer fixture')
        if d<2:need(quant==files[f'quant-{d}.bin'],'original quantize matches active capture')
        else:files['quant-2.bin']=quant
    probe=files['quant-2.bin'];need(struct.unpack_from('<I',probe,288+4)[0]==1,'host retains subnormal scale')
    expected=[]
    for n in (0,1,2,126):
        for v in (n,n+1,n+1):expected.extend((v,-v))
    need(probe[:24]==bytes(v&255 for v in expected),'all half-neighbor ties-away witnesses')
    rejected=[]
    for label,group,wanted in (('zero',[0]*32,3),('nan',[0x7fc00001]+[0]*31,2),
          ('infinity',[0x7f800000]+[0]*31,2),('underflowed-scale',[63]+[0]*31,4),
          ('finite-positive-scale-outside-int8',[128]+[0]*31,5)):
        raw=words(group)+files['fp-2.bin'][128:]
        status,_=quantize(raw);need(status==wanted,'specific invalid-domain rejection '+label)
        files['rejected-'+label+'.bin']=raw;rejected.append(dict(label=label,status=status))
    _,_,helpers=active.support(repo)
    s8=lambda raw:list(struct.unpack('<'+str(len(raw))+'b',raw))
    u32=lambda raw:list(struct.unpack('<'+str(len(raw)//4)+'I',raw))
    for m in range(3):
        weight=s8(files[f'weight-{m}.bin']);packed=s8(files[f'packed-{m}.bin'])
        need(packed==[weight[(8*t+r)*288+32*g+k] for t in range(36) for g in range(9) for r in range(8) for k in range(32)],
             'complete persistent packed weight identity')
        f=dict(weight=weight,packed=packed,weight_scale=u32(files[f'scale-{m}.bin']),
               inputs=[s8(files[f'quant-{d}.bin'][:288]) for d in range(2)],
               input_scale=[u32(files[f'quant-{d}.bin'][288:]) for d in range(2)])
        for d in range(2):need(words(helpers.python_golden(f,d))==files[f'y-{d}-{m}.bin'],'independent full projection golden')
    metadata=dict(status='ACTUAL_CONSUMER_QKV_INPUT_AND_QUANTIZER_ORACLE_PASS',layer=0,
        measured_position=0,functional_position=1,tokens=[1,7],trained=False,active_result_sha256=sha((capture/'result.json').read_bytes()),
        active_source_files=parent['source_files'],original_capture_files=origins,
        callback_journal_sha256=sha(journal_raw),selected_callback_records=12,
        fp32_provenance='team_quantize capture; original quantize matches journal-bound q/scales; separately frozen here',
        members={n:dict(bytes=len(raw),sha256=sha(raw)) for n,raw in sorted(files.items())},
        invalid_domain_controls=rejected,host_subnormal_scale_verified=True,host_command=command,
        host_library_sha256=sha(library.read_bytes()),upstream_sha256=active.UPSTREAM_SHA)
    files['metadata.json']=(json.dumps(metadata,indent=2)+'\n').encode()
    archive=out/'fixture.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
    active.save(out/'result.json',dict(metadata,fixture_sha256=sha(archive.read_bytes())))
    return dict(status=metadata['status'],fixture_sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.repo.resolve(),a.capture.resolve(),a.output.resolve()),indent=2))
