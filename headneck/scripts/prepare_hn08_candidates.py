"""Reproduce session-eight *candidate* figure crops and raw text, without modifying source files.

These crops and raw text are not verified transcription or a finished booklet.
Requires requirements.txt; writes only to .cache/hn08/candidates and .cache/hn08/raw_text.
"""
import hashlib,json,unicodedata
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'headneck/reports/hn08_evidence/figure_candidates.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 data=json.loads(DATA.read_text(encoding='utf-8'))
 source=ROOT/data['source']
 if sha(source)!=data['source_sha256']:raise ValueError('Session-eight source bytes changed')
 docs={}
 for entry in data['figure_assets']:
  path=ROOT/entry['path'];path.parent.mkdir(parents=True,exist_ok=True)
  src=ROOT/entry['source']
  if str(src) not in docs:docs[str(src)]=pymupdf.open(src)
  doc=docs[str(src)];page=doc[entry['source_pdf_page']-1]
  page.get_pixmap(matrix=pymupdf.Matrix(2,2),clip=pymupdf.Rect(entry['bbox_points']),alpha=False).save(path)
  if sha(path)!=entry['sha256']:raise ValueError(f'Candidate bytes differ: {path}')
 out=ROOT/'.cache/hn08/raw_text';out.mkdir(parents=True,exist_ok=True)
 for i,page in enumerate(docs[str(source)],1):
  (out/f'page-{i:02}.txt').write_text(unicodedata.normalize('NFKC',page.get_text()),encoding='utf-8')
 for doc in docs.values():doc.close()
 print(f"{len(data['figure_assets'])} candidate crops verified; raw extraction for {data['pages']} pages generated. Manual review is still required.")
if __name__=='__main__':main()
