from pathlib import Path
from html import escape
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
INK = '#263745'
BLUE = '#285D84'
TEAL = '#267A78'
BLUE_FILL = '#F0F5FA'
TEAL_FILL = '#EFF7F6'
GREY = '#65747F'
STROKE = '#CFDAE2'
FONT = 'Microsoft YaHei, 微软雅黑, SimSun, 宋体, "Noto Sans CJK SC", sans-serif'
parts=[]
nodes=[]
edges=[]

def emit(s):parts.append(s)
def text(x,y,s,anchor='middle',color=INK,size=41,weight=400):
    emit(f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(s)}</text>')
def rect(x,y,w,h,stroke=STROKE,fill='white',rx=0,sw=1.8):
    emit(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def line(x1,y1,x2,y2,color=INK,arrow=False,sw=2.2):
    marker={'#285D84':'blue','#267A78':'teal'}.get(color,'ink')
    end=f' marker-end="url(#{marker})"' if arrow else ''
    emit(f'<path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="{color}" stroke-width="{sw}"{end}/>')
def path(d,color=INK,arrow=False,sw=2.2):
    marker={'#285D84':'blue','#267A78':'teal'}.get(color,'ink')
    end=f' marker-end="url(#{marker})"' if arrow else ''
    emit(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"{end}/>')
def operator(name,x,y,label,color,fill,r=24):
    emit(f'<g id="{name}"><circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{color}" stroke-width="2"/>')
    text(x,y+14,label,color=color)
    emit('</g>')
    nodes.append({'id':name,'kind':'operator','operation':label,'center':[x,y]})
def edge(source,target,role):edges.append({'source':source,'target':target,'role':role})

emit('<?xml version="1.0" encoding="UTF-8"?>')
emit('<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="122mm" viewBox="0 0 1600 1220" role="img" aria-labelledby="title desc">')
emit('<title id="title">S3-01 两种独立求值结构及对应架构状态比较</title>')
emit('<desc id="desc">相同程序与初始状态分别进入RTL与NEMU。RTL示意八对有符号字节相乘及组合平衡归约；NEMU示意逐项乘法、从零开始的sum反馈及循环结束。算术结果仅写入各模型向量状态，CSR与异常来自各模型整体状态。三个中性比较节点分别接收一份DUT和一份参考的同类状态。图中不表示周期、完整硬件布线或测试通过。</desc>')
emit(f'<style>text {{font-family:{FONT};}} path,rect,circle {{vector-effect:non-scaling-stroke;}}</style>')
# Fixed user-unit stroke widths scale with the 160 mm native figure.
# Remove non-scaling stroke so both exports and inline embedding scale together.
parts[-1]=f'<style>text {{font-family:{FONT};}}</style>'
emit('<defs>')
for name,col in [('blue',BLUE),('teal',TEAL),('ink',INK)]:
    emit(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto" markerUnits="userSpaceOnUse"><path d="M 1 1 L 9 5 L 1 9 Z" fill="{col}"/></marker>')
emit('</defs>')
rect(0,0,1600,1220,stroke='none')

# Shared program / initial architectural state, without invented instructions.
text(800,57,'同一程序与初始状态',size=42)
line(800,82,800,125)
emit(f'<circle cx="800" cy="125" r="4" fill="{INK}"/>')
path('M 800 125 H 385 V 196',BLUE,True)
path('M 800 125 H 1215 V 196',TEAL,True)
edge('common_input','rtl_model','shared_program_initial_state')
edge('common_input','nemu_model','shared_program_initial_state')

# Two model boundaries. State rows belong to each complete model; they are not
# output ports of an arithmetic FU.
for x,col,fill,label in [(40,BLUE,BLUE_FILL,'RTL / 硬件求值'),(870,TEAL,TEAL_FILL,'NEMU / 参考求值')]:
    rect(x,200,690,920,stroke=col,rx=10,sw=1.9)
    rect(x+1,201,688,66,stroke='none',fill=fill,rx=8)
    text(x+32,247,label,anchor='start',color=col,size=44,weight=600)
    line(x+24,790,x+666,790,color=STROKE,sw=1.5)

# RTL: eight actual signed8 product nodes, then 4 + 2 + 1 combinational additions.
text(385,313,'8 对 signed8',color=BLUE)
xs=[133+72*i for i in range(8)]
for i,x in enumerate(xs):
    rect(x-27,335,24,35,stroke=BLUE,fill=BLUE_FILL,sw=1.6)
    rect(x+3,335,24,35,stroke=BLUE,fill='white',sw=1.6)
    line(x-15,370,x-10,392,BLUE,True,1.8)
    line(x+15,370,x+10,392,BLUE,True,1.8)
    operator(f'rtl_mul_{i}',x,416,'×',BLUE,BLUE_FILL)
    edge(f'rtl_a_{i}',f'rtl_mul_{i}','signed8_operand')
    edge(f'rtl_b_{i}',f'rtl_mul_{i}','signed8_operand')

level1=[(xs[2*i]+xs[2*i+1])/2 for i in range(4)]
for i,x in enumerate(level1):
    for k,child in enumerate(xs[2*i:2*i+2]):
        end=x-10 if k==0 else x+10
        path(f'M {child} 440 V 468 L {end} 497',BLUE,True)
        edge(f'rtl_mul_{2*i+k}',f'rtl_add1_{i}','product')
    operator(f'rtl_add1_{i}',x,521,'+',BLUE,BLUE_FILL)
level2=[(level1[2*i]+level1[2*i+1])/2 for i in range(2)]
for i,x in enumerate(level2):
    for k,child in enumerate(level1[2*i:2*i+2]):
        end=x-10 if k==0 else x+10
        path(f'M {child} 545 V 565 L {end} 577',BLUE,True)
        edge(f'rtl_add1_{2*i+k}',f'rtl_add2_{i}','partial_sum')
    operator(f'rtl_add2_{i}',x,601,'+',BLUE,BLUE_FILL)
for i,child in enumerate(level2):
    end=385-10 if i==0 else 385+10
    path(f'M {child} 625 V 641 L {end} 647',BLUE,True)
    edge(f'rtl_add2_{i}','rtl_add3','partial_sum')
operator('rtl_add3',385,671,'+',BLUE,BLUE_FILL)
line(385,695,385,730,BLUE,True)
text(80,746,'组合归约',anchor='start',color=GREY)
rect(315,730,140,50,stroke=BLUE,fill=BLUE_FILL,rx=6)
text(385,764,'D',color=BLUE)
edge('rtl_add3','rtl_result_D','signed_sum_to_32bit')

# NEMU: a software expression/variable loop, not a pipeline or eight DUT cycles.
text(1215,313,'i = 0 … 7',color=TEAL)
rect(1030,335,370,56,stroke=TEAL,fill=TEAL_FILL,rx=6)
text(1215,373,'a[i] , b[i]',color=TEAL)
line(1215,391,1215,419,TEAL,True)
operator('nemu_mul',1215,445,'×',TEAL,TEAL_FILL,r=26)
line(1215,471,1215,523,TEAL,True)
operator('nemu_add',1215,548,'+',TEAL,TEAL_FILL,r=25)
line(1215,573,1215,630,TEAL,True)
rect(1130,630,170,62,stroke=TEAL,fill=TEAL_FILL,rx=6)
text(1215,672,'sum',color=TEAL)
text(1102,673,'初值 0',anchor='end',color=GREY)
line(1108,660,1128,660,TEAL,True,1.8)
path('M 1300 661 H 1470 V 548 H 1241',TEAL,True)
text(1385,518,'循环',color=TEAL)
line(1215,692,1215,730,TEAL,True)
text(1310,724,'结束',anchor='start',color=GREY)
rect(1145,730,140,50,stroke=TEAL,fill=TEAL_FILL,rx=6)
text(1215,764,'R',color=TEAL)
for a,b,kind in [('nemu_pair','nemu_mul','signed8_pair'),('nemu_mul','nemu_add','product'),
                 ('nemu_add','nemu_sum','assignment'),('nemu_sum','nemu_add','software_feedback'),
                 ('zero','nemu_sum','initialization_only'),('nemu_sum','nemu_result_R','after_loop')]:edge(a,b,kind)

# Architecturally visible fields: three whole-row outputs per side.
centers=[907.5,981,1053.5]
field_names=['vector','vcsr','exception']
for prefix,x,col,fill,result,heading in [('dut',75,BLUE,BLUE_FILL,'D','对应提交状态'),
                                       ('ref',905,TEAL,TEAL_FILL,'R','参考架构状态')]:
    text(x,845,heading,anchor='start',color=col)
    rect(x,870,620,220,stroke=col,rx=5,sw=1.7)
    line(x,945,x+620,945,col,sw=1.4)
    line(x,1017,x+620,1017,col,sw=1.4)
    text(x+20,921,'vd[127:0]',anchor='start',color=INK)
    text(x+20,995,'向量 CSR',anchor='start',color=INK)
    text(x+20,1067,'异常状态',anchor='start',color=INK)
    # High 96 zero bits / low 32 result, true 3:1 field proportions.
    bx=x+280
    rect(bx,884,305,42,stroke=col,fill='white',sw=1.6)
    rect(bx+228.75,884,76.25,42,stroke=col,fill=fill,sw=1.6)
    text(bx+114.375,918,'0',color=GREY)
    text(bx+266.875,918,result,color=col)
    for offset,width,label in [(280,80,'vl'),(380,135,'vtype'),(535,50,'…')]:
        rect(x+offset,960,width,43,stroke=col,fill=fill,rx=3,sw=1.5)
        text(x+offset+width/2,993,label,color=col)
    rect(x+280,1026,305,55,stroke=col,fill=fill,rx=3,sw=1.5)
    text(x+432.5,1069,'异常信息',color=col)
    for name,y in zip(field_names,centers):
        nodes.append({'id':f'{prefix}_{name}','kind':'architectural_state_field','model':prefix,'row_y':y})

# Only each arithmetic result feeds its vector-result field. The other state
# fields remain properties of the whole model, with no arithmetic-to-CSR arrows.
path('M 455 755 H 621.875 V 882',BLUE,True,1.8)
path('M 1285 755 H 1451.875 V 882',TEAL,True,1.8)
edge('rtl_result_D','dut_vector','low32_field_only')
edge('nemu_result_R','ref_vector','low32_field_only')

for field,y in zip(field_names,centers):
    line(695,y,764,y,BLUE,True)
    line(905,y,836,y,TEAL,True)
    emit(f'<g id="compare_{field}"><path d="M 800 {y-31} L 835 {y} L 800 {y+31} L 765 {y} Z" fill="white" stroke="{INK}" stroke-width="1.8"/>')
    text(800,y+14,'?',color=INK)
    emit('</g>')
    nodes.append({'id':f'compare_{field}','kind':'comparison_operation','preselected_result':None})
    edge(f'dut_{field}',f'compare_{field}','DUT')
    edge(f'ref_{field}',f'compare_{field}','REF')
text(800,1188,'DiffTest',color=INK,size=42)
emit('</svg>')

svg='\n'.join(parts)+'\n'
ET.fromstring(svg)
assert len([n for n in nodes if n['id'].startswith('rtl_mul_')])==8
assert len([n for n in nodes if n['id'].startswith('rtl_add')])==7
for field in field_names:
    incoming=[e for e in edges if e['target']=='compare_'+field]
    assert len(incoming)==2 and {e['role'] for e in incoming}=={'DUT','REF'}
    assert {e['source'] for e in incoming}=={'dut_'+field,'ref_'+field}
assert not [e for e in edges if e['source'] in {'rtl_result_D','nemu_result_R'} and e['target'].endswith(('vcsr','exception'))]
target=ROOT/'S3-01-structural.svg'
target.write_text(svg,encoding='utf-8',newline='\n')
manifest={'figure':'S3-01','version':'structural-svg-v1','canvas_mm':[160,122],
    'font_user_units':{'body':41,'model_name':44,'shared_input_and_difftest':42},
    'minimum_font_pt':41*160/1600*72/25.4,'role_colors':{'DUT':BLUE,'REF':TEAL},
    'nodes':nodes,'edges':edges,'svg_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'scope':'Diagram of independent computation and matching architectural fields; no cycle axis, test result, or DiffTest-internal queue implementation.'}
(ROOT/'diagram-structure.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'svg':str(target),'sha256':manifest['svg_sha256'],'minimum_font_pt':manifest['minimum_font_pt'],'nodes':len(nodes),'edges':len(edges)},ensure_ascii=False))
