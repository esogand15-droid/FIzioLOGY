#!/usr/bin/env python3
"""Build a source-page/topic crosswalk from declared provenance, not a text audit.

The resulting inventory makes omissions and misplaced assets easier to find. It
must not be interpreted as proof that a page was transcribed verbatim or that an
image was visually checked.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / 'headneck/content'
outline = json.loads((CONTENT / 'outline/hn02_topics.json').read_text(encoding='utf-8'))
topics = [t for name in ('hn02_a.json', 'hn02_b.json')
          for t in json.loads((CONTENT / name).read_text(encoding='utf-8'))]
names = {t['topic_id']: t['title'] for t in outline['topics']}
trans = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')

def source_pages(src):
    src = src.translate(trans)
    if 'جزوه' not in src:
        return []
    result = set()
    for m in re.finditer(r'(?:صفحهٔ\s*PDF|صفحه|ص)\s*(\d+)(?:\s*[–-]\s*(\d+))?', src):
        lo = int(m.group(1)); hi = int(m.group(2) or lo)
        if 1 <= lo <= hi <= 33:
            result.update(range(lo, hi + 1))
    return sorted(result)

pages = {str(n): {'topics': [], 'text_blocks': [], 'lecture_images': []} for n in range(1, 34)}
for topic in topics:
    tid = topic['topic_id']
    for index, block in enumerate(topic['blocks']):
        for page in source_pages(block.get('src', '')):
            row = pages[str(page)]
            if tid not in row['topics']:
                row['topics'].append(tid)
            if block['type'] in ('p', 'ul', 'ol') and 'متن جزوه' in block.get('src', ''):
                row['text_blocks'].append({'topic': tid, 'block_index': index, 'type': block['type']})
            if block['type'] == 'plate' and block.get('book') == 'lecture':
                row['lecture_images'].append({'topic': tid, 'block_index': index, 'asset': block['asset']})
# Use the start pages reported by the most recent PDF QA pass.  These are
# topic ranges, not an assertion of the precise location of each block.
qa_path = ROOT / 'headneck/reports/HN_S02_QA_REPORT.md'
qa = qa_path.read_text(encoding='utf-8').translate(trans)
starts = {m.group(1): int(m.group(2)) for m in re.finditer(
    r'^\| (hn02-T\d+) \| [^|]+ \| \d+ \| \d+ \| (\d+) \|$', qa, re.M)}
if set(starts) != set(names):
    raise ValueError('QA report does not contain a start page for each topic; rebuild and run QA first')
ordered_starts = sorted(starts.items(), key=lambda x: x[1])
if len({p for _, p in ordered_starts}) != len(ordered_starts):
    raise ValueError('Topic start pages are not distinct')
# The last topic ends before the summary; its exact end is left unspecified.
ranges = {}
for i, (tid, start) in enumerate(ordered_starts):
    ranges[tid] = {'start_page': start,
                   'end_page_inclusive': ordered_starts[i + 1][1] - 1 if i + 1 < len(ordered_starts) else None}
for key, row in pages.items():
    row['topic_titles'] = [names[x] for x in row['topics']]
    row['output_topic_page_ranges'] = {x: ranges[x] for x in row['topics']}
    row['verification'] = 'declared provenance only; transcription and image coverage not certified'
out = {'session': 'hn02', 'source_pdf_pages': pages,
       'method': 'Automatic mapping from source citations in base content; does not certify completeness or visual checks.'}
path = ROOT / 'headneck/reports/HN_S02_COVERAGE_MATRIX.json'
path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{path.relative_to(ROOT)}: {len(pages)} pages; {sum(len(x["text_blocks"]) for x in pages.values())} text mappings; {sum(len(x["lecture_images"]) for x in pages.values())} image mappings')
