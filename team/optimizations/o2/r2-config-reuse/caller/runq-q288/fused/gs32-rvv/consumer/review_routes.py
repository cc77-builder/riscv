"""Reproduce the bounded instruction review for one frozen GS32 consumer ELF.

This records machine-code evidence for the manually reviewed fixed call sites.
It is not a general symbolic executor or a substitute for numerical validation.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct
import sys

ELF_SHA = '20fa1bc02dcc195833cd4b7f47d484bc57b22f56e5729f50280c74a47d25ed0b'
DIS_SHA = '3bbc4c34b000bbb446db391735381799e271b77ae039be75f2998bfbd114bf89'
SITES = [
    ('Q', 0x80005090, 0x800050a8, 'q288_gs32_rvv'),
    ('K', 0x800050b8, 0x800050d0, 'q288_gs32_rvv'),
    ('V', 0x800050e4, 0x800050f8, 'q288_gs32_rvv'),
    ('Wo', 0x800053ac, 0x800053c4, 'q288_gs32_rvv'),
    ('W1', 0x80005444, 0x8000545c, 'q288_gs32_rvv'),
    ('W3', 0x8000546c, 0x80005484, 'q288_gs32_rvv'),
    ('W2', 0x80005508, 0x80005520, 'q288_fused_rvv4'),
    ('classifier', 0x800055c8, 0x800055d0, 'q288_gs32_rvv'),
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
    sys.path.insert(0, str(controller))
    spec = importlib.util.spec_from_file_location('gs32_route_review_build', controller / 'build.py')
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    need(not output.exists(), 'fresh review output')
    record = b.read(build / 'result.json')
    r, _ = b.support(Path(record['parent_campaign']))
    elf_path = build / (b.PREFIX + '.elf')
    dis_path = build / 'disassembly.stdout.log'
    need(b.digest(elf_path) == ELF_SHA and b.digest(dis_path) == DIS_SHA, 'reviewed exact ELF and disassembly')
    elf = r.b.base.f.g.ELF(elf_path.read_bytes())
    word = lambda pc: struct.unpack('<I', elf.read(pc, 4))[0]
    evidence = lambda pcs: [dict(pc=hex(pc), bytes=elf.read(pc, 4).hex(), word=f'{word(pc):08x}') for pc in pcs]

    def pair(pc, reg, operation=0x13):
        first, second = word(pc), word(pc + 4)
        need(first & 0xfff == ((reg << 7) | 0x17), 'AUIPC destination at ' + hex(pc))
        need(second & 0xfffff == ((reg << 15) | (reg << 7) | operation), 'paired instruction at ' + hex(pc + 4))
        return (pc + signed(first & 0xfffff000, 32) + signed(second >> 20, 12)) & ((1 << 64) - 1)

    begin, size, *_ = elf.symbols['consumer_gs32_cache']
    need(begin == 0x80004e64 and size == 2088, 'complete reviewed consumer function bounds')
    words = {pc: word(pc) for pc in range(begin, begin + size, 4)}
    need(all(value & 3 == 3 for value in words.values()), 'complete 32-bit instruction stream')
    actual = [pc for pc, target in b.calls(dis_path.read_text()) if begin <= pc < begin + size and target == 'route_matmul']
    need(actual == [site[2] for site in SITES], 'all eight call relocations without omission')
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
        need(not any(setup < target <= call + 4 for target in targets), 'no direct branch enters pointer/call interior')
        for pc in range(setup + 8, call, 4):
            value = word(pc)
            opcode = value & 127
            need(opcode not in (0x63, 0x6f, 0x67), 'straight-line argument preparation')
            need(opcode in (0x23, 0x27) or (value >> 7) & 31 != 15, 'no a5 overwrite')
        route_calls.append(dict(site=label, pc=hex(call), jalr_pc=hex(call + 4), kernel=kernel,
            kernel_address=hex(address), instruction_evidence=evidence(range(setup, call + 8, 4)),
            straight_line_pointer_setup=True, no_a5_overwrite=True, no_direct_branch_interior_entry=True))

    fixed = {
        0x80002c14: 0x30000813, 0x80002c18: 0x00078a13,
        0x80002c28: 0x12000793, 0x80002c2c: 0x1b068663,
        0x80002dd8: 0x04f70863, 0x80002ce8: 0x000a00e7,
        0x80002d88: 0x000a00e7, 0x80002ea4: 0x00ea0663,
        0x80002eb0: 0x05010513, 0x80002eb4: 0x000780e7,
        0x80006180: 0x00058493, 0x800062d4: 0x00400793,
        0x800062d8: 0x0297e663, 0x80006304: 0x00000513,
    }
    for pc, value in fixed.items():
        need(word(pc) == value, 'manually reviewed selector or method-domain instruction: ' + hex(pc))
    need(pair(0x80002e94, 14) == elf.symbols['q288_fused_rvv4'][0], 'FR pointer comparison')
    need(pair(0x80002e9c, 15) == elf.symbols['q768_fr'][0], 'default W2 FR target')
    need(pair(0x80002ea8, 15) == elf.symbols['q768_ta'][0], 'non-FR alternative target')
    need(branch_target(0x80002ea4, word(0x80002ea4)) == 0x80002eb0, 'FR equality skips TA load')
    need(branch_target(0x800062d8, word(0x800062d8)) == 0x80006304, 'method above four returns zero')
    need(pair(0x80006518, 1, 0x67) == begin, 'new public entry calls new consumer clone')
    bodies = {}
    for name in ('consumer_gs32_cache', 'route_matmul', 'r2_w2_gs32_forward', 'r2_w2_forward'):
        pc, count, *_ = elf.symbols[name]
        bodies[name] = dict(pc=hex(pc), bytes=count, sha256=b.derive.sha(elf.read(pc, count)))
    result = dict(status='GS32_CONSUMER_ROUTING_REVIEW_PASS', elf_sha256=ELF_SHA,
        disassembly_sha256=DIS_SHA, route_calls=route_calls,
        w2_fr_selection=dict(kernel='q768_fr', pointer_comparison='q288_fused_rvv4',
            applicable_domain='fixed initialized model, K=768, output=288, recognized W2 tensor',
            instruction_evidence=evidence([0x80002c14, 0x80002c18, 0x80002c28, 0x80002c2c, 0x80002dd8] + list(range(0x80002e94, 0x80002eb8, 4)))),
        old_method_5_still_invalid=True,
        old_method_evidence=evidence([0x80006180, 0x800062d4, 0x800062d8, 0x80006304]),
        k288_full_and_tail_indirect_calls=evidence([0x80002ce8, 0x80002d88]),
        public_entry_call=evidence([0x80006518, 0x8000651c]),
        complete_function_bodies=bodies, checker_sha256=b.digest(Path(__file__)),
        checker_scope='fixed-ELF reproduction of manual instruction review; no runtime or performance claim',
        call_pc_convention='R_RISCV_CALL AUIPC address; jalr_pc records actual transfer instruction')
    b.save(output, result)
    print(json.dumps(dict(status=result['status'], output=str(output), sha256=b.digest(output),
        route_calls=len(route_calls), gs32=7, retained_w2_fr=1)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'controller', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    review(args.build.resolve(), args.controller.resolve(), args.output.resolve())
