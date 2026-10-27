"""Audit the bounded 300k-cycle probe; deliberately never qualify full forward."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import resource
import struct
import time

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
s=load('consumer_probe_stream',HERE/'stream_audit.py')
t=load('consumer_probe_inputs',HERE/'target_run.py')
need,read,save=t.need,t.read,t.save
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def run(probe,output):
    need(not output.exists() and not output.is_relative_to(s.REPO) and not output.is_relative_to(probe),'fresh isolated partial audit')
    receipt=read(probe/'result.json');files=read(probe/'runtime-inputs.json')
    cfg=read(probe/'configuration.json');identity=read(probe/'parent-identity.json')
    unused,runtime=t.r.r.parent.runtime(s.REPO,identity)
    need(cfg==identity['configuration'],'same fixed parent configuration');runtime.verify_files(files)
    need(receipt['status']=='TARGET_PROCESS_EXITED_REQUIRES_RAW_AUDIT' and receipt['process_started'] is True and
         receipt['process_group_absent_after_exit'] is True and receipt['direct_child_reaped'] is True and
         not receipt.get('residual_process_group') and not receipt.get('timed_out') and receipt['exit_code']==0,'complete bounded probe process receipt')
    expected=[str(Path(cfg['hardware_source'])/'build/emu'),'-i',str(probe/'image.bin'),'--flash='+cfg['flash'],
              '--ram-size=128MB','--diff='+cfg['reference'],'--max-cycles=300000','--seed=1','--log-end=0']
    need(receipt['method']==4 and receipt['negative'] is False and receipt['max_cycles']==300000 and
         receipt['command']==expected,'exact original DiffTest probe argv without omitted/extra switches')
    paths=[probe/'stderr.log',probe/'stdout.log']
    for p in paths:need(sha(p)==receipt['raw_sha256'][p.name] and p.stat().st_size==receipt['raw_bytes'][p.name],'complete original raw log identity')
    elfpaths=[Path(p) for p in files if p.endswith('/consumer-target.elf')]
    need(len(elfpaths)==1,'one actual target harness ELF');elfpath=elfpaths[0];build=elfpath.parent
    fixed=read(build/'result.json');control=read(probe/'image-control.json')
    need(control['controls']==[4,0,1] and control['offset']==fixed['control_offset'] and
         control['base_sha256']==fixed['artifacts']['consumer-target.bin'],'actual explicit probe control')
    image=bytearray((build/'consumer-target.bin').read_bytes());image[control['offset']:control['offset']+12]=struct.pack('<3I',4,0,1)
    need(hashlib.sha256(image).hexdigest()==control['sha256']==sha(probe/'image.bin'),'exact target image except allowed control words');del image
    for p in (*paths,probe/'result.json',probe/'runtime-inputs.json',probe/'configuration.json',probe/'image-control.json',
              probe/'parent-identity.json',HERE/'audit_probe.py',HERE/'stream_audit.py'):
        key=str(p);value=sha(p);need(key not in files or files[key]==value,'no probe identity rebinding');files[key]=value
    runtime.verify_files(files);output.mkdir(parents=True);save(output/'inputs.json',files)
    start=time.monotonic();protocol,uart,counters=s.audit_files(paths,require_complete=False)
    streaming_elapsed=time.monotonic()-start;streaming_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    need(protocol['status']=='O2_PARTIAL_TRACE_AUDIT' and protocol['unfinished_rob_count']>0,'explicit unfinished prefix')
    save(output/'protocol.json',protocol);(output/'uart.txt').write_text(uart);(output/'counter-source.txt').write_text(counters)
    # A one-time old-reader comparison bounds this qualification to the actual
    # probe. Production audit_files does not allocate either whole string/list.
    start=time.monotonic();stderr,stdout=[p.read_text() for p in paths];text=stderr+stdout
    legacy=s.old.analyze(text,require_complete=False);transactions=legacy.pop('transactions')
    h=hashlib.sha256()
    for row in transactions:h.update((json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode())
    need(len(transactions)==protocol['transaction_count'] and h.hexdigest()==protocol['transaction_sha256'],'every canonical ordered transaction identical by count/SHA256')
    need(legacy=={k:v for k,v in protocol.items() if k not in ('transaction_count','transaction_sha256','storage')},'exact original partial summary')
    legacy_elapsed=time.monotonic()-start;legacy_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    try:s.old.analyze(text,require_complete=True)
    except ValueError as error:complete_rejection=str(error)
    else:raise ValueError('incomplete prefix unexpectedly qualified as complete')
    del legacy,transactions
    banner=load('consumer_probe_banner',s.REPO/'team/optimizations/o2/fullcore/run_suite.py')
    fatal=load('consumer_probe_fatal',s.REPO/'team/optimizations/o2/fullcore/recheck.py')
    gate=load('consumer_probe_failure',s.REPO/'team/optimizations/o1/audit/runtime_gate.py')
    banner.validate_runtime(text,cfg['reference'])
    for value,expected_limits in ((stderr,0),(stdout,1),(uart,1)):
        fatal.reject_fatal_output(value);normalized=gate.normalize_console(value);kept=[];limits=0
        for line in normalized.splitlines():
            if 'EXCEEDING CYCLE/INSTR LIMIT' in line:
                need(re.fullmatch(r'Core 0: EXCEEDING CYCLE/INSTR LIMIT at pc = 0x[0-9a-f]+',line) is not None,'sole canonical expected cycle-limit line')
                limits+=1
            else:kept.append(line)
        need(limits==expected_limits,'exact expected partial-limit occurrence per raw/reconstructed stream')
        gate.validate_failure_markers('\n'.join(kept))
    plain=gate.normalize_console(uart)
    need(plain.count('CONSUMER_BEGIN method=4 token=1 position=0 negative=0')==1 and
         not any(word in plain for word in ('CONSUMER_PASS','CONSUMER_REJECT','HIT GOOD TRAP','HIT BAD TRAP')) and
         plain.count('EXCEEDING CYCLE/INSTR LIMIT')==1,'unique started but cycle-limited incomplete application')
    match=re.findall(r'instrCnt\s*=\s*(\d+),\s*cycleCnt\s*=\s*(\d+)',plain)
    need(len(match)==1 and int(match[0][1])==300000,'exact observed requested guest-cycle budget')
    records={name:[] for name in s.old.T13_FIELDS}
    for match in re.finditer(r'T13_(COUNTER_ENQUEUE|CSR_SAMPLE|RETIRE)[ \t]+([^\n]*)\n',counters):
        kind,body=match.groups();records[kind].append(s.old.parse_fields('T13_'+kind,body,s.old.T13_FIELDS[kind].split(),t13=True))
    need(all(len(v)==2 for v in records.values()),'exact two completed initial counter chains; no invented ending sample')
    need(len(fixed['counter_sites'])==4 and [int(x['csr'],16) for x in fixed['counter_sites']]==[0xc00,0xc02,0xc02,0xc00],'complete static fenced counter order')
    elf=t.a.a.b.f.g.ELF(elfpath.read_bytes());pairs=[];previous=-1
    for index,(enq,csr,ret) in enumerate(zip(records['COUNTER_ENQUEUE'],records['CSR_SAMPLE'],records['RETIRE'])):
        site=fixed['counter_sites'][index];pc=int(site['pc'],16);addr=int(site['csr'],16);word=struct.unpack('<I',elf.read(pc,4))[0]
        need(addr==(0xc00,0xc02)[index] and enq['pc']==ret['pc']==pc and enq['word']==ret['word']==word,'actual initial counter PC/word')
        need(word>>20==csr['addr']==addr and csr['wen']==0 and enq['rob']==ret['rob'] and
             ret['count']==1 and ret['slot']==0 and ret['data']==csr['data'],'actual read-only CSR reaches its unique retirement')
        need(enq['empty']==1 and previous<enq['cycle']<csr['cycle']<ret['cycle'],'empty fenced ROB and ordered initial chain')
        previous=ret['cycle'];pairs.append(dict(enqueue=enq,sample=csr,retire=ret))
    timing=dict(status='FENCED_COUNTER_PREFIX_ONLY',reads=2,complete_windows=0,records=pairs)
    save(output/'counter-prefix.json',timing);runtime.verify_files(files)
    report=dict(status='TARGET_PROBE_PARTIAL_AUDITED_NOT_QUALIFIED',protocol=protocol,counter_prefix=timing,
        original_partial_summary_equal=True,original_transaction_sha256_equal=True,complete_checker_rejection=complete_rejection,
        streaming_elapsed_seconds=streaming_elapsed,streaming_process_maxrss_kib=streaming_rss,
        legacy_elapsed_seconds=legacy_elapsed,process_maxrss_after_legacy_kib=legacy_rss,
        observed_guest_retired=int(re.findall(r'instrCnt\s*=\s*(\d+)',plain)[0]),observed_guest_cycles=300000,
        probe_observed_elapsed_seconds=receipt['observed_elapsed_seconds'],probe_raw_bytes=receipt['raw_bytes'],
        original_difftest_enabled=True,complete_forward_validated=False,performance_qualified=False,
        source_sha256=sha(HERE/'audit_probe.py'),stream_source_sha256=sha(HERE/'stream_audit.py'))
    save(output/'result.json',report);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--probe',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.probe.resolve(),args.output.resolve())
    print(json.dumps({k:v for k,v in result.items() if k not in ('protocol','counter_prefix')},indent=2))
