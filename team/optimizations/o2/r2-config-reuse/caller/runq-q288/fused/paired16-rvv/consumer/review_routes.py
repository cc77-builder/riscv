"""Reproduce the instruction review for the actual paired16 consumer ELF.

The addresses below were read from this ELF's GNU disassembly. This bounded
proof covers pointer preparation and route selection, not symbolic execution
of the whole consumer or a numerical/performance qualification.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct
import sys

ELF_SHA = '2f7fc718a6c3a388d514392649a1f6fb824f68a1b6d8223eec37855fced63ab9'
DIS_SHA = '83de3b00e3706965df2ef304911800baa5e2de1d4d2a5a2e17747992d7df8a08'
SITES = [
    ('Q', 0x80005350, 0x80005368, 'q288_paired16_rvv'),
    ('K', 0x80005378, 0x80005390, 'q288_paired16_rvv'),
    ('V', 0x800053a4, 0x800053b8, 'q288_paired16_rvv'),
    ('Wo', 0x8000566c, 0x80005684, 'q288_paired16_rvv'),
    ('W1', 0x80005704, 0x8000571c, 'q288_paired16_rvv'),
    ('W3', 0x8000572c, 0x80005744, 'q288_paired16_rvv'),
    ('W2', 0x800057c8, 0x800057e0, 'q288_fused_rvv4'),
    ('classifier', 0x80005888, 0x80005890, 'q288_paired16_rvv'),
]


def need(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def branch_target(pc, word):
    immediate = ((word >> 31) << 12) | (((word >> 7) & 1) << 11)
    immediate |= ((word >> 25) & 63) << 5 | ((word >> 8) & 15) << 1
    return pc + signed(immediate, 13)


def jump_target(pc, word):
    immediate = ((word >> 31) << 20) | (((word >> 12) & 255) << 12)
    immediate |= ((word >> 20) & 1) << 11 | ((word >> 21) & 1023) << 1
    return pc + signed(immediate, 21)


def review(build, controller, output):
    need('build' not in sys.modules and 'derive' not in sys.modules, 'fresh Python controller namespace')
    sys.path.insert(0, str(controller))
    spec = importlib.util.spec_from_file_location('paired16_route_review_build', controller / 'build.py')
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    need(not output.exists(), 'fresh routing review output')
    record = b.read(build / 'result.json')
    r, support_files = b.support(Path(record['parent_campaign']), Path(record['support_snapshot']))
    elf_path = build / (b.PREFIX + '.elf')
    dis_path = build / 'disassembly.stdout.log'
    need(b.digest(elf_path) == ELF_SHA and b.digest(dis_path) == DIS_SHA, 'actual reviewed ELF and disassembly')
    elf = r.b.base.f.g.ELF(elf_path.read_bytes())
    word = lambda pc: struct.unpack('<I', elf.read(pc, 4))[0]
    evidence = lambda pcs: [dict(pc=hex(pc), bytes=elf.read(pc, 4).hex(), word=f'{word(pc):08x}') for pc in pcs]

    def pair(pc, reg, operation=0x13):
        first, second = word(pc), word(pc + 4)
        need(first & 0xfff == ((reg << 7) | 0x17), 'AUIPC destination at ' + hex(pc))
        need(second & 0xfffff == ((reg << 15) | (reg << 7) | operation), 'paired instruction at ' + hex(pc + 4))
        return (pc + signed(first & 0xfffff000, 32) + signed(second >> 20, 12)) & ((1 << 64) - 1)

    begin, size, *_ = elf.symbols['consumer_paired16_cache']
    need(begin == 0x80005124 and size == 2088, 'complete reviewed consumer function bounds')
    words = {pc: word(pc) for pc in range(begin, begin + size, 4)}
    need(all(value & 3 == 3 for value in words.values()), 'complete 32-bit instruction stream')
    actual = [pc for pc, target in b.calls(dis_path.read_text())
              if begin <= pc < begin + size and target == 'route_matmul']
    need(actual == [site[2] for site in SITES], 'all eight actual route relocations without omission')
    targets = []
    for pc, value in words.items():
        if value & 127 == 0x63:
            targets.append(branch_target(pc, value))
        elif value & 127 == 0x6f:
            targets.append(jump_target(pc, value))
    route_calls = []
    for label, setup, call, kernel in SITES:
        address = pair(setup, 15)
        need(address == elf.symbols[kernel][0], 'resolved a5 pointer for ' + label)
        need(pair(call, 1, 0x67) == elf.symbols['route_matmul'][0], 'actual AUIPC/JALR call destination')
        need(not any(setup < target <= call + 4 for target in targets), 'no direct branch into pointer/call interior')
        for pc in range(setup + 8, call, 4):
            value = word(pc)
            opcode = value & 127
            need(opcode not in (0x63, 0x6f, 0x67), 'straight-line argument preparation')
            need(opcode in (0x23, 0x27) or (value >> 7) & 31 != 15, 'no a5 overwrite')
        route_calls.append(dict(site=label, pc=hex(call), jalr_pc=hex(call + 4), kernel=kernel,
            kernel_address=hex(address), instruction_evidence=evidence(range(setup, call + 8, 4)),
            straight_line_pointer_setup=True, no_a5_overwrite=True, no_direct_branch_interior_entry=True))

    fixed = {
        0x80002ed4: 0x30000813, 0x80002ed8: 0x00078a13,
        0x80002ee8: 0x12000793, 0x80002eec: 0x1b068663,
        0x80003098: 0x04f70863, 0x80002fa8: 0x000a00e7,
        0x80003048: 0x000a00e7, 0x80003164: 0x00ea0663,
        0x80003170: 0x05010513, 0x80003174: 0x000780e7,
        0x80006440: 0x00058493, 0x80006594: 0x00400793,
        0x80006598: 0x0297e663, 0x800065c4: 0x00000513,
    }
    for pc, value in fixed.items():
        need(word(pc) == value, 'reviewed selector or method-domain instruction: ' + hex(pc))
    need(pair(0x80003154, 14) == elf.symbols['q288_fused_rvv4'][0], 'FR pointer comparison')
    need(pair(0x8000315c, 15) == elf.symbols['q768_fr'][0], 'default W2 FR target')
    need(pair(0x80003168, 15) == elf.symbols['q768_ta'][0], 'non-FR alternative target')
    need(branch_target(0x80003164, word(0x80003164)) == 0x80003170, 'FR equality skips TA load')
    need(branch_target(0x80006598, word(0x80006598)) == 0x800065c4, 'method above four returns zero')
    need(pair(0x800067d8, 1, 0x67) == begin, 'new public entry calls the new clone')
    bodies = {}
    for name in ('consumer_paired16_cache', 'route_matmul', 'r2_w2_paired16_forward', 'r2_w2_forward'):
        pc, count, *_ = elf.symbols[name]
        bodies[name] = dict(pc=hex(pc), bytes=count, sha256=b.derive.sha(elf.read(pc, count)))
    b.verify(support_files)
    result = dict(status='PAIRED16_CONSUMER_ROUTING_REVIEW_PASS', elf_sha256=ELF_SHA,
        disassembly_sha256=DIS_SHA, route_calls=route_calls,
        support_snapshot=record['support_snapshot'],
        support_identity_sha256=b.digest(Path(record['support_snapshot']) / 'support-identity.json'),
        w2_fr_selection=dict(kernel='q768_fr', pointer_comparison='q288_fused_rvv4',
            applicable_domain='fixed initialized model, K=768, output=288, recognized W2 tensor',
            instruction_evidence=evidence([0x80002ed4, 0x80002ed8, 0x80002ee8, 0x80002eec, 0x80003098]
                                          + list(range(0x80003154, 0x80003178, 4)))),
        old_method_5_still_invalid=True,
        old_method_evidence=evidence([0x80006440, 0x80006594, 0x80006598, 0x800065c4]),
        k288_full_and_tail_indirect_calls=evidence([0x80002fa8, 0x80003048]),
        public_entry_call=evidence([0x800067d8, 0x800067dc]),
        complete_function_bodies=bodies, checker_sha256=b.digest(Path(__file__)),
        checker_scope='fixed-ELF reproduction of manual instruction review; no runtime or performance claim',
        call_pc_convention='R_RISCV_CALL AUIPC address; jalr_pc records actual transfer instruction')
    b.save(output, result)
    print(json.dumps(dict(status=result['status'], output=str(output), sha256=b.digest(output),
                          route_calls=8, paired16=7, retained_w2_fr=1)), flush=True)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'controller', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    review(args.build.resolve(), args.controller.resolve(), args.output.resolve())
