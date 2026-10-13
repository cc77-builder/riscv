"""Audit exact corpus union and source-bound real DiffTest shard receipts."""
import argparse, collections, datetime, functools, gzip, hashlib, importlib.util, json, re, subprocess
from pathlib import Path


def require(value, message):
    if not value: raise ValueError(message)


def require_expected_identity(expected):
    """Caller-pinned inputs: agreement among receipts alone is insufficient."""
    require(isinstance(expected,dict), 'explicit expected source/runtime/plan identity required')
    for key,length in (('source',40),('parent_source',40),('emu',64),('reference',64),('flash',64),('plan',64)):
        value=expected.get(key)
        require(isinstance(value,str) and re.fullmatch(r'[0-9a-f]{'+str(length)+'}',value),
                f'invalid or missing expected {key} digest')
    require(type(expected.get('unique_cases')) is int and expected['unique_cases']>0,
            'positive expected unique-case count required')


def require_runtime_identity(source,runtime,expected):
    require_expected_identity(expected)
    require(source==expected['source'], 'receipt source differs from explicitly pinned tested source')
    require(tuple(runtime)==(expected['emu'],expected['reference'],expected['flash']),
            'runtime differs from explicitly pinned EMU/reference/flash')


def parse_status(text,expected_exit,field='exit_code'):
    lines=text.splitlines()
    values=[x.split('=',1)[1] for x in lines if x.startswith(field+'=')]
    require(values==[str(expected_exit)], 'missing, duplicate or contradictory driver exit status')
    times=[x.split('=',1)[1] for x in lines if x.startswith('finished_at=')]
    require(len(times)==1, 'missing or duplicate driver completion time')
    parsed=datetime.datetime.fromisoformat(times[0])
    require(parsed.tzinfo is not None, 'completion time lacks timezone')


def key_values(text):
    result={}
    for line in text.splitlines():
        if '=' not in line:continue
        k,v=line.split('=',1)
        require(k not in result, f'duplicate runtime parameter: {k}')
        result[k]=v
    return result


def full_sums(path):
    result={}
    for line in raw_log(path).decode().splitlines():
        value,name=line.split(None,1);name=name.strip()
        require(name not in result and re.fullmatch(r'[0-9a-f]{64}',value), 'invalid or duplicated full source digest')
        result[name]=value
    require(result,'empty checksum record')
    return result


@functools.lru_cache(maxsize=512)
def git_bytes(repo,revision,path):
    require(re.fullmatch(r'[0-9a-f]{40}',revision), 'source revision must be complete SHA')
    p=Path(path)
    require(not p.is_absolute() and '..' not in p.parts and ':' not in path, 'invalid repository source path')
    return subprocess.check_output(['git','-C',str(repo),'show',revision+':'+path],stderr=subprocess.PIPE)


def verified_repo_sources(repo,revision,records):
    require(records,'missing compiled workload source digests')
    rel={}
    for name,value in records.items():
        parts=name.split('/team/',1)
        require(len(parts)==2, 'workload source is not attributable to the team tree')
        path='team/'+parts[1]
        require(path not in rel, 'duplicate relative workload source')
        require(hashlib.sha256(git_bytes(str(repo),revision,path)).hexdigest()==value,
                'compiled source differs from tested Git revision: '+path)
        rel[path]=value
    return rel


def verify_driver_completion(out):
    parse_status((out/'status').read_text(),0)
    log=raw_log(out/'driver.log').decode();lines=log.splitlines()
    markers=[i for i,x in enumerate(lines) if x=='SHARD_FULLCORE_PASS']
    actions=[i for i,x in enumerate(lines) if x.startswith('VDOT_ACTION_DONE action=run-rtl ')]
    verdict=[]
    for i,line in enumerate(lines):
        if line.startswith('{'):
            try:obj=json.loads(line)
            except json.JSONDecodeError:continue
            if obj.get('status')=='VDOT_WORKLOAD_PASS':
                require(obj.get('difftest') is True and obj.get('extension_pass') is True,
                        'driver lacks actual full-core checker verdict')
                verdict.append(i)
    require(len(markers)==len(actions)==len(verdict)==1 and verdict[0]<actions[0]<markers[0],
            'driver has no unique ordered checker/action/completion evidence')


