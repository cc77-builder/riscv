#!/usr/bin/env python3
"""Documentation-only control-flow drawing from the frozen team NEMU patch.

SVG coordinates are millimetres. The diagram is not a new validation result.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'evidence'
STEM = 'S3-02-nemu-execution'
W, H = 160, 168
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
C = dict(ink='#24384A', teal='#287F84', gray='#637487', line='#CED9E2',
         pale='#F2F5F8', light='#E8F2F3', red='#AA4054', redlight='#F8EEF0')
FONT = 'Noto Sans CJK SC'

source = (SOURCE/'nemu-vdot.h').read_text(encoding='utf-8')
patch = (SOURCE/'nemu-vdot.patch').read_text(encoding='utf-8')
source_record = json.loads((SOURCE/'source-record.json').read_text(encoding='utf-8'))
assert hashlib.sha256((SOURCE/'nemu-vdot.patch').read_bytes()).hexdigest() == source_record['sha256']
assert hashlib.sha256((SOURCE/'nemu-vdot.h').read_bytes()).hexdigest() == source_record['extracted_source_sha256']
required = ['!vp_enable()', 'vtype->vill', 'vtype->pad', 'vtype->vsew != 0',
            'vtype->vlmul != 0', 'vl->val != 8', 'vstart->val != 0',
            'longjmp_exception(EX_II)', 'const uint64_t a', 'const uint64_t b',
            'int32_t sum = 0', 'i < 8', 'sum += x * y',
            'cpu.vr[vd]._64[0] = (uint32_t)sum', 'cpu.vr[vd]._64[1] = 0',
            'vp_set_dirty()']
assert all(s in source for s in required)
assert '0000001 ????? ????? 000 ????? 00010 11' in patch
assert source.index('longjmp_exception(EX_II)') < source.index('const uint64_t a')
assert source.index('const uint64_t b') < source.index('cpu.vr[vd]._64[0]')

def tag(name): return '{'+NS+'}'+name
svg = ET.Element(tag('svg'), dict(width=f'{W}mm', height=f'{H}mm',
    viewBox=f'0 0 {W} {H}', version='1.1', role='img'))
ET.SubElement(svg,tag('title')).text='NEMU vdot 的识别、状态检查与独立执行'
ET.SubElement(svg,tag('desc')).text=(
    'Exact custom-0 pattern matching is followed by all vector-state checks. '
    'Nonmatching instructions continue other decode. An illegal matched state '
    'raises cause 2 before source reads or destination writes. The legal path '
    'snapshots both low64 sources, calculates eight signed INT8 products, writes '
    'the entire 128-bit destination with high96 zero and low32 sum, then marks VS dirty. '
    'This is a source-level interpreter control flow, not DUT-cycle timing.')

def el(name, attrs, parent=svg):
    return ET.SubElement(parent,tag(name),{k:str(v) for k,v in attrs.items()})
defs=el('defs',{})
for name,colour in [('gray',C['gray']),('teal',C['teal']),('red',C['red'])]:
    marker=el('marker',{'id':name,'viewBox':'0 0 8 8','refX':7,'refY':4,
        'markerWidth':2.2,'markerHeight':2.2,'orient':'auto',
        'markerUnits':'userSpaceOnUse'},defs)
    el('path',{'d':'M 0 0 L 8 4 L 0 8 Z','fill':colour},marker)

def text(x,y,s,pt=11.5,colour=C['ink'],anchor='start',mono=False,bold=False):
    t=el('text',{'x':x,'y':y,'font-size':f'{pt*25.4/72:.6f}',
        'font-family':'DejaVu Sans Mono' if mono else FONT,
        'fill':colour,'text-anchor':anchor,'font-weight':'600' if bold else '400'})
    t.text=s
    return t
def rect(x,y,w,h,fill='white',stroke=C['line'],sw=.28):
    return el('rect',{'x':x,'y':y,'width':w,'height':h,'fill':fill,
                      'stroke':stroke,'stroke-width':sw})
def path(d,colour='gray',arrow=False,dash=None,sw=.32):
    a={'d':d,'fill':'none','stroke':C[colour],'stroke-width':sw}
    if arrow:a['marker-end']=f'url(#{colour})'
    if dash:a['stroke-dasharray']=dash
    return el('path',a)
def diamond(x,y,w,h):
    return el('path',{'d':f'M {x-w/2} {y} L {x} {y-h/2} L {x+w/2} {y} L {x} {y+h/2} Z',
                     'fill':'white','stroke':C['ink'],'stroke-width':.30})

rect(0,0,W,H,stroke='none')
text(80,7,'(inst & 0xFE00707F) == 0x0200000B',anchor='middle',mono=True)
path('M 50 11 V 17',arrow=True)
diamond(50,27,86,20)
text(50,28.5,'匹配 vdot？',pt=12,anchor='middle')
path('M 93 27 H 112',arrow=True)
text(102.5,23.3,'否',anchor='middle',colour=C['gray'])
rect(112,20,43,14,fill=C['pale'])
text(133.5,28.5,'其他译码',anchor='middle')

path('M 50 37 V 53',colour='teal',arrow=True)
text(56,46,'是',colour=C['teal'])
diamond(50,74,94,42)
text(50,67.3,'VS 启用 · vtype 合法',anchor='middle')
text(50,75.6,'e8 / m1 · vl = 8',anchor='middle')
text(50,83.9,'vstart = 0',anchor='middle')
path('M 97 74 H 112',colour='red',arrow=True)
text(104.5,70.3,'否',anchor='middle',colour=C['red'])
rect(112,60,43,29,fill=C['redlight'],stroke=C['red'])
text(133.5,68,'非法指令',anchor='middle',colour=C['red'])
text(133.5,76.2,'cause = 2',anchor='middle',mono=True,colour=C['red'])
text(133.5,84.4,'vd 不写回',anchor='middle',colour=C['red'])

path('M 50 95 V 104',colour='teal',arrow=True)
text(56,101,'是',colour=C['teal'])
rect(5,104,90,13,fill=C['light'],stroke=C['teal'])
text(50,112.4,'快照 vs1、vs2 的低64位',anchor='middle')
text(112,109,'允许目的/源别名',colour=C['gray'])
text(112,117,'先读，后写',colour=C['gray'])
path('M 101 110.5 H 95',dash='1 1')

path('M 50 117 V 126',colour='teal',arrow=True)
rect(5,126,90,13,fill='white',stroke=C['teal'])
text(50,134.4,'Σ a[i] × b[i]，i = 0…7',anchor='middle')
text(112,134.4,'有符号 INT8',colour=C['gray'])
path('M 50 139 V 148',colour='teal',arrow=True)
text(19,145.8,'127:32',colour=C['gray'],mono=True)
text(83.75,145.8,'31:0',colour=C['gray'],mono=True,anchor='middle')
rect(5,148,67.5,9,fill=C['pale'],stroke=C['gray'])
rect(72.5,148,22.5,9,fill=C['light'],stroke=C['teal'])
text(38.75,154.3,'高96位 = 0',anchor='middle')
text(83.75,154.3,'sum',anchor='middle',mono=True)
text(112,154.3,'128 位写回',colour=C['gray'])
path('M 50 157 V 161',colour='teal',arrow=True)
text(50,166,'VS ← Dirty',anchor='middle')

svg_path=ROOT/f'{STEM}.svg'
ET.indent(svg,space='  ')
svg_path.write_bytes(ET.tostring(svg,encoding='utf-8',xml_declaration=True))
pdf_path=ROOT/f'{STEM}.pdf'
subprocess.run(['inkscape',str(svg_path),'--export-area-page','--export-text-to-path','--export-type=pdf',
                f'--export-filename={pdf_path}'],check=True,capture_output=True)
subprocess.run(['pdftoppm','-r','250','-singlefile','-png',str(pdf_path),str(ROOT/STEM)],
               check=True,capture_output=True)

import fitz
with fitz.open(pdf_path) as doc:
    p=doc[0]
    spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b
           for l in b['lines'] for s in l['spans'] if s['text'].strip()]
    # Some CFF subsets had visually correct digits but incorrect ToUnicode.
    # Preserve text in the editable SVG; the delivery PDF uses vector outlines.
    assert not spans
    assert not p.get_images()
    assert p.get_drawings()
    outside=[]
    minpt=min(float(t.attrib['font-size'])*72/25.4 for t in svg.findall('.//'+tag('text')))
    assert minpt>=11.49,minpt
    fonts=[dict(zip(['xref','ext','type','basefont','name','encoding'],f[:6])) for f in p.get_fonts()]

srcdir=ROOT/'evidence'
srcdir.mkdir(exist_ok=True)
for name in ['nemu-vdot.h','nemu-vdot.patch']:
    if (SOURCE/name).resolve() != (srcdir/name).resolve():
        shutil.copy2(SOURCE/name,srcdir/name)
hashes={}
for p in [svg_path,pdf_path,ROOT/f'{STEM}.png',ROOT/'render.py',*srcdir.iterdir()]:
    raw=p.read_bytes()
    hashes[str(p.relative_to(ROOT))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
manifest={
 'figure':'S3-02','status':'candidate; human visual approval pending',
 'method':'exact SVG from frozen team NEMU source; no image generation or new execution',
 'geometry':{'width_mm':W,'height_mm':H,'minimum_text_pt':minpt,'outside_page':outside,
             'output_high_low_width_ratio':67.5/22.5},
 'pdf_fonts':fonts,'pdf_text_representation':'vector outlines; editable text retained in SVG',
 'font_size_basis':'SVG font-size in mm converted to pt at 160 mm physical width',
 'files':hashes,
 'source':{'repository':'cc77-builder/riscv','commit':'eca41d7cd959f5f3c4f240e382919c492d1ccb96',
           'path':'team/patches/nemu/vdot-s8x8-r32-v0.1.patch','patch_version':'1.1.0',
           'base_rev':'a48a11f208ff81ad765591d83271d1b339fb3861',
           'source_record':'evidence/source-record.json'},
 'required_adjacent_scope':[
  'Exact match only; other decoder paths decide whether nonmatching encodings are legal.',
  'vtype legality includes vill and reserved pad bits; e8/m1 means SEW8, LMUL1.',
  'Checks precede all source reads, destination writes and VS dirtying.',
  'sum is the low32 two-complement field, zero-extended to the complete 128-bit destination.',
  'VLEN128 and team contract scope; vl/vtype/vstart/vxrm/vxsat/vcsr unchanged on success.',
  'Exception xTVAL follows the fixed platform profile, with M-mode test coverage; no new privilege-mode proof.',
  'Source-level interpreter flow; no hardware-cycle, PASS or current-run claim.'],
 'visual_review':{'actual_pdf_png_viewed':False,'human_adopted':False}}
(ROOT/'source-and-review.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'figure':STEM,'geometry':manifest['geometry'],'files':hashes},ensure_ascii=False))
