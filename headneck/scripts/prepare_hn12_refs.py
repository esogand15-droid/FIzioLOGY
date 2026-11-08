"""Prepare the newborn-skull plate and reuse inspected Netter crops from session 11."""
from pathlib import Path
import hashlib,json,shutil
import pymupdf
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'headneck/images/hn12_refs';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'علوم تشریح سر و گردن/جلسه 1 - سر و گردن 1/Netter Atlas of Human Anatomy Classic Regional Approach.pdf'
p=pymupdf.open(source)[86];r=p.rect;p.get_pixmap(matrix=pymupdf.Matrix(2.2,2.2),clip=pymupdf.Rect(0,r.height*.075,r.width,r.height*.93),alpha=False).save(OUT/'netter_87.png')
for n in ['124','202','213']:shutil.copyfile(ROOT/f'headneck/images/hn11_refs/netter_{n}.png',OUT/f'netter_{n}.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta={'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'references':[{'plate':plate,'file_page':page,'asset':str((OUT/f'netter_{page}.png').relative_to(ROOT)),'sha256':sha(OUT/f'netter_{page}.png')} for page,plate in [(87,35),(124,72),(202,150),(213,161)]]}
(ROOT/'headneck/reports/hn12_evidence/reference_candidates.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
