#!/usr/bin/env python3
"""Retain the full old decode campaign and add actual operation observations."""
import hashlib
from pathlib import Path

OLD_SHA256 = '06ba8130d98de5521126ec26a2f7dd17b85aeba51085f38a07d184468f91095b'


def derive(source, fragment, output, feature):
    if feature not in (0, 1):
        raise ValueError('feature must be 0 or 1')
    raw = Path(source).read_bytes()
    if hashlib.sha256(raw).hexdigest() != OLD_SHA256:
        raise ValueError('frozen decode source identity mismatch')
    extra = Path(fragment).read_text()
    if extra.count('@DOT16_FEATURE@') != 2:
        raise ValueError('unexpected feature placeholders')
    extra = extra.replace('@DOT16_FEATURE@', str(feature))
    globals_extra = ('static unsigned requested_op=0,probe_fault=0;\n'
                     'static bool probe_fault_injected=false,probe_fault_enabled=' + ('false' if feature else 'true') + ';\n'
                     'static uint64_t simple_checks[2]{},complex_checks[2]{};\n')
    observe = '''static unsigned observed_op(bool complex){
  unsigned actual=complex?d.complex_op:d.simple_op;
  if(probe_fault_enabled&&!probe_fault_injected&&probe_fault==(complex?2U:1U)){
    probe_fault_injected=true;
    std::cerr<<"DOT16_DECODE_INJECT "<<(complex?"complex_op":"simple_op")<<'\\n';
    actual^=1U;
  }
  return actual;
}
'''
    stall = '    d.io_word = word(31, 30, 29); d.io_vsew ^= 1; d.io_vlmul ^= 1;'
    replacement_stall = ('    d.io_word = 0x0200000bU | (31U<<7) | (30U<<15) | (29U<<20);'
                         ' d.io_vsew ^= 1; d.io_vlmul ^= 1;')
    edits = [
        ('VVDotDecodeTestTop', 'VVDot16DecodeProbe', 2),
        ('#include <stdexcept>', '#include <stdexcept>\n#include <string>', 1),
        ('static uint64_t cases = 0;', 'static uint64_t cases = 0;\n' + globals_extra, 1),
        ('static void eval()', observe + 'static void eval()', 1),
        ('return 0x0200000bU | vd << 7 | vs1 << 15 | vs2 << 20;',
         'return (requested_op ? 0x0e00000bU : 0x0200000bU) | vd << 7 | vs1 << 15 | vs2 << 20;', 1),
        ('  require(d.io_snapshot == expected_snapshot, "vtype/vstart snapshot changed");',
         '  require(d.io_snapshot == expected_snapshot, "vtype/vstart snapshot changed");\n'
         '  ++complex_checks[requested_op];\n'
         '  require(observed_op(true)==requested_op,"complex operation mismatch");', 1),
        ('  require(d.io_num_uops == 1 && d.io_num_wb == 1, "LMUL expanded custom instruction");',
         '  require(d.io_num_uops == 1 && d.io_num_wb == 1, "LMUL expanded custom instruction");\n'
         '  ++simple_checks[requested_op];\n'
         '  require(observed_op(false)==requested_op,"simple operation mismatch");', 1),
        (stall, replacement_stall, 1),
        ('int main(int argc, char **argv) {', extra + '\nint main(int argc, char **argv) {', 1),
        ('  Verilated::commandArgs(argc, argv);',
         '  if(argc==2&&std::string(argv[1])=="--fault-simple-op")probe_fault=1;\n'
         '  else if(argc==2&&std::string(argv[1])=="--fault-complex-op")probe_fault=2;\n'
         '  else if(argc!=1){std::cerr<<"unexpected decode arguments\\n";return 2;}\n'
         '  Verilated::commandArgs(argc, argv);', 1),
        ('    require(!d.io_classified && !d.io_simple_vdot && d.io_complex, "vadd vector regression");',
         '    require(!d.io_classified && !d.io_simple_vdot && d.io_complex, "vadd vector regression");\n'
         '    dot16_decode_extra();', 1),
    ]
    text = raw.decode()
    for before, after, count in edits:
        if text.count(before) != count:
            raise ValueError('ambiguous decode derivation anchor: ' + before[:80])
        text = text.replace(before, after)
    restored = text
    for before, after, count in reversed(edits):
        if restored.count(after) != count:
            raise ValueError('ambiguous inverse decode anchor')
        restored = restored.replace(after, before)
    if restored.encode() != raw:
        raise ValueError('full original decode campaign not reconstructed')
    if Path(output).exists():
        raise ValueError('derived C++ output already exists')
    Path(output).write_text(text)
    return dict(schema=1, feature=feature, edits=len(edits),
                original_sha256=OLD_SHA256, original_reconstructed_byte_exact=True,
                fragment_sha256=hashlib.sha256(Path(fragment).read_bytes()).hexdigest(),
                derived_sha256=hashlib.sha256(text.encode()).hexdigest())
