"""Rebuild evidence figures from the frozen, attributed data beside this file.

Usage: python figures/build_evidence_figures.py [--preview-dir DIR]
Requires matplotlib, NumPy, installed Microsoft YaHei and SimSun;
PDF previews also use PyMuPDF. Plots, state diagrams, numbers and labels are
typeset from fixed data. No engineering program is executed by this script.
All plotted numbers come from source CSVs
or exact log records in evidence-20261105/figure-data.json. No new simulation.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import re
import shutil
from decimal import Decimal
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon
from matplotlib.transforms import Bbox
from matplotlib.text import Text
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "evidence-20261105/figure-data.json").read_text(encoding="utf-8"))
NAVY, TEAL, GRAY = "#24384A", "#287F84", "#637487"
LIGHT, PALE, LINE = "#E8F2F3", "#F2F5F8", "#CED9E2"
RED, AMBER = "#AA4054", "#A46B2E"
FONT_SANS, FONT_SERIF = 'Microsoft YaHei', 'SimSun'
# Resolve installed font families through the normal font renderer. Do not
# copy or distribute the Windows system-font files with the report.
FONT_RESOLUTION = {}
for family in (FONT_SANS, FONT_SERIF):
    resolved = font_manager.findfont(font_manager.FontProperties(family=family),
                                     fallback_to_default=False)
    actual = font_manager.FontProperties(fname=resolved).get_name()
    if actual != family:
        raise SystemExit(f'Font substitution is forbidden: {family} -> {actual}')
    FONT_RESOLUTION[family] = {'resolved_family': actual, 'file_name': Path(resolved).name}
plt.rcParams.update({"font.family": FONT_SANS, "font.size": 11,
                     "text.color": NAVY, "axes.labelcolor": NAVY,
                     "xtick.color": GRAY, "ytick.color": NAVY,
                     # Type 42 embedding of this OpenType CJK collection produced
                     # missing/wrong visible glyphs despite correct extracted text.
                     # Type 3 preserves the actual vector glyph outlines.
                     "pdf.fonttype": 3, "ps.fonttype": 42,
                     "axes.unicode_minus": False, "savefig.facecolor": "white"})
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--preview-dir", type=Path)
parser.add_argument("--preview-dpi", type=int, default=180)
parser.add_argument("--only", nargs='+', help='Build only these figure IDs for a bounded visual review.')
args = parser.parse_args()
OUTPUTS = []


def label(ax, x, y, text, size=11, color=NAVY, ha="left", va="center", weight="normal", serif=False, **kw):
    return ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va,
                   fontweight=weight, fontfamily=FONT_SERIF if serif else FONT_SANS,
                   transform=ax.transAxes, zorder=6, **kw)



def figure_text(fig, x, y, text, size=13, color=NAVY, **kwargs):
    return fig.text(x, y, text, fontsize=size, color=color,
                    fontfamily=FONT_SANS, va="center", **kwargs)

def rect(ax, x, y, w, h, face=PALE, edge="none", radius=0.012, **kw):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=face, edgecolor=edge, linewidth=.6,
                       transform=ax.transAxes, **kw)
    ax.add_patch(p)
    return p


def canvas(fid, title, subtitle, height):
    fig = plt.figure(figsize=(6.3, height))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    # The report owns the figure title and places it below the artwork.
    # Keep only diagram labels here; crop the former header band on export.
    return fig, ax


def arrow(ax, x0, y0, x1, y1, color=GRAY, lw=1.1, style='->', **kw):
    ax.annotate('', xy=(x1,y1), xytext=(x0,y0), xycoords='axes fraction',
                arrowprops={'arrowstyle':style,'lw':lw,'color':color,
                            'shrinkA':0,'shrinkB':0, **kw}, zorder=4)


def asset(ax, name, x, y, w, h):
    """Place the unchanged generated RGBA asset; preserve its aspect ratio."""
    arr = plt.imread(ROOT/'generated-assets-20261105'/name)
    fw,fh = ax.figure.get_size_inches()
    ratio = arr.shape[1]/arr.shape[0]
    if w*fw/(h*fh) > ratio:
        fitw=h*fh*ratio/fw; x+=(w-fitw)/2; w=fitw
    else:
        fith=w*fw/ratio/fh; y+=(h-fith)/2; h=fith
    ax.imshow(arr, extent=(x,x+w,y,y+h), transform=ax.transAxes,
              aspect='auto', interpolation='antialiased', zorder=2)
    ax.set_xlim(0,1); ax.set_ylim(0,1)


def check(ax,x,y,size=.025,color=TEAL):
    ax.plot([x-size*.7,x-size*.12,x+size],[y,y-size*.5,y+size*.7],
            transform=ax.transAxes,color=color,lw=2.0,zorder=5,solid_capstyle='round')


def cross(ax,x,y,size=.018,color=RED):
    for sign in (-1,1):
        ax.plot([x-size,x+size],[y-sign*size,y+sign*size],
                transform=ax.transAxes,color=color,lw=1.6,zorder=7,solid_capstyle='round')


def token(ax,x,y,w,h,text,color=TEAL):
    rect(ax,x,y,w,h,face=color,radius=.008,zorder=3)
    label(ax,x+w/2,y+h/2,text,9.4,'white',ha='center',weight='bold')


def foot(ax,text,y=.033):
    label(ax,.035,y,text,7.8,'#766E65',serif=True)


def save(fig, fid):
    path = ROOT / (fid + ".pdf")
    width, height = fig.get_size_inches()
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    frame=fig.get_window_extent(renderer)
    visible_text=[t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
    minimum_font=min(t.get_fontsize() for t in visible_text)
    assert minimum_font>=11, (fid,minimum_font)
    outside=[]
    for t in visible_text:
        box=t.get_window_extent(renderer)
        if box.x0<frame.x0-.5 or box.y0<frame.y0-.5 or box.x1>frame.x1+.5 or box.y1>frame.y1+.5:
            outside.append(t.get_text())
    assert not outside,(fid,outside)
    fig.savefig(path, dpi=300, bbox_inches=Bbox.from_extents(0, 0, width, height),
        metadata={"Creator": "VDot report evidence figure generator",
        "Title": fid + " — historical evidence redrawn", "CreationDate": None, "ModDate": None})
    if args.preview_dir:
        import fitz
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        # Preview the delivered PDF itself; direct matplotlib PNG output can
        # hide PDF-only font failures.
        with fitz.open(path) as pdf:
            pdf[0].get_pixmap(dpi=args.preview_dpi, alpha=False).save(args.preview_dir / (fid + ".png"))
    OUTPUTS.append({"id": fid, "path": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "typography": FONT_RESOLUTION,
                    "technical_content": 'deterministic geometry and frozen data',
                    "illustration_assets": False,
                    "physical_size_mm": [width*25.4,height*25.4],
                    "minimum_text_size_pt": minimum_font,
                    "outside_canvas": outside})
    plt.close(fig)


def grid(ax, rows, cols, x=.275, y=.785, width=.685, step=.059, highlights=()):
    """rows = (name, values, color); invalid values must already be '—'."""
    cw = width / len(cols)
    for j, c in enumerate(cols):
        if j in highlights:
            rect(ax, x+j*cw, y-len(rows)*step+.012, cw, len(rows)*step+.04,
                 face="#fff3df", radius=0)
        label(ax, x+(j+.5)*cw, y+step*.66, str(c), 7.4, GRAY, ha="center")
    for i, (name, values, color) in enumerate(rows):
        cy = y-i*step
        label(ax, .035, cy, name, 8.0, NAVY)
        ax.plot([x, x+width], [cy-step*.46]*2, transform=ax.transAxes, lw=.45, color=LINE)
        for j, value in enumerate(values):
            active = str(value) not in ("0", "—", "-")
            if active:
                rect(ax, x+j*cw+.003, cy-step*.36, cw-.006, step*.72,
                     face=LIGHT if color == TEAL else PALE, radius=.005)
            label(ax, x+(j+.5)*cw, cy, str(value), 8.0,
                  color if active else GRAY, ha="center", weight="bold" if active else "normal")


def s1_timeline():
    alu = list(csv.DictReader((ROOT.parent/'evidence/vector-fix-alu-events.csv').open()))
    commits = [r for r in csv.DictReader((ROOT.parent/'evidence/vadd-commit-events.csv').open())
               if int(r['pc'],16)==0x80000138 and int(r['instruction'],16)==0x021101d7 and r['vecwen']=='1' and r['wdest']=='3']
    assert [int(r['cycle']) for r in commits]==[19631,25466,33015]
    fig,ax=canvas('S1-06','','',3.15)
    xs=(.34,.60,.86)
    for x,t in zip(xs,('输入','结果输出','ROB 提交')):label(ax,x,.90,t,12,ha='center',weight='bold')
    for i,name in enumerate(('正数','负数','边界')):
        y=.72-i*.245
        label(ax,.045,y,name,12.5,weight='bold')
        vals=(alu[2*i]['cycle'],alu[2*i+1]['cycle'],commits[i]['cycle'])
        for x,v in zip(xs,vals):
            ax.plot(x,y,'o',ms=6,color=TEAL,transform=ax.transAxes,zorder=4)
            label(ax,x,y-.085,v,12,ha='center')
        for a,b in zip(xs[:-1],xs[1:]):arrow(ax,a+.025,y,b-.025,y,color=TEAL,lw=1.15)
    label(ax,.045,.038,'CSV 事件坐标；列间距不表示时间比例。',11,color=GRAY)
    save(fig,'S1-06')


def s2_ii1():
    rr=DATA['parent']['ii1']
    assert [r['cycle'] for r in rr]==list(range(10,18))
    assert all(r['accept'] and r['out_ready'] for r in rr)
    assert all(r['response'] and r['p_to_r'] for r in rr[2:])
    assert (rr[2]['pseq'],rr[2]['rseq'],rr[2]['accept_seq'])==(2,1,3)
    fig,ax=canvas('S2-05','','',4.25)
    label(ax,.035,.95,'cycle 12：三个动作同拍完成',13,weight='bold')
    label(ax,.96,.87,'槽位为沿前状态',11,color=GRAY,ha='right')
    for x,slot,seq,col in ((.35,'P 槽',2,TEAL),(.62,'R 槽',1,NAVY)):
        rect(ax,x-.075,.625,.15,.15,face='white',edge=col,radius=.008)
        label(ax,x,.815,slot,12,ha='center',weight='bold')
        label(ax,x,.70,'#'+str(seq),14,col,ha='center',weight='bold')
    label(ax,.085,.70,'#3',14,AMBER,ha='center',weight='bold')
    arrow(ax,.135,.70,.267,.70,color=AMBER,lw=1.5)
    arrow(ax,.435,.70,.537,.70,color=TEAL,lw=1.5)
    arrow(ax,.705,.70,.87,.70,color=NAVY,lw=1.5)
    for x,t,col in ((.20,'接收',AMBER),(.485,'迁移',TEAL),(.79,'响应',NAVY)):
        label(ax,x,.59,t,11.5,col,ha='center')
    xx=(.31,.50,.69,.88)
    rect(ax,.595,.16,.19,.32,face='#fff5e7',radius=.004)
    for x,r in zip(xx,rr[:4]):label(ax,x,.46,str(r['cycle']),12,ha='center',weight='bold' if r['cycle']==12 else 'normal')
    label(ax,.035,.46,'cycle',11.5,color=GRAY)
    for y,key,t,col in ((.34,'accept_seq','接收',TEAL),(.215,'response_seq','响应',NAVY)):
        label(ax,.035,y,t,12,weight='bold')
        for x,r in zip(xx,rr[:4]):
            value='#'+str(r[key]) if key=='accept_seq' or r['response'] else '—'
            label(ax,x,y,value,13,col if value!='—' else GRAY,ha='center')
    label(ax,.035,.055,'接收间隔 1 拍',12.5,TEAL,weight='bold')
    label(ax,.96,.055,'最早 2 拍响应 · out_ready=1',11,ha='right')
    save(fig,'S2-05')


def s1_boot():
    boot=DATA['boot']
    assert 'instrCnt = 2' in boot['failure'][1]['plain']
    assert '--flash=' in boot['command'][0]['plain'] and 'Read 12 bytes' in boot['command'][4]['plain']
    assert 'HELLO_VADD_PASS cases=3 lanes=24' in boot['success'][1]['plain']
    assert 'exit_code=0' in boot['status'][0]['plain']
    instructions=re.findall(r'^\s*([048]):\s+([0-9a-f]{8})\s+(.+)$',
                            boot['disassembly'],re.MULTILINE)
    assert [int(x[0]) for x in instructions]==[0,4,8]
    assert [x[1] for x in instructions]==['0010029b','01f29293','00028067']
    fig,ax=canvas('S1-07','','',4.7)
    label(ax,.035,.95,'首次差异：PC 0x10000004，instrCnt = 2',12.5,weight='bold')
    label(ax,.035,.88,'t0 不一致；两端默认启动序列不同',12,color=RED)
    ax.plot([.035,.965],[.81,.81],color=LINE,lw=.8,transform=ax.transAxes)
    label(ax,.035,.76,'共同启动输入',12.5,weight='bold')
    label(ax,.965,.76,'boot-flash.bin · 12 B',12,ha='right')
    left,width=.045,.91
    for i,(offset,word,asm) in enumerate(instructions):
        x=left+i*width/3; center=x+width/6
        label(ax,center,.68,f'{int(offset)}–{int(offset)+3} B',11,GRAY,ha='center')
        rect(ax,x,.56,width/3,.09,face=LIGHT if i%2==0 else PALE,edge=LINE,radius=0)
        label(ax,center,.605,word,12.5,ha='center')
        label(ax,center,.50,re.sub(r'\s+',' ',asm),11.5,ha='center')
    ax.plot([left,left+width],[.44,.44],color=LINE,lw=.8,transform=ax.transAxes)
    ax.plot([.5,.5],[.44,.39],color=GRAY,lw=1,transform=ax.transAxes)
    ax.plot([.25,.75],[.39,.39],color=GRAY,lw=1,transform=ax.transAxes)
    for x,name in ((.25,'RTL / DUT'),(.75,'NEMU')):
        arrow(ax,x,.39,x,.34,color=TEAL)
        rect(ax,x-.14,.265,.28,.075,face='white',edge=TEAL,radius=0)
        label(ax,x,.303,name,12.5,ha='center')
    arrow(ax,.25,.265,.395,.20,color=TEAL)
    arrow(ax,.75,.265,.605,.20,color=TEAL)
    diamond=Polygon([[.395,.20],[.5,.245],[.605,.20],[.5,.155]],
                    closed=True,facecolor='white',edgecolor=NAVY,linewidth=.8,
                    transform=ax.transAxes)
    ax.add_patch(diamond)
    label(ax,.5,.20,'DiffTest',11.5,ha='center')
    arrow(ax,.5,.155,.5,.105,color=TEAL)
    label(ax,.5,.060,'3 类 · 24 元素 · GOOD TRAP · exit 0',12,TEAL,ha='center')
    save(fig,'S1-07')


def s2_backpressure():
    rr=DATA['backpressure'];states=[r for r in rr if r['kind']=='O2_STATE'];stall=[r for r in rr if r['kind']=='O2_STALL']
    response=[r for r in rr if r['kind']=='O2_RESPONSE' and r['seq']=='1321']
    assert len(states)==10 and len(stall)==7 and len(response)==1
    fields=('data','rob','pdest','illegal','vecwen','v0wen','exception','vpu','perf')
    assert all(all(r[k]==response[0][k] for k in fields) for r in stall)
    assert response[0]['data']=='0x00000000000000000000000000001a87'
    assert [int(r['cycle']) for r in states]==list(range(181597,181607))
    assert states[-1]['inready']=='0' and states[-1]['vready']=='1' and states[-1]['move']=='1' and states[-1]['pseq']=='1322'
    fig,ax=canvas('S2-06','','',4.65)
    label(ax,.035,.95,'七拍反压期间，结果与身份保持',13,weight='bold')
    label(ax,.035,.875,'A = #1321    B = #1322',11.5)
    label(ax,.96,.875,'沿前采样',11,GRAY,ha='right')
    left,cw=.235,.0715
    rect(ax,left+2*cw,.255,7*cw,.54,face='#fff5e7',radius=0)
    for j in range(10):
        label(ax,left+(j+.5)*cw,.79,'+'+str(j),11,color=GRAY,ha='center')
        ax.plot([left+j*cw]*2,[.265,.75],color=LINE,lw=.5,transform=ax.transAxes,zorder=1)
    label(ax,.035,.79,'cycle',11,color=GRAY)
    def band(name,values,y,color_map):
        label(ax,.035,y,name,11.5)
        start=0
        for end in range(1,len(values)+1):
            if end==len(values) or values[end]!=values[start]:
                value=values[start];col=color_map.get(value,PALE)
                rect(ax,left+start*cw+.003,y-.037,(end-start)*cw-.006,.074,face=col,radius=.004)
                label(ax,left+(start+end)*cw/2,y,value,12,'white' if col in (TEAL,NAVY) else NAVY,ha='center')
                start=end
    name=lambda seq:'A' if seq=='1321' else 'B'
    band('P 槽',[name(r['pseq']) if r['pvalid']=='1' else '—' for r in states],.68,{'A':TEAL,'B':NAVY})
    band('R 槽',[name(r['rseq']) if r['rvalid']=='1' else '—' for r in states],.56,{'A':TEAL})
    band('outvalid',[r['outvalid'] for r in states],.43,{'1':PALE})
    band('outready',[r['outready'] for r in states],.31,{'1':PALE,'0':'#f4e2c5'})
    arrow(ax,left+2*cw,.225,left+9*cw,.225,color=AMBER,lw=1.1,style='<->')
    label(ax,left+5.5*cw,.18,'7 拍',12,AMBER,ha='center',weight='bold')
    label(ax,.035,.10,'+9：A 响应一次，B 从 P 迁入 R',12,TEAL,weight='bold')
    label(ax,.035,.035,'此时 FU vready=1，父级 inready=0。',11,color=GRAY)
    save(fig,'S2-06')


def s2_cancel():
    fig,ax=canvas('S2-07','','',5.55)
    specs=[('cancel_p','仅取消 P',12790,12791),('cancel_r','仅取消 R',12878,12879),('cancel_both','两槽取消',12266,12267),('reset','reset 与 redirect 同拍',14811,14813)]
    for i,(key,title,cy,ncy) in enumerate(specs):
        x=.03+(i%2)*.495;top=.97-(i//2)*.455
        before=next(r for r in DATA['parent'][key] if r['cycle']==cy);after=next(r for r in DATA['parent'][key] if r['cycle']==ncy)
        assert before['p'] and before['r'] and not after['p']
        if key=='cancel_p':assert after['r'] and after['rseq']==before['rseq']
        elif key=='cancel_r':assert after['r'] and after['rseq']==before['pseq']
        else:assert not after['r']
        if key=='reset':assert before['reset_drop']==2 and not before['kill_p'] and not before['kill_r']
        label(ax,x+.005,top,title,12,weight='bold')
        xs=[x+.15,x+.34]
        for cx,n in zip(xs,('P','R')):label(ax,cx,top-.066,n,11.5,ha='center',color=GRAY)
        yy0,yy1=top-.135,top-.285
        label(ax,x+.005,yy0,'前',11,color=GRAY);label(ax,x+.005,yy1,'后',11,color=GRAY)
        for cx in xs:
            for yy in (yy0,yy1):rect(ax,cx-.066,yy-.045,.132,.09,face='white',edge=LINE,radius=.004)
        for cx,t,col in zip(xs,('A','B'),(TEAL,NAVY)):label(ax,cx,yy0,t,14,col,ha='center',weight='bold')
        label(ax,xs[0],yy1,'—',12,GRAY,ha='center')
        survivor='B' if key=='cancel_p' else ('A' if key=='cancel_r' else '—')
        label(ax,xs[1],yy1,survivor,14,TEAL if survivor=='A' else NAVY,ha='center',weight='bold')
        if key=='cancel_p':
            cross(ax,xs[0],yy0,.031);arrow(ax,xs[1],yy0-.052,xs[1],yy1+.052,color=NAVY)
            result='B 保留并响应'
        elif key=='cancel_r':
            cross(ax,xs[1],yy0,.031);arrow(ax,xs[0]+.025,yy0-.052,xs[1]-.025,yy1+.052,color=TEAL,lw=1.3)
            result='A 迁入 R 后响应'
        else:
            if key=='cancel_both':
                for cx in xs:cross(ax,cx,yy0,.031)
            arrow(ax,x+.245,yy0-.052,x+.245,yy1+.052,color=RED)
            result='两槽失效' if key=='cancel_both' else 'reset 优先，清除有效位'
        label(ax,x+.245,top-.375,result,11,TEAL if i<2 else RED,ha='center')
    ax.plot([.51,.51],[.11,.98],color=LINE,lw=.7,transform=ax.transAxes)
    ax.plot([.03,.98],[.55,.55],color=LINE,lw=.7,transform=ax.transAxes)
    label(ax,.03,.055,'四个独立场景；A/B 为场景内事务，— 表示无效槽。',11,color=GRAY)
    save(fig,'S2-07')


def s2_div():
    fig,ax=canvas('S2-08','','',5.7)
    label(ax,.035,.96,'排空 VDot 后，接收 DIV',13,weight='bold')
    xs=(.32,.52,.72,.92)
    for x,t in zip(xs,('旧 R 输出','VDot 排空','DIV 接收','DIV 响应')):label(ax,x,.88,t,11,ha='center',color=GRAY)
    for i,(key,kind,cycles) in enumerate((('switch_int','整数 DIV',[11447,11448,11449,11459]),('switch_fp','浮点 DIV',[11504,11505,11506,11514]))):
        yy=.80-i*.11;rr=DATA['parent'][key];assert all(c in [r['cycle'] for r in rr] for c in cycles)
        label(ax,.035,yy,kind,11.5,weight='bold')
        for x,c in zip(xs,cycles):
            ax.plot(x,yy+.025,'o',ms=5.5,color=TEAL if x==.72 else NAVY,transform=ax.transAxes)
            label(ax,x,yy-.02,str(c),11,ha='center')
        for a,b in zip(xs[:-1],xs[1:]):arrow(ax,a+.015,yy+.025,b-.025,yy+.025,color=GRAY,lw=.8)
    ax.plot([.035,.97],[.61,.61],color=LINE,lw=.8,transform=ax.transAxes)
    label(ax,.035,.555,'取消清理后关钟，再接收 VDot',13,weight='bold')
    xx=(.28,.45,.62,.79,.94)
    for x,t in zip(xx,('入 DIV','取消清理','空闲','入 VDot','响应')):label(ax,x,.475,t,11,ha='center',color=GRAY)
    for i,(key,name) in enumerate((('cancel_int','整数 DIV'),('cancel_fp','浮点 DIV'))):
        rr=DATA['parent'][key];yy=.38-i*.155
        assert len(rr)==8 and all(rr[j]['clocks']==0 for j in (2,3,4))
        assert rr[1]['kill_div'] and rr[5]['accept'] and rr[7]['response']
        label(ax,.035,yy,name,11.5,weight='bold')
        for x,j in zip(xx,(0,1,2,5,7)):
            rect(ax,x-.052,yy-.037,.104,.074,face='#f7e4ca' if j==1 else (LIGHT if j==2 else PALE),radius=.004)
            label(ax,x,yy,str(rr[j]['clocks']),13,TEAL if j==2 else NAVY,ha='center',weight='bold')
            label(ax,x,yy-.065,'+2～+4' if j==2 else '+'+str(j),11,GRAY,ha='center')
    label(ax,.035,.09,'沿后子时钟掩码：1=VDot，2=VIDiv，4=VFDiv。',11,color=GRAY)
    label(ax,.035,.035,'事件顺序示意；列间距不表示时间比例。',11,color=GRAY)
    save(fig,'S2-08')


def s3_negative_recovery():
    evidence=json.loads((ROOT/'evidence-20261105/negative-recovery-source.json').read_text(encoding='utf-8'));files=evidence['files']
    negative,normal=[json.loads(files[i]['content']) for i in (1,3)]
    for idx,result in ((0,negative),(2,normal)):
        raw=files[idx]['content'].encode('utf-8')
        assert hashlib.sha256(raw).hexdigest()==result['raw_logs_sha256']['stdout.log']
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==files[idx]['sha']
    assert negative['exit_code']==1 and normal['exit_code']==0
    assert negative['bit']==100 and negative['pc']=='0x80001bdc' and negative['vd']==10
    assert 'right= 0x0000001000000000, wrong = 0x0000000000000000' in files[0]['content']
    assert int('0000001000000000',16)==1<<(100-64)
    for suffix in ('/emu','/vdot-exceptions.bin','/boot-flash.bin'):
        keys=[k for k in negative['files'] if k.endswith(suffix)];assert len(keys)==1 and negative['files'][keys[0]]==normal['files'][keys[0]]
    assert 'planned=15 executed=15 passed=15 failed=0 unreachable=0' in files[2]['content']
    fig,ax=canvas('S3-03','','',4.3)
    label(ax,.035,.95,'同一 DUT、程序与启动文件；两次独立运行',12,weight='bold')
    label(ax,.035,.835,'负控比较 v10',12,RED,weight='bold')
    left,width=.235,.70
    for x,t in ((left+width*.25,'高 64 位'),(left+width*.75,'低 64 位')):label(ax,x,.79,t,11,ha='center',color=GRAY)
    for yy,name in ((.69,'DUT'),(.51,'负控 REF')):
        label(ax,.035,yy,name,12,weight='bold')
        for j in range(2):rect(ax,left+j*width/2,yy-.045,width/2,.09,face=PALE if j==0 else LIGHT,edge='white',radius=0)
    bx=left+width*((127-100)+.5)/128
    rect(ax,bx-.004,.465,.008,.09,face=RED,radius=0)
    arrow(ax,bx,.605,bx,.558,color=RED,lw=1)
    label(ax,bx+.025,.615,'bit100 注错',11.5,RED)
    for x,t in ((left,'127'),(left+width/2,'64 / 63'),(left+width,'0')):label(ax,x,.405,t,11,GRAY,ha='center')
    ax.plot([.035,.965],[.325,.325],color=LINE,lw=.8,transform=ax.transAxes)
    cross(ax,.07,.23,.024,RED);label(ax,.12,.23,'负控：预期拒错',12.5,RED,weight='bold')
    check(ax,.57,.23,.024,TEAL);label(ax,.62,.23,'正常参考通过',12.5,TEAL,weight='bold')
    label(ax,.12,.12,'检出高位差异',11.5)
    label(ax,.62,.12,'15 / 15 用例',12,TEAL,weight='bold')
    label(ax,.035,.035,'128 位完整比较；参考模型分别加载，不在运行中切换。',11,color=GRAY)
    save(fig,'S3-03')


def s3_performance():
    """Adopt the reviewed exact chart, checking its recorded data and bytes.

    The editable Matplotlib SVG and renderer are delivered beside the fixed PDF.
    Keeping that PDF avoids changing fonts after the actual preview was reviewed.
    """
    import fitz
    folder = ROOT / 'redesigned-20261105/formal/S3-05'
    spec = json.loads((folder / 'selection.json').read_text(encoding='utf-8'))
    for entry in spec['files']:
        source = (folder / entry['file']).resolve()
        assert source.is_relative_to(folder.resolve())
        raw = source.read_bytes()
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
    rows = {row['scenario']: row for row in DATA['performance'] if row['mode'] == 'after'}
    assert set(rows) == {'single', 'chain', 'batch', 'stream'}
    for selected in spec['values']:
        row = rows[selected['scenario']]
        assert int(row['samples_per_method']) == selected['samples_per_method'] == 12
        assert int(row['dots']) == selected['dots_per_window']
        assert Decimal(str(row['custom_mean_cycles'])) == Decimal(selected['vdot_mean_cycles'])
        assert Decimal(str(row['rvv_mean_cycles'])) == Decimal(selected['rvv_mean_cycles'])
        assert Decimal(str(row['custom_sum_cycles'])) == Decimal(selected['vdot_mean_cycles']) * 12
        assert Decimal(str(row['rvv_sum_cycles'])) == Decimal(selected['rvv_mean_cycles']) * 12
        percent = 100 * float(row['custom_sum_cycles']) / float(row['rvv_sum_cycles'])
        assert f'{percent:.2f}%' == selected['displayed_percent']
        assert math.isclose(float(selected['ratio_of_cycle_sums']),
                            float(row['speedup_ratio_of_sums']), rel_tol=1e-12)
    assert spec['root_review']['actual_final_pdf_preview_reviewed']
    svg = folder / 'S3-05-normalized-cycles.svg'
    raw_svg = svg.read_text(encoding='utf-8')
    xml = ET.fromstring(raw_svg)
    width_pt = float(xml.attrib['width'].removesuffix('pt'))
    view_width = float(xml.attrib['viewBox'].split()[2])
    assert abs(width_pt - view_width) < 1e-6
    minimum = min(float(x) for x in re.findall(r'font-size:\s*([0-9.]+)px', raw_svg))
    assert minimum == spec['typography']['minimum_pt'] == 11.5
    source = folder / 'S3-05-normalized-cycles.pdf'
    path = ROOT / 'S3-05.pdf'
    with fitz.open(source) as pdf:
        assert len(pdf) == 1 and not pdf[0].get_text().strip()
        assert not pdf[0].get_images() and pdf[0].get_drawings()
        size = [pdf[0].rect.width * 25.4 / 72, pdf[0].rect.height * 25.4 / 72]
        assert abs(size[0] - 160) < .02 and abs(size[1] - 132) < .02
        shutil.copyfile(source, path)
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
            pdf[0].get_pixmap(dpi=args.preview_dpi, alpha=False).save(args.preview_dir / 'S3-05.png')
    OUTPUTS.append({
        'id': 'S3-05', 'path': path.name,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'typography': spec['typography'], 'physical_size_mm': size,
        'minimum_text_size_pt': minimum,
        'technical_content': 'Frozen after data cross-checked; common linear per-scenario relative-cycle axis',
        'illustration_assets': False,
        'method': 'Adopt exact reviewed PDF; editable SVG and renderer supplied',
        'source_selection': str((folder / 'selection.json').relative_to(ROOT)),
        'outside_canvas_automated_check': 'Not inferred from empty outline text extraction; actual PDF preview reviewed separately',
        'actual_final_pdf_preview_reviewed': True,
    })

def s3_cost():
    """Nominal 1 ns / 5 fF path-class slacks, not a WNS chart."""
    data = DATA
    profiles = ["period050", "nominal", "period200", "load001", "load020"]
    paths = [("fu", p) for p in ("i2o", "i2r", "r2o", "r2r", "ready")]
    paths += [("parent", p) for p in ("gate_enable", "i2o", "i2r", "r2o", "r2r", "ready", "vdot_i2r", "vdot_r2o", "vdot_r2r")]
    timing = data["timing"]
    assert len(timing) == 70
    records = {(r["boundary"], r["path"], r["profile"]): r for r in timing}
    assert len(records) == 70
    assert set(records) == {(b, p, q) for b, p in paths for q in profiles}
    nominal = data["profiles"]["nominal"]
    assert float(nominal["period_ns"]) == 1 and float(nominal["load_ff"]) == 5
    values = [float(records[b, p, "nominal"]["after_slack_ns"]) for b, p in paths]
    negative_count = sum(value < 0 for value in values)
    assert negative_count == 10 and len(values) == 14
    assert min(values) > -2.6 and max(values) < .8
    fu_area = float(data["area"]["fu"]["after"]["area"])
    parent_area = float(data["area"]["parent"]["after"]["area"])
    assert 0 < fu_area < parent_area
    fig = plt.figure(figsize=(6.3, 6.1), facecolor="white")
    figure_text(fig, .035, .955, "VDot FU")
    figure_text(fig, .965, .955, f"{fu_area:,.3f} μm²", ha="right")
    figure_text(fig, .035, .908, "VFEX4 父级（含 FU）")
    figure_text(fig, .965, .908, f"{parent_area:,.3f} μm²", ha="right")
    fig.add_artist(plt.Line2D([.035, .965], [.87, .87], transform=fig.transFigure,
                              color=LINE, linewidth=.8))
    figure_text(fig, .035, .828, "1 ns / 5 fF", weight="bold")
    figure_text(fig, .965, .828, f"{negative_count} / {len(values)} 项为负", color=RED,
          ha="right", weight="bold")
    ax = fig.add_axes([.245, .12, .53, .61])
    ys = list(range(5)) + list(range(6, 15))
    ax.set(xlim=(-2.6, .8), ylim=(14.8, -1.1))
    ax.set_yticks(ys, [p for b, p in paths], fontsize=13)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.set_xticks([-2, -1, 0, .5], ["−2", "−1", "0", "+0.5"], fontsize=11)
    ax.tick_params(axis="x", length=3, pad=6)
    ax.set_xlabel("时序裕量 / ns", fontsize=13, labelpad=9)
    ax.axvline(0, color=NAVY, linewidth=1.1, zorder=2)
    for x in (-2, -1):
        ax.axvline(x, color=LINE, linewidth=.65, zorder=0)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    colors = [RED if value < 0 else TEAL for value in values]
    ax.barh(ys, values, height=.55, color=colors, zorder=3)
    fy = lambda y: .12 + .61 * (14.8 - y) / 15.9
    figure_text(fig, .035, .765, "VDot FU", weight="bold")
    figure_text(fig, .965, .765, "裕量 / ns", ha="right")
    figure_text(fig, .035, fy(5), "VFEX4 父级", weight="bold")
    ax.axhline(5, color=LINE, linewidth=.75)
    for y, value, color in zip(ys, values, colors):
        figure_text(fig, .965, fy(y), f"{value:+.6f}", ha="right", color=color)
    fig.vdot_data = {"id": "S3-07", "profile": "nominal", "paths": paths,
                     "slack_ns": values, "negative_count": negative_count,
                     "area_um2": {"fu": fu_area, "parent_including_fu": parent_area},
                     "caption_scope": "Path-class slacks, including gate-enable check; i2r is not WNS. Full five-profile table remains in the original appendix."}
    save(fig, 'S3-07')


if __name__ == '__main__':
    builders={'S1-06':s1_timeline,'S1-07':s1_boot,'S2-05':s2_ii1,
              'S2-06':s2_backpressure,'S2-07':s2_cancel,'S2-08':s2_div,
              'S3-03':s3_negative_recovery,'S3-05':s3_performance,'S3-07':s3_cost}
    selected=args.only or list(builders)
    for fid in selected:
        if fid not in builders:raise SystemExit('Unknown figure: '+fid)
        builders[fid]()
    manifest='generated-figures-preview.json' if args.only else 'generated-figures.json'
    (ROOT/'evidence-20261105'/manifest).write_text(json.dumps(OUTPUTS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figures':len(OUTPUTS),'ids':[x['id'] for x in OUTPUTS],
                      'fonts':FONT_RESOLUTION},ensure_ascii=False))
