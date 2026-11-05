"""Compose report panels without changing the archived screenshot pixels.

Chinese panel captions are placed below each panel. Original screenshot PNGs
remain unchanged; PyMuPDF clips their display region in the output PDF.
Requires PyMuPDF, Pillow, Matplotlib and installed SimSun.
"""
from pathlib import Path
from io import BytesIO
import argparse
import hashlib
import json

import fitz
from PIL import Image
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--preview-dir', type=Path)
parser.add_argument('--preview-dpi', type=int, default=180)
args = parser.parse_args()
font_path = font_manager.findfont(font_manager.FontProperties(family='SimSun'), fallback_to_default=False)
assert font_manager.FontProperties(fname=font_path).get_name() == 'SimSun'
plt.rcParams.update({'font.family':'SimSun', 'pdf.fonttype':3, 'axes.unicode_minus':False})

def item(name, caption='', crop=None):
    return {'name':name,'caption':caption,'crop':crop}

LAYOUTS = {
    'S1-03': [[item('WindowsTerminal_m5hXeDJnV1.png')]],
    'S1-04': [
        [item('msrdc_TvJP0uDH6i.png','(a) 输出位置：19626 ps',[220,0,2012,520])],
        [item('S1-04-01-vadd-positive-input.png','(b) 输入位置：19625 ps',[220,0,910,550]),
         item('S1-04-03-vadd-positive-commit.png','(c) 提交位置：19631 ps',[220,0,910,550])]],
    'S1-05': [
        [item('msrdc_yWBpPeYM8q.png','(a) 负数样例：输出位置 25461 ps')],
        [item('msrdc_6cIzJ9aIVJ.png','(b) 边界样例：输出位置 33010 ps')]],
    'S2-09': [
        [item('Notepad_kUWl09ct1X.png','(a) 组合算术 RTL 测试统计')],
        [item('S2-09-02-vdot-positive-response.png','(b) 正数事务：期望值 204 与完整响应',[0,0,693,150])],
        [item('S2-09-03-vdot-negative-response.png','(c) 负数事务：期望值 -8 与完整响应',[0,0,659,150])],
        [item('S2-09-04-vdot-boundary-response.png','(d) 边界事务：期望值 131072 与完整响应',[0,0,663,150])]],
    'SUP-S2-ARITH': [
        [item('WindowsTerminal_9ib5XAdUs2.png','(a) VDotProducts 乘积计算')],
        [item('WindowsTerminal_LFLdXsfe26.png','(b) VDotReduce 归约求和')]],
    'SUP-S2-MODEL': [[item('WindowsTerminal_yFneKZvWHF.png')]],
    'SUP-S2-OVERLAP': [[item('S2-05-vdot-overlap-log-2.png',crop=[0,150,875,552])]],
    'SUP-S2-STATE': [
        [item('WindowsTerminal_YZINbZqezU.png','(a) 槽位寄存器与 32 位结果保存',[0,45,900,434])],
        [item('WindowsTerminal_EK8zDAyWdk.png','(b) 握手与取消条件')],
        [item('WindowsTerminal_b2FCbAEdzj.png','(c) 状态更新与旧 P 迁移')]],
    'SUP-S3-SUMMARY': [
        [item('Notepad_25TDi0pHhe.png','(a) FU、父级与全核验证记录',[1266,0,1910,134])],
        [item('Notepad_4e1yBGB6vI.png','(b) 面积与时序记录',[1278,0,1903,55])]],
}

manifest = json.loads((ROOT/'screenshot-insertion-manifest.json').read_text(encoding='utf-8'))
expected = {Path(x['archived_source'].replace('\\','/')).name:x['source_sha256'] for x in manifest['source_images']}
receipt = {'layout':'captions below panels','font':'SimSun','source_pixels':'unchanged archived PNGs; PDF display clipping only','figures':[]}

def prepare(panel, width):
    path=ROOT/'source-screenshots'/panel['name']
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    assert sha==expected[panel['name']], panel['name']
    with Image.open(path) as image:
        iw,ih=image.size
    crop=panel['crop'] or [0,0,iw,ih]
    x0,y0,x1,y1=crop
    assert 0<=x0<x1<=iw and 0<=y0<y1<=ih
    height=width*(y1-y0)/(x1-x0)
    return {**panel,'path':path,'sha256':sha,'image_size':[iw,ih],'crop':crop,'width':width,'height':height}

def paint_image(page, panel, x, y):
    image_doc=fitz.open(panel['path'])
    image_pdf=fitz.open(stream=image_doc.convert_to_pdf(),filetype='pdf')
    r=image_pdf[0].rect; iw,ih=panel['image_size']
    x0,y0,x1,y1=panel['crop']
    clip=fitz.Rect(x0*r.width/iw,y0*r.height/ih,x1*r.width/iw,y1*r.height/ih)
    target=fitz.Rect(x,y,x+panel['width'],y+panel['height'])
    page.show_pdf_page(target,image_pdf,0,clip=clip)
    image_pdf.close();image_doc.close()
    return list(target)

def paint_caption(page, text, x, y, width):
    if not text:return
    fig=plt.figure(figsize=(width/72,20/72),facecolor='white')
    fig.text(.5,.45,text,ha='center',va='center',fontsize=9.2 if width>300 else 8.8,color='#17324d')
    output=BytesIO()
    fig.savefig(output,format='pdf',metadata={'CreationDate':None,'ModDate':None})
    plt.close(fig)
    with fitz.open(stream=output.getvalue(),filetype='pdf') as label_pdf:
        page.show_pdf_page(fitz.Rect(x,y,x+width,y+20),label_pdf,0)

for fid,rows in LAYOUTS.items():
    prepared=[];height=0
    for row in rows:
        width=(460-10*(len(row)-1))/len(row)
        panels=[prepare(p,width) for p in row]
        rh=max(p['height']+(20 if p['caption'] else 0) for p in panels)
        prepared.append((height,panels));height+=rh+10
    out=fitz.open();page=out.new_page(width=460,height=height-10)
    record={'id':fid,'panels':[]}
    for y,panels in prepared:
        for j,p in enumerate(panels):
            x=j*(p['width']+10)
            rect=paint_image(page,p,x,y)
            paint_caption(page,p['caption'],x,y+p['height'],p['width'])
            record['panels'].append({'source':p['path'].relative_to(ROOT).as_posix(),'source_sha256':p['sha256'],'crop_pixels':p['crop'],'display_rect_points':rect,'caption':p['caption']})
    out.set_metadata({'title':fid,'creator':'VDot report panel layout'})
    path=ROOT/(fid+'.pdf');out.save(path,garbage=4,deflate=True);out.close()
    record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();receipt['figures'].append(record)
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True,exist_ok=True)
        with fitz.open(path) as doc:
            doc[0].get_pixmap(dpi=args.preview_dpi,alpha=False).save(args.preview_dir/(fid+'.png'))

(ROOT/'screenshot-layout.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'composed':len(receipt['figures']),'all_source_hashes_verified':True}))
