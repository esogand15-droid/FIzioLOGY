#!/usr/bin/env python3
"""Compare tokens for review; PDF RTL extraction is noisy, not a gold standard."""
from collections import Counter
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[2]
inv=json.loads((ROOT/'headneck/reports/HN_S03_SOURCE_INVENTORY.json').read_text(encoding='utf-8'))
trans=json.loads((ROOT/'headneck/content/hn03_source_transcription_wip.json').read_text(encoding='utf-8'))

def tokens(text):
    text=text.translate(str.maketrans({'ك':'ک','ي':'ی','ۀ':'ه','ة':'ه','ؤ':'و','ئ':'ی'})).replace('\u200c',' ')
    return Counter(w.lower() for w in re.findall(r'[آ-ی]{3,}|[a-zA-Z]{3,}',text))

results=[]
for page in trans['pages']:
    n=page['pdf_page']
    original=inv['lecture']['pages'][n-1]['raw_text']
    typed=' '.join(b.get('text','')+' '+' '.join(b.get('items',[])) for b in page['blocks'])
    source_words=tokens(original); typed_words=tokens(typed)
    results.append({'pdf_page':n,'raw_token_count':sum(source_words.values()),
        'transcription_token_count':sum(typed_words.values()),
        'raw_only':dict(source_words-typed_words),'transcription_only':dict(typed_words-source_words),
        'visual_second_pass_recorded':bool(page.get('visual_second_pass_recorded')),
        'independent_reconciliation_verified':bool(page['independently_reconciled'])})
out=ROOT/'headneck/reports/HN_S03_TOKEN_COMPARISON_WIP.json'
out.write_text(json.dumps({'disclaimer':'Counts are order-insensitive and PDF extraction is noisy; '
    'missing or extra words may be extraction artifacts or transcription errors. '
    'A match does not prove verbatim accuracy.', 'pages':results},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(f'{len(results)} pages compared; token comparison is not evidence of exact transcription')
