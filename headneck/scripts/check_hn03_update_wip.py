#!/usr/bin/env python3
"""Structural checks for the session 3 work in progress (not a content audit)."""
from pathlib import Path
from collections import Counter
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
C = ROOT / 'headneck/content'
base = {t['topic_id']: t['blocks'] for part in ('a', 'b')
        for t in json.loads((C / f'hn03_{part}.json').read_text(encoding='utf-8'))}
update = json.loads((C / 'hn03_update.json').read_text(encoding='utf-8'))
assert 'work in progress' in update['status']
assert set(update['topics']) == set(base) and len(base) == 19
assets = json.loads((ROOT/'headneck/images/INDEX.json').read_text(encoding='utf-8'))['assets']
by_path = {a['path']: a for a in assets}
types = Counter()
for tid, original in base.items():
    spec = update['topics'][tid]
    assert original[0]['type'] == 'idcard' and original[-1]['type'] == 'handoff', tid
    assert len(spec['card_rows']) >= 2, tid
    for key, extra in spec['after'].items():
        assert 0 <= int(key) < len(original) - 1, (tid, key)
        for block in extra:
            types[block['type']] += 1
            assert block.get('src'), (tid, block['type'])
            if block['type'] == 'plate':
                path = block['asset']
                assert path in by_path and (ROOT/path).is_file(), (tid,path)
                a = by_path[path]
                assert a['book'] == 'netter' and a['session'] == 'hn03' and len(a['bbox']) == 4
                with Image.open(ROOT/path) as image:
                    assert image.size == (a['w'], a['h']) and min(image.size) > 400
            if block['type'] == 'table':
                assert block['head'] and all(len(row) == len(block['head']) for row in block['rows'])
transcription = json.loads((C/'hn03_source_transcription_wip.json').read_text(encoding='utf-8'))
assert [p['pdf_page'] for p in transcription['pages']] == list(range(2, 21))
print('19 topic overlays structurally valid;', dict(types),
      '; pages independently reconciled and verified:', [p['pdf_page'] for p in transcription['pages'] if p['independently_reconciled']],
      '; pages not independently verified:', [p['pdf_page'] for p in transcription['pages'] if not p['independently_reconciled']])
print('Structural checks do not prove exact transcription, scientific accuracy, crop readability in the PDF, or complete atlas review.')
