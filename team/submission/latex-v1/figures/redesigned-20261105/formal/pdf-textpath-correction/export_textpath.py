from pathlib import Path
import hashlib
import json
import subprocess
import fitz

ROOT=Path(__file__).resolve().parent
results=[]
for stem in ['S1-01-environment','S3-01-structural']:
    source=ROOT/'sources'/(stem+'.svg')
    pdf=ROOT/(stem+'-textpath.pdf')
    png=ROOT/(stem+'-textpath.png')
    commands=[['inkscape',str(source),'--export-type=pdf','--export-text-to-path','--export-filename='+str(pdf)],
              ['pdftoppm','-png','-r','220','-singlefile',str(pdf),str(png.with_suffix(''))]]
    runs=[]
    for cmd in commands:
        p=subprocess.run(cmd,capture_output=True,text=True,check=True)
        runs.append({'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    doc=fitz.open(pdf)
    assert len(doc)==1
    assert doc[0].get_text().strip()==''
    assert doc[0].get_fonts()==[]
    result={'figure':stem,'runs':runs,'page_mm':[doc[0].rect.width*25.4/72,doc[0].rect.height*25.4/72],
            'text_extraction':'empty as expected; all visible text is outlined','embedded_fonts':0,
            'visual_inspection_pending':True,'files':[]}
    for p in [source,pdf,png]:
        b=p.read_bytes();result['files'].append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    results.append(result)
(ROOT/'render-qa.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False))
