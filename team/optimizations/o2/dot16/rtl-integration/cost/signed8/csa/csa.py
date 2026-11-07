#!/usr/bin/env python3
"""Continue one fixed, closed CSA generation with the previously unrun FU/cost stages."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
CONTRACT = 'dot16-fused-signed8-csa-continuation-v4'
PREVIOUS_PINS = {
    'result.json': '84b752a19a62d6e436d347cdd1273110c6530bd6024c41eecd58fbd8574e450d',
    'inputs.json': '612f760a4d593a1899e7079c98a4fde5b2d14e702435cb09ffc1425e5f981616',
    'overlay-classes.json': 'd76cd45beda440ecc8fdc64ced5dc796e19c1e8641d7ebd7e8e12c8e401e242a',
    'classpath-before.json': 'd9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902',
    'arithmetic-structure.json': '9483d70f24876e7c89281e559d3d062355c0787e38a7f3fd7ab9cf36d3cd8ad6',
    'actual-csa-independent-miter.log': 'a9175ff5e52888f37d8cf8eeeb1673f6975e32cc8e08687be91f3db2cc845b2b',
    'prove.ys': 'a530cc27b2bd446913d16d3e3b673350224839c53645a5495331cf8ee0b9ccb1',
    'gate.sv': 'fced35a0f4d64fdd036d670246d29ea84124ebeca8a0062fbd01ae0e173082f5',
    'gold.sv': '5a8c5a6f316ba97295751d4a356c4397df8b4dbb9872dd8a4fe15c59a2c7a198',
    'source-snapshot/csa.py': '07d93e73072304a64b7bc415820b2856a27b2d74a01e649a2e141f78e8adf0f7',
    'source-snapshot/CSA_CONTRACT.md': '06a524756a6555934cf79a8c65e60490e32c21b256d62265a8c8676390049862',
}
PREVIOUS_LABELS = ['compile-source-overlay', 'generate-cost-0', 'generate-fu-0',
                   'generate-cost-1', 'generate-fu-1', 'actual-csa-structure',
                   'actual-csa-independent-miter']
RWIDTH_BASELINE_SHA = 'f42f7285ff8a357877c546d433251b1dc8c8eef66ee9218c9e3b2c002ca0a261'
RWIDTH_WRAPPER_SHA = '70dcc27381d3e7226eeff333c943d35b982ec1fdd37b75b680060a13aaf94e2a'
RWIDTH_DATAPATH_SHA = '50522c0cd2700f7f852872049533bc31f79ce811ad2ed53da2c1d333cece45e2'
VERIFY_SHA = 'e6924e406792fe9e2b82f27be5a591b37466fb7b3ee23ec93935698934e397de'
WRAPPER_SHA = '4a525d2e8ead5cc10a193d9724342162af4ffebd130c58ad7c606093849ac1c8'
ORIGINAL_WRAPPER_SHA = '63911b937a526b97ddaa67e34526fd19bbd2fa2801eadfda10ae6c2fa4b9fe9e'
REL_WRAPPER = 'src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala'
BASELINE_SHA = '19f90c867022ba2259b83fb2600bb56ef7066eda54023cead03c6e35bf23b7d7'
GEN_SHA = '7b45921ee1b5ff564113daa61403c4e52ecb598305aad6c093f4ab5768fe0a09'
GEN_INPUTS_SHA = 'ec29dc8725cf3a1c04ea684e2753debc1a9b2a04d37b4adadcdfe96f85ec20d8'
CP_SHA = 'd9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902'
COST_SHA = '8c9a22771594565bfaa812309f68c84de4e8a213b02b9aba03440373f61e2e51'
SOURCE_SHA = '62ace0342070bc2a40f57b999c8aa94d376543a4cc79d455cf69e6083742488c'
ORIGINAL_SOURCE_SHA = '161df70403fd131a3adf445230ed637dc7ad7c619d05c0a890aa8aa1791546d8'
REL_SOURCE = 'src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala'
HELPERS = {
    'process_helper.py':('team/optimizations/o2/dot16/rtl-integration/run_fu.py','db8fc437041c9b3580126ef8498085212313510ce96eb483f21a8c04e17479b3'),
    'classpath_helper.py':('team/optimizations/o2/dot16/rtl-integration/decode/run.py','0214e9a220b905156c9818342832a9226e3b7bfcce2a8f5340f0b659f7c68b7c'),
    'cost_helpers.py':('team/optimizations/o2/dot16/cost_helpers.py','bee29ddcfb0b1b6281dd8e05637bd9a032587a7b5ec18abaf85e08dda26be209'),
    'check_negative_fu.py':('team/optimizations/o2/check_negative_fu.py','edbf473f3bb61a3b834dd16d994b5f92090582d5a7761cee6fecff7fed2511be'),
}
CPP = {0:('flag0-02','6ecc823cfcca3b338ebde376c995a2da996282ce459f3a15ff7fea144bf0265c'),
       1:('flag1-01','0c6914a6d896dcb7e0c38c6ac826c295adc78d4655bfc9d043feec56c9c2dbbb')}
VECTORS_SHA = '901a7be30e62b81bcd3df55b20538a5ba9c879ba9c7c34f28b8c0421d8e6a327'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data,indent=2)+'\n')


def module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    sys.modules[name]=obj
    spec.loader.exec_module(obj)
    return obj



def wrapper_binding(text, previous, feature):
    compact=lambda value: re.sub(r'\s+','',value)
    instances={name:body for name,body in re.findall(r'\bVDotCarrySaveRows\s+(\w+)\s*\((.*?)\);',text,re.S)}
    expected={'products','highProducts'} if feature else {'products'}
    need(set(instances)==expected,'actual one/two CSA instances')
    for name,body in instances.items():
        pairs=re.findall(r'\.(\w+)\s*\(([^()]*)\)',body)
        rest=re.sub(r'\.(\w+)\s*\(([^()]*)\)','',body)
        need(not rest.replace(',','').strip() and len(pairs)==4 and len(dict(pairs))==4,
             'closed four CSA instance ports')
        ports={k:compact(v) for k,v in pairs}
        high=name=='highProducts'; hi,lo=(127,64) if high else (63,0)
        need(ports=={'vs1':f'io_in_bits_data_src_0[{hi}:{lo}]',
                     'vs2':f'io_in_bits_data_src_1[{hi}:{lo}]',
                     'row0':f'_{name}_row0','row1':f'_{name}_row1'},'exact input halves and output wires')
    pnames=[f'pRows_{half}_{row}' for half in range(2 if feature else 1) for row in range(2)]
    declarations=re.findall(r'\breg\s+\[(\d+):0\]\s+(pRows_\d+_\d+)\s*;',text)
    need(declarations==[('18',name) for name in pnames],'actual complete 19-bit P rows')
    updates=re.findall(r'(?m)^\s*(\w+)\s*<=\s*(.*?);',text,re.S)
    previous_updates=re.findall(r'(?m)^\s*(\w+)\s*<=\s*(.*?);',previous,re.S)
    data=lambda name: name.startswith('pRows_') or name.startswith('pProducts_') or name=='rPacket_res_data'
    need([(n,compact(e)) for n,e in updates if not data(n)]==
         [(n,compact(e)) for n,e in previous_updates if not data(n)],
         'all actual non-data sequential assignments unchanged')
    for half in range(2 if feature else 1):
        for row in range(2):
            name=f'pRows_{half}_{row}'; expressions=[compact(e) for n,e in updates if n==name]
            expected=f'isDot16?_highProducts_row{row}:19\'h0' if half else f'_products_row{row}'
            need(expressions==[expected],'exact P capture and dot8 zero encoding')
    output=re.search(r'\bassign\s+io_out_bits_res_data\s*=\s*(.*?);',text,re.S)
    previous_output=re.search(r'\bassign\s+io_out_bits_res_data\s*=\s*(.*?);',previous,re.S)
    need(output and previous_output and compact(output[1])==compact(previous_output[1]),
         'unchanged architectural output sign extension')
    # The source inverse binds unchanged accept/move conditions. Match the whole
    # emitted R expression to the independently reviewed fixed-width decode.
    expressions=[dict(name=n,expression=e) for n,e in updates if n=='rPacket_res_data']
    need(len(expressions)==1,'single actual R data write')
    expected_rhs = (
        "pCtrl_exceptionVec_2?20'h0:{pRows_1_1[18],pRows_1_1}+{pRows_1_0[18],pRows_1_0}"
        "+{pRows_0_1[18],pRows_0_1}+{pRows_0_0[18],pRows_0_0}" if feature else
        "pCtrl_exceptionVec_2?19'h0:pRows_0_0+pRows_0_1")
    need(compact(expressions[0]['expression'])==expected_rhs,
         'exact reviewed signed-row width/extension/invalid-zero R expression')
    return dict(instances=sorted(instances),p_row_registers=pnames,input_halves_verified=True,
        p_capture_and_dot8_zero_verified=True,non_data_sequential_assignments_unchanged=True,
        architectural_output_unchanged=True,r_data_write=expressions[0],
        post_p_actual_expression_verified=True,post_p_actual_expression_review_pending=False)


def run(a):
    deadline=time.monotonic()+a.budget_seconds
    os.sched_setaffinity(0,{a.cpu});os.setpriority(os.PRIO_PROCESS,0,5)
    repo,cost,fu,out=a.repo.resolve(),a.cost_root.resolve(),a.fu_root.resolve(),a.output.resolve()
    here=Path(__file__).resolve().parent
    candidate=here/'VDotDatapath.scala'
    wrapper=here/'VDotElastic.scala'
    baseline=a.signed8_local.resolve()
    rbase=a.rwidth_local.resolve()
    previous=a.previous_local.resolve()
    need(120<=a.budget_seconds<=1800 and not out.exists(), 'fresh output and finite budget')
    for d in (repo,cost,fu,here,baseline,rbase,previous):
        need(out!=d and not out.is_relative_to(d) and not d.is_relative_to(out),'separate input/output trees')
    gen,nominal=cost/'generation-01',cost/'nominal-01'
    pins={}
    def pin(path,expected=None):
        path=Path(path).resolve();actual=sha(path)
        need(expected is None or actual==expected,'fixed input '+str(path))
        need(str(path) not in pins or pins[str(path)]==actual,'consistent pin')
        pins[str(path)]=actual
        return path
    pin(gen/'result.json',GEN_SHA);pin(gen/'inputs.json',GEN_INPUTS_SHA)
    pin(gen/'classpath-before.json',CP_SHA);pin(nominal/'result.json',COST_SHA)
    pin(candidate,SOURCE_SHA);pin(repo/REL_SOURCE,ORIGINAL_SOURCE_SHA)
    pin(wrapper,WRAPPER_SHA);pin(repo/REL_WRAPPER,ORIGINAL_WRAPPER_SHA)
    pin(Path(__file__));pin(here/'CSA_CONTRACT.md');pin(here/'source-derivation.json')
    pin(here/'verify_csa.py',VERIFY_SHA)
    # This is a single closed predecessor, not a generic resume or retry option.
    for rel,digest in PREVIOUS_PINS.items():pin(previous/rel,digest)
    prior=json.loads((previous/'result.json').read_bytes())
    prior_inputs=json.loads((previous/'inputs.json').read_bytes())
    need(prior['contract']=='dot16-fused-signed8-csa-local-v3' and prior['status']=='FAILED'
         and prior.get('finished') and not prior['fu_results'] and not prior['cost_results'],
         'exact closed predecessor stopped before FU/cost')
    need([r['label'] for r in prior['commands']]==PREVIOUS_LABELS,
         'only the six completed precursor commands and one bounded miter')
    need(all(r.get('finished') and r.get('reaped') is True and r.get('group_absent') is True
             for r in prior['commands']), 'all predecessor processes recorded reaped')
    need(all(r.get('exit_code')==0 and r['expected_exit']==0 for r in prior['commands'][:6]),
         'all six reused stages really completed')
    last=prior['commands'][-1]
    need(last['budget_seconds']==120 and last['expected_exit'] is None and 'exit_code' not in last
         and last.get('cleanup_complete') is True and
         prior['error']==repr(subprocess.TimeoutExpired(last['argv'],120)),
         'only the recorded external wall timeout may be continued')
    need(prior['candidate_source_sha256']==SOURCE_SHA and prior['candidate_wrapper_sha256']==WRAPPER_SHA
         and prior['wrapper_post_p_decode_review_completed'] is True
         and prior['direct_signed_row_encoding_verified'] is True
         and prior_inputs['recipe_sha256']==GEN_INPUTS_SHA, 'same actual source and generation recipe')
    for path,digest in {**prior_inputs['originals'],**prior_inputs['snapshots']}.items():pin(path,digest)
    class_pins=json.loads((previous/'overlay-classes.json').read_bytes())
    need(set(class_pins)=={str(p.resolve()) for p in (previous/'overlay-classes').rglob('*') if p.is_file()},
         'closed exact predecessor compiled-class set')
    for path,digest in class_pins.items():pin(path,digest)
    need(len(prior['generated'])==4 and
         {(x['kind'],x['feature']) for x in prior['generated']}=={(k,f) for k in ('cost','fu') for f in (0,1)},
         'all four original generated consumers exactly once')
    # Record these predecessor input pins before writing this run's inputs.json.
    for entry in prior['generated']:
        for rec in entry['files']:pin(previous/rec['path'],rec['sha256'])
        folder=previous/f"{entry['kind']}-feature{entry['feature']}"/'rtl'
        pin(folder/'filelist.f',entry['filelist_sha256'])
        pin(folder/'firrtl_black_box_resource_files.f',entry['resource_manifest_sha256'])
    miter_log=(previous/'actual-csa-independent-miter.log').read_text()
    need('Solving problem with 39622 variables and 111869 clauses..' in miter_log and
         not any(s in miter_log for s in ('SAT proof finished', 'ERROR:', 'TIMEOUT')),
         'recorded solver log has neither result nor error; it is not solver PASS')
    pin(rbase/'result.json',RWIDTH_BASELINE_SHA)
    pin(rbase/'source-snapshot/VDotElastic.scala',RWIDTH_WRAPPER_SHA)
    pin(rbase/'source-snapshot/VDotDatapath.scala',RWIDTH_DATAPATH_SHA)
    rb=json.loads((rbase/'result.json').read_bytes())
    need(rb['status']=='SIGNED8_RESULT_WIDTH_GENERATED_FU_AND_COST_COMPLETE' and rb['fu_qualified']
         and rb['arithmetic_equivalent'] and rb['inputs_unchanged'] and rb['all_children_reaped'],
         'completed applicable actual R19/R20 baseline')
    for entry in rb['generated']:
        for rec in entry['files']:pin(rbase/rec['path'],rec['sha256'])
    pin(baseline/'result.json',BASELINE_SHA)
    base=json.loads((baseline/'result.json').read_bytes())
    need(base['status']=='INLINE_SIGNED8_GENERATED_EQUIVALENT_FU_AND_COST_COMPLETE'
         and base['arithmetic_equivalent'] and base['inputs_unchanged'] and base['all_children_reaped'],
         'completed applicable signed8 source proof and cost')
    proof=json.loads((here/'source-derivation.json').read_bytes())
    need(proof['baseline_wrapper_sha256']==RWIDTH_WRAPPER_SHA and
         proof['candidate_wrapper_sha256']==WRAPPER_SHA and proof['exact_inverse'] is True and
         proof['baseline_datapath_sha256']==RWIDTH_DATAPATH_SHA and
         proof['candidate_datapath_sha256']==SOURCE_SHA and proof['old_datapath_exact_prefix_bytes']==2925,
         'fixed source derivation')
    need(candidate.read_bytes()[:2925]==(rbase/'source-snapshot/VDotDatapath.scala').read_bytes(),
         'unchanged complete legacy datapath prefix')
    restored=wrapper.read_text()
    for edit in reversed(proof['edits']):
        need(restored.count(edit['after'])==1, 'unique wrapper inverse edit')
        restored=restored.replace(edit['after'],edit['before'],1)
    need(restored.encode()==(rbase/'source-snapshot/VDotElastic.scala').read_bytes(), 'entire actual R19/R20 wrapper recovered')
    for feature in (0,1):
        for kind in ('cost','fu'):
            for name in ('VDotProducts.sv','VDotSignedByteProduct.sv','VDotReduce.sv'):
                path=baseline/f'{kind}-feature{feature}'/'rtl'/name
                entry=next(x for x in base['generated'] if x['feature']==feature and x['kind']==kind)
                expected=next(x['sha256'] for x in entry['files'] if x['path']==path.relative_to(baseline).as_posix())
                pin(path,expected)
    old_gen=json.loads((gen/'result.json').read_bytes())
    cfg=json.loads((gen/'inputs.json').read_bytes())
    old_cost=json.loads((nominal/'result.json').read_bytes())
    need(old_gen['status']=='TWO_COST_INPUTS_GENERATED_AND_PARSED' and old_gen['input_identity_unchanged'],
         'completed common generation receipt')
    need(old_cost['status']=='TWO_COMMON_FU_COSTS_RECORDED' and old_cost['inputs_unchanged'],'completed common cost receipt')
    for path,digest in {**cfg['originals'],**cfg['snapshots']}.items():pin(path,digest)
    for rel,digest in HELPERS.values():pin(repo/rel,digest)
    for feature,(folder,cpp_sha) in CPP.items():
        status_path=pin(fu/folder/'status.json')
        status=json.loads(status_path.read_bytes())
        need(status['passed'] is True and status['qualification']==f'DOT16_FU_FEATURE_{feature}_PASS'
             and status['process_group_absent'] is True,'applicable original FU completion')
        pin(fu/folder/'source-snapshot/dot16_fu_test.cpp',cpp_sha)
        pin(fu/folder/'campaign/vectors.tsv',VECTORS_SHA)
        manifest_path=pin(fu/folder/'campaign/generated-files.json')
        for rec in json.loads(manifest_path.read_bytes()):
            pin(fu/folder/'campaign'/rec['path'],rec['sha256'])
        for rec in old_gen['generated'][feature]['files']:pin(gen/rec['path'],rec['sha256'])
        for name,key in (('map.ys','map_script_sha256'),('timing.tcl','sta_script_sha256')):
            pin(nominal/f'feature{feature}'/name,old_cost['results'][feature][key])
        constraint=pin(nominal/f'feature{feature}'/'abc.constr')
        need(constraint.read_bytes()==b'set_driving_cell BUF_X1\nset_load 5.0\n','original exact ABC driving/load constraint')
    lib=pin(old_cost['library']['path'],old_cost['library']['sha256'])
    for rec in old_cost['tools'].values():pin(rec['path'],rec['sha256'])
    verilator_root=Path('/home/lizufan/riscv-tools/verilator-5.052')
    verilator=pin(verilator_root/'bin/verilator','098b09b11ba7d3e904ae13d924a9e8dac8ced5c9d7c9beff3b9d36119a417581')
    pin(verilator_root/'bin/verilator_bin','44e1e7e32a8f3005a2fc6323b040c871d43e9884b30fa801b10d06c342513b84')
    # Bind emitted-model headers/make rules and the selected C++/make executables.
    for p in sorted((verilator_root/'share/verilator').rglob('*')):
        if p.is_file():pin(p)
    for p in ('/usr/bin/make','/usr/bin/ar'):pin(p)
    pin('/usr/local/bin/clang++','7969846391c1fe04f816c26bd7d6a09171e9330378c9ec8fd6c841dafec66faa')
    pins['/usr/local/bin/clang++']='7969846391c1fe04f816c26bd7d6a09171e9330378c9ec8fd6c841dafec66faa'
    out.mkdir(parents=True);snap=out/'source-snapshot';snap.mkdir();tmp=out/'tmp';tmp.mkdir()
    copies={name:repo/rel for name,(rel,_) in HELPERS.items()}
    copies.update({'VDotDatapath.scala':candidate,'original-VDotDatapath.scala':repo/REL_SOURCE,
        'GenerateVDotCost.scala':gen/'source-snapshot/GenerateVDotCost.scala',
        'csa.py':Path(__file__),'CSA_CONTRACT.md':here/'CSA_CONTRACT.md',
        'verify_csa.py':here/'verify_csa.py',
        'VDotElastic.scala':wrapper,'original-VDotElastic.scala':repo/REL_WRAPPER,
        'source-derivation.json':here/'source-derivation.json',
        'vectors.tsv':fu/'flag1-01/campaign/vectors.tsv'})
    for feature,(folder,_) in CPP.items():copies[f'feature{feature}-fu_test.cpp']=fu/folder/'source-snapshot/dot16_fu_test.cpp'
    for name in ('VDotProducts.sv','VDotSignedByteProduct.sv','VDotReduce.sv'):
        copies['gold-'+name]=baseline/'cost-feature0/rtl'/name
    for name,rel in {
        'predecessor-result.json':'result.json', 'predecessor-inputs.json':'inputs.json',
        'predecessor-overlay-classes.json':'overlay-classes.json',
        'predecessor-csa.py':'source-snapshot/csa.py',
        'predecessor-CSA_CONTRACT.md':'source-snapshot/CSA_CONTRACT.md',
    }.items():copies[name]=previous/rel
    snapshots={}
    for name,source in copies.items():
        target=snap/name;target.write_bytes(source.read_bytes())
        need(sha(target)==pins[str(source.resolve())],'exact snapshot '+name)
        snapshots[str(target)]=sha(target)
    util=module(snap/'process_helper.py','inline_process')
    cp_util=module(snap/'classpath_helper.py','inline_classpath')
    helper=module(snap/'cost_helpers.py','inline_cost')
    need(all(not util.group_exists(r['pid']) for r in prior['commands']),
         'predecessor process groups still absent; never stop or reuse another process')
    cp_old=json.loads((gen/'classpath-before.json').read_bytes())
    cp_paths=[x['path'] for x in cp_old]
    need(cp_util.classpath_identity(cp_paths,repo)==cp_old,'unchanged entire original cached classpath')
    need(all(not Path(p).exists() and not Path(p).is_symlink() for p in cfg['absent_optional_resources']),
         'original absent resource paths')
    save(out/'classpath-before.json',cp_old)
    result=dict(contract=CONTRACT,status='RUNNING',started=util.stamp(),commands=[],
        candidate_source_sha256=SOURCE_SHA,original_source_sha256=ORIGINAL_SOURCE_SHA,
        candidate_wrapper_sha256=WRAPPER_SHA,original_wrapper_sha256=ORIGINAL_WRAPPER_SHA,
        signed8_gold_result_sha256=BASELINE_SHA,rwidth_baseline_result_sha256=RWIDTH_BASELINE_SHA,
        result_widths={0:19,1:20},p_row_bits=19,p_rows_per_half=2,
        representation_equivalence_basis='Strict full emitted-module DAG/Boolean/weight proof plus exact source inverse, actual wrapper binding and complete FU checks. No whole-FU sequential SAT claim.',
        cpu_affinity=[a.cpu],nice=5,budget_seconds=a.budget_seconds,resident_modified=False,
        original_cache_modified=False,production_default_changed=False,new_core_builds=0,new_core_runs=0,
        arithmetic_equivalent=False,fu_qualified=False,parent_qualified=False,
        wrapper_post_p_decode_review_completed=False,
        fullcore_qualified=False,application_performance_qualified=False,core_cost_qualified=False,
        generation_reused=True,predecessor=dict(path=str(previous),result_sha256=PREVIOUS_PINS['result.json'],
            status=prior['status'],commands_reused=6,commands_not_retried=1,
            source_generation_and_structure_only=True),
        generated=[],fu_results=[],cost_results=[])
    save(out/'inputs.json',dict(originals=pins,snapshots=snapshots,recipe_sha256=GEN_INPUTS_SHA))
    save(out/'result.json',result)
    pending=[None]
    def interrupt(signum,frame):
        if pending[0] is None:pending[0]=signum
    def check():
        if pending[0] is not None:raise InterruptedError('received signal '+str(pending[0]))
    signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
    env={**os.environ,**cfg['flags'],'LANG':'C','LC_ALL':'C','OMP_NUM_THREADS':'1',
        'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1',
        'TMPDIR':str(tmp),'CHISEL_FIRTOOL_PATH':str(Path(cfg['firtool_path']).parent),
        'VERILATOR_ROOT':str(verilator_root/'share/verilator'),'MAKEFLAGS':'-j1',
        'PATH':'/usr/bin:/bin','MAKE':'/usr/bin/make','CXX':'/usr/local/bin/clang++','LINK':'/usr/local/bin/clang++','AR':'/usr/bin/ar'}
    for key in ('JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','JAVA_OPTS',
                'MAKEFILES','MFLAGS','MAKEOVERRIDES'):env.pop(key,None)
    java_base=[x if not x.startswith('-Djava.io.tmpdir=') else '-Djava.io.tmpdir='+str(tmp) for x in cfg['java_base']]
    def command(label,argv,limit=120,expected=0):
        check();remaining=deadline-time.monotonic();need(remaining>0,'total deadline before '+label)
        rec=dict(label=label,argv=list(map(str,argv)),started=util.stamp(),budget_seconds=min(limit,remaining),
                 feature=env['VDOT_DOT16'],expected_exit=expected)
        result['commands'].append(rec);proc=None
        try:
            with (out/(label+'.log')).open('wb') as log:
                proc=subprocess.Popen(rec['argv'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                rec['pid']=proc.pid;save(out/'result.json',result)
                until=time.monotonic()+rec['budget_seconds']
                while True:
                    check();left=until-time.monotonic()
                    if left<=0:raise subprocess.TimeoutExpired(rec['argv'],rec['budget_seconds'])
                    try:rec['exit_code']=proc.wait(timeout=min(.25,left));break
                    except subprocess.TimeoutExpired:continue
            need(expected is None or rec['exit_code']==expected,label+' exit mismatch')
            need(not util.group_exists(proc.pid),label+' left child processes')
        finally:
            if proc is not None:
                if util.group_exists(proc.pid):rec['cleanup_complete']=util.stop_group(proc)
                rec['reaped']=proc.poll() is not None;rec['group_absent']=not util.group_exists(proc.pid)
            rec['finished']=util.stamp();save(out/'result.json',result)
        return (out/(label+'.log')).read_text(errors='replace'),rec['exit_code']
    generated_pins={}
    try:
        # The exact generated bytes and compiler/classpath identities were retained
        # by the closed predecessor. No Scala, generator, checker or SAT subprocess runs here.
        save(out/'reused-overlay-classes.json',class_pins)
        generated_pins[str(out/'reused-overlay-classes.json')]=sha(out/'reused-overlay-classes.json')
        for feature in (0,1):
            env['VDOT_DOT16']=str(feature)
            for kind in ('cost','fu'):
                folder=out/f'{kind}-feature{feature}';rtl=folder/'rtl'
                entry=next(x for x in prior['generated'] if x['feature']==feature and x['kind']==kind)
                old_folder=previous/f'{kind}-feature{feature}'/'rtl'
                rtl.mkdir(parents=True)
                for rec in entry['files']:
                    source=previous/rec['path']
                    need(source.parent==old_folder and source.suffix=='.sv', 'only exact prior consumer SV files')
                    pin(source,rec['sha256'])
                    need(source.stat().st_size==rec['bytes'], 'prior SV byte count')
                    target=rtl/source.name
                    need(not target.exists(), 'unique copied generated SV name')
                    target.write_bytes(source.read_bytes())
                    need(sha(target)==rec['sha256'], 'identical reused SV bytes')
                for name,key in (('filelist.f','filelist_sha256'),
                                 ('firrtl_black_box_resource_files.f','resource_manifest_sha256')):
                    source=pin(old_folder/name,entry[key])
                    (rtl/name).write_bytes(source.read_bytes())
                    need(sha(rtl/name)==entry[key], 'identical relative generated manifest')
                top='CommonFuCostTop' if kind=='cost' else 'VDotElasticFuTestTop'
                expected={'VDotElastic.sv','VDotCarrySaveRows.sv',top+'.sv','extern_modules.sv'}
                files=sorted(rtl.glob('*.sv'))
                need({p.name for p in files}==expected,'closed three design SV files plus exact external comment file')
                header=(rtl/(top+'.sv')).read_text().split('module '+top+'(',1)[0]
                need((rtl/'extern_modules.sv').read_text()==header+'// external module VDotCarrySaveRows\n\n',
                     'external declaration file contains only exact generated header and comment')
                filelist=rtl/'filelist.f'
                listed=[(rtl/t).resolve() for t in shlex.split(filelist.read_text(),comments=True)]
                need(len(listed)==len(files) and set(listed)=={p.resolve() for p in files},'exact full generated filelist')
                need(all(b'// ----- 8< ----- FILE "' not in p.read_bytes() for p in files),'no virtual files')
                resource=rtl/'firrtl_black_box_resource_files.f'
                tokens=shlex.split(resource.read_text(),comments=True)
                resources=[(Path(t) if Path(t).is_absolute() else rtl/t).resolve() for t in tokens]
                need(resources==[(rtl/'VDotCarrySaveRows.sv').resolve()],'exact actual inline resource manifest')
                old_rtl=gen/f'feature{feature}'/'rtl' if kind=='cost' else fu/CPP[feature][0]/'campaign/rtl'
                need((rtl/(top+'.sv')).read_bytes()==(old_rtl/(top+'.sv')).read_bytes(),
                     'unchanged entire public common-FU consumer top')
                binding=wrapper_binding((rtl/'VDotElastic.sv').read_text(),
                    (rbase/f'{kind}-feature{feature}/rtl/VDotElastic.sv').read_text(),feature)
                result.setdefault('wrapper_bindings',[]).append(dict(feature=feature,kind=kind,**binding))
                storage=re.findall(r'\breg\s+\[(\d+):0\]\s+rPacket_res_data\s*;', (rtl/'VDotElastic.sv').read_text())
                need(storage==[str(19 if feature else 18)], 'exact actual result storage width')
                for p in files+[resource,filelist]:generated_pins[str(p)]=sha(p)
                result['generated'].append(dict(feature=feature,kind=kind,reused_from=str(old_folder),generation_reused=True,files=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in files],resource_manifest_sha256=sha(resource),filelist_sha256=sha(filelist)))
                save(out/'result.json',result)
        first=out/'cost-feature0/rtl'
        for row in result['generated']:
            rtl=out/f"{row['kind']}-feature{row['feature']}"/'rtl'
            need((rtl/'VDotCarrySaveRows.sv').read_bytes()==(first/'VDotCarrySaveRows.sv').read_bytes(),
                 'identical actual arithmetic across all four consumers')
        need(len(result['wrapper_bindings'])==4 and
             all(x['post_p_actual_expression_verified'] for x in result['wrapper_bindings']),
             'all four actual post-P expressions bound')
        result['wrapper_post_p_decode_review_completed']=True
        for name in ('arithmetic-structure.json','actual-csa-independent-miter.log','gold.sv','gate.sv','prove.ys'):
            target=out/name;target.write_bytes((previous/name).read_bytes())
            need(sha(target)==PREVIOUS_PINS[name], 'exact preserved proof artifact')
            generated_pins[str(target)]=sha(target)
        structure=json.loads((out/'arithmetic-structure.json').read_bytes())
        need(structure==prior['arithmetic_structure_proof'] and
             structure['status']=='CSA_STRUCTURAL_EQUIVALENCE_PASS' and
             structure['all_inputs_equivalent'] is True and structure['parsed_entire_module'] is True
             and structure['verifier']['sha256']==VERIFY_SHA
             and structure['rtl_sha256']==sha(first/'VDotCarrySaveRows.sv'),
             'exact previously completed full-input structural proof of these bytes')
        need(structure['discarded_carries']==[] and structure['rows_msb_to_lsb']['row0'][0]=="1'b1"
             and structure['rows_msb_to_lsb']['row1'][0]=="1'b0", 'required stronger signed-row encoding')
        result['arithmetic_structure_proof']=structure
        result['arithmetic_structure_proof_reused_from']=str(previous/'arithmetic-structure.json')
        result['direct_signed_row_encoding_verified']=True
        result['independent_miter']=dict(status='UNKNOWN_EXTERNAL_TIMEOUT',solver_timeout_seconds=60,
            total_command_budget_seconds=120,log_sha256=PREVIOUS_PINS['actual-csa-independent-miter.log'],
            unconstrained_inputs=True,counterexample_found=False,solver_equivalence_proved=False,
            baseline_result_sha256=BASELINE_SHA,reused_from=str(previous),retried=False)
        result['arithmetic_proof_completed']=True
        save(out/'result.json',result)
        for feature in (0,1):
            env['VDOT_DOT16']=str(feature)
            rtl=out/f'fu-feature{feature}'/'rtl';files=sorted(rtl.glob('*.sv'));obj=out/f'fu-feature{feature}'/'obj'
            top='VDotElasticFuTestTop';stem=f'fu-{feature}'
            command(stem+'-lint',[verilator,'--lint-only','--assert','--top-module',top,*files],120)
            command(stem+'-build',[verilator,'--cc','--exe','--build','--assert','--top-module',top,
                '--Mdir',obj,'--compiler','clang','-j','1','-MAKEFLAGS','CXX=/usr/local/bin/clang++ LINK=/usr/local/bin/clang++ AR=/usr/bin/ar',
                '-CFLAGS','-std=c++17 -O2',*files,snap/f'feature{feature}-fu_test.cpp'],300)
            binary=obj/('V'+top)
            generated_pins[str(binary)]=sha(binary)
            log,_=command(stem+'-positive',[binary,snap/'vectors.tsv'],60)
            coverage=util.completion_gate(log,feature,dict(passed=True,stage='fu'))
            for fault in ('identity','wen','high','cancel'):
                label=stem+'-inject-'+fault
                _,rc=command(label,[binary,snap/'vectors.tsv',fault],60,expected=None)
                command(stem+'-check-'+fault,[sys.executable,'-B',snap/'check_negative_fu.py','--fault',fault,
                    '--return-code',str(rc),'--log',out/(label+'.log')],30)
            result['fu_results'].append(dict(feature=feature,coverage=coverage,binary_sha256=sha(binary),faults=['identity','wen','high','cancel'],passed=True))
            save(out/'result.json',result)
        result['fu_tests_completed']=True
        for feature in (0,1):
            env['VDOT_DOT16']=str(feature)
            rtl=out/f'cost-feature{feature}'/'rtl';dest=out/f'cost-feature{feature}'/'mapped';dest.mkdir()
            old_dir=nominal/f'feature{feature}';old_rtl=old_dir/'generated-rtl'
            point=old_cost['results'][feature]
            (dest/'abc.constr').write_bytes((old_dir/'abc.constr').read_bytes())
            need(sha(dest/'abc.constr')==pins[str((old_dir/'abc.constr').resolve())],'exact copied ABC constraint')
            generated_pins[str(dest/'abc.constr')]=sha(dest/'abc.constr')
            for name in ('map.ys','timing.tcl'):
                original=(old_dir/name).read_text()
                changed=original.replace(str(old_rtl),str(rtl)).replace(str(old_dir),str(dest))
                prefix=''
                if name=='map.ys':
                    old_lines=[line for line in changed.splitlines() if line.startswith('read_verilog ')]
                    need(len(old_lines)==4,'fixed four original common-FU read commands')
                    replacement=['read_verilog -sv -DSYNTHESIS '+str(rtl/n) for n in
                        ('VDotCarrySaveRows.sv','VDotElastic.sv','CommonFuCostTop.sv')]
                    old_block='\n'.join(old_lines)+'\n';new_block='\n'.join(replacement)+'\n'
                    need(changed.count(old_block)==1,'one contiguous original module read block')
                    changed=changed.replace(old_block,new_block,1)
                final=prefix+changed
                inverse=final[len(prefix):]
                if name=='map.ys':
                    need(inverse.count(new_block)==1,'one exact replacement module read block')
                    inverse=inverse.replace(new_block,old_block,1)
                inverse=inverse.replace(str(dest),str(old_dir)).replace(str(rtl),str(old_rtl))
                need(inverse==original,'only exact input-module read list and output paths changed in mapping/STA template')
                (dest/name).write_text(final)
                generated_pins[str(dest/name)]=sha(dest/name)
            log,_=command(f'map-{feature}',[old_cost['tools']['yosys']['path'],'-T','-s',dest/'map.ys'],240)
            design=json.loads((dest/'mapped.json').read_bytes())['modules']['CommonFuCostTop']
            cells=Counter(x['type'] for x in design['cells'].values());areas=helper.library_areas(lib)
            need(not set(cells)-set(areas),'all actual cells mapped, no blackbox')
            area=sum(areas[k]*v for k,v in cells.items())
            printed=re.findall(r'Chip area for module.*?:\s*([0-9.]+)',log)
            need(printed and abs(float(printed[-1])-area)<.02,'independent area sum')
            ports={n:dict(direction=p['direction'],width=len(p['bits']),offset=p.get('offset',0)) for n,p in design['ports'].items()}
            need(ports==point['ports'],'complete unchanged common-FU interface')
            actual_dff=sum(v for k,v in cells.items() if k.startswith('DFF'))
            expected_dff=1675 if feature else 1637
            need(actual_dff<=rb['cost_results'][feature]['dff_cells'], 'compressed P state adds no registers')
            log,_=command(f'sta-{feature}',[old_cost['tools']['sta']['path'],'-no_init','-exit',dest/'timing.tcl'],60)
            need(not re.search(r'(?m)^.*\bError:',log) and 'not found' not in log and
                 log.splitlines().count('DOT16_GENERATED_FU_STA_COMPLETE')==1,'complete error-free same-template STA')
            timing={n:helper.parse_path((dest/(n+'.rpt')).read_text()) for n in ('r2r','i2r','r2o','i2o','ready')}
            need(all(p['exists'] for p in timing.values()),'all five path classes exist')
            constants=helper.constant_warnings((dest/'setup-checks.rpt').read_text(),design)
            result['cost_results'].append(dict(feature=feature,cell_area=area,cell_count=sum(cells.values()),
                dff_cells=actual_dff,original_dff_cells=point['dff_cells'],
                result_storage_bits=20 if feature else 19,cell_histogram=dict(sorted(cells.items())),ports=ports,
                source_expected_dff_cells=expected_dff,dff_matches_source_expectation=actual_dff==expected_dff,
                dff_delta_from_rwidth=actual_dff-rb['cost_results'][feature]['dff_cells'],
                area_delta_from_rwidth=area-rb['cost_results'][feature]['cell_area'],
                area_delta_from_signed8=area-base['cost_results'][feature]['cell_area'],
                area_delta_from_matched_original=area-point['cell_area'],area_within_20000=area<=20000,
                timing=timing,reviewed_constant_endpoints=constants,
                nominal_setup_met=all(p['slack_ns']>=0 for p in timing.values()),
                mapped_sha256=sha(dest/'mapped.v'),mapped_json_sha256=sha(dest/'mapped.json')))
            save(out/'result.json',result)
        check()
        need(len(result['commands'])==26, 'only the previously unrun 22 FU and four cost commands')
        for path,h in {**pins,**snapshots,**class_pins,**generated_pins}.items():need(sha(path)==h,'unchanged pin '+path)
        need(cp_util.classpath_identity(cp_paths,repo)==cp_old,'original entire classpath remained unchanged')
        need(all(not Path(p).exists() and not Path(p).is_symlink() for p in cfg['absent_optional_resources']),
             'optional resource paths remained absent')
        need(time.monotonic()<deadline,'total budget after complete final audit')
        save(out/'final-artifact-pins.json',{**snapshots,**class_pins,**generated_pins})
        result.update(status='CSA_REUSED_GENERATION_ARITHMETIC_FU_AND_COST_COMPLETE',
            arithmetic_equivalent=True,fu_qualified=True,
            inputs_unchanged=True,generated_inputs_unchanged=True,original_classpath_unchanged=True,
            all_children_reaped=all(r['reaped'] and r['group_absent'] for r in result['commands']))
    except BaseException as exc:
        result.update(status='FAILED',error=repr(exc));raise
    finally:
        result['finished']=util.stamp();save(out/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','generated','cost_results')},indent=2))
    print(json.dumps(dict(cost_results=[{k:v for k,v in x.items() if k not in ('cell_histogram','ports','reviewed_constant_endpoints')} for x in result['cost_results']]),indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','cost-root','fu-root','signed8-local','rwidth-local','previous-local','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,choices=range(4),default=1)
    p.add_argument('--budget-seconds',type=int,default=1200)
    run(p.parse_args())
