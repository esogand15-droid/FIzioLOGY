"""Index source pages, raw text and existing topic/figure references for review.

This is an inventory, not OCR or a transcription. PDF text extraction can
reverse mixed-script text, break words, or omit text embedded in pictures.
Image blocks do not include every vector drawing. A page/topic match is only
an outline reference, not proof that its contents or figures were transferred.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / 'headneck/content'
OUT = ROOT / 'headneck/reports/source_inventory_01_05'
SOURCES = {
  1: ['جلسه 1 - سر و گردن 1/جلسه_اول_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'],
  2: ['جلسه 2 - سر و گردن 2/جلسه_دوم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'],
  3: ['جلسه 3 -Spheneid & Palatin & Occipital bones/جلسه_سوم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'],
  4: ['جلسه 4 - قاعده جمجمه/جلسه_چهارم_پارت_اول_علوم_تشریح_سر_و_گردن_مهر_1404.pdf',
      'جلسه 4 - قاعده جمجمه/جلسه_چهارم_پارت_دوم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'],
  5: ['جلسه 5 - گردن/جلسه_پنجم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'],
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = json.loads((ROOT / 'headneck/images/INDEX.json').read_text(encoding='utf-8'))['assets']
    report = {'disclaimer': 'فهرست ماشینی برای بازبینی؛ استخراج خام رونویسی نیست و تعداد تصویرها شامل همهٔ ترسیم‌های برداری نیست.', 'sessions': []}
    for number, sources in SOURCES.items():
        sid = f'hn{number:02}'
        outline = json.loads((CONTENT / f'outline/{sid}_topics.json').read_text(encoding='utf-8'))
        topics = {t['topic_id']: dict(t, placed_figures=[]) for t in outline['topics']}
        for suffix in ('a', 'b'):
            for topic in json.loads((CONTENT / f'{sid}_{suffix}.json').read_text(encoding='utf-8')):
                for block in topic['blocks']:
                    if block['type'] == 'plate':
                        topics[topic['topic_id']]['placed_figures'].append({k: block.get(k) for k in ('book', 'asset', 'title', 'citation', 'src')})
        session = {'session': sid, 'topics': list(topics.values()), 'source_parts': [],
                   'registered_assets': [a for a in index if a.get('session') == sid]}
        for part, name in enumerate(sources, 1):
            path = ROOT / 'علوم تشریح سر و گردن' / name
            doc = pymupdf.open(path)
            source = {'part': part, 'path': str(path.relative_to(ROOT)),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'page_count': len(doc), 'pages': []}
            raw = []
            for offset, page in enumerate(doc):
                page_no = offset + 1
                outline_page = 100 + page_no if number == 4 and part == 2 else page_no
                text = page.get_text()
                raw.append({'pdf_page': page_no, 'raw_text': text})
                blocks = [b for b in page.get_text('dict')['blocks'] if b['type'] == 1]
                source['pages'].append({'pdf_page': page_no, 'outline_page': outline_page,
                    'text_characters': len(text),
                    'image_blocks': [{'bbox': [round(x, 2) for x in b['bbox']], 'width': b['width'], 'height': b['height']} for b in blocks],
                    'outline_topics': [t['topic_id'] for t in outline['topics'] if outline_page in t['pages']]})
            session['source_parts'].append(source)
            (OUT / f'{sid}_part{part}_raw_text.json').write_text(json.dumps({'source': source['path'],
                'disclaimer': 'استخراج خام PDF؛ به دلیل ترتیب راست‌به‌چپ و خطاهای دیگر باید با صفحهٔ تصویری مقابله شود.',
                'pages': raw}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        report['sessions'].append(session)
    (OUT / 'inventory.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Indexed', sum(p['page_count'] for s in report['sessions'] for p in s['source_parts']), 'pages;',
          sum(len(s['topics']) for s in report['sessions']), 'topics.')


if __name__ == '__main__':
    main()