def verify_provenance_chain(repo,runs,index,folder,expected):
    out=runs/f'run-{index}';ev=out/'evidence';build=runs/f'build-{index}'
    load=lambda p:json.loads(raw_log(p).decode())
    actual=load(ev/'build-verification.json');captured=load(build/'workload-provenance.json')
    require(actual==captured,'run workload provenance differs from captured build provenance')
    require(actual.get('schema_version')==1 and actual.get('kind')=='vdot' and
            actual.get('arch')=='riscv64-xs' and actual.get('mode')=='full','wrong workload role')
    require(actual.get('am_rev')=='086a238062fdfb3281b745a537b361983d0154b5','wrong pinned AM revision')
    require(actual.get('am_libraries_sha256') and actual.get('am_source_sha256'),'missing AM compilation provenance')
    params=key_values((ev/'runtime-parameters.txt').read_text())
    require(params.get('platform')=='rtl' and params.get('mode')=='full','runtime not a full RTL execution')
    require(params.get('data')==actual['data_dir'],'run data path differs from compiled input')
    image=params.get('image');images=actual['images_sha256']
    require(image in images and images==full_sums(build/'workload.sha256'),'runtime image is not the checked build')
    require(Path(image).name=='vdot-exceptions.bin','unexpected workload image role')
    for name,value in actual['inputs_sha256'].items():
        require(Path(name).parent.as_posix()==actual['data_dir'],'compiled corpus has external input')
        require(sha(folder/Path(name).name)==value,'archived corpus differs from compiled input')
    require(actual['inputs_sha256']==full_sums(ev/'inputs.sha256'),'run and build corpus digest sets differ')
    sources=full_sums(ev/'source.sha256')
    require(sources==actual['source_sha256'],'run/build workload source sets differ')
    verified_repo_sources(repo,expected['source'],sources)
    require(not (ev/'working-tree.txt').read_text().strip(),'tested team source was dirty')
    for name in ('input-verification.txt','image-verification.txt'):
        lines=(ev/name).read_text().splitlines()
        require(lines and all(x.endswith(': OK') for x in lines),'input/image byte verification did not complete')
    runtime=full_sums(ev/'runtime.sha256')
    for key,pin in (('binary','emu'),('reference','reference'),('flash','flash')):
        require(runtime.get(params.get(key))==expected[pin],'actual runtime differs from explicit path/digest pin')
    nr=load(ev/'nemu-verification.json')
    manifest=json.loads(git_bytes(str(repo),expected['source'],'team/patches/nemu/manifest.json'))
    require(nr.get('schema_version')==2 and nr.get('build_mode')=='reference','wrong NEMU role/schema')
    require(nr.get('binary_sha256')==expected['reference'],'NEMU provenance not bound to loaded reference')
    for key in ('base_rev','patch_version','patch_sha256','contract_id','platform_profile','patched_source_sha256'):
        require(nr.get(key)==manifest[key], 'NEMU provenance differs from candidate patch: '+key)
    require((ev/'nemu.sha').read_text().strip()==manifest['base_rev'],'NEMU baseline revision differs')
    config=(ev/'nemu.config').read_bytes()
    require(hashlib.sha256(config).hexdigest()==nr['config_sha256'],'NEMU configuration digest mismatch')
    cfg=config.decode().splitlines()
    for key in ('SHARE','RVV','CUSTOM_VDOT','CUSTOM_VDOT_XS_TVAL','TVAL_EX_II','NMIE_INIT'):
        entries=[x for x in cfg if x.startswith('CONFIG_'+key+'=') or x=='# CONFIG_'+key+' is not set']
        require(entries==['CONFIG_'+key+'=y'],'required NEMU feature missing/contradictory: '+key)
    require('# CONFIG_MDT_INIT is not set' in cfg and 'CONFIG_MDT_INIT=y' not in cfg,'wrong target reset policy')
    for name,value in manifest['patched_source_sha256'].items():
        require(nr['source_sha256'].get(name)==value,'NEMU source snapshot differs from checked patch')
    allowed=set(manifest['patched_source_sha256'])
    for line in (ev/'nemu-working-tree.txt').read_text().splitlines():
        require(line[3:] in allowed,'unexplained dirty NEMU source')
    return dict(image_sha256=images[image],config_sha256=nr['config_sha256'],patch_sha256=nr['patch_sha256'])


