"""Index every Netter PDF page's searchable text and likely session-1 matches.

This index is only a discovery aid, not image recognition: searchable text can
refer to an adjacent figure or cross-reference another plate, and image-only
labels are not searchable. Candidate images still require visual review.
"""
import hashlib
import json
import re
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parents[2]
p=next((ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1').glob('Netter*.pdf'))
terms=['skull','cranium','frontal bone','nasal bone','maxilla','maxillary sinus','hyoid bone','lacrimal sac','hard palate','diploë','cranial base']
doc=pymupdf.open(p);pages=[]
for i,page in enumerate(doc):
 text=page.get_text();low=text.casefold();lines=[x.strip() for x in text.splitlines() if x.strip()]
 plates=re.findall(r'\bPlate\s+(?:BP\s*)?\d+\b', text, re.I)
 pages.append({'pdf_page':i+1,'first_text_lines':lines[:5], 'plate_mentions':list(dict.fromkeys(plates)),
               'candidate_terms':[term for term in terms if term in low], 'text_characters':len(text)})
out={'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
     'page_count':len(doc),'disclaimer':'فهرست ماشینی کل صفحات؛ تطابق کلمه اثبات ارتباط شکل یا بازبینی بصری نیست.','pages':pages}
path=ROOT/'headneck/reports/HN_S01_NETTER_INDEX.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(len(pages),'pages;',sum(bool(x['candidate_terms']) for x in pages),'search candidates')
