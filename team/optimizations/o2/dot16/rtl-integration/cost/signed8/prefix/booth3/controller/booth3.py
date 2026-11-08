#!/usr/bin/env python3
"""Compile one three-row Booth candidate; prove new P and R arithmetic, then FU/cost."""
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
CONTRACT = 'dot16-prefix-booth3-local-v1'
CONTROLLER_BASELINE_SHA = '6681fce5cc739206c5922e025d76ae0a75334d57502b089902b5a7a72f05ea60'
PREFIX_BASELINE_SHA = 'a0c4dd60fddc001f368b71ec283327f2d7fe0874080ac35304e3debe783116d0'
PREFIX_BASELINE_BYTES = 205865
PREFIX_DATAPATH_SHA = '1d02d8a34772e7d9b9947f997f32465f3e946f4b24cacc66159eef7ee10ab3bb'
CSA_BASELINE_SHA = '21510c330817f12c03426ac0ca262331c4ff088d90e33b2be1fefae0c605707a'
CSA_BASELINE_BYTES = 109822
CSA_DATAPATH_SHA = '62ace0342070bc2a40f57b999c8aa94d376543a4cc79d455cf69e6083742488c'
CSA_WRAPPER_SHA = '4a525d2e8ead5cc10a193d9724342162af4ffebd130c58ad7c606093849ac1c8'
CSA_STRUCTURE_SHA = '9483d70f24876e7c89281e559d3d062355c0787e38a7f3fd7ab9cf36d3cd8ad6'
CSA_MULTIPLICATION_LOG_SHA = 'a9175ff5e52888f37d8cf8eeeb1673f6975e32cc8e08687be91f3db2cc845b2b'
SOURCE_DERIVATION_SHA = '202bc499e58ee12cac8986a65d2ec9a4e5ccd78b0e530370c22516b6edbac876'
CSA_DFF_CELLS = {0: 1639, 1: 1678}
RWIDTH_BASELINE_SHA = 'f42f7285ff8a357877c546d433251b1dc8c8eef66ee9218c9e3b2c002ca0a261'
RWIDTH_WRAPPER_SHA = '70dcc27381d3e7226eeff333c943d35b982ec1fdd37b75b680060a13aaf94e2a'
RWIDTH_DATAPATH_SHA = '50522c0cd2700f7f852872049533bc31f79ce811ad2ed53da2c1d333cece45e2'
VERIFY_SHA = 'c0181c3c099a4a4e3ce4fcfcd1af3c34d337031675b6533ad303327ad632d587'
WRAPPER_SHA = '1bc162257ab7d53671a06b0d24015045026330c8680ee25dae482dbf7a316238'
PREFIX_WRAPPER_SHA = '912c1a038ef8e9a1ac56cfa349161ae1c582d763acfce5352b08ebde2a227f92'
ORIGINAL_WRAPPER_SHA = '63911b937a526b97ddaa67e34526fd19bbd2fa2801eadfda10ae6c2fa4b9fe9e'
REL_WRAPPER = 'src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala'
BASELINE_SHA = '19f90c867022ba2259b83fb2600bb56ef7066eda54023cead03c6e35bf23b7d7'
GEN_SHA = '7b45921ee1b5ff564113daa61403c4e52ecb598305aad6c093f4ab5768fe0a09'
GEN_INPUTS_SHA = 'ec29dc8725cf3a1c04ea684e2753debc1a9b2a04d37b4adadcdfe96f85ec20d8'
CP_SHA = 'd9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902'
COST_SHA = '8c9a22771594565bfaa812309f68c84de4e8a213b02b9aba03440373f61e2e51'
SOURCE_SHA = '880ba4c2046721985560b788bf871cc69d930ebfe27561628ba7b930370ff680'
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
    matches=re.findall(r'\bVDotCarrySaveRows\s+(\w+)\s*\((.*?)\);',text,re.S)
    instances=dict(matches)
    expected={'products','highProducts'} if feature else {'products'}
    need(len(matches)==len(expected) and set(instances)==expected,'actual one/two unique CSA instances')
    for name,body in instances.items():
        pairs=re.findall(r'\.(\w+)\s*\(([^()]*)\)',body)
        rest=re.sub(r'\.(\w+)\s*\(([^()]*)\)','',body)
        need(not rest.replace(',','').strip() and len(pairs)==5 and len(dict(pairs))==5,
             'closed five CSA instance ports')
        ports={k:compact(v) for k,v in pairs}
        high=name=='highProducts'; hi,lo=(127,64) if high else (63,0)
        need(ports=={'vs1':f'io_in_bits_data_src_0[{hi}:{lo}]',
                     'vs2':f'io_in_bits_data_src_1[{hi}:{lo}]',
                     'row0':f'_{name}_row0','row1':f'_{name}_row1','row2':f'_{name}_row2'},'exact input halves and all three output wires')
    pnames=[f'pRows_{half}_{row}' for half in range(2 if feature else 1) for row in range(3)]
    declarations=re.findall(r'\breg\s+\[(\d+):0\]\s+(pRows_\d+_\d+)\s*;',text)
    need(declarations==[(str(19 if feature else 18),name) for name in pnames],
         'actual complete P rows: feature0 low19, feature1 full20')
    updates=re.findall(r'(?m)^\s*(\w+)\s*<=\s*(.*?);',text,re.S)
    previous_updates=re.findall(r'(?m)^\s*(\w+)\s*<=\s*(.*?);',previous,re.S)
    data=lambda name: name.startswith('pRows_') or name.startswith('pProducts_') or name=='rPacket_res_data'
    need([(n,compact(e)) for n,e in updates if not data(n)]==
         [(n,compact(e)) for n,e in previous_updates if not data(n)],
         'all actual non-data sequential assignments unchanged')
    for half in range(2 if feature else 1):
        for row in range(3):
            name=f'pRows_{half}_{row}'; expressions=[compact(e) for n,e in updates if n==name]
            if half:
                constant="20'h80000" if row==0 else "20'h0"
                expected=f'isDot16?_highProducts_row{row}:{constant}'
            else:
                expected=f'_products_row{row}'+('' if feature else '[18:0]')
            need(expressions==[expected],'exact P capture and dot8 biased-zero encoding')
    output=re.search(r'\bassign\s+io_out_bits_res_data\s*=\s*(.*?);',text,re.S)
    previous_output=re.search(r'\bassign\s+io_out_bits_res_data\s*=\s*(.*?);',previous,re.S)
    need(output and previous_output and compact(output[1])==compact(previous_output[1]),
         'unchanged architectural output sign extension')
    # Source inverse binds all accept/move conditions. Actual emitted ports bind
    # the saved rows to the independently proved, fixed-width prefix finish.
    width=20 if feature else 19
    prefix_instances=re.findall(r'\b(VDotPrefixFinish\d+)\s+(\w+)\s*\((.*?)\);',text,re.S)
    need(len(prefix_instances)==1 and prefix_instances[0][:2]==(f'VDotPrefixFinish{width}','prefixSum'),
         'exact single emitted prefixSum instance')
    body=prefix_instances[0][2]
    pairs=re.findall(r'\.(\w+)\s*\(([^()]*)\)',body)
    rest=re.sub(r'\.(\w+)\s*\(([^()]*)\)','',body)
    need(not rest.replace(',','').strip() and len(pairs)==len(pnames)+1 and len(dict(pairs))==len(pairs),
         'closed prefix ports, no duplicates or unparsed connection')
    ports={k:compact(v) for k,v in pairs}
    expected_ports={'result':'_prefixSum_result'}
    for i,name in enumerate(pnames):
        expected_ports[f'rows_{i}']=name
    need(ports==expected_ports,'exact saved unsigned rows, no signed extension or post-P correction')
    declared=re.findall(r'\bwire\s+\[(\d+):0\]\s+_prefixSum_result\s*;',text)
    need(declared==[str(width-1)],'actual exact prefix result width')
    expressions=[dict(name=n,expression=e) for n,e in updates if n=='rPacket_res_data']
    need(len(expressions)==1,'single actual R data write')
    need(compact(expressions[0]['expression'])==f"pCtrl_exceptionVec_2?{width}'h0:_prefixSum_result",
         'exact illegal-zero or prefix result R expression')
    return dict(instances=sorted(instances),p_row_registers=pnames,input_halves_verified=True,
        p_capture_and_dot8_biased_zero_verified=True,p_row_bits=20 if feature else 19,
        non_data_sequential_assignments_unchanged=True,
        architectural_output_unchanged=True,r_data_write=expressions[0],prefix_module=f'VDotPrefixFinish{width}',
        prefix_instance='prefixSum',prefix_ports=ports,prefix_result_width=width,
        post_p_actual_expression_verified=True,post_p_actual_expression_review_pending=False)


