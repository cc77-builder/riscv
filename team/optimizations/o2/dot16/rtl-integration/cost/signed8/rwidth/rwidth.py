#!/usr/bin/env python3
"""Compile exact R20/R19 result storage and run the unchanged full FU/cost checks."""
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
CONTRACT = 'dot16-signed8-result-width-local-v1'
WRAPPER_SHA = '70dcc27381d3e7226eeff333c943d35b982ec1fdd37b75b680060a13aaf94e2a'
ORIGINAL_WRAPPER_SHA = '63911b937a526b97ddaa67e34526fd19bbd2fa2801eadfda10ae6c2fa4b9fe9e'
REL_WRAPPER = 'src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala'
BASELINE_SHA = '19f90c867022ba2259b83fb2600bb56ef7066eda54023cead03c6e35bf23b7d7'
GEN_SHA = '7b45921ee1b5ff564113daa61403c4e52ecb598305aad6c093f4ab5768fe0a09'
GEN_INPUTS_SHA = 'ec29dc8725cf3a1c04ea684e2753debc1a9b2a04d37b4adadcdfe96f85ec20d8'
CP_SHA = 'd9a3071fc4f2cb1fb6766bcf3d3efdc0571bfc09986bace0b432b3b82d445902'
COST_SHA = '8c9a22771594565bfaa812309f68c84de4e8a213b02b9aba03440373f61e2e51'
SOURCE_SHA = '50522c0cd2700f7f852872049533bc31f79ce811ad2ed53da2c1d333cece45e2'
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


