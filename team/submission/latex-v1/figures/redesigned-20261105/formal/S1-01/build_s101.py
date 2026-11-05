from pathlib import Path
from html import escape
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
INK = '#263745'
BLUE = '#285D84'
TEAL = '#267A78'
GREY = '#65747F'
FRAME = '#CBD6DD'
BLUE_FILL = '#F0F5FA'
TEAL_FILL = '#EFF7F6'
FONT = 'Microsoft YaHei, 微软雅黑, SimSun, 宋体, "Noto Sans CJK SC", sans-serif'
parts=[]
nodes=[]
edges=[]

def emit(s): parts.append(s)
def text(x,y,s,anchor='middle',color=INK,size=41,weight=400):
    emit(f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(s)}</text>')
def rect(x,y,w,h,stroke=FRAME,fill='white',sw=1.7):
    emit(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def path(d,color=INK,arrow=False,dashed=False,sw=2):
    marker={BLUE:'blue',TEAL:'teal'}.get(color,'ink')
    extra=f' marker-end="url(#{marker})"' if arrow else ''
    extra+=' stroke-dasharray="10 7"' if dashed else ''
    emit(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"{extra}/>')
def line(x1,y1,x2,y2,**kwargs): path(f'M {x1} {y1} L {x2} {y2}',**kwargs)
def dot(x,y,color=INK): emit(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
def node(id,kind,label): nodes.append({'id':id,'kind':kind,'label':label})
def edge(source,target,kind): edges.append({'source':source,'target':target,'kind':kind})
def file_shape(id,x,y,w,h,label,color=INK,fill='white'):
    fold=20
    emit(f'<g id="{id}"><path d="M {x} {y} H {x+w-fold} L {x+w} {y+fold} V {y+h} H {x} Z" fill="{fill}" stroke="{color}" stroke-width="1.8"/>')
    path(f'M {x+w-fold} {y} V {y+fold} H {x+w}',color=color,sw=1.5)
    text(x+w/2,y+h/2+14,label,color=color)
    emit('</g>')

emit('<?xml version="1.0" encoding="UTF-8"?>')
emit('<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="120mm" viewBox="0 0 1600 1200" role="img" aria-labelledby="title desc">')
emit('<title id="title">S1-01 阶段一开发环境、构建产物与差分运行关系</title>')
emit('<desc id="desc">2026年10月9日历史环境的功能关系图。Windows宿主承载WSL2 Ubuntu，构建与运行位于WSL原生文件系统。香山Scala/Chisel生成RTL并编译为EMU；AM程序经ELF提取BIN；独立启动汇编产生启动flash；NEMU构建动态参考库。程序BIN与启动flash为两个不同输入，共同用于RTL执行和NEMU参考执行；EMU与参考库的运行使用另行连接。DiffTest比较对应的架构状态，不表示独立操作系统进程、网络拓扑、周期锁步或测试通过。实线为构建依赖，虚线为运行使用关系。</desc>')
emit(f'<style>text {{font-family:{FONT};}}</style>')
emit('<defs>')
for name,col in [('blue',BLUE),('teal',TEAL),('ink',INK)]:
    emit(f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto" markerUnits="userSpaceOnUse"><path d="M 1 1 L 9 5 L 1 9 Z" fill="{col}"/></marker>')
emit('</defs>')
rect(0,0,1600,1200,stroke='none')

# Environment containment only: no later Windows Git/release responsibilities.
rect(20,20,1560,1160,stroke=GREY,sw=1.8)
text(52,70,'Windows 宿主',anchor='start',weight=500)
line(865,55,925,55,arrow=True)
text(943,70,'构建依赖',anchor='start')
line(1200,55,1260,55,arrow=True,dashed=True)
text(1278,70,'运行使用',anchor='start')
rect(55,110,1490,1035,stroke=FRAME,sw=1.8)
text(90,163,'WSL2 · Ubuntu 22.04.5',anchor='start',weight=500)
text(1508,163,'原生文件系统',anchor='end',color=GREY)
line(78,185,1522,185,color=FRAME,sw=1.3)

# Four source inputs. The boot source is distinct from the AM program.
for id,x,w,col,labels in [
    ('hardware_source',100,280,BLUE,['香山硬件','Scala / Chisel']),
    ('am_source',470,280,INK,['AM 程序','hello / vadd']),
    ('boot_source',850,280,INK,['boot-flash.S']),
    ('nemu_source',1220,280,TEAL,['NEMU'])]:
    rect(x,215,w,110,stroke=col)
    if len(labels)==2:
        text(x+w/2,259,labels[0],color=col)
        text(x+w/2,304,labels[1],color=col)
    else: text(x+w/2,284,labels[0],color=col)
    node(id,'source',' / '.join(labels))

# Real intermediate artifacts are shown only where useful to the relationship.
line(240,325,240,399,color=BLUE,arrow=True)
text(267,375,'生成',anchor='start',color=GREY)
file_shape('rtl_artifact',100,400,280,70,'RTL',BLUE,BLUE_FILL)
line(240,470,240,539,color=BLUE,arrow=True)
text(267,517,'仿真编译',anchor='start',color=GREY)

line(610,325,610,399,arrow=True)
text(636,375,'编译',anchor='start',color=GREY)
file_shape('elf_artifact',500,400,220,70,'ELF')
line(610,470,610,539,arrow=True)
text(636,517,'提取',anchor='start',color=GREY)

for cx,col,label in [(990,INK,'编译 · 提取'),(1360,TEAL,'宿主编译')]:
    line(cx,325,cx,385,color=col)
    text(cx,435,label,color=GREY)
    line(cx,455,cx,539,color=col,arrow=True)

for id,x,w,label,col,fill in [
    ('emu_artifact',100,280,'EMU',BLUE,BLUE_FILL),
    ('program_bin',500,220,'程序 BIN',INK,'white'),
    ('flash_bin',850,280,'启动 flash',INK,'white'),
    ('reference_library',1220,280,'参考库',TEAL,TEAL_FILL)]:
    file_shape(id,x,540,w,90,label,col,fill)
    node(id,'build_artifact',label)
node('rtl_artifact','intermediate_artifact','RTL')
node('elf_artifact','intermediate_artifact','ELF')
for a,b in [('hardware_source','rtl_artifact'),('rtl_artifact','emu_artifact'),
            ('am_source','elf_artifact'),('elf_artifact','program_bin'),
            ('boot_source','flash_bin'),('nemu_source','reference_library')]: edge(a,b,'build_dependency')

# One logical differential run. The boundary is not an OS process map.
rect(90,650,1420,455,stroke=FRAME,fill='#FCFDFE',sw=1.7)
text(120,1080,'差分运行',anchor='start',color=GREY)

# The shared input node means the pair of distinct files, not byte concatenation.
path('M 610 630 V 715 H 800',dashed=True)
path('M 990 630 V 715 H 800',dashed=True)
dot(800,715)
text(800,695,'共同输入',color=INK)
line(800,715,800,765,dashed=True)
dot(800,765)
path('M 800 765 H 450 V 824',arrow=True,dashed=True)
path('M 800 765 H 1150 V 824',arrow=True,dashed=True)
edge('program_bin','common_inputs','runtime_input')
edge('flash_bin','common_inputs','runtime_input')
node('common_inputs','input_set','program BIN and separate shared boot flash')
edge('common_inputs','dut_role','shared_runtime_inputs')
edge('common_inputs','ref_role','shared_runtime_inputs')

# Build products are used by the corresponding execution roles.
line(240,630,240,824,color=BLUE,arrow=True,dashed=True)
text(269,750,'运行',anchor='start',color=BLUE)
line(1360,630,1360,824,color=TEAL,arrow=True,dashed=True)
text(1328,750,'--diff',anchor='end',color=TEAL)
edge('emu_artifact','dut_role','runtime_use')
edge('reference_library','ref_role','runtime_use_via_diff')

for id,x,w,col,fill,line1,line2 in [
    ('dut_role',180,380,BLUE,BLUE_FILL,'RTL 执行','DUT'),
    ('ref_role',1040,380,TEAL,TEAL_FILL,'NEMU 执行','REF')]:
    rect(x,825,w,100,stroke=col,fill=fill,sw=1.8)
    text(x+w/2,868,line1,color=col)
    text(x+w/2,910,line2,color=col,weight=500)
    node(id,'logical_execution_role',line1+' / '+line2)

# Exactly one state input from each model; no preselected equality/PASS result.
path('M 370 925 V 1018 H 639',color=BLUE,arrow=True,dashed=True)
path('M 1230 925 V 1018 H 961',color=TEAL,arrow=True,dashed=True)
text(502,990,'提交状态',color=BLUE)
text(1097,990,'参考状态',color=TEAL)
rect(640,965,320,105,stroke=INK,sw=1.8)
text(800,1008,'DiffTest',size=42)
text(800,1052,'架构状态比较')
node('difftest','architectural_comparison','DiffTest')
edge('dut_role','difftest','DUT_corresponding_commit_state')
edge('ref_role','difftest','REF_corresponding_arch_state')
emit('</svg>')

svg='\n'.join(parts)+'\n'
ET.fromstring(svg)
target=ROOT/'S1-01-environment.svg'
target.write_text(svg,encoding='utf-8',newline='\n')
manifest={'figure':'S1-01','version':'environment-svg-v1','canvas_mm':[160,120],
    'font_user_units':{'body':41,'difftest':42},'minimum_font_pt':41*160/1600*72/25.4,
    'scope_date':'2026-10-09','nodes':nodes,'edges':edges,
    'legend':{'solid':'build_dependency','dashed':'runtime_use_or_arch_state_flow'},
    'svg_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'limits':['environment containment, not physical network or OS process topology',
              'program BIN, boot flash and NEMU reference library remain separate files',
              'architectural correspondence, not DUT/reference cycle lockstep',
              'no 0f version identity, Windows Git/release policy, or measured PASS claim']}
(ROOT/'diagram-structure.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Preserve exact frozen source bytes and validate the Git blob identities.
evidence=ROOT/'evidence'; evidence.mkdir(exist_ok=True)
source_manifest=[]
for item in json.loads((ROOT/'source-api.json').read_text(encoding='utf-8')):
    data=item['content'].encode('utf-8')
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if blob != item['blob_sha']:
        raise ValueError('Frozen source blob mismatch: '+item['path'])
    suffix=Path(item['path']).suffix
    local=evidence/(item['key']+suffix)
    local.write_bytes(data)
    source_manifest.append({k:v for k,v in item.items() if k!='content'} | {
        'local':str(local.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_verified':True})
(ROOT/'sources.json').write_text(json.dumps(source_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'svg':str(target),'svg_sha256':manifest['svg_sha256'],'minimum_font_pt':manifest['minimum_font_pt'],
                  'frozen_source_count':len(source_manifest),'nodes':len(nodes),'edges':len(edges)},ensure_ascii=False))
