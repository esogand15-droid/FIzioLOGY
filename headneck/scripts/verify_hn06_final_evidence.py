"""Verify byte identity and recorded coverage, NOT that reading/scientific review happened."""
import hashlib
import json
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'headneck/reports/hn06_final_evidence'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((E/n).read_text())
def verify():
 from reproduce_hn06_evidence import reproduce
 renders=ROOT/'.cache/hn06-reproduced'
 assert reproduce(renders)==113
 pdf=ROOT/'pdf/HumsYar_HeadNeck_Jalase6_FINAL.pdf';sha=digest(pdf)
 with pymupdf.open(pdf) as doc:count=len(doc)
 manual=load('manual_review.json');assert manual['pdf_sha256']==sha and not manual['not_yet_reviewed']
 assert [r['page'] for r in manual['reviewed_pages']]==list(range(1,count+1))
 for r in manual['reviewed_pages']:assert digest(renders/r['render'])==r['render_sha256']
 source=load('source_editorial_review.json');refs=load('reference_editorial_inventory.json')
 for inv,key in [(source,'source_pages'),(refs,'pages')]:
  assert inv['final_pdf_sha256']==sha
  for r in inv[key]:assert digest(renders/r['source_render'])==r['source_render_sha256']
 assert digest(ROOT/source['file'])==source['source_sha256']
 assert [r['source_pdf_page'] for r in source['source_pages']]==list(range(1,21))
 expected={*(('netter',n) for n in [105,106,107,109,281,282,283,284,285]),*(('gray_neck',n) for n in [35,36,37,38,56,57,58]),*(('gray_back',n) for n in [85,95,108,112,113,114,115,116,117,120,121,122,123,124,125,126,127])}
 assert {(r['book'],r['source_pdf_page']) for r in refs['pages']}==expected
 for r in refs['sources']:assert digest(ROOT/r['file'])==r['sha256']
 for n,printed in [(121,94),(122,93)]:assert next(r for r in refs['pages'] if r['book']=='gray_back' and r['source_pdf_page']==n)['printed_page']==printed
 pairs=load('source_text_pairs.json');assert pairs['final_pdf_sha256']==sha and len(pairs['pairs'])==236
 typed=json.loads((ROOT/'headneck/content/hn06_transcription.json').read_text())
 assert [r['text'] for r in pairs['pairs']]==[b['text'] for p in typed['pages'] for b in p['blocks']]
 machine=load('machine_manifest.json');assert machine['sha256']==sha and not machine['errors'] and not machine['outside_spans']
 assert machine['bytes']==pdf.stat().st_size and machine['pages']==count
 assert machine['baseline_pdf_sha256']==digest(ROOT/'pdf/HumsYar_HeadNeck_Jalase6.pdf')=='fd92b99026629cff963965eea6d5b8546f6b9eff6f91b48a958cd8fdf37dd50f'
 for r in machine['content']+machine['sources']:assert digest(ROOT/r['file'])==r['sha256']
 assert len(machine['figures'])==29
 assert len({r['asset'] for r in machine['figures']})==28
 for r in machine['figures']:
  assert digest(ROOT/r['asset'])==r['asset_sha256'] and (ROOT/r['source_file']).is_file()
  assert r['output_pages']
 assert load('layout_trace.json')['sha256']==sha
 assert sha in (ROOT/'headneck/reports/HN_S06_FINAL_TECHNICAL_QA_REPORT.md').read_text()
 return dict(sha256=sha,pages=count,source_pages=20,reference_pages=33,figures=29,result='Byte identity and recorded coverage verified; NOT automatic proof of reading or scientific correctness.')
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
