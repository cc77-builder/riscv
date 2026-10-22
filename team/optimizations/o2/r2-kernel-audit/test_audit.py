"""Host tests for the offline R2 auditor; these are not RTL tests."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import audit

def code(body=(0x00000293,)):
    words = audit.PREFIX + tuple(body) + audit.SUFFIX
    return struct.pack('<' + 'I' * len(words), *words)

def fixture_elf(payload):
    """Small independent ELF64 fixture with two executable function symbols."""
    text_at = 64
    text = payload + payload
    strings = b'\0t13_kernel_2\0t13_kernel_3\0'
    strings_at = text_at + len(text)
    sym_at = (strings_at + len(strings) + 7) // 8 * 8
    symbols = bytes(24)
    symbols += struct.pack('<IBBHQQ', 1, 0x12, 0, 1, 0x80000000, len(payload))
    symbols += struct.pack('<IBBHQQ', 14, 0x12, 0, 1, 0x80000000 + len(payload), len(payload))
    shoff = sym_at + len(symbols)
    hdr = struct.pack('<16sHHIQQQIHHHHHH', b'\x7fELF\x02\x01\x01' + bytes(9),
                      2, 243, 1, 0, 0, shoff, 5, 64, 0, 0, 64, 4, 0)
    sections = bytes(64)
    sections += struct.pack('<IIQQQQIIQQ', 0, 1, 6, 0x80000000, text_at, len(text), 0, 0, 4, 0)
    sections += struct.pack('<IIQQQQIIQQ', 0, 3, 0, 0, strings_at, len(strings), 0, 0, 1, 0)
    sections += struct.pack('<IIQQQQIIQQ', 0, 2, 0, 0, sym_at, len(symbols), 2, 1, 8, 24)
    return hdr + text + strings + bytes(sym_at - strings_at - len(strings)) + symbols + sections

class AuditorTests(unittest.TestCase):
    def test_git_hash(self):
        self.assertEqual(audit.git_blob(b''), 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')

    def test_known_instruction_classes(self):
        pairs = {0x03880a0b:'vdot.vv', 0x00000293:'addi', 0x03c60e83:'lb',
                 0x03df8fbb:'mulw', 0x01f282bb:'addw', 0x00805073:'csrwi',
                 0x020f8807:'vle8.v', 0x028f8027:'vs1r.v', 0xc0047057:'vsetivli',
                 0x43402fd7:'vmv.x.s', 0x4202e057:'vmv.s.x', 0x5e003057:'vmv.v.i',
                 0xef0e2a57:'vwmul.vv', 0xc7480857:'vwredsum.vs'}
        for word, name in pairs.items():
            with self.subTest(word=hex(word)):
                self.assertEqual(audit.decode(word)[0], name)

    def test_custom_operands(self):
        self.assertEqual(audit.decode(0x03880a0b), ('vdot.vv', 'v20, v16, v24'))

    def test_signed_immediate(self):
        self.assertEqual(audit.decode(0xfff00293), ('addi', 'x5, x0, -1'))

    def test_unknown_or_branch_rejected(self):
        for word in (0x00000063, 0xffffffff, 0x00008067):
            with self.assertRaises(ValueError):
                audit.audit_kernel(code((word,)), 0)

    def test_span_boundary(self):
        r = audit.audit_kernel(code(), 0x80000000)
        self.assertEqual((r['body_instructions'], r['marker_span_instructions']), (1, 13))
        self.assertEqual(r['body_start'], '0x80000018')
        self.assertEqual(r['body_end_exclusive'], '0x8000001c')

    def test_duplicate_or_missing_marker_rejected(self):
        for raw in (code((audit.START,)), code().replace(struct.pack('<I', audit.STOP), bytes(4))):
            with self.assertRaises(ValueError):
                audit.audit_kernel(raw, 0)

    def test_reversed_markers_rejected(self):
        raw = struct.pack('<II', audit.STOP, audit.START)
        with self.assertRaises(ValueError):
            audit.audit_kernel(raw, 0)

    def test_wrapper_modification_rejected(self):
        raw = bytearray(code()); raw[4] ^= 0x10
        with self.assertRaises(ValueError):
            audit.audit_kernel(bytes(raw), 0)

    def test_compressed_or_truncated_rejected(self):
        for raw in (code()[:-1], code((1,))):
            with self.assertRaises(ValueError):
                audit.audit_kernel(raw, 0)

    def test_elf_symbol_extraction(self):
        functions = audit.elf_functions(fixture_elf(code()))
        self.assertEqual(set(functions), {'t13_kernel_2', 't13_kernel_3'})
        self.assertEqual(functions['t13_kernel_2'], (0x80000000, code()))

    def test_bad_elf_rejected(self):
        for raw in (bytes(12), bytes(64), fixture_elf(code())[:-1]):
            with self.assertRaises(ValueError):
                audit.elf_functions(raw)

    def test_source_pseudo_normalization(self):
        self.assertEqual(audit.source_counts(['li t0, 0','mv t6, a3','.word 0x03880a0b']),
                         {'addi':2, 'vdot.vv':1})

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, 'new directory'):
                audit.run(Path(root), Path(root))

    def test_generator_identity_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/audit.GENERATOR;p.parent.mkdir(parents=True);p.write_text('pass\n')
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                audit.load_generator(root)

    def test_full_readonly_runner_with_independent_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); payload=code();raw=fixture_elf(payload)
            gen=b'def stores(m):\n    return []\ndef kernel(*args):\n    return ["li t0, 0"]\n'
            p=root/audit.GENERATOR;p.parent.mkdir(parents=True);p.write_bytes(gen)
            directory=root/audit.ARCHIVE/'fixture';directory.mkdir(parents=True)
            (directory/'vdot-perf.elf').write_bytes(raw)
            rows=[{'id':f'gemv-4x13-endtoend-reuse-{m}','machine_instructions':13,'custom_instructions':0}
                  for m in ('vdot','rvv')]
            (directory/'elf-audit.json').write_text(json.dumps({'kernels':rows}))
            hashes={(4,13,m):hashlib.sha256(payload).hexdigest() for m in ('vdot','rvv')}
            with patch.object(audit,'INPUTS',{'fixture':(4,13,audit.git_blob(raw))}), \
                 patch.object(audit,'GENERATOR_BLOB',audit.git_blob(gen)), \
                 patch.object(audit,'CODE_HASHES',hashes):
                report=audit.run(root,root/'out')
            self.assertEqual(report['status'],'R2_PINNED_KERNEL_AUDIT_PASS')
            self.assertEqual(len(report['kernels']),2)
            self.assertEqual((directory/'vdot-perf.elf').read_bytes(),raw)
            self.assertEqual(len(list((root/'out').glob('*.disassembly.txt'))),2)

if __name__ == '__main__':
    unittest.main()