def raw_log(path):
    path=Path(path)
    if path.exists():return path.read_bytes()
    packed=path.with_suffix(path.suffix+'.gz')
    with gzip.open(packed,'rb') as stream:return stream.read()


def sha(path):
    path=Path(path)
    return hashlib.sha256(path.read_bytes() if path.exists() else raw_log(path)).hexdigest()


def load_data(folder):
    m=json.loads((folder/'manifest.json').read_text())
    raw=(folder/'cases.jsonl').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==m['cases_sha256'],'case corpus checksum mismatch')
    for name,wanted in m['artifacts_sha256'].items():
        require(Path(name).name==name,'nonlocal artifact path')
        require(sha(folder/name)==wanted,f'artifact checksum mismatch: {folder/name}')
    legal=[json.loads(x) for x in raw.splitlines()][:m['smoke_count']]
    exceptions=json.loads((folder/'exceptions.json').read_text())
    require(len(legal)==m['smoke_count'] and len(exceptions)==m['exception_count'],'corpus count mismatch')
    require(len({x['id'] for x in legal+exceptions})==len(legal)+len(exceptions),'duplicate corpus case ID')
    return m,legal,exceptions


def sums(path):
    records={}
    for line in path.read_text().splitlines():
        digest,name=line.split(None,1);name=name.strip()
        key=Path(name).name
        require(key not in records,'ambiguous runtime basename')
        records[key]=digest
    return records


