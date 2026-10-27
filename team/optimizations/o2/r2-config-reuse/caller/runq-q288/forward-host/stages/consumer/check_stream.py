"""Differential checks against the unchanged original O2 auditor and fixtures."""
from pathlib import Path
import argparse
import importlib.util
import io
import json
import sys
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('consumer_stream_under_test',HERE/'stream_audit.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
sys.path.insert(0,str(s.REPO/'team/optimizations/o2/fullcore'))
import analyze
import test_trace

def check(output):
    s.require(not output.exists() and not output.is_relative_to(s.REPO),'new isolated stream-check output');output.mkdir(parents=True)
    original=analyze.analyze;counts=dict(accepted=0,rejected=0,chunk_cases=0)
    def compared(text,**options):
        try:expected=original(text,**options)
        except ValueError as first:
            try:s.analyze(text,**options)
            except ValueError:counts['rejected']+=1;raise first
            raise AssertionError('stream accepted a trace rejected by the original')
        actual=s.analyze(text,**options)
        if expected!=actual:
            keys=[k for k in set(expected)|set(actual) if expected.get(k)!=actual.get(k)]
            raise AssertionError('original/stream differ: '+','.join(keys))
        counts['accepted']+=1;return actual
    analyze.analyze=compared
    try:
        suite=unittest.defaultTestLoader.loadTestsFromModule(test_trace)
        with (output/'unittest.log').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
        s.require(result.wasSuccessful(),'all original directed tests pass new/old differential checks')
    finally:analyze.analyze=original
    # Safe full ROB-key reuse while completed younger kills queue behind an
    # older stalled response exercises history folding and backlog > 2.
    reused=test_trace.Fixture();reused.enqueue('0:5');reused.enqueue('0:6',8)
    reused.tick('0:5');reused.tick('0:6')
    for index in range(3):
        reused.tick(ready=0,flush=('0:5',0),auto_commit=False)
        reused.tick(ready=0)
        if index<2:reused.enqueue('0:6',8);reused.tick('0:6',ready=0)
    reused.drain();actual=compared(reused.text())
    s.require(actual['counts']['ACCEPTED_THEN_SQUASHED']==3 and
              actual['counts']['ACCEPTED_YOUNGER_SQUASHED']==3,'each reused cancelled allocation counted once')
    bounded=s.analyze_reader(s.Reader([io.StringIO(reused.text())]))
    s.require(bounded['storage']['max_pending_transactions']>2,'completed younger kills remain ordered behind older R')
    eof=test_trace.REAL_RESET_PREFIX+'O2_REDIRECT cycle=1 rob=0:5 ftq=0:1 self=0\n'
    compared(eof,require_complete=False)
    try:compared(eof)
    except ValueError:pass
    else:raise AssertionError('complete trace accepted a missing final redirect observation')
    gap=eof+test_trace.REAL_RESET_PREFIX.splitlines()[1].replace('cycle=                   0','cycle=3')+'\n'
    try:compared(gap,require_complete=False)
    except ValueError:pass
    else:raise AssertionError('partial trace accepted a missing middle redirect observation')
    class Chunks(io.StringIO):
        def __init__(self,text,size):super().__init__(text);self.chunk=size
        def readline(self,size=-1):return super().readline(self.chunk if size<0 else min(size,self.chunk))
    texts=[test_trace.basic().text(),test_trace.stream().text(),test_trace.blocked().text(),
           test_trace.killed(False,True,False).text()]
    # Preserve a UART token split by an observer record and non-ASCII residue.
    first=texts[0];line=next(v+'\n' for v in first.splitlines() if v.startswith('O2_STATE '))
    texts.append(first.replace(line,'O2_DI'+line+'AG_BEGIN utf8=香山\n',1))
    for text in texts:
        wanted=original(text)
        for chunk in (1,2,7,31,64,511):
            transactions=[];reader=s.Reader([Chunks(text,chunk)])
            actual=s.analyze_reader(reader,transaction_sink=transactions.append)
            for key in ('transaction_count','transaction_sha256','storage'):actual.pop(key)
            actual['transactions']=transactions
            s.require(actual==wanted,'exact results across split names/fields/UART/lines')
            s.require(reader.uart==s.old.extract_events_and_uart(text)[1],'same reconstructed UART after splitting')
            counts['chunk_cases']+=1
    text=texts[0];cut=text.index('\n')+1
    paths=[output/'stderr-eol.log',output/'stdout-eol.log']
    paths[0].write_bytes(text[:cut-1].encode()+b'\r');paths[1].write_bytes(b'\n'+text[cut:].replace('\n','\r\n').encode())
    wanted=original(''.join(p.read_text() for p in paths));transactions=[]
    actual,uart,counters=s.audit_files(paths,transaction_sink=transactions.append)
    for key in ('transaction_count','transaction_sha256','storage'):actual.pop(key)
    actual['transactions']=transactions;s.require(actual==wanted,'independent per-file universal-newline identity')
    report=dict(status='STREAM_ORIGINAL_DIRECTED_DIFFERENTIAL_PASS',tests_run=result.testsRun,**counts,
        newline_boundary_case=True,original_checker_sha256=s.ORIGINAL_SHA,
        reused_cancelled_rob_case=True,ordered_completion_backlog=bounded['storage']['max_pending_transactions'],
        final_redirect_partial_case=True,middle_redirect_gap_rejected=True,
        stream_checker_sha256=s.hashlib.sha256((HERE/'stream_audit.py').read_bytes()).hexdigest(),
        check_sha256=s.hashlib.sha256((HERE/'check_stream.py').read_bytes()).hexdigest())
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(check(args.output.resolve()),indent=2))
