#!/usr/bin/env python3
"""Restyle reviewed exact SVG drawings without changing text or geometry."""
from pathlib import Path
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
import fitz

ROOT=Path(__file__).resolve().parent
PALETTE={'#F6F3EE':'#FFFFFF','#242424':'#24384A','#E8E3DC':'#E8F2F3',
         '#CE4B32':'#287F84','#766E65':'#637487','#DAD4CB':'#CED9E2'}
OUTPUT=ROOT/'figures';OUTPUT.mkdir(exist_ok=True)
records=[]
for fid in ['S2-01','S2-02','S2-03','S2-10','S3-04']:
    src=ROOT/'inputs'/f'{fid}.svg'
    raw=src.read_bytes();before=raw.decode('utf-8');after=before
    for old,new in PALETTE.items():after=after.replace(old,new)
    assert re.sub(r'#[0-9a-fA-F]{6}','<color>',before)==re.sub(r'#[0-9a-fA-F]{6}','<color>',after)
    svg=OUTPUT/f'{fid}.svg';svg.write_text(after,encoding='utf-8')
    xml=ET.fromstring(after)
    width=float(xml.attrib['width'].removesuffix('mm'))
    height=float(xml.attrib['height'].removesuffix('mm'))
    view_width=float(xml.attrib['viewBox'].split()[2])
    font_sizes=[float(v) for v in re.findall(r'font-size="([0-9.]+)"',after)]
    font_sizes += [float(v) for v in re.findall(r'font-size:\s*([0-9.]+)(?:px)?',after)]
    assert font_sizes
    minimum=min(font_sizes)*width/view_width*72/25.4
    assert minimum>=10.99,(fid,minimum)
    pdf=OUTPUT/f'{fid}.pdf'
    subprocess.run(['inkscape',str(svg),'--export-area-page','--export-text-to-path',
                    '--export-type=pdf',f'--export-filename={pdf}'],check=True,capture_output=True)
    subprocess.run(['pdftoppm','-r','230','-singlefile','-png',str(pdf),str(OUTPUT/fid)],
                    check=True,capture_output=True)
    with fitz.open(pdf) as doc:
        p=doc[0]
        assert len(doc)==1 and not p.get_text().strip() and not p.get_images()
        assert p.get_drawings()
        assert abs(p.rect.width/72*25.4-width)<.01
        assert abs(p.rect.height/72*25.4-height)<.01
    files={}
    for ext in ['svg','pdf','png']:
        p=OUTPUT/f'{fid}.{ext}';b=p.read_bytes()
        files[p.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    records.append({'id':fid,'source':str(src.relative_to(ROOT)),
        'source_sha256':hashlib.sha256(raw).hexdigest(),'geometry_and_text_unchanged':True,
        'width_mm':width,'height_mm':height,'minimum_text_pt':minimum,
        'typography_basis':'authored SVG font-size and physical/viewBox scale; editable text retained',
        'pdf_text_representation':'vector outlines; no incorrect CFF ToUnicode retained',
        'files':files,'actual_final_pdf_preview_reviewed':False,'human_adopted':False})
record={'schema':1,'method':'exact palette replacement only, followed by mature SVG/PDF rendering',
    'palette_mapping':PALETTE,'scope':'No geometry, label, engineering data or frozen source changed.',
    'font_fallback':'Noto Sans CJK SC installed; Windows font families are named only and not distributed.',
    'figures':records}
(ROOT/'source-and-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'count':len(records),'figures':[{k:r[k] for k in ['id','width_mm','height_mm','minimum_text_pt']} for r in records]},ensure_ascii=False))
