"""Recompute a completed O1 campaign from raw logs; never launches an EMU.

The caller must authenticate the enclosing archive/input inventory separately.
This entry checks each runtime receipt and recomputes functional/trace evidence.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re

from check_trace import require
from check_extended import extended_audit
from run_extended_core import ROOT, module, matrix_union
from run_trace_core import control_check, sha
from evidence_output import require_new_output, write_new_json


def recheck(folder):
    inventory=json.loads((folder/'software.json').read_text())['files']
    images=folder/'images'
    require(all(sha(images/n)==h for n,h in inventory.items()),'archived software changed')
    matrix=matrix_union(images)
    functional=module('recheck_functional',ROOT/'team/scripts/check-vdot-run.py')
    negative=module('recheck_negative',ROOT/'team/scripts/check-vdot-negative.py')
    perf=module('recheck_perf',ROOT/'team/workloads/vdot-perf/check.py')
    pins=json.loads((folder/'inputs.json').read_text())
    emus={p:h for p,h in pins.items() if p.endswith('/build/emu')}
    refs={p:h for p,h in pins.items() if p.endswith('/riscv64-nemu-interpreter-so')}
    require(len(emus)==len(refs)==1,'missing/ambiguous hardware/reference pins')
    emu=next(iter(emus));ref=next(iter(refs))
    require(refs[ref]=='e8c9c9be7d798a348a0f8c5ad3a4c601c27511a1967ca3c4cc0af576233f52a1','wrong reviewed reference')
    jobs=['hello','control','calibration','batch128']+[f'matrix-{i}' for i in range(8)]+['negative']
    results={}
    image_map={'hello':'hello-vadd.bin','control':'control-pressure-v2/vdot-regression.bin',
               'calibration':'calibration/vdot-perf.bin','batch128':'t13-images/performance-d0-s06/vdot-perf.bin',
               'negative':'matrix/build-0/vdot-exceptions.bin'}
    image_map.update({f'matrix-{i}':f'matrix/build-{i}/vdot-exceptions.bin' for i in range(8)})
    for name in jobs:
        directory=folder/name
        record=json.loads((directory/'runtime.json').read_text())
        require(record['name']==name and record['files']==pins,'runtime pins differ')
        require(record['image_sha256']==inventory[image_map[name]],'wrong executed image')
        require(set(record['raw_sha256'])=={'stdout.log','stderr.log'} and
                all(sha(directory/n)==h for n,h in record['raw_sha256'].items()),'raw log drift')
        command=record['command']
        require(command[:4]==['timeout','60m','stdbuf','-o0'] and command[4]=='-e0','wrong runtime wrapper')
        roles=perf.runtime_roles(command[5:])
        selected_ref=next(p for p,h in pins.items() if p.endswith('/negative-reference-v2.so')) if name=='negative' else ref
        require(roles['emu']==emu and roles['reference']==selected_ref and
                roles['image'].endswith('/images/'+image_map[name]) and
                pins[roles['flash']]==inventory['boot-flash.bin'],'runtime roles differ')
        require(record['reference_sha256']==pins[selected_ref],'runtime reference hash differs')
        require(record['environment']=={'XS_NEGATIVE_VECTOR_TARGET':'vdot' if name=='negative' else None},'wrong fault environment')
        stdout=(directory/'stdout.log').read_text();stderr=(directory/'stderr.log').read_text();text=stderr+stdout
        require(text.count('Difftest enabled.')==1 and 'The reference model is '+selected_ref in text,'missing actual reference banner')
        rc=record['exit_code']
        if name=='negative':
            results[name]=negative.check(text,rc);continue
        require(rc==0 and stdout.count('HIT GOOD TRAP')==1 and not re.search(r'BAD TRAP|Assertion.*failed|different at pc|DIFFTEST FAIL|ABORT',text),'runtime failure')
        trace,events=extended_audit(stderr.splitlines(),vdot=name!='hello')
        if name=='hello':
            require(stdout.count('HELLO_VADD_PASS')==1,'hello failure')
            result=dict(status='O1_HELLO_PASS')
        elif name=='control':
            manifest=json.loads((images/'control-pressure-v2/data/manifest.json').read_text())
            old=control_check(text,trace['protocol'],manifest,rc)
            coverage=dict(old['coverage'],repeated_ftq_wrap=trace['ftq'].get('wraps',0)>=8)
            require(all(coverage.values()),'incomplete control coverage')
            result=dict(status='O1_CONTROL_COVERAGE_PASS',coverage=coverage,committed=old['expected_vdot_commits'])
        elif name.startswith('matrix-'):
            result=functional.validate(stdout,'full',rc,images/f'matrix/data-{name[-1]}',require_diff=True)
        else:
            build=images/Path(image_map[name]).parent
            manifest=json.loads((build/'data/manifest.json').read_text())
            perf.verify_build_record(build);perf.verify_generation(build,manifest)
            perf.check_compiled_cases(build/'vdot-perf.elf',manifest)
            samples=perf.trace_windows(events,manifest,perf.elf_kernels(build/'vdot-perf.elf'))
            perf.check_uart(stdout,manifest,samples)
            expected=sum(manifest['rows'][p['index']]['dots'] for p in manifest['plan'] if manifest['rows'][p['index']]['method']=='vdot')
            require(trace['protocol']['rob']['committed']==expected,'wrong architectural VDot count')
            result=dict(status='O1_CALIBRATED_WINDOWS_PASS',samples=samples,vdot_committed=expected,performance_ab=False)
        results[name]=dict(result=result,trace=trace)
    require(sum(results[f'matrix-{i}']['result']['executed'] for i in range(8))==124,'matrix execution count differs')
    failed=json.loads((folder/'negative/runtime.json').read_text())
    recovered=json.loads((folder/'matrix-0/runtime.json').read_text())
    require(failed['image_sha256']==recovered['image_sha256'] and
            datetime.fromisoformat(failed['finished'])<=datetime.fromisoformat(recovered['started']),
            'normal-reference recovery does not follow the identical-image injection')
    return dict(status='O1_EXTENDED_OFFLINE_RECHECK_PASS',new_cpu_runs=0,archived_cpu_runs=13,
                emu_sha256=emus[emu],matrix=matrix,results=results,default_o1=False,performance_ab=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    require_new_output(a.output)
    result=recheck(a.run)
    write_new_json(a.output,result)
    print(result['status'])
