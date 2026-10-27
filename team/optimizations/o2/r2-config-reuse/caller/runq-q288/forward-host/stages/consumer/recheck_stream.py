"""Compare every streamed transaction and summary with frozen real-log evidence."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import resource
import time
import types

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
s=load('consumer_stream_real',HERE/'stream_audit.py')
target=load('original_boundary_counter_audit',HERE.parent/'projection/target/run.py')
need=s.require

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

class SavedProtocol:
    """Stream the original JSON transaction array; never materialize that array."""
    def __init__(self,path):
        self.file=Path(path).open('r',encoding='utf-8');self.buffer='';self.pos=0;self.eof=False
        self.decoder=json.JSONDecoder();self.summary={};self.keys=set();self.done=False;self.count=0
        try:self.expect('{');self.fields(until_transactions=True)
        except BaseException:self.file.close();raise

    def fill(self):
        self.buffer=self.buffer[self.pos:];self.pos=0
        part=self.file.read(65536);self.eof=not part;self.buffer+=part

    def space(self):
        while True:
            while self.pos<len(self.buffer) and self.buffer[self.pos] in ' \t\r\n':self.pos+=1
            if self.pos<len(self.buffer) or self.eof:return
            self.fill()

    def peek(self):
        self.space();need(self.pos<len(self.buffer),'complete saved JSON');return self.buffer[self.pos]

    def expect(self,char):
        need(self.peek()==char,'expected saved JSON '+char);self.pos+=1

    def value(self):
        self.space()
        while True:
            try:value,end=self.decoder.raw_decode(self.buffer,self.pos)
            except json.JSONDecodeError:
                need(not self.eof,'complete saved JSON value');self.fill();continue
            if end==len(self.buffer) and not self.eof:self.fill();continue
            self.pos=end;return value

    def fields(self,until_transactions=False):
        while self.peek()!='}':
            key=self.value();need(isinstance(key,str) and key not in self.keys,'unique saved JSON key');self.keys.add(key);self.expect(':')
            if key=='transactions':
                need(until_transactions,'single saved transaction array');self.expect('[');return
            self.summary[key]=self.value()
            if self.peek()==',':
                self.pos+=1;need(self.peek()!='}','no saved object trailing comma')
            else:break
        need(not until_transactions,'saved protocol has a transaction array');self.expect('}')
        self.space();need(self.pos==len(self.buffer) and self.eof,'no trailing saved JSON content')

    def finish_array(self):
        self.expect(']')
        if self.peek()==',':
            self.pos+=1;need(self.peek()!='}','no saved object trailing comma')
        else:need(self.peek()=='}','saved transaction field separator')
        self.fields();self.done=True

    def next(self):
        need(not self.done,'new auditor emitted too many transactions')
        if self.peek()==']':self.finish_array();raise StopIteration
        value=self.value();need(isinstance(value,dict),'saved transaction object');self.count+=1
        if self.peek()==',':
            self.pos+=1;need(self.peek()!=']','no saved array trailing comma')
        else:need(self.peek()==']','saved transaction separator')
        return value

    def finish(self):
        if not self.done:self.finish_array()

    def close(self):self.file.close()

def run(baseline,output):
    need(not output.exists() and not output.is_relative_to(s.REPO) and not output.is_relative_to(baseline),'fresh independent audit output')
    output.mkdir(parents=True);start=time.monotonic()
    read=lambda p:json.loads(Path(p).read_text())
    receipt=read(baseline/'result.json');checked=read(baseline/'validation.json')
    need(checked['status'] in ('PROJECTION_BOUNDARY_DIFFTEST_PASS','EXPECTED_PROJECTION_APPLICATION_REJECTION'),'frozen completed actual target evidence')
    need(receipt.get('process_started') is True and receipt.get('process_group_absent_after_exit') is True and not receipt.get('timed_out'),'frozen complete process receipt')
    names=('result.json','validation.json','protocol.json','counter-audit.json','custom-commit-pcs.bin','stderr.log','stdout.log')
    pins={str(baseline/n):sha(baseline/n) for n in names}
    for n in ('stderr.log','stdout.log'):need(pins[str(baseline/n)]==receipt['raw_sha256'][n],'original raw output identity')
    need(pins[str(baseline/'validation.json')]==receipt['validation_sha256'] and
         pins[str(baseline/'custom-commit-pcs.bin')]==checked['custom_commit_pc_sha256'],'original independent validation/PC stream identity')
    image=Path(receipt['command'][receipt['command'].index('-i')+1]);build=image.parent
    fixed=read(build/'result.json');elfpath=build/'projection-boundaries.elf'
    # Pin inherited code/artifacts against the original execution receipt, not
    # merely against hashes computed from today's files.
    historical={elfpath,build/'result.json',s.ORIGINAL,HERE.parent/'projection/target/run.py',
                s.REPO/'team/optimizations/o1/audit/runtime_gate.py'}
    modules=[target];seen=set()
    while modules:
        module=modules.pop()
        if not isinstance(module,types.ModuleType) or id(module) in seen:continue
        seen.add(id(module));modules.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_relative_to(s.REPO):historical.add(path)
    for p in sorted(historical):
        need(receipt['files'].get(str(p))==sha(p),'exact source/artifact in frozen original receipt')
        pins[str(p)]=sha(p)
    need(sha(elfpath)==fixed['artifacts']['projection-boundaries.elf'],'same actual counter-audited ELF')
    for p in (elfpath,build/'result.json',HERE/'stream_audit.py',HERE/'recheck_stream.py',s.ORIGINAL,HERE.parent/'projection/target/run.py'):
        pins[str(p)]=sha(p)
    (output/'inputs.json').write_text(json.dumps(pins,indent=2)+'\n')
    legacy=SavedProtocol(baseline/'protocol.json');pc_count=0;pc_hash=hashlib.sha256()
    try:
        with (baseline/'custom-commit-pcs.bin').open('rb') as pc_stream:
            def transaction(value):
                try:wanted=legacy.next()
                except StopIteration:raise ValueError('stream has extra transaction')
                need(value==wanted,'every complete ordered transaction equals frozen original')
            def commit(value):
                nonlocal pc_count
                raw=value['pc'].to_bytes(8,'little');need(pc_stream.read(8)==raw,'every ROB-age ordered custom PC equals frozen original')
                pc_hash.update(raw);pc_count+=1
            protocol,uart,counters=s.audit_files([baseline/'stderr.log',baseline/'stdout.log'],transaction_sink=transaction,commit_sink=commit)
            need(not pc_stream.read(1),'no missing custom commit');legacy.finish()
        comparable={k:v for k,v in protocol.items() if k not in ('transaction_count','transaction_sha256','storage')}
        need(comparable==legacy.summary,'all original protocol, coverage and histogram fields equal')
        need(legacy.count==protocol['transaction_count'],'complete transaction count')
    finally:legacy.close()
    need(pc_hash.hexdigest()==checked['custom_commit_pc_sha256'],'complete PC byte-stream SHA identical')
    windows=2 if checked['mode'] else 8
    timing=target.counter_audit(counters,target.b.g.ELF(elfpath.read_bytes()),fixed['counter_sites'],windows,checked['samples'],s.old)
    need(timing==read(baseline/'counter-audit.json')==checked['counter_audit'],'exact original counter enqueue/sample/retire evidence')
    plain=target.load('stream_old_failure_normalizer',s.REPO/'team/optimizations/o1/audit/runtime_gate.py').normalize_console(uart)
    need([line for line in plain.splitlines() if line.startswith('TILE_')]==checked['transcript'],'complete original reconstructed application transcript')
    for path,value in pins.items():need(sha(path)==value,'frozen inputs unchanged after streaming audit')
    report=dict(status='STREAM_REAL_LOG_EQUIVALENCE_PASS',baseline=str(baseline),input_sha256=protocol['input_sha256'],
        source_sha256=sha(HERE/'stream_audit.py'),original_source_sha256=s.ORIGINAL_SHA,protocol=protocol,
        custom_count=pc_count,custom_pc_sha256=pc_hash.hexdigest(),counter_audit=timing,transcript=checked['transcript'],
        elapsed_seconds=time.monotonic()-start,maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        raw_bytes={n:(baseline/n).stat().st_size for n in ('stderr.log','stdout.log')},
        every_original_transaction_equal=True,all_original_summary_fields_equal=True,official_or_frozen_files_modified=False)
    report['saved_protocol_identity_scope']='current saved original result compared completely; no historical protocol.json SHA was recorded by the old runner'
    report['historical_artifact_and_helper_files_verified']=len(historical)
    (output/'uart.txt').write_text(uart);(output/'counter-source.txt').write_text(counters)
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.baseline.resolve(),args.output.resolve())
    print(json.dumps({k:result[k] for k in ('status','elapsed_seconds','maxrss_kib','custom_count','every_original_transaction_equal','all_original_summary_fields_equal')},indent=2))
