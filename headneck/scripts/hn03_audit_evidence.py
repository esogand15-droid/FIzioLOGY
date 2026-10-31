#!/usr/bin/env python3
"""Create reproducible session-3 review evidence, without claiming visual verification.

Usage: python headneck/scripts/hn03_audit_evidence.py /path/to/candidate.pdf
The script writes machine-produced comparison evidence and a page manifest. It
never overwrites the separate manual tracker or marks a page as reviewed.
"""
from collections import Counter
from difflib import unified_diff
from pathlib import Path
import hashlib, json, re, sys, unicodedata
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'headneck/reports/hn03_audit_evidence'
OUT.mkdir(parents=True, exist_ok=True)
pdf = Path(sys.argv[1])
pdfhash = hashlib.sha256(pdf.read_bytes()).hexdigest()
source = json.loads((ROOT/'headneck/reports/HN_S03_SOURCE_INVENTORY.json').read_text(encoding='utf-8'))
trans = json.loads((ROOT/'headneck/content/hn03_source_transcription_wip.json').read_text(encoding='utf-8'))

def normal(s):
    # Presentation forms and Arabic letter variants only; do not equate words.
    s = unicodedata.normalize('NFKC',s).translate(str.maketrans({'ك':'ک','ي':'ی','\u200c':' '}))
    return re.findall(r'[\w\u0600-\u06ff]+',s.lower())

records=[]
for page in trans['pages']:
    n=page['pdf_page']; original=source['lecture']['pages'][n-1]['raw_text']
    blocks=[]
    for block in page['blocks']:
        if 'text' in block: blocks.append(block['text'])
        blocks.extend(block.get('items',[]))
    typed='\n'.join(blocks)
    a=normal(original); b=normal(typed)
    diff='\n'.join(unified_diff(a,b,fromfile=f'source-pdf-{n}-raw',tofile=f'transcription-{n}',lineterm='',n=3))
    ap=Counter(a); bp=Counter(b)
    p=OUT/f'lecture_page_{n:02}_diff.json'
    p.write_text(json.dumps({'source_page':n,'scope':'source-extracted tokens versus transcription; NOT direct output text; RTL extraction and line order are noisy',
        'source_tokens':len(a),'transcription_tokens':len(b),'only_in_source':dict(ap-bp),
        'only_in_transcription':dict(bp-ap),'ordered_token_diff':diff},ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    records.append({'page':n,'non_image_blocks':sum(x['type']!='image' for x in page['blocks']),
        'comparison_evidence':str(p.relative_to(ROOT)),'visual_word_by_word_verified':False})

# Store extraction and page hashes to bind future manual evidence to exact bytes.
doc=pymupdf.open(pdf); pages=[]
for i,page in enumerate(doc):
    text=page.get_text()
    pages.append({'output_page':i+1,'extracted_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                  'visual_review':'NOT_STARTED'})
manifest={'pdf_sha256':pdfhash,'pdf_path_at_generation':str(pdf),'page_count':len(doc),
          'source_pdf_sha256':source['lecture']['sha256'], 'source_pages':records,'output_pages':pages,
          'notes':['Diffs compare source-extracted text to transcription, not rendered output.',
                   'Neither diffs nor a page render alone establish visual or textual correctness.',
                   'Any changed PDF invalidates page-specific visual review for that PDF hash.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(f'{len(records)} source-page diffs and {len(pages)} output-page entries; PDF {pdfhash}')
