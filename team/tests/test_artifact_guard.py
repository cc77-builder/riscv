"""Source/runtime gates must reject counterexamples, including Git ignores."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('artifact_guard',Path(__file__).resolve().parents[1]/'scripts/artifact_guard.py')
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo=(Path(self.temp.name)/'repo').resolve()
        self.repo.mkdir()
        (self.repo/'src').mkdir()
        (self.repo/'src/main.c').write_bytes(b'void f(void) {}\n')
        (self.repo/'.gitignore').write_bytes(b'build/\n.idea/\n.config\n')
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
        # The guard compares physical bytes, so fixture Git must not inherit a
        # host's newline conversion. Resolve Windows short/case aliases too.
        subprocess.run(['git','-C',str(self.repo),'config','core.autocrlf','false'],check=True)
        subprocess.run(['git','-C',str(self.repo),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.repo),'-c','user.name=Source guard test',
                        '-c','user.email=guard@example.invalid','commit','-qm','fixture'],check=True)
        self.revision=guard.git(self.repo,'rev-parse','HEAD').decode().strip()

    def test_ignored_compiler_source_and_header_rejected(self):
        guard.audit_repo(self.repo,self.revision)
        for name in ('build/extra.c','.idea/extra.h'):
            path=self.repo/'src'/name
            path.parent.mkdir(exist_ok=True)
            path.write_text('/* must reject */\n')
            with self.assertRaisesRegex(ValueError,'Unknown compiler input'):
                guard.audit_repo(self.repo,self.revision)
            path.unlink()

    def test_tracked_content_and_revision_bound(self):
        (self.repo/'src/main.c').write_text('void evil(void) {}\n')
        with self.assertRaisesRegex(ValueError,'Tracked source differs'):
            guard.audit_repo(self.repo,self.revision)
        with self.assertRaisesRegex(ValueError,'Revision mismatch'):
            guard.audit_repo(self.repo,'0'*40)

    def test_stale_source_image_mode_and_data_rejected(self):
        evidence=self.repo/'build';evidence.mkdir()
        data=evidence/'data';data.mkdir()
        source=self.repo/'src/main.c'
        image=evidence/'workload.bin';image.write_bytes(b'image')
        record=dict(schema_version=1,kind='vdot',arch='riscv64-xs',mode='full',data_dir=str(data.resolve()),
                    source_sha256={str(source):guard.digest(source)},inputs_sha256={},
                    images_sha256={str(image):guard.digest(image)})
        (evidence/'workload-provenance.json').write_text(json.dumps(record))
        guard.verify_build(evidence,image,data,'vdot','full')
        for kind,mode,selected in (('baseline','full',data),('vdot','selftest',data),('vdot','full',evidence)):
            with self.assertRaises(ValueError): guard.verify_build(evidence,image,selected,kind,mode)
        source.write_text('void changed(void) {}\n')
        with self.assertRaisesRegex(ValueError,'digest mismatch'):
            guard.verify_build(evidence,image,data,'vdot','full')
        source.write_bytes(b'void f(void) {}\n')
        image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'digest mismatch'):
            guard.verify_build(evidence,image,data,'vdot','full')

    def test_nemu_binary_config_and_source_provenance(self):
        build=self.repo/'build';build.mkdir()
        binary=build/'riscv64-nemu-interpreter';binary.write_bytes(b'fixture binary')
        (self.repo/'.config').write_text('CONFIG_RVV=y\nCONFIG_CUSTOM_VDOT=y\nCONFIG_CUSTOM_VDOT_XS_TVAL=y\nCONFIG_TVAL_EX_II=y\nCONFIG_NMIE_INIT=y\n# CONFIG_MDT_INIT is not set\n# CONFIG_SHARE is not set\n')
        root=Path(self.temp.name)/'team-root'
        (root/'team/patches/nemu').mkdir(parents=True)
        manifest=dict(base_rev=self.revision,contract_id='vdot-s8x8-r32-v0.1',patch_sha256='fixture',
                      patched_source_sha256={'src/main.c':guard.digest(self.repo/'src/main.c')})
        (root/'team/patches/nemu/manifest.json').write_text(json.dumps(manifest))
        with patch.object(guard,'ROOT',root),patch.object(guard,'DEPENDENCIES',{}):
            record=dict(manifest,schema_version=2,build_mode='standalone',
                        config_sha256=guard.digest(self.repo/'.config'),binary_sha256=guard.digest(binary),
                        source_sha256=guard.nemu_snapshot(self.repo))
            (build/'vdot-provenance.json').write_text(json.dumps(record))
            guard.verify_nemu(self.repo,binary,'standalone')
            with self.assertRaises(ValueError): guard.verify_nemu(self.repo,build/'other','standalone')
            with self.assertRaises(ValueError): guard.verify_nemu(self.repo,binary,'reference')
            (self.repo/'.config').write_text('changed')
            with self.assertRaisesRegex(ValueError,'config changed'):
                guard.verify_nemu(self.repo,binary,'standalone')
            (self.repo/'.config').write_text('CONFIG_RVV=y\nCONFIG_CUSTOM_VDOT=y\nCONFIG_CUSTOM_VDOT_XS_TVAL=y\nCONFIG_TVAL_EX_II=y\nCONFIG_NMIE_INIT=y\n# CONFIG_MDT_INIT is not set\n# CONFIG_SHARE is not set\n')
            binary.write_bytes(b'changed binary')
            with self.assertRaisesRegex(ValueError,'binary changed'):
                guard.verify_nemu(self.repo,binary,'standalone')


if __name__=='__main__': unittest.main()
