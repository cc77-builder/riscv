from pathlib import Path
from html import escape
import hashlib
import json
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
BG, INK, FILL, ACCENT = '#F6F3EE', '#242424', '#E8E3DC', '#CE4B32'
FONT = 'Microsoft YaHei, 微软雅黑, SimSun, 宋体, "Noto Sans CJK SC", sans-serif'
COMMIT = '0f12df675378556670afd0dd2153f47fcb330610'


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def source_record(name, repo_path, expected):
    data = (OUT / 'evidence' / name).read_bytes()
    for removed in range(3):
        candidate = data if removed == 0 else data[:-removed]
        if removed and data[-removed:] != b'\n' * removed:
            continue
        if blob(candidate) == expected:
            return {'path': repo_path, 'git_blob': expected, 'local_cache': 'evidence/' + name,
                    'local_sha256': hashlib.sha256(data).hexdigest(), 'local_git_blob': blob(data),
                    'canonical_git_blob': blob(candidate), 'appended_final_LF_bytes_removed_in_memory': removed,
                    'cache_modified': False}
    raise ValueError('Evidence does not match fixed source: ' + name)


source_files = [
    source_record('0f-VDotDatapath.scala', 'src/main/scala/xiangshan/backend/fu/vector/VDotDatapath.scala',
                  'e0703191ed2b626179e36fb40eb9741cdb843151'),
    source_record('0f-VDotElastic.scala', 'src/main/scala/xiangshan/backend/fu/wrapper/VDotElastic.scala',
                  '72d23e224bbfea13245865cc5a506ac87aed877b'),
]


class SVG:
    def __init__(self):
        self.parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="136mm" viewBox="0 0 1600 1360" role="img" aria-labelledby="title description">
