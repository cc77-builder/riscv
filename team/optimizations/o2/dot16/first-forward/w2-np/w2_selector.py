"""Inspect the real final ELF selector and the incoming kernel provenance.

Four fixed inputs only. A callee-saved register follows the standard RV64 ABI
across calls; this proof is not dynamic execution or a call-count claim.
"""
from pathlib import Path
import hashlib
import importlib.util
import struct


def need(ok, message):
    if not ok:
        raise ValueError(message)


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def branch(pc, w):
    offset = (w >> 31) << 12 | ((w >> 7) & 1) << 11 | ((w >> 25) & 63) << 5 | ((w >> 8) & 15) << 1
    return pc + signed(offset, 13)


def jump(pc, w):
    offset = (w >> 31) << 20 | ((w >> 12) & 255) << 12 | ((w >> 20) & 1) << 11 | ((w >> 21) & 1023) << 1
    return pc + signed(offset, 21)


def reach(graph, origin, blocked=frozenset()):
    pending, seen = [origin], set()
    while pending:
        pc = pending.pop()
        if pc in seen or pc in blocked:
            continue
        seen.add(pc); pending.extend(graph.get(pc, ()))
    return seen


def may_write(w, reg):
    # Stores, branches, fences and FP/vector loads have no integer destination.
    if (w & 127) in (0x23, 0x27, 0x63, 0x0f, 0x07, 0x43, 0x47, 0x4b, 0x4f):
        return False
    return reg != 0 and ((w >> 7) & 31) == reg


