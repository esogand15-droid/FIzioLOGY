#!/usr/bin/env python3
"""Inventory session 3 source and Netter image placements before editing.

Automated extraction is a navigation aid, not a visual or verbatim audit.
Image placements are not necessarily individual illustrations: one raster may
contain several figures and vector drawings are not counted as raster images.
"""
from pathlib import Path
import hashlib
import json
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
LECTURE = next((ROOT / 'علوم تشریح سر و گردن').glob('جلسه 3*/*.pdf'))
ATLAS = next((ROOT / 'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1').glob('Netter*.pdf'))
OUTPUT = ROOT / 'headneck/reports/HN_S03_SOURCE_INVENTORY.json'


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(path, lecture=False):
    doc = pymupdf.open(path)
    pages = []
    for n, page in enumerate(doc, 1):
        placements = []
        for item in page.get_images(full=True):
            xref, _, width, height = item[:4]
            for rect in page.get_image_rects(xref):
                placements.append({'xref': xref, 'bbox': [round(x, 2) for x in rect],
                                   'pixel_width': width, 'pixel_height': height})
        row = {'pdf_page': n, 'page_width': page.rect.width, 'page_height': page.rect.height,
               'raster_placements': placements}
        if lecture:
            # Plain extraction can reorder RTL, drop glyphs, or corrupt words.
            row['raw_text'] = page.get_text('text')
        pages.append(row)
    return {'source': str(path.relative_to(ROOT)), 'sha256': sha256(path),
            'page_count': len(doc), 'pages': pages}


lecture = inventory(LECTURE, lecture=True)
atlas = inventory(ATLAS)
gray_dir = ROOT / 'علوم تشریح دستگاه اعصاب'
gray = [inventory(next(gray_dir.glob(f'*Gray*{part}.pdf'))) for part in ('801-1000', '1001-1189')]
outline = json.loads((ROOT / 'headneck/content/outline/hn03_topics.json').read_text(encoding='utf-8'))['topics']
for page in lecture['pages']:
    page['declared_outline_topics'] = [t['topic_id'] for t in outline if page['pdf_page'] in t['pages']]
content = [t for part in ('a', 'b') for t in
           json.loads((ROOT / f'headneck/content/hn03_{part}.json').read_text(encoding='utf-8'))]
assets = json.loads((ROOT / 'headneck/images/INDEX.json').read_text(encoding='utf-8'))['assets']
used = []
for topic in content:
    for index, block in enumerate(topic['blocks']):
        if block.get('type') == 'plate':
            matches = [a for a in assets if a.get('path') == block.get('asset')]
            used.append({'topic': topic['topic_id'], 'block_index': index,
                         'asset': block.get('asset'), 'book': block.get('book'),
                         'source_page': matches[0].get('page') if matches else None,
                         'source_bbox': matches[0].get('bbox') if matches else None})
out = {'disclaimer': 'Automatic inventory only; raw RTL text requires visual reconciliation. '
       'Raster placements do not count all individual figures or vector artwork. '
       'This inventory is not evidence of visual review or complete coverage.',
       'lecture': lecture, 'netter': atlas, 'gray_parts': gray, 'base_figure_uses': used}
OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{OUTPUT.relative_to(ROOT)}: lecture={len(lecture["pages"])} pages, '
      f'Netter={len(atlas["pages"])} pages, base figure uses={len(used)}')
