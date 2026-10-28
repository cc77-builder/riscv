#!/usr/bin/env python3
"""Append the sealed C3-HF trial to three ledgers; no RTL/EDA/Git operations.

Run once from any directory. Old record/source containers are deep-compared;
pre-edit bytes and maintenance receipt stay outside the sealed evidence.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import copy
import gzip
import hashlib
import json
import re

MAIN = Path('/home/riscv/riscv-lab/zjhwork2-review-20261018/repo')
WORK = Path('/home/riscv/riscv-lab/o2-c3-hf-20261025')
MOD = MAIN / 'team/optimizations/o2/r3-div-gate/c3-hf'
REV = MOD / 'reviews'
ARCH = MOD / 'evidence/20261025-trial'
MAN = ARCH / 'manifest.json'
HEAD = '77d0a1228f0da7d584d5c7375b404dcda9763cf3'
BASE = '0f12df675378556670afd0dd2153f47fcb330610'
EXE = '150baa7c78aa8948ff0f4fb771912f7d2058aaa802a0853ee99ea3a2dc0bb9b7'
EXPECTED_MAN = 'd59cb0ebaec8209a8683ce3b3f97fafabc4daedbd50e0a2e0f36caf948d3ce31'
EXPECTED = {
    'version-data-ledger.json': 'ead9a206c8e2d8f4a8971e9b5e615cc9e9e286b621a201ba9f74da6a928200d7',
    'version-data-ledger-sources.json': '8cef7ad08b0e73f4d58b94037f96d28fc66ac66cb1425df9cbd67dedb79375f2',
    'version-data-ledger.md': '3ba85586f294c842decabd0c748f7a0828049efef659a77778e17ba7d241a638',
}
def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()
def sha(path):
    return sha_bytes(path.read_bytes())
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'
def rel(path):
    return str(path.relative_to(MAIN))
def table(columns, rows):
    return '\n'.join(['| ' + ' | '.join(columns) + ' |',
                      '| ' + ' | '.join(['---'] * len(columns)) + ' |'] +
                     ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in rows])
def result_tables(text):
    tables, block = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            block.append([v.strip() for v in line.strip().strip('|').split('|')])
        elif block:
            if len(block) >= 2:
                tables.append({'columns': block[0], 'rows': block[2:]})
            block = []
    return tables

assert MAN.is_file() and sha(MAN) == EXPECTED_MAN
manifest = read(MAN)
assert manifest['status'] == 'C3_HF_EVIDENCE_SEALED'
assert manifest['candidate_commit'] == HEAD and manifest['baseline_commit'] == BASE
old_bytes = {name: (MAIN / 'team/docs' / name).read_bytes() for name in EXPECTED}
assert {name: sha_bytes(data) for name, data in old_bytes.items()} == EXPECTED
old = json.loads(old_bytes['version-data-ledger.json'])
old_sources = json.loads(old_bytes['version-data-ledger-sources.json'])
old_md = old_bytes['version-data-ledger.md'].decode('utf-8')
assert len(old['records']) == 20
assert old['records'][-1]['record_id'] == 'C3-G0-20261025-01'
assert 'C3-HF' not in old['hardware_identities'] and 'c3_hf' not in old['source_tables']

candidate = read(WORK / 'candidate.json')
local = read(WORK / 'local-result.json')
final = read(WORK / 'final-record.json')
screen = read(WORK / 'cost-01/screen-01/result.json')
audit = read(WORK / 'independent-review/cost-final-01/audit.json')
local_audit = read(WORK / 'independent-review/local-audit.json')
q = read(WORK / 'cost-qualification.json')
mapping = read(WORK / 'cost-01/parent-map-01/summary.json')
sta = read(WORK / 'cost-01/parent-sta-01/summary.json')
campaign = read(WORK / 'cost-01/campaign.json')
targeted = read(WORK / 'cost-01/screen-01/state.json')
assert candidate['candidate_commit'] == HEAD and candidate['baseline'] == BASE
assert candidate['candidate_exeunit_sha256'] == EXE
assert candidate == read(MOD / 'candidate.json') == local['candidate']
assert final['local'] == local and final['cost'] == screen and final['adopted'] is False
assert screen['status'] == 'C3_HF_SCREEN_REJECT'
assert local['status'] == 'C3_HF_LOCAL_PASS'
assert audit['status'] == 'C3_HF_COST_INDEPENDENT_AUDIT_PASS'
assert local_audit['status'] == 'C3_HF_LOCAL_INDEPENDENT_AUDIT_PASS'
assert audit['screening_pass'] is False and audit['paths'] == 45 and audit['path_pass_count'] == 20
assert screen['candidate_head'] == audit['candidate_head'] == HEAD
assert sha(WORK / 'cost-01/screen-01/result.json') == audit['screen_result_sha256']
assert sha(WORK / 'cost-qualification.json') == screen['local_qualification_sha256']
assert screen['fullcore_authorized_by_gate'] is False and screen['inputs_unchanged'] is True
assert final['fullcore'] == final['cycles'] == 'NOT_TESTED'
assert candidate['contract_sha256'] == sha(MOD / 'CONTRACT.md')
assert candidate['patch_sha256'] == sha(MOD / 'c3-hf-production.patch')
profiles = ['nominal', 'period050', 'period200', 'load001', 'load020']
paths = ['r2r', 'i2r', 'vdot_r2r', 'vdot_i2r', 'vdot_r2o', 'ready', 'icg0', 'icg1', 'icg2']
comparisons = screen['comparisons']
assert len(comparisons) == 45
assert {(r['profile'], r['path']) for r in comparisons} == {(p, s) for p in profiles for s in paths}
assert sum(r['pass_'] for r in comparisons) == 20
assert len(screen['failures']) == 26
for version in ['before', 'after']:
    assert set(audit['states'][version]) == set(profiles)
    assert len(set(audit['semantics'][version].values())) == 3
    assert set(audit['semantics'][version]) == {
        'dut.elasticDivOccupied_divBusy', 'dut.uncer_en_reg', 'dut.uncer_en_reg_1'}
    for profile in profiles:
        assert set(audit['states'][version][profile]) == {'state0', 'state1', 'state2'}
assert audit['states']['after']['nominal']['state1']['arrival_ns'] == 0.557445
assert audit['states']['after']['nominal']['state2']['arrival_ns'] == 1.60977
assert screen['area_after'] == mapping['cell_area_sum'] == 285138.966
assert mapping['unknown_cells'] == [] and sta['gate_count'] == 3
assert len(campaign['steps']) == 3 and all(s['exit_code'] == 0 for s in campaign['steps'])
assert len(targeted['steps']) == 10 and all(s['exit_code'] == 0 for s in targeted['steps'])
assert len(sta['profiles']) == 5

# Newly selected pins are separate from every previous source namespace.
by_origin = {}
for entry in manifest['files']:
    by_origin.setdefault(entry['origin'], []).append(entry)
selected = {
    WORK / x for x in [
        'candidate.json', 'final-record.json', 'local-result.json', 'cost-qualification.json',
        'independent-review/local-audit.json', 'independent-review/source-review.json',
        'independent-review/cost-final-01/audit.json',
        'protocol-review/instrument-review.json', 'parent-replay.json',
        'cost-review/implementation-freeze.json',
        'cost-01/inputs.json', 'cost-01/preflight.json', 'cost-01/campaign.json',
        'cost-01/parent-cost-01/result.json', 'cost-01/parent-cost-01/command.json',
        'cost-01/parent-map-01/summary.json', 'cost-01/parent-sta-01/summary.json',
    ]
}
for e in manifest['files']:
    p = e['path']
    if p.startswith('source/c3-hf/'):
        selected.add(Path(e['origin']))
    if p.startswith('work/cost-01/screen-01/') and p.endswith(('.json', '.tcl')):
        selected.add(Path(e['origin']))
    for stage in ['fu-01', 'parent-01', 'supplement-02']:
        prefix = 'work/' + stage + '/'
        if p.startswith(prefix):
            name = p[len(prefix):]
            if '/' not in name and name.endswith(('.json', '.env', '.log')):
                selected.add(Path(e['origin']))

pins = {}
for p in sorted(selected):
    raw = p.read_bytes()
    entries = by_origin[str(p)]
    assert entries and all(e['raw_sha256'] == sha_bytes(raw) for e in entries), str(p)
    e = entries[0]
    assert e['raw_bytes'] == len(raw)
    archived = ARCH / e['stored']
    stored = archived.read_bytes()
    assert len(stored) == e['stored_bytes'] and sha_bytes(stored) == e['stored_sha256']
    unpacked = gzip.decompress(stored) if e['compression'] == 'gzip' else stored
    assert e['compression'] in ['gzip', 'none'] and unpacked == raw
    key = rel(p) if p.is_relative_to(MAIN) else str(p)
    pins[key] = {
        'sha256': sha_bytes(raw), 'bytes': len(raw), 'origin': str(p),
        'archive_manifest': rel(MAN), 'archive_entry': e['path'],
        'stored_path': rel(archived), 'stored_sha256': e['stored_sha256'],
        'stored_bytes': e['stored_bytes'], 'compression': e['compression'],
    }
for p in [MOD / 'RESULT.md', MAN]:
    key = rel(p)
    assert key not in pins
    pins[key] = {
        'sha256': sha(p), 'bytes': p.stat().st_size, 'origin': str(p),
        'role': 'frozen_result_document' if p.name == 'RESULT.md' else 'sealed_manifest',
        'scope': 'Repository document pinned directly; not a self-referential payload entry.'
    }

path_rows = []
for r in comparisons:
    b, a = r['before'], r['after']
    path_rows.append([r['profile'], r['path'],
        f"{b['arrival_ns']:.6f} / {b['slack_ns']:.6f}",
        f"{a['arrival_ns']:.6f} / {a['slack_ns']:.6f}",
        f"{r['delta_percent']:+.6f}%", 'PASS' if r['pass_'] else 'FAIL'])
state_rows = []
for key, label in [('state0', 'divBusy'), ('state1', 'FP hold'), ('state2', 'INT hold')]:
    b = audit['states']['before']['nominal'][key]
    a = audit['states']['after']['nominal'][key]
    state_rows.append([label, f"{b['arrival_ns']:.6f}", f"{a['arrival_ns']:.6f}",
                       f"{(a['arrival_ns']/b['arrival_ns']-1)*100:+.6f}%"])
columns = ['档位', '路径', '0f arrival / slack (ns)', 'C3-HF arrival / slack (ns)', 'arrival 变化', '筛选']
state_columns = ['控制 D 端', '0f (ns)', 'C3-HF (ns)', '变化']

record = {
    'record_id': 'C3-HF-20261025-01',
    'label': 'C3-HF 单点 FP DIV/SQRT 保持位置位候选：局部验证与同约束成本筛选',
    'identity_ids': ['DIV-fix0f', 'C3-HF'], 'source_ids': ['c3_hf'],
    'kind': 'actual_local_rtl_and_fixed_constraint_parent_cost_trial',
    'source_commit': HEAD, 'candidate_commit': HEAD, 'baseline_commit': BASE,
    'candidate_exeunit_sha256': EXE, 'candidate_patch_sha256': candidate['patch_sha256'],
    'contract_refs': [rel(MOD / 'CONTRACT.md'), rel(MOD / 'cost/CONTRACT.md')],
    'contract_sha256': candidate['contract_sha256'],
    'cost_contract_sha256': sha(MOD / 'cost/CONTRACT.md'),
    'source_snapshot_manifest_sha256': sha(WORK / 'cost-qualification.json'),
    'source_snapshot_manifest_path': str(WORK / 'cost-qualification.json'),
    'source_manifest_bindings': q['source_manifests'],
    'configuration': {
        'top': 'CommonParentCostTop', 'config': 'MinimalConfig(1)', 'mode': 'o2',
        'boundary': 'complete production VFEX4 parent', 'trace': False,
        'library': 'Nangate45 typical 25C/1.1V',
        'library_sha256': mapping['library_sha256'],
        'tool_versions': ['Yosys 0.9', 'ABC 1.01', 'OpenSTA 2.0.17'],
        'tool_manifest': '/home/riscv/riscv-lab/o4-cost-20261020/tools/executable-identities.json',
        'tool_manifest_sha256': sha(Path('/home/riscv/riscv-lab/o4-cost-20261020/tools/executable-identities.json')),
        'abc_D_ps': 1000, 'input_driver': 'BUF_X1', 'wire_load_model': sta['wire_load_model'],
        'clock_model': 'ideal', 'clock_uncertainty_ns': 0.05, 'clock_transition_ns': 0.05,
        'io_delay_ns': 0.1, 'TE': 0,
        'profiles': [{k: p[k] for k in ['profile', 'period_ns', 'load_ff']} for p in sta['profiles']],
        'local_artifact_identities': {s: read(WORK / s / 'artifacts.json')
                                     for s in ['fu-01', 'parent-01', 'supplement-02']},
        'fullcore_emu': 'NOT_TESTED', 'nemu_difftest': 'NOT_TESTED',
        'performance_images': 'NOT_TESTED',
    },
    'summary': 'Local RTL PASS; cost 20/45 PASS and 25/45 FAIL; area +0.184115%; worst three-state D -16.617459%; reject.',
    'decision': 'C3_HF_SCREEN_REJECT_NOT_ADOPTED_KEEP_DIV_FIX0F',
    'adopted': False, 'gating_trial_closed': True,
    'verification': {
        'numeric_rtl_complete_128bit': 'PASS', 'fu': 'PASS', 'real_parent': 'PASS',
        'supplement': 'PASS', 'control_monitor': local['hold_monitor']['status'],
        'independent_local_audit': local_audit['status'],
        'area_sta': 'VALID_REPORT_SCREEN_REJECT',
        'independent_cost_audit': audit['status'],
        'fullcore_difftest': 'NOT_TESTED', 'cycles': 'NOT_TESTED',
        'power': 'NOT_TESTED', 'fullcore_fmax': 'NOT_TESTED',
        'member_manual_reproduction': 'NOT_TESTED',
    },
    'execution': {
        'started_at': candidate['created'], 'finished_at': final['finished'],
        'local_stage_receipts': {s: read(WORK / s / 'runner.status.json')
                                for s in ['fu-01', 'parent-01', 'supplement-02']},
        'cost_campaign': campaign, 'targeted_sta': targeted,
        'new_production_generations': 1, 'new_synthesis_runs': 1,
        'new_standard_sta_profiles': 5, 'new_targeted_sta_runs': 10,
        'new_fullcore_runs': 0, 'new_cycle_runs': 0, 'github_writes': 0,
    },
    'metrics': {
        'local_result_at_completion': local,
        'parent_trace_replay': read(WORK / 'parent-replay.json'),
        'local_audit': local_audit,
        'cost': screen,
        'control_states_all_profiles': audit['states'],
        'control_semantic_D_bindings': audit['semantics'],
        'area_limit': 284899.560946, 'area_gate_pass': False,
        'control_limit_ns': 1.737526, 'control_gate_pass': True,
        'path_count': 45, 'path_pass_count': 20, 'path_fail_count': 25,
        'baseline_DFF_count': 17172,
        'candidate_DFF_count': sum(v for k, v in mapping['cell_histogram'].items() if k.startswith('DFF')),
        'candidate_cell_count': mapping['cell_count'],
        'unknown_cells': mapping['unknown_cells'], 'ICG_count': sta['gate_count'],
        'positive_slack_icg_preserved': all(r['after']['slack_ns'] >= 0 for r in comparisons
                                          if r['path'].startswith('icg') and r['before']['slack_ns'] >= 0),
        'fullcore_entry_open_by_numeric_screen': False,
        'cost_threshold_negative_observations': audit['threshold_observation_self_check'],
    },
    'input_identities': {
        'baseline_manifest_sha256': screen['baseline_manifest_sha256'],
        'qualification_sha256': sha(WORK / 'cost-qualification.json'),
        'generation_result_sha256': mapping['generation_sha256'],
        'mapped_verilog_sha256': mapping['mapped_sha256'],
        'mapped_json_sha256': mapping['mapped_json_sha256'],
        'sta_netlist_sha256': sta['name_binding']['sta_netlist_sha256'],
        'retained_baseline_exeunit_sha256': 'fd98aaced17c39dabd4776a53948f05650c8956178f6540bf5695d15753d60fa',
        'retained_baseline_emu_sha256': '2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8',
        'candidate_emu_sha256': 'NOT_TESTED',
    },
    'independent_cost_audit': {
        'status': audit['status'], 'screening_pass': audit['screening_pass'],
        'path': str(WORK / 'independent-review/cost-final-01/audit.json'),
        'sha256': sha(WORK / 'independent-review/cost-final-01/audit.json'),
        'input_files': audit['input_files'], 'input_hashes_unchanged': audit['input_hashes_unchanged'],
    },
    'raw_evidence_location': str(WORK), 'evidence_manifest_path': rel(MAN),
    'evidence_manifest_sha256': sha(MAN),
    'result_path': rel(MOD / 'RESULT.md'), 'result_sha256': sha(MOD / 'RESULT.md'),
    'final_record_path': str(WORK / 'final-record.json'),
    'final_record_sha256': sha(WORK / 'final-record.json'),
    'limitations': [
        'Only FP hold SET changed; no owner-state merge or gate+hold experiment.',
        'Local checker name C2_PARENT_SUPPLEMENT_PASS denotes reused suite; receipts bind this C3 candidate.',
        'Local-result area_sta NOT_TESTED is retained as its earlier timestamp; later actual cost is a separate metrics.cost object.',
        'Monitor proves observed valid synchronous-bootstrap domain, not async physical reset signoff or new exhaustive RTL formal proof.',
        'Mapping results are reference-library pre-layout costs; no post-route area, power, whole-core Fmax or new acceleration.',
        'Whole-parent ABC remapping can change unchanged-module paths; no unique Boolean-cause attribution.',
        'Observation negative controls are not RTL mutations; overlapping test counters are not summed into coverage percentage.',
        'supplement-01 infrastructure compile failure and later supplement-02 pass remain archived.',
        'Cost gate failed; no new fullcore/NEMU/cycle campaign; retain 0f and close current gating trial.',
    ],
}
new = copy.deepcopy(old)
new['generated_at'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
new['hardware_identities']['C3-HF'] = {
    'hardware_commit': HEAD, 'baseline_commit': BASE, 'exeunit_sha256': EXE,
    'patch_sha256': candidate['patch_sha256'], 'emu_sha256': 'NOT_TESTED',
    'kind': 'FP hold SET-only local trial; dual hold retained; cost rejected; not adopted',
}
new['records'].append(record)
new['source_tables']['c3_hf'] = {
    'source': rel(MOD / 'RESULT.md'),
    'tables': result_tables((MOD / 'RESULT.md').read_text(encoding='utf-8')),
    'complete_path_table': {'columns': columns, 'rows': path_rows},
    'control_nominal_table': {'columns': state_columns, 'rows': state_rows},
}
new['c3_hf_source_pins'] = pins
new['archive_pin_refs'].append(rel(MAN))
sources = copy.deepcopy(old_sources)
sources['c3_hf_sources'] = pins
sources['c3_hf_archive_manifest_path'] = rel(MAN)
sources['c3_hf_archive_manifest_sha256'] = sha(MAN)

# Preserve historical rows and sections; append the new dedicated section.
md = old_md
old_synopsis = next(line for line in md.splitlines() if line.startswith('历史部分只读取'))
new_synopsis = (
    '历史部分只读取已有成果，未重跑旧版本或补授资格。当前保留的生产实现是 '
    '**O2＋H1＋DIV 取消关钟修复 0f12df6**。C1、C2 已否决。C3-G0 的只读建议'
    '保留在第 10 节；随后实施的 **C3-HF 单次最小试验也已否决**：局部验证通过，'
    '面积 +0.184115% 超限，五档路径 20/45 通过、25/45 失败。三控制 D 最差虽下降 '
    '16.617459%，仍未通过完整合同。第 11 节追加本轮真实结果，旧记录保留各自当时状态。'
    '新全核/NEMU、周期、功耗和整核 Fmax 均 NOT_TESTED；当前门控试验关闭，0f 与原 EMU 不变。')
md = md.replace(old_synopsis, new_synopsis, 1)
count_old = '20 条工程记录（第20条为评审/抽象控制，非新硬件实测）'
count_new = '21 条工程记录（第20条为评审/抽象控制，第21条为 C3-HF 真实局部及成本试验）'
assert count_old in md
md = md.replace(count_old, count_new, 1)
row_anchor = next(line for line in md.splitlines() if line.startswith('| C3-G0 评审 |'))
version_row = (
    '| C3-HF 实测 | 仅 FP DIV/SQRT hold 置位去 ready 依赖；保留双 hold 和原 ICG 公式 '
    '| PASS（本轮新 FU、父级、补充及观察） | NOT_TESTED | NOT_TESTED '
    '| 面积超限；20/45 通过、25/45 失败 | REJECT，保留 0f，关闭当前门控试验 |')
md = md.replace(row_anchor, row_anchor + '\n' + version_row, 1)
identity_anchor = '| C2 | 6704ce3502a7235cdb81697638c01ed23f6914f6 | NOT_TESTED |'
assert identity_anchor in md
identity_row = f'| C3-HF | {HEAD} | NOT_TESTED |'
md = md.replace(identity_anchor, identity_anchor + '\n' + identity_row, 1)
new_section = f"""
## 11. C3-HF 单次最小试验：局部通过、成本否决（2026-10-25）