def inspect(elf):
    start, size, *_ = elf.symbols['route_matmul']
    need(size % 4 == 0 and 0 < size <= 32768, 'bounded 32-bit route function')
    raw = elf.read(start, size)
    words = {start + i: struct.unpack_from('<I', raw, i)[0] for i in range(0, size, 4)}
    need(all(w & 3 == 3 for w in words.values()), 'no compressed or incomplete route words')
    def pair(pc, reg):
        a, b = words.get(pc, 0), words.get(pc + 4, 0)
        if a & 0xfff != (reg << 7 | 0x17) or b & 0xfffff != (reg << 15 | reg << 7 | 0x13):
            return None
        return (pc + signed(a & 0xfffff000, 32) + signed(b >> 20, 12)) & ((1 << 64) - 1)
    entries = [(pc, reg) for pc in words for reg in range(1, 32)
               if pair(pc, reg) == elf.symbols['q288_fused_rvv4'][0]]
    need(len(entries) == 1, 'one actual FR constant starts the K768 selector')
    entry, constant_reg = entries[0]
    calls = [pc for pc in range(entry, min(entry + 256, start + size), 4)
             if words[pc] & 0x7f == 0x67]
    need(calls, 'bounded selector has a real indirect call')
    terminal = calls[0]; end = terminal + 4
    need((words[terminal] >> 7) & 31 == 1, 'selector terminates in jalr ra')
    graph, reverse = {}, {pc: set() for pc in words}
    direct, indirect_exits, abi_calls = [], [], []
    for pc, w in words.items():
        opcode, rd = w & 127, (w >> 7) & 31
        if opcode == 0x63:
            targets = [pc + 4, branch(pc, w)]; direct.append((pc, targets[1]))
            need(all(p in words for p in targets), 'all conditional successors remain inside route')
        elif opcode == 0x6f:
            need(rd in (0, 1), 'only ordinary direct jump or ABI call in route')
            target = jump(pc, w); direct.append((pc, target))
            if rd == 0 and target not in words:
                need(target == elf.symbols['matmul'][0], 'only known matmul tail exit')
            if rd == 1:
                need(target not in words, 'no intra-function call hides a selector entry')
            targets = [target] if rd == 0 else [pc + 4]
        elif opcode == 0x67:
            need((w >> 12) & 7 == 0 and rd in (0, 1), 'ordinary JALR encoding and ABI destination')
            if rd == 0:
                if w == 0x00008067:
                    indirect_exits.append(dict(pc=hex(pc), kind='canonical_ret'))
                else:
                    rs1 = (w >> 15) & 31; previous = words.get(pc - 4, 0)
                    need(previous & 0xfff == (rs1 << 7 | 0x17), 'resolved AUIPC/JALR external tail exit')
                    target = ((pc - 4 + signed(previous & 0xfffff000, 32) + signed(w >> 20, 12)) & ((1 << 64) - 1)) & ~1
                    need(target not in words and target == elf.symbols['matmul'][0], 'only original external matmul tail exit')
                    indirect_exits.append(dict(pc=hex(pc), kind='resolved_matmul_tail', target=hex(target)))
                targets = []
            else:
                targets = [pc + 4]; abi_calls.append(hex(pc))
        else:
            targets = [pc + 4]
        need(all(p % 4 == 0 for p in targets), 'aligned route control flow')
        graph[pc] = [] if pc == entry else [p for p in targets if p in words]
        for p in graph[pc]: reverse[p].add(pc)
    for row in indirect_exits:
        if row['kind'] == 'resolved_matmul_tail':
            pc = int(row['pc'], 16)
            need(reverse[pc] == {pc - 4}, 'tail JALR only entered through its address AUIPC')
    incoming = reach(graph, start) & reach(reverse, entry)
    need(entry in incoming, 'selector reachable from function entry')
    candidates = []
    for pc in incoming:
        w = words[pc]; reg = (w >> 7) & 31
        if (w & 0xfff07f) != ((15 << 15) | 0x13) or w >> 20 != 0 or reg not in (8, 9, *range(18, 28)):
            continue
        # ADDI saved-reg,a5,0 must dominate the selector; all paths retain a5 up to it.
        if entry in reach(graph, start, {pc}):
            continue
        prefix = reach(graph, start, {pc}) & reach(reverse, pc)
        if any(may_write(words[p], 15) or
               ((words[p] & 127) in (0x67, 0x6f) and (words[p] >> 7) & 31 != 0)
               for p in prefix):
            continue
        after = reach(graph, pc + 4) & incoming
        if any(may_write(words[p], reg) for p in after if p != entry):
            continue
        candidates.append((pc, reg, sorted(prefix), sorted(after)))
    need(len(candidates) == 1, 'one proved unmodified callee-saved copy of input a5')
    copied_at, saved_reg, prefix, after = candidates[0]
    known_callees = {elf.symbols[name][0] for name in ('matmul', 'memcpy') if name in elf.symbols}
    for pc in after:
        w = words[pc]; opcode = w & 127
        if opcode == 0x6f and (w >> 7) & 31 == 1:
            need(jump(pc, w) in known_callees, 'only source-declared ABI direct calls before selector')
        if opcode == 0x67 and (w >> 7) & 31 == 1:
            rs1 = (w >> 15) & 31
            if rs1 == saved_reg and signed(w >> 20, 12) == 0:
                continue  # The supplied four Q288 functions all follow RV64 ABI.
            previous = words.get(pc - 4, 0)
            need(previous & 0xfff == (rs1 << 7 | 0x17) and reverse[pc] == {pc - 4},
                 'other pre-selector call has an unavoidable actual AUIPC')
            target = ((pc - 4 + signed(previous & 0xfffff000, 32) + signed(w >> 20, 12)) & ((1 << 64) - 1)) & ~1
            need(target in known_callees, 'only source-declared ABI indirect calls before selector')
    need(not any(not (entry <= pc < end) and entry < target < end for pc, target in direct),
         'no external direct edge bypasses selector initialization')
    path = Path(__file__).with_name('selector_proof.py')
    spec = importlib.util.spec_from_file_location('bounded_w2_selector_proof', path)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    names = {'fr': ('q288_fused_rvv4', 'q768_fr'),
             'paired16': ('q288_paired16_rvv', 'q768_paired16_rvv'),
             'narrow': ('q288_dot16_whole8_narrow', 'q768_dot16_whole8_narrow'),
             'legacy_ta': ('q288_tail_vdot', 'q768_ta')}
    cases = {name: (elf.symbols[a][0], elf.symbols[b][0]) for name, (a, b) in names.items()}
    proof = helper.prove_selector(raw, start, entry, end, saved_reg, cases)
    return dict(function_address=hex(start), function_bytes=size,
                function_sha256=hashlib.sha256(raw).hexdigest(), entry=hex(entry), end=hex(end),
                constant_register=constant_reg, saved_kernel_register=saved_reg,
                input_a5_copy_pc=hex(copied_at), input_a5_copy_word=hex(words[copied_at]),
                copy_dominates_selector=True, all_paths_preserve_input_and_saved_register=True,
                callee_saved_rv64_abi_assumed_for_calls=True,
                abi_call_pcs=abi_calls, closed_indirect_exits=indirect_exits,
                no_external_direct_edge_into_selector_interior=True,
                relevant_pre_selector_instructions=[dict(pc=hex(p), word=hex(words[p]))
                    for p in sorted(set(prefix + after + [copied_at])) if p != entry],
                four_input_scope=names, selector_proof=proof, dynamic_call_count_claimed=False,
                arbitrary_other_pointer_behavior_proved=False)
