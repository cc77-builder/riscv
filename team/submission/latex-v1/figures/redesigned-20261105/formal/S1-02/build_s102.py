#!/usr/bin/env python3
"""Draw the historical S1-02 deployment process; never runs project commands.

Run: python build_s102.py [--source-root /path/to/latex-v1]
Without --source-root, finds the report root among this script's ancestors.
Needs Noto Sans CJK SC, Inkscape, PyMuPDF. Only writes beside this script.
SVG text stays editable; PDF text is outlined; PNG comes from the actual PDF.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import fitz

HERE=Path(__file__).resolve().parent
STEM='S1-02-deployment-flow'
W,H=160.0,148.0
PT=25.4/72
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
NAVY,TEAL,GRAY,LINE='#24384A','#287F84','#637487','#CED9E2'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def resolve_source_root(requested=None):
    candidates=[requested.expanduser().resolve()] if requested is not None else [HERE,*HERE.parents]
    for candidate in candidates:
        if (candidate/'figures/placement.json').is_file() and (candidate/'content').is_dir():
            return candidate
    raise FileNotFoundError('Report root must contain figures/placement.json and content; use --source-root if it is not an ancestor of this script.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root',type=Path,help='Report root; by default search this script\'s ancestors')
    try:
        src=resolve_source_root(ap.parse_args().source_root)
    except FileNotFoundError as exc:
        ap.error(str(exc))
    names=['content/overview-stage1.tex','content/narrative-stage1.md','figures/placement.json',
           'evidence/tool-versions.txt','evidence/build-concurrency-adjustment.log',
           'evidence/hello-vadd-summary.log','evidence/hello-vadd-run-20261009-205354.log',
           'evidence/hello-vadd-run-20261009-205526.status']
    files=[src/n for n in names]
    baseline=HERE/'evidence/stage1-e2.tex'
    baseline_source={'repository':'cc77-builder/riscv','ref':'e2c2e8d5fa9a92c5d99c3c3e3f5399d60a115c63',
                     'path':'team/submission/latex-v1/sections/stage1.tex','local':'evidence/stage1-e2.tex',
                     'sha256':'c3d69defa8252b558c37e5282e9031dfcc0e7133defa06fabedb3f0bea3caff1',
                     'blob_sha':'836284ad8f9a96c813921c7e7d6fcc2fcfc233de'}
    raw_baseline=baseline.read_bytes()
    assert sha(baseline)==baseline_source['sha256']
    assert hashlib.sha1(f'blob {len(raw_baseline)}\0'.encode()+raw_baseline).hexdigest()==baseline_source['blob_sha']
    files.append(baseline)
    script_source=HERE/'evidence/stage1_script.sh'
    source_index=HERE/'evidence/stage1-script-source.json'
    frozen=json.loads(source_index.read_text(encoding='utf-8'))
    assert frozen['key']=='stage1_script'
    raw_script=script_source.read_bytes()
    assert sha(script_source)==frozen['sha256']
    assert hashlib.sha1(f'blob {len(raw_script)}\0'.encode()+raw_script).hexdigest()==frozen['blob_sha']
    files.extend([script_source,source_index])
    overview=files[0].read_text(encoding='utf-8')
    narrative=files[1].read_text(encoding='utf-8')
    for phrase in ['配置WSL资源','核对工具版本','构建NEMU','差分运行','退出状态']:
        assert phrase in overview,phrase
    assert '失败记录与恢复记录分别保存' in narrative
    assert '按故障原因返回' in (src/'figures/placement.json').read_text(encoding='utf-8')
    assert 'Exit status: 0' in (src/'evidence/hello-vadd-summary.log').read_text(encoding='utf-8')
    assert 'Exit status: 1' in (src/'evidence/hello-vadd-run-20261009-205354.log').read_text(encoding='utf-8')

    svg=ET.Element(f'{{{NS}}}svg',{'width':f'{W:g}mm','height':f'{H:g}mm',
        'viewBox':f'0 0 {W:g} {H:g}','version':'1.1','role':'img','aria-labelledby':'title desc'})
    def el(tag,parent=None,**attrs):
        return ET.SubElement(svg if parent is None else parent,f'{{{NS}}}{tag}',{k.replace('_','-'):str(v) for k,v in attrs.items()})
    el('title',id='title').text='S1-02 环境部署与验证执行流程'
    el('desc',id='desc').text=(
        'Historical 2026-10-09 deployment: prepare WSL and fixed sources, check tools, build NEMU/EMU '
        'and hello-vadd/flash, run DiffTest with fixed inputs and inspect output/exit state. Successful '
        'results and failed evidence are archived separately. Failures are preserved before diagnosis. '
        'Dashed return branches select preparation, tool checks or affected builds according to cause; '
        'they are a diagnostic method, not claims that every historical step failed, or that all three '
        'must be repeated. No new run or PASS is represented.')
    defs=el('defs')
    for name,col in [('navy',NAVY),('gray',GRAY),('teal',TEAL)]:
        m=el('marker',parent=defs,id=f'arrow-{name}',viewBox='0 0 8 8',refX='7.2',refY='4',
             markerWidth='2.2',markerHeight='2.2',orient='auto',markerUnits='userSpaceOnUse')
        el('path',parent=m,d='M 0 0 L 8 4 L 0 8 Z',fill=col)
    el('rect',x=0,y=0,width=W,height=H,fill='white')
    texts=[]
    def txt(x,y,s,size=11.5,color=NAVY,anchor='start',ident=None):
        assert size>=11.5
        ident=ident or f'text-{len(texts):02d}'
        t=el('text',id=ident,x=x,y=y,font_family='Noto Sans CJK SC',font_size=f'{size*PT:.6f}',
             text_anchor=anchor,fill=color,font_weight=400)
        t.text=s;texts.append({'id':ident,'text':s,'size_pt':size})
    def path(d,color=NAVY,dash=False,arrow=False,width=.30,ident=None):
        a={'d':d,'fill':'none','stroke':color,'stroke_width':width,'stroke_linejoin':'round'}
        if dash:a['stroke_dasharray']='1.4 1.0'
        if arrow:a['marker_end']='url(#arrow-'+{NAVY:'navy',GRAY:'gray',TEAL:'teal'}[color]+')'
        if ident:a['id']=ident
        el('path',**a)
    def box(x,y,w,h,title,lines,kind='main',ident=''):
        col=TEAL if kind=='archive' else NAVY if kind=='main' else GRAY
        fill='#F1F8F8' if kind=='archive' else 'white'
        el('rect',id=ident,x=x,y=y,width=w,height=h,fill=fill,stroke=col,stroke_width=.28)
        txt(x+w/2,y+5.5,title,size=12.0,color=col,anchor='middle',ident=ident+'-title')
        for i,s in enumerate(lines):txt(x+w/2,y+11.5+6.0*i,s,color=GRAY,anchor='middle',ident=ident+f'-detail-{i}')

    # A dated scope label, not a success stamp or a duplicated figure title.
    txt(3,6.8,'2026-10-09 历史流程',color=GRAY)
    txt(156.5,6.8,'实线：执行与留证',color=GRAY,anchor='end')
    path('M 3 13 H 10',color=TEAL,dash=True,arrow=True)
    txt(12,14.6,'按原因选择返回点',color=TEAL)

    x,w,c=24.0,65.0,56.5
    nodes=[
        ('prepare',20,14,'环境准备',['WSL 资源 · 固定源码依赖']),
        ('tools',41,14,'工具核查',['版本与路径']),
        ('build',62,23,'构建产物',['NEMU reference / EMU','hello/vadd / 共同 flash']),
        ('run',94,23,'DiffTest 运行',['固定 reference 与 flash','核对输出与退出状态']),
        ('success',128,14,'成功结果归档',['成功日志 · 输入身份']),
    ]
    for key,y,h,title,lines in nodes:
        box(x,y,w,h,title,lines,kind='archive' if key=='success' else 'main',ident=key)
    for y1,y2 in [(34,41),(55,62),(85,94),(117,128)]:
        path(f'M {c} {y1} V {y2-.7}',arrow=True)
    txt(61,124.4,'正常完成',size=11.5)

    # Conditional failures converge on their own evidence archive. Each branch
    # is labelled; this does not assert that all branches historically occurred.
    for key,y in [('prepare',27),('tools',48),('build',73.5),('run',101)]:
        path(f'M 89 {y} H 105',color=GRAY,ident=f'failure-from-{key}')
        txt(97.1,y-1.4,'异常',color=GRAY,anchor='middle')
    path('M 105 27 V 101 H 110.3',color=GRAY,arrow=True)
    box(111,94,46,14,'失败证据归档',['日志 · 退出码'],kind='failure',ident='failure-evidence')
    box(111,128,46,14,'定位与修正',['按最早异常定位'],kind='failure',ident='diagnose')
    path('M 134 108 V 127.3',color=GRAY,arrow=True)

    # Three explicitly alternative return ports, with no direct jump to success
    # or weakening/disabling of DiffTest. The loop runs outside all process boxes.
    path('M 134 142 V 146 H 8 V 27',color=TEAL,dash=True)
    for key,y in [('prepare',27),('tools',48),('build',73.5)]:
        path(f'M 8 {y} H 23.3',color=TEAL,dash=True,arrow=True,ident=f'return-to-{key}')

    svgfile=HERE/f'{STEM}.svg';pdffile=HERE/f'{STEM}.pdf';pngfile=HERE/f'{STEM}.png'
    ET.indent(svg,space='  ');svgfile.write_bytes(ET.tostring(svg,encoding='utf-8',xml_declaration=True))
    subprocess.run(['inkscape',str(svgfile),'--export-area-page','--export-text-to-path','--export-type=pdf',
                    f'--export-filename={pdffile}'],check=True,capture_output=True)
    doc=fitz.open(pdffile);page=doc[0];page.get_pixmap(dpi=240,alpha=False).save(pngfile)
    assert not page.get_fonts() and not page.get_text().strip()
    q=subprocess.run(['inkscape',str(svgfile),'--query-all'],check=True,text=True,capture_output=True).stdout
    bounds={r.split(',')[0]:[float(v) for v in r.split(',')[1:]] for r in q.splitlines() if len(r.split(','))==5}
    overflow=[]
    for t in texts:
        a,b,ww,hh=bounds[t['id']]
        if a<0 or b<0 or a+ww>W*96/25.4+.1 or b+hh>H*96/25.4+.1:overflow.append(t['text'])
    assert not overflow,overflow
    report={
        'schema':'s102-deployment-flow-review-v1','figure_id':'S1-02','created_utc':datetime.now(timezone.utc).isoformat(),
        'status':'candidate-awaiting-actual-visual-review','human_aesthetic_approval':False,
        'canvas_mm':[W,H],'minimum_text_pt':min(t['size_pt'] for t in texts),
        'font':{'family':'Noto Sans CJK SC','svg_text_editable':True,'pdf_text_outlined':True,
                'validation':'SVG native point sizes and Inkscape glyph bounds; actual PDF preview. No PDF text-span claim.'},
        'automatic_checks':{'documentary_assertions':True,'text_outside_canvas':overflow,
                            'pdf_no_text_objects':not page.get_text().strip(),'pdf_size_mm':[page.rect.width*PT,page.rect.height*PT]},
        'preview':{'renderer':'PyMuPDF from saved outlined PDF','dpi':240},
        'scope':'2026-10-09 historical process; documentation only, no new engineering execution, PASS, or 0f/T04 result transfer.',
        'semantic_edges':[
            ['prepare','tools','normal progression'],['tools','build','normal progression'],
            ['build','run','normal progression'],['run','success','only after normal completion and output/exit-state review'],
            *[[k,'failure-evidence','conditional abnormal result; method, not claim of actual historical occurrence'] for k in ['prepare','tools','build','run']],
            ['failure-evidence','diagnose','preserve failure before diagnosis and correction'],
            *[['diagnose',k,'select the corresponding return point according to cause; not all return points mandatory'] for k in ['prepare','tools','build']]],
        'evidence_mapping':{
            'main_sequence':'overview-stage1.tex lines 27,32-37; stage1-e2.tex lines 41,48-53',
            'inputs_and_archive':'narrative-stage1.md build/loader roles, lines 11-18,48,103-111; overview lines 80,112',
            'success_failure_separate':'narrative-stage1.md lines 56-62; actual failing run exit 1, successful summary exit 0 and status file',
            'diagnostic_alternatives':'current placement S1-02 scope explicitly returns to preparation/tools/build by fault cause; narrative-stage1.md failure diagnosis method',
            'historical_recovery_examples':'build-concurrency-adjustment.log: intentional interruption, -j4, preserve objects; startup flash difference and common-image recovery in narrative lines 56-62'},
        'direct_script_source':{**frozen,'local_checked':str(script_source),'independently_verified_sha256_and_git_blob':True,
                                'observed':'nemu/emu/workload/run actions, per-action logs and EXIT status trap, artifact SHA, explicit flash/reference and 128MB RAM; no automatic diagnostic or repair loop'},
        'baseline_source':{**baseline_source,'independently_verified_sha256_and_git_blob':True},
        'not_asserted':['No claim that stage1.sh automatically diagnoses or repairs faults; its frozen script was read, never run.',
                        'No claim that all depicted abnormal branches occurred historically.',
                        'No claim that all faults need a rebuild or full reinstallation.',
                        'No OOM diagnosis added to the intentional C++ interruption record.',
                        'No new PASS, simulation, benchmark, or 2026-10-25 T04 event in this historical process.'],
        'sources':[{'path':str(p),'sha256':sha(p)} for p in files],
        'outputs':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in [svgfile,pdffile,pngfile,Path(__file__).resolve()]},
        'text_inventory':texts,'visual_review':{'actual_pdf_preview_viewed':False},
        'recommended_caption':'环境部署、差分运行与分支归档流程',
        'recommended_scope_note':'2026年10月9日阶段一流程。虚线表示按故障原因选择的修正返回点，成功结果与失败证据分别保存。'
    }
    (HERE/'source-and-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pdf':str(pdffile),'canvas_mm':[W,H],'minimum_text_pt':11.5,'out_of_canvas':overflow},ensure_ascii=False))

if __name__=='__main__':main()
