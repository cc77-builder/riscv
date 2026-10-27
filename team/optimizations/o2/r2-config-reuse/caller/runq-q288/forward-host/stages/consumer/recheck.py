"""Recompute all consumer reference decisions from a byte-restored core archive."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import time
import types

HERE=Path(__file__).resolve().parent
REL=Path('team/optimizations/o2/r2-config-reuse/caller/runq-q288/forward-host/stages/consumer')
REPO=HERE.parents[8]
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def frozen_validator(root,campaign,build,entry):
    frozen=campaign/'runtime-source';pins=read(campaign/'runtime-inputs.json');source=frozen/REL/entry
    suffix='/'+(REL/entry).as_posix();keys=[k for k in pins if k.endswith(suffix)]
    need(len(keys)==1,'one original validator root');original=Path(keys[0][:-len(suffix)])
    for path in frozen.rglob('*'):
        if path.is_file():need(pins.get(str(original/path.relative_to(frozen)))==sha(path),'every captured source equals original runtime inventory')
    build_pin=sha(build/'result.json')
    need(sum(p.endswith('/result.json') and value==build_pin for p,value in pins.items())==1,'selected build belongs to actual campaign')
    # The legacy helper imports runtime_experiment by name. Remove prior
    # restored modules and search paths before selecting the next snapshot.
    for name,module in list(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if path and Path(path).resolve().is_relative_to(root):sys.modules.pop(name,None)
    sys.path[:]=[p for p in sys.path if not Path(p).resolve().is_relative_to(root)]
    validator=load('restored_'+campaign.name.replace('-','_'),source)
    observed=validator.REPO if hasattr(validator,'REPO') else validator.r.REPO
    need(observed==frozen,'validator imports resolve within this restored snapshot')
    pending=[validator];seen=set();closure={}
    while pending:
        module=pending.pop()
        if not isinstance(module,types.ModuleType) or id(module) in seen:continue
        seen.add(id(module));pending.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
        path=getattr(module,'__file__',None)
        if path:
            path=Path(path).resolve()
            if path.is_relative_to(root) or path.is_relative_to(REPO) or path.is_relative_to(original):
                need(path.is_relative_to(frozen),'no original-machine/current-tree/other-snapshot project import')
                rel=path.relative_to(frozen);value=sha(path);need(pins.get(str(original/rel))==value,'actual imported helper matches original campaign SHA');closure[str(rel)]=value
    return validator,pins,dict(entry_sha256=sha(source),actual_imported_source_sha256=closure)

def case_records(summary,labels):
    records=summary['records'];need(len(records)==len(labels) and {r['name'] for r in records}==set(labels),'exact original campaign case set')
    need(set(summary['validations'])==set(labels),'exact original validation set')
    pids=[r.get('pid') for r in records]
    need(all(type(p) is int and p>0 for p in pids) and len(pids)==len(set(pids)),'distinct actual reference process identities')
    return {r['name']:r for r in records}

def recheck(root,manifest_path,expected_manifest,output):
    need(not output.exists() and not output.is_relative_to(REPO) and not output.is_relative_to(root),'fresh isolated recheck output')
    need(sha(manifest_path)==expected_manifest,'exact published core manifest')
    manifest=read(manifest_path);need(manifest['format']=='sha256-object-zip-v1','known original archive format')
    rows=manifest['files'];names={x['path'] for x in rows}
    need(len(names)==len(rows)==manifest['file_count'],'unique full archive inventory')
    def verify_restored():
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        need(actual==names,'exact full restored file membership')
        for row in rows:
            p=root/row['path'];need(p.resolve().is_relative_to(root) and not p.is_symlink() and p.stat().st_size==row['size'] and sha(p)==row['sha256'],'every restored original byte')
    verify_restored();output.mkdir(parents=True);start=time.monotonic();results={};snapshots={};mapped=0
    # Execute only the already-used team validators captured by each actual
    # campaign. No source file, receipt, image or numerical input is rewritten.
    sys.dont_write_bytecode=True
    for campaign_name,build_name in (('reference-01','build-01'),('reference-02','build-02')):
        campaign=root/campaign_name;build=root/build_name;summary=read(campaign/'results.json');state=read(campaign/'state.json')
        need(summary['status']==state['status']=='PURE_FORWARD_REFERENCE_CAMPAIGN_PASS' and not state['active'] and not state.get('cleanup_unknown'),'closed original campaign')
        validator,pins,snapshots[campaign_name]=frozen_validator(root,campaign,build,'run.py')
        receipts=case_records(summary,[n for n,m,x in validator.CASES])
        wanted=summary['validations'];actual={}
        for label,method,negative in validator.CASES:
            case=campaign/label;receipt=read(case/'result.json')
            need(receipt==receipts[label] and receipt['method']==method and receipt['negative'] is negative,'same original case receipt and controls')
            need(sha(case/'validation.json')==receipt['validation_sha256'],'original validation receipt link')
            actual[label]=validator.validate(build,case,method,negative,receipt)
            need(actual[label]==read(case/'validation.json')==wanted[label],'recomputed complete original reference decision '+campaign_name+'/'+label)
            results[campaign_name+'/'+label]=actual[label]['status']
        need(actual['ta-cache']==actual['recovery']==actual['replay'],'complete independently replayed raw states and flags')
        need(all(actual[n]['flags']==actual['scalar']['flags'] for n in ('fr','ta','fr-cache','ta-cache')),'five method final flags')
    for campaign_name,build_name in (('api-reference-01','api-build-02'),('target-reference-01','target-build-02')):
        campaign=root/campaign_name;build=root/build_name;summary=read(campaign/'results.json');state=read(campaign/'state.json')
        need(summary['status']==state['status']=='SHARED_CONSUMER_AUX_REFERENCE_CAMPAIGN_PASS' and state['active_pid'] is None,'closed actual auxiliary campaign')
        validator,pins,snapshots[campaign_name]=frozen_validator(root,campaign,build,'aux_run.py')
        original=read(build/'result.json');qualified=Path(original['qualified_campaign'])
        need(qualified.name=='reference-02','expected original qualification source')
        for filename in ('results.json','state.json','runtime-inputs.json'):
            need(pins[str(qualified/filename)]==sha(root/'reference-02'/filename),'relocated reference qualification is byte-identical')
        # The validator reads flags from this one directory. Relocate only that
        # data lookup in a temporary in-memory dict; raw metadata stays intact.
        record=dict(original,qualified_campaign=str(root/'reference-02'));mapped+=1
        cases=[('api',None,False)] if original['kind']=='api' else [('negative',4,True),('fr',3,False),('ta',4,False),('replay',4,False)]
        receipts=case_records(summary,[n for n,m,x in cases])
        actual={}
        for label,method,negative in cases:
            case=campaign/label;receipt=read(case/'result.json')
            need(receipt==receipts[label] and receipt['method']==method and receipt['negative'] is negative,'same original auxiliary receipt and controls')
            need(sha(case/'validation.json')==receipt['validation_sha256'],'original auxiliary validation link')
            actual[label]=validator.validate(build,case,record,receipt,method,negative)
            need(actual[label]==read(case/'validation.json')==summary['validations'][label],'recomputed complete original auxiliary decision '+campaign_name+'/'+label)
            results[campaign_name+'/'+label]=actual[label]['status']
        if original['kind']=='target':need(actual['ta']==actual['replay'],'exact target-harness standalone reference replay')
    need(len(results)==21,'all twenty-one original actual reference cases rechecked');verify_restored()
    report=dict(status='RESTORED_CONSUMER_RAW_REFERENCE_RECHECK_PASS',cases=results,case_count=len(results),
        source_sha256=sha(HERE/'recheck.py'),manifest_sha256=expected_manifest,restored_file_count=len(rows),
        original_validator_snapshots=snapshots,qualified_campaign_data_path_relocations=mapped,
        elapsed_seconds=time.monotonic()-start,new_reference_runs=0,new_emu_runs=0,
        physical_runtime_identity_rechecked=False,
        complete_forward_difftest_qualified=False,performance_qualified=False)
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','manifest','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-manifest-sha256',required=True);a=p.parse_args()
    print(json.dumps(recheck(a.root.resolve(),a.manifest.resolve(),a.expected_manifest_sha256,a.output.resolve()),indent=2))
