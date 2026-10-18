"""Exercise real pack/materialize/verify boundaries with isolated Git repos."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

HELPER=runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/prepare-core-baseline.py'))


class DependencyInputsTests(unittest.TestCase):
    def git(self,repo,*args):
        return subprocess.check_output(['git','-C',str(repo),'-c','user.name=Test',
            '-c','user.email=test@example.invalid','-c','protocol.file.allow=always',*args],stderr=subprocess.DEVNULL)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name);dep=base/'dependency';dep.mkdir();self.git(dep,'init')
        (dep/'src/main/scala').mkdir(parents=True)
        (dep/'src/main/scala/Known.scala').write_text('object Known {}\n')
        for nested in ('hardfloat','cde'):
            folder=dep/nested/'src/main/scala';folder.mkdir(parents=True)
            (folder/'Known.scala').write_text('object Known {}\n')
        (dep/'.gitignore').write_text('build/\n*.ignored.scala\n')
        self.git(dep,'add','.');self.git(dep,'commit','-m','dependency')
        self.source=base/'source';self.source.mkdir();self.git(self.source,'init')
        self.git(self.source,'submodule','add',str(dep),'dep')
        (self.source/'build.sc').write_text('// isolated input\n')
        self.git(self.source,'add','.');self.git(self.source,'commit','-m','source')
        self.pack=base/'pack'
        with contextlib.redirect_stdout(io.StringIO()):
            HELPER['pack'](self.source,self.pack)
            HELPER['materialize'](self.source,self.pack,base/'native')
        self.target=Path((self.pack/'build-copy.txt').read_text().strip())
        self.child=self.target/'dep'

    def verify(self):
        with contextlib.redirect_stdout(io.StringIO()):HELPER['verify'](self.source,self.pack,self.target)

    def test_clean_build_and_ignored_build_outputs_are_accepted(self):
        (self.child/'build').mkdir();(self.child/'build/cache.bin').write_bytes(b'generated')
        self.verify()

    def test_unknown_source_added_after_materialize_is_rejected(self):
        (self.child/'src/main/scala/Extra.scala').write_text('object Extra {}')
        with self.assertRaisesRegex(RuntimeError,'Untracked dependency'):self.verify()

    def test_ignored_source_added_after_materialize_is_rejected(self):
        (self.child/'src/main/scala/Extra.ignored.scala').write_text('object Extra {}')
        with self.assertRaisesRegex(RuntimeError,'Ignored dependency compiler'):self.verify()

    def test_ignored_nested_hardfloat_source_is_rejected(self):
        (self.child/'hardfloat/src/main/scala/Extra.ignored.scala').write_text('object Extra {}')
        with self.assertRaisesRegex(RuntimeError,'Ignored dependency compiler'):self.verify()

    def test_ignored_nested_cde_source_is_rejected(self):
        (self.child/'cde/src/main/scala/Extra.ignored.scala').write_text('object Extra {}')
        with self.assertRaisesRegex(RuntimeError,'Ignored dependency compiler'):self.verify()

    def test_tracked_source_changes_staged_and_unstaged_are_rejected(self):
        (self.child/'src/main/scala/Known.scala').write_text('object Changed {}')
        with self.assertRaises(subprocess.CalledProcessError):self.verify()
        self.git(self.child,'add','.')
        with self.assertRaises(subprocess.CalledProcessError):self.verify()

    def test_pack_also_rejects_ignored_compiler_input(self):
        (self.source/'dep/src/main/scala/Extra.ignored.scala').write_text('object Extra {}')
        with self.assertRaisesRegex(RuntimeError,'Ignored dependency compiler'):
            HELPER['pack'](self.source,self.pack.with_name('invalid-pack'))


if __name__=='__main__':unittest.main()