def validate(parent_data, runs, repo, plan_only=False, *, expected=None):
    if not plan_only: require_expected_identity(expected)
    parent,legal,exceptions=load_data(parent_data)
    if not plan_only:
        for name,value in parent['source_sha256'].items():
            require(hashlib.sha256(git_bytes(str(repo),expected['parent_source'],'team/tests/'+name)).hexdigest()==value,
                    'mother-corpus generator/model differs from pinned parent source')
    wanted={x['id']:x for x in legal+exceptions}
    require(legal and legal[0]['id']=='D00','parent must start with legal D00')
    plan=hashlib.sha256(json.dumps(dict(legal=legal,exceptions=exceptions),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    folders=sorted(p for p in runs.glob('data-*') if p.is_dir())
    require(folders,'missing shard folders')
    counts=collections.Counter(); indices=set(); plans=[]; common_source=None
    for folder in folders:
        m,cases,bad=load_data(folder);shard=m['shard'];i=shard['index'];n=shard['count']
        require(type(i) is int and type(n) is int and 0<=i<n,'invalid shard index/count')
        require(i not in indices,'duplicate shard index');indices.add(i)
        require(folder.name==f'data-{i}','directory/index disagreement')
        require(shard['parent_plan_sha256']==plan,'different parent plan')
        require(shard['parent_legal_count']==len(legal) and shard['parent_exception_count']==len(exceptions),'parent count mismatch')
        require(shard['legal_control']=='D00' and cases[0]==legal[0],'missing identical leading legal control')
        expected_legal=[legal[0]]+[x for position,x in enumerate(legal) if position%n==i and x['id']!='D00']
        expected_bad=[x for position,x in enumerate(exceptions) if position%n==i]
        require(cases==expected_legal and bad==expected_bad,'partition inputs/order/expectations changed')
        for item in cases+bad:
            require(item==wanted.get(item['id']),'changed test expectation');counts[item['id']]+=1
        source=(m['contract_id'],m['model_version'],m['generator_version'],m['seed'],m['coverage_profile'],json.dumps(m['source_sha256'],sort_keys=True))
        if common_source is None: common_source=source
        require(source==common_source,'mixed shard generator/model/source configuration')
        if not plan_only:
            for name,value in m['source_sha256'].items():
                require(hashlib.sha256(git_bytes(str(repo),expected['source'],'team/tests/'+name)).hexdigest()==value,
                        'shard generator/model differs from tested candidate')
        plans.append((i,n,folder,len(cases),len(bad)))
    if not plan_only:
        require(plan==expected['plan'], 'parent plan differs from explicitly pinned corpus')
        require(len(wanted)==expected['unique_cases'], 'unique-case count differs from explicitly pinned corpus')
    n=plans[0][1]
    require(all(x[1]==n for x in plans) and indices==set(range(n)),'missing/inconsistent shards')
    require(set(counts)==set(wanted),'union omits/adds cases')
    require(counts['D00']==n and all(v==1 for key,v in counts.items() if key!='D00'),'duplicate/missing noncontrol cases')
    result=dict(status='INPUT_PARTITION_VERIFIED_NOT_EXECUTION' if plan_only else 'FULLCORE_VDOT_SHARDED_PASS',
                extension_pass=not plan_only,unique_cases=len(wanted),unique_legal=len(legal),unique_exceptions=len(exceptions),
                shards=n,executed_extension_records=sum(counts.values()),duplicate_legal_controls=n-1,
                parent_plan_sha256=plan,parent_manifest_sha256=sha(parent_data/'manifest.json'))
    if plan_only:return result
    spec=importlib.util.spec_from_file_location('per_shard_check',repo/'team/scripts/check-vdot-run.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    results=[];actual=[];runtime_identity=None
    for i,_,folder,lc,ec in sorted(plans):
        out=runs/f'run-{i}';ev=out/'evidence'
        status=(out/'status').read_text()
        verify_driver_completion(out)
        rc=int((ev/'exit-code.txt').read_text());log=raw_log(ev/'run.log').decode('utf-8',errors='strict')
        verdict=checker.validate(log,'full',rc,folder,require_diff=True)
        require(verdict['executed']==lc+ec,'executed count differs from shard')
        provenance=verify_provenance_chain(repo,runs,i,folder,expected)
        runtime=sums(ev/'runtime.sha256')
        identity=tuple(runtime.get(key) for key in ('emu','riscv64-nemu-interpreter-so','boot-flash.bin'))
        require(all(identity),'required runtime digests missing')
        tested_source=(ev/'team.sha').read_text().strip()
        require_runtime_identity(tested_source,identity,expected)
        if runtime_identity is None:runtime_identity=identity
        require(identity==runtime_identity,'mixed EMU/reference/flash among shards')
        expanded=checker.expand_packed_records(re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',log))
        scope=expanded.split('VDOT_EXTENSION_BEGIN',1)[1]
        actual.extend(checker.fields(line) for line in scope.splitlines() if line.startswith('VDOT_CASE '))
        results.append(dict(index=i,legal=lc,exceptions=ec,status=verdict,provenance=provenance,exit_code=rc,
                            source_sha=tested_source,driver_status=status,
                            log_sha256=sha(ev/'run.log'),raw_log=str(ev/'run.log')))
    require(len({x['source_sha'] for x in results})==1,'mixed source snapshots in receipts')
    require(collections.Counter(x['id'] for x in actual)==counts,'executed union differs from planned union')
    neg=runs/'negative-0';nr=json.loads((neg/'result.json').read_text())
    normal_reference=json.loads(raw_log(runs/'run-0/evidence/nemu-verification.json'))
    negative_reference=json.loads(raw_log(neg/'reference-verification.json'))
    require(normal_reference==negative_reference,'negative/normal base-reference provenance differs')
    normal_build=json.loads(raw_log(runs/'build-0/workload-provenance.json'))
    negative_build=json.loads(raw_log(neg/'image-verification.json'))
    require(normal_build==negative_build,'negative/normal actual workload provenance differs')
    require(nr['status']=='EXPECTED_DIFFERENTIAL_REJECTION' and nr['bit']==100 and nr['negative_exit']==1,'negative verdict not accepted')
    require(int(nr['instruction'],16)&0xfe00707f==0x0200000b,'negative injection is not vdot')
    parse_status((neg/'status').read_text(),1)
    ns=sums(neg/'inputs.sha256')
    build=runs/'build-0'
    normal_image=sums(build/'workload.sha256').get('vdot-exceptions.bin')
    require(normal_image and normal_image==ns['vdot-exceptions.bin'],'negative/normal image digest mismatch')
    require(results[0]['provenance']['image_sha256']==normal_image,'negative/normal actual image mismatch')
    if (build/'vdot-exceptions.bin').exists():
        require(sha(build/'vdot-exceptions.bin')==normal_image,'normal image bytes do not match captured build digest')
    require(ns.get('emu')==runtime_identity[0] and ns.get('riscv64-nemu-interpreter-so')==runtime_identity[1],'negative base runtime mismatch')
    require(ns.get('boot-flash.bin')==runtime_identity[2], 'negative/normal boot flash mismatch')
    nlog=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',raw_log(neg/'run.log').decode('utf-8',errors='strict'))
    hits=re.findall(r'DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=(\d+) pc=(0x[0-9a-f]+) instruction=(0x[0-9a-f]+)',nlog)
    require(len(hits)==1,'missing/duplicate real injection event')
    vd,pc,word=hits[0];require(int(word,16)&0xfe00707f==0x0200000b,'raw negative event is not vdot')
    require(nr.get('vd')==int(vd) and nr.get('pc')==pc and nr.get('instruction')==word, 'negative summary disagrees with its raw event')
    require(((int(word,16)>>7)&31)==int(vd), 'negative destination disagrees with instruction encoding')
    mismatch=re.search(r'v(\d+)_high different at pc = (0x[0-9a-f]+), right=\s*(0x[0-9a-f]+), wrong =\s*(0x[0-9a-f]+)',nlog)
    require(mismatch and int(mismatch[1])==int(vd),'missing matching real vector-high mismatch')
    require(int(mismatch[2],16)==int(pc,16), 'negative mismatch PC differs from the injected instruction PC')
    require(int(mismatch[3],16)^int(mismatch[4],16)==1<<36,'negative difference not precisely bit100')
    require('Difftest enabled' in nlog and 'ABORT' in nlog,'missing negative full-core differential failure')
    result.update(expected_identity=expected,runs=results,runtime_sha256=dict(zip(('emu','nemu_reference','boot_flash'),runtime_identity)),
                  negative_control=dict(nr,same_image_normal_control='PASS shard-0'),same_image_normal_restore='PASS shard-0',completed_selftests=7*n,
                  completed_harness_negative_controls=3*n,covered_ids=sorted(wanted),
                  scope='fixed v0.1 legal/precise-exception corpus; not complete speculative/control coverage or PPA')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-data',type=Path,required=True);parser.add_argument('--runs',type=Path,required=True)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--plan-only',action='store_true');parser.add_argument('--output',type=Path)
    parser.add_argument('--expected-source')
    parser.add_argument('--expected-parent-source')
    parser.add_argument('--expected-emu')
    parser.add_argument('--expected-reference')
    parser.add_argument('--expected-flash')
    parser.add_argument('--expected-plan')
    parser.add_argument('--expected-unique-cases',type=int)
    a=parser.parse_args()
    try:
        expected=dict(source=a.expected_source,parent_source=a.expected_parent_source,emu=a.expected_emu,reference=a.expected_reference,
                      flash=a.expected_flash,plan=a.expected_plan,unique_cases=a.expected_unique_cases)
        report=validate(a.parent_data,a.runs,a.repo,a.plan_only,expected=expected);text=json.dumps(report,indent=2)+'\n'
        if a.output:
            with a.output.open('x') as f:f.write(text)
        print(text)
    except (ValueError,KeyError,FileNotFoundError) as error:raise SystemExit(f'VDOT_SHARDS_REJECTED: {error}')
