"""Assemble the judge-facing report from reviewed, named source blocks."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
HEADINGS = re.compile(r'(?m)^\\(section|subsection|subsubsection)\{([^\n]+)\}\s*$')


def split_blocks(text, prefix):
    matches = list(HEADINGS.finditer(text))
    blocks = []
    if matches and text[:matches[0].start()].strip():
        blocks.append({'id': prefix + ':intro', 'title': '',
                       'tex': text[:matches[0].start()].strip()})
    for index, match in enumerate(matches, 1):
        end = matches[index].start() if index < len(matches) else len(text)
        blocks.append({'id': f'{prefix}:{index:02}', 'title': match[2],
                       'original_level': match[1], 'tex': text[match.end():end].strip()})
    return blocks


def source_blocks(overview, narrative, technical, convert):
    # Legacy drawn placeholders are replaced by explicit figure placements in
    # the reviewed structure. Their original source remains in the archive.
    overview = re.sub(r'\\begin\{center\}\s*\\begin\{tikzpicture\}.*?\\end\{center\}',
                      '', overview, flags=re.S)
    blocks = split_blocks(overview, 'overview')
    blocks += split_blocks(convert(narrative), 'narrative')
    for index, (title, path, text) in enumerate(technical, 1):
        entries = split_blocks(convert(text), f'technical{index}')
        for entry in entries:
            entry['source_title'] = title
            entry['source_path'] = path
        blocks += entries
    return blocks


def assemble(stage, blocks, tex_text):
    layout = json.loads((ROOT / 'content' / f'structure-stage{stage}.json').read_text(encoding='utf-8'))
    sources = {x['id']: x for x in blocks}
    slots = {x['id']: x for x in json.loads((ROOT / 'figures/placement.json').read_text(encoding='utf-8'))}
    used = []
    figures = []
    supplement_path = ROOT / 'sections' / f'screenshots-stage{stage}.tex'
    supplements = {}
    if supplement_path.exists():
        for line in supplement_path.read_text(encoding='utf-8').splitlines():
            match = re.match(r'\\evidencefigure\{([^}]+)\}', line)
            if match:
                supplements[match[1]] = line
    used_supplements = []
    result = [r'\renewcommand{\stagefigureprefix}{' + str(stage) + r'}\setcounter{figure}{0}',
              r'\reporttitle{' + layout['report_title'] + '}', layout.get('introduction_tex', '')]
    for section in layout['sections']:
        result.append(r'\section{' + section['title'] + '}')
        for item in section['items']:
            if 'block' in item:
                key = item['block']
                assert key in sources and key not in used, (stage, key)
                used.append(key)
                block = sources[key]
                title = item.get('title', block['title'])
                if item.get('heading', True) and title:
                    result.append(r'\subsection{' + title + '}')
                result.append(block['tex'])
            elif 'tex' in item:
                if item.get('heading', True) and item.get('title'):
                    result.append(r'\subsection{' + item['title'] + '}')
                result.append(item['tex'])
            elif 'supplement' in item:
                fid = item['supplement']
                assert fid in supplements and fid not in used_supplements, fid
                used_supplements.append(fid)
                result.append(supplements[fid])
            elif 'figure' in item:
                fid = item['figure']
                assert fid in slots and slots[fid]['stage'] == stage and fid not in figures, fid
                figures.append(fid)
                slot = slots[fid]
                result.append(r'\reportfigure{' + fid + '}{' + tex_text(slot['title']) + '}{' +
                              str(slot['height_cm']) + 'cm}{' + tex_text(slot['content']) + '}{' +
                              tex_text(slot['source'] + '。' + slot['scope']) + '}')
            else:
                raise ValueError('Unknown layout item: ' + str(item))
    omitted = layout.get('omitted', {})
    assert not (set(used) & set(omitted)), 'A block cannot be used and omitted'
    assert set(used) | set(omitted) == set(sources), ('Unaccounted blocks', set(sources) - set(used) - set(omitted))
    assert set(figures) == {fid for fid, x in slots.items() if x['stage'] == stage}, 'Missing figure placement'
    assert set(used_supplements) == set(supplements), 'Missing supplemental figure placement'
    return '\n\n'.join(result) + '\n'
