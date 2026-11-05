from pathlib import Path
from html import escape
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
INK='#263745'
BLUE='#285D84'
TEAL='#267A78'
GREY='#65747F'
FRAME='#B8CCD9'
FONT='Microsoft YaHei, 微软雅黑, SimSun, 宋体, "Noto Sans CJK SC", sans-serif'
parts=[]
nodes=[]
edges=[]

def emit(s):parts.append(s)
def text(x,y,s,anchor='middle',color=INK,size=41,weight=400):
    emit(f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(s)}</text>')
def rect(x,y,w,h,stroke=FRAME,fill='white',sw=1.8):
    emit(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def path(d,color=BLUE,arrow=False,sw=2,dashed=False):
    marker='teal' if color==TEAL else 'blue' if color==BLUE else 'ink'
    extra=f' marker-end="url(#{marker})"' if arrow else ''
    extra+=' stroke-dasharray="9 6"' if dashed else ''
    emit(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"{extra}/>')
def line(x1,y1,x2,y2,**kw):path(f'M {x1} {y1} L {x2} {y2}',**kw)
def op(id,x,y,label):
    emit(f'<g id="{id}"><circle cx="{x}" cy="{y}" r="22" fill="#F0F5FA" stroke="{BLUE}" stroke-width="1.8"/>')
    text(x,y+14,label,color=BLUE)
    emit('</g>')
    nodes.append({'id':id,'kind':'arithmetic_operator','operation':label})
def edge(a,b,kind):edges.append({'source':a,'target':b,'kind':kind})
def compare(id,y,label):
    emit(f'<g id="{id}"><path d="M 445 {y-32} L 480 {y} L 445 {y+32} L 410 {y} Z" fill="white" stroke="{INK}" stroke-width="1.8"/>')
    text(445,y+14,'?')
    text(445,y+72,label,color=GREY)
    emit('</g>')
    nodes.append({'id':id,'kind':'comparison_operation','result':None})

emit('<?xml version="1.0" encoding="UTF-8"?>')
emit('<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="126mm" viewBox="0 0 1600 1260" role="img" aria-labelledby="title desc">')
emit('<title id="title">S2-04 验证层级、实现范围与独立对照关系</title>')
emit('<desc id="desc">嵌套框表示整核含真实VFEX4父级、父级含VDot FU、FU含算术逻辑这一实现关系，并列出各层可观察维度；不表示测试集合全包含或同时进行一次测试。独立整数模型位于硬件之外，与完整128位算术结果对照；NEMU另与整核对应架构状态进行DiffTest差分。八路乘积与四二一归约仅标识算术范围，不增加流水级或时序含义。各层原证据独立保留，图中不预设通过。</desc>')
emit(f'<style>text {{font-family:{FONT};}}</style>')
emit('<defs>')
for name,col in [('blue',BLUE),('teal',TEAL),('ink',INK)]:
    emit(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto" markerUnits="userSpaceOnUse"><path d="M 1 1 L 9 5 L 1 9 Z" fill="{col}"/></marker>')
emit('</defs>')
rect(0,0,1600,1260,stroke='none')

# Hardware inclusion is real; coverage datasets and historical runs are separate.
layers=[
    ('core',500,40,1050,1160,'整核差分','架构状态 · 异常 · 别名','#F8FBFD'),
    ('parent',540,215,970,945,'真实 VFEX4','派发互斥 · 共享输出 · 门控','white'),
    ('fu',580,390,890,730,'VDot FU','握手 / 反压 · 身份 · flush/reset','#F5F9FC'),
    ('arith',620,565,810,515,'算术 RTL','完整 128 位结果','white')]
for id,x,y,w,h,name,obs,fill in layers:
    rect(x,y,w,h,stroke=BLUE,fill=fill,sw=1.8)
    text(x+48,y+63,name,anchor='start',color=BLUE,size=42,weight=500)
    text(x+48,y+123,obs,anchor='start',color=INK)
    nodes.append({'id':id,'kind':'tested_hardware_scope','label':name,'observation':obs})
for a,b in [('core','parent'),('parent','fu'),('fu','arith')]:edge(a,b,'implementation_contains_not_coverage_superset')

# The architectural reference and mathematical model are two distinct roles.
rect(40,70,330,140,stroke=TEAL,fill='#EFF7F6')
text(205,126,'NEMU',color=TEAL,size=42,weight=500)
text(205,182,'参考状态',color=TEAL)
nodes.append({'id':'nemu_ref','kind':'architectural_reference','label':'NEMU'})
line(370,140,409,140,color=TEAL,arrow=True,dashed=True)
line(500,140,481,140,color=BLUE,arrow=True,dashed=True)
compare('fullcore_compare',140,'差分')
edge('nemu_ref','fullcore_compare','REF_arch_state')
edge('core','fullcore_compare','DUT_corresponding_commit_state')

rect(40,820,330,225,stroke=TEAL,fill='#EFF7F6')
text(205,873,'独立整数模型',color=TEAL,size=42,weight=500)
text(205,931,'数学期望',color=TEAL)
text(205,992,'Σ(a × b)',color=TEAL)
nodes.append({'id':'math_model','kind':'independent_mathematical_reference','label':'独立整数模型'})

# A compact exact arithmetic tree identifies what is locally compared.
xs=[700+90*i for i in range(8)]
for i,x in enumerate(xs):op(f'mul_{i}',x,735,'×')
first=[(xs[2*i]+xs[2*i+1])/2 for i in range(4)]
for i,x in enumerate(first):
    for k,ch in enumerate(xs[2*i:2*i+2]):
        end=x-10 if k==0 else x+10
        path(f'M {ch} 757 V 770 L {end} 778',arrow=True)
        edge(f'mul_{2*i+k}',f'add1_{i}','product')
    op(f'add1_{i}',x,800,'+')
second=[(first[2*i]+first[2*i+1])/2 for i in range(2)]
for i,x in enumerate(second):
    for k,ch in enumerate(first[2*i:2*i+2]):
        end=x-10 if k==0 else x+10
        path(f'M {ch} 822 V 835 L {end} 843',arrow=True)
        edge(f'add1_{2*i+k}',f'add2_{i}','partial_sum')
    op(f'add2_{i}',x,865,'+')
for i,ch in enumerate(second):
    end=1015-10 if i==0 else 1015+10
    path(f'M {ch} 887 V 900 L {end} 908',arrow=True)
    edge(f'add2_{i}','add3','partial_sum')
op('add3',1015,930,'+')

# Complete field layout: high 96 zero / low 32 result. Arithmetic enters S only.
rect(860,995,430,50,stroke=BLUE,sw=1.8)
rect(1182.5,995,107.5,50,stroke=BLUE,fill='#F0F5FA',sw=1.8)
text(1021.25,1033,'0',color=GREY)
text(1236.25,1033,'S',color=BLUE)
path('M 1015 952 V 973 H 1236.25 V 994',arrow=True)
nodes.append({'id':'full128','kind':'observed_result_field','bits':128,'high_96':0,'low_32':'S'})
edge('add3','full128','arithmetic_result_to_low32_only')

# Observation routes cross scope boundaries; they are testbench comparison, not
# hardware wiring joining the five layers into one executed test.
line(860,1020,481,1020,color=BLUE,arrow=True,dashed=True)
line(370,1020,409,1020,color=TEAL,arrow=True,dashed=True)
compare('arithmetic_compare',1020,'对照')
edge('full128','arithmetic_compare','actual_full128')
edge('math_model','arithmetic_compare','expected_full128')
text(800,1240,'框线表示实现范围；各层分别核验',color=GREY)
emit('</svg>')

svg='\n'.join(parts)+'\n'
ET.fromstring(svg)
target=ROOT/'S2-04-validation-layers.svg';target.write_text(svg,encoding='utf-8',newline='\n')
manifest={'figure':'S2-04','version':'validation-layers-svg-v1','canvas_mm':[160,126],
          'minimum_source_font_pt':41*160/1600*72/25.4,'maximum_source_font_pt':42*160/1600*72/25.4,
          'nodes':nodes,'edges':edges,'svg_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
          'scope_note':'Hardware inclusion and independent observations, not a statistical coverage-superset diagram or a single fresh PASS.',
          'arithmetic_inset_note':'Legal arithmetic only; no input sampling, pipeline, clock, or control-coverage claim.',
          'pdf_export':'text to paths; accurate editable text retained in SVG'}
(ROOT/'diagram-structure.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'svg':str(target),'sha256':manifest['svg_sha256'],'font_pt':[manifest['minimum_source_font_pt'],manifest['maximum_source_font_pt']]}))
