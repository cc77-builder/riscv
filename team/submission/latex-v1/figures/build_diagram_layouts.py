"""Build display PDFs from the thirteen reviewed replacement diagrams.

Archived user PNGs are verified and preserved. The selected-artwork manifest
identifies each replacement and its actual production method. The thirteen
formal engineering diagrams use authored SVG geometry and editable text;
reviewed PDF outlines avoid an observed CFF digit-mapping defect. Report
captions remain outside the artwork. Original and failed exports are retained
under their recorded identities and never substituted for selected assets.
Requires PyMuPDF and Pillow.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parent
WIDTH_PT = 160.0 / 25.4 * 72.0
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--preview-dir', type=Path)
parser.add_argument('--preview-dpi', type=int, default=180)
args = parser.parse_args()
plan = json.loads((ROOT / 'diagram-layout-plan.json').read_text(encoding='utf-8'))
originals = {x['id']: x for x in json.loads(
    (ROOT / 'named-figure-insertion-manifest-20261104.json').read_text(encoding='utf-8'))}
selected = json.loads((ROOT / 'redesigned-20261105' / 'selected-diagrams.json').read_text(encoding='utf-8'))
specs = {x['id']: x for x in selected['figures']}
assert len(specs) == len(selected['figures']) == 13
assert set(specs) == {x['id'] for x in plan['figures']}

receipt = {'archive_policy': 'original PNGs verified and unchanged',
           'titles': 'provided below each figure by the report',
           'display_width_mm': 160.0, 'figures': []}


def outlined_svg_typography(fid, spec, supporting_sources):
    """Check the editable, hash-bound SVG for explicitly outlined PDF text.

    Outlining avoids an observed CFF ToUnicode digit-mapping defect. It is not
    permission to infer font size from raster pixels or silently skip checks.
    These authored SVGs use unscaled text and optional translations only.
    """
    relative = spec['editable_svg']
    assert relative in {x['file'] for x in supporting_sources}, (fid, 'unbound SVG')
    path = (ROOT / relative).resolve()
    raw = path.read_text(encoding='utf-8')
    svg = ET.fromstring(raw)
    assert svg.attrib['width'].endswith('mm') and svg.attrib['height'].endswith('mm'), fid
    width = float(svg.attrib['width'][:-2])
    height = float(svg.attrib['height'][:-2])
    view = [float(x) for x in svg.attrib['viewBox'].split()]
    sx, sy = width / view[2], height / view[3]
    assert abs(width - 160) < .05 and abs(sx - sy) < 1e-6, (fid, 'SVG scale')
    for node in svg.iter():
        transform = node.attrib.get('transform', '').strip()
        assert not transform or re.fullmatch(r'translate\([^)]*\)', transform), (fid, 'scaled text not supported')
    sizes = [float(x) for x in re.findall(r'font-size=[\"\']([0-9.]+)(?:px)?[\"\']', raw)]
    sizes += [float(x) for x in re.findall(r'font-size:\s*([0-9.]+)(?:px)?', raw)]
    assert sizes and svg.findall('.//{http://www.w3.org/2000/svg}text'), (fid, 'editable text missing')
    minimum = min(sizes) * sx * 72 / 25.4
    assert minimum >= 10.98, (fid, 'outlined text below 11 pt', minimum)
    review = spec['typography_review']
    assert review['actual_final_pdf_preview_reviewed'], (fid, 'actual preview not reviewed')
    assert abs(review['minimum_text_pt'] - minimum) < .03, (fid, 'SVG font-size mismatch')
    return minimum, [width, height]

for original in plan['figures']:
    fid = original['id']
    archived = ROOT / (fid + '.png')
    archived_sha = hashlib.sha256(archived.read_bytes()).hexdigest()
    assert archived_sha == original['source_sha256'] == originals[fid]['sha256'], fid
    with Image.open(archived) as im:
        assert list(im.size) == original['source_size_pixels'], fid

    spec = specs[fid]
    artwork = (ROOT / spec['file']).resolve()
    assert artwork.is_relative_to(ROOT), (fid, 'asset outside figures')
    assert artwork.suffix.lower() in {'.pdf', '.png'}, fid
    digest = hashlib.sha256(artwork.read_bytes()).hexdigest()
    assert digest == spec['sha256'], (fid, 'selected asset changed')
    destination = ROOT / (fid + '.pdf')
    record = {'id': fid, 'archived_source': archived.name,
              'archived_source_sha256': archived_sha, 'source': spec['file'],
              'source_sha256': digest, 'method': spec['method']}
    supporting_sources = []
    for supporting in spec.get('supporting_sources', []):
        source = (ROOT / supporting['file']).resolve()
        assert source.is_relative_to(ROOT), (fid, 'supporting source outside figures')
        source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        assert source_sha == supporting['sha256'], (fid, 'supporting source changed')
        supporting_sources.append({'file': supporting['file'], 'sha256': source_sha})
    if supporting_sources:
        record['supporting_sources'] = supporting_sources

    if artwork.suffix.lower() == '.pdf':
        with fitz.open(artwork) as src:
            assert len(src) == 1, (fid, 'one artwork page required')
            page = src[0]
            assert abs(page.rect.width - WIDTH_PT) < 0.2, (fid, page.rect)
            spans = [s for b in page.get_text('dict')['blocks'] if 'lines' in b
                     for line in b['lines'] for s in line['spans'] if s['text'].strip()]
            if spec.get('text_representation') == 'vector-outlines':
                assert not spans and not page.get_images() and page.get_drawings(), (fid, 'outlined vector PDF required')
                minimum, svg_size = outlined_svg_typography(fid, spec, supporting_sources)
                assert abs(page.rect.height / 72 * 25.4 - svg_size[1]) < .05, (fid, 'SVG/PDF height')
                record.update({'text_representation': 'vector outlines',
                               'editable_svg': spec['editable_svg'],
                               'typography_basis': 'hash-bound editable SVG at native physical size'})
            else:
                assert spans, (fid, 'precise diagram must retain authored text')
                minimum = min(s['size'] for s in spans)
                assert minimum >= 10.98, (fid, 'text below 11 pt', minimum)
                outside = [s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))]
                assert not outside, (fid, 'text outside artwork', outside)
            record.update({'minimum_text_pt': minimum,
                           'display_size_mm': [page.rect.width / 72 * 25.4,
                                               page.rect.height / 72 * 25.4]})
        shutil.copyfile(artwork, destination)
    else:
        with Image.open(artwork) as im:
            iw, ih = im.size
        height = WIDTH_PT * ih / iw
        out = fitz.open()
        page = out.new_page(width=WIDTH_PT, height=height)
        page.insert_image(page.rect, filename=str(artwork))
        out.set_metadata({'title': fid, 'creator': 'VDot report selected artwork'})
        out.save(destination, garbage=4, deflate=True, no_new_id=True)
        out.close()
        record.update({'source_size_pixels': [iw, ih],
                       'display_size_mm': [160.0, height / 72 * 25.4],
                       'typography_review': spec['typography_review']})

    record['sha256'] = hashlib.sha256(destination.read_bytes()).hexdigest()
    receipt['figures'].append(record)
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        with fitz.open(destination) as doc:
            doc[0].get_pixmap(dpi=args.preview_dpi, alpha=False).save(
                args.preview_dir / (fid + '.png'))

(ROOT / 'diagram-layout.json').write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'composed': len(receipt['figures']),
                  'all_archive_and_selected_hashes_verified': True}))
