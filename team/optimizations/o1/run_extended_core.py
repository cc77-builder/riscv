#!/usr/bin/env python3
"""Source-bound O1 FTQ/counter calibration, full matrix and real DiffTest fault.

Frozen software is extracted from the independently pinned historical archive.
Historical observer gates remain unchanged; no performance A/B is claimed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile

from check_extended import extended_audit
from check_trace import require
from run_trace_core import ROOT, ARCHIVE_SHA256, control_check, now, save, sha


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def extract_images(out):
    archive=ROOT/'team/evidence/james-fullcore-20261016/workloads.tar.gz'
    require(sha(archive)==ARCHIVE_SHA256,'frozen software archive changed')
    prefixes=('matrix/','calibration/','control-pressure-v2/','t13-images/performance-d0-s06/')
    single={'boot-flash.bin','hello-vadd.bin','negative-reference-v2.so'}
    out.mkdir()
    inventory={}; total=0
    with tarfile.open(archive,'r:gz') as source:
        for member in source:
            if not (member.name.startswith(prefixes) or member.name in single):continue
            name=PurePosixPath(member.name)
            require(member.isfile() and not name.is_absolute() and '..' not in name.parts
                    and member.name not in inventory,'unsafe/duplicate software member')
            total+=member.size; require(total<1024**3,'software archive exceeds bound')
            target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.extractfile(member).read())
            inventory[member.name]=sha(target)
    require(inventory.get('negative-reference-v2.so')=='8b16e687e672339126bb94cc111531030c607006730d299fcbd4af99c753cd5b','wrong negative reference fixture')
    return inventory


def matrix_union(images):
    parent=ROOT/'team/evidence/t10-t11-fullcore-20261013/parent'
    expected=[json.loads(x) for x in (parent/'cases.jsonl').read_text().splitlines()]
    expected+=json.loads((parent/'exceptions.json').read_text())
    by_id={x['id']:x for x in expected};seen={};total=0
    for index in range(8):
        data=images/f'matrix/data-{index}'
        cases=[json.loads(x) for x in (data/'cases.jsonl').read_text().splitlines()]
        cases+=json.loads((data/'exceptions.json').read_text())
        for case in cases:
            require(case==by_id.get(case['id']),'matrix differs from independent parent corpus')
            require(case['id'] not in seen or case['id']=='D00','unexpected repeated matrix case')
            seen[case['id']]=case;total+=1
    require(len(seen)==117 and set(seen)==set(by_id) and total==124,'incomplete matrix')
    return dict(unique=117,executions=124,legal=80,exceptions=37,repeated_control='D00',
                parent={p.name:sha(p) for p in (parent/'cases.jsonl',parent/'exceptions.json')})


def build_guard(args, out, phase):
    build=args.receipt;emu=args.core/'build/emu'
    for name in ('build.status','split-build.status'):
        require((build/name).read_text().strip()=='exit_code=0','unfinished/failed core build')
    require('CORE_BASELINE_BUILD_PASS' in (build/'build.log').read_text() and
            'CORE_SPLIT_BUILD_PASS' in (build/'split-build.log').read_text(),'missing build completion')
    env=(build/'environment.txt').read_text().splitlines()
    for item in ('VDOT_O1_TRACE=1','VDOT_O1_HANDOFF=1','VDOT_T14_FUSED_INPUT=1','VDOT_T12_TRACE=0','VDOT_T13_TRACE=0'):
        require(item in env,'wrong hardware observer flags')
    require(sha(emu)==(build/'emu.sha256').read_text().split()[0],'EMU differs from build')
    require((build/'source-binding.json').read_bytes()==(args.core/'build/source-binding.json').read_bytes(),'wrong source receipt')
    binding=json.loads((build/'source-binding.json').read_text())
    profile=json.loads((build/'compile-profile.json').read_text())
    require(profile==json.loads((args.core/'build/emu-compile/core-compile-profile.json').read_text()) and
            profile['source_pack_sha256']==binding['source_pack_sha256']==sha(args.pack/'source-pack.json') and
            profile['rtl_manifest_sha256']==sha(build/'rtl.sha256') and
            (profile['config'],profile['num_cores'],profile['emu_threads'])==('MinimalConfig',1,1),'wrong compile profile')
    commands=[['python3','-B',str(ROOT/'team/scripts/prepare-core-baseline.py'),'verify',
               '--source',str(ROOT),'--pack',str(args.pack),'--target',str(args.core)],
              ['sha256sum','-c',str(build/'rtl.sha256')]]
    for index,command in enumerate(commands):
        with (out/f'{phase}-{index}.log').open('wb') as log:
            subprocess.run(command,cwd=args.core,stdout=log,stderr=subprocess.STDOUT,check=True)


def run(args):
    out=args.output;out.mkdir(parents=True,exist_ok=False)
    args.created_output=True
    save(out/'campaign.json',dict(status='PREPARING',started=now()))
    scripts=ROOT/'team/scripts'
    perf=module('extended_perf',ROOT/'team/workloads/vdot-perf/check.py')
    functional=module('extended_functional',scripts/'check-vdot-run.py')
    negative=module('extended_negative',scripts/'check-vdot-negative.py')
    sys.path.insert(0,str(scripts));import artifact_guard
    build_guard(args,out,'before')
    ref=args.reference_root/'build/riscv64-nemu-interpreter-so'
    save(out/'reference-before.json',artifact_guard.verify_nemu(args.reference_root,ref,'reference'))
    images=out/'images';inventory=extract_images(images)
    save(out/'software.json',dict(archive_sha256=ARCHIVE_SHA256,files=inventory))
    union=matrix_union(images);save(out/'matrix-union.json',union)
    emu=args.core/'build/emu';flash=images/'boot-flash.bin';badref=images/'negative-reference-v2.so'
    # The archived shim links the real reference. Verify the resolved dependency,
    # not just the shim's outer digest, before accepting a genuine mismatch.
    dep=subprocess.run(['ldd',str(badref)],capture_output=True,text=True,check=True)
    (out/'negative-dependencies.txt').write_text(dep.stdout+dep.stderr)
    require('not found' not in dep.stdout and str(ref) in dep.stdout,'negative shim uses unavailable/different reference')
    code=[Path(__file__),Path(__file__).with_name('check_extended.py'),Path(__file__).with_name('check_trace.py'),
          Path(__file__).with_name('run_trace_core.py'),scripts/'check-vdot-run.py',scripts/'check-vdot-negative.py',
          scripts/'artifact_guard.py',ROOT/'team/workloads/vdot-perf/check.py']
    pins={str(p):sha(p) for p in code+[emu,ref,badref,flash]}
    for name in ('source-binding.json','compile-profile.json','environment.txt','rtl.sha256','emu.sha256'):
        pins[str(args.receipt/name)]=sha(args.receipt/name)
    save(out/'inputs.json',pins)
    jobs=[('hello',images/'hello-vadd.bin',None,ref),('control',images/'control-pressure-v2/vdot-regression.bin',None,ref),
          ('calibration',images/'calibration/vdot-perf.bin',images/'calibration',ref),
          ('batch128',images/'t13-images/performance-d0-s06/vdot-perf.bin',images/'t13-images/performance-d0-s06',ref)]
    jobs += [(f'matrix-{i}',images/f'matrix/build-{i}/vdot-exceptions.bin',images/f'matrix/data-{i}',ref) for i in range(8)]
    jobs.append(('negative',jobs[4][1],None,badref))
    for name,image,data,reference in jobs:
        require(image.is_file() and sha(image)==inventory[image.relative_to(images).as_posix()],'missing/changed image')
        if name in ('calibration','batch128'):
            manifest=json.loads((data/'data/manifest.json').read_text())
            perf.verify_build_record(data)
            perf.verify_generation(data,manifest)
            perf.check_compiled_cases(data/'vdot-perf.elf',manifest)
    def job(name,image,data,reference):
        folder=out/name;folder.mkdir()
        command=['timeout','60m','stdbuf','-o0','-e0',str(emu),'-i',str(image),'--flash='+str(flash),
                 '--ram-size=128MB','--diff='+str(reference),'--max-cycles=5000000','--seed=1']
        record=dict(name=name,status='RUNNING',started=now(),command=command,cwd=str(args.core),
                    image_sha256=sha(image),reference_sha256=sha(reference),files=pins,
                    environment={'XS_NEGATIVE_VECTOR_TARGET':'vdot' if name=='negative' else None})
        save(folder/'runtime.json',record)
        try:
            env=dict(os.environ);env.pop('XS_NEGATIVE_VECTOR_TARGET',None)
            if name=='negative':env['XS_NEGATIVE_VECTOR_TARGET']='vdot'
            with (folder/'stdout.log').open('wb') as stdout,(folder/'stderr.log').open('wb') as stderr:
                rc=subprocess.run(command,cwd=args.core,env=env,stdout=stdout,stderr=stderr).returncode
            record.update(exit_code=rc,finished=now(),raw_sha256={n:sha(folder/n) for n in ('stdout.log','stderr.log')})
            save(folder/'runtime.json',record)
            require(all(sha(Path(p))==digest for p,digest in pins.items()),'runtime/code input changed')
            stdout=(folder/'stdout.log').read_text();stderr=(folder/'stderr.log').read_text();text=stderr+stdout
            require(text.count('Difftest enabled.')==1 and 'The reference model is '+str(reference) in text,'missing/wrong live DiffTest')
            if name=='negative':
                result=negative.check(text,rc)
            else:
                require(rc==0 and stdout.count('HIT GOOD TRAP')==1 and not re.search(r'HIT BAD TRAP|Assertion.*failed|different at pc|DIFFTEST FAIL|ABORT',text),'core runtime failure')
                trace,events=extended_audit(stderr.splitlines(),vdot=name!='hello')
                save(folder/'trace.json',trace)
                if name=='hello':
                    require(stdout.count('HELLO_VADD_PASS')==1,'hello smoke failed')
                    result=dict(status='O1_HELLO_PASS')
                elif name=='control':
                    manifest=json.loads((images/'control-pressure-v2/data/manifest.json').read_text())
                    old=control_check(text,trace['protocol'],manifest,rc)
                    coverage=dict(old['coverage'],repeated_ftq_wrap=trace['ftq'].get('wraps',0)>=8)
                    require(all(coverage.values()),'incomplete control coverage')
                    result=dict(status='O1_CONTROL_COVERAGE_PASS',coverage=coverage,committed=old['expected_vdot_commits'])
                elif name.startswith('matrix-'):
                    result=functional.validate(stdout,'full',rc,data,require_diff=True)
                else:
                    manifest=json.loads((data/'data/manifest.json').read_text())
                    samples=perf.trace_windows(events,manifest,perf.elf_kernels(data/'vdot-perf.elf'))
                    perf.check_uart(stdout,manifest,samples)
                    expected=sum(manifest['rows'][p['index']]['dots'] for p in manifest['plan'] if manifest['rows'][p['index']]['method']=='vdot')
                    require(trace['protocol']['rob']['committed']==expected,'VDot count differs from compiled plan')
                    result=dict(status='O1_CALIBRATED_WINDOWS_PASS',samples=samples,vdot_committed=expected,performance_ab=False)
            save(folder/'checked.json',result);record['status']=result['status']
        except Exception as error:record.update(status='FAILED',error=repr(error),finished=now())
        save(folder/'result.json',record);print(name,record['status'],record.get('error',''),flush=True)
        return record
    # Run the injected reference first. The identical normal-reference shard is
    # then an actual recovery run, rather than an earlier unrelated success.
    records=[job(*jobs[-1])]
    save(out/'progress.json',records)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(job,*j) for j in jobs[:-1]]
        for future in as_completed(futures):
            records.append(future.result());save(out/'progress.json',records)
    build_guard(args,out,'after')
    save(out/'reference-after.json',artifact_guard.verify_nemu(args.reference_root,ref,'reference'))
    require(all(sha(images/n)==digest for n,digest in inventory.items()),'software artifact drift')
    by_name={r['name']:r for r in records}
    require(by_name['negative']['image_sha256']==by_name['matrix-0']['image_sha256'],'negative recovery image mismatch')
    require(datetime.fromisoformat(by_name['negative']['finished'])<=datetime.fromisoformat(by_name['matrix-0']['started']),
            'normal reference recovery ran before the negative control')
    passed=len(records)==13 and all(r['status']!='FAILED' for r in records)
    result=dict(status='O1_CONTROL_MATRIX_COUNTER_PASS' if passed else 'FAILED',finished=now(),
                emu_sha256=sha(emu),matrix=union,runs=records,default_o1=False,performance_ab=False)
    save(out/'campaign.json',result)
    return 0 if passed else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('core','receipt','pack','reference-root','output'):
        parser.add_argument('--'+name,type=lambda x:Path(x).resolve(),required=True)
    parser.add_argument('--jobs',type=int,choices=(1,2,4),default=2)
    args=parser.parse_args()
    try:code=run(args)
    except Exception as error:
        if getattr(args,'created_output',False):
            failure=dict(status='FAILED',error=repr(error),finished=now())
            save(args.output/'failure.json',failure)
            # Preserve completed jobs, including expected and unexpected failures.
            progress=args.output/'progress.json'
            if progress.is_file():failure['runs']=json.loads(progress.read_text())
            save(args.output/'campaign.json',failure)
        raise
    raise SystemExit(code)
