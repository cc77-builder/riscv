"""Inspect compiled report PDFs and render contact sheets for human visual review.

Requires PyMuPDF and Pillow. Run after build.py; this checks document delivery,
not RTL or historical engineering qualification. Visual review remains separate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'main':'三阶段技术文档_合订本.pdf', 'stage1':'第一阶段_执行日志与过程文档.pdf',
         'stage2':'第二阶段_设计与基础测试文档.pdf', 'stage3':'第三阶段_协同仿真与性能分析.pdf'}
NEW = {'S1-06','S1-07','S2-05','S2-06','S2-07','S2-08','S3-03','S3-05','S3-07'}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compiled-dir',type=Path,default=ROOT/'output')
parser.add_argument('--logs-dir',type=Path,required=True)
parser.add_argument('--result-dir',type=Path,required=True)
parser.add_argument('--render-dir',type=Path)
args = parser.parse_args()
args.result_dir.mkdir(parents=True,exist_ok=True)
slots = json.loads((ROOT/'figures/placement.json').read_text(encoding='utf-8'))
reports, maps = {}, {}
compact = lambda text: re.sub(r'\s+','',text)
for key,name in NAMES.items():
    path=args.compiled_dir/name
    doc=fitz.open(path)
    texts=[page.get_text() for page in doc]
    body_start=doc.get_toc()[0][2]
    fonts=sorted({font[3] for page in doc for font in page.get_fonts(full=True)})
    outside=[]
    for n,page in enumerate(doc,1):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    if x0 < -1 or y0 < -1 or x1 > page.rect.width+1 or y1 > page.rect.height+1:
                        outside.append({'page':n,'bbox':span['bbox'],'text':span['text']})
    log=(args.logs_dir/key/(key+'.log')).read_text(encoding='utf-8',errors='replace')
    diagnostics=[line for line in log.splitlines() if re.search(r'Overfull|Underfull|Missing character|LaTeX Warning|Package .+ Warning|^!',line)]
    body_text='\n'.join(page.get_text(clip=fitz.Rect(0,65,page.rect.width,780)) for page in list(doc)[body_start-1:])
    count=len(re.findall('[\u4e00-\u9fff]',body_text))
    figure_map={}
    for slot in slots:
        if key!='main' and slot['stage']!=int(key[-1]):continue
        fid=slot['id'];number=f"{slot['stage']}-{int(fid[-2:])}"
        caption=compact('图'+number+slot['title'])
        pages=[i+1 for i,text in enumerate(texts) if caption in compact(text)]
        images=[ROOT/'figures'/(fid+'.'+ext) for ext in ('pdf','png','jpg')]
        actual=next((p for p in images if p.is_file()),None)
        figure_map[fid]={'number':number,'pdf_pages':pages,'present':actual is not None,
                         'source_path':str(actual.relative_to(ROOT)) if actual else None}
    footer_mismatches=[]
    for i in range(body_start-1,len(doc)):
        expected=str(i-(body_start-1)+1)
        footer=doc[i].get_text(clip=fitz.Rect(240,790,355,842)).strip()
        if footer!=expected:footer_mismatches.append({'page':i+1,'expected':expected,'actual':footer})
    record={'pages':len(doc),'body_start_pdf_page':body_start,'body_chinese_characters':count,
            'final_log_diagnostics':diagnostics,'outside_text':outside,'fonts':fonts,
            'pdf_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'pdf_bytes':path.stat().st_size,'footer_mismatches':footer_mismatches,
            'placeholder_pages':[i+1 for i,t in enumerate(texts) if '待插入图片' in t],
            'a4_all_pages':all(abs(p.rect.width-595.276)<.5 and abs(p.rect.height-841.89)<.5 for p in doc),
            'figure_captions_unique':all(len(f['pdf_pages'])==1 for f in figure_map.values())}
    if key!='main':record['required_chinese_characters']=10000 if key=='stage1' else 17000
    reports[key]=record;maps[key]={'pages':len(doc),'figures':figure_map}
    if args.render_dir:
        dest=args.render_dir/key;dest.mkdir(parents=True,exist_ok=True)
        for first in range(0,len(doc),12):
            sheet=Image.new('RGB',(1050,4*520),'#e5e9ed');draw=ImageDraw.Draw(sheet)
            for j,index in enumerate(range(first,min(first+12,len(doc)))):
                pix=doc[index].get_pixmap(matrix=fitz.Matrix(.56,.56),alpha=False)
                thumb=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                x=(j%3)*350+(350-thumb.width)//2;y=(j//3)*520+25
                sheet.paste(thumb,(x,y));draw.text(((j%3)*350+10,(j//3)*520+5),f'{key} / PDF page {index+1}',fill='#17324d')
            sheet.save(dest/f'contact-{first+1:03d}.png')
        selected={0,body_start-1}
        for fid,value in figure_map.items():
            if fid in NEW:selected.update(p-1 for p in value['pdf_pages'])
        for index in sorted(selected):
            doc[index].get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(dest/f'page-{index+1:03d}.png')
    print(json.dumps({'document':key,'pages':len(doc),'body_start':body_start,'han':count,
                      'diagnostics':diagnostics,'outside_count':len(outside),
                      'caption_ok':record['figure_captions_unique'],'footers':footer_mismatches},ensure_ascii=False))
result={'date':'2026-11-05','status':'AUTOMATED_INSPECTION_COMPLETE_VISUAL_REVIEW_PENDING',
        'scope':'Nine missing figure slots completed from fixed historical evidence; no new RTL/simulation/EDA validation.',
        'body_count_method':'U+4E00..U+9FFF in extractable PDF text from first body bookmark to end, clipped to y=65..780 points. Cover, TOC, header and footer excluded. Only extractable figure text is counted; Type3 outline glyphs are not included.',
        'reports':reports}
(args.result_dir/'pdf-inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(args.result_dir/'page-map.json').write_text(json.dumps(maps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
