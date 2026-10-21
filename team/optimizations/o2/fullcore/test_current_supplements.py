"""Fresh input selection must not weaken supplement source or corpus gates."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_supplements as run


class CurrentSupplements(unittest.TestCase):
    def test_git_corpus_image_and_am_closure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'repo';root.mkdir()
            prefix='team/optimizations/o2/fullcore/workloads/'
            source=root/prefix;source.mkdir(parents=True)
            (source/'main.c').write_bytes(b'/* committed source */\n')
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'add','.'],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
            revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            build=Path(temp)/'build';(build/'source').mkdir(parents=True);(build/'data').mkdir()
            (build/'source/main.c').write_bytes((source/'main.c').read_bytes())
            frozen=root/'team/optimizations/o2/evidence/20261019-fullcore-validation/files/runs/diagnostic-build-03/data'
            frozen.mkdir(parents=True)
            manifest={'expected_vdot_commits':1158}
            for name,body in [('manifest.json',json.dumps(manifest).encode()),('kernels.S',b'fixed asm'),('cases.h',b'fixed header')]:
                (build/'data'/name).write_bytes(body);(frozen/name).write_bytes(body)
            for name in ('o2-diag.bin','o2-diag.elf','o2-diag.txt','symbols.txt'):(build/name).write_bytes(name.encode())
            am=Path(temp)/'am'
            libraries={}
            for name in ('am/build/am-riscv64-xs.a','libs/klib/build/klib-riscv64-xs.a'):
                p=am/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'am');libraries[str(p)]=run.suite.sha(p)
            hello=Path(temp)/'hello.json';hello.write_text(json.dumps({'am_home':str(am),'am_revision':'086a238062fdfb3281b745a537b361983d0154b5'}))
            row=dict(status='O2_DIAGNOSTIC_BUILD_PASS',kind='diagnostic',exit_code=0,source_commit=revision,
                     command=['make','-C',str(build/'source'),'ARCH=riscv64-xs','MARCH=rv64gcv','O2_DATA='+str(build/'data'),
                              'O2_OBJ_ROOT='+str(build/'objects'),'BINARY='+str(build/'o2-diag'),'-j2'],
                     source_sha256={'source/main.c':run.suite.sha(build/'source/main.c')},
                     generated_sha256={p.relative_to(build).as_posix():run.suite.sha(p) for p in (build/'data').iterdir()},
                     images_sha256={n:run.suite.sha(build/n) for n in ('o2-diag.bin','o2-diag.elf','o2-diag.txt','symbols.txt')},
                     am_libraries_sha256=libraries,nexus_am_commit='086a238062fdfb3281b745a537b361983d0154b5')
            contract=dict(supplements={'diagnostic':{'build':str(build),'sha256':run.suite.sha(build/'o2-diag.bin')}},
                          receipts={'hello':str(hello)},files=dict(libraries))
            for group in ('source_sha256','generated_sha256','images_sha256'):
                contract['files'].update({str(build/name):digest for name,digest in row[group].items()})
            workload=run.suite.load_module('current_supplement_checker',run.HERE/'workloads/check.py')
            def check(changed):
                (build/'build.json').write_text(json.dumps(changed))
                return run.validate_build('diagnostic',build,workload,contract)
            with patch.object(run,'ROOT',root):
                check(row)
                for group,key in [('images_sha256','o2-diag.elf'),('am_libraries_sha256',next(iter(libraries))),('source_sha256','source/main.c')]:
                    bad=copy.deepcopy(row);bad[group].pop(key)
                    with self.subTest(group=group),self.assertRaises(ValueError):check(bad)
                bad=copy.deepcopy(row);bad['nexus_am_commit']='a'*40
                with self.assertRaisesRegex(ValueError,'AM contract'):check(bad)
                (build/'source/main.c').write_bytes(b'/* changed judge */\n')
                bad=copy.deepcopy(row);bad['source_sha256']['source/main.c']=run.suite.sha(build/'source/main.c')
                contract['files'][str(build/'source/main.c')]=bad['source_sha256']['source/main.c']
                with self.assertRaisesRegex(ValueError,'bound to Git'):check(bad)


if __name__=='__main__':unittest.main()
