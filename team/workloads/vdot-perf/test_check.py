import copy
import unittest
import check as c
import generate as g


class CounterTests(unittest.TestCase):
    def fixture(self):
        a,b=g.dataset_pair(0)
        row=g.case('empty','calibration-nop','control',0,a,b)
        words=[c.START,0x0330000f,c.COUNTERS[0],0x0330000f,c.COUNTERS[1],0x0330000f,0x0330000f,c.COUNTERS[2],0x0330000f,c.COUNTERS[3],0x0330000f,c.STOP]
        code={0x80000000+4*i:w for i,w in enumerate(words)}
        ticks=[10,20,40,50,70,80,90,110,120,140,150,160]
        absolute=(1<<63)+1234567
        data=[absolute,absolute+1000,absolute+1040,absolute+7]
        retires=[];enqueues=[];samples=[];j=0
        for i,(pc,w) in enumerate(code.items()):
            e=dict(cycle=ticks[i],slot=0,flag=0,rob=i,pc=pc,word=w,count=1,data=0)
            if w in c.COUNTERS:
                e['data']=data[j]
                samples.append(dict(cycle=ticks[i]-3,addr=w>>20,data=data[j],wen=0))
                enqueues.append(dict(e,cycle=ticks[i]-6,empty=1,wait=0,block=0))
                j+=1
            retires.append(e)
        m=dict(plan=[dict(index=0,phase='calibration',repeat=0)],rows=[row],dataset=0)
        return dict(RETIRE=retires,COUNTER_ENQUEUE=enqueues,CSR_SAMPLE=samples),m,{0:code}

    def test_exact_large_integers(self):
        result=c.trace_windows(*self.fixture())[0]
        self.assertEqual((result['cycles'],result['instructions']),(40,7))
        self.assertGreater(result['counter_values'][0],1<<53)

    def reject(self,edit):
        events,manifest,kernels=self.fixture();edit(events,manifest,kernels)
        with self.assertRaises(ValueError):c.trace_windows(events,manifest,kernels)

    def test_missing_retirement(self):
        self.reject(lambda e,m,k:e['RETIRE'].pop(5))

    def test_missing_counter(self):
        self.reject(lambda e,m,k:e['CSR_SAMPLE'].pop())

    def test_counter_writeback_corruption(self):
        self.reject(lambda e,m,k:e['CSR_SAMPLE'][1].update(data=2))

    def test_counter_bypasses_fence(self):
        self.reject(lambda e,m,k:e['CSR_SAMPLE'][1].update(cycle=49))

    def test_wrong_rob_identity(self):
        self.reject(lambda e,m,k:e['COUNTER_ENQUEUE'][0].update(rob=31))

    def test_wrong_pc(self):
        self.reject(lambda e,m,k:e['RETIRE'][3].update(pc=0x80000000))

    def test_changed_instret_pair(self):
        def edit(e,m,k):
            e['CSR_SAMPLE'][-1]['data']+=1;e['RETIRE'][9]['data']+=1
        self.reject(edit)

    def test_changed_cycle_pair(self):
        def edit(e,m,k):
            e['CSR_SAMPLE'][2]['data']+=1;e['RETIRE'][7]['data']+=1
        self.reject(edit)

    def test_unexpected_control_compression(self):
        self.reject(lambda e,m,k:e['RETIRE'][0].update(count=2))

    def test_walker_rejects_jump(self):
        self.reject(lambda e,m,k:k[0].update({0x80000018:0x0000006f}))

    def test_event_overflow(self):
        with self.assertRaises(ValueError):c.parse_events('T13_CSR_SAMPLE cycle=1 addr=0xc00 data=0x10000000000000000 wen=0')

    def test_malformed_event(self):
        for text in ['T13_OTHER bad','T13_CSR_SAMPLE cycle=1 addr=0xc00 data=0x2 wen=0 junk']:
            with self.assertRaises(ValueError):c.parse_events(text)

    def test_partial_matrix(self):
        self.reject(lambda e,m,k:m['plan'].append(m['plan'][0]))


class CorpusTests(unittest.TestCase):
    def test_signed_extreme(self):
        self.assertEqual(g.dot(bytes([128])*16,bytes([128])*16).hex(),'00000200'+'00'*12)
        self.assertEqual(g.dot(bytes([128])*16,bytes([127])*16).hex(),'0004feff'+'00'*12)

    def test_lean_sequence_counts(self):
        self.assertEqual(len(g.rvv(10,8,9)),5)
        self.assertEqual(len(g.rvv(10,8,9,True)),7)
        self.assertEqual(len(g.batch()),14)

    def test_scratch_overlap(self):
        for operands in [(2,8,9),(10,3,9),(10,8,2)]:
            with self.assertRaises(ValueError):g.rvv(*operands)

    def test_pair_order_and_input_equality(self):
        for dataset in range(3):
            rows,plan=g.corpus('performance',dataset)
            self.assertEqual(len(plan),156)
            for i in range(0,len(plan),2):
                p,q=plan[i:i+2];a,b=rows[p['index']],rows[q['index']]
                self.assertEqual(a['before'],b['before']);self.assertEqual(a['stream'],b['stream'])
                self.assertEqual(a['expected'],b['expected']);self.assertEqual(a['outputs'],b['outputs'])
                self.assertEqual(p['repeat'],q['repeat'])
                self.assertEqual(a['method'],'vdot' if p['repeat']%2==0 else 'rvv')


if __name__=='__main__':unittest.main()
