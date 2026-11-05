"""Rebuild evidence figures from the frozen, attributed data beside this file.

Usage: python figures/build_evidence_figures.py [--preview-dir DIR]
Requires matplotlib, NumPy, installed Microsoft YaHei and SimSun;
PDF previews also use PyMuPDF. Generated illustration assets are embedded
unchanged; all technical geometry, numbers, labels and fonts are typeset here.
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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "evidence-20261105/figure-data.json").read_text(encoding="utf-8"))
NAVY, TEAL, GRAY = "#17324d", "#087f8c", "#697b8c"
LIGHT, PALE, LINE = "#eaf4f5", "#f2f5f8", "#d4dee6"
RED, AMBER = "#ad4b3a", "#b27828"
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
plt.rcParams.update({"font.family": FONT_SANS, "font.size": 8.5,
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


def label(ax, x, y, text, size=8.5, color=NAVY, ha="left", va="center", weight="normal", serif=False, **kw):
    return ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va,
                   fontweight=weight, fontfamily=FONT_SERIF if serif else FONT_SANS,
                   transform=ax.transAxes, zorder=6, **kw)


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
    label(ax, .035, .963, fid + "  /  EVIDENCE", 7.2, TEAL, weight="bold")
    label(ax, .035, .902 if height < 3.3 else .917, title, 12.0, weight="bold")
    label(ax, .035, .840 if height < 3.3 else .869, subtitle, 7.3, GRAY)
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
    label(ax,.035,y,text,7.8,'#526475',serif=True)


def save(fig, fid):
    path = ROOT / (fid + ".pdf")
    fig.savefig(path, dpi=300, metadata={"Creator": "VDot report evidence figure generator",
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
                    "illustration_assets": fid in ('S1-07','S2-05','S2-07','S3-03')})
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
    alu = list(csv.DictReader((ROOT.parent / "evidence/vector-fix-alu-events.csv").open()))
    commits = [r for r in csv.DictReader((ROOT.parent / "evidence/vadd-commit-events.csv").open())
               if int(r['pc'], 16) == 0x80000138 and int(r['instruction'], 16) == 0x021101d7
               and r['vecwen'] == '1' and r['wdest'] == '3']
    assert [int(r['cycle']) for r in commits] == [19631, 25466, 33015]
    fig, ax = canvas("S1-06", "vadd：输入、结果与提交", "2026-10-09 历史事件 CSV · 三列按事件阶段排列", 3.05)
    phases = ["输入事件", "输出事件", "ROB 提交"]
    for x, p in zip((.35, .60, .85), phases): label(ax, x, .77, p, 8.3, GRAY, ha="center")
    for i, name in enumerate(("正数", "负数", "边界")):
        a, b, c = alu[2*i], alu[2*i+1], commits[i]
        y = .64-i*.205
        rect(ax, .035, y-.097, .93, .175, face=PALE)
        label(ax, .06, y+.013, name, 9.5, weight="bold")
        for x, v, col in zip((.35, .60, .85), (a["cycle"], b["cycle"], c["cycle"]), (NAVY, TEAL, NAVY)):
            label(ax, x, y+.018, v, 11, col, ha="center", weight="bold")
        for x0, x1 in ((.405,.54),(.655,.79)):
            ax.annotate("", xy=(x1,y+.018), xytext=(x0,y+.018), xycoords="axes fraction",
                        arrowprops={"arrowstyle":"->", "lw":.9, "color":GRAY})
        result = b["result"].lower().removeprefix("0x")[-16:].upper()
        label(ax, .30, y-.051, "输出低 64 位  0x" + result, 8.5, TEAL)
    foot(ax, 'CSV 事件坐标；图中间距不表示时间长度。')
    save(fig, "S1-06")


def s2_ii1():
    rr=DATA['parent']['ii1']
    assert [r['cycle'] for r in rr]==list(range(10,18))
    assert all(r['accept'] and r['out_ready'] for r in rr)
    assert all(r['response'] and r['p_to_r'] for r in rr[2:])
    assert (rr[2]['pseq'],rr[2]['rseq'],rr[2]['accept_seq'])==(2,1,3)
    fig,ax=canvas('S2-05','同一拍，接收、移动与输出重叠','0f 真实父级 · 无阻塞窗口 · cycle 12 放大示意',3.65)
    for xx,slot,seq,col in ((.265,'P',2,TEAL),(.555,'R',1,NAVY)):
        asset(ax,'pipeline-tray.png',xx,.535,.19,.17)
        label(ax,xx+.095,.731,slot+' 槽（沿前）',8.3,ha='center',weight='bold')
        token(ax,xx+.058,.587,.074,.061,'#'+str(seq),col)
    token(ax,.060,.588,.09,.060,'#3',AMBER)
    arrow(ax,.158,.618,.257,.618,AMBER,lw=1.4)
    arrow(ax,.463,.618,.547,.618,TEAL,lw=1.4)
    arrow(ax,.752,.618,.886,.618,NAVY,lw=1.4)
    label(ax,.201,.677,'接收 #3',7.9,AMBER,ha='center')
    label(ax,.503,.677,'移动 #2',7.9,TEAL,ha='center')
    label(ax,.823,.677,'输出 #1',7.9,NAVY,ha='center')
    label(ax,.912,.618,'响应',8.9,NAVY,ha='center',weight='bold')
    label(ax,.035,.472,'连续窗口',8.8,weight='bold')
    label(ax,.96,.472,'out_ready = 1',7.5,GRAY,ha='right')
    rows=[('接收事务',['#'+str(r['accept_seq']) for r in rr],TEAL),
          ('FU 响应',['#'+str(r['response_seq']) if r['response'] else '—' for r in rr],NAVY)]
    grid(ax,rows,[r['cycle'] for r in rr],x=.25,width=.715,y=.352,step=.090,highlights=(2,))
    label(ax,.035,.126,'接收间隔 1 拍',10.2,TEAL,weight='bold')
    label(ax,.43,.126,'#1：cycle 10 接收 → 12 响应',8.4)
    foot(ax,'仅此无反压窗口；seq 为测试事务号，FU 响应不表示 ROB 提交。')
    save(fig,'S2-05')


def s1_boot():
    boot=DATA['boot']
    first=boot['failure'][0]['plain']
    m=re.search(r'pc\s*=\s*(0x[0-9a-f]+),\s*right=\s*(0x[0-9a-f]+),\s*wrong\s*=\s*(0x[0-9a-f]+)',first)
    assert m and int(m[1],16)==0x10000004
    assert 'instrCnt = 2' in boot['failure'][1]['plain']
    assert '--flash=' in boot['command'][0]['plain'] and 'Read 12 bytes' in boot['command'][4]['plain']
    assert 'HELLO_VADD_PASS cases=3 lanes=24' in boot['success'][1]['plain']
    assert 'exit_code=0' in boot['status'][0]['plain']
    fig,ax=canvas('S1-07','统一启动输入，恢复差分一致','2026-10-09 · hello / vadd 历史故障与恢复',3.95)
    ax.plot([.355,.355],[.19,.81],color=LINE,lw=.8,transform=ax.transAxes)
    label(ax,.05,.79,'修复前',9.8,RED,weight='bold')
    label(ax,.405,.79,'显式装载同一文件',9.8,TEAL,weight='bold')
    for yy,name in ((.64,'DUT'),(.45,'NEMU')):
        rect(ax,.055,yy-.038,.105,.078,face=PALE,edge=LINE)
        label(ax,.107,yy,'默认输入',7.8,ha='center')
        arrow(ax,.165,yy,.201,yy)
        rect(ax,.205,yy-.044,.105,.088,face='white',edge=NAVY)
        label(ax,.257,yy,name,9,ha='center',weight='bold')
    # Both sides are compared before and after the boot-input change.
    arrow(ax,.276,.591,.313,.546,color=RED,lw=.9)
    arrow(ax,.276,.499,.313,.546,color=RED,lw=.9)
    label(ax,.328,.546,'≠',17,RED,ha='center',weight='bold')
    label(ax,.182,.295,'DiffTest：启动差异',8.6,RED,ha='center')
    label(ax,.182,.234,'两套默认启动输入',7.7,GRAY,ha='center')
    asset(ax,'boot-document.png',.385,.40,.21,.30)
    label(ax,.49,.695,'12 B',11,TEAL,ha='center',weight='bold')
    label(ax,.49,.382,'boot-flash.bin',8.2,ha='center')
    # One file, two independent load endpoints: no shared physical ROM.
    ax.plot([.582,.615,.615],[.55,.55,.69],color=TEAL,lw=1.1,transform=ax.transAxes)
    ax.plot([.615,.615],[.55,.44],color=TEAL,lw=1.1,transform=ax.transAxes)
    arrow(ax,.615,.69,.662,.69,color=TEAL)
    arrow(ax,.615,.44,.662,.44,color=TEAL)
    for yy,name in ((.69,'DUT'),(.44,'NEMU')):
        rect(ax,.67,yy-.048,.14,.096,face=LIGHT,edge=TEAL)
        label(ax,.74,yy,name,10,ha='center',weight='bold')
        arrow(ax,.817,yy,.877,.566,color=TEAL)
    label(ax,.89,.565,'=',18,TEAL,ha='center',weight='bold')
    label(ax,.89,.49,'DiffTest',7.8,ha='center')
    check(ax,.456,.255,.019)
    label(ax,.50,.255,'3 组 · 24 元素通过',10.2,TEAL,weight='bold')
    label(ax,.50,.204,'GOOD TRAP · 退出 0',8.0,GRAY)
    foot(ax,'DiffTest 全程启用；共同文件分别按两端的平台映射装载。',.105)
    foot(ax,'历史记录重绘；精确差异、三条启动指令与来源见图注及附件。')
    save(fig,'S1-07')


def s2_backpressure():
    rr=DATA["backpressure"]
    states=[r for r in rr if r["kind"]=="O2_STATE"]
    stall=[r for r in rr if r["kind"]=="O2_STALL"]
    response=[r for r in rr if r["kind"]=="O2_RESPONSE" and r["seq"]=="1321"]
    assert len(states)==10 and len(stall)==7 and len(response)==1
    fields=("data","rob","pdest","illegal","vecwen","v0wen","exception","vpu","perf")
    assert all(all(r[k]==response[0][k] for k in fields) for r in stall)
    assert response[0]["data"]=="0x00000000000000000000000000001a87"
    assert [int(r['cycle']) for r in states]==list(range(181597,181607))
    assert states[-1]['inready']=='0' and states[-1]['vready']=='1'
    assert states[-1]['move']=='1' and states[-1]['pseq']=='1322'
    fig,ax=canvas('S2-06','反压 7 拍，结果与事务身份保持','0f 历史全核观察器 · cycle 181597 + 横轴偏移',4.55)
    left,cw=.267,.0677
    rect(ax,left+2*cw,.205,7*cw,.55,face='#fff4df',radius=.004)
    label(ax,left+5.5*cw,.782,'连续 7 拍反压',10.0,AMBER,ha='center',weight='bold')
    for j in range(10):
        label(ax,left+(j+.5)*cw,.727,'+'+str(j),7.6,GRAY,ha='center')
        ax.plot([left+j*cw]*2,[.217,.705],color=LINE,lw=.4,transform=ax.transAxes,zorder=1)
    def bands(name,values,y,colors):
        label(ax,.035,y,name,8.1,weight='bold' if name in ('P 槽','R 槽') else 'normal')
        first=0
        for j in range(1,len(values)+1):
            if j==len(values) or values[j]!=values[first]:
                val=values[first];col=colors.get(str(val),PALE)
                rect(ax,left+first*cw+.003,y-.026,(j-first)*cw-.006,.052,face=col,radius=.003)
                label(ax,left+(first+j)/2*cw,y,str(val),8.0,'white' if col in (TEAL,NAVY) else NAVY,ha='center',weight='bold' if str(val).startswith('#') else 'normal')
                first=j
    bands('P 槽',['#'+r['pseq'] if r['pvalid']=='1' else '—' for r in states],.651,{'#1321':TEAL,'#1322':NAVY})
    bands('R 槽',['#'+r['rseq'] if r['rvalid']=='1' else '—' for r in states],.563,{'#1321':TEAL})
    bands('outvalid',[r['outvalid'] for r in states],.464,{'1':'#d2e9e9'})
    bands('outready',[r['outready'] for r in states],.394,{'1':'#d2e9e9','0':'#f1dfbd'})
    bands('FU vready',[r['vready'] for r in states],.324,{'1':'#d2e9e9'})
    bands('父级 inready',[r['inready'] for r in states],.254,{'1':'#d2e9e9'})
    label(ax,.035,.782,'+0 接收 #1321',8.3,TEAL,weight='bold')
    label(ax,left+9.5*cw,.510,'响应',7.0,TEAL,ha='center')
    label(ax,.035,.149,'+9：#1321 单次响应，同时 #1322 从 P 转入 R',8.4,TEAL,weight='bold')
    foot(ax,'条带为沿前采样；接收到响应相隔 9 拍，包含 7 拍反压。',.085)
    foot(ax,'完整 128 位结果与控制字段逐行保持；原值、身份与来源见图注及附件。')
    save(fig,'S2-06')


def s2_cancel():
    fig,ax=canvas('S2-07','取消与复位：看清事务保留和迁移','0f 真实父级 · 四个独立窗口 · 槽位为沿前状态',4.55)
    specs=[('cancel_p','A  仅取消 P',12790,12791),
           ('cancel_r','B  仅取消 R',12878,12879),
           ('cancel_both','C  两槽同时取消',12266,12267),
           ('reset','D  reset + redirect',14811,14813)]
    for i,(key,title,cy,ncy) in enumerate(specs):
        x=.035+(i%2)*.485;top=.80-(i//2)*.345
        rr=DATA['parent'][key];before=next(r for r in rr if r['cycle']==cy)
        after=next(r for r in rr if r['cycle']==ncy)
        assert before['p'] and before['r'] and not after['p']
        if key=='cancel_p':assert after['r'] and after['rseq']==before['rseq']
        elif key=='cancel_r':assert after['r'] and after['rseq']==before['pseq']
        else:assert not after['r']
        if key=='reset':assert before['reset_drop']==2 and not before['kill_p'] and not before['kill_r']
        rect(ax,x,top-.302,.445,.322,face='#f7f9fb',edge=LINE)
        label(ax,x+.018,top-.011,title,9.0,weight='bold')
        label(ax,x+.111,top-.060,'之前',7.1,GRAY,ha='center')
        label(ax,x+.340,top-.060,'之后',7.1,GRAY,ha='center')
        yP,yR=top-.113,top-.205
        for yy,slot in ((yP,'P'),(yR,'R')):
            label(ax,x+.026,yy,slot,9,GRAY,weight='bold')
            for xx in (x+.047,x+.276):
                asset(ax,'pipeline-tray.png',xx,yy-.041,.128,.083)
            token(ax,x+.087,yy-.020,.048,.040,'A' if slot=='P' else 'B',TEAL if slot=='P' else NAVY)
        if key in ('cancel_p','cancel_both'):
            cross(ax,x+.111,yP,.021)
        if key in ('cancel_r','cancel_both'):
            cross(ax,x+.111,yR,.021)
        if key=='cancel_p':
            token(ax,x+.316,yR-.020,.048,.040,'B',NAVY)
            arrow(ax,x+.181,yR,x+.269,yR,color=NAVY)
            label(ax,x+.224,yP,'取消',7.3,RED,ha='center')
            result='原 R 保留并输出'
        elif key=='cancel_r':
            token(ax,x+.316,yR-.020,.048,.040,'A',TEAL)
            arrow(ax,x+.181,yP,x+.269,yR,color=TEAL,lw=1.4)
            label(ax,x+.224,yP+.016,'P → R',7.8,TEAL,ha='center')
            result='原 P 转入 R 后输出'
        elif key=='cancel_both':
            arrow(ax,x+.187,(yP+yR)/2,x+.263,(yP+yR)/2,color=RED)
            result='两槽 valid 均清除'
        else:
            # Reset is not drawn as two redirect kills.
            label(ax,x+.226,(yP+yR)/2+.010,'reset',8.0,RED,ha='center',weight='bold')
            arrow(ax,x+.190,(yP+yR)/2-.025,x+.264,(yP+yR)/2-.025,color=RED)
            result='reset 优先 · 两槽失效'
        label(ax,x+.222,top-.275,result,8.0,TEAL if i<2 else RED,ha='center',weight='bold')
    foot(ax,'A / B 是各小图内的事务标记；空槽仅表示 valid=0。',.069)
    foot(ax,'取消按 ROB 判龄；程序年龄、cycle、真实 seq 和来源保留在图注及附件。')
    save(fig,'S2-07')


def s2_div():
    fig,ax=canvas('S2-08','DIV 切换、取消清理与空闲关钟','0f 真实父级 · 整数 DIV / 浮点 DIV 动态记录',4.8)
    label(ax,.035,.796,'A  先排空 VDot，再接收 DIV',9.5,weight='bold')
    xs=[.25,.48,.71,.92]
    for x,t in zip(xs,['旧 R 输出','剩余 VDot 输出','DIV 接收','DIV 响应']):
        label(ax,x,.729,t,7.5,GRAY,ha='center')
    for i,(key,kind,cycles) in enumerate([
        ('switch_int','整数 DIV',[11447,11448,11449,11459]),
        ('switch_fp','浮点 DIV',[11504,11505,11506,11514])]):
        yy=.662-i*.086;rr=DATA['parent'][key]
        assert all(c in [r['cycle'] for r in rr] for c in cycles)
        label(ax,.035,yy,kind,8.5,weight='bold')
        for x,c in zip(xs,cycles):
            rect(ax,x-.047,yy-.027,.094,.054,face=LIGHT if x==.71 else PALE)
            label(ax,x,yy,str(c),8.7,TEAL if x==.71 else NAVY,ha='center',weight='bold')
        for x0,x1 in zip(xs[:-1],xs[1:]):arrow(ax,x0+.055,yy,x1-.055,yy,lw=.8)
    label(ax,.035,.480,'B  取消当拍完成清理，随后采样为零',9.5,weight='bold')
    for i,(key,name,base) in enumerate([('cancel_int','整数 DIV',13328),('cancel_fp','浮点 DIV',13769)]):
        rr=DATA['parent'][key];yy=.376-i*.142
        assert len(rr)==8 and all(rr[j]['clocks']==0 for j in (2,3,4))
        assert rr[1]['kill_div'] and rr[5]['accept'] and rr[7]['response']
        label(ax,.035,yy+.015,name,8.5,weight='bold')
        label(ax,.035,yy-.025,'起点 '+str(base),7.2,GRAY)
        xx,cw=.26,.085
        for j,n,tag in ((0,1,'入 DIV'),(1,1,'取消清理'),(2,3,'关钟'),(5,1,'入 VDot'),(6,1,''),(7,1,'响应')):
            x=xx+j*cw;w=n*cw
            rect(ax,x+.002,yy-.030,w-.004,.061,face='#fff0d9' if j==1 else (LIGHT if j==2 else PALE),radius=.004)
            label(ax,x+w/2,yy+.059,'+2～+4' if j==2 else '+'+str(j),7.4,GRAY,ha='center')
            label(ax,x+w/2,yy,str(rr[j]['clocks']),10.0,TEAL if j==2 else NAVY,ha='center',weight='bold')
            label(ax,x+w/2,yy-.055,tag,7.0,RED if j==1 else GRAY,ha='center')
    foot(ax,'下部数字为沿后子时钟采样值：1=VDot，2=VIDiv，4=VFDiv；不是 gate_enable。',.092)
    foot(ax,'仅 DIV 动态记录；事件箭头不按时长比例绘制，SQRT 范围见正文。')
    save(fig,'S2-08')


def s3_negative_recovery():
    evidence = json.loads((ROOT/'evidence-20261105/negative-recovery-source.json').read_text(encoding='utf-8'))
    files = evidence['files']
    negative, normal = [json.loads(files[i]['content']) for i in (1,3)]
    for text_index, result in ((0,negative),(2,normal)):
        raw = files[text_index]['content'].encode('utf-8')
        assert hashlib.sha256(raw).hexdigest() == result['raw_logs_sha256']['stdout.log']
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == files[text_index]['sha']
    assert negative['exit_code']==1 and normal['exit_code']==0
    assert negative['bit']==100 and negative['pc']=='0x80001bdc' and negative['vd']==10
    assert 'right= 0x0000001000000000, wrong = 0x0000000000000000' in files[0]['content']
    assert int('0000001000000000',16)==1<<(100-64)
    for suffix in ('/emu','/vdot-exceptions.bin','/boot-flash.bin'):
        keys=[k for k in negative['files'] if k.endswith(suffix)]
        assert len(keys)==1 and negative['files'][keys[0]]==normal['files'][keys[0]]
    assert 'planned=15 executed=15 passed=15 failed=0 unreachable=0' in files[2]['content']
    fig,ax=canvas('S3-03','高位注错被检出，正常参考通过','2026-10-24 · core-01 · 同镜像的两次独立运行',4.5)
    asset(ax,'verification-chip.png',.055,.682,.23,.16)
    label(ax,.315,.783,'同一 DUT · 同一程序 · 同一启动文件',10.0,weight='bold')
    label(ax,.315,.728,'仅更换所加载的参考模型',8.1,GRAY)
    # Branches are separate experiments, not an in-run reference switch.
    ax.plot([.50,.50],[.698,.662],color=GRAY,lw=1,transform=ax.transAxes)
    ax.plot([.265,.735],[.662,.662],color=GRAY,lw=1,transform=ax.transAxes)
    arrow(ax,.265,.662,.265,.620)
    arrow(ax,.735,.662,.735,.620)
    for col,(title,normal_run,color) in enumerate([
        ('A  参考模型注错',False,RED),('B  恢复正常参考',True,TEAL)]):
        xx=.035+col*.485
        rect(ax,xx,.167,.445,.441,face='#fff7f2' if col==0 else '#f0f7f7',edge=LINE)
        label(ax,xx+.024,.575,title,9.2,color,weight='bold')
        label(ax,xx+.165,.514,'高 64 位',7.3,GRAY,ha='center')
        label(ax,xx+.318,.514,'低 64 位',7.3,GRAY,ha='center')
        for yy,who in ((.463,'DUT'),(.353,'REF')):
            label(ax,xx+.022,yy,who,8.2,weight='bold')
            barx=xx+.086;barw=.31
            rect(ax,barx,yy-.024,barw/2,.048,face='#dce8f0',edge=LINE,radius=.003)
            rect(ax,barx+barw/2,yy-.024,barw/2,.048,face='#eaf0f4',edge=LINE,radius=.003)
            # Linear 127..0 bit position; only the indicated mismatch is encoded.
            if not normal_run and who=='REF':
                bx=barx+barw*((127-100)+.5)/128
                rect(ax,bx-.0045,yy-.028,.009,.056,face=RED,radius=0)
                arrow(ax,bx,.409,bx,yy+.032,color=RED,lw=.8)
                label(ax,bx+.012,.412,'bit100',7.7,RED)
        label(ax,xx+.241,.407,'=' if normal_run else '≠',16,color,ha='center',weight='bold')
        if normal_run:
            check(ax,xx+.072,.240,.018,color)
            label(ax,xx+.116,.240,'15 / 15 用例通过',10.1,color,weight='bold')
        else:
            cross(ax,xx+.072,.240,.016,color)
            label(ax,xx+.116,.240,'预期拒错',10.3,color,weight='bold')
    foot(ax,'向量条只示意高低半部及注错位；不虚构完整 128 位打印值。',.097)
    foot(ax,'EMU / BIN / 参考模型身份、首次差异和退出码见图注及原始记录。')
    save(fig,'S3-03')


def s3_performance():
    rows=[r for r in DATA['performance'] if r['mode']=='after']
    assert len(rows)==4 and all(int(r['samples_per_method'])==12 for r in rows)
    fig,ax=canvas('S3-05','四类微基准：逐项周期与加速比','0f · 固定同镜像 RVV 对照 · 全核 DUT cycle 计时窗口',4.1)
    for i,r in enumerate(rows):
        col=i%2;row=i//2
        pax=fig.add_axes([.14+col*.48,.55-row*.31,.31,.17])
        custom=float(r['custom_mean_cycles']);rvv=float(r['rvv_mean_cycles'])
        speed=float(r['rvv_sum_cycles'])/float(r['custom_sum_cycles'])
        assert math.isclose(speed,float(r['speedup_ratio_of_sums']),rel_tol=1e-12)
        bars=pax.barh([1,0],[rvv,custom],height=.43,color=[GRAY,TEAL])
        pax.set_xlim(0,rvv*1.21);pax.set_ylim(-.6,1.6)
        pax.set_yticks([1,0],['RVV','vdot'],fontsize=7.3)
        for spine in ('top','right','left'):pax.spines[spine].set_visible(False)
        pax.spines['bottom'].set_color(LINE);pax.tick_params(axis='y',length=0,pad=3)
        pax.tick_params(axis='x',labelsize=6.7,length=2)
        pax.set_xlabel('平均周期 / cycles',fontsize=6.9,labelpad=2)
        for b,v in zip(bars,[rvv,custom]):
            pax.text(v+rvv*.025,b.get_y()+b.get_height()/2,f'{v:g}',va='center',fontsize=7.3,color=NAVY)
        name={'single':'single × 1','chain':'chain × 256','batch':'batch × 128','stream':'stream × 64'}[r['scenario']]
        label(ax,.035+col*.48,.775-row*.31,name,9.3,weight='bold')
        label(ax,.45+col*.48,.775-row*.31,f'{speed:.3f}×',10.3,TEAL,ha='right',weight='bold')
    foot(ax,'同镜像 · 每类每法 n=12 · 各子图横轴尺度不同。',.100)
    foot(ax,'加速比按总周期之比；仅为所列微基准结果。')
    save(fig,'S3-05')


def s3_cost():
    fig,ax=canvas('S3-07','Nangate45：面积与时序约束敏感性','8b5024fc → 0f12df67 · Typical 1.10 V / 25°C · 布局前评估',5.45)
    for i,b in enumerate(('fu','parent')):
        x=.035+i*.48;v=DATA['area'][b];before=v['before'];after=v['after']
        rect(ax,x,.708,.45,.112,face=PALE)
        label(ax,x+.018,.798,'VDot FU' if b=='fu' else '完整 VFEX4 父级（含 FU）',8.2,weight='bold')
        label(ax,x+.018,.759,f'{after["area"]:,.3f} μm²',11.3,TEAL,weight='bold')
        change=100*(after['area']/before['area']-1)
        label(ax,x+.018,.726,f'面积变化 {change:+.4f}%',7.9,GRAY)
    profiles=['period050','nominal','period200','load001','load020']
    paths=[('fu',p) for p in ['i2o','i2r','r2o','r2r','ready']]+[('parent',p) for p in ['gate_enable','i2o','i2r','r2o','r2r','ready','vdot_i2r','vdot_r2o','vdot_r2r']]
    rows=DATA['timing'];assert len(rows)==70
    matrix=np.array([[float(next(r for r in rows if r['boundary']==b and r['path']==p and r['profile']==q)['after_slack_ns']) for q in profiles] for b,p in paths])
    pax=fig.add_axes([.30,.258,.65,.365])
    cmap=LinearSegmentedColormap.from_list('slack',['#b45a4a','#f8eee9','#f7fafb','#b9dfe1','#087f8c'])
    norm=TwoSlopeNorm(vmin=-3,vcenter=0,vmax=1.7)
    img=pax.imshow(matrix,cmap=cmap,norm=norm,aspect='auto',interpolation='none')
    ticklabels=[f'{DATA["profiles"][p]["period_ns"]:g} ns\n{DATA["profiles"][p]["load_ff"]} fF' for p in profiles]
    pax.set_xticks(range(5),ticklabels,fontsize=6.8);pax.xaxis.tick_top();pax.tick_params(length=0,pad=4)
    pax.set_yticks(range(14),[p for b,p in paths],fontsize=7.0)
    label(ax,.044,.557,'VDot FU',8.0,weight='bold')
    label(ax,.044,.382,'VFEX4\n父级',8.0,weight='bold')
    for spine in pax.spines.values():spine.set_visible(False)
    annotated={(i,1) for i in range(14)} | {np.unravel_index(matrix.argmin(),matrix.shape),np.unravel_index(matrix.argmax(),matrix.shape),(5,2)}
    for (i,j),value in np.ndenumerate(matrix):
        if (i,j) not in annotated:continue
        rgb = cmap(norm(value))[:3]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        luminance = sum(v*w for v,w in zip(linear,(.2126,.7152,.0722)))
        navy_luminance = .0303
        contrast_white = 1.05/(luminance+.05)
        contrast_navy = (luminance+.05)/(navy_luminance+.05)
        ink = 'white' if contrast_white > contrast_navy else NAVY
        pax.text(j,i,f'{value:+.3f}',ha='center',va='center',fontsize=7.1,color=ink)
    pax.axhline(4.5,color='white',lw=2)
    pax.add_patch(Rectangle((.5,-.5),1,14,fill=False,edgecolor=NAVY,linewidth=.8))
    label(ax,.035,.680,'候选裕量 / ns · 负值表示未满足',8.7,weight='bold')
    cax=fig.add_axes([.32,.207,.57,.014])
    cb=fig.colorbar(img,cax=cax,orientation='horizontal',ticks=[-3,-2,-1,0,1])
    cb.outline.set_visible(False);cb.ax.tick_params(labelsize=6.4,length=2,pad=2)
    label(ax,.035,.132,'1 ns / 5 fF：10 / 14 项为负',10.0,RED,weight='bold')
    foot(ax,'框选名义档；数字标名义档及选定关键值，完整 70 项见附件。',.078)
    foot(ax,'含门控建立检查；父级面积已含 FU。布局前结果不等同功耗或整核 PPA。')
    save(fig,'S3-07')


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
