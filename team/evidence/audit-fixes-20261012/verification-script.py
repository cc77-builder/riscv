from pathlib import Path
import hashlib, json, re, subprocess

root=Path(__file__).resolve().parents[2]
out=root/'team/out'
def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git',*args],cwd=root)
archive_count=0; historical={}
for sums in [*(root/'team/evidence').glob('*/archive.sha256'),*(root/'team/evidence').glob('*/SHA256SUMS')]:
    if sums.parent.name=='audit-fixes-20261012': continue
    count=0
    for line in sums.read_text().splitlines():
        h,name=line.split(maxsplit=1)
        require(digest(sums.parent/name.lstrip('*'))==h,f'Historical archive changed: {name}')
        count+=1
    historical[sums.parent.name]=count;archive_count+=count
for name in ('team/tests/data/vdot-directed.jsonl','team/patches/nemu/vdot-s8x8-r32-v0.1.patch','team/patches/nemu/manifest.json'):
    require((root/name).read_bytes()==git('show','7cd588a8f:'+name),'Contract fixture/patch changed: '+name)
old=git('show','7cd588a8f:team/spec/vdot.md').decode()
new=(root/'team/spec/vdot.md').read_text(encoding='utf-8')
def normative(s): return s[s.index('## 2.'):s.index('## 5.')]
require(normative(old)==normative(new),'Normative ISA sections2-4 changed')
diag=(out/'fix-diagnostic.log').read_text()
for field in ('pre_src1_128=0xa5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5','pre_src2_128=0x5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a',
              'actual_vd128=0x80000000000000000000000000000000','first_bad_reg=10 first_bad_byte=15 actual_byte=128 expected_byte=0'):
    require(field in diag,'Diagnostic field missing: '+field)
sequence={}
for name in ('fix-baseline-build','fix-baseline-virt'):
    dis=(out/name/'disassembly.txt').read_text()
    symbols={s:int(a,16) for a,s in re.findall(r'^([0-9a-f]+) <([^>]+)>:',dis,re.M)}
    instructions={int(a,16):(int(w,16),len(w)//2) for a,w in re.findall(r'^\s+([0-9a-f]+):\s+([0-9a-f]{4,8})\s',dis,re.M)}
    require(not any(size==4 and word&0x7f==0x0b for word,size in instructions.values()),'Baseline contains custom-0')
    names=[s[:-6] for s in symbols if re.fullmatch(r'baseline_[0-9a-f]{8}_begin',s)]
    require(len(names)>1000,'Too few compiled operand stubs')
    for s in names:
        begin,end=symbols[s+'_begin'],symbols[s+'_end']
        require(end-begin==52 and len([a for a in instructions if begin<=a<end])==13,'Wrong complete sequence: '+s)
        require(symbols[s+'_reduce']+4-symbols[s+'_multiply']==12,'Wrong arithmetic interval: '+s)
    sequence[name]=dict(compiled_stubs=len(names),core_instructions=13,arithmetic_instructions=3,no_custom0=True)
(out/'fix-sequence-check.json').write_text(json.dumps(sequence,sort_keys=True,indent=2)+'\n')
coverage={}
for folder,prefix,manifest in [('fix-baseline-run','BASELINE_CASE ','fix-baseline-data'),('fix-baseline-virt','BASELINE_CASE ','fix-baseline-virt-data'),('fix-vdot-run','VDOT_CASE ','fix-vdot-data')]:
    log=(out/folder/'run.log').read_text()
    rows=[dict(re.findall(r'(\w+)=([^\s]+)',line)) for line in log.splitlines() if line.startswith(prefix)]
    if prefix=='VDOT_CASE ': rows=[r for r in rows if not r['id'].startswith(('X','H','N'))]
    require(len(rows)==1304,f'{folder}: incorrect arithmetic count {len(rows)}')
    registers=set();tuples=set();vs={};layouts=set();cross=set()
    for row in rows:
        word=int(row['instruction'],16);t=(word>>7&31,word>>15&31,word>>20&31)
        registers.update(t);tuples.add(t)
        before=int(row['pre_mstatus'],16)>>9&3;after=int(row['raw_mstatus'],16)>>9&3
        require(before==int(row['requested_vs']) and after==3,'Incorrect VS transition')
        require(row['pre32_checked']=='1','Missing pre32 compare')
        vs[str(before)]=vs.get(str(before),0)+1
        csr=row['pre_csr'].split('/')
        cross.add((int(csr[0],16),int(csr[3],16),int(csr[4],16),before))
        if 'scratch_mask' in row: layouts.add(int(row['scratch_mask'],16))
    require(registers==set(range(32)) and len(tuples)==1147 and len(cross)==96,'Coverage dimensions missing')
    coverage[folder]=dict(executed=len(rows),registers=sorted(registers),operand_tuples=len(tuples),policy_csr_vs_cross=len(cross),pre_vs_histogram=vs,scratch_masks=len(layouts))
(out/'fix-runtime-coverage.json').write_text(json.dumps(coverage,sort_keys=True,indent=2)+'\n')
result=dict(historical_archives=historical,historical_files_verified=archive_count,fixture_and_patch_unchanged=True,normative_sections_2_4_unchanged=True,diagnostic_fields_checked=True,sequence=sequence,coverage=coverage)
(out/'fix-delivery-check.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
