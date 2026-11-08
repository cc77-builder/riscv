"""O2 supplemental PC/pair selector. Offline summaries never grant target qualification."""
from pathlib import Path
import importlib.util
import json
import hashlib
from collections import defaultdict, Counter
from functools import cmp_to_key
HERE = Path(__file__).resolve().parent
reuse = json.loads((HERE / 'BASE_REUSE.json').read_text())['analyzer']
p = Path(reuse['path'])
assert p.stat().st_size == reuse['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == reuse['sha256'], 'Pinned base analyzer changed'
spec = importlib.util.spec_from_file_location('o2_cancel_frozen_sp1_analyzer', p)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def select(text, contract, require_hit=True):
    audit = base.analyze(text, require_complete=True, local=False)
    events, uart = base.extract_events_and_uart(text)
    pcmap = {int(k): v for k, v in contract['pc_roles'].items()}
    groups = defaultdict(list)
    for cycle, _, kind, row in events[1:]:
        groups[cycle].append((kind, row))
    live, bindings, retired = {}, {}, []
    for cycle, rows in sorted(groups.items()):
        def age(a, b):
            return 0 if a["rob"] == b["rob"] else 1 if base.flushed(a["rob"], b["rob"], 0) else -1
        for row in sorted([v for k, v in rows if k == "COMMIT"], key=cmp_to_key(age)):
            need(row["rob"] in live and "seq" in live[row["rob"]], "unbound retirement allocation")
            retired.append(live[row["rob"]]["seq"])
        for kind, row in rows:
            if kind == 'ENQUEUE':
                role = pcmap.get(row['pc'])
                need(role is not None, 'custom PC outside frozen supplemental image')
                need(row['word'] == role['word'], 'custom encoding differs from frozen object')
                live[row['rob']] = dict(row, role=role)
        for kind, row in rows:
            if kind == 'ACCEPT':
                need(row['rob'] in live, 'accept without exact allocation')
                e = live[row['rob']]
                need(row['seq'] not in bindings, 'duplicate allocation identity')
                need(row['vl'] == 8 and row['illegal'] == 0, 'supplement accepts illegal configuration')
                vpu = row['vpu']
                need(((vpu >> 187) & 255) == 0 and ((vpu >> 178) & 1) == 1 and ((vpu >> 170) & 255) == 0, 'frozen VTYPE/VM/VSTART contract mismatch')
                need(row['vs1'] & ((1 << 64) - 1) == e['role']['vs1_low64'], 'wrong active input A')
                need(row['vs2'] & ((1 << 64) - 1) == e['role']['vs2_low64'], 'wrong active input B')
                e['seq'] = row['seq']
                bindings[row['seq']] = dict(e, accepted=row)
    tx = {t['seq']: t for t in audit['transactions']}
    need(set(tx) == set(bindings), 'transaction allocation mismatch')
    commits = [row for _, _, kind, row in events if kind == 'COMMIT']
    if contract.get('expected_commits') is not None:
        need(len(commits) == contract['expected_commits'], 'complete custom retirement count mismatch')
    pc_counts, ordinals = Counter(), {}
    for seq in retired:
        pc = bindings[seq]['pc']
        ordinals[seq] = pc_counts[pc]
        pc_counts[pc] += 1
    if contract.get('expected_retired_pc_sequence') is not None:
        need([bindings[seq]['pc'] for seq in retired] == contract['expected_retired_pc_sequence'], 'retired PC sequence differs from frozen calls')
    witnesses = {'S0': [], 'S1': []}
    for cycle, rows in sorted(groups.items()):
        st = next((v for k, v in rows if k == 'STATE'), None)
        if not st or not (st['pvalid'] and st['rvalid']):
            continue
        pa, ra = tx[st['pseq']], tx[st['rseq']]
        pb, rb = bindings[st['pseq']], bindings[st['rseq']]
        pr, rr = pb['role'], rb['role']
        if not (pr['packet'] == 'B' and rr['packet'] == 'A' and pr['stage'] == rr['stage'] and pr['phase'] == rr['phase']):
            continue
        ec = pa['accept_cycle']
        erows = groups[ec]
        est = next(v for k, v in erows if k == 'STATE')
        # This exact A was already stalled when this exact B entered P.
        if not (pa['route'] == 'ENQUEUE_P' and est['rvalid'] and est['rseq'] == ra['seq'] and not est['outready'] and not est['pvalid']):
            continue
        immediate = next((v for k, v in groups.get(ec + 1, []) if k == 'STATE'), None)
        if not (immediate and immediate['pvalid'] and immediate['rvalid'] and immediate['pseq'] == pa['seq'] and immediate['rseq'] == ra['seq']):
            continue
        common = dict(phase=pr['phase'],r_seq=ra['seq'],p_seq=pa['seq'],a_pc=rb['pc'],b_pc=pb['pc'],r_rob=ra['rob'],p_rob=pa['rob'],enqueue_cycle=ec,dual_cycle=ec+1)
        if pr['stage'] == 'S0':
            if pa.get('outcome') == ra.get('outcome') == 'response' and pa['seq'] in ordinals and ra['seq'] in ordinals:
                witnesses['S0'].append(common)
        if pr['stage'] == 'S1':
            need('eligible_commit_ordinal' in rr, 'missing S1 probe allocation ordinal')
            if ordinals.get(ra['seq']) != rr['eligible_commit_ordinal']:
                continue
            red = next((v for k, v in rows if k == 'VFEX4_REDIRECT'), None)
            if not red or not st['killp'] or st['killr']:
                continue
            # Strict A < branch-origin < B. No fabricated branch-PC field.
            need(ra['rob'] != red['rob'] != pa['rob'], 'redirect origin must lie between packet ROB identities')
            need(not base.flushed(ra['rob'], red['rob'], red['self']) and base.flushed(pa['rob'], red['rob'], red['self']), 'actual ROB ages do not kill B and preserve A')
            need(pa.get('outcome') == 'kill' and pa.get('kill_slot') == 'P' and pa['end_cycle'] == cycle, 'P cancellation belongs to wrong transaction')
            need(ra.get('outcome') == 'response' and ra['end_cycle'] >= cycle, 'surviving A must respond exactly once at or after kill')
            # Base parser enforces no cancelled allocation commit, no duplicate response,
            # complete128 data, all state transitions, and the final idle/drained state.
            witnesses['S1'].append(dict(common,kill_cycle=cycle,redirect_rob=red['rob'],flush_itself=red['self'],survivor_response_cycle=ra['end_cycle']))
    # Multiple cycles may describe the same pair; retain one stable witness per pair.
    for stage in witnesses:
        witnesses[stage] = list({(w['r_seq'], w['p_seq']): w for w in witnesses[stage]}.values())
    hit = all(witnesses.values())
    if require_hit:
        need(hit, 'NOT_HIT: S0 pressure/P occupancy or S1 P-only cancellation missing')
    return dict(status='SUPPLEMENT_TRACE_HIT' if hit else 'SUPPLEMENT_TRACE_NOT_HIT',witnesses=witnesses,counts=audit['counts'],full128_checked_accepts=len(tx),custom_commits=len(commits),observer_input_sha256=audit['input_sha256'],target_run_qualified=False,performance_measured=False,scope='offline exact allocation/complete trace and supplemental pair selector only',branch_pc_dynamically_observed=False,f2v_grant_dynamically_observed=False)
