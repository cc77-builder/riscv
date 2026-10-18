import copy
import importlib.util
from pathlib import Path
import unittest
from collections import defaultdict
import subprocess
import sys
import tempfile

import check_extended as c
from check_trace import TraceError
from test_trace import pair, line as base_line


def line(tag,row):
    return tag+' '+' '.join(f'{k}='+ (hex(v) if k in c.HEX else str(v)) for k,v in row.items())


def fixture():
    rows=[('O2_ROB_BEGIN',dict(schema=2,cycle=0,mode=2,robsize=48,ftqsize=8,predictwidth=16,renamewidth=6,commitwidth=8,hart=0))]
    for tag in ('O2_CSR_BEGIN','O2_CSR_OWNER_BEGIN'):
        rows.append((tag,dict(schema=2,cycle=0,mode=2,hart=0)))
    for tag,row in pair():
        if tag.startswith('O1_ROB_') and not tag.endswith('BEGIN'):
            rows.append((tag.replace('O1_ROB_','O2_FTQ_'),dict(cycle=row['cycle'],slot=row['slot'],rf=row['rf'],rv=row['rv'],ftf=row['rv']%2,ftv=3,fto=row['rv'])))
    return rows


def encoded(rows, base=True):
    return ([base_line(t,r) for t,r in pair()] if base else [])+[line(t,r) for t,r in rows]


def counter_fixture():
    rows=fixture()
    rows.extend([
        ('O2_COUNTER_ENQ',dict(cycle=11,slot=0,rf=0,rv=3,pc=0x80001000,word=0xc0002873,empty=1,wait=0,block=0)),
        ('O2_CSR_ISSUE',dict(cycle=14,rf=0,rv=3,addr=0xc00,wen=0)),
        ('O2_CSR_SAMPLE',dict(cycle=14,addr=0xc00,data=2**63+14,wen=0)),
        ('O2_COUNTER_COMMIT',dict(cycle=16,slot=0,rf=0,rv=3,pc=0x80001000,word=0xc0002873,data=2**63+14)),
    ])
    return rows