记录 ID：C3-HF-20261025-01。实际开始 {candidate['created']}，完成 {final['finished']}。
[结果](../optimizations/o2/r3-div-gate/c3-hf/RESULT.md)、
[生产合同](../optimizations/o2/r3-div-gate/c3-hf/CONTRACT.md)、
[成本合同](../optimizations/o2/r3-div-gate/c3-hf/cost/CONTRACT.md)。
**REJECT，不采用，保留 0f，关闭当前门控试验。** 此结论不改变任何历史版本加速比。

唯一候选 {HEAD}，ExeUnit SHA-256 {EXE}。
基线 {BASE}。仅 FP DIV/SQRT hold SET 从真实 fire 改为 P_F；
两个 hold、divBusy、ROB、原 ICG.E 公式、实际接受协议、整数和 VDot 保持。
该单点试验不构成 C1/C2 完整两因素归因，亦未实施 gate＋hold 更大改法。

### 11.1 本轮实际局部验证

| 层级 | 实际结果 |
| --- | --- |
| 主机检查 | 49 父级＋2 FU，共 51 项通过 |
| FU | 22 定向＋10,000 随机，完整 128 位结果；31,499 拍，4 个坏观察被拒绝 |
| 原真实父级 | 13 组、35,075 拍；16 个坏观察被拒绝；本轮严格轨迹重放通过 |
| 补充父级 | 115 场景、6 组、2,959 拍；7 个坏观察被拒绝；实际完成 attempt 为 supplement-02 |
| C3 hold 观察 | 2,958 拍有效初始化域内 P_F＝实际 FP fire；FP/INT hold 符合原 fire 递推；9 个坏观察被拒绝 |
| 实际观察覆盖 | 143 次 FP 接受、15 次普通 SQRT、54 次取消、291 拍 FP 反压、20 个 TE0 复位场景／40 拍复位 |
| 取消后关钟 | 54 窗口、162 个立即空闲采样；0 多余时钟 |
| 独立局部审计 | C3_HF_LOCAL_INDEPENDENT_AUDIT_PASS，1103 个输入、126 依赖 |
| 全核/NEMU、周期、功耗、整核 Fmax | NOT_TESTED |

