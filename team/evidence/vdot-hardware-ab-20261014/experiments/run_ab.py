#!/usr/bin/env python3
"""Run REAL Chisel/FU A/B in the task's isolated Linux repository only.

No model replacement, handwritten RTL, CPU build, submodule mutation, network
setup, branch publication, or production configuration promotion occurs here.
The explicit experiment patch must already have been applied and reviewed.
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone

BASE_SHA = '6bf3c2c3be0c88ff3a020786ff10cbec9aa126d3'
EXPECTED_REPO = Path('/home/lizufan/xiangshan-t12-perf-20261014/hardware-repo')
EXPECTED_RUNS = Path('/home/lizufan/xiangshan-t12-perf-20261014/hardware-runs')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def trace_metrics(path):
    accepted, responses, first_valid, first_post_valid = [], [], {}, {}
    pending = None
    with path.open(newline='') as source:
        for row in csv.DictReader(source, delimiter='\t'):
            if row['label'] != 'all-vectors-with-backpressure':
                continue
            cycle = int(row['cycle'])
            if row['in_valid'] == '1' and row['in_ready'] == '1':
                if pending is not None:
                    raise RuntimeError('trace contains concurrent requests')
                pending = cycle
                accepted.append(cycle)
            if row['post_edge_out_valid'] == '1' and pending is not None:
                first_post_valid.setdefault(pending, cycle)
            if row['out_valid'] == '1':
                if pending is None:
                    raise RuntimeError('trace output without accepted request')
                first_valid.setdefault(pending, cycle)
                if row['out_ready'] == '1':
                    responses.append(cycle - pending)
                    pending = None
    if len(accepted) != 10022 or len(responses) != 10022 or pending is not None:
        raise RuntimeError('trace arithmetic transaction conservation failed')
    def histogram(values):
        return {str(v): values.count(v) for v in sorted(set(values))}
    return {'arithmetic_accepted':len(accepted), 'arithmetic_responded':len(responses),
            'first_post_edge_valid_delta_histogram':histogram([first_post_valid[c]-c for c in accepted]),
            'first_pre_edge_valid_delta_histogram':histogram([first_valid[c]-c for c in accepted]),
            'response_handshake_delta_histogram':histogram(responses),
            'accept_interval_histogram':histogram([b-a for a,b in zip(accepted,accepted[1:])]),
            'minimum_accept_interval':min(b-a for a,b in zip(accepted,accepted[1:]))}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True,help='fresh directory under hardware-runs')
    parser.add_argument('--firtool-dir',type=Path,required=True)
    parser.add_argument('--xs-env',type=Path,required=True,help='actual read-verified existing xs-env root')
    parser.add_argument('--structural-proxy',action='store_true',help='optional generic Yosys cells; NOT physical PPA')
    args=parser.parse_args()
    repo=args.repo.resolve()
    out=args.out.resolve()
    if platform.system() != 'Linux' or repo != EXPECTED_REPO:
        parser.error('requires the exact authorized isolated Linux hardware-repo')
    if out == EXPECTED_RUNS or EXPECTED_RUNS not in out.parents or out.exists():
        parser.error('output must be a NEW descendant of the authorized hardware-runs')
    if not (args.xs_env/'NEMU').is_dir() or not (args.xs_env/'nexus-am').is_dir():
        parser.error('verify and provide the actual existing xs-env; no guessed default')
    exp=Path(__file__).resolve().parent
    hashes=json.loads((exp/'patch-sources.json').read_text())
    for p,item in hashes.items():
        normalized=(repo/p).read_text(encoding='utf-8').encode()
        if hashlib.sha256(normalized).hexdigest() != item['candidate_sha256_lf']:
            parser.error('experiment patch absent or changed: '+p)
    for name in ['git','java','mill','python3','verilator','clang++','bash']:
        if shutil.which(name) is None:
            parser.error('missing actual executable: '+name)
    firtool=args.firtool_dir.resolve()/'firtool'
    if not firtool.is_file():
        parser.error('missing real firtool')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    subprocess.run(['git','merge-base','--is-ancestor',BASE_SHA,head],cwd=repo,check=True)
    controlled_paths=['src','build.sc','build.sbt','.gitmodules','team/models/vdot','team/rtl/vdot']
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE_SHA,'--',*controlled_paths],cwd=repo,text=True).splitlines())
    if changed != set(hashes):
        parser.error('source A/B differs from baseline outside the two experiment patch paths: '+repr(changed))
    submodules=subprocess.check_output(['git','submodule','status','--recursive'],cwd=repo,text=True)
    if any(line.startswith(('-', '+', 'U')) for line in submodules.splitlines()):
        parser.error('submodule versions are incomplete or differ from source pins')
    available_kib=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
    if available_kib < 6*1024*1024:
        parser.error('less than 6GiB currently available; coordinate with primary workload before rerun')
    out.mkdir(parents=True)
    env=os.environ.copy()
    env.update(CHISEL_FIRTOOL_PATH=str(firtool.parent),JAVA_OPTS='-Xmx4G -Xss8m',BUILD_JOBS='1',
               TEAM_XS_ENV_ROOT=str(args.xs_env.resolve()),OMP_NUM_THREADS='1')
    receipt={'timestamp':datetime.now(timezone.utc).isoformat(),'base_sha':BASE_SHA,'source_head':head,
             'repo':str(repo),'out':str(out),'fullcore_build':False,'jobs':1,'steps':[],
             'platform':platform.platform(),'uid':os.getuid(),'username':subprocess.check_output(['id','-un'],text=True).strip(),
             'mem_available_kib':available_kib,'env_overrides':{k:env[k] for k in ['CHISEL_FIRTOOL_PATH','JAVA_OPTS','BUILD_JOBS','TEAM_XS_ENV_ROOT','OMP_NUM_THREADS']}}
    (out/'submodules.txt').write_text(submodules)
    source_paths=['build.sc','src/main/scala/xiangshan/backend/fu/wrapper/VDot.scala','src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala',
                  'src/main/scala/xiangshan/backend/fu/FuConfig.scala','src/main/scala/xiangshan/backend/fu/FuncUnit.scala',
                  'src/main/scala/xiangshan/backend/rob/RobBundles.scala','team/rtl/vdot/GenerateVDotFu.scala',
                  'team/models/vdot/data/manifest.json','team/models/vdot/data/directed.jsonl','team/models/vdot/data/random.jsonl']
    receipt['source_sha256']={p:digest(repo/p) for p in source_paths}
    receipt['experiment_sha256']={p.name:digest(p) for p in exp.iterdir() if p.is_file()}
    def persist():
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    def run(name,argv,expected=0,extra_env=None):
        print('START '+name,flush=True)
        cmd_env=env.copy()
        if extra_env: cmd_env.update(extra_env)
        start=time.monotonic()
        log=out/(name+'.log')
        with log.open('wb') as stream:
            result=subprocess.run([str(v) for v in argv],cwd=repo,env=cmd_env,stdout=stream,stderr=subprocess.STDOUT)
        step={'name':name,'argv':[str(v) for v in argv],'elapsed_seconds':round(time.monotonic()-start,6),
              'exit_code':result.returncode,'expected_exit_code':expected,'log':log.name,
              'status':'PASS' if result.returncode==expected else 'FAIL'}
        receipt['steps'].append(step)
        persist()
        if result.returncode != expected:
            raise RuntimeError(name+' unexpected exit; see '+str(log))
        return log.read_text(errors='replace')
    persist()
    try:
        run('git-status',['git','status','--short'])
        run('resources',['bash','-c','id; uname -a; free -h; ps -eo pid,ppid,comm,pcpu,pmem,rss --sort=-rss | head -20'])
        for name,cmd in [('java',['java','-version']),('mill',['mill','--version']),('firtool',[firtool,'--version']),
                         ('verilator',['verilator','--version']),('clang',['clang++','--version']),('python',['python3','--version'])]:
            run(name+'-version',cmd)
        run('original-model',['bash','team/scripts/check-vdot-model.sh'])
        run('original-datapath',['bash','team/scripts/check-vdot-datapath.sh'],extra_env={'VDOT_OUT_DIR':str(out/'original-datapath')})
        run('original-default-FU',['bash','team/scripts/check-vdot-fu.sh'],extra_env={'VDOT_OUT_DIR':str(out/'original-default-FU')})
        run('vectors',['python3','-B','team/rtl/vdot/prepare_vectors.py','team/models/vdot/data',out/'vectors.tsv'])
        metrics={}
        for variant,latency in [('baseline',3),('fused',2)]:
            rtl=out/variant/'rtl'
            rtl.mkdir(parents=True)
            argsv=['mill','-i','-j','1','vdotFu.runMain','team.vdot.GenerateVDotFu',rtl]
            if variant=='fused': argsv.append('--fuse-input-stage')
            run(variant+'-elaboration',argsv)
            sv=rtl/'VDotFuTestTop.sv'
            receipt.setdefault('generated_rtl_sha256',{})[variant]=digest(sv)
            obj=out/variant/'obj_dir'
            run(variant+'-verilator-build',['verilator','--cc','--exe','--build','--assert','--top-module','VDotFuTestTop',
                  '--Mdir',obj,'-j','1','-CFLAGS',f'-std=c++17 -O2 -DVDOT_RESPONSE_LATENCY={latency}',sv,exp/'fu_ab_test.cpp'])
            binary=obj/'VVDotFuTestTop'
            trace=out/variant/'trace.tsv'
            text=run(variant+'-AB-regression',[binary,out/'vectors.tsv'],extra_env={'VDOT_AB_TRACE':str(trace)})
            if 'VDOT_FU_PASS groups=6' not in text:
                raise RuntimeError('missing FU completion marker')
            metrics[variant]=trace_metrics(trace)
            if metrics[variant]['first_post_edge_valid_delta_histogram'] != {str(latency-1):10022} or metrics[variant]['minimum_accept_interval'] != latency+1:
                raise RuntimeError('trace timing disagrees with declared interface')
            for fault in ['identity','cancel-leak','drop']:
                text=run(variant+'-negative-'+fault,[binary,out/'vectors.tsv','--inject-'+fault],expected=1)
                if 'VDOT_FU_FAULT_INJECTION '+fault not in text or 'VDOT_FU_FAIL case=' not in text:
                    raise RuntimeError('negative control failed for '+fault)
            text=run(variant+'-invalid-vlen',argsv+['--invalid-vlen'],expected=1)
            if 'VDot requires VLEN=128' not in text:
                raise RuntimeError('VLEN guard failed')
            with trace.open('rb') as source, gzip.open(str(trace)+'.gz','wb') as dest:
                shutil.copyfileobj(source,dest)
            receipt.setdefault('raw_trace_sha256',{})[variant]=digest(trace)
            if args.structural_proxy:
                if shutil.which('yosys'):
                    run(variant+'-yosys-structural-proxy',['yosys','-p',f'read_verilog -sv {sv}; hierarchy -top VDotFuTestTop; flatten; synth -top VDotFuTestTop; stat -json'])
                else:
                    receipt['steps'].append({'name':variant+'-yosys-structural-proxy','status':'NOT_RUN','reason':'yosys unavailable'})
        receipt['metrics']=metrics
        receipt['status']='LOCAL_REAL_FU_AB_PASS_NOT_PROMOTED'
        receipt['STA']='NOT_RUN'
        receipt['fullcore_diffTest']='NOT_RUN'
    except Exception as error:
        receipt['status']='FAIL'
        receipt['error']=str(error)
        raise
    finally:
        persist()

if __name__=='__main__':
    main()