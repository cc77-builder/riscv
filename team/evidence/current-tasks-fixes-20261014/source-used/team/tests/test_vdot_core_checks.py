"""Negative controls for actual target binding and optimized Python validation."""
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from artifact_guard import audit_repo, digest
from vdot_core_checks import (check, check_guest_log, select_decode_rtl, verify_core,
                              verify_manifest, verify_run_command, write_json)


def manifest(path, files):
    path.write_text(''.join(digest(p) + '  ' + str(p.resolve()) + '\n' for p in files))


def guest_log():
    ids = ('D03', 'D05', 'D07', 'L04-0-8-9', 'L04-10-0-9', 'L04-10-8-0', 'L04-0-0-9',
           'L04-31-31-31', 'L05-3-ff', 'clean-vs', 'X02-m2', 'X02-mf2', 'X03-vl0',
           'X03-vl7', 'X04-vstart1', 'X05-vill', 'X06-VS-off', 'X07-vm0', 'X09-v0', 'X11-VS-1')
    return '\n'.join('T10_CASE id=' + name + ' result=PASS cause=' + ('2' if name.startswith('X') else '0')
                     + ' all32=1 pre32=1' for name in ids) + (
        '\nT10_CORE_SMOKE_PASS legal=10 illegal=10 all32=20 pre32=20\n'
        'Difftest enabled\nHIT GOOD TRAP\nExit status: 0\n')


class CoreChecksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def core_fixture(self):
        root = self.root / 'native'; evidence = self.root / 'core'
        evidence.mkdir(); root.mkdir()
        def put(name, content=b'fixture'):
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
            return path
        source = put('src/X.scala'); put('build/emu'); put('build/rtl/SimTop.fir')
        put('build/rtl/SimTop.sv'); header = put('build/generated-src/diffstate.h')
        dep = root / 'dependency'; put('dependency/src/library.scala')
        def git(*args):
            return subprocess.check_output(['git', '-C', str(dep), *args], stderr=subprocess.DEVNULL)
        git('init', '-q'); git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
        revision = git('rev-parse', 'HEAD').decode().strip()
        binding = dict(build_copy=str(root), source_pack_sha256='a' * 64,
                       physical_root_sha256={'src/X.scala': digest(source)}, modules={'dependency': revision})
        write_json(root / 'build/source-binding.json', binding); write_json(evidence / 'source-binding.json', binding)
        for name, files in (('emu', [root / 'build/emu']), ('fir-input', [root / 'build/rtl/SimTop.fir']),
                            ('rtl', [root / 'build/rtl/SimTop.sv'])):
            manifest(evidence / (name + '.sha256'), files)
        profile = dict(source_pack_sha256=binding['source_pack_sha256'],
                       rtl_manifest_sha256=digest(evidence / 'rtl.sha256'),
                       cxx_sha256=digest(sys.executable), cc_sha256=digest(sys.executable),
                       generated_source_sha256={'diffstate.h': digest(header)})
        (root / 'build/emu-compile').mkdir()
        write_json(root / 'build/emu-compile/core-compile-profile.json', profile)
        write_json(evidence / 'compile-profile.json', profile)
        (evidence / 'build-command.txt').write_text(shlex.join(['make', 'emu', 'CXX=' + sys.executable, 'CC=' + sys.executable]))
        write_json(evidence / 'dependency-sources.json', dict(failures=[], sources={'dependency': audit_repo(dep, revision)}))
        (evidence / 'build.status').write_text('exit_code=0\n')
        (evidence / 'build.log').write_text('CORE_BASELINE_BUILD_PASS\n')
        return root, evidence

    def test_guest_log_rejects_incomplete_or_wrong_state(self):
        good = guest_log(); check_guest_log(good)
        mutations = [good.replace(good.splitlines()[0] + '\n', ''), good + good.splitlines()[0] + '\n',
                     good.replace('id=D03 ', 'id=unknown '), good.replace('cause=2', 'cause=0', 1),
                     good.replace('all32=1', 'all32=0', 1), good.replace('pre32=1', 'pre32=0', 1),
                     good.replace('result=PASS', 'result=FAIL', 1), good.replace('Difftest enabled', ''),
                     good.replace('HIT GOOD TRAP', 'HIT BAD TRAP'), good.replace('Exit status: 0', 'Exit status: 1'),
                     good.replace('T10_CORE_SMOKE_PASS', 'missing_summary'), good + 'Exit status: 0\n',
                     good + 'T10_CASE malformed\n']
        for value in mutations:
            with self.subTest(value=value[-100:]), self.assertRaises(ValueError): check_guest_log(value)

    def test_manifest_rejects_relocated_and_changed_selected_image(self):
        original = self.root / 'original.bin'; copy = self.root / 'copy.bin'
        original.write_bytes(b'original'); copy.write_bytes(b'changed')
        path = self.root / 'workload.sha256'; manifest(path, [original])
        verify_manifest(path, self.root, [original])
        with self.assertRaisesRegex(ValueError, 'actual selected'): verify_manifest(path, self.root, [copy])
        original.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'): verify_manifest(path, self.root, [original])

    def test_manifest_rejects_duplicate_missing_or_malformed_inventory(self):
        image = self.root / 'image'; image.write_bytes(b'image')
        path = self.root / 'files.sha256'; manifest(path, [image]); row = path.read_text()
        for value in (row + row, '', 'malformed\n'):
            path.write_text(value)
            with self.subTest(value=value), self.assertRaises(ValueError): verify_manifest(path, self.root, [image])

    def test_core_rejects_root_and_dependency_changes(self):
        root, evidence = self.core_fixture(); verify_core(root, evidence)
        for name in ('src/X.scala', 'dependency/src/library.scala'):
            path = root / name; before = path.read_bytes(); path.write_bytes(b'changed')
            with self.subTest(name=name), self.assertRaises(ValueError): verify_core(root, evidence)
            path.write_bytes(before)
        ignored = root / 'dependency/src/untracked.scala'; ignored.write_bytes(b'unknown')
        with self.assertRaises(ValueError): verify_core(root, evidence)

    def test_core_rejects_changed_generated_and_compiled_artifacts(self):
        root, evidence = self.core_fixture()
        for name in ('build/generated-src/diffstate.h', 'build/emu', 'build/rtl/SimTop.fir', 'build/rtl/SimTop.sv'):
            path = root / name; before = path.read_bytes(); path.write_bytes(b'changed')
            with self.subTest(name=name), self.assertRaises(ValueError): verify_core(root, evidence)
            path.write_bytes(before)
        (root / 'build/generated-src/new.h').write_bytes(b'unknown')
        with self.assertRaises(ValueError): verify_core(root, evidence)

    def test_core_rejects_ambiguous_compiler_and_foreign_manifest(self):
        root, evidence = self.core_fixture()
        command = evidence / 'build-command.txt'; before = command.read_text()
        command.write_text(before + ' CXX=unknown')
        with self.assertRaises(ValueError): verify_core(root, evidence)
        command.write_text(before)
        copy = self.root / 'other-emu'; copy.write_bytes((root / 'build/emu').read_bytes())
        manifest(evidence / 'emu.sha256', [copy])
        with self.assertRaisesRegex(ValueError, 'actual selected'): verify_core(root, evidence)

    def test_decode_rtl_requires_exactly_one_actual_output(self):
        destination = self.root / 'selected.sv'
        with self.assertRaises(ValueError): select_decode_rtl(self.root / 'missing', destination)
        a = self.root / 'a'; a.mkdir(); (a / 'VdotDecodeHarness.sv').write_bytes(b'actual RTL')
        select_decode_rtl(a, destination); self.assertEqual(destination.read_bytes(), b'actual RTL')
        b = a / 'duplicate'; b.mkdir(); (b / 'VdotDecodeHarness.sv').write_bytes(b'other RTL')
        with self.assertRaises(ValueError): select_decode_rtl(a, destination)

    def test_failure_revokes_stale_receipt_before_metadata_read(self):
        (self.root / 'check.json').write_text('{"status":"STALE_PASS"}')
        with self.assertRaises(OSError): check(self.root, self.root, self.root, self.root, self.root)
        self.assertFalse((self.root / 'check.json').exists())
        (self.root / 'check.json').write_text('{"status":"STALE_PASS"}')
        result = subprocess.run([sys.executable, '-O', str(SCRIPTS / 'vdot_core_checks.py'), 'finish',
                                 '--evidence', str(self.root)], capture_output=True)
        self.assertNotEqual(result.returncode, 0); self.assertFalse((self.root / 'check.json').exists())

    def test_runtime_rejects_duplicate_inputs_and_foreign_reference(self):
        root = self.root; (root / 'build').mkdir(); (root / 'build/emu').write_bytes(b'emu')
        reference = root / 'reference.so'; reference.write_bytes(b'reference')
        manifest(root / 'runtime.sha256', [root / 'build/emu', reference])
        args = ['./build/emu', '-i', str(root / 'vdot-integration.bin'), '--flash=' + str(root / 'boot-flash.bin'),
                '--ram-size=128MB', '--diff=' + str(reference), '--max-cycles=2000000']
        (root / 'run-command.txt').write_text(shlex.join(args)); verify_run_command(root, root, reference)
        relative = ['./build/emu', '-i', './vdot-integration.bin', '--flash=./boot-flash.bin',
                    '--ram-size=128MB', '--diff=./reference.so', '--max-cycles=2000000']
        (root / 'run-command.txt').write_text(shlex.join(relative)); verify_run_command(root, root, reference)
        foreign = root / 'other-reference.so'; foreign.write_bytes(reference.read_bytes())
        (root / 'run-command.txt').write_text(shlex.join(relative[:-2] + ['--diff=./other-reference.so', relative[-1]]))
        with self.assertRaises(ValueError): verify_run_command(root, root, reference)
        for extra in (['-i', 'other.bin'], ['--diff=other.so'], ['--no-diff'], ['--ram-size=256MB']):
            (root / 'run-command.txt').write_text(shlex.join(args + extra))
            with self.subTest(extra=extra), self.assertRaises(ValueError): verify_run_command(root, root, reference)

    def test_optimized_python_keeps_log_manifest_and_dependency_guards(self):
        root, evidence = self.core_fixture()
        (root / 'dependency/src/library.scala').write_bytes(b'changed dependency')
        image = self.root / 'original.bin'; image.write_bytes(b'original')
        copy = self.root / 'selected.bin'; copy.write_bytes(b'changed')
        path = self.root / 'files.sha256'; manifest(path, [image])
        code = '''import sys
sys.path.insert(0,sys.argv[1])
from pathlib import Path
from vdot_core_checks import check_guest_log,verify_manifest,verify_core
checks=(lambda:check_guest_log('Difftest enabled\\nHIT GOOD TRAP\\nExit status: 0\\n'),
        lambda:verify_manifest(Path(sys.argv[2]),Path(sys.argv[3]),[Path(sys.argv[4])]),
        lambda:verify_core(Path(sys.argv[5]),Path(sys.argv[6])))
for check in checks:
 try:check()
 except ValueError:pass
 else:raise RuntimeError('Negative control was accepted')
print('OPTIMIZED_GUARDS_PASS checks=3')
'''
        for optimize in ('0', '1', '2'):
            env = dict(os.environ, PYTHONOPTIMIZE=optimize)
            result = subprocess.run([sys.executable, '-c', code, str(SCRIPTS), str(path), str(self.root),
                                     str(copy), str(root), str(evidence)], env=env, capture_output=True)
            with self.subTest(optimize=optimize):
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertIn(b'OPTIMIZED_GUARDS_PASS checks=3', result.stdout)


if __name__ == '__main__':
    unittest.main()
