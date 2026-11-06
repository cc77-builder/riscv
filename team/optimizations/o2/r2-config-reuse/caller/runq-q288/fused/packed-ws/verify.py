"""Independent checks for the actual three-word layout/load transformation.

No candidate assembly generator is imported here. The candidate's unchanged
instructions are bound to the complete baseline bodies; the three changed
words are decoded and checked, then their address streams are enumerated.
This is an equivalence certificate, not a cycle model or execution of a new
load opcode by the old finite instruction model.
"""
from collections import Counter
import hashlib
import struct

PAIRS = (('q288_tail_vdot', 'q288_ws_vdot'), ('q288_fused_rvv4', 'q288_ws_rvv4'))
LOAD_BEFORE = 0x0bc76607  # vlse32.v v12,(a4),t3, unmasked
LOAD_AFTER = 0x02076607   # vle32.v v12,(a4), unmasked
GROUP_BEFORE, GROUP_AFTER = 0x00470713, 0x02070713
TILE_BEFORE, TILE_AFTER = 0x0fc70713, 0x00070713
CHANGES = {LOAD_BEFORE: LOAD_AFTER, GROUP_BEFORE: GROUP_AFTER, TILE_BEFORE: TILE_AFTER}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def signed12(word):
    value = word >> 20
    return value-4096 if value & 2048 else value


def address_proof(group_step=32, tile_step=0, packed_indices=None):
    # Derive the inverse layout independently: consecutive groups of eight
    # lanes correspond to eight original rows, with nine scales per row.
    original = list(range(2592))
    if packed_indices is None:
        packed_indices = []
        for start in range(0, 2592, 72):
            rows = [original[start+9*r:start+9*r+9] for r in range(8)]
            packed_indices.extend(value for column in zip(*rows) for value in column)
    need(len(packed_indices) == 2592, 'exact packed scale extent')
    a4 = old_a4 = 0
    accessed, original_accessed = Counter(), Counter()
    for tile in range(36):
        need(a4 == old_a4 == tile*288, 'same tile boundary cursor')
        for group in range(9):
            for lane in range(8):
                address = a4 + 4*lane
                before = old_a4 + 36*lane
                need(0 <= address <= 10364 and address % 4 == 0, 'candidate scale buffer bound')
                need(0 <= before <= 10364 and before % 4 == 0, 'original scale buffer bound')
                need(packed_indices[address//4] == original[before//4],
                     'identical full 32-bit scale at tile/group/lane')
                accessed[address//4] += 1
                original_accessed[before//4] += 1
            a4 += group_step
            old_a4 += 4
        a4 += tile_step
        old_a4 += 252
    need(accessed == original_accessed == Counter({i: 1 for i in range(2592)}),
         'both representations read every scale exactly once')
    need(a4 == old_a4 == 10368, 'identical final cursor')
    return dict(groups=324, lanes_per_group=8, scale_words=2592,
                bytes_read=10368, exact_once=True, exact_values=True,
                initial_cursor=0, final_cursor=a4, required_alignment=4)


def pair_certificate(before, after, label):
    need(len(before) == len(after) and len(before) % 4 == 0, 'equal complete function sizes')
    old = list(struct.unpack('<'+'I'*(len(before)//4), before))
    new = list(struct.unpack('<'+'I'*(len(after)//4), after))
    locations = []
    for source, target in CHANGES.items():
        indices = [i for i, word in enumerate(old) if word == source]
        need(len(indices) == 1, 'one expected baseline scale instruction')
        i = indices[0]
        need(new[i] == target, 'exact candidate scale word')
        locations.append(dict(word_index=i, byte_offset=4*i, before=f'{source:08x}', after=f'{target:08x}'))
    changed = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
    need(changed == sorted(x['word_index'] for x in locations), 'all and only three changed words')
    # Decode all fields, independently of the source spelling.
    w = new[next(i for i, x in enumerate(old) if x == LOAD_BEFORE)]
    need((w & 127, (w >> 12) & 7, (w >> 7) & 31, (w >> 15) & 31,
          (w >> 20) & 31, (w >> 25) & 1, (w >> 26) & 3, w >> 28) ==
         (7, 6, 12, 14, 0, 1, 0, 0), 'unit-stride e32 load: v12/a4, vm=1, no extra fields')
    group = new[old.index(GROUP_BEFORE)]
    tile = new[old.index(TILE_BEFORE)]
    need(group & 0xfffff == tile & 0xfffff == 0x70713, 'a4 self-add operands')
    proof = address_proof(signed12(group), signed12(tile))
    # Prefix's six pointer reads include offset16/40; no entry-pointer read.
    need(old[:6] == [0x00053603, 0x00853883, 0x01053703, 0x01853283, 0x02053803, 0x02853683],
         'six-pointer ABI prefix')
    return dict(label=label, function_bytes=len(before), baseline_sha256=sha(before),
                candidate_sha256=sha(after), changes=locations, unchanged_word_count=len(old)-3,
                control_flow_bytes_unchanged=True, integer_fp_and_return_words_unchanged=True,
                architectural_instruction_count_unchanged=True, context_read_bytes=48,
                address_equivalence=proof, new_load_executed_by_old_numeric_model=False)


def certificate(elf):
    return {'status': 'PACKED_WS_ACTUAL_WORD_ADDRESS_EQUIVALENCE_PASS',
            'pairs': [pair_certificate(elf.symbol_data(a), elf.symbol_data(b), b) for a, b in PAIRS]}


def negative_controls(elf):
    rows = []
    for old_name, new_name in PAIRS:
        old, new = elf.symbol_data(old_name), elf.symbol_data(new_name)
        words = list(struct.unpack('<'+'I'*(len(new)//4), new))
        load_index = words.index(LOAD_AFTER)
        group_index = words.index(GROUP_AFTER)
        tile_index = words.index(TILE_AFTER)
        # Real full-function mutations are passed through the positive checker.
        for name, index, word in [('stride-load-retained', load_index, LOAD_BEFORE),
                                  ('old-group-step', group_index, GROUP_BEFORE),
                                  ('old-tile-step', tile_index, TILE_BEFORE),
                                  ('unexpected-prefix-change', 0, words[0] ^ (1 << 20))]:
            mutant = list(words); mutant[index] = word
            raw = struct.pack('<'+'I'*len(mutant), *mutant)
            try:
                pair_certificate(old, raw, new_name)
            except ValueError as error:
                rows.append(dict(function=new_name, mutation=name, rejected=str(error), mutant_sha256=sha(raw)))
            else:
                raise ValueError('mutated function was accepted: '+name)
    for name, args in [('row-major-as-packed', dict(packed_indices=list(range(2592)))),
                       ('wrong-group-cursor', dict(group_step=4)),
                       ('wrong-tile-cursor', dict(tile_step=252))]:
        try:
            address_proof(**args)
        except ValueError as error:
            rows.append(dict(mutation=name, rejected=str(error)))
        else:
            raise ValueError('incorrect layout/cursor accepted: '+name)
    return dict(status='PACKED_WS_EQUIVALENCE_NEGATIVE_CONTROLS_PASS', controls=rows)
