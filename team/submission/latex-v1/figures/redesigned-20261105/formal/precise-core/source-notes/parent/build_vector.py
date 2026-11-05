from pathlib import Path
from html import escape
import hashlib
import json
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
SOURCE = OUT / 'evidence' / '0f-ExeUnit.scala'
EXPECTED_BLOB = '8486333c3a4e51f5c2e6feb56c66c15b847ed2c5'
COMMIT = '0f12df675378556670afd0dd2153f47fcb330610'
BG, INK, FILL, ACCENT = '#F6F3EE', '#242424', '#E8E3DC', '#CE4B32'
FONT = 'Microsoft YaHei, 微软雅黑, SimSun, 宋体, "Noto Sans CJK SC", sans-serif'


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


raw_source = SOURCE.read_bytes()
if git_blob(raw_source) == EXPECTED_BLOB:
    canonical_source = raw_source
    normalization = 'none'
elif raw_source.endswith(b'\n') and git_blob(raw_source[:-1]) == EXPECTED_BLOB:
    canonical_source = raw_source[:-1]
    normalization = 'one appended final LF removed in memory only'
else:
    raise ValueError('The cached source does not match the fixed 0f Git blob.')


class SVG:
    def __init__(self):
        self.items = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="145mm" viewBox="0 0 1600 1450" role="img" aria-labelledby="title description">
<title id="title">VFEX4 的输入派发、独立门控与共享输出</title>
<desc id="description">固定 0f 版本的精确结构示意。三列依次为 VDot、VIDiv、VFDivSqrt。输入 bits 广播，valid 按许可及选中位限定；ready 使用 Mux1H 取选中功能单元。每列独立时钟门控。共享输出有效路至多一条，out.ready 广播。短标签表示同名网络连接，不表示新增端口或状态。</desc>
<defs>
 <marker id="arrow-ink" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" viewBox="0 0 14 14" refX="12" refY="7" orient="auto"><path d="M 1 1 L 12 7 L 1 13 Z" fill="{INK}"/></marker>
 <marker id="arrow-clock" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" viewBox="0 0 14 14" refX="12" refY="7" orient="auto"><path d="M 1 1 L 12 7 L 1 13 Z" fill="{ACCENT}"/></marker>