4＋16＋7＋9 是运行时/离线坏观察拒错，非 RTL 变异；观察覆盖存在重叠，不能累计为唯一覆盖率。
旧 C3-G0 抽象论证只复用，没有重复计入本轮 RTL 验证。
supplement-01 的测试观察器编译宽度告警失败保留，修正测试表达式后新 supplement-02 通过；
未把基础设施失败伪装成候选通过，也未修改生产 RTL 以绕过门禁。
保持位观察结论限定于测试顶层实际采样的有效同步 bootstrap 域，不是异步物理复位签核。

### 11.2 同约束成本和三状态 D

采用相同 CommonParentCostTop/MinimalConfig(1)、Nangate45 typical 25°C/1.1V、
Yosys 0.9／ABC 1.01／OpenSTA 2.0.17。ABC -D 1000 ps；BUF_X1 输入驱动、
理想时钟、5K_hvratio_1_1 wireload、uncertainty/transition 各 0.05 ns、I/O delay 0.1 ns、TE=0。
五档为 nominal(1 ns,5 fF)、period050(0.5 ns,5 fF)、period200(2 ns,5 fF)、
load001(1 ns,1 fF)、load020(1 ns,20 fF)。
实际一次新生产生成、一次综合、五档常规 STA、两边各五档定向 STA；
无第二候选、映射挑选或阈值放宽。

