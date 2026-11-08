"""R4 actual-image/static/host-only delta gates; no target or native reference load."""
from pathlib import Path
import ast,copy,hashlib,json,os,subprocess,sys,tempfile,unittest
from unittest import mock
import runner,adapter,negative_group
from common import read,sha,save
from fixtures_local import normal,negative
from test_image_integration import obj
import review_m1
N=Path(__file__).resolve().parent.parent
OLD=N.parent/'sp1-e-o2-cancel-host-20261107'
R2=N.parent/'sp1-e-o2-cancel-calibration-r2-20261107'
M=read(N/'software/manifest.json')

class M1(unittest.TestCase):
    def test_01_frozen_source_reuse_and_unchanged_C_contract(self):
        for name in ['main.c','judge.c','data.c','contract.h','cases.h']:
            self.assertEqual((N/'software'/name).read_bytes(),(OLD/'software'/name).read_bytes())
        r4=N.parent/'sp1-e-o2-cancel-m1-r4-host-20261107'
        # Explicit no-regeneration/no-build round: compare the immutable prepared inputs.
        for p in (N/'software').iterdir():
            if not p.is_file():continue
            self.assertEqual(p.read_bytes(),(r4/'software'/p.name).read_bytes(),p.name)
            built=N/'build-review/attempt-01/source'/p.name
            if built.is_file():self.assertEqual(p.read_bytes(),built.read_bytes(),p.name)
        self.assertEqual([M['expected_calls'],M['expected_custom_commits'],M['expected_f2v_arch_instructions']],[41,77,320])
        self.assertEqual(M['phases'],[0,1,2,4])
        print('M1_POSITIVE frozen_source_reuse_unchanged_C_full_calls_NO_REGENERATION',flush=True)

    def test_02_zero_add_full_inputs_and_preDIV_semantics(self):
        raw=0x40600000;q=0x8000000000003039//3
        self.assertEqual(q,0x2aaaaaaaaaaababd);self.assertEqual(q&2,0)
        original=bytes.fromhex(M['input_bytes']);v8=original[:16];v9=original[16:]
        self.assertEqual(len(original),32)
        for phase in [0,1,2,4]:
            scalar=raw
            for _ in range(phase):scalar^=1;scalar^=1
            for value in range(256):self.assertEqual((value+(scalar&255))&255,value)
            revised=bytes((x+(scalar&255))&255 for x in v8[:8])+v8[8:]
            self.assertEqual(revised,v8)
            signed=lambda a:a-256 if a>=128 else a
            total=sum(signed(x)*signed(y) for x,y in zip(revised[:8],v9[:8]))
            self.assertEqual((total&0xffffffff).to_bytes(16,'little').hex(),M['expected_dot128'])
            self.assertEqual(0x40e00000+(q&2),0x40e00000)
            gate=raw&255
            for _ in range(phase):gate^=1;gate^=1
            self.assertEqual(q+gate,q);self.assertNotEqual(q+gate,q+1)
        self.assertNotEqual(bytes((x+1)&255 for x in v8[:8]),v8[:8])
        self.assertNotEqual(q&1,0)
        print('M1_POSITIVE full128_inputs_dot_preDIV_and_1024_zero_byte_cases',flush=True)

    def test_03_actual_sequence_mutation_rejection(self):
        build=N/'build-review/attempt-01'
        symbols={line.split()[-1]:int(line.split()[0],16) for line in (build/'o2-cancel.elf.nm.stdout').read_text().splitlines() if len(line.split())>=3}
        ins=obj.parse_disassembly((build/'o2-cancel.elf.objdump.stdout').read_text())
        checked=0
        for f in M['functions']:
            if f['stage']=='prelude':continue
            text=[ins[pc]['mnemonic']+' '+ins[pc]['operands'].split('#')[0].strip() for pc in range(f['start_pc'],f['end_pc'],4)]
            obj.audit_m1_sequence(text,f,symbols,ins)
            pos=lambda v:text.index(v)
            pressure_end=pos('vfmv.v.f v31,ft0')
            mutations=[('drop_release',pos('fmv.x.w t6,ft0'),'addi t6,zero,0'),
              ('wrong_zero_scalar',pos('vadd.vx v8,v8,t6'),'vadd.vx v8,v8,t3'),
              ('drop_RAW',pos('vadd.vx v8,v8,t6'),'vadd.vx v8,v8,zero'),
              ('wrong_VL',pressure_end+1,'vsetivli zero,4,e8,m1,tu,mu'),
              ('wrong_SEW',pressure_end+1,'vsetivli zero,8,e16,m1,tu,mu'),
              ('wrong_policy',pressure_end+1,'vsetivli zero,8,e8,m1,ta,mu'),
              ('missing_pressure',pressure_end,'vfmv.v.f v30,ft0'),
              ('input_preload',pos('vl1re8.v v8,(a0)'),'vl1re8.v v8,(a2)')]
            if f['stage']=='S1':mutations += [('quotient_nonzero_mask',pos('andi t4,t0,2'),'andi t4,t0,1'),('drop_FP_gate',pos('add t3,t3,t4'),'addi t3,t3,0'),('drop_branch_gate',pos('andi t4,t6,255'),'addi t4,zero,0')]
            if f['phase']:
                reg='t6' if f['stage']=='S0' else 't4';mutations.append(('single_XOR',pos(f'xori {reg},{reg},1'),f'addi {reg},{reg},0'))
            for label,index,replacement in mutations:
                with self.subTest(function=f['name'],control=label):
                    bad=list(text);self.assertNotEqual(bad[index],replacement);bad[index]=replacement
                    with self.assertRaises(ValueError):obj.audit_m1_sequence(bad,f,symbols,ins)
                    checked+=1;print('M1_NEGATIVE '+f['name']+'_'+label,flush=True)
            # Preserve byte count while swapping a late FMV with first pressure uop.
            bad=list(text);a=pos('fmv.x.w t6,ft0');b=pos('vfmv.v.f v24,ft0');bad[a],bad[b]=bad[b],bad[a]
            with self.assertRaises(ValueError):obj.audit_m1_sequence(bad,f,symbols,ins)
            checked+=1;print('M1_NEGATIVE '+f['name']+'_late_release',flush=True)
            if f['stage']=='S1':
                bad=copy.deepcopy(ins);branch=f['branch_pc'];bad[branch]['operands']=f"t0,t2,{f['skip_b_pc']+4:x}"
                with self.assertRaises(ValueError):obj.audit_m1_sequence(text,f,symbols,bad)
                checked+=1;print('M1_NEGATIVE '+f['name']+'_wrong_branch_target',flush=True)
        self.assertEqual(checked,94)

    def test_04_new_normal_binding_and_synthetic_coverage(self):
        result=adapter.collect(normal(),'candidate-normal',0)
        self.assertEqual(result['status'],'SUPPLEMENT_TRACE_HIT')
        self.assertEqual((result['custom_commits'],result['uart_calls'],result['uart_rows']),(77,41,84))
        self.assertEqual([len(result['witnesses'][k]) for k in ['S0','S1']],[4,4])
        self.assertFalse(result['target_run_qualified'])
        # A real old log is not a new-image positive; reject its banner explicitly.
        old=(R2/'target-01/02-candidate-normal/stdout.log').read_text()
        with self.assertRaisesRegex(ValueError,'exact image banner'):adapter.image_gate(old,'candidate-normal')
        print('M1_POSITIVE new_PC_all41_synthetic_only',flush=True)

    def test_05_new_bit100_binding_positive_and_negative(self):
        for before,after,tail in [(0,0,31),(2,2,31),(2,2,1)]:
            result=adapter.collect(negative(before,after,tail,255),'bit100',1)
            self.assertEqual(result['status'],'NEW_GUARD_BIT100_LOG_PASS');self.assertFalse(result['target_run_qualified'])
        text=negative(2,2)
        mutations=[('image',adapter.C['runtime']['bin']['path'],'/tmp/wrong.bin'),
          ('reference',adapter.C['runtime']['negative_reference']['path'],'/tmp/wrong-reference.so'),
          ('injection_pc','pc=0x80000278 instruction','pc=0x8000027c instruction'),
          ('injection_word','instruction=0x0294000b','instruction=0x0294080b'),
          ('injection_vd','bit=100 vd=0','bit=100 vd=16'),
          ('wrong_bit','right= 0x0000001000000000','right= 0x0000000800000000')]
        for label,old,new in mutations:
            self.assertEqual(text.count(old),1,label)
            bad=text.replace(old,new,1);self.assertNotEqual(bad,text)
            with self.assertRaises(ValueError):adapter.collect(bad,'bit100',1)
            print('M1_BINDING_NEGATIVE '+label,flush=True)

    def test_06_reuse_exact_mechanisms_and_C_judge(self):
        reuse=read(N/'REUSE.json')
        for name,row in reuse['runtime_sources'].items():
            self.assertEqual(sha(row['path']),row['sha256']);self.assertEqual(sha(N/'runtime'/name),row['sha256'])
        functions=lambda text:{x.name:ast.dump(x,include_attributes=False) for x in ast.parse(text).body if isinstance(x,ast.FunctionDef)}
        before=functions(Path(reuse['runner_original']['path']).read_text());after=functions((N/'runtime/runner.py').read_text())
        for name in before:
            if name!='validate_auth':self.assertEqual(before[name],after[name],name)
        self.assertIn('checks=538',Path(reuse['old_C_judge_log']['path']).read_text())
        self.assertEqual(read(reuse['old_C_judge_result']['path'])['status'],'PASS_HOST_C_JUDGE')
        for row in reuse['old_C_judge_sources']:
            self.assertEqual(sha(row['path']),row['sha256']);self.assertEqual(sha(N/'software'/Path(row['path']).name),row['sha256'])
        print('M1_REUSE parser_supervisor_schedule_receipt_and_538_C_checks',flush=True)

    def test_07_old_full_real_logs_keep_original_bindings(self):
        proc=subprocess.run([sys.executable,'-B',str(N/'host/offline_old.py')],capture_output=True,text=True,timeout=90)
        self.assertEqual(proc.returncode,0,proc.stderr)
        result=json.loads(proc.stdout);self.assertEqual(result['status'],'PASS_OLD_REAL_LOGS_ORIGINAL_BINDING')
        save(N/'review/OLD_LOGS_OFFLINE.json',result)
        self.assertEqual([x['status'] for x in result['results']],['NEW_GUARD_BIT100_LOG_PASS','NEW_GUARD_BIT100_LOG_PASS','SUPPLEMENT_TRACE_NOT_HIT'])
        print('M1_POSITIVE old_R1_R2_logs_not_relabelled_as_new_results',flush=True)

    def test_08_cold_closure_and_missing_wrong_drift_controls(self):
        f=runner.verify();review_m1.check_closure(f)
        path=read(N/'runtime/BASE_REUSE.json')['fixture']['path']
        missing=copy.deepcopy(f);missing['files']=[x for x in missing['files'] if x['path']!=path]
        with self.assertRaisesRegex(ValueError,'missing execution companion'):review_m1.check_closure(missing)
        for label,field,value in [('wrong_path','path','/tmp/m1-required-input-does-not-exist'),('content_drift','sha256','0'*64)]:
            bad=copy.deepcopy(f);index=next(i for i,v in enumerate(bad['files']) if v['path']==path);bad['files'][index][field]=value
            real_read=runner.read
            def altered(p):return bad if Path(p)==N/'EXECUTION_FREEZE.json' else real_read(p)
            with mock.patch.object(runner,'read',side_effect=altered):
                with self.assertRaises((OSError,ValueError)):runner.verify()
            print('M1_FREEZE_NEGATIVE '+label,flush=True)
        maps=Path('/proc/self/maps').read_text()
        for key in ['normal_reference','negative_reference']:self.assertNotIn(adapter.C['runtime'][key]['path'],maps)
        for path in ['RUN_AUTHORIZATION.json','EXECUTION_REQUEST.txt','LAUNCH.used.json','BATCH.used.json','target-01']:self.assertFalse((N/path).exists())
        print('M1_FREEZE_NEGATIVE missing_companion',flush=True)

    def test_09_explicit_future_request_gate_no_target(self):
        with self.assertRaises(FileNotFoundError):runner.validate_auth()
        # Pure temporary authorization fixture; never calls launch/execute/run_group.
        with tempfile.TemporaryDirectory(prefix='o2m1-auth-') as temp:
            d=Path(temp);(d/'host').mkdir()
            for name in ['EXECUTION_FREEZE.json','CONTRACT.json']:(d/name).write_text('{}\n')
            (d/'USER_INSTRUCTION.txt').write_text('host only; no targets\n')
            (d/'EXECUTION_REQUEST.txt').write_text('fixture only, explicit two bounded targets; NEVER EXECUTED\n')
            save(d/'host/RESULT.json',{'status':'PASS_HOST_ADMISSION'})
            a={'operation_id':runner.C['operation_id'],'user_instruction_sha256':sha(d/'EXECUTION_REQUEST.txt'),'freeze_sha256':sha(d/'EXECUTION_FREEZE.json'),'contract_sha256':sha(d/'CONTRACT.json'),'roles':runner.ROLES,'limits':runner.C['limits'],'allow_retry':False,'host_result_sha256':sha(d/'host/RESULT.json')}
            save(d/'RUN_AUTHORIZATION.json',a)
            with mock.patch.object(runner,'N',d):
                self.assertEqual(runner.validate_auth(),sha(d/'RUN_AUTHORIZATION.json'))
                (d/'EXECUTION_REQUEST.txt').write_bytes((d/'USER_INSTRUCTION.txt').read_bytes())
                with self.assertRaisesRegex(ValueError,'fresh explicit target request'):runner.validate_auth()
        print('M1_POSITIVE future_request_gate_host_task_not_target_permission',flush=True)

if __name__=='__main__':unittest.main(verbosity=2,failfast=True)
