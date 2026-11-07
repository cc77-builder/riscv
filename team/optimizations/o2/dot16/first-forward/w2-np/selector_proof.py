"""Bounded RV64 pointer selection proof for four declared kernel addresses.

This helper does not locate the fragment or prove how the incoming a5 value
reaches saved_kernel_reg. The caller must prove that provenance, the fragment
boundaries and external incoming edges, and bind the addresses to qualified
functions in the same final ELF. Success covers only the four supplied inputs.

Only AUIPC, ADDI, BEQ/BNE, JAL x0 and one terminal JALR ra are accepted. No guest,
memory access, file access, compiler, or subprocess is used. end is exclusive;
the terminal call need not be the highest-address instruction in the fragment.
"""

from collections.abc import Mapping
import hashlib
import struct


MASK64 = (1 << 64) - 1


class SelectorProofError(ValueError):
    """The declared fragment does not satisfy this bounded proof contract."""


def _need(condition, message):
    if not condition:
        raise SelectorProofError(message)


def _signed(value, width):
    return value - (1 << width) if value & (1 << (width - 1)) else value


def _decode(word, pc):
    opcode, rd = word & 0x7f, (word >> 7) & 31
    funct3, rs1, rs2 = (word >> 12) & 7, (word >> 15) & 31, (word >> 20) & 31
    if opcode == 0x17:
        return dict(op='auipc', rd=rd, imm=_signed(word & 0xfffff000, 32))
    if opcode == 0x13 and funct3 == 0:
        return dict(op='addi', rd=rd, rs1=rs1, imm=_signed(word >> 20, 12))
    if opcode == 0x63 and funct3 in (0, 1):
        imm = ((word >> 31) << 12) | (((word >> 7) & 1) << 11)
        imm |= (((word >> 25) & 63) << 5) | (((word >> 8) & 15) << 1)
        return dict(op='beq' if funct3 == 0 else 'bne', rs1=rs1, rs2=rs2,
                    target=(pc + _signed(imm, 13)) & MASK64)
    if opcode == 0x6f and rd == 0:
        imm = ((word >> 31) << 20) | (((word >> 12) & 255) << 12)
        imm |= (((word >> 20) & 1) << 11) | (((word >> 21) & 1023) << 1)
        return dict(op='jal', target=(pc + _signed(imm, 21)) & MASK64)
    if opcode == 0x67 and funct3 == 0 and rd == 1:
        return dict(op='jalr', rs1=rs1, imm=_signed(word >> 20, 12))
    raise SelectorProofError(f'unsupported instruction at {pc:#x}: {word:08x}')


