"""Lossless transport tests; synthetic rows do not certify DUT behavior."""
import base64
import importlib.util
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest
from generate_vdot_cases import generate
from test_vdot_log import checker, fixture

NAMES=('instruction','trap_count','expected_cause','actual_cause','fault_pc','actual_epc',
       'resume_pc','mtval','pre_mstatus','raw_mstatus','capture_phase','protocol_errors','requested_vs')
ROOT=Path(__file__).resolve().parents[2]

def values_for(row):
    values=[int(row.get(k,'0'),0) for k in NAMES]
    for key in ('pre_csr','post_csr'):
        values += [int(x,0) for x in row.get(key,'0/0/0/0/0/0').split('/')]
    for key in ('pre_vd128','expected_vd128','post_vd128'):
        n=int(row.get(key,'0'),0); values += [n&((1<<64)-1),n>>64]
    values += [int(row.get(k,'0'),0) for k in ('all32_checked','pre32_checked','guards_ok')]
    assert len(values)==34
    return values

def encode_values(values):
    payload=bytearray()
    for i,value in enumerate(values):
        if value in values[:i]:payload.append(values.index(value));continue
        payload.append(128)
        while value>=128:payload.append((value&127)|128);value>>=7
        payload.append(value)
    return base64.b64encode(payload).decode()

def pack(content):
    out=[]
    for line in content.splitlines():
        if line.startswith('VDOT_BEGIN '):
            out += [line,'VDOT_LOG_FORMAT packed-u64-v1'];continue
        if line.startswith(('VDOT_CASE ','HARNESS_NEGATIVE ')):
            row=checker.fields(line)
            prefix='VDOT_PACKED' if line.startswith('VDOT_CASE ') else 'HARNESS_PACKED'
            out.append(f"{prefix} id={row['id']} result={row['result']} payload={encode_values(values_for(row))}")
        else:out.append(line)
    return '\n'.join(out)

class PackedLogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.data=Path(self.temp.name)/'data';generate(self.data,32,0x20261011)
    def check(self,s):return checker.validate(s,'selftest',0,self.data)
    def test_existing_semantic_checker_accepts_lossless_roundtrip(self):
        detailed=fixture();packed=pack(detailed)
        self.assertEqual(self.check(detailed),self.check(packed))
        before=[checker.fields(x) for x in detailed.splitlines() if x.startswith('VDOT_CASE ')]
        after=[checker.fields(x) for x in checker.expand_packed_records(packed).splitlines() if x.startswith('VDOT_CASE ')]
        self.assertEqual([values_for(x) for x in before],[values_for(x) for x in after])
        # Synthetic negatives are already short; compare the actual case
        # records rather than imposing an invented ratio on framing overhead.
        detailed_cases='\n'.join(x for x in detailed.splitlines() if x.startswith('VDOT_CASE '))
        packed_cases='\n'.join(x for x in packed.splitlines() if x.startswith('VDOT_PACKED '))
        self.assertLess(len(packed_cases),len(detailed_cases)//3)
    def test_wrong_fields_remain_rejected_after_compression(self):
        s=fixture()
        for bad in (s.replace('all32_checked=1','all32_checked=0',1),
                    s.replace('pre32_checked=1','pre32_checked=0',1),
                    s.replace('actual_cause=0x3','actual_cause=0x2',1),
                    s.replace('actual_epc=0x80000000','actual_epc=0x80000004',1),
                    s.replace('post_vd128=0x'+32*'f','post_vd128=0x'+32*'0',1),
                    s.replace('capture_phase=2','capture_phase=1',1),
                    s.replace('id=H04-vill','id=H03-vstart7'),
                    s.replace('result=VECTOR_CHANGED','result=PASS')):
            with self.subTest(bad=bad[-80:]),self.assertRaises(ValueError):self.check(pack(bad))
    def test_missing_duplicate_mixed_and_unknown_format_rejected(self):
        s=pack(fixture())
        for bad in (s.replace('VDOT_LOG_FORMAT packed-u64-v1\n',''),
                    s.replace('VDOT_LOG_FORMAT packed-u64-v1','VDOT_LOG_FORMAT packed-u64-v1\nVDOT_LOG_FORMAT packed-u64-v1'),
                    s.replace('packed-u64-v1','unknown-v2'),s+'\nVDOT_CASE id=X result=PASS'):
            with self.assertRaises(ValueError):self.check(bad)
    def test_truncated_overflow_forward_ref_and_trailing_data_rejected(self):
        invalid=[b'\x00',b'\x81',b'\x80',b'\x80'+b'\xff'*9+b'\x02',
                 b'\x80\x80\x00',b'\x80\x00'+b'\x00'*33+b'\x00']
        for p in invalid:
            line='VDOT_LOG_FORMAT packed-u64-v1\nVDOT_PACKED id=X result=PASS payload='+base64.b64encode(p).decode()
            with self.subTest(payload=p),self.assertRaises(ValueError):checker.expand_packed_records(line)
    def test_existing_timeout_and_final_count_checks_are_unchanged(self):
        s=pack(fixture())
        with self.assertRaises(ValueError):checker.validate(s,'selftest',124,self.data)
        with self.assertRaises(ValueError):self.check(s.replace('planned=7','planned=6'))
        with self.assertRaises(ValueError):self.check(s.replace('VDOT_SUMMARY','REMOVED'))
    @unittest.skipUnless(shutil.which('gcc'),'host C compiler required for target encoder roundtrip')
    def test_actual_c_encoder_against_independent_decoder(self):
        src=(ROOT/'team/workloads/vdot-exceptions/main.c').read_text()
        part=src.split('#if VDOT_LOG_COMPACT\nstatic uint64_t read_le64',1)[1].split('#endif',1)[0]
        part='static uint64_t read_le64'+part
        driver=r"""
#include "harness.h"
#include <stdio.h>
#include <string.h>
static struct trap_record record;
static struct { unsigned char regs[32][16]; } before,after;
static unsigned char expected_regs[32][16];
static void _putc(char c){putchar(c);}
static void text(const char *s){fputs(s,stdout);}
static int guards_ok(void){return 1;}
const char *verdict_name(enum verdict v){(void)v;return "PASS";}
"""+part+r"""
int main(void){
  uint64_t v[34];
  while(scanf("%lu",&v[0])==1){
    for(unsigned i=1;i<34;i++)if(scanf("%lu",&v[i])!=1)return 2;
    record.trap_count=v[1];record.cause=v[3];record.expected_pc=v[4];record.epc=v[5];
    record.resume_pc=v[6];record.tval=v[7];record.pre_status=v[8];record.raw_status=v[9];
    record.phase=v[10];record.errors=v[11];struct run_config cfg={0};cfg.vs=v[12];
    record.pre=(struct vector_csrs){v[13],v[14],v[15],v[16],v[17],v[18]};
    record.post=(struct vector_csrs){v[19],v[20],v[21],v[22],v[23],v[24]};
    memcpy(before.regs[10],&v[25],16);memcpy(expected_regs[10],&v[27],16);memcpy(after.regs[10],&v[29],16);
    packed_case("SYNTHETIC",(unsigned)v[0],10,&cfg,v[2],PASS,1);
  }
  return 0;
}
"""
        source=Path(self.temp.name)/'encoder.c';exe=Path(self.temp.name)/'encoder';source.write_text(driver)
        subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'team/workloads/vdot-exceptions'),str(source),'-o',str(exe)],check=True,capture_output=True,text=True)
        rng=random.Random(0x20261013);samples=[]
        for i in range(256):
            values=[rng.getrandbits(64) for _ in range(34)];values[0]&=0xffffffff;values[31:]=[1,1,1]
            if i%2==0:
                for k in range(1,31):values[k]=values[k%4]
            samples.append(values)
        output=subprocess.check_output([str(exe)],input='\n'.join(' '.join(str(v) for v in x) for x in samples)+'\n',text=True)
        expanded=checker.expand_packed_records('VDOT_LOG_FORMAT packed-u64-v1\n'+output)
        rows=[checker.fields(x) for x in expanded.splitlines() if x.startswith('VDOT_CASE ')]
        self.assertEqual([values_for(x) for x in rows],samples)

if __name__=='__main__':unittest.main()