def run(a):
    deadline=time.monotonic()+a.budget_seconds
    os.sched_setaffinity(0,{a.cpu});os.setpriority(os.PRIO_PROCESS,0,5)
    repo,cost,fu,out=a.repo.resolve(),a.cost_root.resolve(),a.fu_root.resolve(),a.output.resolve()
    here=Path(__file__).resolve().parent
    source=here.parent/'source'
    candidate=source/'VDotDatapath.scala'
    wrapper=source/'VDotElastic.scala'
    baseline=a.signed8_local.resolve()
    rbase=a.rwidth_local.resolve()
    cbase=a.csa_local.resolve()
    pbase=a.prefix_local.resolve()
    need(a.cpu==2 and a.budget_seconds==1200 and not out.exists(), 'CPU2, exact 1200s work budget, fresh output')
    for d in (repo,cost,fu,here,source,baseline,rbase,cbase,pbase):
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
    pin(Path(__file__));pin(here/'BOOTH_CONTRACT.md');pin(here/'verify_booth.py',VERIFY_SHA)
    pin(here/'controller-derivation.json');pin(source/'source-derivation.json',SOURCE_DERIVATION_SHA)
    controller_proof=json.loads((here/'controller-derivation.json').read_bytes())
    need(controller_proof['baseline_sha256']==CONTROLLER_BASELINE_SHA and
         controller_proof['candidate_sha256']==sha(__file__) and controller_proof['exact_inverse'] is True,
         'fixed controller derivation identity')
    restored_controller=Path(__file__).read_bytes().decode('utf-8')
    for edit in reversed(controller_proof['edits']):
        need(restored_controller.count(edit['after'])==1,'unique controller inverse edit')
        restored_controller=restored_controller.replace(edit['after'],edit['before'],1)
    need(hashlib.sha256(restored_controller.encode()).hexdigest()==CONTROLLER_BASELINE_SHA,
         'entire completed Booth2 controller recovered')
    pin(cbase/'result.json',CSA_BASELINE_SHA)
    need((cbase/'result.json').stat().st_size==CSA_BASELINE_BYTES,'exact closed CSA result bytes')
    pin(cbase/'source-snapshot/VDotDatapath.scala',CSA_DATAPATH_SHA)
    pin(cbase/'source-snapshot/VDotElastic.scala',CSA_WRAPPER_SHA)
    pin(cbase/'arithmetic-structure.json',CSA_STRUCTURE_SHA)
    pin(cbase/'actual-csa-independent-miter.log',CSA_MULTIPLICATION_LOG_SHA)
    cb=json.loads((cbase/'result.json').read_bytes())
    need(cb['status']=='CSA_REUSED_GENERATION_ARITHMETIC_FU_AND_COST_COMPLETE' and
         cb['arithmetic_equivalent'] is True and cb['fu_qualified'] is True and
         cb['inputs_unchanged'] is True and cb['generated_inputs_unchanged'] is True and
         cb['original_classpath_unchanged'] is True and cb['all_children_reaped'] is True and
         cb['candidate_source_sha256']==CSA_DATAPATH_SHA and cb['candidate_wrapper_sha256']==CSA_WRAPPER_SHA,
         'fixed completed and applicable CSA arithmetic/FU/local-cost baseline')
    need(len(cb['generated'])==4 and {(x['feature'],x['kind']) for x in cb['generated']}==
         {(f,k) for f in (0,1) for k in ('cost','fu')},'complete four prior CSA consumers')
    for entry in cb['generated']:
        rtl=cbase/f"{entry['kind']}-feature{entry['feature']}"/'rtl'
        top='CommonFuCostTop' if entry['kind']=='cost' else 'VDotElasticFuTestTop'
        expected={'VDotCarrySaveRows.sv','VDotElastic.sv',top+'.sv','extern_modules.sv'}
        need(len(entry['files'])==4 and {Path(x['path']).name for x in entry['files']}==expected,
             'closed prior CSA module set')
        for rec in entry['files']:
            path=cbase/rec['path']
            need(path.parent==rtl,'exact prior consumer-relative path')
            pin(path,rec['sha256']);need(path.stat().st_size==rec['bytes'],'exact prior generated byte count')
        pin(rtl/'filelist.f',entry['filelist_sha256'])
        pin(rtl/'firrtl_black_box_resource_files.f',entry['resource_manifest_sha256'])
    need({x['feature']:x['dff_cells'] for x in cb['cost_results']}==CSA_DFF_CELLS,
         'actual measured CSA DFF baseline 1639/1678')
    old_miter=cb['independent_miter']
    need(old_miter['status']=='UNKNOWN_EXTERNAL_TIMEOUT' and old_miter['retried'] is False and
         old_miter['solver_equivalence_proved'] is False and old_miter['counterexample_found'] is False and
         old_miter['log_sha256']==CSA_MULTIPLICATION_LOG_SHA,
         'preserve the old multiplication SAT timeout without promoting or retrying it')
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
    pin(pbase/'result.json',PREFIX_BASELINE_SHA)
    need((pbase/'result.json').stat().st_size==PREFIX_BASELINE_BYTES,'exact closed prefix result')
    pb=json.loads((pbase/'result.json').read_bytes())
    need(pb['status']=='PREFIX_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE' and
         all(pb[k] is True for k in ('arithmetic_equivalent','fu_qualified','inputs_unchanged',
             'generated_inputs_unchanged','original_classpath_unchanged','all_children_reaped')) and
         pb['candidate_source_sha256']==PREFIX_DATAPATH_SHA and pb['candidate_wrapper_sha256']==PREFIX_WRAPPER_SHA,
         'completed applicable exact prefix arithmetic, FU and local cost')
    pin(pbase/'source-snapshot/VDotDatapath.scala',PREFIX_DATAPATH_SHA)
    pin(pbase/'source-snapshot/VDotElastic.scala',PREFIX_WRAPPER_SHA)
    need(len(pb['generated'])==4 and {(x['feature'],x['kind']) for x in pb['generated']}==
         {(f,k) for f in (0,1) for k in ('cost','fu')},'complete prior prefix consumer set')
    for entry in pb['generated']:
        feature,kind=entry['feature'],entry['kind']
        rtl=pbase/f'{kind}-feature{feature}'/'rtl'
        top='CommonFuCostTop' if kind=='cost' else 'VDotElasticFuTestTop'
        expected={'VDotCarrySaveRows.sv','VDotElastic.sv',f'VDotPrefixFinish{20 if feature else 19}.sv',top+'.sv','extern_modules.sv'}
        need(len(entry['files'])==5 and {Path(x['path']).name for x in entry['files']}==expected,
             'closed five-file prior prefix generated set')
        for rec in entry['files']:
            path=pbase/rec['path'];need(path.parent==rtl,'exact prefix consumer-relative path')
            pin(path,rec['sha256']);need(path.stat().st_size==rec['bytes'],'exact prefix generated length')
        pin(rtl/'filelist.f',entry['filelist_sha256'])
        pin(rtl/'firrtl_black_box_resource_files.f',entry['resource_manifest_sha256'])
    need(len(pb['prefix_miters'])==2 and {m['width'] for m in pb['prefix_miters']}=={19,20},
         'exact two original prefix SAT records')
    for miter in pb['prefix_miters']:
        width=miter['width'];feature=1 if width==20 else 0
        need(miter['feature']==feature and miter['row_count']==(4 if feature else 2) and
             miter['status']=='PASS' and miter['solver_equivalence_proved'] is True and
             miter['unconstrained_inputs'] is True and miter['counterexample_found'] is False and
             miter['exit_code']==0 and miter['retried'] is False,'complete exact old prefix SAT qualification')
        pin(pbase/f'cost-feature{feature}/rtl/VDotPrefixFinish{width}.sv',miter['actual_rtl_sha256'])
        for name,key in (('gold.sv','gold_sha256'),('gate.sv','gate_sha256'),('prove.ys','script_sha256')):
            pin(pbase/f'prefix-proof-{width}'/name,miter[key])
        log=pin(pbase/f'actual-prefix-{width}-miter.log',miter['log_sha256']).read_text()
        need(log.count('SAT proof finished - no model found: SUCCESS!')==1 and
             'SAT proof finished - model found: FAIL!' not in log and 'ERROR:' not in log,
             'actual preserved original successful prefix solver log')
    proof=json.loads((source/'source-derivation.json').read_bytes())
    need(proof['contract']==CONTRACT and proof['baseline_datapath_sha256']==PREFIX_DATAPATH_SHA and
         proof['candidate_datapath_sha256']==SOURCE_SHA and proof['baseline_wrapper_sha256']==PREFIX_WRAPPER_SHA and
         proof['candidate_wrapper_sha256']==WRAPPER_SHA and proof['wrapper_byte_identical'] is False and
         proof['exact_inverse'] is True and len(proof['edits'])==16,
         'complete prefix-to-Booth2-to-Booth3 inverse, sixteen exact hunks')
    need(Counter(e['file'] for e in proof['edits'])=={'VDotDatapath.scala':7,'VDotElastic.scala':9},
         'closed per-source edit counts')
    for name,path in (('VDotDatapath.scala',candidate),('VDotElastic.scala',wrapper)):
        restored=path.read_bytes().decode('utf-8')
        for edit in reversed([e for e in proof['edits'] if e['file']==name]):
            need(restored.count(edit['after'])==1,'unique source inverse '+name)
            restored=restored.replace(edit['after'],edit['before'],1)
        need(restored.encode()==(pbase/'source-snapshot'/name).read_bytes(),
             'full frozen prefix source recovered '+name)
    need(proof['external_interface_unchanged'] and proof['clock_reset_slot_protocol_unchanged'] and
         proof['old_prefix_finish_source_retained'] is False and proof['old_prefix_network_suffix_retained'] and
         proof['fresh_three_six_row_unconstrained_proofs_required'] and proof['p_rows_per_half']==3,
         'one P/R boundary change, preserved slot control, fresh R arithmetic proof required')
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
        'booth3.py':Path(__file__),'BOOTH_CONTRACT.md':here/'BOOTH_CONTRACT.md',
        'verify_booth.py':here/'verify_booth.py',
        'prefix-result.json':pbase/'result.json',
        'prefix-VDotDatapath.scala':pbase/'source-snapshot/VDotDatapath.scala',
        'prefix-VDotElastic.scala':pbase/'source-snapshot/VDotElastic.scala',
        'controller-derivation.json':here/'controller-derivation.json',
        'csa-result.json':cbase/'result.json',
        'csa-arithmetic-structure.json':cbase/'arithmetic-structure.json',
        'csa-independent-miter.log':cbase/'actual-csa-independent-miter.log',
        'csa-VDotDatapath.scala':cbase/'source-snapshot/VDotDatapath.scala',
        'csa-VDotElastic.scala':cbase/'source-snapshot/VDotElastic.scala',
        'VDotElastic.scala':wrapper,'original-VDotElastic.scala':repo/REL_WRAPPER,
        'source-derivation.json':source/'source-derivation.json',
        'vectors.tsv':fu/'flag1-01/campaign/vectors.tsv'})
    for feature,(folder,_) in CPP.items():copies[f'feature{feature}-fu_test.cpp']=fu/folder/'source-snapshot/dot16_fu_test.cpp'
    for width in (19,20):
        for name in ('gold.sv','gate.sv','prove.ys'):
            copies[f'prefix-proof-{width}-{name}']=pbase/f'prefix-proof-{width}'/name
        copies[f'prefix-proof-{width}.log']=pbase/f'actual-prefix-{width}-miter.log'
        copies[f'prefix-finish-{width}.sv']=pbase/f'cost-feature{1 if width==20 else 0}/rtl/VDotPrefixFinish{width}.sv'
    snapshots={}
    for name,source in copies.items():
        target=snap/name;target.write_bytes(source.read_bytes())
        need(sha(target)==pins[str(source.resolve())],'exact snapshot '+name)
        snapshots[str(target)]=sha(target)
    util=module(snap/'process_helper.py','inline_process')
    cp_util=module(snap/'classpath_helper.py','inline_classpath')
    helper=module(snap/'cost_helpers.py','inline_cost')
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
        csa_baseline_result_sha256=CSA_BASELINE_SHA,csa_baseline_result_bytes=CSA_BASELINE_BYTES,
        prefix_baseline_result_sha256=PREFIX_BASELINE_SHA,prefix_baseline_result_bytes=PREFIX_BASELINE_BYTES,
        result_widths={0:19,1:20},p_row_bits={0:19,1:20},p_rows_per_half=3,
        representation_equivalence_basis='New complete proof of actual three-row Booth heap; fresh actual unconstrained three/six-row R SAT; full source inverse, emitted wrapper binding and new FU tests. No whole-FU sequential or RTL-to-mapped SAT claim.',
        cpu_affinity=[a.cpu],nice=5,budget_seconds=a.budget_seconds,resident_modified=False,
        original_cache_modified=False,production_default_changed=False,new_core_builds=0,new_core_runs=0,
        arithmetic_equivalent=False,fu_qualified=False,parent_qualified=False,
        wrapper_post_p_decode_review_completed=False,
        fullcore_qualified=False,application_performance_qualified=False,core_cost_qualified=False,
        prefix_miters=[],generated=[],fu_results=[],cost_results=[],local_cost_recorded=False,
        no_clock_reset_latency_or_slot_protocol_change=True,internal_P_row_width_changed=True)
    save(out/'inputs.json',dict(originals=pins,snapshots=snapshots,recipe_sha256=GEN_INPUTS_SHA))
    save(out/'result.json',result)
    pending=[None]
    def interrupt(signum,frame):
        if pending[0] is None:pending[0]=signum
    def check():
        if pending[0] is not None:raise InterruptedError('received signal '+str(pending[0]))
        if time.monotonic()>=deadline:raise TimeoutError('total success budget exhausted')
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
        check();now=time.monotonic();until=min(deadline,now+limit)
        need(until>now,'total deadline before '+label)
        rec=dict(label=label,argv=list(map(str,argv)),started=util.stamp(),budget_seconds=until-now,
                 feature=env['VDOT_DOT16'],expected_exit=expected)
        result['commands'].append(rec);proc=None
        try:
            with (out/(label+'.log')).open('wb') as log:
                proc=subprocess.Popen(rec['argv'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                rec['pid']=proc.pid;save(out/'result.json',result)
                # Absolute command deadline was fixed before Popen, including launch/log overhead.
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
        classes=out/'overlay-classes';classes.mkdir()
        command('compile-source-overlay',java_base+['-cp',':'.join(cfg['compiler_paths']),'scala.tools.nsc.Main',
            '-classpath',':'.join(cfg['run_paths']),'-d',classes,*cfg['scalac_options'],
            snap/'VDotDatapath.scala',snap/'VDotElastic.scala',snap/'GenerateVDotCost.scala'],300)
        need((classes/'xiangshan/backend/fu/vector/VDotCarrySaveRows.class').is_file()
             and (classes/'xiangshan/backend/fu/vector/VDotProducts.class').is_file()
             and (classes/'xiangshan/backend/fu/vector/VDotPrefixFinish.class').is_file()
             and (classes/'xiangshan/backend/fu/wrapper/VDotElastic.class').is_file(),'real new compiled classes')
        class_pins={str(p):sha(p) for p in classes.rglob('*') if p.is_file()}
        save(out/'overlay-classes.json',class_pins)
        for feature in (0,1):
            env['VDOT_DOT16']=str(feature)
            for kind in ('cost','fu'):
                folder=out/f'{kind}-feature{feature}';rtl=folder/'rtl'
                generator='team.vdot.GenerateVDotCost' if kind=='cost' else 'team.vdot.GenerateVDotElasticFu'
                args=['fu',rtl] if kind=='cost' else [rtl]
                command(f'generate-{kind}-{feature}',java_base+['-cp',str(classes)+':'+':'.join(cfg['run_paths']),generator,*args],180)
                top='CommonFuCostTop' if kind=='cost' else 'VDotElasticFuTestTop'
                width=20 if feature else 19
                prefix_name=f'VDotPrefixFinish{width}.sv'
                expected={'VDotElastic.sv','VDotCarrySaveRows.sv',prefix_name,top+'.sv','extern_modules.sv'}
                files=sorted(rtl.glob('*.sv'))
                need({p.name for p in files}==expected,'closed four design SV files plus exact external comment file')
                previous_rtl=cbase/f'{kind}-feature{feature}'/'rtl'
                header=(previous_rtl/(top+'.sv')).read_bytes().split(('module '+top+'(').encode(),1)[0]
                csa_comment=b'// external module VDotCarrySaveRows\n\n'
                prefix_comment=f'// external module VDotPrefixFinish{width}\n\n'.encode()
                need((previous_rtl/'extern_modules.sv').read_bytes()==header+csa_comment,
                     'exact prior firtool header and sole external CSA comment')
                need((rtl/'extern_modules.sv').read_bytes() in
                     (header+csa_comment+prefix_comment,header+prefix_comment+csa_comment),
                     'only prior exact header and the two exact comments; order alone may vary')
                filelist=rtl/'filelist.f'
                listed=[(rtl/t).resolve() for t in shlex.split(filelist.read_text(),comments=True)]
                need(len(listed)==len(files) and set(listed)=={p.resolve() for p in files},'exact full generated filelist')
                need(all(b'// ----- 8< ----- FILE "' not in p.read_bytes() for p in files),'no virtual files')
                resource=rtl/'firrtl_black_box_resource_files.f'
                tokens=shlex.split(resource.read_text(),comments=True)
                resources=[(Path(t) if Path(t).is_absolute() else rtl/t).resolve() for t in tokens]
                need(len(resources)==2 and set(resources)=={(rtl/'VDotCarrySaveRows.sv').resolve(),(rtl/prefix_name).resolve()},
                     'exact complete two-module inline resource manifest')
                old_rtl=gen/f'feature{feature}'/'rtl' if kind=='cost' else fu/CPP[feature][0]/'campaign/rtl'
                need((rtl/(top+'.sv')).read_bytes()==(old_rtl/(top+'.sv')).read_bytes(),
                     'unchanged entire public common-FU consumer top')
                # The changed P representation is bound below; whole-wrapper byte reuse is not claimed.
                binding=wrapper_binding((rtl/'VDotElastic.sv').read_text(),
                    (previous_rtl/'VDotElastic.sv').read_text(),feature)
                result.setdefault('wrapper_bindings',[]).append(dict(feature=feature,kind=kind,**binding))
                storage=re.findall(r'\breg\s+\[(\d+):0\]\s+rPacket_res_data\s*;', (rtl/'VDotElastic.sv').read_text())
                need(storage==[str(19 if feature else 18)], 'exact actual result storage width')
                for p in files+[resource,filelist]:generated_pins[str(p)]=sha(p)
                result['generated'].append(dict(feature=feature,kind=kind,files=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in files],resource_manifest_sha256=sha(resource),filelist_sha256=sha(filelist)))
                save(out/'result.json',result)
        first=out/'cost-feature0/rtl'
        for row in result['generated']:
            rtl=out/f"{row['kind']}-feature{row['feature']}"/'rtl'
            need((rtl/'VDotCarrySaveRows.sv').read_bytes()==(first/'VDotCarrySaveRows.sv').read_bytes(),
                 'all four actual new CSA modules have identical complete bytes')
        for feature in (0,1):
            name=f'VDotPrefixFinish{20 if feature else 19}.sv'
            need((out/f'cost-feature{feature}/rtl'/name).read_bytes()==
                 (out/f'fu-feature{feature}/rtl'/name).read_bytes(),
                 'actual new cost/FU R bytes are identical and require fresh SAT proofs')
        need(len(result['wrapper_bindings'])==4 and
             all(x['post_p_actual_expression_verified'] for x in result['wrapper_bindings']),
             'all four actual post-P expressions bound')
        result['wrapper_post_p_decode_review_completed']=True
        # Prove the actual emitted recoder, biased heap, compressor graph and rows.
        # This verifier accepts no unparsed SV statements or hidden arithmetic.
        report=out/'arithmetic-structure.json'
        command('actual-booth-structure',[sys.executable,'-B',snap/'verify_booth.py',
            '--rtl',first/'VDotCarrySaveRows.sv','--output',report],60)
        structure=json.loads(report.read_bytes())
        need(structure['status']=='BOOTH3_CSA_STRUCTURAL_EQUIVALENCE_PASS' and
             structure['all_inputs_equivalent'] is True and structure['parsed_entire_module'] is True and
             structure['verifier']['sha256']==VERIFY_SHA and
             structure['rtl_sha256']==sha(first/'VDotCarrySaveRows.sv') and
             structure['full_adders']==272 and structure['half_adders']==19 and
             structure['actual_recode_cases']==7168 and structure['signed_byte_decomposition_cases']==256 and
             structure['layers']==list(range(7)) and structure['total_correction']==350208 and
             structure['disabled_high_half_sum']==1<<19,
             'new complete actual Booth proof with exact recode, bias and FA/HA counts')
        result['arithmetic_structure_proof']=structure
        result['arithmetic_structure_proof_reused']=False
        result['biased_unsigned_row_encoding_verified']=True
        result['direct_signed_row_encoding_verified']=False
        generated_pins[str(report)]=sha(report)
        result['historical_multiplication_miter']=dict(cb['independent_miter'])
        result['historical_multiplication_miter_source']=str(cbase)
        result['independent_miter']=dict(status='NOT_RUN',solver_equivalence_proved=False,
            retried=False,qualification_scope='new P candidate',
            reason='New actual structural proof is used; no new monolithic multiplication solver run.')
        result['prefix_miters_reused']=False
        for feature,width,row_count in ((0,19,3),(1,20,6)):
            env['VDOT_DOT16']=str(feature)
            actual=out/f'cost-feature{feature}/rtl/VDotPrefixFinish{width}.sv'
            # Exact header/ports close the harness width and input-count binding.
            # The arithmetic is read only from the real emitted DUT below.
            header=(f'module VDotPrefixFinish{width}(\n'+''.join(
                f'  input wire [{width-1}:0] rows_{i},\n' for i in range(row_count))+
                f'  output wire [{width-1}:0] result\n);\n')
            need(actual.read_bytes().startswith(b'// Generated by CIRCT firtool-1.62.1\n'+header.encode()),
                 'actual prefix module name and complete exact-width input/output header')
            folder=out/f'prefix-proof-{width}';folder.mkdir()
            gold,gate,prove=folder/'gold.sv',folder/'gate.sv',folder/'prove.ys'
            inputs=', '.join(f'input wire [{width-1}:0] a{i}' for i in range(row_count))
            ports=inputs+f', output wire [{width-1}:0] result'
            gold.write_text('module Gold('+ports+');\nassign result='+
                '+'.join(f'a{i}' for i in range(row_count))+';\nendmodule\n')
            gate.write_text('module Gate('+ports+');\n'+f'VDotPrefixFinish{width} actual('+ 
                ', '.join(f'.rows_{i}(a{i})' for i in range(row_count))+
                ', .result(result));\nendmodule\n')
            prove.write_text('\n'.join(['read_verilog -sv '+str(p) for p in (gold,gate,actual)]+
                ['miter -equiv -flatten Gold Gate miter','hierarchy -check -top miter','proc','opt','flatten',
                 'sat -verify -timeout 30 -prove trigger 0 -show-inputs -show-outputs'])+'\n')
            for p in (gold,gate,prove):generated_pins[str(p)]=sha(p)
            record=dict(feature=feature,width=width,row_count=row_count,status='RUNNING',
                actual_rtl_sha256=sha(actual),gold_sha256=sha(gold),gate_sha256=sha(gate),script_sha256=sha(prove),
                unconstrained_inputs=True,solver_timeout_seconds=30,total_command_budget_seconds=60,
                qualification_scope='actual prefix combinational modular sum only',retried=False)
            result['prefix_miters'].append(record);save(out/'result.json',result)
            label=f'actual-prefix-{width}-miter'
            try:
                log,rc=command(label,[old_cost['tools']['yosys']['path'],'-T','-s',prove],60,expected=None)
                record['exit_code']=rc
                record['log_sha256']=sha(out/(label+'.log'))
                counterexample='SAT proof finished - model found: FAIL!' in log
                solved=log.count('SAT proof finished - no model found: SUCCESS!')==1
                record['counterexample_found']=counterexample
                need(rc==0 and solved and not counterexample and 'ERROR:' not in log,
                     'new actual prefix SAT must explicitly succeed; timeout/tool error/counterexample blocks FU/cost')
                record['status']='PASS';record['solver_equivalence_proved']=True
                generated_pins[str(out/(label+'.log'))]=record['log_sha256']
            except BaseException as exc:
                record.update(status='FAILED',solver_equivalence_proved=False,error=repr(exc))
                if (out/(label+'.log')).exists():record['log_sha256']=sha(out/(label+'.log'))
                raise
            finally:
                save(out/'result.json',result)
        need(len(result['prefix_miters'])==2 and all(x['status']=='PASS' for x in result['prefix_miters']),
             'both actual emitted prefix modules proved before any FU/cost command')
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
                        ('VDotCarrySaveRows.sv',f'VDotPrefixFinish{20 if feature else 19}.sv','VDotElastic.sv','CommonFuCostTop.sv')]
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
            expected_dff=CSA_DFF_CELLS[feature]
            # Mapping can remove/recombine constant state; measured delta is evidence, not a stale estimate gate.
            log,_=command(f'sta-{feature}',[old_cost['tools']['sta']['path'],'-no_init','-exit',dest/'timing.tcl'],60)
            need(not re.search(r'(?m)^.*\bError:',log) and 'not found' not in log and
                 log.splitlines().count('DOT16_GENERATED_FU_STA_COMPLETE')==1,'complete error-free same-template STA')
            timing={n:helper.parse_path((dest/(n+'.rpt')).read_text()) for n in ('r2r','i2r','r2o','i2o','ready')}
            need(all(p['exists'] for p in timing.values()),'all five path classes exist')
            constants=helper.constant_warnings((dest/'setup-checks.rpt').read_text(),design)
            result['cost_results'].append(dict(feature=feature,cell_area=area,cell_count=sum(cells.values()),
                dff_cells=actual_dff,original_dff_cells=point['dff_cells'],
                result_storage_bits=20 if feature else 19,cell_histogram=dict(sorted(cells.items())),ports=ports,
                csa_baseline_dff_cells=expected_dff,dff_matches_csa_baseline=actual_dff==expected_dff,
                dff_delta_from_csa=actual_dff-expected_dff,
                area_delta_from_csa=area-cb['cost_results'][feature]['cell_area'],
                delta_from_csa=dict(cell_area=area-cb['cost_results'][feature]['cell_area'],
                    dff_cells=actual_dff-expected_dff,
                    timing={n:{k:timing[n][k]-cb['cost_results'][feature]['timing'][n][k]
                               for k in ('arrival_ns','slack_ns')} for n in timing}),
                dff_delta_from_rwidth=actual_dff-rb['cost_results'][feature]['dff_cells'],
                delta_from_prefix=dict(cell_area=area-pb['cost_results'][feature]['cell_area'],
                    dff_cells=actual_dff-pb['cost_results'][feature]['dff_cells'],
                    timing={n:{k:timing[n][k]-pb['cost_results'][feature]['timing'][n][k]
                               for k in ('arrival_ns','slack_ns')} for n in timing}),
                area_delta_from_rwidth=area-rb['cost_results'][feature]['cell_area'],
                area_delta_from_signed8=area-base['cost_results'][feature]['cell_area'],
                area_delta_from_matched_original=area-point['cell_area'],area_within_20000=area<=20000,
                timing=timing,reviewed_constant_endpoints=constants,
                nominal_setup_met=all(p['slack_ns']>=0 for p in timing.values()),
                mapped_sha256=sha(dest/'mapped.v'),mapped_json_sha256=sha(dest/'mapped.json')))
            save(out/'result.json',result)
        check()
        for path,h in {**pins,**snapshots,**class_pins,**generated_pins}.items():need(sha(path)==h,'unchanged pin '+path)
        need(cp_util.classpath_identity(cp_paths,repo)==cp_old,'original entire classpath remained unchanged')
        need(all(not Path(p).exists() and not Path(p).is_symlink() for p in cfg['absent_optional_resources']),
             'optional resource paths remained absent')
        need(time.monotonic()<deadline,'total budget after complete final audit')
        save(out/'final-artifact-pins.json',{**snapshots,**class_pins,**generated_pins})
        check()
        need(time.monotonic()<deadline,'total budget after final manifest and pending-signal check')
        result.update(status='BOOTH3_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE',
            arithmetic_equivalent=True,fu_qualified=True,local_cost_recorded=True,
            inputs_unchanged=True,generated_inputs_unchanged=True,original_classpath_unchanged=True,
            all_children_reaped=all(r['reaped'] and r['group_absent'] for r in result['commands']))
    except BaseException as exc:
        result.update(status='FAILED',error=repr(exc));raise
    finally:
        result['finished']=util.stamp();save(out/'result.json',result)
        if result.get('status')=='BOOTH3_GENERATED_ARITHMETIC_FU_AND_COST_COMPLETE':
            try:check()
            except BaseException as exc:
                result.update(status='FAILED',error=repr(exc),finished=util.stamp())
                save(out/'result.json',result)
                raise
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','generated','cost_results')},indent=2))
    print(json.dumps(dict(cost_results=[{k:v for k,v in x.items() if k not in ('cell_histogram','ports','reviewed_constant_endpoints')} for x in result['cost_results']]),indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','cost-root','fu-root','signed8-local','rwidth-local','csa-local','prefix-local','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,choices=[2],default=2)
    p.add_argument('--budget-seconds',type=int,default=1200)
    run(p.parse_args())