def run(a):
    deadline=time.monotonic()+a.budget_seconds
    os.sched_setaffinity(0,{a.cpu});os.setpriority(os.PRIO_PROCESS,0,5)
    repo,cost,fu,out=a.repo.resolve(),a.cost_root.resolve(),a.fu_root.resolve(),a.output.resolve()
    here=Path(__file__).resolve().parent
    candidate=here/'VDotDatapath.scala'
    wrapper=here/'VDotElastic.scala'
    baseline=a.signed8_local.resolve()
    need(120<=a.budget_seconds<=1800 and not out.exists(), 'fresh output and finite budget')
    for d in (repo,cost,fu,here,baseline):
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
    pin(Path(__file__));pin(here/'RWIDTH_CONTRACT.md');pin(here/'source-derivation.json')
    pin(baseline/'result.json',BASELINE_SHA)
    base=json.loads((baseline/'result.json').read_bytes())
    need(base['status']=='INLINE_SIGNED8_GENERATED_EQUIVALENT_FU_AND_COST_COMPLETE'
         and base['arithmetic_equivalent'] and base['inputs_unchanged'] and base['all_children_reaped'],
         'completed applicable signed8 source proof and cost')
    proof=json.loads((here/'source-derivation.json').read_bytes())
    need(proof['original_source_sha256']==ORIGINAL_WRAPPER_SHA and
         proof['candidate_source_sha256']==WRAPPER_SHA and proof['exact_inverse'] is True, 'fixed source derivation')
    restored=wrapper.read_text()
    for edit in reversed(proof['edits']):
        need(restored.count(edit['after'])==1, 'unique wrapper inverse edit')
        restored=restored.replace(edit['after'],edit['before'],1)
    need(restored.encode()==(repo/REL_WRAPPER).read_bytes(), 'entire actual original wrapper recovered')
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
        'rwidth.py':Path(__file__),'RWIDTH_CONTRACT.md':here/'RWIDTH_CONTRACT.md',
        'VDotElastic.scala':wrapper,'original-VDotElastic.scala':repo/REL_WRAPPER,
        'source-derivation.json':here/'source-derivation.json',
        'vectors.tsv':fu/'flag1-01/campaign/vectors.tsv'})
    for feature,(folder,_) in CPP.items():copies[f'feature{feature}-fu_test.cpp']=fu/folder/'source-snapshot/dot16_fu_test.cpp'
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
        signed8_baseline_result_sha256=BASELINE_SHA,result_widths={0:19,1:20},
        representation_equivalence_basis='Exact source-expression identity and move-enabled state induction after first write; full FU validation. No whole-FU sequential formal claim.',
        cpu_affinity=[a.cpu],nice=5,budget_seconds=a.budget_seconds,resident_modified=False,
        original_cache_modified=False,production_default_changed=False,new_core_builds=0,new_core_runs=0,
        arithmetic_equivalent=False,fu_qualified=False,parent_qualified=False,
        fullcore_qualified=False,application_performance_qualified=False,core_cost_qualified=False,
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
        classes=out/'overlay-classes';classes.mkdir()
        command('compile-source-overlay',java_base+['-cp',':'.join(cfg['compiler_paths']),'scala.tools.nsc.Main',
            '-classpath',':'.join(cfg['run_paths']),'-d',classes,*cfg['scalac_options'],
            snap/'VDotDatapath.scala',snap/'VDotElastic.scala',snap/'GenerateVDotCost.scala'],300)
        need((classes/'xiangshan/backend/fu/vector/VDotSignedByteProduct.class').is_file()
             and (classes/'xiangshan/backend/fu/vector/VDotProducts.class').is_file()
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
                expected={'VDotElastic.sv','VDotProducts.sv','VDotReduce.sv','VDotSignedByteProduct.sv',top+'.sv','extern_modules.sv'}
                files=sorted(rtl.glob('*.sv'))
                need({p.name for p in files}==expected,'closed five design SV files plus exact external comment file')
                header=(rtl/'VDotProducts.sv').read_text().split('module VDotProducts(',1)[0]
                need((rtl/'extern_modules.sv').read_text()==header+'// external module VDotSignedByteProduct\n\n',
                     'external declaration file contains only exact generated header and comment')
                filelist=rtl/'filelist.f'
                listed=[(rtl/t).resolve() for t in shlex.split(filelist.read_text(),comments=True)]
                need(len(listed)==len(files) and set(listed)=={p.resolve() for p in files},'exact full generated filelist')
                need(all(b'// ----- 8< ----- FILE "' not in p.read_bytes() for p in files),'no virtual files')
                resource=rtl/'firrtl_black_box_resource_files.f'
                tokens=shlex.split(resource.read_text(),comments=True)
                resources=[(Path(t) if Path(t).is_absolute() else rtl/t).resolve() for t in tokens]
                need(resources==[(rtl/'VDotSignedByteProduct.sv').resolve()],'exact actual inline resource manifest')
                need(len(re.findall(r'\bVDotSignedByteProduct\s+\w+\s*\(', (rtl/'VDotProducts.sv').read_text()))==8,
                     'new Products actually instantiates eight inline multipliers')
                old_rtl=gen/f'feature{feature}'/'rtl' if kind=='cost' else fu/CPP[feature][0]/'campaign/rtl'
                for name in ('VDotReduce.sv',top+'.sv'):
                    need((rtl/name).read_bytes()==(old_rtl/name).read_bytes(),'unchanged surrounding generated module '+name)
                for name in ('VDotProducts.sv','VDotSignedByteProduct.sv','VDotReduce.sv'):
                    need((rtl/name).read_bytes()==(baseline/f'{kind}-feature{feature}'/'rtl'/name).read_bytes(),
                         'all actual signed8 arithmetic unchanged from proved baseline '+name)
                storage=re.findall(r'\breg\s+\[(\d+):0\]\s+rPacket_res_data\s*;', (rtl/'VDotElastic.sv').read_text())
                need(storage==[str(19 if feature else 18)], 'exact actual result storage width')
                for p in files+[resource,filelist]:generated_pins[str(p)]=sha(p)
                result['generated'].append(dict(feature=feature,kind=kind,files=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in files],resource_manifest_sha256=sha(resource),filelist_sha256=sha(filelist)))
                save(out/'result.json',result)
        first=out/'cost-feature0/rtl'
        for row in result['generated']:
            rtl=out/f"{row['kind']}-feature{row['feature']}"/'rtl'
            for name in ('VDotProducts.sv','VDotSignedByteProduct.sv'):
                need((rtl/name).read_bytes()==(first/name).read_bytes(),'same arithmetic across all four actual consumers')
        # Reuse the already completed unconstrained product proof only after byte identity
        # of Products, inline multiplier and Reduce in all four newly emitted consumers.
        result['arithmetic_proof_reused']=dict(result_sha256=BASELINE_SHA,actual_generated_bytes_equal=True)
        result['arithmetic_proof_completed']=True
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
                prefix='read_verilog -sv -DSYNTHESIS '+str(rtl/'VDotSignedByteProduct.sv')+'\n' if name=='map.ys' else ''
                final=prefix+changed
                inverse=final[len(prefix):].replace(str(dest),str(old_dir)).replace(str(rtl),str(old_rtl))
                need(inverse==original,'mapping/STA template inverse')
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
            expected_dff=point['dff_cells']-(12 if feature else 13)
            need(actual_dff==expected_dff, 'only the exact redundant result state bits removed')
            log,_=command(f'sta-{feature}',[old_cost['tools']['sta']['path'],'-no_init','-exit',dest/'timing.tcl'],60)
            need(not re.search(r'(?m)^.*\bError:',log) and 'not found' not in log and
                 log.splitlines().count('DOT16_GENERATED_FU_STA_COMPLETE')==1,'complete error-free same-template STA')
            timing={n:helper.parse_path((dest/(n+'.rpt')).read_text()) for n in ('r2r','i2r','r2o','i2o','ready')}
            need(all(p['exists'] for p in timing.values()),'all five path classes exist')
            constants=helper.constant_warnings((dest/'setup-checks.rpt').read_text(),design)
            result['cost_results'].append(dict(feature=feature,cell_area=area,cell_count=sum(cells.values()),
                dff_cells=actual_dff,original_dff_cells=point['dff_cells'],
                result_storage_bits=20 if feature else 19,cell_histogram=dict(sorted(cells.items())),ports=ports,
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
        result.update(status='SIGNED8_RESULT_WIDTH_GENERATED_FU_AND_COST_COMPLETE',
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
    for name in ('repo','cost-root','fu-root','signed8-local','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu',type=int,choices=range(4),default=1)
    p.add_argument('--budget-seconds',type=int,default=1200)
    run(p.parse_args())
