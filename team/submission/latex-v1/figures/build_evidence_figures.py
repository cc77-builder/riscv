"""Rebuild evidence figures from the frozen, attributed data beside this file.

Usage: python figures/build_evidence_figures.py [--preview-dir DIR]
Requires matplotlib, NumPy and a CJK font; PDF previews also use PyMuPDF.
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
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "evidence-20261105/figure-data.json").read_text(encoding="utf-8"))
NAVY, TEAL, GRAY = "#17324d", "#087f8c", "#697b8c"
LIGHT, PALE, LINE = "#eaf4f5", "#f2f5f8", "#d4dee6"
RED, AMBER = "#ad4b3a", "#b27828"
for font in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc"):
    if Path(font).exists():
        font_manager.fontManager.addfont(font)
        CJK = font_manager.FontProperties(fname=font).get_name()
        break
else:
    raise SystemExit("Install Noto Sans CJK, Microsoft YaHei or SimSun.")
plt.rcParams.update({"font.family": CJK, "font.size": 8.5,
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
args = parser.parse_args()
OUTPUTS = []


def label(ax, x, y, text, size=8.5, color=NAVY, ha="left", va="center", weight="normal", **kw):
    return ax.text(x, y, text, fontsize=size, color=color, ha=ha, va=va,
                   fontweight=weight, transform=ax.transAxes, **kw)


def rect(ax, x, y, w, h, face=PALE, edge="none", radius=0.012, **kw):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=face, edgecolor=edge, linewidth=.6,
                       transform=ax.transAxes, **kw)
    ax.add_patch(p)
    return p


def canvas(fid, title, subtitle, height):
    fig = plt.figure(figsize=(6.3, height))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    label(ax, .035, .963, fid + "  /  EVIDENCE", 7.2, TEAL, weight="bold")
    label(ax, .035, .902 if height < 3.3 else .917, title, 12.0, weight="bold")
    label(ax, .035, .840 if height < 3.3 else .869, subtitle, 7.3, GRAY)
    return fig, ax


def save(fig, fid):
    path = ROOT / (fid + ".pdf")
    fig.savefig(path, metadata={"Creator": "VDot report evidence figure generator",
        "Title": fid + " — historical evidence redrawn", "CreationDate": None, "ModDate": None})
    if args.preview_dir:
        import fitz
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        # Preview the delivered PDF itself; direct matplotlib PNG output can
        # hide PDF-only font failures.
        with fitz.open(path) as pdf:
            pdf[0].get_pixmap(dpi=args.preview_dpi, alpha=False).save(args.preview_dir / (fid + ".png"))
    OUTPUTS.append({"id": fid, "path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    plt.close(fig)


def grid(ax, rows, cols, x=.275, y=.785, width=.685, step=.059, highlights=()):
    """rows = (name, values, color); invalid values must already be '—'."""
    cw = width / len(cols)
    for j, c in enumerate(cols):
        if j in highlights:
            rect(ax, x+j*cw, y-len(rows)*step+.012, cw, len(rows)*step+.04,
                 face="#fff3df", radius=0)
        label(ax, x+(j+.5)*cw, y+.029, str(c), 7.4, GRAY, ha="center")
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
    label(ax, .035, .064, "提交 PC 0x80000138  ·  指令 0x021101D7  ·  目的向量寄存器 v3", 7.1, GRAY)
    label(ax, .035, .023, "数字沿用 CSV 事件坐标；图中间距不表示时间长度，不能推导物理时钟或新硬件延迟。", 7.0, GRAY)
    save(fig, "S1-06")


def s2_ii1():
    rr = DATA["parent"]["ii1"]
    assert [r["cycle"] for r in rr] == list(range(10,18))
    assert all(r["accept"] and r["out_ready"] for r in rr)
    assert all(r["response"] and r["p_to_r"] for r in rr[2:])
    fig,ax=canvas("S2-05", "无阻塞时：接收、移动与输出同拍重叠", "0f · 真实 VFEX4 父级逐拍日志 · frozen-vdot-II1", 3.8)
    rows = [
        ("输入 offered / ready", [f'{r["offered"]}/{r["ready"]}' for r in rr], TEAL),
        ("输出 out_ready", [r["out_ready"] for r in rr], NAVY),
        ("P 槽事务（沿前）", [r["pseq"] if r["p"] else "—" for r in rr], TEAL),
        ("R 槽事务（沿前）", [r["rseq"] if r["r"] else "—" for r in rr], NAVY),
        ("P → R 移动", [r["p_to_r"] for r in rr], TEAL),
        ("新接收 seq", [r["accept_seq"] for r in rr], TEAL),
        ("FU 响应 seq", [r["response_seq"] if r["response"] else "—" for r in rr], NAVY),
    ]
    grid(ax, rows, [r["cycle"] for r in rr], y=.77, step=.066, highlights=(2,))
    rect(ax,.035,.17,.93,.115,face=LIGHT)
    label(ax,.055,.248,"cycle 12：R 输出 #1 ＋ P→R 移动 #2 ＋ 新接收 #3",9.1,TEAL,weight="bold")
    label(ax,.055,.202,"#1 在 10 接收、12 响应；连续接收间隔 = 1 拍。仅适用于无反压窗口。",7.6)
    label(ax,.035,.102,"seq 是独立测试记分板事务号；无效槽显示“—”。响应指 FU 握手，非 ROB 提交。",7.0,GRAY)
    label(ax,.035,.054,"来源：green-parent-01/result.log.gz，原行 12–19；时钟边沿由记录的 cycle 表示。",7.0,GRAY)
    save(fig,"S2-05")


def s1_boot():
    boot=DATA['boot']
    first=boot['failure'][0]['plain']
    m=re.search(r'pc\s*=\s*(0x[0-9a-f]+),\s*right=\s*(0x[0-9a-f]+),\s*wrong\s*=\s*(0x[0-9a-f]+)',first)
    assert m and int(m[1],16)==0x10000004
    assert 'instrCnt = 2' in boot['failure'][1]['plain']
    assert '--flash=' in boot['command'][0]['plain'] and 'Read 12 bytes' in boot['command'][4]['plain']
    assert 'HELLO_VADD_PASS cases=3 lanes=24' in boot['success'][1]['plain']
    assert 'exit_code=0' in boot['status'][0]['plain']
    fig,ax=canvas('S1-07','统一启动文件后，差分恢复正常','2026-10-09 历史运行 · 原日志与反汇编摘录重排',4.6)
    rect(ax,.035,.642,.93,.172,face='#fff1eb')
    label(ax,.055,.786,'A  首次差异发生在启动阶段',9.5,RED,weight='bold')
    label(ax,.055,.746,'t0  ·  首次差异 PC 0x10000004  ·  instrCnt = 2',8.5)
    label(ax,.055,.701,'right  '+m[2],8.3)
    label(ax,.52,.701,'wrong  '+m[3],8.3,RED)
    label(ax,.055,.667,'定位使用首次寄存器差异；未把后续 ABORT 事件地址当作首次故障 PC。',7.1,GRAY)
    rect(ax,.035,.321,.93,.282,face=PALE)
    label(ax,.055,.576,'B  DUT 与 NEMU 显式使用同一个 12 字节 flash',9.1,weight='bold')
    label(ax,.055,.540,'原命令：--flash=…/boot-flash.bin；NEMU 原日志：Read 12 bytes',7.8,TEAL)
    for x,t in ((.065,'文件偏移'),(.30,'机器字'),(.56,'反汇编指令')):label(ax,x,.499,t,7.6,GRAY)
    for i,(off,word,inst) in enumerate([('0x0','0010029b','addiw t0, zero, 1'),('0x4','01f29293','slli t0, t0, 0x1f'),('0x8','00028067','jr t0')]):
        assert word in boot['disassembly']
        for x,t in ((.065,off),(.30,word),(.56,inst)):label(ax,x,.465-i*.038,t,8.4)
    label(ax,.055,.344,'两端使用相同启动文件；装载地址遵循各自平台映射。',7.1,GRAY)
    rect(ax,.035,.105,.93,.177,face=LIGHT)
    label(ax,.055,.255,'C  同一历史恢复记录正常结束',9.5,TEAL,weight='bold')
    label(ax,.055,.214,'HELLO_VADD_PASS cases=3 lanes=24',9.1,TEAL)
    label(ax,.055,.176,'HIT GOOD TRAP at pc = 0x8000029c',8.6)
    label(ax,.055,.137,'Exit status: 0  ·  状态文件 exit_code=0',8.5)
    label(ax,.035,.060,'失败：20:53:54 运行，原行164/166；恢复：20:55:26运行，21:00:28 +08结束。',7.0,GRAY)
    label(ax,.035,.025,'日志、状态与反汇编的固定提交/文件SHA保存在图数据附件；本图没有新增运行。',7.0,GRAY)
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
    rows=[
      ("父级 inready",[r["inready"] for r in states],NAVY),
      ("FU vready",[r["vready"] for r in states],TEAL),
      ("输出 outvalid",[r["outvalid"] for r in states],TEAL),
      ("输出 outready",[r["outready"] for r in states],NAVY),
      ("P 槽 seq（有效时）",[r["pseq"] if r["pvalid"]=="1" else "—" for r in states],TEAL),
      ("R 槽 seq（有效时）",[r["rseq"] if r["rvalid"]=="1" else "—" for r in states],NAVY),
      ("P → R 移动",[r["move"] for r in states],TEAL),
      ("#1321 FU 响应",["1" if r["cycle"]=="181606" else "0" for r in states],NAVY),
    ]
    fig,ax=canvas("S2-06", "反压 7 拍：完整结果和事务身份保持", "0f 历史全核观察器 · core-01/control · 基准 cycle = 181597",4.55)
    grid(ax,rows,["+"+str(i) for i in range(10)],x=.27,width=.695,y=.785,step=.055,highlights=range(2,9))
    rect(ax,.035,.235,.93,.09,face=LIGHT)
    label(ax,.055,.296,"181599–181605：outvalid = 1，outready = 0",8.5,TEAL,weight="bold")
    label(ax,.055,.257,"128 位 data = 0x00000000000000000000000000001A87",8.1)
    label(ax,.035,.192,"保持字段：seq 1321 · ROB 1:9 · pdest 158 · vecwen 1 · v0wen 0 · exception 0",7.5)
    label(ax,.035,.151,"VPU 与 perf 全字段也逐行相同；181606 仅有一次 #1321 FU 响应。",7.5)
    label(ax,.035,.105,"父级 inready 与 FU vready 不同；181606 前者仍为 0。无效槽残留身份不绘为在途事务。",6.9,GRAY)
    label(ax,.035,.060,"原日志行 15012–15044；响应不是 ROB 提交。接收到响应相隔 9 拍，包含 7 拍反压。",7.0,GRAY)
    label(ax,.035,.024,"EMU 2d1db77cc407… · raw SHA256 c7351619b11e… · 历史记录重绘，无新增仿真。",6.9,GRAY)
    save(fig,"S2-06")


def s2_cancel():
    fig,ax=canvas("S2-07", "取消与复位：只保留仍然有效的事务", "0f 真实父级 · 三个取消窗口与一个独立复位窗口",5.55)
    specs=[("cancel_p","(a) 仅取消 P · ROB 环绕","partial-ROB-48",12790,12791),
           ("cancel_r","(b) 仅取消 R · 反序接收","partial-ROB-54",12878,12879),
           ("cancel_both","(c) P / R 同时取消","partial-ROB-12",12266,12267),
           ("reset","(d) reset 优先于 redirect","TE0-reset-7",14811,14813)]
    for k,(key,title,case,cancel,nextcycle) in enumerate(specs):
        yy=.775-k*.178
        rr=DATA["parent"][key]
        before=next(r for r in rr if r["cycle"]==cancel)
        after=next(r for r in rr if r["cycle"]==nextcycle)
        rect(ax,.035,yy-.119,.93,.16,face=PALE)
        label(ax,.052,yy+.015,title,8.6,weight="bold")
        label(ax,.95,yy+.015,case,7.0,GRAY,ha="right")
        def identity(r,slot):
            seq=r[slot+"seq"]
            if not r[slot]:return "无效"
            ident=DATA["identities"][str(seq)]
            return f'#{seq} / ROB {ident["rob_flag"]}:{ident["rob"]}'
        x1,x2=.16,.66
        label(ax,x1,yy-.024,f'cycle {cancel} 沿前',7.4,GRAY)
        label(ax,x1,yy-.055,'P  '+identity(before,'p'),7.8,TEAL)
        label(ax,x1,yy-.084,'R  '+identity(before,'r'),7.8,NAVY)
        if key=='reset': event='reset=1\nredirect=1'
        else:event=f'kill_P={before["kill_p"]}\nkill_R={before["kill_r"]}'
        label(ax,.51,yy-.058,event,7.4,RED,ha="center")
        for x0,x1 in ((.414,.464),(.558,.617)):
            ax.annotate('',xy=(x1,yy-.058),xytext=(x0,yy-.058),xycoords='axes fraction',
                        arrowprops={'arrowstyle':'->','lw':.7,'color':GRAY})
        label(ax,x2,yy-.024,f'cycle {nextcycle} 沿前',7.4,GRAY)
        label(ax,x2,yy-.055,'P  '+identity(after,'p'),7.8,TEAL)
        label(ax,x2,yy-.084,'R  '+identity(after,'r'),7.8,NAVY)
        if key in ('cancel_p','cancel_r'):
            tail=("P → R；" if key=='cancel_r' else "")+f'幸存事务 #{after["response_seq"]} 于 {nextcycle} 输出'
        elif key=='cancel_both':tail='取消当拍 child_out=0；下一拍两槽均无效'
        else:tail='reset_drop=2，kill_P/R=0；14813–14815 子时钟均为 0'
        label(ax,.052,yy-.106,tail,6.9,GRAY)
    label(ax,.035,.093,"取消使用 ROB 的 flag 与 index 判龄；seq 仅标识测试事务，不能代替程序年龄。",7.1,GRAY)
    label(ax,.035,.058,"redirect 的 ROB：(a)(b) 为 1:0，(c)(d) 为 0:10；self 均为 0。",7.1,GRAY)
    label(ax,.035,.024,"图中槽状态为边沿前记录；新接收发生在该边沿。原 case 与逐行证据见 figure-data.json。",6.9,GRAY)
    save(fig,"S2-07")


def s2_div():
    fig,ax=canvas("S2-08", "DIV 切换、取消清理与空闲关钟", "0f 真实 VFEX4 父级 · 动态记录仅含整数 DIV 与浮点 DIV",5.7)
    label(ax,.035,.802,"A  先排空 VDot，再接收 DIV",9.4,weight="bold")
    for i,(key,kind,c1,c2,c3,c4) in enumerate([
        ('switch_int','整数 DIV',11447,11448,11449,11459),
        ('switch_fp','浮点 DIV',11504,11505,11506,11514)]):
        yy=.711-i*.135; rr=DATA['parent'][key]
        rect(ax,.035,yy-.062,.93,.116,face=PALE)
        label(ax,.052,yy+.033,kind,8.3,weight='bold')
        label(ax,.95,yy+.033,rr[0]['case'],6.8,GRAY,ha='right')
        xs=[.18,.42,.66,.89]
        texts=[f'{c1}\n旧 R 输出',f'{c2}\n剩余 VDot 输出',f'{c3}\nDIV 接收',f'{c4}\nDIV 响应']
        for x,t in zip(xs,texts):label(ax,x,yy-.019,t,7.4,TEAL if x==.66 else NAVY,ha='center')
        for x0,x1 in zip(xs[:-1],xs[1:]):
            ax.annotate('',xy=(x1-.07,yy-.013),xytext=(x0+.07,yy-.013),xycoords='axes fraction',arrowprops={'arrowstyle':'->','lw':.7,'color':GRAY})
    label(ax,.035,.463,"B  取消仍保留清理边沿，随后关闭子时钟",9.4,weight='bold')
    for i,(key,name,base) in enumerate([('cancel_int','整数 DIV',13328),('cancel_fp','浮点 DIV',13769)]):
        rr=DATA['parent'][key];yy=.383-i*.137
        label(ax,.035,yy+.024,name,8.0,weight='bold')
        label(ax,.035,yy-.007,rr[0]['case'],6.8,GRAY)
        label(ax,.035,yy-.038,f'起点 {base}',6.8,GRAY)
        cw=.665/8;xx=.30
        for j,r in enumerate(rr):
            x=xx+(j+.5)*cw
            face='#fff3df' if r['kill_div'] else (LIGHT if r['clocks']==0 else PALE)
            rect(ax,xx+j*cw+.002,yy-.047,cw-.004,.083,face=face,radius=.004)
            label(ax,x,yy+.019,'+'+str(j),7.1,GRAY,ha='center')
            label(ax,x,yy-.007,str(r['clocks']),8.5,TEAL if r['clocks']==0 else NAVY,ha='center',weight='bold')
            evt='取消' if r['kill_div'] else ('入 DIV' if j==0 else ('入 VDot' if r['accept'] else ('响应' if r['response'] else '')))
            label(ax,x,yy-.033,evt,7.2,RED if r['kill_div'] else GRAY,ha='center')
    label(ax,.035,.139,"数字为上升沿后采样的子时钟位掩码：1 = VDot，2 = VIDiv，4 = VFDiv。",7.0,GRAY)
    label(ax,.035,.103,"0 表示三个子时钟均关闭；取消当拍保留清理时钟。该记录不是 gate_enable 波形。",7.0,GRAY)
    label(ax,.035,.065,"SQRT 仅有静态取消路径检查，本图不扩展为 SQRT 动态验证或功耗测量。",7.2,RED)
    label(ax,.035,.027,"原始逐拍日志重绘；上部箭头间距按事件排列，不表示 DIV 运算时间比例。",7.0,GRAY)
    save(fig,"S2-08")


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
    fig,ax=canvas('S3-03','高位错误被拒绝，同镜像恢复通过','0f 原始整核记录 · 2026-10-24 · core-01 的两个连续运行',5.05)
    rect(ax,.035,.737,.93,.081,face=PALE)
    label(ax,.055,.793,'保持相同：EMU 2d1db77cc407…  /  BIN b8b7e1a70320…',8.0,weight='bold')
    label(ax,.055,.759,'同一 boot-flash；恢复时将负控参考模型切回正常参考模型。',7.6,GRAY)
    rect(ax,.035,.369,.93,.334,face='#fff1eb')
    label(ax,.055,.673,'A  negative-vdot：按预期拒错',10.0,RED,weight='bold')
    label(ax,.94,.673,'exit 1',9.7,RED,ha='right',weight='bold')
    label(ax,.055,.634,'首次差异 PC 0x80001bdc · 指令 0x0294050b · 目的 v10',8.2)
    label(ax,.055,.596,'原 stdout 的高 64 位差异（L204）',7.9,GRAY)
    label(ax,.075,.555,'right = 0x0000001000000000',9.3,TEAL)
    label(ax,.075,.515,'wrong = 0x0000000000000000',9.3,RED)
    label(ax,.055,.468,'位位置：高半部 bit 36 = 完整 128 位向量的 bit 100',8.5,weight='bold')
    label(ax,.055,.426,'12:46:20 → 12:58:45 +08  ·  负控参考 SHA256 9b3aecf362b7…',7.5)
    label(ax,.055,.392,'ABORT 事件 PC 0x800016b0 是另一字段，不作首次失配地址。',7.3,GRAY)
    rect(ax,.035,.118,.93,.216,face=LIGHT)
    label(ax,.055,.304,'B  functional-0：恢复正常参考',10.0,TEAL,weight='bold')
    label(ax,.94,.304,'exit 0',9.7,TEAL,ha='right',weight='bold')
    label(ax,.055,.265,'VDOT_SUMMARY  planned=15  executed=15  passed=15',8.6)
    label(ax,.055,.228,'failed=0  unreachable=0  ·  HIT GOOD TRAP at 0x8000236a',8.1)
    label(ax,.055,.188,'12:58:45 → 13:28:42 +08  ·  正常参考 SHA256 efbed0774add…',7.5)
    label(ax,.055,.148,'原 stdout L40–41 与 result.json；这是同镜像恢复，未添加独立 replay。',7.0,GRAY)
    label(ax,.035,.073,'读数范围：原 stdout 显示高 64 位差异；完整向量位号由 64 + 36 得出。',7.0,GRAY)
    label(ax,.035,.032,'本图绑定 2026-10-24 原 0f 运行；R5 clean02 的独立验收身份见正文。',7.0,GRAY)
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
    rect(ax,.035,.075,.93,.095,face=LIGHT)
    label(ax,.052,.139,'加速比 = ΣRVV 周期 / Σvdot 周期；每法每类 12 个正式样本。',7.5)
    label(ax,.052,.101,'DIV 关钟修复前 8b5024 与 0f：配对窗口周期相同；stream 仅约 1.005×。',7.2)
    label(ax,.035,.029,'柱图分别从零开始，横轴尺度因场景不同；不减空窗口，不使用主机运行时间。',7.0,GRAY)
    save(fig,'S3-05')


def s3_cost():
    fig,ax=canvas('S3-07','Nangate45：面积与五档 setup 裕量','8b5024fc → 0f12df67 · Typical 1.10 V / 25°C · 布局前评估',5.8)
    for i,b in enumerate(('fu','parent')):
        x=.035+i*.48;v=DATA['area'][b];before=v['before'];after=v['after']
        rect(ax,x,.708,.45,.112,face=PALE)
        label(ax,x+.018,.798,'VDot FU' if b=='fu' else '完整 VFEX4 父级（含 FU）',8.2,weight='bold')
        label(ax,x+.018,.761,f'{before["area"]:,.3f} → {after["area"]:,.3f} μm²',8.0,TEAL)
        change=100*(after['area']/before['area']-1)
        label(ax,x+.018,.727,f'Δ {change:+.4f}%   ·   DFF {before["dff_count"]}→{after["dff_count"]}   ·   ICG {after["icg_count"]}',6.8,GRAY)
    profiles=['period050','nominal','period200','load001','load020']
    paths=[('fu',p) for p in ['i2o','i2r','r2o','r2r','ready']]+[('parent',p) for p in ['gate_enable','i2o','i2r','r2o','r2r','ready','vdot_i2r','vdot_r2o','vdot_r2r']]
    rows=DATA['timing'];assert len(rows)==70
    matrix=np.array([[float(next(r for r in rows if r['boundary']==b and r['path']==p and r['profile']==q)['after_slack_ns']) for q in profiles] for b,p in paths])
    pax=fig.add_axes([.30,.235,.65,.375])
    cmap=LinearSegmentedColormap.from_list('slack',['#b45a4a','#f8eee9','#f7fafb','#b9dfe1','#087f8c'])
    norm=TwoSlopeNorm(vmin=-3,vcenter=0,vmax=1.7)
    pax.imshow(matrix,cmap=cmap,norm=norm,aspect='auto',interpolation='none')
    ticklabels=[f'{DATA["profiles"][p]["period_ns"]:g} ns\n{DATA["profiles"][p]["load_ff"]} fF' for p in profiles]
    pax.set_xticks(range(5),ticklabels,fontsize=6.8);pax.xaxis.tick_top();pax.tick_params(length=0,pad=4)
    pax.set_yticks(range(14),[b+'/'+p for b,p in paths],fontsize=6.9)
    for spine in pax.spines.values():spine.set_visible(False)
    for (i,j),value in np.ndenumerate(matrix):
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
    label(ax,.035,.680,'候选时序裕量 / ns（含门控建立检查）；负值表示未满足',8.3,weight='bold')
    rect(ax,.035,.112,.93,.079,face='#fff1eb')
    label(ax,.052,.164,'1 ns / 5 fF：所报 14 类检查中 10 类为负；不代表 1 ns 时序收敛。',8.0,RED,weight='bold')
    label(ax,.052,.132,'父级面积已包含 FU，不能相加。面积变化不能直接推算动态功耗。',7.2)
    label(ax,.035,.073,'五档为单变量约束敏感性；布局前参考库结果，未测整核 PPA、布线后时序、功耗或 Fmax。',7.0,GRAY)
    label(ax,.035,.031,'来源：cost/results/timing.csv（70 行）与 summary.json；完整精度与起止点保留于数据附件。',7.0,GRAY)
    save(fig,'S3-07')


if __name__ == '__main__':
    s1_timeline();s1_boot();s2_ii1();s2_backpressure();s2_cancel();s2_div();s3_negative_recovery();s3_performance();s3_cost()
    (ROOT/'evidence-20261105/generated-figures.json').write_text(json.dumps(OUTPUTS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figures':len(OUTPUTS),'ids':[x['id'] for x in OUTPUTS]},ensure_ascii=False))
