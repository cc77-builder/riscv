"""Pinned platform xTVAL policy tests, independent of arithmetic goldens."""
import hashlib,importlib.util,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('tval_guard',ROOT/'team/scripts/artifact_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
class TrapValuePolicyTests(unittest.TestCase):
    def test_config_requires_explicit_policy_and_ordinary_illegal_tval(self):
        good=['CONFIG_CUSTOM_VDOT_XS_TVAL=y','CONFIG_TVAL_EX_II=y']
        guard.check_xiangshan_tval_config(good)
        for bad in ([],good[:1],good[1:],good+['# CONFIG_TVAL_EX_II is not set'],
                    ['# CONFIG_CUSTOM_VDOT_XS_TVAL is not set','CONFIG_TVAL_EX_II=y']):
            with self.assertRaises(ValueError):guard.check_xiangshan_tval_config(bad)
    @unittest.skipUnless(shutil.which('gcc'),'host C compiler required')
    def test_actual_patched_header_complete_register_domain_and_boundary_states(self):
        patch=(ROOT/'team/patches/nemu/vdot-s8x8-r32-v0.1.patch').read_text()
        marker='+++ b/src/isa/riscv64/local-include/vdot_tval.h\n'
        self.assertEqual(patch.count(marker),1)
        section=patch.split(marker,1)[1].split('\ndiff --git ',1)[0]
        header='\n'.join(x[1:] for x in section.splitlines() if x.startswith('+'))+'\n'
        manifest=json.loads((ROOT/'team/patches/nemu/manifest.json').read_text())
        self.assertEqual(hashlib.sha256(header.encode()).hexdigest(),manifest['patched_source_sha256']['src/isa/riscv64/local-include/vdot_tval.h'])
        driver=r"""
#include "vdot_tval.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
 unsigned long checks=0;
 const uint64_t lengths[]={0,1,7,8,9,16,255,UINT64_MAX};
 for(unsigned a=0;a<32;a++)for(unsigned b=0;b<32;b++)for(unsigned d=0;d<32;d++){
  uint32_t w=0x0200000bu|(a<<15)|(b<<20)|(d<<7);
  for(unsigned policy=0;policy<4;policy++)for(unsigned k=0;k<8;k++){
   assert(xs_vdot_tval_is_zero(w,true,policy<<6,lengths[k],0)==(lengths[k]!=8));checks++;
  }
  assert(!xs_vdot_tval_is_zero(w,false,0,9,0));checks++;
  assert(!xs_vdot_tval_is_zero(w,true,0,9,1));checks++;
 }
 for(unsigned bit=0;bit<64;bit++){
  assert(!xs_vdot_tval_is_zero(0x0200000b,true,0,9,UINT64_C(1)<<bit));checks++;
  if(bit!=6 && bit!=7){assert(!xs_vdot_tval_is_zero(0x0200000b,true,UINT64_C(1)<<bit,9,0));checks++;}
 }
 for(unsigned bit=0;bit<32;bit++)if((0xfe00707fu>>bit)&1){
  assert(!xs_vdot_tval_is_zero(0x0200000bu^(1u<<bit),true,0,9,0));checks++;
 }
 assert(!xs_vdot_tval_is_zero(0x02000057,true,0,9,0));checks++;
 printf("XS_VDOT_TVAL_POLICY_PASS checks=%lu\n",checks);
 return 0;
}
"""
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'vdot_tval.h').write_text(header);(root/'check.c').write_text(driver)
            subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(root/'check.c'),'-o',str(root/'check')],check=True,capture_output=True)
            out=subprocess.check_output([str(root/'check')],text=True)
            self.assertIn('XS_VDOT_TVAL_POLICY_PASS',out);print(out.strip())
if __name__=='__main__':unittest.main()
