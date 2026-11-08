from pathlib import Path
import copy,json,hashlib,unittest,ast,sys
import runner,adapter,negative_group
from common import need,read,sha
from fixtures_local import normal,negative
N=Path(__file__).resolve().parent.parent

class Delta(unittest.TestCase):
    def test_01_unchanged_sources_and_frozen_manifest(self):
        reuse=read(N/'REUSE.json')
        for name in ['common.py','supervisor.py','watchdog.py','o2_cancel_selector.py','normal_adapter.py','runtime_gate.py']:
            self.assertEqual(sha(N/'runtime'/name),reuse[name]['sha256'])
        self.assertEqual(read(adapter.C['software_manifest']['path'])['expected_custom_commits'],77)
        old=Path(reuse['negative_group_source']['path']).read_text();new=(N/'runtime/negative_group.py').read_text()
        funcs=lambda s:{x.name:ast.dump(x,include_attributes=False) for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)}
        a,b=funcs(old),funcs(new)
        for name in ['vector_destination','bind_current_custom']:self.assertEqual(a[name],b[name])
        normalized=new.replace('gate=runtime_gate','gate=legacy.runtime_gate')
        self.assertEqual(a['validate_negative_group'],funcs(normalized)['validate_negative_group'])
    def test_02_actual_ELF_guard_and_group_positive(self):
        for before,after,tail in [(0,0,31),(2,2,31),(2,2,1)]:
            r=adapter.collect(negative(before,after,tail,255),'bit100',1)
            self.assertEqual(r['status'],'NEW_GUARD_BIT100_LOG_PASS');self.assertEqual(r['fault']['vd'],0)
            self.assertFalse(r['target_run_qualified'])
    def test_03_guard_binding_negative_controls(self):
        t=negative(2,2)
        mutations=[t.replace('bit=100 vd=0','bit=100 vd=16'),t.replace('pc=0x80000278 instruction','pc=0x8000027c instruction'),t.replace('instruction=0x0294000b','instruction=0x0294080b'),t.replace('right= 0x0000001000000000','right= 0x0000000800000000'),t.replace('v0: 0x0000000000000000','v0: 0x0000000000000001'),t.replace('vl: 0x0000000000000008','vl: 0x0000000000000004'),t.replace('cmtcnt 5 <--','cmtcnt 1 <--'),t.replace('dst 255','dst 256'),t.replace('HIT GOOD TRAP','X')+'HIT GOOD TRAP\n',t.replace('Difftest enabled.','Difftest disabled.'),t.replace(adapter.C['runtime']['bin']['path'],'/tmp/wrong.bin'),t.replace('v0_high','v1_high')]
        for bad in mutations:
            with self.assertRaises(ValueError):adapter.collect(bad,'bit100',1)
        with self.assertRaises(ValueError):adapter.collect(t,'bit100',0)
    def test_04_normal_actual_contract_and_failure_controls(self):
        t=normal();r=adapter.collect(t,'candidate-normal',0)
        self.assertEqual((r['custom_commits'],r['uart_calls'],r['status']),(77,41,'SUPPLEMENT_TRACE_HIT'))
        for bad in [t.replace('OC19_PASS seq=20\n',''),t.replace('OC19_PASS seq=20','OC19_FAIL seq=20'),t.replace('Guest cycle spent: 20000',''),t.replace('HIT GOOD TRAP','HIT BAD TRAP'),t+'Core 0: ABORT at pc = 0x80000278\n',t.replace(adapter.C['runtime']['normal_reference']['path'],'/tmp/wrong.so')]:
            with self.assertRaises(ValueError):adapter.collect(bad,'candidate-normal',0)
    def test_05_exact_two_role_plan(self):
        self.assertEqual([(s['name'],s['wall_seconds'],s['guest_cycles']) for s in runner.ROLES],[('bit100',300,100000),('candidate-normal',900,300000)])
        for s in runner.ROLES:
            cmd,env,cwd=runner.plan(s['name']);self.assertIn('--max-cycles='+str(s['guest_cycles']-16),cmd);self.assertEqual('SP1_CHAIN_BIT100' in env,s['name']=='bit100');self.assertEqual(cwd,str(N/'runtime'))
        self.assertEqual([runner.C['limits'][k] for k in ['target_seconds','host_seconds','outer_seconds']],[1200,900,2100])
    def test_06_first_failure_and_not_hit_stop(self):
        for failing in ['bit100','candidate-normal',None]:
            calls=[]
            def run(s):calls.append(s['name']);return s['name']
            def check(s,v):
                if s['name']==failing:raise ValueError('NOT_HIT' if failing=='candidate-normal' else 'bad negative')
            if failing:
                with self.assertRaises(ValueError):runner.schedule(run,check)
            else:runner.schedule(run,check)
            self.assertEqual(calls,['bit100'] if failing=='bit100' else ['bit100','candidate-normal'])
    def test_07_receipt_identity_and_resources(self):
        import tempfile
        from common import save
        from supervisor import now
        with tempfile.TemporaryDirectory(prefix='o2-receipt-host-') as tmp:
            d=Path(tmp);role='bit100';cmd,env,cwd=runner.plan(role);pid=777777;birth=12345
            lim={k:runner.C['limits'][k] for k in ['cpu_affinity','thread_cap','rss_cap_bytes','log_cap_bytes']};lim.update(wall_seconds=300,guest_cycles=100000)
            proc={'pid':pid,'pgid':pid,'sid':pid,'start_ticks':birth,'state':'S','rss_bytes':4096,'threads_reported':1,'tids':[{'tid':pid,'cpu_affinity':'4'}]}
            ident={'pid':pid,'process':proc,'executable':runner.C['runtime']['candidate_emu']['path'],'executable_sha256':runner.C['runtime']['candidate_emu']['sha256'],'command':cmd,'environment':env,'cwd':cwd}
            boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            launch={'role':role,'limits':lim,'command':cmd,'env':env,'cwd':cwd,'boot_id':boot}
            sample={'threads':1,'rss_bytes':4096,'processes':[proc],'live_processes':[proc]}
            (d/'stdout.log').write_text('HOST_SYNTHETIC_NOT_A_REAL_TARGET\n');(d/'stderr.log').write_text('')
            (d/'telemetry.jsonl').write_text(json.dumps(sample)+'\n')
            sizes={k:(d/(k+'.log')).stat().st_size for k in ['stdout','stderr']}
            rec={'role':role,'limits':lim,'resource_ok':True,'cleanup_ok':True,'stop_reason':None,'exception':None,'cleanup_error':None,'exit_code':1,'guest_cycles':20000,'elapsed_seconds':12.0,'boot_id':boot,'execution_identity':ident,'pid':pid,'known_pid_start_ticks':{str(pid):birth},'command':cmd,'cwd':cwd,'process_started':True,'observed_bytes':sizes,'retained_bytes':sizes,'raw_truncated':False,'raw_sha256':{k:sha(d/(k+'.log')) for k in sizes},'sample_count':1,'peak_threads':1,'peak_rss_bytes':4096,'final_snapshot':{'processes':[]},'observed_mapped_files':{runner.C['runtime'][k]['path']:{'pid':pid} for k in ['normal_reference','negative_reference']}}
            save(d/'record.json',rec);save(d/'launch.json',launch);save(d/'execution-identity.json',ident)
            self.assertEqual(runner.receipt(role,d,lim)['status'],'ACTUAL_RUNTIME_RECEIPT_PASS')
            for key,value in [('resource_ok',False),('cleanup_ok',False),('exit_code',0),('guest_cycles',100001),('elapsed_seconds',301),('observed_mapped_files',{}),('raw_truncated',True),('peak_threads',5)]:
                bad=copy.deepcopy(rec);bad[key]=value;save(d/'record.json',bad)
                with self.assertRaises((ValueError,KeyError)):runner.receipt(role,d,lim)
            save(d/'record.json',rec)
            bad=copy.deepcopy(ident);bad['executable_sha256']='0'*64;save(d/'execution-identity.json',bad)
            with self.assertRaises(ValueError):runner.receipt(role,d,lim)

    def test_08_cold_import_closed_source_and_no_target_authorization(self):
        f=runner.verify();allowed={x['path'] for x in f['files']}
        self.assertIn(str(N/'host/fixtures_local.py'),allowed)
        self.assertFalse((N/'RUN_AUTHORIZATION.json').exists());self.assertFalse((N/'BATCH.used.json').exists());self.assertFalse((N/'target-01').exists())
        maps=Path('/proc/self/maps').read_text()
        self.assertNotIn(runner.C['runtime']['normal_reference']['path'],maps)
        self.assertNotIn(runner.C['runtime']['negative_reference']['path'],maps)

if __name__=='__main__':unittest.main(verbosity=2)