</defs>
<rect width="1600" height="1450" fill="{BG}"/>
<g font-family="{escape(FONT, quote=True)}" fill="{INK}" stroke-linecap="round" stroke-linejoin="round">''']

    def group(self, name):
        self.items.append(f'<g id="{name}">')

    def end(self):
        self.items.append('</g>')

    def text(self, x, y, value, size=40, anchor='middle', color=INK, bold=False):
        self.items.append(f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" text-anchor="{anchor}" fill="{color}" font-weight="{"700" if bold else "400"}">{escape(value)}</text>')

    def rect(self, x, y, w, h, fill=FILL, color=INK, width=2.6, radius=5):
        self.items.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{radius:g}" fill="{fill}" stroke="{color}" stroke-width="{width:g}"/>')

    def circle(self, x, y, r=5, color=INK):
        self.items.append(f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{color}"/>')

    def line(self, points, color=INK, dashed=False, arrow=True, width=3.3, bridge=False):
        pts = ' '.join(f'{x:g},{y:g}' for x, y in points)
        if bridge:
            self.items.append(f'<polyline points="{pts}" fill="none" stroke="{BG}" stroke-width="{width+10:g}"/>')
        extra = ' stroke-dasharray="11 9"' if dashed else ''
        if arrow:
            extra += f' marker-end="url(#{"arrow-clock" if color == ACCENT else "arrow-ink"})"'
        self.items.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width:g}"{extra}/>')

    def polygon(self, points, fill=FILL, color=INK, width=2.6):
        pts = ' '.join(f'{x:g},{y:g}' for x, y in points)
        self.items.append(f'<polygon points="{pts}" fill="{fill}" stroke="{color}" stroke-width="{width:g}"/>')

    def save(self):
        return '\n'.join(self.items + ['</g>', '</svg>', ''])


s = SVG()

# Logical expressions are separated from the three hardware columns.
s.group('input-admission-and-valid')
s.text(40, 55, '互斥派发', 44, 'start', bold=True)
s.text(40, 112, 'fuSel = acceptCond(in.bits)', 40, 'start')
s.text(40, 175, 'allow = ¬DIV忙', 40, 'start')
s.text(190, 230, '∧ (VDot请求 ∨ ¬VDot忙)', 40, 'start')
s.text(190, 285, '∧ ¬flush.valid ∧ ¬reset', 40, 'start')
s.text(40, 350, 'v[i] = in.valid ∧ allow ∧ fuSel[i]', 40, 'start')
s.text(40, 415, 'in.ready = allow ∧ selectedReady', 40, 'start')
s.end()

# rV/rI/rF are named nets from the in.ready pin of the matching column.
s.group('selected-child-ready')
s.text(1230, 55, 'r[i] = FU[i].in.ready', 40)
for x, name in [(1030, 'rV'), (1230, 'rI'), (1430, 'rF')]:
    s.text(x, 130, name, 40)
    s.line([(x, 145), (x, 205)], dashed=True)
s.polygon([(980, 205), (1480, 205), (1430, 310), (1030, 310)])
s.text(1230, 272, 'Mux1H', 44, bold=True)
s.line([(1550, 258), (1455, 258)])
s.text(1550, 180, 'fuSel', 40, 'end')
s.line([(1230, 310), (1230, 343)], dashed=True)
s.text(1230, 393, 'selectedReady', 40)
s.end()

# Exactly the bits field is broadcast. The local v* nets obey the expression above.
s.group('broadcast-input-data')
s.text(60, 470, 'in.bits 广播', 40, 'start')
s.line([(60, 505), (1510, 505)], arrow=False, width=3.6)
for x in [360, 860, 1360]:
    s.circle(x, 505)
    s.line([(x, 505), (x, 720)], width=3.6)
s.end()

# The output ready trunk is drawn first; crossing data paths get a background gap.
s.group('output-ready-broadcast')
s.line([(1550, 1375), (60, 1375)], dashed=True, arrow=False)
for spine, pin in [(545, 485), (1045, 985), (1545, 1485)]:
    s.circle(spine, 1375, 4)
    s.line([(spine, 1375), (spine, 995), (pin, 995), (pin, 960)], dashed=True)
s.text(1550, 1430, 'out.ready 广播', 40, 'end')
s.end()

columns = [
    {'x': 210, 'name': 'VDot', 'tag': 'V'},
    {'x': 710, 'name': 'VIDiv', 'tag': 'I'},
    {'x': 1210, 'name': 'VFDivSqrt', 'tag': 'F'},
]
for column in columns:
    x, name, tag = column['x'], column['name'], column['tag']
    center, valid_pin, ready_pin = x+150, x+215, x+275
    s.group(f'fu-{name}')
    s.line([(valid_pin, 645), (valid_pin, 720)])
    s.text(valid_pin, 622, 'v'+tag, 40)
    s.line([(ready_pin, 720), (ready_pin, 645)], dashed=True)
    s.text(ready_pin, 622, 'r'+tag, 40)
    s.rect(x, 720, 300, 240)
    s.text(center, 777, name, 44, bold=True)
    if tag == 'V':
        s.rect(x+35, 815, 80, 70, BG, radius=1)
        s.rect(x+185, 815, 80, 70, BG, radius=1)
        s.text(x+75, 863, 'P', 44)
        s.text(x+225, 863, 'R', 44)
        s.line([(x+115, 850), (x+185, 850)])
    elif tag == 'I':
        s.text(center, 885, '÷', 68)
    else:
        s.text(center, 880, '静态结构', 40)
    s.end()

    # Local same-name clk nets deliberately avoid every functional data branch.
    s.group(f'clock-gate-{name}')
    cg_x = x-120
    s.line([(x-180, 860), (cg_x, 860)], ACCENT, arrow=False)
    s.text(x-155, 835, 'clk', 40, color=ACCENT)
    s.rect(cg_x, 820, 90, 80, BG, ACCENT, radius=3)
    s.text(cg_x+45, 873, 'CG', 40, color=ACCENT)
    s.line([(cg_x+45, 780), (cg_x+45, 820)], ACCENT, arrow=False)
    s.text(cg_x+45, 759, 'en'+tag, 40, color=ACCENT)
    s.line([(cg_x+90, 860), (x, 860)], ACCENT, arrow=False)
    s.polygon([(x, 848), (x+16, 860), (x, 872)], BG, ACCENT)
    s.end()

s.group('shared-one-hot-output')
s.line([(360, 960), (360, 1080), (660, 1080), (660, 1120)], bridge=True)
s.line([(860, 960), (860, 1120)], bridge=True)
s.line([(1360, 960), (1360, 1080), (960, 1080), (960, 1120)], bridge=True)
s.polygon([(620, 1120), (1020, 1120), (980, 1240), (660, 1240)])
s.text(820, 1194, 'Mux1H', 44, bold=True)
s.line([(1190, 1175), (1002, 1175)], bridge=True)
s.text(1150, 1151, 'valid_i', 40)
s.line([(820, 1240), (820, 1300)])
s.text(820, 1350, '输出', 44, bold=True)
s.text(50, 1220, 'out.valid = OR(valid_i)', 40, 'start')
s.text(50, 1285, '至多一路有效', 40, 'start')
s.end()

svg = s.save()
svg_path = OUT / 'S2-03.svg'
svg_path.write_text(svg, encoding='utf-8', newline='\n')

sources = {
    'figure': 'S2-03',
    'repository': 'cc77-builder/riscv',
    'hardware_commit': COMMIT,
    'source': {
        'path': 'src/main/scala/xiangshan/backend/exu/ExeUnit.scala',
        'git_blob': EXPECTED_BLOB,
        'local_cache': 'evidence/0f-ExeUnit.scala',
        'local_sha256': hashlib.sha256(raw_source).hexdigest(),
        'local_git_blob': git_blob(raw_source),
        'canonical_git_blob': git_blob(canonical_source),
        'normalization': normalization,
        'cache_modified': False,
    },
    'diagram_aliases': {
        'fuSel': 'selected = VecInit(acceptCond(io.in.bits))',
        'allow': 'allowInput',
        'V': 'VDot',
        'I': 'VIDiv',
        'F': 'VFDivSqrt',
        'v[i]': 'sources(i).valid / corresponding child io.in.valid',
        'r[i]': 'corresponding child io.in.ready',
        'valid_i': 'corresponding output valid used for one-hot output selection',
        'clk': 'the same parent clock net at each independently gated FU',
        'enV_enI_enF': 'separate clk_en instances, not one shared enable net',
        'column_labels_are_funcUnits_indices': False,
    },
    'facts': [
        {'id': 'vdot_occupied', 'lines': [89, 91], 'expression': 'pValid || rValid'},
        {'id': 'div_occupied', 'lines': [166, 186], 'expression': 'divBusy || divOutValid || !divReady'},
        {'id': 'div_ready_internal', 'lines': [167, 173], 'expression': 'AND of the DIV child in.ready signals'},
        {'id': 'input_selection', 'lines': [300, 306], 'expression': 'selected = VecInit(acceptCond(io.in.bits))'},
        {'id': 'input_admission', 'lines': [307, 309], 'expression': '!elasticDivOccupied && (newIsVDot || !elasticVDotOccupied) && !io.flush.valid && !reset'},
        {'id': 'selected_ready', 'lines': [310, 311], 'expression': 'selectedReady = Mux1H(selected, funcUnits.map(_.io.in.ready)); io.in.ready = allowInput && selectedReady'},
        {'id': 'input_bits', 'lines': [312, 314], 'expression': 'source.bits = io.in.bits'},
        {'id': 'child_valid', 'lines': [312, 314], 'expression': 'source.valid = io.in.valid && allowInput && selected(i)'},
        {'id': 'output_one_hot_zero', 'lines': [332, 333], 'expression': 'PopCount(funcUnits.map(_.io.out.valid)) <= 1'},
        {'id': 'independent_clock_gates', 'lines': [95, 158], 'expression': 'a separate clk_en and ClockGate for each applicable FU'},
        {'id': 'vdot_clock_enable', 'lines': [146, 150], 'expression': 'elasticVDotOccupied || fu.io.in.fire || reset'},
        {'id': 'div_clock_release', 'lines': [126, 143], 'expression': 'hold state released on out.fire or matching elasticDivCancelled; old hold supplies the cancellation edge'},
        {'id': 'output_valid', 'lines': [696, 696], 'expression': 'Cat(fuOutValidOH).orR'},
        {'id': 'output_ready', 'lines': [697, 697], 'expression': 'all FU out.ready = parent io.out.ready'},
        {'id': 'output_data_select', 'lines': [699, 714], 'expression': 'Mux1H over the corresponding valid one-hot vectors for data and control fields'},
        {'id': 'output_identity_select', 'lines': [734, 737], 'expression': 'Mux1H(fuOutValidOH, fuOutBitsVec.map(_.perfDebugInfo))'},
    ],
    'scope': {
        'configuration_assumption': {'VDotO2.enabled': True, 'EnableClockGate': True},
        'configuration_source_lines': [67, 78, 95],
        'VFDivSqrt': 'static topology only; no dynamic coverage claim',
        'arbitration': 'no priority arbiter or queue added',
        'clock_net_routing': 'local named parent clk stubs; no crossing with functional data paths',
        'input_ready_net_routing': 'named rV/rI/rF nets terminate at the selected-ready Mux1H',
        'functional_verification_performed': False,
    },
    'layout': {
        'width_mm': 160,
        'height_mm': 145,
        'viewBox': [0, 0, 1600, 1450],
        'minimum_font_user_units': 40,
        'minimum_font_pt_at_160mm': 40 * 0.1 * 72 / 25.4,
        'body_font_user_units': 44,
        'body_font_pt_at_160mm': 44 * 0.1 * 72 / 25.4,
        'font_stack': FONT,
        'colors': {'background': BG, 'ink': INK, 'fill': FILL, 'accent': ACCENT},
    },
    'output': {'file': 'S2-03.svg', 'sha256': hashlib.sha256(svg_path.read_bytes()).hexdigest()},
}
(OUT / 'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

root = ET.fromstring(svg)
ns = {'s': 'http://www.w3.org/2000/svg'}
texts = root.findall('.//s:text', ns)
minimum = min(float(t.attrib['font-size']) for t in texts)
assert minimum >= 40
assert not root.findall('.//s:image', ns)
assert not root.findall('.//s:foreignObject', ns)
print(json.dumps({'file': str(svg_path), 'sha256': sources['output']['sha256'], 'width_mm': 160,
                  'height_mm': 145, 'editable_text_nodes': len(texts), 'minimum_font_pt': minimum*0.1*72/25.4,
                  'source_git_blob': sources['source']['canonical_git_blob']}, ensure_ascii=False, indent=2))