<title id="title">VDot 点积算术与 P/R 寄存器边界</title>
<desc id="description">合法算术路径。每源低 64 位按八个有符号字节相乘，八个 16 位乘积进入 P。P 与 R 之间是组合归约：四个 17 位、两个 18 位、一个 19 位和，再符号扩展为 32 位进入 R。输出高 96 位为零。控制、异常与 perf 随事务同步迁移。三个加法层没有额外流水寄存器。</desc>
<defs><marker id="arrow" viewBox="0 0 14 14" refX="12" refY="7" markerWidth="14" markerHeight="14" markerUnits="userSpaceOnUse" orient="auto"><path d="M 1 1 L 12 7 L 1 13 Z" fill="{INK}"/></marker></defs>
<rect width="1600" height="1360" fill="{BG}"/>
<g font-family="{escape(FONT, quote=True)}" fill="{INK}" stroke-linecap="round" stroke-linejoin="round">
<g transform="translate(0,-70)">''']

    def group(self, name):
        self.parts.append(f'<g id="{name}">')

    def end(self):
        self.parts.append('</g>')

    def rect(self, x, y, w, h, fill=BG, stroke=INK, radius=5, width=2.8):
        self.parts.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{radius:g}" fill="{fill}" stroke="{stroke}" stroke-width="{width:g}"/>')

    def circle(self, x, y, r):
        self.parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{BG}" stroke="{INK}" stroke-width="2.8"/>')

    def text(self, x, y, value, size=44, anchor='middle', color=INK, bold=False):
        self.parts.append(f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" text-anchor="{anchor}" fill="{color}" font-weight="{"700" if bold else "400"}">{escape(value)}</text>')

    def line(self, points, arrow=True, dashed=False, color=INK, width=3):
        pts = ' '.join(f'{x:g},{y:g}' for x, y in points)
        extra = ' marker-end="url(#arrow)"' if arrow else ''
        if dashed:
            extra += ' stroke-dasharray="11 9"'
        self.parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width:g}"{extra}/>')

    def result(self):
        return '\n'.join(self.parts + ['</g>', '</g>', '</svg>', ''])


s = SVG()
s.text(705, 132, '两源各取低64位 · 8路有符号 INT8', 40)
s.text(1435, 132, '随事务保存', 40)
lanes = [200, 345, 490, 635, 780, 925, 1070, 1215]
sums17 = [(lanes[i] + lanes[i+1])/2 for i in range(0, 8, 2)]
sums18 = [(sums17[i] + sums17[i+1])/2 for i in range(0, 4, 2)]
total = (sums18[0] + sums18[1])/2

s.group('P-and-R-register-boundaries')
s.rect(125, 420, 1435, 125, FILL, radius=8)
s.rect(125, 1095, 1435, 115, FILL, radius=8)
s.text(65, 498, 'P', 52, color=ACCENT, bold=True)
s.text(65, 1169, 'R', 52, color=ACCENT, bold=True)
s.end()

s.group('arithmetic-connections')
for x in lanes:
    s.line([(x, 215), (x-68, 215), (x-68, 343), (x-22, 343)], arrow=False)
    s.line([(x, 315), (x+22, 315), (x+22, 343)], arrow=False)
    s.line([(x, 395), (x, 447)])
for j, x in enumerate(sums17):
    s.line([(lanes[j*2], 517), (lanes[j*2], 564), (x-22, 586)], arrow=False)
    s.line([(lanes[j*2+1], 517), (lanes[j*2+1], 564), (x+22, 586)], arrow=False)
for j, x in enumerate(sums18):
    s.line([(sums17[j*2], 643), (sums17[j*2], 683), (x-22, 736)], arrow=False)
    s.line([(sums17[j*2+1], 643), (sums17[j*2+1], 683), (x+22, 736)], arrow=False)
s.line([(sums18[0], 793), (sums18[0], 828), (total-22, 886)], arrow=False)
s.line([(sums18[1], 793), (sums18[1], 828), (total+22, 886)], arrow=False)
s.line([(total, 943), (total, 984)])
s.line([(total, 1049), (total, 1120)])
s.line([(total, 1185), (total, 1230), (1087.5, 1230), (1087.5, 1280)])
s.end()

s.group('eight-signed-products')
s.text(40, 194, 'vs1', 40, 'start')
s.text(40, 294, 'vs2', 40, 'start')
for i, x in enumerate(lanes):
    s.rect(x-55, 145, 110, 70)
    s.text(x, 193, f'a{i}')
    s.rect(x-55, 245, 110, 70)
    s.text(x, 293, f'b{i}')
    s.circle(x, 365, 30)
    s.text(x, 381, '×')
    s.rect(x-50, 447, 100, 70, radius=1)
    s.text(x, 495, '16')
s.end()

s.group('combinational-reduction')
for x in sums17:
    s.circle(x, 610, 33)
    s.text(x, 626, '+')
for x in sums18:
    s.circle(x, 760, 33)
    s.text(x, 776, '+')
s.circle(total, 910, 33)
s.text(total, 926, '+')
s.text(50, 625, '4 × 17位', 40, 'start')
s.text(50, 775, '2 × 18位', 40, 'start')
s.text(50, 925, '1 × 19位', 40, 'start')
s.line([(1255, 570), (1275, 570), (1275, 1060), (1255, 1060)], arrow=False, color=ACCENT, width=2.8)
s.text(1240, 835, '组合归约', 44, 'end', color=ACCENT)
s.rect(total-97.5, 984, 195, 65, FILL)
s.text(total, 1028, '19 → 32', 40)
s.text(870, 1028, '符号扩展', 40, 'start')
s.text(155, 1165, '结果槽', 40, 'start')
s.rect(total-90, 1120, 180, 65, radius=1)
s.text(total, 1165, '32')
s.end()

# The control/exception/perf names appear only once. Blank cells align with P/R.
s.group('control-exception-perf-sideband')
s.rect(1330, 165, 210, 150, FILL)
s.text(1435, 207, '控制', 40)
s.text(1435, 257, '异常', 40)
s.text(1435, 305, 'perf', 40)
s.line([(1435, 315), (1435, 447)], dashed=True)
s.rect(1330, 447, 210, 70, radius=1)
s.line([(1435, 517), (1435, 1120)], dashed=True)
s.rect(1334, 770, 202, 70, BG, BG, radius=0, width=0)
s.text(1435, 818, '同拍迁移', 40)
s.rect(1330, 1120, 210, 65, radius=1)
s.line([(1435, 1185), (1435, 1280)], dashed=True)
s.rect(1330, 1280, 210, 70, FILL)
s.text(1435, 1327, '随包输出', 40)
s.end()

s.group('full-vector-result')
s.rect(300, 1280, 675, 70, FILL, radius=0)
s.rect(975, 1280, 225, 70, BG, radius=0)
s.text(637.5, 1327, '高96位 = 0')
s.text(1087.5, 1327, '低32位')
s.text(750, 1395, '128位完整结果', 40)
s.end()

svg = s.result()
svg_path = OUT / 'S2-02.svg'
svg_path.write_text(svg, encoding='utf-8', newline='\n')
root = ET.fromstring(svg)
ns = {'s': 'http://www.w3.org/2000/svg'}
texts = root.findall('.//s:text', ns)
minimum = min(float(t.attrib['font-size']) for t in texts)
assert minimum >= 40
assert not root.findall('.//s:image', ns)
assert not root.findall('.//s:foreignObject', ns)

provenance = {
    'figure': 'S2-02', 'repository': 'cc77-builder/riscv', 'hardware_commit': COMMIT,
    'sources': source_files,
    'previous_review': {
        'file': 'evidence/previous-verification-notes.md',
        'sha256': hashlib.sha256((OUT/'evidence/previous-verification-notes.md').read_bytes()).hexdigest(),
    },
    'facts': [
        {'id': 'lane_inputs', 'source': 'VDotDatapath.scala', 'lines': [6, 21], 'value': {'lanes': 8, 'operand_bits_per_lane': 8, 'signed': True, 'used_operand_bits': [63, 0], 'ignored_operand_bits': [127, 64]}},
        {'id': 'P_products', 'source': 'VDotElastic.scala', 'lines': [38, 42], 'value': {'count': 8, 'bits': 16, 'registered': True}},
        {'id': 'balanced_reduction', 'source': 'VDotDatapath.scala', 'lines': [34, 45], 'value': [{'count': 4, 'bits': 17}, {'count': 2, 'bits': 18}, {'count': 1, 'bits': 19}], 'combinational': True},
        {'id': 'sign_extension', 'source': 'VDotDatapath.scala', 'lines': [47, 49], 'value': {'from_bits': 19, 'to_bits': 32}},
        {'id': 'R_data', 'source': 'VDotElastic.scala', 'lines': [45, 51], 'value': {'bits': 32, 'registered': True}},
        {'id': 'full_output', 'source': 'VDotElastic.scala', 'lines': [69, 74], 'value': {'bits': 128, 'high_96': 0, 'low_32': 'R.data'}},
        {'id': 'sideband', 'source': 'VDotElastic.scala', 'lines': [85, 107], 'value': 'accepted control including exception and write enables, plus perfDebugInfo, move with the same P-to-R transaction'},
        {'id': 'illegal_input', 'source': 'VDotElastic.scala', 'lines': [85, 107], 'value': 'illegal input disables destination writes; exception is retained and R data becomes zero', 'display': 'external caption'},
        {'id': 'earliest_latency', 'source': 'VDotElastic.scala', 'lines': [20, 24], 'value': {'accept': 'E0', 'P_to_R': 'E1', 'first_possible_response': 'E2', 'minimum_cycles': 2, 'initiation_interval_cycles': 1}, 'conditions': 'no blocking, input admissible, no cancellation', 'display': 'external caption'},
    ],
    'scope': {'VDotO2.enabled': True, 'VLEN': 128, 'arithmetic_path_shown': 'legal',
              'internal_slots': ['P', 'R'], 'extra_registers_between_reduction_levels': 0,
              'framework_latency': 'uncertain; the drawing is not a fixed-latency framework declaration',
              'functional_verification_performed': False},
    'layout': {'width_mm': 160, 'height_mm': 136, 'minimum_font_user_units': minimum,
               'minimum_font_pt_at_160mm': minimum*0.1*72/25.4,
               'body_font_pt_at_160mm': 44*0.1*72/25.4, 'font_stack': FONT,
               'colors': {'background': BG, 'ink': INK, 'fill': FILL, 'accent': ACCENT},
               'editable_text_nodes': len(texts), 'embedded_rasters': 0},
    'output': {'file': 'S2-02.svg', 'sha256': hashlib.sha256(svg_path.read_bytes()).hexdigest()},
}
(OUT/'sources.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'file': str(svg_path), 'sha256': provenance['output']['sha256'], **provenance['layout']}, ensure_ascii=False, indent=2))