class ExtendedTests(unittest.TestCase):
    def run_trace(self,rows): return c.extended_audit(encoded(rows))[0]
    def reject(self,rows):
        with self.assertRaises(ValueError): self.run_trace(rows)

    def test_ftq_identity_and_wrap(self):
        r=self.run_trace(fixture())
        self.assertEqual(r['ftq'],dict(allocated=2,committed=2,wraps=1))

    def test_existing_run_directory_is_not_rewritten_on_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            original=b'IMMUTABLE PREVIOUS CAMPAIGN\n'
            (out/'campaign.json').write_bytes(original)
            command=[sys.executable,'-OO','-B',str(Path(__file__).with_name('run_extended_core.py'))]
            for name in ('core','receipt','pack','reference-root','output'):command+=['--'+name,str(out)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual((out/'campaign.json').read_bytes(),original)
            self.assertFalse((out/'failure.json').exists())

    def test_ftq_cannot_drop_entire_lifecycle(self):
        self.reject([(t,r) for t,r in fixture() if not (t.startswith('O2_FTQ_') and r['rv']==1)])

    def test_wrong_ftq_pointer_offset_or_base_identity(self):
        for field,value in [('ftf',0),('ftv',4),('fto',9),('rv',4)]:
            rows=fixture(); next(r for t,r in rows if t=='O2_FTQ_COMMIT')[field]=value
            self.reject(rows)

    def test_headers_duplicates_bounds_and_damaged_prefix(self):
        for index in range(3):
            rows=fixture(); rows.pop(index); self.reject(rows)
        rows=fixture(); rows.insert(1,rows[0]); self.reject(rows)
        for field,value in [('slot',8),('rf',2),('rv',48),('ftv',8),('fto',16)]:
            rows=fixture(); rows[-1][1][field]=value; self.reject(rows)
        with self.assertRaises(TraceError): c.extended_audit(encoded(fixture())+['broken O2_CSR_SAMPLE cycle=1'])

    def test_extra_unknown_missing_field(self):
        for text in ['O2_WRONG cycle=1','O2_CSR_SAMPLE cycle=1 addr=0xc00 data=0x1',
                     'O2_CSR_SAMPLE cycle=1 addr=0xc00 data=0x1 wen=0 wen=0',
                     'O2_CSR_SAMPLE cycle=NaN addr=0xc00 data=0x1 wen=0']:
            with self.assertRaises(TraceError): c.record(text)

    def test_real_counter_values_and_lifecycle(self):
        r=self.run_trace(counter_fixture())
        self.assertEqual(r['counters'],dict(allocated=1,sampled=1,committed=1))

    def test_counter_missing_sample_owner_allocation_or_commit(self):
        for tag in ('O2_CSR_ISSUE','O2_CSR_SAMPLE','O2_COUNTER_ENQ','O2_COUNTER_COMMIT'):
            self.reject([(t,r) for t,r in counter_fixture() if t!=tag])

    def test_counter_wrong_identity_time_or_writeback(self):
        for tag,field,value in [('O2_CSR_ISSUE','cycle',13),('O2_CSR_ISSUE','rv',4),
                                ('O2_COUNTER_COMMIT','data',14),('O2_COUNTER_COMMIT','pc',123),
                                ('O2_COUNTER_COMMIT','cycle',14),('O2_CSR_SAMPLE','wen',1)]:
            rows=counter_fixture(); next(r for t,r in rows if t==tag)[field]=value; self.reject(rows)

    def test_marker_slots_in_same_commit_group(self):
        rows=fixture()
        for slot,word in enumerate((c.START,0x13,c.STOP,c.START,c.STOP)):
            rows.append(('O2_RETIRE',dict(cycle=20,slot=slot,rf=0,rv=slot+10,pc=0x80002000+slot*4,word=word,count=1,data=0)))
        self.assertEqual(self.run_trace(rows)['windows'],2)
        self.reject(rows[:-1])
        bad=copy.deepcopy(rows); bad[-2][1]['word']=c.STOP; self.reject(bad)

    def test_counter_squash_and_reused_pointer_are_distinct(self):
        original=counter_fixture()[-4:]
        rows=defaultdict(list)
        for tag,row in original[:3]:rows[tag].append(row)
        rows['O2_FTQ_REDIRECT'].append(dict(cycle=15,rf=0,rv=3,self=1,ftf=0,ftv=0,fto=0))
        for tag,row in original:
            r=dict(row,cycle=row['cycle']+20)
            if 'data' in r:r['data']+=20
            rows[tag].append(r)
        counts,completed=c.counter_audit(rows)
        self.assertEqual(counts,dict(allocated=2,sampled=2,squashed=1,committed=1))
        self.assertEqual(len(completed),1)
        rows['O2_COUNTER_COMMIT'][0]['data']-=20
        with self.assertRaises(TraceError):c.counter_audit(rows)

    def test_counter_sample_at_redirect_cannot_be_reused(self):
        rows=defaultdict(list)
        for tag,row in counter_fixture()[-4:-1]:rows[tag].append(row)
        rows['O2_FTQ_REDIRECT'].append(dict(cycle=14,rf=0,rv=3,self=1,ftf=0,ftv=0,fto=0))
        counts,completed=c.counter_audit(rows)
        self.assertEqual(counts['squashed'],1)
        self.assertEqual(completed,{})
        rows['O2_COUNTER_COMMIT'].append(counter_fixture()[-1][1])
        with self.assertRaises(TraceError):c.counter_audit(rows)

    def test_counter_redirect_blocks_allocation_and_commit(self):
        for tick in (11,16):
            rows=defaultdict(list)
            for tag,row in counter_fixture()[-4:]:rows[tag].append(row)
            rows['O2_FTQ_REDIRECT'].append(dict(cycle=tick,rf=0,rv=3,self=1,ftf=0,ftv=0,fto=0))
            with self.assertRaisesRegex(TraceError,'during ROB redirect'):c.counter_audit(rows)

    def test_read_only_counter_write_cannot_commit(self):
        rows=counter_fixture()
        for tag,row in rows:
            if tag in ('O2_CSR_ISSUE','O2_CSR_SAMPLE'):row['wen']=1
        self.reject(rows)

    def test_marker_truncation_nested_and_outside(self):
        for words in ((c.START,), (c.START,c.START,c.STOP), (0x13,c.START,c.STOP), (c.STOP,)):
            rows=fixture()+[('O2_RETIRE',dict(cycle=20+i,slot=0,rf=0,rv=i+10,pc=0x80002000+i*4,word=w,count=1,data=0)) for i,w in enumerate(words)]
            self.reject(rows)

    def test_retire_vdot_must_match_actual_base_commit(self):
        rows=fixture()+[('O2_RETIRE',dict(cycle=20+i,slot=0,rf=0,rv=i+10,pc=0x80002000+i*4,word=w,count=1,data=0)) for i,w in enumerate((c.START,0x0200000b,c.STOP))]
        self.reject(rows)

    def test_converted_windows_use_independent_counts_and_fences(self):
        folder=Path(__file__).resolve().parents[2]/'workloads/vdot-perf'
        spec=importlib.util.spec_from_file_location('o2_perf',folder/'check.py')
        perf=importlib.util.module_from_spec(spec); spec.loader.exec_module(perf)
        words=[c.START,0x0330000f,*sum(([w,0x0330000f] for w in perf.COUNTERS),[]),c.STOP]
        # Four serialized reads, with intervening retired fences and exact
        # cycle/instret values chosen independently of any UART text.
        ticks=[10,20,40,50,70,80,110,120,140,150,160]
        data=[2**63,2**63+1000,2**63+1040,2**63+6]
        rows=fixture(); j=0
        for i,(word,tick) in enumerate(zip(words,ticks)):
            r=dict(cycle=tick,slot=0,rf=0,rv=10+i,pc=0x80002000+i*4,word=word,count=1,data=0)
            if word in perf.COUNTERS:
                r['data']=data[j];j+=1
                rows += [('O2_COUNTER_ENQ',dict(cycle=tick-6,slot=0,rf=0,rv=10+i,pc=r['pc'],word=word,empty=1,wait=0,block=0)),
                         ('O2_CSR_ISSUE',dict(cycle=tick-3,rf=0,rv=10+i,addr=word>>20,wen=0)),
                         ('O2_CSR_SAMPLE',dict(cycle=tick-3,addr=word>>20,data=r['data'],wen=0)),
                         ('O2_COUNTER_COMMIT',{k:v for k,v in r.items() if k!='count'})]
            rows.append(('O2_RETIRE',r))
        result,events=c.extended_audit(encoded(rows))
        self.assertEqual(result['windows'],1)
        manifest=dict(plan=[dict(index=0,phase='calibration',repeat=0)],rows=[dict(id='empty',scenario='calibration-nop',method='control',n=0,dots=0)],dataset=0)
        kernels={0:{0x80002000+i*4:w for i,w in enumerate(words)}}
        values=perf.trace_windows(events,manifest,kernels)
        self.assertEqual((values[0]['cycles'],values[0]['instructions']),(40,6))
        for field in ('data','cycle'):
            bad=copy.deepcopy(events);bad['CSR_SAMPLE'][2][field]+=1
            with self.assertRaises(ValueError):perf.trace_windows(bad,manifest,kernels)
        bad=copy.deepcopy(events);bad['RETIRE'].pop(5)
        with self.assertRaises(ValueError):perf.trace_windows(bad,manifest,kernels)


if __name__=='__main__': unittest.main()
