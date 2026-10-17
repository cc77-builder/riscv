"""Archive gate tests: synthetic traces are NOT new hardware evidence.

The optional real pilot test rechecks only archived JSON + original stdout.
"""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('o0_replay', HERE / 'replay_archive.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def json_bytes(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def fixture(root):
    """Small synthetic run through the ACTUAL frozen parser/analyzer."""
    originals = ['team/optimizations/o0/analyze.py', 'team/scripts/check-vdot-regression.py']
    for name in originals:
        dest = root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(r.ROOT / name, dest)
    command = ['timeout', '120m', '/fixture/emu', '-i', '/fixture/image/vdot-perf.bin',
               '--flash=/fixture/flash', '--ram-size=128MB', '--diff=/fixture/ref', '--seed=1']
    roles = {'emu': 'a'*64, 'reference': 'b'*64, 'flash': 'c'*64, 'image': 'd'*64}
    run = {'image': 'fixture', 'replay': 0, 'exit_code': 0, 'single_core': True, 'emu_threads': 1,
           'build': '/fixture/image', 'command': command,
           'files': {'/fixture/emu':roles['emu'], '/fixture/ref':roles['reference'],
                     '/fixture/flash':roles['flash'], '/fixture/image/vdot-perf.bin':roles['image']}}
    samples, events, console = [], [], []
    console.extend(['The first instruction of core 0 has commited. Difftest enabled.',
                    'The reference model is /fixture/ref', 'The image is /fixture/image/vdot-perf.bin',
                    'T13_BEGIN suite=performance dataset=0 plan=12 contract=vdot-s8x8-r32-v0.1',
                    'T13_CONTROLS detected=6 expected=6'])
    serial = 0
    for seq in range(12):
        repeat = seq // 2
        method = ('vdot','rvv')[seq%2] if repeat%2 == 0 else ('rvv','vdot')[seq%2]
        phase = 'first' if repeat == 0 else 'warmup' if repeat == 1 else 'measured'
        tick, inst = 1000+seq*1000, 8 if method == 'vdot' else 12
        samples.append({'seq':seq, 'id':'batch-1-'+method, 'scenario':'batch', 'method':method,
                        'n':1, 'dots':4, 'phase':phase, 'repeat':repeat, 'dataset':0,
                        'cycles':20, 'instructions':inst, 'counter_values':[2**54+seq*100,2**55+tick,2**55+tick+20,2**54+seq*100+inst],
                        'sample_ticks':[tick,tick+10,tick+30,tick+40]})
        console.append(f'T13_P seq={seq} c=20 i={inst}')
        if seq == 0:
            console.append('T13_SCRATCH_CONTROL allowed=1')
        if method == 'vdot':
            for i in range(4):
                core = tick+12+3*i
                child = serial*3+10
                rob = f'0:{serial}'
                events.extend([f'T12_VFEX4_ACCEPT cycle={core} rob={rob} fu=0x800000000',
                               f'T12_ACCEPT cycle={child} rob={rob} pdest={serial+1} vl=8 illegal=0'])
                if i < 3:
                    events.append(f'T12_VFEX4_WAIT cycle={core+2} rob=0:{serial+1} fu=0x800000000 busy=1')
                events.append(f'T12_RESPONSE cycle={child+2} rob={rob} pdest={serial+1} illegal=0 data=0x0')
                serial += 1
    console += ['T13_SUMMARY executed=12 failures=0 scratch_control=1', 'Core 0: HIT GOOD TRAP']
    stdout = '\r\n'.join(console)+'\r\n'
    stderr = '\n'.join(events)+'\n'
    hashes = {'stdout.log':r.sha256(stdout.encode()), 'stderr.log':r.sha256(stderr.encode())}
    run['raw_sha256'] = hashes
    analysis = {'status':'PASS', 'scope':'full-core DiffTest, exact state and calibrated CSR windows',
                'samples':samples, 'raw_sha256':hashes, 'image_sha256':roles['image'],
                'fu':{'accepted':24, 'responses':24, 'killed':0, 'stalls':0, 'committed':24,
                      'response_latency_min':2, 'response_latency_max':2,
                      'response_latency_histogram':{'2':24}, 'acceptance_interval_min':3}}
    data = {'analysis':json_bytes(analysis), 'result':json_bytes(run),
            'stdout':gzip.compress(stdout.encode(),mtime=0), 'stderr':gzip.compress(stderr.encode(),mtime=0)}
    pin = {'schema':1,'source_commit':'0'*40,'image':'fixture','scenario':'batch','n':1,'dots':4,
           'fu_latency':2, 'runtime_sha256':roles,'files':{}}
    for role,b in data.items():
        path = 'fixture/' + role + ('.gz' if role in ('stdout','stderr') else '.json')
        file = root/path
        file.parent.mkdir(exist_ok=True)
        file.write_bytes(b)
        pin['files'][role] = {'path':path,'git_blob':r.blob(b)}
    return pin, analysis, run, stdout, stderr


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pin,self.analysis,self.run,self.stdout,self.stderr = fixture(self.root)

    def test_program_mode_is_explicitly_incomplete(self):
        result = r.replay(self.root,self.pin,'program')
        self.assertEqual(result['status'],'O0_PROGRAM_LOG_RECHECK_PASS_TRACE_PENDING')
        self.assertFalse(result['raw_hardware_trace_replayed'])
        self.assertFalse(result['o0_complete'])

    def test_real_parser_synthetic_trace_integration(self):
        result = r.replay(self.root,self.pin,'trace')
        self.assertTrue(result['raw_hardware_trace_replayed'])
        self.assertEqual(result['replayed_diagnostics']['counts']['accepted'],24)
        self.assertEqual(len(result['replayed_diagnostics']['response_coincident_busy_wait_cycles']),18)
        self.assertEqual([w['observed_FU_accepts_including_speculation'] for w in result['window_observations']],
                         [4,0,0,4,4,0,0,4,4,0,0,4])
        self.assertFalse(result['new_hardware_run'])
        self.assertFalse(result['o0_complete'])

    def test_trace_requires_raw_stderr(self):
        (self.root/self.pin['files']['stderr']['path']).unlink()
        with self.assertRaisesRegex(ValueError,'missing pinned file'):
            r.replay(self.root,self.pin,'trace')
        self.assertFalse(r.replay(self.root,self.pin,'program')['raw_hardware_trace_replayed'])

    def test_changed_stored_blob(self):
        path = self.root/self.pin['files']['stdout']['path']
        path.write_bytes(path.read_bytes()+b'X')
        with self.assertRaisesRegex(ValueError,'Git blob mismatch'): r.replay(self.root,self.pin,'program')

    def test_changed_decompressed_hash(self):
        self.run['raw_sha256']['stdout.log'] = 'f'*64
        with self.assertRaisesRegex(ValueError,'digest mismatch'):
            r.decode_gzip(gzip.compress(self.stdout.encode()),self.run['raw_sha256']['stdout.log'])

    def test_mixed_run_hashes(self):
        self.analysis['raw_sha256'] = dict(self.analysis['raw_sha256'], **{'stderr.log':'f'*64})
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_changed_image(self):
        self.run['files']['/fixture/image/vdot-perf.bin'] = 'e'*64
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_changed_reference(self):
        self.run['files']['/fixture/ref'] = 'e'*64
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_changed_emu(self):
        self.run['files']['/fixture/emu'] = 'e'*64
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_failed_exit(self):
        self.run['exit_code'] = 1
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_boolean_exit_is_not_zero(self):
        self.run['exit_code'] = False
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_wrong_replay(self):
        self.run['replay'] = 1
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_multicore(self):
        self.run['single_core'] = False
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_duplicate_diff_option(self):
        self.run['command'].append('--diff=/fixture/ref')
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_float_cycle(self):
        self.analysis['samples'][0]['cycles'] = 20.0
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_boolean_counter(self):
        self.analysis['samples'][0]['counter_values'][0] = True
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_u64_large_exact_values(self):
        r.check_metadata(self.analysis,self.run,self.pin)
        self.assertGreater(self.analysis['samples'][0]['counter_values'][0],2**53)

    def test_u64_overflow(self):
        self.analysis['samples'][0]['counter_values'][0] = 2**64
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_cycle_delta(self):
        self.analysis['samples'][0]['sample_ticks'][2] += 1
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_counter_delta(self):
        self.analysis['samples'][0]['counter_values'][2] += 1
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_window_order(self):
        self.analysis['samples'][1]['sample_ticks'] = self.analysis['samples'][0]['sample_ticks'][:]
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_missing_sample(self):
        self.analysis['samples'].pop()
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_sample_id_mismatch(self):
        self.analysis['samples'][0]['id'] = 'single-1-vdot'
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_reordered_phase(self):
        self.analysis['samples'][0]['phase'] = 'measured'
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_fu_conservation(self):
        self.analysis['fu']['accepted'] += 1
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_fu_latency_histogram(self):
        self.analysis['fu']['response_latency_histogram']['2'] -= 1
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_fu_old_latency_not_claimed_as_t14(self):
        self.analysis['fu']['acceptance_interval_min'] = 2
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_console_cycle_mismatch(self):
        with self.assertRaises(ValueError): r.check_stdout(self.stdout.replace('seq=0 c=20','seq=0 c=21'),self.analysis,self.run)

    def test_extra_malformed_console_record(self):
        with self.assertRaises(ValueError): r.check_stdout(self.stdout+'T13_P broken\n',self.analysis,self.run)

    def test_early_good_trap(self):
        text = 'HIT GOOD TRAP\n'+self.stdout.replace('Core 0: HIT GOOD TRAP','')
        with self.assertRaises(ValueError): r.check_stdout(text,self.analysis,self.run)

    def test_duplicate_summary(self):
        with self.assertRaises(ValueError): r.check_stdout(self.stdout+'T13_SUMMARY executed=12 failures=0 scratch_control=1\n',self.analysis,self.run)

    def test_bad_trap_even_with_good(self):
        with self.assertRaises(ValueError): r.check_stdout(self.stdout+'HIT BAD TRAP\n',self.analysis,self.run)

    def test_reference_banner(self):
        with self.assertRaises(ValueError): r.check_stdout(self.stdout.replace('model is /fixture/ref','model is wrong'),self.analysis,self.run)

    def test_mixed_stream(self):
        with self.assertRaises(ValueError): r.check_stdout(self.stdout+'T12_ACCEPT ',self.analysis,self.run)

    def test_ansi_and_crlf(self):
        r.check_stdout(self.stdout.replace('HIT GOOD TRAP','\x1b[32mHIT GOOD TRAP\x1b[0m'),self.analysis,self.run)

    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError): r.strict_json(b'{"x":1,"x":2}')

    def test_non_finite_json(self):
        with self.assertRaises(ValueError): r.strict_json(b'{"x":NaN}')

    def test_root_json_array(self):
        with self.assertRaises(ValueError): r.strict_json(b'[]')

    def test_path_traversal(self):
        with self.assertRaises(ValueError): r.contained(self.root,'../other')

    def test_absolute_path(self):
        with self.assertRaises(ValueError): r.contained(self.root,'/etc/passwd')

    def test_symlink_escape(self):
        (self.root/'escape').symlink_to('/tmp')
        with self.assertRaises(ValueError): r.contained(self.root,'escape/x')

    def test_compressed_limit(self):
        with patch.object(r,'LIMIT',100):
            with self.assertRaises(ValueError): r.decode_gzip(gzip.compress(b'x'*101),r.sha256(b'x'*101))

    def test_corrupt_gzip(self):
        with self.assertRaises((OSError,EOFError)): r.decode_gzip(b'not-gzip','0'*64)

    def test_source_mapper_guard(self):
        with (self.root/'team/optimizations/o0/analyze.py').open('a') as f: f.write('\n')
        with self.assertRaises(ValueError): r.replay(self.root,self.pin,'trace')

    def test_raw_trace_mismatch_is_not_summary_fallback(self):
        self.pin['files']['stderr']['git_blob'] = '0'*40
        with self.assertRaises(ValueError): r.replay(self.root,self.pin,'trace')

    def test_cli_default_trace_and_no_overwrite(self):
        pins = self.root/'pins.json'; pins.write_bytes(json_bytes(self.pin))
        out = self.root/'result.json'
        cmd = [sys.executable,'-B',str(HERE/'replay_archive.py'),'--repository',str(self.root),'--pins',str(pins),'--output',str(out)]
        first = subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(first.returncode,0,first.stderr)
        before = out.read_bytes()
        self.assertTrue(json.loads(before)['raw_hardware_trace_replayed'])
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
        self.assertEqual(out.read_bytes(),before)

    def test_failed_cli_does_not_write_success(self):
        pins = self.root/'pins.json'; pins.write_bytes(json_bytes(self.pin))
        (self.root/self.pin['files']['stderr']['path']).unlink()
        out = self.root/'failed.json'
        cmd = [sys.executable,'-B',str(HERE/'replay_archive.py'),'--repository',str(self.root),'--pins',str(pins),'--output',str(out)]
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
        self.assertFalse(out.exists())

    def test_boolean_schema(self):
        self.pin['schema'] = True
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_invalid_commit(self):
        self.pin['source_commit'] = 'not-a-commit'
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_batch_dot_count(self):
        self.pin['dots'] = 8
        with self.assertRaises(ValueError): r.check_metadata(self.analysis,self.run,self.pin)

    def test_cli_rejects_output_in_sealed_evidence(self):
        pins = self.root/'pins.json'; pins.write_bytes(json_bytes(self.pin))
        out = self.root/'team/evidence/old-campaign/new.json'
        cmd = [sys.executable,'-B',str(HERE/'replay_archive.py'),'--repository',str(self.root),
               '--pins',str(pins),'--level','program','--output',str(out)]
        self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2)
        self.assertFalse(out.exists())

    def test_real_archived_pilot_program_only(self):
        pin = r.strict_json(r.DEFAULT_PINS.read_bytes())
        if not all((r.ROOT/pin['files'][role]['path']).is_file() for role in ('analysis','result','stdout')):
            self.skipTest('real archived pilot not materialized')
        result = r.replay(r.ROOT,pin,'program')
        self.assertEqual(result['measured_cycles_from_original_stdout']['vdot'],[465,464,464,464])
        self.assertEqual(result['measured_cycles_from_original_stdout']['rvv'],[678,678,678,678])
        self.assertFalse(result['raw_hardware_trace_replayed'])


if __name__ == '__main__':
    unittest.main()