def prove_selector(code, base, entry, end, saved_kernel_reg, cases):
    """Return JSON-safe paths proving the four declared pointer mappings.

    code: immutable bytes, whose first byte has virtual address base.
    entry/end: the inclusive/exclusive bounds of the instruction fragment.
    saved_kernel_reg: externally proved incoming kernel register, x1..x31.
    cases: exactly four {name: (kernel_address, expected_target_address)} items.

    Addresses in the result are hexadecimal strings. Unknown values may be
    copied/computed into dead registers, but may never determine a branch or
    terminal target. The saved kernel register is read-only before the call.
    All words, even unvisited words, must belong to the supported subset; all
    direct successors stay inside the fragment. Only one call instruction is
    allowed. Cycles are rejected independently for each concrete input.
    """
    _need(isinstance(code, bytes), 'code must be immutable bytes')
    _need(all(type(x) is int for x in (base, entry, end, saved_kernel_reg)),
          'addresses and saved kernel register must be integers')
    _need(0 <= base <= entry < end <= base + len(code) <= 1 << 64,
          'fragment bounds must be contained in the supplied RV64 bytes')
    _need(base % 4 == entry % 4 == end % 4 == 0, '32-bit instruction alignment')
    _need(1 <= saved_kernel_reg <= 31, 'saved kernel register must be x1..x31')
    _need(isinstance(cases, Mapping) and len(cases) == 4, 'exactly four named input cases')
    checked_cases = []
    for name, addresses in cases.items():
        _need(isinstance(name, str) and bool(name), 'nonempty input case name')
        _need(isinstance(addresses, (tuple, list)) and len(addresses) == 2,
              f'{name}: expected a kernel/target address pair')
        kernel, target = addresses
        _need(all(type(x) is int and 0 <= x <= MASK64 and x % 4 == 0
                  for x in addresses), f'{name}: aligned unsigned RV64 function addresses')
        checked_cases.append((name, kernel, target))
    _need(len({kernel for _, kernel, _ in checked_cases}) == 4,
          'four distinct input kernel addresses')

    instructions, terminals = {}, []
    for pc in range(entry, end, 4):
        word = struct.unpack_from('<I', code, pc - base)[0]
        decoded = _decode(word, pc)
        decoded['word'] = word
        instructions[pc] = decoded
        _need(not (decoded['op'] in ('auipc', 'addi') and
                   decoded['rd'] == saved_kernel_reg),
              f'saved kernel register overwritten at {pc:#x}')
        if decoded['op'] == 'jalr':
            terminals.append(pc)
    _need(len(terminals) == 1, 'fragment must contain exactly one terminal JALR ra call')
    for pc, insn in instructions.items():
        if insn['op'] == 'jalr':
            continue
        successors = [] if insn['op'] == 'jal' else [pc + 4]
        if insn['op'] in ('beq', 'bne', 'jal'):
            successors.append(insn['target'])
        for successor in successors:
            _need(successor % 4 == 0 and entry <= successor < end,
                  f'out-of-fragment or misaligned successor {successor:#x} at {pc:#x}')

    paths, visited_union = {}, set()
    for name, kernel, expected in checked_cases:
        regs = [None] * 32
        regs[0], regs[saved_kernel_reg] = 0, kernel
        pc, seen, steps = entry, set(), []
        while True:
            _need(pc in instructions, f'{name}: execution left fragment at {pc:#x}')
            _need(pc not in seen, f'{name}: repeated PC / cycle at {pc:#x}')
            seen.add(pc)
            insn = instructions[pc]
            op = insn['op']
            row = dict(pc=hex(pc), word=f"{insn['word']:08x}", op=op)
            next_pc = pc + 4
            if op in ('auipc', 'addi'):
                source = pc if op == 'auipc' else regs[insn['rs1']]
                value = None if source is None else (source + insn['imm']) & MASK64
                rd = insn['rd']
                if rd:
                    regs[rd] = value
                row.update(rd=rd, value='unknown' if value is None else hex(value),
                           discarded=(rd == 0))
            elif op in ('beq', 'bne'):
                left, right = regs[insn['rs1']], regs[insn['rs2']]
                _need(left is not None and right is not None,
                      f'{name}: unknown branch operand at {pc:#x}')
                taken = (left == right) if op == 'beq' else (left != right)
                if taken:
                    next_pc = insn['target']
                row.update(rs1=insn['rs1'], rs2=insn['rs2'], left=hex(left),
                           right=hex(right), taken=taken)
            elif op == 'jal':
                next_pc = insn['target']
            else:  # The decoder admits only the one terminal JALR here.
                source = regs[insn['rs1']]
                _need(source is not None, f'{name}: unknown terminal target at {pc:#x}')
                target = ((source + insn['imm']) & MASK64) & ~1
                _need(target == expected,
                      f'{name}: terminal target {target:#x} != expected {expected:#x} at {pc:#x}')
                row.update(rs1=insn['rs1'], source=hex(source), imm=insn['imm'], target=hex(target))
                steps.append(row)
                paths[name] = dict(kernel=hex(kernel), expected_target=hex(expected),
                                   target=hex(target), terminal_pc=hex(pc), steps=steps)
                visited_union.update(seen)
                break
            row['next_pc'] = hex(next_pc)
            steps.append(row)
            pc = next_pc

    _need({row['terminal_pc'] for row in paths.values()} == {hex(terminals[0])},
          'all four inputs must reach the same terminal call')
    fragment = code[entry - base:end - base]
    return dict(status='FOUR_FIXED_INPUT_SELECTOR_TARGETS_VERIFIED',
                base=hex(base), entry=hex(entry), end=hex(end),
                fragment_bytes=len(fragment), fragment_sha256=hashlib.sha256(fragment).hexdigest(),
                saved_kernel_reg=saved_kernel_reg, terminal_pc=hex(terminals[0]), paths=paths,
                unvisited_pcs=[hex(pc) for pc in instructions if pc not in visited_union],
                caller_obligations=[
                    'Prove incoming a5 provenance into the saved kernel register at entry.',
                    'Prove fragment boundaries and exclude unproved external entries.',
                    'Bind input and expected target addresses to qualified functions in the same final ELF.'],
                scope='Only the four supplied kernel inputs; no whole-function or arbitrary-pointer proof.')
