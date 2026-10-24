"""Exercise rejection before side effects, independently of frozen v1 pins."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import entry_experiment as e
import entry_c_api as c


class LiveGuards(unittest.TestCase):
    def test_input_outputs_rejected_before_any_files_created(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); repo=root/'repo'; repo.mkdir()
            build=root/'build'; build.mkdir()
            hardware=root/'hardware'; hardware.mkdir()
            cfg={'hardware_source':str(hardware)}
            for protected in (repo,build,hardware):
                for run in (lambda out:c.run(repo,cfg,build,out,'test'),
                            lambda out:e.run(repo,cfg,[build],out,'test',False,False)):
                    out=protected/'new-run'
                    with self.assertRaisesRegex(ValueError,'protected input'):run(out)
                    self.assertFalse(out.exists())

    def test_build_outputs_rejected_before_any_files_created(self):
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp); out=repo/'new-build'
            for build in (lambda:c.build(repo,{},out),lambda:e.build(repo,{},out,[1],[0],1)):
                with self.assertRaisesRegex(ValueError,'protected input'):build()
                self.assertFalse(out.exists())

    def test_ambient_environment_not_inherited(self):
        with patch.dict(os.environ,{'LD_PRELOAD':'bad.so','LD_LIBRARY_PATH':'bad',
                                   'PYTHONPATH':'bad','XS_NEGATIVE_VECTOR_TARGET':'vdot','MAKEFLAGS':'bad'}):
            env=e.build_environment('/am',{'gcc':'/usr/bin/gcc','make':'/usr/bin/make'})
            self.assertEqual(set(env),{'PATH','LANG','LC_ALL','TZ','AM_HOME','LINUX_GNU_TOOLCHAIN'})
            self.assertNotIn('XS_NEGATIVE_VECTOR_TARGET',e.frozen_m.execution_environment())
            self.assertEqual(e.frozen_m.execution_environment(True)['XS_NEGATIVE_VECTOR_TARGET'],'vdot')

    def test_new_sibling_is_valid_and_no_output_created_by_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); repo=root/'repo'; repo.mkdir()
            out=root/'new'
            e.protect_output(repo,{},out)
            self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