| 指标 | 0f | C3-HF | 冻结门槛与判定 |
| --- | --- | --- | --- |
| 父级参考库单元面积和 | 284614.946 | 285138.966 | +0.184115%；上限 284899.560946，FAIL |
| 父级 DFF | 17172 | {record['metrics']['candidate_DFF_count']} | 实际映射，非预设数量 |
| 最差控制 D / ns | 1.930584 | 1.609770 | -16.617459%；上限 1.737526，PASS |
| ICG / 未知单元 | 3 / 0 | 3 / 0 | 完整生产边界 |
| 五档全部路径 | 45 项 | 20 PASS / 25 FAIL | 任一失败即否决 |

{table(state_columns, state_rows)}

两边均绑定 divBusy、FP hold、INT hold 三个不同 DFF 的 D。FP hold 显著缩短至 0.557445 ns，
但当前最差已转为 INT hold 1.609770 ns；不能只展示有利的 FP 单点。
配套 JSON 保留三状态全部五档 arrival、slack、实际起止点与语义到 D 引脚映射。

### 11.3 五档 45 项完整比较

每项 arrival 最多比同档 0f 增加 1%；基线非负的 ICG slack 仍须非负。
这是本项目冻结筛选合同，并非官方比赛阈值；相对 PASS 不表示绝对时序收敛。

