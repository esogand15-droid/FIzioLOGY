#!/usr/bin/env python3
"""Map initial session-3 lecture transcription to pre-existing topics.

This is an editorial plan, not an independent transcription audit. It does
not alter existing session content, activate the overlay, or build a PDF.
Every non-image block must be assigned exactly once. Figures are already used
in the base content and are handled separately to avoid duplicate plates.
"""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = ROOT / 'headneck/content'
source = json.loads((C / 'hn03_source_transcription_wip.json').read_text(encoding='utf-8'))
pages = {p['pdf_page']:p for p in source['pages']}
# (PDF page, inclusive start, exclusive end, topic).  Image blocks in the
# ranges are skipped; their source and placements are separately inventoried.
plan = [
 (2,0,10,1), (3,0,3,1), (3,3,8,2),
 (4,0,9,3), (4,9,15,4), (5,0,5,4), (5,5,8,3), (5,8,10,2), (5,10,11,8), (5,11,12,4),
 (6,0,2,8), (6,2,5,7), (6,5,11,5), (6,11,18,4),
 (7,0,2,4), (7,2,6,5), (7,6,9,6), (8,0,1,6), (8,1,7,6), (8,7,15,7),
 (9,0,6,7), (9,6,10,8), (10,0,12,9), (10,12,14,10),
 (11,0,9,10), (12,0,18,11), (13,0,3,11), (13,3,11,12),
 (14,0,2,12), (14,2,12,13), (15,0,4,13), (15,4,6,14), (15,6,10,12), (15,10,11,15),
 (16,0,15,15), (16,15,17,16), (17,0,12,16), (17,12,13,17), (18,0,1,17), (18,1,8,18),
 (19,0,7,18), (19,7,12,17), (20,0,1,17), (20,1,6,18), (20,6,14,19),
]
topics = {f'hn03-T{n:02}':[] for n in range(1,20)}
seen = Counter()
for page, start, end, topic_no in plan:
    blocks=pages[page]['blocks']
    assert 0 <= start < end <= len(blocks), (page,start,end)
    for i in range(start,end):
        block=blocks[i]
        if block['type'] == 'image':
            continue
        seen[(page,i)] += 1
        topics[f'hn03-T{topic_no:02}'].append({'source_pdf_page':page,
            'transcription_block_index':i, 'block':block})
expected={(p['pdf_page'],i) for p in pages.values()
          for i,b in enumerate(p['blocks']) if b['type'] != 'image'}
assert set(seen) == expected, {'missing':sorted(expected-set(seen)),
                               'unexpected':sorted(set(seen)-expected)}
assert all(n == 1 for n in seen.values()), [p for p,n in seen.items() if n != 1]
assert all(topics.values())
result={'status':'work in progress; page transcription second-pass reviewed; topic mapping still needs editorial review',
        'method':'manual topic assignment of transcription blocks; image blocks handled separately',
        'source':'headneck/content/hn03_source_transcription_wip.json','topics':topics}
out=ROOT/'headneck/reports/HN_S03_TRANSCRIPTION_TOPIC_MAP_WIP.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(f'{len(expected)} non-image blocks mapped exactly once into {len(topics)} topics; '
      'this is not proof of transcription accuracy.')
