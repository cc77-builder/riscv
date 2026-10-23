"""Linked ELF fixtures test the gate, not a XiangShan runtime or performance.

R2_TEST_DATA may name a previously generated S2 source directory. Without it,
use the pinned candidate generator from the full repository checkout.
"""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import linked_gate as g
import fullcore_screen as f

ROOT=Path(__file__).resolve().parents[4]
LD='''pmem_base = 0x80000000;
MEMORY { ram (rwxa) : ORIGIN = 0x80000000, LENGTH = 128M }
ENTRY(_start)
SECTIONS {
. = ORIGIN(ram); .text : { *(entry) *(.text) }
.rodata 0x80080000 : { *(.rodata*) }
.benchmark_inputs 0x80100000 : { *(.benchmark.inputs) }
.benchmark_expected 0x80110000 : { *(.benchmark.expected) }
.benchmark_cases 0x80120000 : { *(.benchmark.cases) }
.benchmark_result 0x80130000 : { *(.benchmark.result) }
.benchmark_sink 0x80131000 : { *(.benchmark.sink) }
.data 0x80140000 : { *(.data) }
.bss 0x80150000 : { *(.bss*) *(.sbss*) *(.scommon) }
}
'''


def fixture(data, output):
    output.mkdir(parents=True)
    for name in ('kernels.S','cases.h','manifest.json'):shutil.copyfile(data/name,output/name)
    (output/'fixture.c').write_text('''#include <stdint.h>
#define static static __attribute__((used))
#include "cases.h"
#undef static
const char r2_unit_test_fixture[] = "NOT A RUNNABLE BENCHMARK";
__attribute__((section(".benchmark.result"))) volatile unsigned char observed[672];
__attribute__((section(".benchmark.sink"))) volatile unsigned char sink[1056];
void _putc(char c) { (void)c; }
void _halt(int c) { (void)c; }
void _trm_init(void) {}
int main(void) { return cases[0].iterations + plan[0].index; }
''')
    (output/'start.S').write_text('.section entry,"ax"\n.global _start\n.type _start,@function\n_start:\n.word 0x0005006b\n.size _start,.-_start\n')
    (output/'fixture.ld').write_text(LD)
    for source in ('fixture.c','start.S','kernels.S'):
        subprocess.run(['clang','--target=riscv64','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-fno-pic','-ffreestanding','-mno-relax','-O0','-c',str(output/source),'-o',str(output/(source+'.o'))],check=True,capture_output=True)
    subprocess.run(['ld.lld','--no-relax','-T',str(output/'fixture.ld'),str(output/'start.S.o'),str(output/'fixture.c.o'),str(output/'kernels.S.o'),'-o',str(output/'fixture.elf')],check=True,capture_output=True)
    subprocess.run(['llvm-objcopy','-S','--set-section-flags','.bss=alloc,contents','-O','binary',str(output/'fixture.elf'),str(output/'fixture.bin')],check=True,capture_output=True)


class LinkedGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
        src=os.environ.get('R2_TEST_DATA')
        if src:data=Path(src)
        else:
            candidate=g.load('unit_candidate',ROOT/g.REL/'candidate.py')
            data=cls.root/'data';candidate.generate(ROOT,data,'s2',0,7,'performance')
        cls.out=cls.root/'fixture';fixture(data,cls.out)
        cls.manifest=json.loads((data/'manifest.json').read_text())
        cls.audit=g.load('unit_original_audit',ROOT/'team/optimizations/o2/r2-kernel-audit/audit.py')
        cls.elf=cls.out/'fixture.elf';cls.bin=cls.out/'fixture.bin';cls.obj=cls.out/'kernels.S.o'

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def inspect(self,**kw):
        return g.inspect(kw.get('elf',self.elf),kw.get('binary',self.bin),kw.get('obj',self.obj),
                         kw.get('manifest',self.manifest),self.audit,allow_test_fixture=True)

    def test_linked_fixture_static_path(self):
        report=self.inspect()
        self.assertEqual(report['status'],'LINKED_ELF_STATIC_CHECK_PASS_NOT_DIFFTEST')
        self.assertFalse(report['runtime_executed'])
        self.assertEqual(report['kernels'][2]['body_instructions'],83)

    def test_fixture_rejected_by_production_gate(self):
        with self.assertRaisesRegex(ValueError,'unit-test fixture'):
            g.inspect(self.elf,self.bin,self.obj,self.manifest,self.audit)

    def test_relocatable_is_not_runnable(self):
        with self.assertRaisesRegex(ValueError,'ET_REL'):
            g.ELF(self.obj.read_bytes()).executable()

    def test_wrong_elf_machine(self):
        raw=bytearray(self.elf.read_bytes());struct.pack_into('<H',raw,18,62)
        with self.assertRaises(ValueError):g.ELF(bytes(raw))

    def test_truncated_section_table(self):
        with self.assertRaises(ValueError):g.ELF(self.elf.read_bytes()[:-60])

    def test_bad_entry(self):
        raw=bytearray(self.elf.read_bytes());struct.pack_into('<Q',raw,24,0x80000004)
        with self.assertRaises(ValueError):g.ELF(bytes(raw)).executable(True)

    def test_bin_tampering(self):
        raw=bytearray(self.bin.read_bytes());raw[0]^=1
        target=self.root/'bad.bin';target.write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'ELF/bin'):self.inspect(binary=target)

    def test_golden_high96_tampering(self):
        m=copy.deepcopy(self.manifest);m['rows'][0]['expected'][0]='00'*16
        with self.assertRaisesRegex(ValueError,'golden'):self.inspect(manifest=m)

    def test_compiled_dot_count(self):
        m=copy.deepcopy(self.manifest);m['rows'][0]['dots']=4
        with self.assertRaisesRegex(ValueError,'constants'):self.inspect(manifest=m)

    def test_compiled_dispatch_pointer(self):
        e=g.ELF(self.elf.read_bytes());s=e.named['.benchmark_cases'];raw=bytearray(e.raw)
        struct.pack_into('<Q',raw,s[4]+24,e.symbols['t13_kernel_1'][0])
        with self.assertRaisesRegex(ValueError,'dispatch'):g.compiled_cases(g.ELF(bytes(raw)),self.manifest)

    def test_compiled_input_data(self):
        m=copy.deepcopy(self.manifest);m['rows'][0]['stream'][0]='00'*16
        with self.assertRaisesRegex(ValueError,'stream'):self.inspect(manifest=m)

    def test_compiled_plan_order(self):
        m=copy.deepcopy(self.manifest);m['plan'][0]['index']=1
        with self.assertRaisesRegex(ValueError,'plan'):self.inspect(manifest=m)

    def test_compiled_case_strings(self):
        m=copy.deepcopy(self.manifest);m['rows'][0]['method']='rvv'
        with self.assertRaisesRegex(ValueError,'text pointer'):self.inspect(manifest=m)

    def test_kernel_machine_code_tamper(self):
        e=g.ELF(self.elf.read_bytes());address,_,index,_=e.symbols['t13_kernel_2'];s=e.sections[index]
        raw=bytearray(e.raw);raw[s[4]+address-s[3]+32]^=4
        target=self.root/'bad-code.elf';target.write_bytes(raw)
        binary=self.root/'bad-code.bin';binary.write_bytes(g.ELF(bytes(raw)).binary())
        with self.assertRaisesRegex(ValueError,'independent assembly'):self.inspect(elf=target,binary=binary)

    def test_wrong_static_body_manifest(self):
        m=copy.deepcopy(self.manifest);m['rows'][2]['body'].append('addi t0, t0, 0')
        with self.assertRaisesRegex(ValueError,'source instruction'):self.inspect(manifest=m)

    def test_fixture_receipt_cannot_enter_runtime(self):
        path=self.root/'receipt';path.mkdir(exist_ok=True)
        g.save(path/'build.json',dict(kind='unit-test-fixture',exit_code=0))
        with self.assertRaisesRegex(ValueError,'real nexus-am'):g.verify_build(path,ROOT)

    def test_missing_runtime_fails_closed(self):
        cfg=dict(am_home=str(self.root/'missing-am'),cross_prefix='not-a-real-tool-',
                 b0_products=str(self.root/'missing-b0'),h1_products=str(self.root/'missing-h1'),
                 b0_build=str(self.root/'missing-b0-build'),h1_build=str(self.root/'missing-h1-build'),
                 reference=str(self.root/'missing-ref'),flash=str(self.root/'missing-flash'))
        p=f.preflight(ROOT,cfg)
        self.assertFalse(p['build_ready']);self.assertFalse(p['runtime_ready'])
        self.assertEqual(p['new_emu_runs'],0)
        self.assertGreaterEqual(len(p['runtime_errors']),10)

    def test_inventory_exact_and_smoke_first(self):
        values=f.inventory()
        self.assertEqual(len(values),26)
        self.assertEqual([(x['variant'],x['shard']) for x in values[:2]],[('s0',7),('s2',7)])
        self.assertEqual(len({f.image_name(i) for i in values}),26)
        self.assertTrue(all(x['suite']=='performance' for x in values[2:]))

    def test_configuration_unknown_field_rejected(self):
        target=self.root/'config.json';g.save(target,{'force_no_diff':True})
        with self.assertRaises(ValueError):f.read_config(target,ROOT)

    def test_missing_measured_samples_rejected(self):
        with self.assertRaises(ValueError):f.summarize([])

    def test_output_reuse_rejected(self):
        with self.assertRaises(FileExistsError):f.run(ROOT,{},self.root,'preflight')

    def test_failed_subprocess_not_success(self):
        with self.assertRaisesRegex(ValueError,'failed/incomplete'):
            f.command(['python3','-c','raise SystemExit(3)'],ROOT,self.root/'failed-command')
        r=json.loads((self.root/'failed-command/command.json').read_text())
        self.assertEqual(r['exit_code'],3)

    def test_timeout_not_success(self):
        with self.assertRaisesRegex(ValueError,'failed/incomplete'):
            f.command(['python3','-c','import time; time.sleep(2)'],ROOT,self.root/'timeout-command',timeout=0.01)
        r=json.loads((self.root/'timeout-command/command.json').read_text())
        self.assertIsNone(r['exit_code']);self.assertTrue(r['timed_out'])

    def synthetic_records(self):
        # Synthetic host fixture, deliberately not an EMU result or performance evidence.
        values=[]
        for shard in (4,5,6,7):
            for mode in ('b0','h1'):
                for variant in ('s0','s2'):
                    for software in ('basic','reuse'):
                        for method in ('vdot','rvv'):
                            for dataset in range(3):
                                for repeat in range(2,6):
                                    values.append(dict(mode=mode,variant=variant,shard=shard,software=software,
                                                       method=method,dataset=dataset,repeat=repeat,phase='measured',
                                                       cycles=100 if method=='vdot' else (70 if software=='reuse' else 80),
                                                       image_sha256=f'fixture-{shard}-{dataset}',instructions=10,
                                                       seq=repeat*4+(software=='reuse')*2+(method=='rvv')))
        return [dict(suite='performance',replay=0,samples=values)]

    def test_synthetic_complete_matrix_and_faster_rvv(self):
        result=f.summarize(self.synthetic_records())
        self.assertEqual((len(result['samples']),len(result['rows'])),(768,32))
        self.assertTrue(all(x['rvv_software']=='reuse' and x['faster_rvv_over_vdot']==0.7 for x in result['faster_rvv_comparison']))

    def test_duplicate_sample_rejected(self):
        records=self.synthetic_records();records[0]['samples'][0]=dict(records[0]['samples'][1])
        with self.assertRaisesRegex(ValueError,'duplicate'):f.summarize(records)

    def test_cross_hardware_image_mismatch_rejected(self):
        records=self.synthetic_records();records[0]['samples'][0]['image_sha256']='wrong-fixture'
        with self.assertRaisesRegex(ValueError,'cross-hardware'):f.summarize(records)

    def test_invariant_shape_cycle_change_rejected(self):
        records=self.synthetic_records();records[0]['samples'][0]['cycles']+=1
        with self.assertRaisesRegex(ValueError,'invariant control'):f.summarize(records)

    def test_smoke_failure_blocks_performance_and_counts_attempt(self):
        out=self.root/'mock-failed-campaign';built=[]
        def build(repo,cfg,directory,item,tools):
            built.append(item)
            return dict(item,name=f.image_name(item),path=str(directory))
        def fail(repo,cfg,image,mode,directory,files,replay=0):
            directory.mkdir(parents=True)
            g.save(directory/'result.json',dict(process_started=True,status='FAILED',synthetic_fixture=True))
            raise ValueError('synthetic smoke failure')
        with patch.object(f,'preflight',return_value=dict(build_ready=True,runtime_ready=True,tools={},files={})), \
             patch.object(f,'runtime_profile',return_value=({},{})), \
             patch.object(f,'build_one',side_effect=build),patch.object(f,'validate_controls',return_value=True), \
             patch.object(f,'execute',side_effect=fail):
            with self.assertRaisesRegex(ValueError,'synthetic smoke'):
                f.run(ROOT,{},out,'all')
        state=json.loads((out/'state.json').read_text())
        self.assertEqual(len(built),2)
        self.assertTrue(all(x['suite']=='smoke' for x in built))
        self.assertEqual((state['new_emu_runs'],state['failed_or_incomplete_emu_runs']),(1,1))
        self.assertFalse(state['performance_measured'])

    def test_blocked_preflight_creates_no_build_or_run(self):
        out=self.root/'mock-preflight-block'
        with patch.object(f,'preflight',return_value=dict(build_ready=False,runtime_ready=False)), \
             patch.object(f,'build_one') as build,patch.object(f,'execute') as execute:
            with self.assertRaisesRegex(ValueError,'dependencies unavailable'):f.run(ROOT,{},out,'all')
        build.assert_not_called();execute.assert_not_called()
        state=json.loads((out/'state.json').read_text())
        self.assertEqual((state['new_emu_runs'],state['linked_elfs']),(0,0))

if __name__=='__main__':unittest.main()