{table(columns, path_rows)}

失败为面积 1 项，以及 VDot i2r、VDot r2o、ready、FP ICG.E、INT ICG.E
五类路径在五档中的 25 项；完整失败文本和实际起止点见配套 JSON。
原文独立成本审计 C3_HF_COST_INDEPENDENT_AUDIT_PASS，857 输入不变，
表明数据有效，**不表示候选通过成本筛选**。
父级 r2r 虽下降至 3.229321 ns，仍有负 slack；不得以其倒数冒充整核 Fmax。
完整父级 ABC 重映射可影响源码未改模块的路径；此数据不证明某一个布尔项是全部变化的唯一原因。

### 11.4 身份、原文与停止边界

[封存 manifest](../optimizations/o2/r3-div-gate/c3-hf/evidence/20261025-trial/manifest.json)
SHA-256：{sha(MAN)}。载荷 1131 份，包含实际新结果、局部/成本审计、
冻结输入、工具与二进制身份、原文路径和失败记录；压缩文件按 manifest 的 raw/stored 双 SHA 读取。
本台账将新来源仅追加到 c3_hf_source_pins／c3_hf_sources，旧 20 条及旧来源保持。

C3-HF 新 EMU、NEMU 差分、性能镜像及同镜像周期均 NOT_TESTED。保留 0f EMU
2d1db77cc407486a2387a4a69da2498b68d44980239025eebcc02370c02826e8，不能把它授予新候选。
本轮不产生新的加速比、功耗或比赛分数结论；当前门控支线结束，回到保留主线的稳定集成与 T17 干净复现。
"""
md = md.rstrip() + '\n\n' + new_section.strip() + '\n'

assert new['records'][:20] == old['records'] and len(new['records']) == 21
assert len({r['record_id'] for r in new['records']}) == 21
mutable_old_keys = {'generated_at', 'records', 'hardware_identities', 'source_tables', 'archive_pin_refs'}
for key in old:
    if key not in mutable_old_keys:
        assert new[key] == old[key], key
for key in ['hardware_identities', 'source_tables']:
    for name, value in old[key].items():
        assert new[key][name] == value, (key, name)
assert new['archive_pin_refs'][:len(old['archive_pin_refs'])] == old['archive_pin_refs']
assert all(sources[key] == value for key, value in old_sources.items())
assert new['records'][-1]['metrics']['cost'] == screen
assert new['records'][-1]['metrics']['local_result_at_completion'] == local
assert all(line in md.splitlines() for line in old_md.splitlines() if line.startswith('|'))
assert old_md[old_md.index('## 8.'):].rstrip() in md
assert sum(line.startswith('## 11.') for line in md.splitlines()) == 1 and len(path_rows) == 45
for target in re.findall(r'\]\(([^)]+)\)', md):
    if '://' not in target and not target.startswith('#'):
        target = target.split('#')[0]
        assert (MAIN / 'team/docs' / target).resolve().exists(), target

backup = REV / 'ledger-before-01'
assert not backup.exists(), 'Do not overwrite an earlier maintenance snapshot'
backup.mkdir()
for name, data in old_bytes.items():
    (backup / name).write_bytes(data)
outputs = {
    'version-data-ledger.json': dump(new),
    'version-data-ledger-sources.json': dump(sources),
    'version-data-ledger.md': md,
}
for name, content in outputs.items():
    assert sha(MAIN / 'team/docs' / name) == EXPECTED[name]
    (MAIN / 'team/docs' / name).write_text(content, encoding='utf-8', newline='\n')
again = read(MAIN / 'team/docs/version-data-ledger.json')
again_sources = read(MAIN / 'team/docs/version-data-ledger-sources.json')
assert again == new and again_sources == sources
assert sha(MAN) == EXPECTED_MAN
assert sha(MOD / 'RESULT.md') == record['result_sha256']
for key, p in pins.items():
    assert sha(Path(p['origin'])) == p['sha256'], key
receipt = {
    'status': 'C3_HF_LEDGER_APPEND_PRESERVATION_PASS',
    'time': datetime.now(timezone(timedelta(hours=8))).isoformat(),
    'record_id': record['record_id'], 'record_count_before': 20, 'record_count_after': 21,
    'old_records_deep_equal': again['records'][:20] == old['records'],
    'old_top_level_values_except_authorized_appends_unchanged': True,
    'old_hardware_identity_entries_unchanged': len(old['hardware_identities']),
    'old_source_table_entries_unchanged': len(old['source_tables']),
    'old_archive_ref_prefix_unchanged': len(old['archive_pin_refs']),
    'all_old_sources_file_keys_deep_equal': list(old_sources),
    'old_source_pins_deep_equal': again['source_pins'] == old['source_pins'],
    'old_c2_local_cost_and_c3_g0_pins_deep_equal': True,
    'old_markdown_table_rows_unchanged': True,
    'old_markdown_sections_8_through_10_unchanged': True,
    'new_source_pin_count': len(pins), 'new_source_pins_verified_against_actual_bytes': True,
    'selected_archived_payloads_verified_raw_and_stored': len(pins) - 2,
    'archive_manifest_sha256': EXPECTED_MAN,
    'old_three_file_sha256': EXPECTED,
    'new_three_file_sha256': {name: sha(MAIN / 'team/docs' / name) for name in EXPECTED},
    'new_record_matches_actual_local_and_screen_json': True,
    'cost_screen_status': screen['status'], 'path_count': 45, 'path_pass': 20, 'path_fail': 25,
    'area_gate_pass': False, 'three_state_control_gate_pass': True,
    'fullcore_and_cycles': 'NOT_TESTED', 'adopted': False, 'current_gating_trial_closed': True,
    'script_sha256': sha(Path(__file__)), 'github_writes': 0,
    'scope': 'Ledger maintenance only. No RTL, build, EDA, EMU, existing record/source or frozen evidence writes.'
}
(REV / 'ledger-maintenance-audit.json').write_text(dump(receipt), encoding='utf-8')
print(dump(receipt))
