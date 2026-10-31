#!/usr/bin/env python3
"""Check opt-in session-3 integration preserves source and original content.

This is a content-identity test, not proof the transcription matches the PDF.
"""
from copy import deepcopy
from pathlib import Path
import json
import os
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'render'))
from hn_updates import apply_update, _hn03_source_blocks
C = ROOT / 'headneck/content'
base = {t['topic_id']: t['blocks'] for part in ('a', 'b')
        for t in json.loads((C / f'hn03_{part}.json').read_text(encoding='utf-8'))}
source = json.loads((C / 'hn03_source_transcription_wip.json').read_text(encoding='utf-8'))
pages = {p['pdf_page']: p['blocks'] for p in source['pages']}
mapping = json.loads((ROOT / 'headneck/reports/HN_S03_TRANSCRIPTION_TOPIC_MAP_WIP.json').read_text(encoding='utf-8'))['topics']
assert set(mapping) == set(base)
os.environ.pop('HUMSYAR_HN03_WIP', None)
assert apply_update('hn03', base) is base
os.environ['HUMSYAR_HN03_WIP'] = '1'
result = apply_update('hn03', base)
count = 0
for tid, entries in mapping.items():
    generated = _hn03_source_blocks(tid, mapping)
    assert result[tid][1:1+len(generated)] == generated
    generated = [b for b in generated if not (b['type']=='h3' and b['text'].startswith('متن جزوهٔ درس — صفحهٔ PDF '))]
    assert len(generated) == len(entries)
    for row, b in zip(entries, generated):
        p, i = row['source_pdf_page'], row['transcription_block_index']
        raw = pages[p][i]
        assert raw == row['block']
        assert b['type'] == {'heading':'h3', 'paragraph':'p', 'list':'ol'}[raw['type']]
        if raw['type'] == 'list': assert b['items'] == raw['items']
        else: assert b['text'] == raw['text']
        count += 1
    # The base survives in order. Presentation-only list type/metadata changes
    # and idcard extension are treated as expected, not as text changes.
    after = result[tid][1+len(_hn03_source_blocks(tid,mapping)):]
    position=0
    for old in base[tid][1:]:
        candidate=deepcopy(old)
        if candidate.get('type')=='ul': candidate['type']='ol'
        if 'src' in candidate:
            candidate['src']=candidate['src'].replace(' — رونویسی در حال مقابله','')
        while position < len(after) and after[position] != candidate: position+=1
        assert position < len(after), (tid,old)
        position+=1
    assert result[tid][0]['rows'][:len(base[tid][0]['rows'])] == base[tid][0]['rows']
assert count == sum(1 for p in source['pages'] for b in p['blocks'] if b['type']!='image') == 210
print(f'{count} source blocks mapped exactly once; base block text and order preserved; production build remains opt-in')
